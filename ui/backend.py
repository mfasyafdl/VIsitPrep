"""Backend switch for the VisitPrep UI.

PREVIEW is decided once at import from the VISITPREP_PREVIEW
environment variable. In preview mode the fixture data from
core.fixtures stands in for the model calls; otherwise the real core
functions are used. Alerts and next_question are not part of this
module: the handlers call core.redflag and core.interview directly in
both modes. There is no try/except in this module.
"""

import copy
import os

from core import fixtures
from core import extract as core_extract
from core import interview as core_interview
from core import summarize as core_summarize
from core.schema import (
    PatientRecord,
    QuestionAnswer,
    SummaryOutput,
    recompute_missing_information,
)

PREVIEW = os.environ.get("VISITPREP_PREVIEW") == "1"

DEFAULT_PREVIEW_FIXTURE = "child_cough"


def _fixture_name(story: str) -> str:
    return fixtures.match_story(story) or DEFAULT_PREVIEW_FIXTURE


def extract(story: str, details: dict | None) -> PatientRecord:
    if PREVIEW:
        record = fixtures.get_fixture(_fixture_name(story))
        if details:
            if details.get("patient_age") is not None:
                record.patient_age = details["patient_age"]
            if details.get("patient_age_text") is not None:
                record.patient_age_text = details["patient_age_text"]
            if details.get("patient_sex") is not None:
                record.patient_sex = details["patient_sex"]
        return recompute_missing_information(record)
    return core_extract.extract_record(story, details)


def merge(record: PatientRecord, asked: list[QuestionAnswer]) -> PatientRecord:
    if PREVIEW:
        return copy.deepcopy(record)
    return core_interview.merge_answers(record, asked)


def summarize(
    record: PatientRecord, asked: list[QuestionAnswer], story: str
) -> SummaryOutput:
    if PREVIEW:
        return fixtures.get_summary(_fixture_name(story))
    return core_summarize.generate_summary(record, asked)
