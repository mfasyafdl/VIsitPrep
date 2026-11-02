"""Fictional fixtures for tests and the UI preview.

Every person and detail is fictional. Every record is passed through
recompute_missing_information before it is stored.
"""

import copy
import re

from core.schema import (
    Medicine,
    PatientRecord,
    SummaryOutput,
    empty_record,
    recompute_missing_information,
)


def _fever_adult() -> PatientRecord:
    record = empty_record()
    record.patient_age = 34
    record.patient_age_text = "34"
    record.patient_sex = "female"
    record.reporting_on_behalf = False
    record.complaint = "I have had a fever and a headache since yesterday."
    record.symptoms = ["fever", "headache", "temperature of 39 this morning"]
    record.onset = "yesterday morning"
    record.duration = "about one day"
    record.severity = "moderate"
    record.medicines = [
        Medicine(
            name="ginger tea",
            medicine_type="herbal",
            dose=None,
            frequency="twice a day",
            duration=None,
            notes=None,
        )
    ]
    record.allergies = []
    record.allergies_denied = True
    return recompute_missing_information(record)


def _child_cough() -> PatientRecord:
    record = empty_record()
    record.patient_age = 7
    record.patient_age_text = "7 years old"
    record.patient_sex = "male"
    record.reporting_on_behalf = True
    record.reporter_relationship = "mother"
    record.complaint = "He has had a cough for five days and it is worse at night."
    record.symptoms = ["cough", "cough worse at night"]
    record.onset = "five days ago"
    record.duration = "five days"
    record.severity = "mild"
    record.severity_note = "He is still playing and eating."
    record.concerns = ["Does he need to stay home from school?"]
    return recompute_missing_information(record)


def _chest_pain() -> PatientRecord:
    record = empty_record()
    record.patient_age = 52
    record.patient_age_text = "52"
    record.patient_sex = "female"
    record.reporting_on_behalf = False
    record.complaint = "A tight pain in my chest that comes and goes."
    record.symptoms = ["tight pain in my chest that comes and goes"]
    record.onset = "two days ago"
    record.medicines = [
        Medicine(
            name="amlodipine",
            medicine_type="prescription",
            dose=None,
            frequency="every morning",
            duration=None,
            notes=None,
        )
    ]
    record.medical_history = ["high blood pressure"]
    record.concerns = ["I'm worried it's my heart."]
    return recompute_missing_information(record)


# Fictional fixture names; keys of FIXTURE_STORIES and FIXTURE_SUMMARIES.
FIXTURE_NAMES = ("fever_adult", "child_cough", "chest_pain")

# Empty record with missing_information recomputed.
FIXTURE_EMPTY = recompute_missing_information(empty_record())

# Fictional 34-year-old female with a fever and headache; no allergies.
FIXTURE_FEVER_ADULT = _fever_adult()

# Fictional 7-year-old male with a cough worse at night, reported by his mother.
FIXTURE_CHILD_COUGH = _child_cough()

# Fictional 52-year-old female with a tight chest pain that comes and goes.
FIXTURE_CHEST_PAIN = _chest_pain()

# One first-person story per fixture name, copied exactly as given.
FIXTURE_STORIES: dict[str, str] = {
    "fever_adult": "I am 34. I have had a fever and a headache since yesterday morning. My temperature was 39 this morning. I drink ginger tea twice a day. I have no allergies.",
    "child_cough": "My son is 7 years old. He has had a cough for five days and it is worse at night. He is still playing and eating. Does he need to stay home from school?",
    "chest_pain": "I am 52. I have a tight pain in my chest that comes and goes. It started two days ago. I take amlodipine every morning for high blood pressure. I'm worried it's my heart.",
}

# fictional example output for the UI preview only
FIXTURE_SUMMARIES: dict[str, SummaryOutput] = {
    "fever_adult": SummaryOutput(
        doctor_card="""Patient: 34, female
Problem: "I have had a fever and a headache since yesterday." (patient's own words)
Started: yesterday morning
Duration: about one day
Severity: moderate
Symptoms: fever; headache; temperature of 39 this morning
Medicines: ginger tea (herbal), twice a day
Allergies: None (patient confirms)
Medical history: Not given
Patient's concerns: Not given""",
        patient_script="I'm 34. I've had a fever and a headache since yesterday morning. My temperature was 39 this morning. I've been drinking ginger tea twice a day. I have no allergies.",
        priority_questions=[
            "What should I watch for over the next few days?",
            "When should I come back if the fever doesn't go down?",
        ],
    ),
    "child_cough": SummaryOutput(
        doctor_card="""Patient: 7 years old, male (reported by his mother)
Problem: "He has had a cough for five days and it is worse at night." (patient's own words)
Started: five days ago
Duration: five days
Severity: mild ("He is still playing and eating.")
Symptoms: cough; cough worse at night
Medicines: Not given
Allergies: Not given
Medical history: Not given
Patient's concerns: "Does he need to stay home from school?" (patient's own words)""",
        patient_script="I'm here about my son. He's 7. He has had a cough for five days, and it's worse at night. He is still playing and eating. I'd like to know if he needs to stay home from school.",
        priority_questions=[
            "Does he need to stay home from school?",
            "What would mean we should come back sooner?",
        ],
    ),
    "chest_pain": SummaryOutput(
        doctor_card="""Patient: 52, female
Problem: "A tight pain in my chest that comes and goes." (patient's own words)
Started: two days ago
Duration: Not given
Severity: Not given
Symptoms: tight pain in my chest that comes and goes
Medicines: amlodipine (prescription), every morning
Allergies: Not given
Medical history: high blood pressure
Patient's concerns: "I'm worried it's my heart." (patient's own words)""",
        patient_script="I'm 52. For two days I've had a tight pain in my chest that comes and goes. I take amlodipine every morning for high blood pressure. I'm worried it's my heart.",
        priority_questions=[
            "What could be causing this pain?",
            "Should my blood pressure medicine be checked?",
        ],
    ),
}


def all_fixtures() -> dict[str, PatientRecord]:
    fixtures: dict[str, PatientRecord] = {}
    fixtures["empty"] = get_fixture("empty")
    for name in FIXTURE_NAMES:
        fixtures[name] = get_fixture(name)
    return fixtures


def get_fixture(name: str) -> PatientRecord:
    records = {
        "empty": FIXTURE_EMPTY,
        "fever_adult": FIXTURE_FEVER_ADULT,
        "child_cough": FIXTURE_CHILD_COUGH,
        "chest_pain": FIXTURE_CHEST_PAIN,
    }
    return copy.deepcopy(records[name])


def get_summary(name: str) -> SummaryOutput:
    return copy.deepcopy(FIXTURE_SUMMARIES[name])


def _normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())


def match_story(story: str) -> str | None:
    normalized = _normalize_whitespace(story)
    for name in FIXTURE_NAMES:
        if normalized == _normalize_whitespace(FIXTURE_STORIES[name]):
            return name
    return None
