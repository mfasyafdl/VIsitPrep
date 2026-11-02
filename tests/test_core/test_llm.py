"""Tests for core.llm (task P1-2): config loading and chat_json with faked _post and _sleep; no network is ever used."""

import copy
import http.client
import json
import ssl
from pathlib import Path

import pytest

from core import llm


class FakePost:
    def __init__(self, results):
        self.results = list(results)
        self.calls = []

    def __call__(self, url, payload, headers, timeout):
        self.calls.append(
            {
                "url": url,
                "payload": copy.deepcopy(payload),
                "headers": dict(headers),
                "timeout": timeout,
            }
        )
        if not self.results:
            raise AssertionError("FakePost has no queued result left")
        item = self.results.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


class FakeSleep:
    def __init__(self):
        self.delays = []

    def __call__(self, seconds):
        self.delays.append(seconds)


def ok_body(content, finish_reason="stop"):
    return json.dumps(
        {
            "choices": [
                {
                    "message": {"role": "assistant", "content": content},
                    "finish_reason": finish_reason,
                }
            ]
        }
    )


CONFIG = llm.LLMConfig("sk-test-key", "zai-org/GLM-5.2", llm.BASE_URL)


@pytest.fixture
def fakes(monkeypatch):
    post = FakePost([])
    sleep = FakeSleep()
    monkeypatch.setattr(llm, "_post", post)
    monkeypatch.setattr(llm, "_sleep", sleep)
    monkeypatch.delenv("MODELSCOPE_API_KEY", raising=False)
    monkeypatch.delenv("MODELSCOPE_MODEL", raising=False)
    monkeypatch.setattr(llm, "_env_file_path", lambda: Path("nonexistent") / ".env")
    return post, sleep


def test_success_returns_dict_and_sends_expected_payload(fakes):
    post, sleep = fakes
    post.results = [(200, ok_body('{"ok": true}'))]
    data = llm.chat_json("SYS", "USR", validate=lambda d: [], config=CONFIG)
    assert data == {"ok": True}
    assert len(post.calls) == 1
    call = post.calls[0]
    assert call["url"] == llm.BASE_URL + "/chat/completions"
    assert call["headers"]["Authorization"] == "Bearer sk-test-key"
    assert call["headers"]["Content-Type"] == "application/json"
    assert call["timeout"] == 120.0
    payload = call["payload"]
    assert payload["model"] == "zai-org/GLM-5.2"
    assert payload["messages"] == [
        {"role": "system", "content": "SYS"},
        {"role": "user", "content": "USR"},
    ]
    assert payload["temperature"] == 0.2
    assert payload["max_tokens"] == 4000
    assert payload["response_format"] == {"type": "json_object"}
    assert sleep.delays == []


@pytest.mark.parametrize(
    "fenced",
    ['```json\n{"ok": true}\n```', '```\n{"ok": true}\n```'],
)
def test_fenced_json_is_stripped(fakes, fenced):
    post, _ = fakes
    post.results = [(200, ok_body(fenced))]
    data = llm.chat_json("SYS", "USR", validate=lambda d: [], config=CONFIG)
    assert data == {"ok": True}
    assert len(post.calls) == 1


def test_http_401_raises_auth_error(fakes):
    post, sleep = fakes
    post.results = [(401, json.dumps({"error": "unauthorized"}))]
    with pytest.raises(llm.LLMAuthError) as exc:
        llm.chat_json("SYS", "USR", validate=lambda d: [], config=CONFIG)
    assert str(exc.value) == "The AI service rejected the server's key."
    assert len(post.calls) == 1
    assert sleep.delays == []


def test_http_403_raises_auth_error(fakes):
    post, sleep = fakes
    post.results = [(403, json.dumps({"error": "forbidden"}))]
    with pytest.raises(llm.LLMAuthError) as exc:
        llm.chat_json("SYS", "USR", validate=lambda d: [], config=CONFIG)
    assert str(exc.value) == "The AI service rejected the server's key."
    assert len(post.calls) == 1
    assert sleep.delays == []


def test_http_429_raises_quota_error(fakes):
    post, sleep = fakes
    post.results = [(429, json.dumps({"error": "rate limited"}))]
    with pytest.raises(llm.LLMQuotaError) as exc:
        llm.chat_json("SYS", "USR", validate=lambda d: [], config=CONFIG)
    assert str(exc.value) == (
        "The free AI quota for today may be used up. Please try again later."
    )
    assert len(post.calls) == 1
    assert sleep.delays == []


def test_500_then_success_retries_once_with_half_second_sleep(fakes):
    post, sleep = fakes
    post.results = [(500, "boom"), (200, ok_body('{"ok": true}'))]
    data = llm.chat_json("SYS", "USR", validate=lambda d: [], config=CONFIG)
    assert data == {"ok": True}
    assert len(post.calls) == 2
    assert sleep.delays == [0.5]


def test_timeout_three_times_raises_network_error(fakes):
    post, sleep = fakes
    post.results = [TimeoutError("t"), TimeoutError("t"), TimeoutError("t")]
    with pytest.raises(llm.LLMNetworkError) as exc:
        llm.chat_json("SYS", "USR", validate=lambda d: [], config=CONFIG)
    assert str(exc.value) == "The AI service did not respond."
    assert len(post.calls) == 3
    assert sleep.delays == [0.5, 1.0]


def test_invalid_json_then_valid_repair(fakes):
    post, sleep = fakes
    post.results = [
        (200, ok_body("this is not json")),
        (200, ok_body('{"ok": true}')),
    ]
    data = llm.chat_json("SYS", "USR", validate=lambda d: [], config=CONFIG)
    assert data == {"ok": True}
    assert len(post.calls) == 2
    assert sleep.delays == []
    assert post.calls[0]["payload"]["messages"] == [
        {"role": "system", "content": "SYS"},
        {"role": "user", "content": "USR"},
    ]
    assert post.calls[1]["payload"]["messages"] == [
        {"role": "system", "content": "SYS"},
        {"role": "user", "content": "USR"},
        {"role": "assistant", "content": "this is not json"},
        {
            "role": "user",
            "content": (
                "Your previous answer was not valid. Problems: "
                "the answer was not valid JSON. "
                "Reply with the corrected JSON object only."
            ),
        },
    ]


def test_validate_errors_twice_raises_response_error(fakes):
    post, _ = fakes
    post.results = [
        (200, ok_body('{"ok": false}')),
        (200, ok_body('{"ok": false}')),
    ]

    def validate(d):
        return [] if d.get("ok") is True else ["ok must be true"]

    with pytest.raises(llm.LLMResponseError) as exc:
        llm.chat_json("SYS", "USR", validate=validate, config=CONFIG)
    assert str(exc.value) == (
        "The AI service returned an answer we could not read. Please try again."
    )
    assert len(post.calls) == 2


def test_content_none_triggers_repair(fakes):
    post, _ = fakes
    post.results = [
        (200, ok_body(None)),
        (200, ok_body('{"ok": true}')),
    ]
    data = llm.chat_json("SYS", "USR", validate=lambda d: [], config=CONFIG)
    assert data == {"ok": True}
    assert len(post.calls) == 2
    repair = post.calls[1]["payload"]["messages"][3]
    assert repair["content"] == (
        "Your previous answer was not valid. Problems: the answer was empty. "
        "Reply with the corrected JSON object only."
    )


def test_missing_key_raises_config_error(fakes):
    with pytest.raises(llm.ConfigError) as exc:
        llm.load_config()
    assert str(exc.value) == "The AI service is not configured on this server."


def test_disallowed_model_raises_config_error(monkeypatch):
    monkeypatch.setenv("MODELSCOPE_API_KEY", "sk-x")
    monkeypatch.setenv("MODELSCOPE_MODEL", "some/other-model")
    with pytest.raises(llm.ConfigError) as exc:
        llm.load_config()
    assert str(exc.value) == (
        "Unknown model. Allowed models: zai-org/GLM-5.2, "
        "deepseek-ai/DeepSeek-V4-Pro-0813, stepfun-ai/Step-3.5-Flash, "
        "Qwen/Qwen3.8-27B"
    )


def test_env_file_parsing_with_quotes_and_comments(monkeypatch, tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "# server config\n"
        "\n"
        'MODELSCOPE_API_KEY="sk-from-env-file"\n'
        "MODELSCOPE_MODEL = 'Qwen/Qwen3.8-27B'\n"
        "VISITPREP_PREVIEW=1\n",
        encoding="utf-8",
    )
    monkeypatch.delenv("MODELSCOPE_API_KEY", raising=False)
    monkeypatch.delenv("MODELSCOPE_MODEL", raising=False)
    monkeypatch.setattr(llm, "_env_file_path", lambda: env_file)
    config = llm.load_config()
    assert config.api_key == "sk-from-env-file"
    assert config.model == "Qwen/Qwen3.8-27B"
    assert config.base_url == llm.BASE_URL


def test_env_file_with_utf8_bom(monkeypatch, tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text(
        'MODELSCOPE_API_KEY="sk-bom-key"\n'
        "MODELSCOPE_MODEL='stepfun-ai/Step-3.5-Flash'\n",
        encoding="utf-8-sig",
    )
    monkeypatch.delenv("MODELSCOPE_API_KEY", raising=False)
    monkeypatch.delenv("MODELSCOPE_MODEL", raising=False)
    monkeypatch.setattr(llm, "_env_file_path", lambda: env_file)
    config = llm.load_config()
    assert config.api_key == "sk-bom-key"
    assert config.model == "stepfun-ai/Step-3.5-Flash"


def test_env_variable_beats_env_file(monkeypatch, tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text(
        'MODELSCOPE_API_KEY="sk-file-key"\n'
        'MODELSCOPE_MODEL="deepseek-ai/DeepSeek-V4-Pro-0813"\n',
        encoding="utf-8",
    )
    monkeypatch.setenv("MODELSCOPE_API_KEY", "sk-env-key")
    monkeypatch.delenv("MODELSCOPE_MODEL", raising=False)
    monkeypatch.setattr(llm, "_env_file_path", lambda: env_file)
    config = llm.load_config()
    assert config.api_key == "sk-env-key"
    assert config.model == "deepseek-ai/DeepSeek-V4-Pro-0813"


def test_model_defaults_to_default_model(monkeypatch):
    monkeypatch.setenv("MODELSCOPE_API_KEY", "sk-x")
    monkeypatch.delenv("MODELSCOPE_MODEL", raising=False)
    monkeypatch.setattr(llm, "_env_file_path", lambda: Path("nonexistent") / ".env")
    config = llm.load_config()
    assert config.model == llm.DEFAULT_MODEL


def test_timeout_out_of_range_raises_value_error(fakes):
    post, _ = fakes
    with pytest.raises(ValueError):
        llm.chat_json("SYS", "USR", validate=lambda d: [], config=CONFIG, timeout=0)
    with pytest.raises(ValueError):
        llm.chat_json("SYS", "USR", validate=lambda d: [], config=CONFIG, timeout=601)
    assert post.calls == []


def test_content_filter_400_raises_after_exactly_one_call(fakes):
    post, sleep = fakes
    body = json.dumps(
        {
            "error": {
                "code": "data_inspection_failed",
                "message": "Output data may contain inappropriate content.",
            }
        }
    )
    post.results = [(400, body)]
    with pytest.raises(llm.LLMContentFilterError) as exc:
        llm.chat_json("SYS", "USR", validate=lambda d: [], config=CONFIG)
    assert str(exc.value) == (
        "The AI service could not process this text. Please describe your "
        "symptoms in plain, simple words and try again."
    )
    assert len(post.calls) == 1
    assert sleep.delays == []


def test_content_filter_finish_reason_raises(fakes):
    post, sleep = fakes
    body = ok_body("fine text", finish_reason="content_filter")
    post.results = [(200, body)]
    with pytest.raises(llm.LLMContentFilterError) as exc:
        llm.chat_json("SYS", "USR", validate=lambda d: [], config=CONFIG)
    assert str(exc.value) == (
        "The AI service could not process this text. Please describe your "
        "symptoms in plain, simple words and try again."
    )
    assert len(post.calls) == 1
    assert sleep.delays == []


def test_response_format_400_resends_once_without_response_format(fakes):
    post, sleep = fakes
    post.results = [
        (
            400,
            json.dumps({"error": {"message": "response_format is not supported"}}),
        ),
        (200, ok_body('{"ok": true}')),
    ]
    data = llm.chat_json("SYS", "USR", validate=lambda d: [], config=CONFIG)
    assert data == {"ok": True}
    assert len(post.calls) == 2
    assert post.calls[0]["payload"]["response_format"] == {"type": "json_object"}
    assert "response_format" not in post.calls[1]["payload"]
    assert post.calls[1]["payload"]["messages"] == post.calls[0]["payload"]["messages"]
    assert sleep.delays == []


def test_errors_do_not_leak_key_or_user_text(fakes):
    post, _ = fakes
    secret_config = llm.LLMConfig("sk-test-SECRET", "zai-org/GLM-5.2", llm.BASE_URL)
    user_text = "MY-PRIVATE-STORY"
    scenarios = [
        [(401, "denied")],
        [(403, "denied")],
        [(429, "slow down")],
        [(400, json.dumps({"error": {"message": "something else"}}))],
        [TimeoutError("t"), TimeoutError("t"), TimeoutError("t")],
        [(500, "boom"), (500, "boom"), (500, "boom")],
    ]
    for results in scenarios:
        post.results = list(results)
        with pytest.raises(llm.LLMError) as exc:
            llm.chat_json("SYS", user_text, validate=lambda d: [], config=secret_config)
        text = str(exc.value)
        assert "sk-test-SECRET" not in text
        assert user_text not in text


def test_config_repr_hides_api_key():
    config = llm.LLMConfig("sk-test-SECRET", "zai-org/GLM-5.2", llm.BASE_URL)
    assert "sk-test-SECRET" not in repr(config)
    assert "sk-test-SECRET" not in str(config)


def test_content_filter_dashscope_spelling_400_raises_after_one_call(fakes):
    post, sleep = fakes
    body = json.dumps(
        {
            "code": "DataInspectionFailed",
            "message": "Output data may contain inappropriate content.",
        }
    )
    post.results = [(400, body)]
    with pytest.raises(llm.LLMContentFilterError) as exc:
        llm.chat_json("SYS", "USR", validate=lambda d: [], config=CONFIG)
    assert str(exc.value) == (
        "The AI service could not process this text. Please describe your "
        "symptoms in plain, simple words and try again."
    )
    assert len(post.calls) == 1
    assert sleep.delays == []


def test_ssl_error_then_success_retries(fakes):
    post, sleep = fakes
    post.results = [ssl.SSLError("x"), (200, ok_body('{"ok": true}'))]
    data = llm.chat_json("SYS", "USR", validate=lambda d: [], config=CONFIG)
    assert data == {"ok": True}
    assert len(post.calls) == 2
    assert sleep.delays == [0.5]


def test_incomplete_read_three_times_raises_network_error(fakes):
    post, sleep = fakes
    post.results = [
        http.client.IncompleteRead(b""),
        http.client.IncompleteRead(b""),
        http.client.IncompleteRead(b""),
    ]
    with pytest.raises(llm.LLMNetworkError) as exc:
        llm.chat_json("SYS", "USR", validate=lambda d: [], config=CONFIG)
    assert str(exc.value) == "The AI service did not respond."
    assert len(post.calls) == 3
    assert sleep.delays == [0.5, 1.0]
