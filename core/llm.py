"""ModelScope LLM client for VisitPrep core: load_config() reads the server key and model from the environment or the project .env file, and chat_json() calls the chat completions API, maps failures to safe English errors and returns a validated JSON object; nothing is printed, logged or chained into an error that could carry the API key or patient text."""

import dataclasses
import http.client
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Callable

BASE_URL = "https://api-inference.modelscope.ai/v1"
DEFAULT_MODEL = "zai-org/GLM-5.2"
ALLOWED_MODELS = (
    "zai-org/GLM-5.2",
    "deepseek-ai/DeepSeek-V4-Pro-0813",
    "stepfun-ai/Step-3.5-Flash",
    "Qwen/Qwen3.8-27B",
)

_NOT_CONFIGURED = "The AI service is not configured on this server."
_UNKNOWN_MODEL = "Unknown model. Allowed models: " + ", ".join(ALLOWED_MODELS)
_KEY_REJECTED = "The AI service rejected the server's key."
_QUOTA_USED_UP = "The free AI quota for today may be used up. Please try again later."
_SERVER_PROBLEM = "The AI service had a problem. Please try again."
_UNREADABLE_ANSWER = "The AI service returned an answer we could not read. Please try again."
_NO_RESPONSE = "The AI service did not respond."
_CONTENT_FILTERED = (
    "The AI service could not process this text. Please describe your "
    "symptoms in plain, simple words and try again."
)


@dataclasses.dataclass
class LLMConfig:
    api_key: str = dataclasses.field(repr=False)
    model: str
    base_url: str


class LLMError(Exception):
    """Base error for all LLM failures in core.llm."""


class ConfigError(LLMError):
    """The LLM configuration is missing or invalid."""


class LLMAuthError(LLMError):
    """The provider rejected the API key."""


class LLMQuotaError(LLMError):
    """The provider quota or rate limit was reached."""


class LLMNetworkError(LLMError):
    """The network request to the provider failed."""


class LLMServerError(LLMError):
    """The provider server returned a server error."""


class LLMResponseError(LLMError):
    """The provider response is not usable JSON data."""


class LLMContentFilterError(LLMError):
    """The provider's content filter rejected the text."""


def _env_file_path() -> Path:
    return Path(__file__).resolve().parent.parent / ".env"


def _read_env_file(path: Path) -> dict:
    values = {}
    if not path.is_file():
        return values
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, _, value = line.partition("=")
        name = name.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
            value = value[1:-1]
        if name:
            values[name] = value
    return values


def load_config() -> LLMConfig:
    api_key = os.environ.get("MODELSCOPE_API_KEY")
    model = os.environ.get("MODELSCOPE_MODEL")
    if api_key is None or model is None:
        file_values = _read_env_file(_env_file_path())
        if api_key is None:
            api_key = file_values.get("MODELSCOPE_API_KEY")
        if model is None:
            model = file_values.get("MODELSCOPE_MODEL")
    if not api_key:
        raise ConfigError(_NOT_CONFIGURED)
    if model is None:
        model = DEFAULT_MODEL
    if model not in ALLOWED_MODELS:
        raise ConfigError(_UNKNOWN_MODEL)
    return LLMConfig(api_key, model, BASE_URL)


def _post(url: str, payload: dict, headers: dict, timeout: float) -> tuple:
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8", "replace")
            return response.status, body
    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8", "replace")
        return error.code, body


def _sleep(seconds: float) -> None:
    time.sleep(seconds)


def _strip_code_fence(text: str) -> str:
    text = text.strip()
    if not text.startswith("```"):
        return text
    first_break = text.find("\n")
    if first_break == -1:
        return text
    header = text[3:first_break].strip()
    if header not in ("", "json"):
        return text
    rest = text[first_break + 1 :].rstrip()
    if not rest.endswith("```"):
        return text
    return rest[: -3].strip()


def _parse_answer(content, validate: Callable[[dict], list[str]]):
    if not isinstance(content, str) or not content.strip():
        return None, ["the answer was empty"]
    try:
        data = json.loads(_strip_code_fence(content))
    except ValueError:
        return None, ["the answer was not valid JSON"]
    if not isinstance(data, dict):
        return None, ["the answer was not a JSON object"]
    return data, list(validate(data))


def chat_json(
    system: str,
    user: str,
    *,
    validate: Callable[[dict], list[str]],
    config: LLMConfig | None = None,
    max_tokens: int = 4000,
    timeout: float = 120.0,
    max_retries: int = 2,
    max_repairs: int = 1,
) -> dict:
    if not (0 < timeout <= 600):
        raise ValueError("timeout must be greater than 0 and at most 600 seconds")
    if config is None:
        config = load_config()
    url = config.base_url + "/chat/completions"
    headers = {
        "Authorization": "Bearer " + config.api_key,
        "Content-Type": "application/json",
    }
    base_payload = {
        "model": config.model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.2,
        "max_tokens": max_tokens,
    }

    def post_with_retries(payload: dict) -> tuple:
        last_error = None
        for index in range(max_retries + 1):
            try:
                status, body = _post(url, payload, headers, timeout)
            except (OSError, http.client.HTTPException):
                last_error = LLMNetworkError(_NO_RESPONSE)
                if index < max_retries:
                    _sleep(min(0.5 * 2 ** index, 4.0))
                continue
            if 500 <= status <= 599:
                last_error = LLMServerError(_SERVER_PROBLEM)
                if index < max_retries:
                    _sleep(min(0.5 * 2 ** index, 4.0))
                continue
            return status, body
        raise last_error from None

    messages = list(base_payload["messages"])
    resent_without_format = False
    repairs_used = 0
    payload = dict(base_payload)
    payload["response_format"] = {"type": "json_object"}
    while True:
        status, body = post_with_retries(payload)

        if status == 200:
            try:
                response_data = json.loads(body)
            except ValueError:
                response_data = None
            choices = (
                response_data.get("choices") if isinstance(response_data, dict) else None
            )
            first = (
                choices[0]
                if isinstance(choices, list) and choices and isinstance(choices[0], dict)
                else {}
            )
            if first.get("finish_reason") == "content_filter":
                raise LLMContentFilterError(_CONTENT_FILTERED) from None
            message = first.get("message")
            content = message.get("content") if isinstance(message, dict) else None
            data, problems = _parse_answer(content, validate)
            if not problems:
                return data
            if repairs_used >= max_repairs:
                raise LLMResponseError(_UNREADABLE_ANSWER) from None
            repairs_used += 1
            assistant_content = content if isinstance(content, str) else ""
            messages = messages + [
                {"role": "assistant", "content": assistant_content},
                {
                    "role": "user",
                    "content": (
                        "Your previous answer was not valid. Problems: "
                        + "; ".join(problems)
                        + ". Reply with the corrected JSON object only."
                    ),
                },
            ]
            payload = dict(base_payload)
            payload["messages"] = messages
            if not resent_without_format:
                payload["response_format"] = {"type": "json_object"}
            continue

        lowered = body.lower()
        if status == 400:
            if (
                "data_inspection_failed" in lowered
                or "datainspectionfailed" in lowered
            ):
                raise LLMContentFilterError(_CONTENT_FILTERED) from None
            if "response_format" in lowered and not resent_without_format:
                resent_without_format = True
                payload = dict(base_payload)
                payload["messages"] = messages
                continue
            raise LLMResponseError(_UNREADABLE_ANSWER) from None
        if status in (401, 403):
            raise LLMAuthError(_KEY_REJECTED) from None
        if status == 429:
            raise LLMQuotaError(_QUOTA_USED_UP) from None
        if 500 <= status <= 599:
            raise LLMServerError(_SERVER_PROBLEM) from None
        raise LLMResponseError(_UNREADABLE_ANSWER) from None
