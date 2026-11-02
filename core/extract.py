"""Extraction interface: extract_record(story, details, *, config) turns the patient's story into a PatientRecord with one model call, using docs/data_contract.md field rules; no logic is implemented yet."""

from core.llm import LLMConfig
from core.schema import PatientRecord


def extract_record(
    story: str,
    details: dict | None = None,
    *,
    config: LLMConfig | None = None,
) -> PatientRecord:
    raise NotImplementedError("extract_record is not implemented yet")
