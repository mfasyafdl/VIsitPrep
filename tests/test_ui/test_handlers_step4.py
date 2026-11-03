"""Tests for ui/handlers.py (step 4: summary, back, reset) with a faked
backend. No network is used. All data is neutral and fictional.
"""

import copy

from core import fixtures
from core.llm import LLMNetworkError
from core.schema import (
    PatientRecord,
    QuestionAnswer,
    SummaryOutput,
    record_to_dict,
)

from ui import handlers
from ui.state import new_state

_NOT_READY = handlers._NOT_READY


class SummarizeServer:
    """Fake ui.backend.summarize that counts calls and records args."""

    def __init__(self, summary=None, error=None):
        self.summary = summary
        self.error = error
        self.calls = 0
        self.args = []

    def __call__(self, record, asked, story):
        self.calls += 1
        self.args.append((record, asked, story))
        if self.error is not None:
            raise self.error
        return self.summary


def _step3_state(record=None, merged=True, editing=None, asked=()):
    state = new_state()
    state["step"] = 3
    state["story"] = "My son has had a cough for five days."
    state["alert_texts"] = ["My son has had a cough for five days."]
    state["merged"] = merged
    state["editing"] = editing
    if record is None:
        record = fixtures.get_fixture("child_cough")
    state["record"] = record_to_dict(record)
    state["asked"] = [dict(qa) for qa in asked]
    return state


def _step4_state():
    state = _step3_state()
    state["step"] = 4
    state["summary"] = {
        "doctor_card": "Patient: 7 years old",
        "patient_script": "I am here about my son.",
        "priority_questions": ["Should he stay home from school?"],
    }
    state["pdf_path"] = "/tmp/example.pdf"
    return state


# on_summarize


def test_on_summarize_calls_backend_once_and_goes_to_step4(monkeypatch):
    record = fixtures.get_fixture("child_cough")
    asked = (
        {"question": "How bad is it: mild, moderate or severe?", "answer": "Mild."},
        {"question": "How long has it been going on?", "answer": "Five days."},
    )
    summary = SummaryOutput(
        doctor_card="Patient: 7 years old, male\nProblem: a cough for five days",
        patient_script="I am here about my son and his cough.",
        priority_questions=["Should he stay home from school?"],
    )
    server = SummarizeServer(summary=summary)
    monkeypatch.setattr("ui.backend.summarize", server)
    state = _step3_state(record=record, asked=asked)
    result = handlers.on_summarize(state)
    assert server.calls == 1
    sent_record, sent_asked, sent_story = server.args[0]
    assert isinstance(sent_record, PatientRecord)
    assert sent_record == record
    assert sent_asked == [
        QuestionAnswer("How bad is it: mild, moderate or severe?", "Mild."),
        QuestionAnswer("How long has it been going on?", "Five days."),
    ]
    assert all(isinstance(qa, QuestionAnswer) for qa in sent_asked)
    assert sent_story == "My son has had a cough for five days."
    assert result["step"] == 4
    assert result["error"] is None
    assert result["summary"] == {
        "doctor_card": "Patient: 7 years old, male\nProblem: a cough for five days",
        "patient_script": "I am here about my son and his cough.",
        "priority_questions": ["Should he stay home from school?"],
    }
    assert result["summary"]["priority_questions"] is not (
        summary.priority_questions
    )
    assert result["token"] == state["token"] + 1


def test_on_summarize_with_open_editor_sets_error_and_skips_backend(monkeypatch):
    server = SummarizeServer(summary=SummaryOutput("a", "b", []))
    monkeypatch.setattr("ui.backend.summarize", server)
    state = _step3_state(editing="allergies")
    result = handlers.on_summarize(state)
    assert server.calls == 0
    assert result["error"] == "Save or cancel your change first."
    assert result["step"] == 3
    assert result["summary"] is None
    assert result["token"] == state["token"] + 1


def test_on_summarize_unmerged_or_wrong_step_returns_state_unchanged(monkeypatch):
    server = SummarizeServer(summary=SummaryOutput("a", "b", []))
    monkeypatch.setattr("ui.backend.summarize", server)
    unmerged = _step3_state(merged=False)
    assert handlers.on_summarize(unmerged) is unmerged
    step2 = _step3_state()
    step2["step"] = 2
    assert handlers.on_summarize(step2) is step2
    step4 = _step4_state()
    assert handlers.on_summarize(step4) is step4
    assert server.calls == 0


def test_on_summarize_network_error_stays_on_step3(monkeypatch):
    server = SummarizeServer(
        error=LLMNetworkError("The AI service did not respond.")
    )
    monkeypatch.setattr("ui.backend.summarize", server)
    state = _step3_state()
    original = copy.deepcopy(state)
    result = handlers.on_summarize(state)
    assert result["step"] == 3
    assert result["summary"] is None
    assert result["error"].endswith(
        "Press Write my summary to try again."
    )
    assert result["error"] == (
        "The AI service did not respond. Your details are kept. "
        "Press Write my summary to try again."
    )
    assert result["record"] == original["record"]


def test_on_summarize_not_implemented_sets_not_ready(monkeypatch):
    server = SummarizeServer(
        error=NotImplementedError("generate_summary is not implemented yet")
    )
    monkeypatch.setattr("ui.backend.summarize", server)
    state = _step3_state()
    result = handlers.on_summarize(state)
    assert result["step"] == 3
    assert result["summary"] is None
    assert result["error"] == _NOT_READY


# on_change_details


def test_on_change_details_goes_back_to_step3_without_remerge():
    state = _step4_state()
    result = handlers.on_change_details(state)
    assert result["step"] == 3
    assert result["summary"] is None
    assert result["pdf_path"] is None
    assert result["editing"] is None
    assert result["error"] is None
    assert result["merged"] is True
    assert result["record"] == state["record"]
    assert result["token"] == state["token"] + 1


def test_on_change_details_does_nothing_on_other_steps():
    state = _step3_state()
    assert handlers.on_change_details(state) is state
    state2 = new_state()
    state2["step"] = 2
    assert handlers.on_change_details(state2) is state2


# on_reset


def test_on_reset_returns_a_fresh_state_from_every_step():
    for step in (1, 2, 3, 4):
        state = new_state()
        state["step"] = step
        state["story"] = "something typed"
        state["token"] = 9
        assert handlers.on_reset(state) == new_state()


# no mutation


def test_step4_handlers_never_mutate_the_input_state(monkeypatch):
    server = SummarizeServer(
        summary=SummaryOutput("a", "b", ["Should he stay home from school?"])
    )
    monkeypatch.setattr("ui.backend.summarize", server)

    state = _step3_state(
        asked=[
            {"question": "How bad is it: mild, moderate or severe?", "answer": "Mild."}
        ]
    )
    original = copy.deepcopy(state)
    handlers.on_summarize(state)
    assert state == original

    state = _step3_state(editing="allergies")
    original = copy.deepcopy(state)
    handlers.on_summarize(state)
    assert state == original

    state = _step4_state()
    original = copy.deepcopy(state)
    handlers.on_change_details(state)
    assert state == original

    state = _step4_state()
    original = copy.deepcopy(state)
    handlers.on_reset(state)
    assert state == original
