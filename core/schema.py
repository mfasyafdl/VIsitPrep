"""VisitPrep data contract, version 1.

Record types and validation shared by core/ and ui/. Standard library
only; no gradio, no network, no state. null means unknown.
"""

import copy
import dataclasses

SEX_VALUES = ("female", "male", "other", "not-specified")
SEVERITY_LEVELS = ("mild", "moderate", "severe")
MEDICINE_TYPES = ("prescription", "over-the-counter", "herbal", "supplement", "unknown")
MISSING_FIELD_KEYS = (
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


class SchemaError(ValueError):
    """A value does not match the data contract."""


@dataclasses.dataclass
class Medicine:
    name: str
    medicine_type: str
    dose: str | None
    frequency: str | None
    duration: str | None
    notes: str | None


@dataclasses.dataclass
class QuestionAnswer:
    question: str
    answer: str


@dataclasses.dataclass
class Alert:
    code: str
    message: str
    level: str


@dataclasses.dataclass
class SummaryOutput:
    doctor_card: str
    patient_script: str
    priority_questions: list[str]


@dataclasses.dataclass
class PatientRecord:
    patient_age: int | None
    patient_age_text: str | None
    patient_sex: str | None
    reporting_on_behalf: bool | None
    reporter_relationship: str | None
    complaint: str | None
    symptoms: list[str]
    onset: str | None
    duration: str | None
    severity: str | None
    severity_note: str | None
    medicines: list[Medicine]
    medicines_denied: bool | None
    allergies: list[str]
    allergies_denied: bool | None
    medical_history: list[str]
    medical_history_denied: bool | None
    pregnant: bool | None
    concerns: list[str]
    missing_information: list[str]


def empty_record() -> PatientRecord:
    return PatientRecord(
        patient_age=None,
        patient_age_text=None,
        patient_sex=None,
        reporting_on_behalf=None,
        reporter_relationship=None,
        complaint=None,
        symptoms=[],
        onset=None,
        duration=None,
        severity=None,
        severity_note=None,
        medicines=[],
        medicines_denied=None,
        allergies=[],
        allergies_denied=None,
        medical_history=[],
        medical_history_denied=None,
        pregnant=None,
        concerns=[],
        missing_information=[],
    )


def _is_missing_field(record: PatientRecord, key: str) -> bool:
    if key == "age":
        return record.patient_age is None
    if key == "sex":
        return record.patient_sex is None
    if key == "severity":
        return record.severity is None
    if key == "onset":
        return record.onset is None
    if key == "duration":
        return record.duration is None
    if key == "medicines":
        return not record.medicines and record.medicines_denied is not True
    if key == "allergies":
        return not record.allergies and record.allergies_denied is not True
    if key == "medical_history":
        return not record.medical_history and record.medical_history_denied is not True
    if key == "concerns":
        return not record.concerns
    raise SchemaError(f"Unknown missing-field key: {key!r}")


def missing_fields(record: PatientRecord) -> list[str]:
    return [key for key in MISSING_FIELD_KEYS if _is_missing_field(record, key)]


def recompute_missing_information(record: PatientRecord) -> PatientRecord:
    updated = copy.deepcopy(record)
    updated.missing_information = missing_fields(record)
    return updated


def _validate_medicine(medicine: Medicine, index: int) -> list[str]:
    where = f"medicines[{index}]"
    errors: list[str] = []
    if not isinstance(medicine, Medicine):
        errors.append(f"{where} must be a Medicine")
        return errors
    if not isinstance(medicine.name, str) or not medicine.name:
        errors.append(f"{where}.name must be a non-empty string")
    if not isinstance(medicine.medicine_type, str):
        errors.append(f"{where}.medicine_type must be a string")
    elif medicine.medicine_type not in MEDICINE_TYPES:
        errors.append(
            f"{where}.medicine_type must be one of: " + ", ".join(MEDICINE_TYPES)
        )
    for key in ("dose", "frequency", "duration", "notes"):
        value = getattr(medicine, key)
        if value is None:
            continue
        if not isinstance(value, str):
            errors.append(f"{where}.{key} must be a string or null")
        elif not value:
            errors.append(f"{where}.{key} must be a non-empty string")
    return errors


def validate_record(record: PatientRecord) -> list[str]:
    errors: list[str] = []

    def check_optional_str(key: str, value: object) -> None:
        if value is None:
            return
        if not isinstance(value, str):
            errors.append(f"{key} must be a string or null")
        elif not value:
            errors.append(f"{key} must be a non-empty string")

    def check_optional_bool(key: str, value: object) -> None:
        if value is not None and not isinstance(value, bool):
            errors.append(f"{key} must be a boolean or null")

    def check_str_list(key: str, value: object) -> list:
        if not isinstance(value, list):
            errors.append(f"{key} must be a list")
            return []
        for i, item in enumerate(value):
            if not isinstance(item, str) or not item:
                errors.append(f"{key}[{i}] must be a non-empty string")
        return value

    def check_denied(key: str, flag: object, items: list) -> None:
        check_optional_bool(key, flag)
        if flag is True and items:
            errors.append(f"{key} is true but the list is not empty")

    age = record.patient_age
    if age is not None:
        if isinstance(age, bool) or not isinstance(age, int):
            errors.append("patient_age must be an integer or null")
        elif not 0 <= age <= 130:
            errors.append("patient_age must be between 0 and 130")

    check_optional_str("patient_age_text", record.patient_age_text)
    sex = record.patient_sex
    if sex is not None:
        if not isinstance(sex, str):
            errors.append("patient_sex must be a string or null")
        elif sex not in SEX_VALUES:
            errors.append(
                "patient_sex must be one of: " + ", ".join(SEX_VALUES)
            )
    check_optional_bool("reporting_on_behalf", record.reporting_on_behalf)
    check_optional_str("reporter_relationship", record.reporter_relationship)
    check_optional_str("complaint", record.complaint)
    check_str_list("symptoms", record.symptoms)
    check_optional_str("onset", record.onset)
    check_optional_str("duration", record.duration)
    severity = record.severity
    if severity is not None:
        if not isinstance(severity, str):
            errors.append("severity must be a string or null")
        elif severity not in SEVERITY_LEVELS:
            errors.append("severity must be one of: " + ", ".join(SEVERITY_LEVELS))
    check_optional_str("severity_note", record.severity_note)

    if not isinstance(record.medicines, list):
        errors.append("medicines must be a list")
        medicines_items: list = []
    else:
        medicines_items = record.medicines
        for i, medicine in enumerate(record.medicines):
            errors.extend(_validate_medicine(medicine, i))
    check_denied("medicines_denied", record.medicines_denied, medicines_items)

    allergies_items = check_str_list("allergies", record.allergies)
    check_denied("allergies_denied", record.allergies_denied, allergies_items)
    history_items = check_str_list("medical_history", record.medical_history)
    check_denied(
        "medical_history_denied", record.medical_history_denied, history_items
    )
    check_optional_bool("pregnant", record.pregnant)
    check_str_list("concerns", record.concerns)

    if not isinstance(record.missing_information, list):
        errors.append("missing_information must be a list")
    else:
        for i, key in enumerate(record.missing_information):
            if not isinstance(key, str) or key not in MISSING_FIELD_KEYS:
                errors.append(
                    f"missing_information[{i}] must be one of: "
                    + ", ".join(MISSING_FIELD_KEYS)
                )
    return errors


def record_to_dict(record: PatientRecord) -> dict:
    return dataclasses.asdict(record)


def _optional_int(value: object, key: str) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise SchemaError(f"{key} must be an integer or null")
    return value


def _optional_str(value: object, key: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise SchemaError(f"{key} must be a string or null")
    return value


def _optional_bool(value: object, key: str) -> bool | None:
    if value is None:
        return None
    if not isinstance(value, bool):
        raise SchemaError(f"{key} must be a boolean or null")
    return value


def _str_list(value: object, key: str) -> list[str]:
    if not isinstance(value, list):
        raise SchemaError(f"{key} must be a list")
    for i, item in enumerate(value):
        if not isinstance(item, str):
            raise SchemaError(f"{key}[{i}] must be a string")
    return list(value)


def _medicine_from_dict(data: object, where: str) -> Medicine:
    if not isinstance(data, dict):
        raise SchemaError(f"{where} must be a dict")
    expected = {field.name for field in dataclasses.fields(Medicine)}
    unknown = sorted(set(data) - expected)
    if unknown:
        raise SchemaError(f"unknown keys in {where}: " + ", ".join(unknown))
    missing = sorted(expected - set(data))
    if missing:
        raise SchemaError(f"missing keys in {where}: " + ", ".join(missing))
    name = data["name"]
    if not isinstance(name, str):
        raise SchemaError(f"{where}.name must be a string")
    medicine_type = data["medicine_type"]
    if not isinstance(medicine_type, str):
        raise SchemaError(f"{where}.medicine_type must be a string")
    return Medicine(
        name=name,
        medicine_type=medicine_type,
        dose=_optional_str(data["dose"], f"{where}.dose"),
        frequency=_optional_str(data["frequency"], f"{where}.frequency"),
        duration=_optional_str(data["duration"], f"{where}.duration"),
        notes=_optional_str(data["notes"], f"{where}.notes"),
    )


def _medicine_list(value: object) -> list[Medicine]:
    if not isinstance(value, list):
        raise SchemaError("medicines must be a list")
    return [
        _medicine_from_dict(item, f"medicines[{i}]")
        for i, item in enumerate(value)
    ]


def record_from_dict(data: dict) -> PatientRecord:
    if not isinstance(data, dict):
        raise SchemaError("record data must be a dict")
    expected = {field.name for field in dataclasses.fields(PatientRecord)}
    unknown = sorted(set(data) - expected)
    if unknown:
        raise SchemaError("unknown keys in record: " + ", ".join(unknown))
    missing = sorted(expected - set(data))
    if missing:
        raise SchemaError("missing keys in record: " + ", ".join(missing))

    record = PatientRecord(
        patient_age=_optional_int(data["patient_age"], "patient_age"),
        patient_age_text=_optional_str(data["patient_age_text"], "patient_age_text"),
        patient_sex=_optional_str(data["patient_sex"], "patient_sex"),
        reporting_on_behalf=_optional_bool(
            data["reporting_on_behalf"], "reporting_on_behalf"
        ),
        reporter_relationship=_optional_str(
            data["reporter_relationship"], "reporter_relationship"
        ),
        complaint=_optional_str(data["complaint"], "complaint"),
        symptoms=_str_list(data["symptoms"], "symptoms"),
        onset=_optional_str(data["onset"], "onset"),
        duration=_optional_str(data["duration"], "duration"),
        severity=_optional_str(data["severity"], "severity"),
        severity_note=_optional_str(data["severity_note"], "severity_note"),
        medicines=_medicine_list(data["medicines"]),
        medicines_denied=_optional_bool(data["medicines_denied"], "medicines_denied"),
        allergies=_str_list(data["allergies"], "allergies"),
        allergies_denied=_optional_bool(data["allergies_denied"], "allergies_denied"),
        medical_history=_str_list(data["medical_history"], "medical_history"),
        medical_history_denied=_optional_bool(
            data["medical_history_denied"], "medical_history_denied"
        ),
        pregnant=_optional_bool(data["pregnant"], "pregnant"),
        concerns=_str_list(data["concerns"], "concerns"),
        missing_information=_str_list(
            data["missing_information"], "missing_information"
        ),
    )
    errors = validate_record(record)
    if errors:
        raise SchemaError("; ".join(errors))
    return record
