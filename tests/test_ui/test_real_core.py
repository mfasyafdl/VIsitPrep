"""Tests that run the real core against the handlers.

Only core.llm._post (and core.llm._sleep, to a no-op) are faked with
monkeypatch; core.extract, core.interview, core.summarize and
core.redflag are the real code. No network is used.
"""

import json

from core import prompts

import ui.backend as backend
from ui import handlers
from ui.state import new_state

STORY = "I have felt tired for a few days."

NOT_CONFIGURED = "The AI service is not configured on this server."


def _minimal_record() -> dict:
    """Only complaint is set; every other field is unknown."""
    return {
        "patient_age": None,
        "patient_age_text": None,
        "patient_sex": None,
        "reporting_on_behalf": None,
        "reporter_relationship": None,
        "complaint": "I have felt tired for a few days.",
        "symptoms": [],
        "onset": None,
        "duration": None,
        "severity": None,
        "severity_note": None,
        "medicines": [],
        "medicines_denied": None,
        "allergies": [],
        "allergies_denied": None,
        "medical_history": [],
        "medical_history_denied": None,
        "pregnant": None,
        "concerns": [],
    }


def _setup(monkeypatch, tmp_path, with_key=True, statuses=None,
           merge_raises=None):
    """Real core with a faked transport; returns the call log."""
    monkeypatch.setattr(backend, "PREVIEW", False)
    monkeypatch.setattr(
        "core.llm._env_file_path", lambda: tmp_path / "no-such-env-file"
    )
    if with_key:
        monkeypatch.setenv("MODELSCOPE_API_KEY", "test-key")
        monkeypatch.setenv("MODELSCOPE_MODEL", "Qwen/Qwen3.8-27B")
    else:
        monkeypatch.delenv("MODELSCOPE_API_KEY", raising=False)
        monkeypatch.delenv("MODELSCOPE_MODEL", raising=False)
    statuses = dict(statuses or {})
    calls = []

    def fake_post(url, payload, headers, timeout):
        system = payload["messages"][0]["content"]
        calls.append(system)
        if merge_raises is not None and system == prompts.MERGE_SYSTEM:
            raise merge_raises
        status = statuses.get(system, 200)
        if status != 200:
            return status, "error"
        if system == prompts.SUMMARY_SYSTEM:
            data = {
                "patient_script": (
                    "I have felt tired for a few days. I would like "
                    "to know why."
                ),
                "priority_questions": ["What could be causing this tiredness?"],
            }
        else:
            data = _minimal_record()
        return 200, json.dumps(
            {"choices": [{"message": {"content": json.dumps(data)}}]}
        )

    monkeypatch.setattr("core.llm._post", fake_post)
    monkeypatch.setattr("core.llm._sleep", lambda seconds: None)
    return calls


def _to_merged_step3(monkeypatch, tmp_path, **fake_kwargs):
    """A fresh session brought to merged step 3 (extract + merge done)."""
    calls = _setup(monkeypatch, tmp_path, **fake_kwargs)
    state = new_state()
    state = handlers.on_continue(state, STORY, "", None)
    state = handlers.on_answer(state, "Mild.")
    state = handlers.on_answer(state, "Two days ago.")
    state = handlers.on_answer(state, "Two days.")
    state = handlers.on_skip(state)
    state = handlers.on_skip(state)
    assert state["step"] == 3
    state = handlers.enter_review(state)
    assert state["merged"] is True
    return calls, state


def test_happy_path_makes_three_model_calls_in_order(monkeypatch, tmp_path):
    calls = _setup(monkeypatch, tmp_path)
    state = new_state()
    state = handlers.on_continue(state, STORY, "", None)
    assert state["step"] == 2
    assert calls == [prompts.EXTRACT_SYSTEM]
    state = handlers.on_answer(state, "Mild.")
    state = handlers.on_answer(state, "Two days ago.")
    state = handlers.on_answer(state, "Two days.")
    state = handlers.on_skip(state)
    state = handlers.on_skip(state)
    assert state["step"] == 3
    state = handlers.enter_review(state)
    assert state["merged"] is True
    assert state["error"] is None
    assert calls == [prompts.EXTRACT_SYSTEM, prompts.MERGE_SYSTEM]
    state = handlers.on_summarize(state)
    assert state["step"] == 4
    assert state["error"] is None
    assert state["summary"] is not None
    assert state["summary"]["patient_script"]
    assert state["summary"]["priority_questions"]
    assert calls == [
        prompts.EXTRACT_SYSTEM,
        prompts.MERGE_SYSTEM,
        prompts.SUMMARY_SYSTEM,
    ]


def test_summary_server_error_keeps_details_and_stays_on_step3(
    monkeypatch, tmp_path
):
    _calls, state = _to_merged_step3(
        monkeypatch, tmp_path, statuses={prompts.SUMMARY_SYSTEM: 500}
    )
    original = state["record"]
    result = handlers.on_summarize(state)
    assert result["step"] == 3
    assert result["summary"] is None
    assert result["record"] == original
    assert result["error"] == (
        "The AI service had a problem. Your details are kept. "
        "Press Write my summary to try again."
    )


def test_summary_quota_error_keeps_details_and_stays_on_step3(
    monkeypatch, tmp_path
):
    _calls, state = _to_merged_step3(
        monkeypatch, tmp_path, statuses={prompts.SUMMARY_SYSTEM: 429}
    )
    original = state["record"]
    result = handlers.on_summarize(state)
    assert result["step"] == 3
    assert result["summary"] is None
    assert result["record"] == original
    assert result["error"] == (
        "The free AI quota for today may be used up. "
        "Please try again later. Your details are kept. "
        "Press Write my summary to try again."
    )


def test_summary_auth_error_keeps_details_and_has_no_retry(
    monkeypatch, tmp_path
):
    _calls, state = _to_merged_step3(
        monkeypatch, tmp_path, statuses={prompts.SUMMARY_SYSTEM: 401}
    )
    original = state["record"]
    result = handlers.on_summarize(state)
    assert result["step"] == 3
    assert result["summary"] is None
    assert result["record"] == original
    assert result["error"] == (
        "The AI service rejected the server's key. Your details are kept."
    )


def test_no_key_continue_keeps_text_and_shows_alert(monkeypatch, tmp_path):
    calls = _setup(monkeypatch, tmp_path, with_key=False)
    state = new_state()
    result = handlers.on_continue(state, "I fainted this morning.", "", None)
    assert result["step"] == 1
    assert result["record"] is None
    assert result["error"] == NOT_CONFIGURED + " Your text is kept."
    assert calls == []
    assert len(result["alerts"]) == 1
    assert result["alerts"][0]["code"] == "altered_consciousness"
    assert result["alerts"][0]["level"] == "urgent"


def test_no_key_config_problem_and_preview(monkeypatch, tmp_path):
    _setup(monkeypatch, tmp_path, with_key=False)
    assert backend.config_problem() == NOT_CONFIGURED
    monkeypatch.setattr(backend, "PREVIEW", True)
    assert backend.config_problem() is None


def test_unexpected_error_in_merge_shows_generic_message(monkeypatch, tmp_path):
    calls = _setup(
        monkeypatch, tmp_path, merge_raises=RuntimeError("boom")
    )
    state = new_state()
    state = handlers.on_continue(state, STORY, "", None)
    state = handlers.on_answer(state, "Mild.")
    assert state["step"] == 2
    state = handlers.on_finish(state)
    assert state["step"] == 3
    original = state["record"]
    state = handlers.enter_review(state)
    assert state["merged"] is True
    assert state["step"] == 3
    assert state["record"] == original
    assert state["error"] == (
        "Something went wrong on our side. Your information is kept. "
        "Please try again."
    )
    assert calls == [prompts.EXTRACT_SYSTEM, prompts.MERGE_SYSTEM]


def test_two_states_never_share_record_alerts_asked_or_skipped(
    monkeypatch, tmp_path
):
    _setup(monkeypatch, tmp_path)
    state_a = handlers.on_continue(new_state(), STORY, "", None)
    state_b = handlers.on_continue(
        new_state(),
        "I have had a mild sore throat for two days.",
        "",
        None,
    )
    assert state_a["step"] == 2
    assert state_b["step"] == 2
    assert state_a["record"] is not state_b["record"]
    state_a["asked"].append(
        {"question": "How bad is it: mild, moderate or severe?", "answer": "Mild."}
    )
    state_a["skipped"].append({"question": "When did it start?", "position": 2})
    state_a["alerts"].append({"code": "x", "message": "m", "level": "attention"})
    state_a["record"]["complaint"] = "changed"
    assert state_b["asked"] == []
    assert state_b["skipped"] == []
    assert state_b["alerts"] == []
    assert state_b["record"]["complaint"] == "I have felt tired for a few days."
