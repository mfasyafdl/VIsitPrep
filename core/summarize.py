"""Summary interface: generate_summary(record, asked, *, config) produces a SummaryOutput (doctor_card, patient_script, priority_questions) with one model call, per docs/data_contract.md; no logic is implemented yet."""

from core.llm import LLMConfig
from core.schema import PatientRecord, QuestionAnswer, SummaryOutput


def generate_summary(
    record: PatientRecord,
    asked: list[QuestionAnswer],
    *,
    config: LLMConfig | None = None,
) -> SummaryOutput:
    raise NotImplementedError("generate_summary is not implemented yet")
