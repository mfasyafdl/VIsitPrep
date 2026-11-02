import pytest

from core.schema import (
    Medicine,
    PatientRecord,
    SchemaError,
    empty_record,
    missing_fields,
    recompute_missing_information,
    record_from_dict,
    record_to_dict,
    validate_record,
)


def make_record() -> PatientRecord:
    return PatientRecord(
        patient_age=34,
        patient_age_text="34 years old",
        patient_sex="female",
        reporting_on_behalf=False,
        reporter_relationship=None,
        complaint="sore throat and mild cough",
        symptoms=[
            "sore throat, worse when swallowing",
            "mild dry cough, mostly at night",
        ],
        onset="Tuesday morning",
        duration="about 3 days",
        severity="mild",
        severity_note="annoying, but I can eat and sleep",
        medicines=[
            Medicine(
                name="honey and lemon tea",
                medicine_type="unknown",
                dose="one cup",
                frequency="twice a day",
                duration="2 days",
                notes="helps a little",
            )
        ],
        medicines_denied=None,
        allergies=[],
        allergies_denied=True,
        medical_history=["mild asthma as a child"],
        medical_history_denied=None,
        pregnant=None,
        concerns=["is this something to worry about?"],
        missing_information=[],
    )


def test_empty_record_is_valid():
    assert validate_record(empty_record()) == []


def test_round_trip_is_exact():
    record = make_record()
    data = record_to_dict(record)
    again = record_from_dict(data)
    assert record_to_dict(again) == data
    assert again == record


def test_allergies_denied_with_non_empty_list_is_rejected():
    record = make_record()
    record.allergies = ["peanuts"]
    record.allergies_denied = True
    errors = validate_record(record)
    assert any("allergies_denied" in error for error in errors)


def test_age_131_is_rejected():
    record = make_record()
    record.patient_age = 131
    errors = validate_record(record)
    assert any("patient_age" in error for error in errors)


def test_unknown_sex_raises_schema_error_in_from_dict():
    data = record_to_dict(make_record())
    data["patient_sex"] = "android"
    with pytest.raises(SchemaError):
        record_from_dict(data)


def test_missing_fields_allergies_denied_vs_not_asked():
    denied = make_record()
    denied.allergies = []
    denied.allergies_denied = True
    assert "allergies" not in missing_fields(denied)

    not_asked = make_record()
    not_asked.allergies = []
    not_asked.allergies_denied = None
    assert "allergies" in missing_fields(not_asked)


def test_recompute_missing_information_new_object_input_unchanged():
    record = make_record()
    record.patient_age = None
    record.missing_information = ["stale"]
    updated = recompute_missing_information(record)
    assert updated is not record
    assert record.missing_information == ["stale"]
    assert updated.missing_information == missing_fields(record)
    assert "age" in updated.missing_information


def test_recompute_missing_information_copies_lists_deeply():
    record = make_record()
    original_symptoms = list(record.symptoms)
    original_medicines = list(record.medicines)
    updated = recompute_missing_information(record)
    updated.symptoms.append("a new symptom in the patient's words")
    updated.medicines.append(
        Medicine(
            name="a second remedy",
            medicine_type="unknown",
            dose=None,
            frequency=None,
            duration=None,
            notes=None,
        )
    )
    assert record.symptoms == original_symptoms
    assert record.medicines == original_medicines
