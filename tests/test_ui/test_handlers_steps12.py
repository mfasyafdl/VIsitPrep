"""Tests for ui/handlers.py (steps 1-2) and ui/backend.py preview mode.

The core functions (core.redflag, core.interview, core.extract) and
ui.backend are faked with monkeypatch; no network is used.
"""

import copy

from core import fixtures
from core.llm import LLMNetworkError
from core.schema import Alert, record_to_dict

import ui.backend as backend
from ui import handlers
from ui.state import new_state


class QuestionServer:
    """Fake core.interview.next_question that counts its calls."""

    def __init__(self, questions):
        self.questions = list(questions)
        self.calls = 0

    def __call__(self, record, asked, skipped, max_questions=5):
        self.calls += 1
        index = self.calls - 1
        if index < len(self.questions):
            return self.questions[index]
        return None


def _fake_redflag(monkeypatch, scan_result, check_result=None,
                  check_raises=False, log=None):
    def fake_scan(*texts):
        if log is not None:
            log.append("scan_text")
        return list(scan_result)

    def fake_check(record):
        if log is not None:
            log.append("check_alerts")
        if check_raises:
            raise RuntimeError("alert check failed")
        return list(check_result or [])

    monkeypatch.setattr("core.redflag.scan_text", fake_scan)
    monkeypatch.setattr("core.redflag.check_alerts", fake_check)


def _fake_extract(monkeypatch, record=None, error=None, log=None):
    def fake_extract(story, details):
        if log is not None:
            log.append("extract")
        if error is not None:
            raise error
        return record

    monkeypatch.setattr("ui.backend.extract", fake_extract)


def _step1_state():
    return new_state()


def _step2_state(record=None, question="What started it?"):
    state = new_state()
    state["step"] = 2
    state["story"] = "I feel unwell."
    state["alert_texts"] = ["I feel unwell."]
    if record is None:
        record = fixtures.get_fixture("fever_adult")
    state["record"] = record_to_dict(record)
    state["question"] = question
    return state


# AC1


def test_recompute_alerts_runs_before_extract(monkeypatch):
    log = []
    record = fixtures.get_fixture("fever_adult")
    _fake_redflag(monkeypatch, [Alert("a", "m", "attention")], log=log)
    _fake_extract(monkeypatch, record=record, log=log)
    server = QuestionServer(["Q1"])
    monkeypatch.setattr("core.interview.next_question", server)
    handlers.on_continue(_step1_state(), "I feel unwell.", "", None)
    assert log.index("scan_text") < log.index("extract")


def test_extract_llm_error_keeps_story_and_stays_on_step1(monkeypatch):
    record = fixtures.get_fixture("fever_adult")
    _fake_redflag(
        monkeypatch,
        [Alert("a", "Watch this", "attention")],
    )
    _fake_extract(
        monkeypatch,
        record=record,
        error=LLMNetworkError("The AI service did not respond."),
    )
    server = QuestionServer(["Q1"])
    monkeypatch.setattr("core.interview.next_question", server)
    result = handlers.on_continue(_step1_state(), "I feel unwell.", "34", "female")
    assert result["step"] == 1
    assert result["story"] == "I feel unwell."
    assert result["details"] == {
        "patient_age": 34,
        "patient_age_text": "34",
        "patient_sex": "female",
    }
    assert result["alerts"] == [{"code": "a", "message": "Watch this", "level": "attention"}]
    assert result["record"] is None
    assert server.calls == 0
    assert result["error"].endswith("Press Continue to try again.")
    assert result["error"] == (
        "The AI service did not respond. Your text is kept. "
        "Press Continue to try again."
    )


def test_three_answers_two_skips_end_on_step3_without_sixth_call(monkeypatch):
    record = fixtures.get_fixture("fever_adult")
    _fake_redflag(monkeypatch, [])
    _fake_extract(monkeypatch, record=record)
    server = QuestionServer(["Q1", "Q2", "Q3", "Q4", "Q5"])
    monkeypatch.setattr("core.interview.next_question", server)
    state = handlers.on_continue(_step1_state(), "I feel unwell.", "", None)
    assert state["step"] == 2
    assert state["question"] == "Q1"
    state = handlers.on_answer(state, "Since Monday.")
    state = handlers.on_answer(state, "It is mild.")
    state = handlers.on_skip(state)
    state = handlers.on_answer(state, "No medicines.")
    state = handlers.on_skip(state)
    assert state["step"] == 3
    assert state["question"] is None
    assert server.calls == 5
    assert len(state["asked"]) == 3
    assert len(state["skipped"]) == 2
    assert [entry["position"] for entry in state["skipped"]] == [3, 5]


def test_empty_answer_sets_error(monkeypatch):
    _fake_redflag(monkeypatch, [])
    server = QuestionServer(["Q1"])
    monkeypatch.setattr("core.interview.next_question", server)
    state = _step2_state()
    result = handlers.on_answer(state, "   ")
    assert result["error"] == "Type an answer, or press Skip this question."
    assert result["asked"] == []
    assert result["step"] == 2
    assert server.calls == 0


def test_empty_story_sets_error(monkeypatch):
    _fake_redflag(monkeypatch, [])
    _fake_extract(monkeypatch)
    server = QuestionServer(["Q1"])
    monkeypatch.setattr("core.interview.next_question", server)
    result = handlers.on_continue(_step1_state(), "   ", "", None)
    assert result["error"] == "Please describe your symptoms first."
    assert result["step"] == 1
    assert result["story"] == ""
    assert server.calls == 0


def test_wrong_step_calls_return_state_unchanged(monkeypatch):
    _fake_redflag(monkeypatch, [])
    _fake_extract(monkeypatch, record=fixtures.get_fixture("fever_adult"))
    server = QuestionServer(["Q1"])
    monkeypatch.setattr("core.interview.next_question", server)
    step1 = _step1_state()
    step2 = _step2_state()
    step3 = _step2_state()
    step3["step"] = 3
    assert handlers.on_continue(step2, "x", "", None) is step2
    assert handlers.on_continue(step3, "x", "", None) is step3
    assert handlers.on_answer(step1, "x") is step1
    assert handlers.on_answer(step3, "x") is step3
    assert handlers.on_skip(step1) is step1
    assert handlers.on_skip(step3) is step3
    assert handlers.on_finish(step1) is step1
    assert handlers.on_finish(step3) is step3
    assert server.calls == 0


def test_sex_none_when_not_chosen(monkeypatch):
    _fake_redflag(monkeypatch, [])
    _fake_extract(monkeypatch, record=fixtures.get_fixture("fever_adult"))
    server = QuestionServer(["Q1"])
    monkeypatch.setattr("core.interview.next_question", server)
    result = handlers.on_continue(_step1_state(), "I feel unwell.", "", None)
    assert result["details"]["patient_sex"] is None
    result = handlers.on_continue(_step1_state(), "I feel unwell.", "", "male")
    assert result["details"]["patient_sex"] == "male"


def test_age_empty_gives_none_and_none(monkeypatch):
    _fake_redflag(monkeypatch, [])
    _fake_extract(monkeypatch, record=fixtures.get_fixture("fever_adult"))
    server = QuestionServer(["Q1"])
    monkeypatch.setattr("core.interview.next_question", server)
    result = handlers.on_continue(_step1_state(), "I feel unwell.", "", None)
    assert result["details"]["patient_age"] is None
    assert result["details"]["patient_age_text"] is None


def test_age_34_gives_34_and_34(monkeypatch):
    _fake_redflag(monkeypatch, [])
    _fake_extract(monkeypatch, record=fixtures.get_fixture("fever_adult"))
    server = QuestionServer(["Q1"])
    monkeypatch.setattr("core.interview.next_question", server)
    result = handlers.on_continue(_step1_state(), "I feel unwell.", " 34 ", None)
    assert result["details"]["patient_age"] == 34
    assert result["details"]["patient_age_text"] == "34"


def test_age_not_a_number_keeps_text(monkeypatch):
    _fake_redflag(monkeypatch, [])
    _fake_extract(monkeypatch, record=fixtures.get_fixture("fever_adult"))
    server = QuestionServer(["Q1"])
    monkeypatch.setattr("core.interview.next_question", server)
    result = handlers.on_continue(_step1_state(), "I feel unwell.", "seven", None)
    assert result["details"]["patient_age"] is None
    assert result["details"]["patient_age_text"] == "seven"


def test_handlers_never_mutate_the_input_state(monkeypatch):
    record = fixtures.get_fixture("fever_adult")
    _fake_redflag(monkeypatch, [Alert("a", "m", "attention")])
    _fake_extract(monkeypatch, record=record)
    server = QuestionServer(["Q1", "Q2"])
    monkeypatch.setattr("core.interview.next_question", server)

    step1 = _step1_state()
    original = copy.deepcopy(step1)
    handlers.on_continue(step1, "I feel unwell.", "34", "female")
    assert step1 == original

    step1b = _step1_state()
    original = copy.deepcopy(step1b)
    handlers.on_continue(step1b, "   ", "", None)
    assert step1b == original

    step2 = _step2_state()
    original = copy.deepcopy(step2)
    handlers.on_answer(step2, "an answer")
    assert step2 == original

    step2b = _step2_state()
    original = copy.deepcopy(step2b)
    handlers.on_answer(step2b, "  ")
    assert step2b == original

    step2c = _step2_state()
    original = copy.deepcopy(step2c)
    handlers.on_skip(step2c)
    assert step2c == original

    step2d = _step2_state()
    original = copy.deepcopy(step2d)
    handlers.on_finish(step2d)
    assert step2d == original


# AC2


def test_recompute_alerts_keeps_previous_and_sets_error(monkeypatch):
    state = _step2_state()
    state["alerts"] = [
        {"code": "old", "message": "Old alert", "level": "attention"}
    ]
    _fake_redflag(
        monkeypatch,
        [Alert("new", "New alert", "attention")],
        check_raises=True,
    )
    result = handlers.recompute_alerts(state)
    assert result["alerts_error"] is True
    assert result["alerts"] == [
        {"code": "old", "message": "Old alert", "level": "attention"}
    ]


def test_recompute_alerts_dedups_same_code(monkeypatch):
    state = _step2_state()
    _fake_redflag(
        monkeypatch,
        [Alert("x", "first", "attention")],
        check_result=[Alert("x", "second", "urgent"), Alert("y", "other", "urgent")],
    )
    result = handlers.recompute_alerts(state)
    assert result["alerts_error"] is False
    assert result["alerts"] == [
        {"code": "y", "message": "other", "level": "urgent"},
        {"code": "x", "message": "first", "level": "attention"},
    ]


def test_recompute_alerts_sorts_urgent_first_then_code(monkeypatch):
    state = _step1_state()
    state["alert_texts"] = ["text"]
    _fake_redflag(
        monkeypatch,
        [
            Alert("b", "mb", "attention"),
            Alert("a", "ma", "urgent"),
        ],
    )
    result = handlers.recompute_alerts(state)
    assert [alert["code"] for alert in result["alerts"]] == ["a", "b"]


# AC3


def test_append_chip_three_cases():
    assert handlers.append_chip("", "It started…") == "It started…"
    assert (
        handlers.append_chip("I am tired.", "It feels…")
        == "I am tired.\nIt feels…"
    )
    assert (
        handlers.append_chip("I am tired", "It feels…") == "I am tired It feels…"
    )


def test_append_chip_never_replaces_text():
    text = "I am tired."
    result = handlers.append_chip(text, "It feels…")
    assert result.startswith(text)
    text2 = "I am tired"
    result2 = handlers.append_chip(text2, "It feels…")
    assert result2.startswith(text2)


# AC4


def _preview(monkeypatch):
    monkeypatch.setattr(backend, "PREVIEW", True)


def test_preview_extract_matches_each_fixture_story(monkeypatch):
    _preview(monkeypatch)
    for name, story in fixtures.FIXTURE_STORIES.items():
        record = backend.extract(story, None)
        expected = fixtures.get_fixture(name)
        assert record.complaint == expected.complaint
        padded = "  " + story.replace(" ", "  ") + "\n "
        padded_record = backend.extract(padded, None)
        assert padded_record.complaint == expected.complaint


def test_preview_extract_unknown_story_gives_chest_pain(monkeypatch):
    _preview(monkeypatch)
    record = backend.extract("A story nobody has heard before.", None)
    expected = fixtures.get_fixture("chest_pain")
    assert record.complaint == expected.complaint


def test_preview_extract_age_override(monkeypatch):
    _preview(monkeypatch)
    story = fixtures.FIXTURE_STORIES["child_cough"]
    record = backend.extract(
        story, {"patient_age": 40, "patient_age_text": "40", "patient_sex": None}
    )
    assert record.patient_age == 40
    assert record.patient_age_text == "40"
    assert record.patient_sex == "male"
    assert "age" not in record.missing_information


def test_preview_extract_returns_copies(monkeypatch):
    _preview(monkeypatch)
    story = fixtures.FIXTURE_STORIES["child_cough"]
    first = backend.extract(story, None)
    first.patient_age = 99
    first.symptoms.append("mutated")
    second = backend.extract(story, None)
    assert second.patient_age == 7
    assert "mutated" not in second.symptoms


def test_preview_summarize_returns_matching_summary(monkeypatch):
    _preview(monkeypatch)
    record = fixtures.get_fixture("fever_adult")
    for name, story in fixtures.FIXTURE_STORIES.items():
        summary = backend.summarize(record, [], story)
        expected = fixtures.get_summary(name)
        assert summary.doctor_card == expected.doctor_card
        assert summary.patient_script == expected.patient_script
        assert summary.priority_questions == expected.priority_questions


def test_preview_merge_returns_copies(monkeypatch):
    _preview(monkeypatch)
    record = fixtures.get_fixture("fever_adult")
    merged = backend.merge(record, [])
    assert merged is not record
    merged.patient_age = 99
    assert record.patient_age == 34
    assert merged.patient_age == 99


def test_full_step1_success_goes_to_step2(monkeypatch):
    record = fixtures.get_fixture("fever_adult")
    _fake_redflag(monkeypatch, [Alert("a", "m", "attention")])
    _fake_extract(monkeypatch, record=record)
    server = QuestionServer(["What started it?"])
    monkeypatch.setattr("core.interview.next_question", server)
    state = handlers.on_continue(_step1_state(), "I feel unwell.", "", None)
    assert state["step"] == 2
    assert state["question"] == "What started it?"
    assert state["error"] is None
    assert state["record"]["complaint"] == record.complaint
    assert state["asked"] == []
    assert state["skipped"] == []
    assert state["alerts"] == [{"code": "a", "message": "m", "level": "attention"}]
    assert state["token"] == 1
