"""Tests for core/fixtures.py (task P1-1c). All people and details are fictional."""

import pytest

from core.fixtures import (
    FIXTURE_CHILD_COUGH,
    FIXTURE_CHEST_PAIN,
    FIXTURE_FEVER_ADULT,
    FIXTURE_NAMES,
    FIXTURE_STORIES,
    FIXTURE_SUMMARIES,
    all_fixtures,
    get_fixture,
    get_summary,
    match_story,
)
from core.schema import (
    missing_fields,
    record_from_dict,
    record_to_dict,
    validate_record,
)

DOCTOR_CARD_LABELS = (
    "Patient",
    "Problem",
    "Started",
    "Duration",
    "Severity",
    "Symptoms",
    "Medicines",
    "Allergies",
    "Medical history",
    "Patient's concerns",
)


def test_all_fixtures_keys():
    assert list(all_fixtures()) == ["empty", *FIXTURE_NAMES]


def test_every_fixture_is_valid_and_round_trips():
    for name, record in all_fixtures().items():
        assert validate_record(record) == [], name
        assert record_from_dict(record_to_dict(record)) == record, name


def test_missing_information_matches_missing_fields():
    for name, record in all_fixtures().items():
        assert record.missing_information == missing_fields(record), name


def test_non_empty_fixtures_have_at_least_two_missing_fields():
    for name, record in all_fixtures().items():
        if name == "empty":
            continue
        assert len(record.missing_information) >= 2, name


def test_fever_adult_allergies_empty_and_denied():
    assert FIXTURE_FEVER_ADULT.allergies == []
    assert FIXTURE_FEVER_ADULT.allergies_denied is True


def test_child_cough_denied_flags_null_and_reported_on_behalf():
    assert FIXTURE_CHILD_COUGH.medicines_denied is None
    assert FIXTURE_CHILD_COUGH.allergies_denied is None
    assert FIXTURE_CHILD_COUGH.medical_history_denied is None
    assert FIXTURE_CHILD_COUGH.reporting_on_behalf is True


def test_story_and_summary_keys_match_fixture_names():
    assert set(FIXTURE_STORIES) == set(FIXTURE_SUMMARIES) == set(FIXTURE_NAMES)


def test_every_summary_has_valid_shape():
    for name, summary in FIXTURE_SUMMARIES.items():
        assert 1 <= len(summary.priority_questions) <= 3, name
        assert 5 <= len(summary.patient_script.split()) <= 120, name
        lines = summary.doctor_card.split("\n")
        assert len(lines) == 10, name
        for line, label in zip(lines, DOCTOR_CARD_LABELS):
            assert line.startswith(f"{label}: "), name


def test_get_fixture_returns_copies():
    first = get_fixture("chest_pain")
    first.symptoms.append("an extra symptom")
    second = get_fixture("chest_pain")
    assert "an extra symptom" not in second.symptoms
    assert "an extra symptom" not in FIXTURE_CHEST_PAIN.symptoms
    assert FIXTURE_CHEST_PAIN.symptoms == ["tight pain in my chest that comes and goes"]


def test_get_summary_returns_copies():
    first = get_summary("fever_adult")
    first.priority_questions.append("an extra question")
    second = get_summary("fever_adult")
    assert "an extra question" not in second.priority_questions
    assert "an extra question" not in FIXTURE_SUMMARIES["fever_adult"].priority_questions


def test_match_story_returns_fixture_name():
    for name in FIXTURE_NAMES:
        assert match_story(FIXTURE_STORIES[name]) == name


def test_match_story_ignores_extra_spaces_and_trailing_newline():
    for name in FIXTURE_NAMES:
        spaced = FIXTURE_STORIES[name].replace(" ", "   ")
        assert match_story(spaced) == name
        assert match_story("  \n  " + spaced + "\n\n") == name


def test_match_story_returns_none_for_unknown_story():
    assert match_story("hello") is None


def test_unknown_fixture_name_raises_key_error():
    with pytest.raises(KeyError):
        get_fixture("not_a_fixture")


def test_unknown_summary_name_raises_key_error():
    with pytest.raises(KeyError):
        get_summary("not_a_fixture")
