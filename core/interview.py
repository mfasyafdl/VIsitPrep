"""Interview interface: next_question(record, asked, skipped, max_questions) picks the next rule-based question with no network call, and merge_answers(record, asked, *, config) folds all answers into a new record with one model call, per docs/data_contract.md; no logic is implemented yet."""

from core.llm import LLMConfig
from core.schema import PatientRecord, QuestionAnswer


def next_question(
    record: PatientRecord,
    asked: list[QuestionAnswer],
    skipped: list[str],
    max_questions: int = 5,
) -> str | None:
    raise NotImplementedError("next_question is not implemented yet")


def merge_answers(
    record: PatientRecord,
    asked: list[QuestionAnswer],
    *,
    config: LLMConfig | None = None,
) -> PatientRecord:
    raise NotImplementedError("merge_answers is not implemented yet")
