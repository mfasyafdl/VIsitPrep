"""Interview interface: next_question(record, asked, skipped, max_questions) picks the next rule-based question with no network call, and merge_answers(record, asked, *, config) folds all answers into a new record with one model call, per docs/data_contract.md."""

from core.llm import LLMConfig
from core.schema import PatientRecord, QuestionAnswer, missing_fields

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


def merge_answers(
    record: PatientRecord,
    asked: list[QuestionAnswer],
    *,
    config: LLMConfig | None = None,
) -> PatientRecord:
    raise NotImplementedError("merge_answers is not implemented yet")
