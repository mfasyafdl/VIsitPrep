"""Tests for ui/handlers.py (step 3 review) with a faked backend and core.

ui.backend.merge and core.redflag are faked with monkeypatch; no network
is used. All data is neutral and fictional.
"""

import copy

from core import fixtures
from core.llm import LLMNetworkError
from core.schema import (
    Medicine,
    PatientRecord,
    QuestionAnswer,
    record_from_dict,
    record_to_dict,
)

from ui import handlers
from ui.state import new_state

_NOT_READY = handlers._NOT_READY


class MergeServer:
    """Fake ui.backend.merge that counts calls and records arguments."""

    def __init__(self, record=None, error=None):
        self.record = record
        self.error = error
        self.calls = 0
        self.args = []

    def __call__(self, record, asked):
        self.calls += 1
        self.args.append((record, asked))
        if self.error is not None:
            raise self.error
        return self.record


def _fake_redflag(monkeypatch, scan_result=(), check_result=(), log=None):
    def fake_scan(*texts):
        if log is not None:
            log.append(("scan_text", texts))
        return list(scan_result)

    def fake_check(record):
        if log is not None:
            log.append(("check_alerts", record))
        return list(check_result)

    monkeypatch.setattr("core.redflag.scan_text", fake_scan)
    monkeypatch.setattr("core.redflag.check_alerts", fake_check)


def _step3_state(record=None, merged=True, editing=None, asked=()):
    state = new_state()
    state["step"] = 3
    state["story"] = "I feel run down."
    state["alert_texts"] = ["I feel run down."]
    state["merged"] = merged
    state["editing"] = editing
    if record is None:
        record = fixtures.get_fixture("fever_adult")
    state["record"] = record_to_dict(record)
    state["asked"] = [dict(qa) for qa in asked]
    return state


# enter_review


def test_enter_review_calls_merge_once_with_question_answers(monkeypatch):
    record = fixtures.get_fixture("fever_adult")
    asked = (
        {"question": "How bad is it?", "answer": "Mild."},
        {"question": "When did it start?", "answer": "Tuesday."},
    )
    server = MergeServer(record=record)
    monkeypatch.setattr("ui.backend.merge", server)
    _fake_redflag(monkeypatch)
    state = _step3_state(record=record, merged=False, asked=asked)
    result = handlers.enter_review(state)
    assert server.calls == 1
    sent_record, sent_asked = server.args[0]
    assert isinstance(sent_record, PatientRecord)
    assert sent_asked == [
        QuestionAnswer("How bad is it?", "Mild."),
        QuestionAnswer("When did it start?", "Tuesday."),
    ]
    assert all(isinstance(qa, QuestionAnswer) for qa in sent_asked)
    assert result["merged"] is True
    assert result["record"] == record_to_dict(record)
    assert result["error"] is None
    second = handlers.enter_review(result)
    assert server.calls == 1
    assert second["record"] == record_to_dict(record)


def test_enter_review_does_nothing_on_step2(monkeypatch):
    server = MergeServer(record=fixtures.get_fixture("fever_adult"))
    monkeypatch.setattr("ui.backend.merge", server)
    _fake_redflag(monkeypatch)
    state = new_state()
    state["step"] = 2
    state["record"] = record_to_dict(fixtures.get_fixture("fever_adult"))
    assert handlers.enter_review(state) is state
    assert server.calls == 0


def test_enter_review_does_nothing_when_already_merged(monkeypatch):
    server = MergeServer(record=fixtures.get_fixture("fever_adult"))
    monkeypatch.setattr("ui.backend.merge", server)
    _fake_redflag(monkeypatch)
    state = _step3_state(merged=True)
    assert handlers.enter_review(state) is state
    assert server.calls == 0


def test_enter_review_llm_error_keeps_record_and_sets_error(monkeypatch):
    record = fixtures.get_fixture("fever_adult")
    server = MergeServer(
        error=LLMNetworkError("The AI service did not respond.")
    )
    monkeypatch.setattr("ui.backend.merge", server)
    _fake_redflag(monkeypatch)
    state = _step3_state(record=record, merged=False)
    original_record = state["record"]
    result = handlers.enter_review(state)
    assert result["record"] == original_record
    assert result["merged"] is True
    assert result["error"].endswith(
        "You can still check and change your details below."
    )
    assert result["error"] == (
        "The AI service did not respond. Your answers are kept. "
        "You can still check and change your details below."
    )


def test_enter_review_not_implemented_sets_not_ready(monkeypatch):
    record = fixtures.get_fixture("fever_adult")
    server = MergeServer(
        error=NotImplementedError("merge_answers is not implemented yet")
    )
    monkeypatch.setattr("ui.backend.merge", server)
    _fake_redflag(monkeypatch)
    state = _step3_state(record=record, merged=False)
    original_record = state["record"]
    result = handlers.enter_review(state)
    assert result["record"] == original_record
    assert result["merged"] is True
    assert result["error"] == _NOT_READY


def test_enter_review_recomputes_alerts_with_merged_record(monkeypatch):
    record = fixtures.get_fixture("fever_adult")
    server = MergeServer(record=record)
    monkeypatch.setattr("ui.backend.merge", server)
    log = []
    _fake_redflag(monkeypatch, log=log)
    state = _step3_state(record=record, merged=False)
    handlers.enter_review(state)
    scan_calls = [args for name, args in log if name == "scan_text"]
    check_calls = [args for name, args in log if name == "check_alerts"]
    assert check_calls
    assert check_calls[-1] == record
    assert scan_calls


# open_editor / cancel_editor


def test_open_editor_switches_and_cancel_closes(monkeypatch):
    _fake_redflag(monkeypatch)
    state = _step3_state()
    first = handlers.open_editor(state, "medicines")
    assert first["editing"] == "medicines"
    second = handlers.open_editor(first, "allergies")
    assert second["editing"] == "allergies"
    closed = handlers.cancel_editor(second)
    assert closed["editing"] is None
    assert closed["error"] is None


def test_open_editor_wrong_step_unmerged_or_unknown_section(monkeypatch):
    _fake_redflag(monkeypatch)
    step2 = new_state()
    step2["step"] = 2
    assert handlers.open_editor(step2, "allergies") is step2
    unmerged = _step3_state(merged=False)
    assert handlers.open_editor(unmerged, "allergies") is unmerged
    state = _step3_state()
    assert handlers.open_editor(state, "nope") is state


def test_cancel_editor_wrong_step_returns_state(monkeypatch):
    _fake_redflag(monkeypatch)
    step2 = new_state()
    step2["step"] = 2
    assert handlers.cancel_editor(step2) is step2


# editor_values


def test_editor_values_per_section():
    record = record_to_dict(fixtures.get_fixture("fever_adult"))
    assert handlers.editor_values(record, "problem") == {
        "complaint": record["complaint"],
        "symptoms": "fever\nheadache\ntemperature of 39 this morning",
    }
    assert handlers.editor_values(record, "timing") == {
        "onset": "yesterday morning",
        "duration": "about one day",
        "severity": "moderate",
    }
    assert handlers.editor_values(record, "medicines") == {
        "lines": "ginger tea, twice a day",
        "none": False,
    }
    assert handlers.editor_values(record, "allergies") == {
        "lines": "",
        "none": True,
    }
    assert handlers.editor_values(record, "history") == {
        "lines": "",
        "none": False,
    }
    assert handlers.editor_values(record, "concerns") == {"lines": ""}
    assert handlers.editor_values(record, "about") == {
        "age_text": "34",
        "sex": "female",
    }


def test_editor_values_empty_record_uses_not_sure_and_none():
    record = record_to_dict(fixtures.get_fixture("empty"))
    assert handlers.editor_values(record, "timing") == {
        "onset": "",
        "duration": "",
        "severity": "not-sure",
    }
    assert handlers.editor_values(record, "about") == {
        "age_text": "",
        "sex": None,
    }


def test_editor_values_medicine_without_frequency():
    record = fixtures.get_fixture("fever_adult")
    record.medicines = [
        Medicine("honey", "herbal", None, None, None, None)
    ]
    data = record_to_dict(record)
    assert handlers.editor_values(data, "medicines") == {
        "lines": "honey",
        "none": False,
    }


def test_editor_values_unknown_section_raises():
    import pytest

    record = record_to_dict(fixtures.get_fixture("fever_adult"))
    with pytest.raises(ValueError):
        handlers.editor_values(record, "nope")


# save_section: medicines


def _step3_with_medicines(medicines, editing="medicines"):
    record = fixtures.get_fixture("fever_adult")
    record.medicines = list(medicines)
    return _step3_state(record=record, editing=editing)


def test_save_medicines_new_name_with_frequency(monkeypatch):
    _fake_redflag(monkeypatch)
    state = _step3_with_medicines([])
    result = handlers.save_section(
        state, "medicines", {"lines": "Amlodipine, every morning", "none": False}
    )
    assert result["error"] is None
    assert result["record"]["medicines"] == [
        {
            "name": "Amlodipine",
            "medicine_type": "unknown",
            "dose": None,
            "frequency": "every morning",
            "duration": None,
            "notes": None,
        }
    ]


def test_save_medicines_existing_name_keeps_fields(monkeypatch):
    _fake_redflag(monkeypatch)
    state = _step3_with_medicines(
        [
            Medicine(
                name="Ginger tea",
                medicine_type="herbal",
                dose="one cup",
                frequency=None,
                duration="3 days",
                notes=None,
            )
        ]
    )
    result = handlers.save_section(
        state, "medicines", {"lines": "ginger tea, twice a day", "none": False}
    )
    assert result["error"] is None
    assert result["record"]["medicines"] == [
        {
            "name": "Ginger tea",
            "medicine_type": "herbal",
            "dose": "one cup",
            "frequency": "twice a day",
            "duration": "3 days",
            "notes": None,
        }
    ]


def test_save_medicines_existing_name_without_frequency_keeps_old(monkeypatch):
    _fake_redflag(monkeypatch)
    state = _step3_with_medicines(
        [
            Medicine(
                name="Ginger tea",
                medicine_type="herbal",
                dose="one cup",
                frequency="twice a day",
                duration=None,
                notes=None,
            )
        ]
    )
    result = handlers.save_section(
        state, "medicines", {"lines": "Ginger tea", "none": False}
    )
    assert result["record"]["medicines"] == [
        {
            "name": "Ginger tea",
            "medicine_type": "herbal",
            "dose": "one cup",
            "frequency": "twice a day",
            "duration": None,
            "notes": None,
        }
    ]


def test_save_medicines_empty_lines_ignored_and_no_comma(monkeypatch):
    _fake_redflag(monkeypatch)
    state = _step3_with_medicines([])
    result = handlers.save_section(
        state, "medicines", {"lines": "Paracetamol\n\n   \n", "none": False}
    )
    assert result["error"] is None
    assert result["record"]["medicines"] == [
        {
            "name": "Paracetamol",
            "medicine_type": "unknown",
            "dose": None,
            "frequency": None,
            "duration": None,
            "notes": None,
        }
    ]


# save_section: denied flags


def test_denied_tick_with_empty_list_sets_true(monkeypatch):
    _fake_redflag(monkeypatch)
    record = fixtures.get_fixture("fever_adult")
    state = _step3_state(record=record, editing="allergies")
    result = handlers.save_section(
        state, "allergies", {"lines": "", "none": True}
    )
    assert result["record"]["allergies"] == []
    assert result["record"]["allergies_denied"] is True

    state = _step3_with_medicines([])
    result = handlers.save_section(
        state, "medicines", {"lines": "", "none": True}
    )
    assert result["record"]["medicines"] == []
    assert result["record"]["medicines_denied"] is True

    state = _step3_state(record=record, editing="history")
    result = handlers.save_section(
        state, "history", {"lines": "", "none": True}
    )
    assert result["record"]["medical_history"] == []
    assert result["record"]["medical_history_denied"] is True


def test_denied_untick_with_empty_list_sets_none_not_false(monkeypatch):
    _fake_redflag(monkeypatch)
    record = fixtures.get_fixture("fever_adult")
    state = _step3_state(record=record, editing="allergies")
    result = handlers.save_section(
        state, "allergies", {"lines": "", "none": False}
    )
    assert result["record"]["allergies_denied"] is None

    state = _step3_with_medicines([])
    result = handlers.save_section(
        state, "medicines", {"lines": "", "none": False}
    )
    assert result["record"]["medicines_denied"] is None

    state = _step3_state(record=record, editing="history")
    result = handlers.save_section(
        state, "history", {"lines": "", "none": False}
    )
    assert result["record"]["medical_history_denied"] is None


def test_denied_tick_with_items_sets_error_and_keeps_record(monkeypatch):
    _fake_redflag(monkeypatch)
    record = fixtures.get_fixture("fever_adult")

    state = _step3_with_medicines(
        [Medicine("ginger tea", "herbal", None, "twice a day", None, None)]
    )
    result = handlers.save_section(
        state, "medicines", {"lines": "Ibuprofen", "none": True}
    )
    assert result["error"] == "Remove the items, or untick the box."
    assert result["record"] == state["record"]
    assert result["editing"] == "medicines"

    state = _step3_state(record=record, editing="allergies")
    result = handlers.save_section(
        state, "allergies", {"lines": "peanuts", "none": True}
    )
    assert result["error"] == "Remove the items, or untick the box."
    assert result["record"] == state["record"]

    state = _step3_state(record=record, editing="history")
    result = handlers.save_section(
        state, "history", {"lines": "asthma", "none": True}
    )
    assert result["error"] == "Remove the items, or untick the box."
    assert result["record"] == state["record"]


# save_section: timing and about


def test_save_timing_not_sure_severity_and_note_kept(monkeypatch):
    _fake_redflag(monkeypatch)
    record = fixtures.get_fixture("child_cough")
    state = _step3_state(record=record, editing="timing")
    result = handlers.save_section(
        state,
        "timing",
        {"onset": "five days ago", "duration": "five days", "severity": "not-sure"},
    )
    assert result["error"] is None
    assert result["record"]["severity"] is None
    assert result["record"]["severity_note"] == "He is still playing and eating."
    assert result["record"]["onset"] == "five days ago"
    assert result["record"]["duration"] == "five days"
    assert "severity" in result["record"]["missing_information"]


def test_save_timing_clears_severity_text_and_kept_level(monkeypatch):
    _fake_redflag(monkeypatch)
    record = fixtures.get_fixture("child_cough")
    state = _step3_state(record=record, editing="timing")
    result = handlers.save_section(
        state, "timing", {"onset": "", "duration": "", "severity": "mild"}
    )
    assert result["record"]["onset"] is None
    assert result["record"]["duration"] is None
    assert result["record"]["severity"] == "mild"


def test_save_about_empty_age_and_no_sex_keeps_reporter(monkeypatch):
    _fake_redflag(monkeypatch)
    record = fixtures.get_fixture("fever_adult")
    record.reporting_on_behalf = True
    record.reporter_relationship = "mother"
    state = _step3_state(record=record, editing="about")
    result = handlers.save_section(
        state, "about", {"age_text": "   ", "sex": None}
    )
    assert result["error"] is None
    assert result["record"]["patient_age"] is None
    assert result["record"]["patient_age_text"] is None
    assert result["record"]["patient_sex"] is None
    assert result["record"]["reporting_on_behalf"] is True
    assert result["record"]["reporter_relationship"] == "mother"
    assert "age" in result["record"]["missing_information"]
    assert "sex" in result["record"]["missing_information"]


# save_section: success side effects


def test_save_success_side_effects(monkeypatch):
    log = []
    _fake_redflag(monkeypatch, log=log)
    record = fixtures.get_fixture("fever_adult")
    state = _step3_state(record=record, editing="problem")
    state["summary"] = {
        "doctor_card": "x",
        "patient_script": "y",
        "priority_questions": [],
    }
    state["pdf_path"] = "/tmp/example.pdf"
    state["token"] = 7
    values = {
        "complaint": "I have had a fever and a headache since yesterday.",
        "symptoms": "fever\nheadache\ntemperature of 39 this morning\nsore eyes",
    }
    result = handlers.save_section(state, "problem", values)
    assert result["summary"] is None
    assert result["pdf_path"] is None
    assert result["editing"] is None
    assert result["error"] is None
    assert result["token"] == 8
    assert result["record"]["symptoms"] == [
        "fever",
        "headache",
        "temperature of 39 this morning",
        "sore eyes",
    ]
    assert "concerns" in result["record"]["missing_information"]
    assert result["alert_texts"][:1] == ["I feel run down."]
    assert "sore eyes" in result["alert_texts"]
    scan_calls = [args for name, args in log if name == "scan_text"]
    assert scan_calls[-1] == tuple(result["alert_texts"])
    check_calls = [args for name, args in log if name == "check_alerts"]
    assert check_calls[-1] == record_from_dict(result["record"])

    reopened = handlers.open_editor(result, "problem")
    again = handlers.save_section(reopened, "problem", values)
    assert again["alert_texts"] == result["alert_texts"]


def test_save_section_not_open_returns_unchanged(monkeypatch):
    _fake_redflag(monkeypatch)
    values = {"complaint": "a mild cough", "symptoms": ""}
    state = _step3_state(editing=None)
    assert handlers.save_section(state, "problem", values) is state
    state = _step3_state(editing="allergies")
    assert handlers.save_section(state, "problem", values) is state
    state = _step3_state(editing="problem", merged=False)
    assert handlers.save_section(state, "problem", values) is state
    state = _step3_state(editing="problem")
    state["step"] = 2
    assert handlers.save_section(state, "problem", values) is state


# no mutation


def test_step3_handlers_never_mutate_the_input_state(monkeypatch):
    record = fixtures.get_fixture("fever_adult")
    server = MergeServer(record=record)
    monkeypatch.setattr("ui.backend.merge", server)
    _fake_redflag(monkeypatch)

    state = _step3_state(
        record=record,
        merged=False,
        asked=[{"question": "How bad is it?", "answer": "Mild."}],
    )
    original = copy.deepcopy(state)
    handlers.enter_review(state)
    assert state == original

    state = _step3_state()
    original = copy.deepcopy(state)
    handlers.open_editor(state, "medicines")
    assert state == original

    state = _step3_state(editing="allergies")
    original = copy.deepcopy(state)
    handlers.cancel_editor(state)
    assert state == original

    state = _step3_state(editing="problem")
    original = copy.deepcopy(state)
    handlers.save_section(
        state, "problem", {"complaint": "new words", "symptoms": "x"}
    )
    assert state == original

    state = _step3_state(editing="allergies")
    original = copy.deepcopy(state)
    handlers.save_section(state, "allergies", {"lines": "peanuts", "none": True})
    assert state == original

    state = _step3_state(editing=None)
    original = copy.deepcopy(state)
    handlers.save_section(
        state, "problem", {"complaint": "a mild cough", "symptoms": ""}
    )
    assert state == original
