"""Interview interface: next_question(record, asked, skipped, max_questions) picks the next rule-based question with no network call, and merge_answers(record, asked, *, config) folds all answers into a new record with one model call, per docs/data_contract.md."""

import copy
import json
import re

from core.extract import _normalize as _normalize_answer
from core.llm import LLMConfig, chat_json
from core.prompts import MERGE_SYSTEM
from core.schema import (
    PatientRecord,
    QuestionAnswer,
    SchemaError,
    missing_fields,
    record_from_dict,
    record_to_dict,
    recompute_missing_information,
    validate_record,
)

PRIORITY_FIELDS = (
    "severity",
    "onset",
    "duration",
    "medicines",
    "allergies",
    "medical_history",
    "age",
    "sex",
    "concerns",
)

QUESTIONS_SELF: dict[str, str] = {
    "severity": "How bad is it: mild, moderate or severe?",
    "onset": "When did it start?",
    "duration": "How long has it been going on?",
    "medicines": (
        "Are you taking any medicines, herbal remedies or supplements? "
        "Please name them."
    ),
    "allergies": "Do you have any allergies?",
    "medical_history": "Do you have any ongoing or past health conditions?",
    "age": "How old are you?",
    "sex": "What is your sex?",
    "concerns": "Is there anything you are worried about or want to ask the doctor?",
}

QUESTIONS_ON_BEHALF: dict[str, str] = {
    "severity": "How bad is it: mild, moderate or severe?",
    "onset": "When did it start?",
    "duration": "How long has it been going on?",
    "medicines": (
        "Is the patient taking any medicines, herbal remedies or supplements? "
        "Please name them."
    ),
    "allergies": "Does the patient have any allergies?",
    "medical_history": "Does the patient have any ongoing or past health conditions?",
    "age": "How old is the patient?",
    "sex": "What is the patient's sex?",
    "concerns": "Is there anything you are worried about or want to ask the doctor?",
}


def _normalize(text: str) -> str:
    return text.casefold().strip()


_QUESTION_FIELDS: dict[str, str] = {
    question.casefold().strip(): field
    for table in (QUESTIONS_SELF, QUESTIONS_ON_BEHALF)
    for field, question in table.items()
}

NEGATIVE_WORDS = {
    "no",
    "none",
    "nothing",
    "nope",
    "nah",
    "not",
    "n",
    "na",
}

REFUSAL_WORDS = NEGATIVE_WORDS | {
    "a",
    "really",
    "at",
    "all",
    "else",
    "other",
    "more",
    "thanks",
    "thank",
    "you",
    "that",
    "s",
    "it",
    "i",
    "have",
    "any",
    "concern",
    "concerns",
    "worry",
    "worries",
    "problem",
    "problems",
}

_NEGATION_WORDS = {
    "not",
    "no",
    "never",
    "isn",
    "wasn",
    "doesn",
    "don",
    "didn",
    "aren",
    "nor",
    "hardly",
    "without",
}

_UNCERTAINTY_FRAGMENTS = (
    "don't know",
    "dont know",
    "do not know",
    "not sure",
    "unsure",
    "no idea",
    "can't remember",
    "cant remember",
    "cannot remember",
    "don't remember",
    "do not remember",
)

_SEVERITY_WORDS = {"mild", "moderate", "severe"}
_TOKEN_RE = re.compile(r"[0-9a-z]+")


def _answer_words(answer: str) -> list[str]:
    return _TOKEN_RE.findall(answer.strip().casefold())


def _is_plain_no(answer: str) -> bool:
    words = _answer_words(answer)
    return (
        bool(words)
        and all(word in REFUSAL_WORDS for word in words)
        and any(word in NEGATIVE_WORDS for word in words)
    )


def _is_hedged(answer: str) -> bool:
    folded = answer.strip().casefold()
    return any(fragment in folded for fragment in _UNCERTAINTY_FRAGMENTS)


def _is_negated(answer: str) -> bool:
    return any(word in _NEGATION_WORDS for word in _answer_words(answer))


def _is_usable_answer(answer: str) -> bool:
    stripped = answer.strip()
    return bool(stripped) and not _is_plain_no(stripped) and not _is_hedged(stripped)


def _severity_levels(answer: str) -> list[str]:
    levels: list[str] = []
    for word in _answer_words(answer):
        if word in _SEVERITY_WORDS and word not in levels:
            levels.append(word)
    return levels


def _is_single_level_words(words: list[str]) -> bool:
    unique = set(words)
    return len(unique) == 1 and unique <= _SEVERITY_WORDS


def _fill_from_answers(
    new_record: PatientRecord, asked: list[QuestionAnswer]
) -> PatientRecord:
    filled = copy.deepcopy(new_record)
    last_answer: dict[str, str] = {}
    for item in asked:
        field = _QUESTION_FIELDS.get(item.question.casefold().strip())
        if field is None:
            continue
        last_answer[field] = item.answer.strip()
    if (
        filled.onset is None
        and "onset" in last_answer
        and _is_usable_answer(last_answer["onset"])
    ):
        filled.onset = last_answer["onset"]
    if (
        filled.duration is None
        and "duration" in last_answer
        and _is_usable_answer(last_answer["duration"])
    ):
        filled.duration = last_answer["duration"]
    if "severity" in last_answer:
        answer = last_answer["severity"]
        if answer and not _is_plain_no(answer):
            words = _answer_words(answer)
            levels = _severity_levels(answer)
            if (
                filled.severity is None
                and len(levels) == 1
                and not _is_hedged(answer)
                and not _is_negated(answer)
            ):
                filled.severity = levels[0]
            if (
                filled.severity_note is None
                and not _is_single_level_words(words)
                and (not _is_hedged(answer) or levels)
            ):
                filled.severity_note = answer
    if (
        not filled.concerns
        and "concerns" in last_answer
        and _is_usable_answer(last_answer["concerns"])
    ):
        filled.concerns = [last_answer["concerns"]]
    return filled


def next_question(
    record: PatientRecord,
    asked: list[QuestionAnswer],
    skipped: list[str],
    max_questions: int = 5,
) -> str | None:
    if max_questions <= 0 or len(asked) + len(skipped) >= max_questions:
        return None
    if record.reporting_on_behalf is True:
        questions = QUESTIONS_ON_BEHALF
    else:
        questions = QUESTIONS_SELF
    missing = missing_fields(record)
    used = {_normalize(item.question) for item in asked}
    used.update(_normalize(item) for item in skipped)
    for field in PRIORITY_FIELDS:
        if field not in missing:
            continue
        question = questions[field]
        if _normalize(question) in used:
            continue
        return question
    return None


_TAG_RE = re.compile(
    r"<\s*/?\s*(?:current_record|patient_report)\s*>", re.IGNORECASE
)

_SCALAR_GUARD_FIELDS = (
    "patient_age",
    "patient_age_text",
    "patient_sex",
    "reporting_on_behalf",
    "reporter_relationship",
    "complaint",
    "onset",
    "duration",
    "severity",
    "severity_note",
    "pregnant",
)

_LIST_GUARD_FIELDS = ("symptoms", "allergies", "medical_history", "concerns")

_FLAG_GUARD_PAIRS = (
    ("medicines_denied", "medicines"),
    ("allergies_denied", "allergies"),
    ("medical_history_denied", "medical_history"),
)


def _build_user_message(
    record: PatientRecord, asked: list[QuestionAnswer]
) -> str:
    current = record_to_dict(record)
    current.pop("missing_information")
    record_part = (
        "<current_record>\n"
        + _TAG_RE.sub("", json.dumps(current, ensure_ascii=False, indent=2))
        + "\n</current_record>"
    )
    blocks = [
        "Question: "
        + _TAG_RE.sub("", item.question)
        + "\nAnswer: "
        + _TAG_RE.sub("", item.answer)
        for item in asked
    ]
    report_part = "<patient_report>\n" + "\n\n".join(blocks) + "\n</patient_report>"
    return record_part + "\n\n" + report_part


def _fact_loss_problems(
    original: PatientRecord, updated: PatientRecord
) -> list[str]:
    problems: list[str] = []
    for field in _SCALAR_GUARD_FIELDS:
        if getattr(original, field) is None:
            continue
        if getattr(updated, field) is None:
            problems.append(f"keep {field}: it was known before")
    for field in _LIST_GUARD_FIELDS:
        new_items = {item.strip().casefold() for item in getattr(updated, field)}
        for item in getattr(original, field):
            if item.strip().casefold() not in new_items:
                problems.append(f"keep every item of {field}: missing {item}")
    new_names = {medicine.name.strip().casefold() for medicine in updated.medicines}
    for medicine in original.medicines:
        if medicine.name.strip().casefold() not in new_names:
            problems.append(f"keep every medicine: missing {medicine.name}")
    for flag_key, list_key in _FLAG_GUARD_PAIRS:
        if (
            getattr(original, flag_key) is True
            and getattr(updated, flag_key) is not True
            and not getattr(updated, list_key)
        ):
            problems.append(f"keep {flag_key}: it was true before")
    return problems


def _validate_merge(data: dict, original: PatientRecord) -> list[str]:
    normalized, problems = _normalize_answer(data)
    if problems:
        return problems
    try:
        updated = record_from_dict(normalized)
    except SchemaError as error:
        return [str(error)]
    problems = validate_record(updated)
    if problems:
        return problems
    return _fact_loss_problems(original, updated)


def merge_answers(
    record: PatientRecord,
    asked: list[QuestionAnswer],
    *,
    config: LLMConfig | None = None,
) -> PatientRecord:
    if not asked:
        return recompute_missing_information(record)

    def validate(answer: dict) -> list[str]:
        return _validate_merge(answer, record)

    user = _build_user_message(record, asked)
    data = chat_json(MERGE_SYSTEM, user, validate=validate, config=config)
    normalized, _problems = _normalize_answer(data)
    updated = record_from_dict(normalized)
    updated = _fill_from_answers(updated, asked)
    return recompute_missing_information(updated)
