"""Summary: build_doctor_card(record) renders the 10-line doctor card from the record in code so it can never invent, drop or reword a fact, and generate_summary(record, asked, *, config) writes only the patient script and the priority questions with one model call, per docs/data_contract.md."""

import json
import re

from core.llm import LLMConfig, chat_json
from core.prompts import SUMMARY_SYSTEM
from core.schema import Medicine, PatientRecord, QuestionAnswer, SummaryOutput, record_to_dict

_NOT_GIVEN = "Not given"
_CONFIRMED_NONE = "None (patient confirms)"

_TAG_RE = re.compile(
    r"<\s*/?\s*(?:current_record|patient_report)\s*>", re.IGNORECASE
)


def _patient_value(record: PatientRecord) -> str:
    parts: list[str] = []
    if record.patient_age_text is not None:
        parts.append(record.patient_age_text)
    elif record.patient_age is not None:
        parts.append(str(record.patient_age))
    if record.patient_sex is not None:
        parts.append(record.patient_sex)
    value = ", ".join(parts)
    if record.reporting_on_behalf is True:
        if record.reporter_relationship is not None:
            if record.patient_sex == "male":
                possessive = "his"
            elif record.patient_sex == "female":
                possessive = "her"
            else:
                possessive = "the patient's"
            suffix = " (reported by " + possessive + " " + record.reporter_relationship + ")"
        else:
            suffix = " (reported by someone else)"
        if value:
            value += suffix
        else:
            value = suffix[1:]
    return value


def _list_value(items: list[str], denied: bool | None) -> str:
    if items:
        return "; ".join(items)
    if denied is True:
        return _CONFIRMED_NONE
    return _NOT_GIVEN


def _medicine_value(medicine: Medicine) -> str:
    value = medicine.name
    if medicine.medicine_type != "unknown":
        value += " (" + medicine.medicine_type + ")"
    details = [
        detail
        for detail in (medicine.dose, medicine.frequency, medicine.duration)
        if detail is not None
    ]
    if details:
        value += ", " + ", ".join(details)
    return value


def build_doctor_card(record: PatientRecord) -> str:
    if record.complaint is not None:
        problem = '"' + record.complaint + '" (patient\'s own words)'
    else:
        problem = _NOT_GIVEN
    if record.severity is not None and record.severity_note is not None:
        severity = record.severity + ' ("' + record.severity_note + '")'
    elif record.severity is not None:
        severity = record.severity
    elif record.severity_note is not None:
        severity = '"' + record.severity_note + '"'
    else:
        severity = _NOT_GIVEN
    if record.concerns:
        concerns = (
            "; ".join('"' + concern + '"' for concern in record.concerns)
            + " (patient's own words)"
        )
    else:
        concerns = _NOT_GIVEN
    lines = [
        "Patient: "
        + (_patient_value(record) or _NOT_GIVEN),
        "Problem: " + problem,
        "Started: " + (record.onset if record.onset is not None else _NOT_GIVEN),
        "Duration: " + (record.duration if record.duration is not None else _NOT_GIVEN),
        "Severity: " + severity,
        "Symptoms: " + _list_value(record.symptoms, None),
        "Medicines: " + _list_value(
            [_medicine_value(medicine) for medicine in record.medicines],
            record.medicines_denied,
        ),
        "Allergies: " + _list_value(record.allergies, record.allergies_denied),
        "Medical history: "
        + _list_value(record.medical_history, record.medical_history_denied),
        "Patient's concerns: " + concerns,
    ]
    return "\n".join(lines)


def _validate_summary(data: dict) -> list[str]:
    problems: list[str] = []
    script = data.get("patient_script")
    if not isinstance(script, str):
        problems.append("patient_script must be a string")
    else:
        words = script.strip().split()
        if len(words) < 5 or len(words) > 120:
            problems.append("patient_script must have 5 to 120 words")
    questions = data.get("priority_questions")
    if not isinstance(questions, list):
        problems.append("priority_questions must be a list of strings")
    else:
        if any(not isinstance(item, str) for item in questions):
            problems.append("priority_questions must be a list of strings")
        cleaned = [
            item.strip()
            for item in questions
            if isinstance(item, str) and item.strip()
        ]
        if not cleaned:
            problems.append("priority_questions must have 1 to 3 questions")
        elif any(not item.endswith("?") for item in cleaned):
            problems.append("each priority question must end with ?")
    return problems


def _build_user_message(record: PatientRecord) -> str:
    current = record_to_dict(record)
    current.pop("missing_information")
    return (
        "<current_record>\n"
        + _TAG_RE.sub("", json.dumps(current, ensure_ascii=False, indent=2))
        + "\n</current_record>"
    )


def generate_summary(
    record: PatientRecord,
    asked: list[QuestionAnswer],
    *,
    config: LLMConfig | None = None,
) -> SummaryOutput:
    user = _build_user_message(record)
    data = chat_json(SUMMARY_SYSTEM, user, validate=_validate_summary, config=config)
    script = data["patient_script"].strip()
    questions = [
        item.strip()
        for item in data["priority_questions"]
        if isinstance(item, str) and item.strip()
    ]
    return SummaryOutput(
        doctor_card=build_doctor_card(record),
        patient_script=script,
        priority_questions=questions[:3],
    )
