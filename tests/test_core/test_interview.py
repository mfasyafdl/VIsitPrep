"""Tests for core.interview.next_question (task P1-5a)."""

from core.fixtures import get_fixture
from core.interview import next_question
from core.schema import (
    Medicine,
    QuestionAnswer,
    empty_record,
    record_to_dict,
)

SEVERITY = "How bad is it: mild, moderate or severe?"
ONSET = "When did it start?"
DURATION = "How long has it been going on?"
MEDICINES_SELF = (
    "Are you taking any medicines, herbal remedies or supplements? "
    "Please name them."
)
MEDICINES_ON_BEHALF = (
    "Is the patient taking any medicines, herbal remedies or supplements? "
    "Please name them."
)
ALLERGIES_ON_BEHALF = "Does the patient have any allergies?"
HISTORY_SELF = "Do you have any ongoing or past health conditions?"
HISTORY_ON_BEHALF = "Does the patient have any ongoing or past health conditions?"


def test_empty_record_asks_severity():
    assert next_question(get_fixture("empty"), [], []) == SEVERITY


def test_fever_adult_asks_medical_history():
    assert next_question(get_fixture("fever_adult"), [], []) == HISTORY_SELF


def test_child_cough_asks_on_behalf_medicines():
    assert next_question(get_fixture("child_cough"), [], []) == MEDICINES_ON_BEHALF


def test_chest_pain_asks_severity():
    assert next_question(get_fixture("chest_pain"), [], []) == SEVERITY


def test_already_asked_question_is_not_asked_again():
    asked = [QuestionAnswer("  " + SEVERITY.casefold() + "  ", "severe")]
    assert next_question(get_fixture("empty"), asked, []) == ONSET


def test_already_skipped_question_is_not_asked_again():
    asked = [QuestionAnswer(SEVERITY, "mild")]
    skipped = ["  " + ONSET.casefold() + "  "]
    assert next_question(get_fixture("empty"), asked, skipped) == DURATION


def test_asked_and_skipped_normalized_together():
    asked = [QuestionAnswer(SEVERITY.upper(), "moderate")]
    skipped = ["when did it start?"]
    assert next_question(get_fixture("empty"), asked, skipped) == DURATION


def test_budget_exhausted_returns_none():
    asked = [
        QuestionAnswer(SEVERITY, "mild"),
        QuestionAnswer(ONSET, "yesterday"),
        QuestionAnswer(DURATION, "one day"),
    ]
    skipped = [MEDICINES_SELF, ALLERGIES_ON_BEHALF]
    assert next_question(get_fixture("empty"), asked, skipped) is None


def test_zero_budget_returns_none():
    assert next_question(get_fixture("empty"), [], [], max_questions=0) is None


def test_child_cough_after_three_questions_returns_none():
    asked = [
        QuestionAnswer(MEDICINES_ON_BEHALF, "no"),
        QuestionAnswer(ALLERGIES_ON_BEHALF, "no"),
        QuestionAnswer(HISTORY_ON_BEHALF, "no"),
    ]
    assert next_question(get_fixture("child_cough"), asked, []) is None


def _fully_known_record() -> "object":
    record = empty_record()
    record.patient_age = 30
    record.patient_age_text = "30"
    record.patient_sex = "female"
    record.onset = "yesterday"
    record.duration = "one day"
    record.severity = "mild"
    record.medicines = [
        Medicine(
            name="honey tea",
            medicine_type="herbal",
            dose=None,
            frequency="once a day",
            duration=None,
            notes=None,
        )
    ]
    record.allergies = ["peanuts"]
    record.medical_history = ["asthma as a child"]
    record.concerns = ["is this serious?"]
    return record


def test_fully_known_record_returns_none():
    assert next_question(_fully_known_record(), [], []) is None


def test_stale_missing_information_is_ignored():
    record = get_fixture("empty")
    record.missing_information = []
    assert next_question(record, [], []) == SEVERITY


def test_inputs_are_not_mutated():
    record = get_fixture("fever_adult")
    asked = [QuestionAnswer("Do you have any allergies?", "no")]
    skipped = [SEVERITY]
    record_before = record_to_dict(record)
    asked_before = [(item.question, item.answer) for item in asked]
    skipped_before = list(skipped)
    assert next_question(record, asked, skipped) == HISTORY_SELF
    assert record_to_dict(record) == record_before
    assert [(item.question, item.answer) for item in asked] == asked_before
    assert skipped == skipped_before
