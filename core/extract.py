"""Extraction: extract_record(story, details, *, config) turns a patient's story into a PatientRecord with one model call, using the reviewed EXTRACT_SYSTEM prompt and the docs/data_contract.md field rules; the story is sent inside <patient_report> tags and details are applied only after the model call."""

import re

from core.llm import LLMConfig, chat_json
from core.prompts import EXTRACT_SYSTEM
from core.schema import (
    MEDICINE_TYPES,
    SEX_VALUES,
    SEVERITY_LEVELS,
    PatientRecord,
    SchemaError,
    record_from_dict,
    recompute_missing_information,
    validate_record,
)

RECORD_KEYS = (
    "patient_age",
    "patient_age_text",
    "patient_sex",
    "reporting_on_behalf",
    "reporter_relationship",
    "complaint",
    "symptoms",
    "onset",
    "duration",
    "severity",
    "severity_note",
    "medicines",
    "medicines_denied",
    "allergies",
    "allergies_denied",
    "medical_history",
    "medical_history_denied",
    "pregnant",
    "concerns",
)

_NULL_WORDS = ("null", "none", "unknown", "n/a", "not given", "not stated")
_PATIENT_REPORT_TAG = re.compile(r"<\s*/?\s*patient_report\s*>", re.IGNORECASE)
_DETAILS_KEYS = ("patient_age", "patient_age_text", "patient_sex")


def _normalize_text(value: object, name: str, problems: list[str]) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        problems.append(f"{name} must be a string or null")
        return None
    text = value.strip()
    if not text or text.lower() in _NULL_WORDS:
        return None
    return text


def _normalize_age(value: object) -> int | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, float):
        if not value.is_integer():
            return None
        value = int(value)
    elif isinstance(value, str):
        text = value.strip()
        if not (text.isascii() and text.isdigit()):
            return None
        value = int(text)
    elif not isinstance(value, int):
        return None
    return value if 0 <= value <= 130 else None


def _normalize_sex(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.strip().lower()
    return text if text in SEX_VALUES else None


def _normalize_bool(value: object) -> bool | None:
    return value if isinstance(value, bool) else None


def _normalize_str_list(value: object, name: str, problems: list[str]) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        value = [value]
    if not isinstance(value, list):
        problems.append(f"{name} must be a list of strings")
        return []
    items: list[str] = []
    for item in value:
        if not isinstance(item, str):
            if f"{name} must be a list of strings" not in problems:
                problems.append(f"{name} must be a list of strings")
            continue
        text = item.strip()
        if text:
            items.append(text)
    return items


def _normalize_medicine(item: object, index: int, problems: list[str]) -> dict | None:
    if isinstance(item, str):
        name = item.strip()
        if not name:
            return None
        return {
            "name": name,
            "medicine_type": "unknown",
            "dose": None,
            "frequency": None,
            "duration": None,
            "notes": None,
        }
    name = item.get("name")
    if not isinstance(name, str):
        return None
    name = name.strip()
    if not name:
        return None
    medicine_type = item.get("medicine_type")
    if not isinstance(medicine_type, str) or medicine_type not in MEDICINE_TYPES:
        medicine_type = "unknown"
    medicine = {
        "name": name,
        "medicine_type": medicine_type,
        "dose": _normalize_text(item.get("dose"), f"medicines[{index}].dose", problems),
        "frequency": _normalize_text(
            item.get("frequency"), f"medicines[{index}].frequency", problems
        ),
        "duration": _normalize_text(
            item.get("duration"), f"medicines[{index}].duration", problems
        ),
        "notes": _normalize_text(
            item.get("notes"), f"medicines[{index}].notes", problems
        ),
    }
    return medicine


def _normalize_medicines(value: object, problems: list[str]) -> list[dict]:
    if value is None:
        return []
    if isinstance(value, str):
        value = [value]
    if not isinstance(value, list):
        problems.append("medicines must be a list of objects")
        return []
    medicines: list[dict] = []
    for index, item in enumerate(value):
        if not isinstance(item, (str, dict)):
            if "medicines must be a list of objects" not in problems:
                problems.append("medicines must be a list of objects")
            continue
        medicine = _normalize_medicine(item, index, problems)
        if medicine is not None:
            medicines.append(medicine)
    return medicines


def _normalize(data: dict) -> tuple[dict, list[str]]:
    problems: list[str] = []
    if not isinstance(data, dict):
        data = {}

    for key in RECORD_KEYS:
        if key not in data:
            problems.append(f"missing key: {key}")

    record: dict = {"missing_information": []}
    record["patient_age_text"] = _normalize_text(
        data.get("patient_age_text"), "patient_age_text", problems
    )
    record["reporter_relationship"] = _normalize_text(
        data.get("reporter_relationship"), "reporter_relationship", problems
    )
    record["complaint"] = _normalize_text(data.get("complaint"), "complaint", problems)
    record["onset"] = _normalize_text(data.get("onset"), "onset", problems)
    record["duration"] = _normalize_text(data.get("duration"), "duration", problems)
    record["patient_age"] = _normalize_age(data.get("patient_age"))
    record["patient_sex"] = _normalize_sex(data.get("patient_sex"))
    record["reporting_on_behalf"] = _normalize_bool(data.get("reporting_on_behalf"))
    record["symptoms"] = _normalize_str_list(data.get("symptoms"), "symptoms", problems)

    record["severity_note"] = _normalize_text(
        data.get("severity_note"), "severity_note", problems
    )
    raw_severity = data.get("severity")
    severity = None
    if isinstance(raw_severity, str):
        text = raw_severity.strip()
        lowered = text.lower()
        if lowered in SEVERITY_LEVELS:
            severity = lowered
        elif text and record["severity_note"] is None:
            record["severity_note"] = text
    record["severity"] = severity

    record["medicines"] = _normalize_medicines(data.get("medicines"), problems)
    record["medicines_denied"] = _normalize_bool(data.get("medicines_denied"))
    record["allergies"] = _normalize_str_list(
        data.get("allergies"), "allergies", problems
    )
    record["allergies_denied"] = _normalize_bool(data.get("allergies_denied"))
    record["medical_history"] = _normalize_str_list(
        data.get("medical_history"), "medical_history", problems
    )
    record["medical_history_denied"] = _normalize_bool(
        data.get("medical_history_denied")
    )
    record["pregnant"] = _normalize_bool(data.get("pregnant"))
    record["concerns"] = _normalize_str_list(
        data.get("concerns"), "concerns", problems
    )

    for flag_key, list_key in (
        ("medicines_denied", "medicines"),
        ("allergies_denied", "allergies"),
        ("medical_history_denied", "medical_history"),
    ):
        if record[flag_key] is True and record[list_key]:
            record[flag_key] = None

    return record, problems


def _validate(data: dict) -> list[str]:
    normalized, problems = _normalize(data)
    if problems:
        return problems
    try:
        record = record_from_dict(normalized)
    except SchemaError as error:
        return [str(error)]
    return validate_record(record)


def extract_record(
    story: str,
    details: dict | None = None,
    *,
    config: LLMConfig | None = None,
) -> PatientRecord:
    text = story.strip()
    if not text:
        raise ValueError("Please describe your symptoms first.")
    user = "<patient_report>\n" + _PATIENT_REPORT_TAG.sub("", text) + "\n</patient_report>"
    data = chat_json(EXTRACT_SYSTEM, user, validate=_validate, config=config)
    normalized, _problems = _normalize(data)
    record = record_from_dict(normalized)
    if details is not None:
        for key in _DETAILS_KEYS:
            if key in details and details[key] is not None:
                setattr(record, key, details[key])
    return recompute_missing_information(record)
