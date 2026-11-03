"""Tests for the rule-based red-flag alerts (task P1-3)."""

import pytest

from core.fixtures import FIXTURE_STORIES, get_fixture
from core.redflag import check_alerts, scan_text
from core.schema import record_to_dict

URGENT_TAIL = (
    " In Indonesia, emergency medical services can be reached on 119. "
    "Please seek medical care now or tell the doctor immediately."
)
ATTENTION_TAIL = " Please make sure to tell your doctor about this during the visit."

EXPECTED_LEVELS = {
    "breathing_difficulty": "urgent",
    "chest_pain": "urgent",
    "heavy_bleeding": "urgent",
    "allergic_reaction": "urgent",
    "seizure": "urgent",
    "altered_consciousness": "urgent",
    "cannot_drink": "urgent",
    "neck_stiffness": "urgent",
    "high_fever": "attention",
    "persistent_vomiting": "attention",
    "infant_fever": "urgent",
    "pregnancy_danger": "urgent",
}

POSITIVE_TEXTS = {
    "breathing_difficulty": [
        "I can\u2019t breathe",
        "I cant breathe",
        "I cannot breathe",
        "I can not breathe",
        "I have difficulty breathing",
        "I have trouble breathing",
        "It is hard to breathe",
        "I have shortness of breath",
        "I am short of breath",
        "I am out of breath at rest",
        "I feel breathless",
        "There is chest indrawing",
        "The doctor heard stridor",
    ],
    "chest_pain": [
        "I have chest pain",
        "pain in my chest",
        "pain in his chest",
        "pain in her chest",
        "pain in the chest",
        "tightness in my chest",
        "tight in her chest",
        "my chest feels tight",
        "pressure on my chest",
        "pressure in his chest",
        "I have a tight pain in my chest",
    ],
    "heavy_bleeding": [
        "I have heavy bleeding",
        "severe bleeding",
        "uncontrolled bleeding",
        "bleeding that won't stop",
        "bleeding that won\u2019t stop",
        "vomiting blood",
        "coughing up blood",
        "blood in the stool",
        "blood in stool",
        "blood in the urine",
        "blood in vomit",
    ],
    "allergic_reaction": [
        "swelling of the face",
        "swelling of the lips",
        "swelling of the tongue",
        "swelling of the throat",
        "swelling of the eyes",
        "swelling of the mouth",
        "swollen face",
        "swollen lips",
        "swollen tongue",
        "swollen throat",
        "my throat feels tight",
        "my throat is closing",
        "difficulty swallowing",
        "I can't swallow",
        "I cant swallow",
    ],
    "seizure": [
        "I had a seizure",
        "she has seizures",
        "one convulsion",
        "he is convulsing",
        "having a fit",
        "she had a fit",
    ],
    "altered_consciousness": [
        "he is unconscious",
        "she fainted",
        "she is fainting",
        "he passed out",
        "she blacked out",
        "he is confused",
        "she seems confused",
        "he is very confused",
        "the baby is lethargic",
        "he is hard to wake",
    ],
    "cannot_drink": [
        "the baby can't drink",
        "she won't drink",
        "he refuses to drink",
        "the baby can\u2019t drink",
        "I can't breastfeed",
        "she refuses to breastfeed",
        "not drinking anything",
    ],
    "neck_stiffness": [
        "stiff neck",
        "her neck is stiff",
        "I can't touch chin to chest",
        "I cant touch chin to chest",
    ],
    "high_fever": [
        "high fever",
        "temperature of 39",
        "my temperature was 39",
        "fever is 39.5",
        "fever reached 40 degrees",
        "temperature 39.5",
        "fever of 40 degrees",
        "fever of 40\u00b0C",
        "fever of 40 C",
    ],
    "persistent_vomiting": [
        "vomiting all day",
        "vomiting many times",
        "vomiting multiple times",
        "vomiting several times",
        "I can't keep food down",
        "I cant keep water down",
        "I cannot keep anything down",
    ],
}

TEXT_CASES = [
    (code, text) for code, texts in POSITIVE_TEXTS.items() for text in texts
]


@pytest.mark.parametrize("code,text", TEXT_CASES)
def test_positive_text_fires_code(code, text):
    alerts = scan_text(text)
    codes = [alert.code for alert in alerts]
    assert code in codes
    alert = next(alert for alert in alerts if alert.code == code)
    assert alert.level == EXPECTED_LEVELS[code]


def test_curly_apostrophe_can_breathe():
    alerts = scan_text("I can\u2019t breathe")
    assert [alert.code for alert in alerts] == ["breathing_difficulty"]


def test_temperature_was_39_point_5():
    assert [a.code for a in scan_text("my temperature was 39.5")] == ["high_fever"]


NEGATIVE_TEXTS = [
    "no chest pain",
    "I don't have trouble breathing",
    "I had a seizure as a child",
    "my father had chest pain years ago",
    "I'm not short of breath",
    "",
    "temperature of 38.5",
]


@pytest.mark.parametrize("text", NEGATIVE_TEXTS)
def test_negative_text_has_no_alerts(text):
    assert scan_text(text) == []


def test_no_arguments_has_no_alerts():
    assert scan_text() == []


def test_fixture_story_chest_pain():
    assert [a.code for a in scan_text(FIXTURE_STORIES["chest_pain"])] == [
        "chest_pain"
    ]


def test_fixture_record_chest_pain():
    assert [a.code for a in check_alerts(get_fixture("chest_pain"))] == [
        "chest_pain"
    ]


def test_fixture_story_fever_adult():
    assert [a.code for a in scan_text(FIXTURE_STORIES["fever_adult"])] == [
        "high_fever"
    ]


def test_fixture_record_fever_adult():
    assert [a.code for a in check_alerts(get_fixture("fever_adult"))] == [
        "high_fever"
    ]


def test_fixture_story_child_cough():
    assert scan_text(FIXTURE_STORIES["child_cough"]) == []


def test_fixture_record_child_cough():
    assert check_alerts(get_fixture("child_cough")) == []


def test_medical_history_is_ignored():
    record = get_fixture("empty")
    record.medical_history = ["chest pain", "a seizure", "heavy bleeding"]
    assert check_alerts(record) == []


def test_urgent_sorts_before_attention():
    codes = [a.code for a in scan_text("chest pain. My temperature was 39")]
    assert codes == ["chest_pain", "high_fever"]


def test_deduplicated_across_texts():
    alerts = scan_text("chest pain", "pain in the chest", "")
    assert [alert.code for alert in alerts] == ["chest_pain"]


def _alert_for_code(code: str):
    if code == "infant_fever":
        record = get_fixture("empty")
        record.patient_age = 0
        record.complaint = "The baby has a fever"
        alerts = check_alerts(record)
    elif code == "pregnancy_danger":
        record = get_fixture("empty")
        record.pregnant = True
        record.complaint = "I have a severe headache"
        alerts = check_alerts(record)
    else:
        alerts = scan_text(POSITIVE_TEXTS[code][0])
    for alert in alerts:
        if alert.code == code:
            return alert
    raise AssertionError(f"no alert with code {code}")


@pytest.mark.parametrize("code", sorted(EXPECTED_LEVELS))
def test_message_level_tail_and_wording(code):
    alert = _alert_for_code(code)
    level = EXPECTED_LEVELS[code]
    tail = URGENT_TAIL if level == "urgent" else ATTENTION_TAIL
    assert alert.level == level
    assert alert.message.endswith(tail)
    lowered = alert.message.lower()
    for forbidden in ("safe", "diagnos", "treat", "take"):
        assert forbidden not in lowered


def test_infant_fever_positive():
    record = get_fixture("empty")
    record.patient_age = 0
    record.complaint = "The baby has a fever"
    assert [a.code for a in check_alerts(record)] == ["infant_fever"]


def test_infant_fever_requires_age_zero():
    record = get_fixture("empty")
    record.patient_age = 34
    record.complaint = "I have a fever"
    assert check_alerts(record) == []


def test_infant_fever_suppressed_by_negation():
    record = get_fixture("empty")
    record.patient_age = 0
    record.complaint = "no fever"
    assert check_alerts(record) == []


def test_pregnancy_danger_positive():
    record = get_fixture("empty")
    record.pregnant = True
    record.complaint = "I have a severe headache"
    assert [a.code for a in check_alerts(record)] == ["pregnancy_danger"]


def test_pregnancy_danger_requires_pregnant_true():
    record = get_fixture("empty")
    record.pregnant = None
    record.complaint = "I have a severe headache"
    assert check_alerts(record) == []


def test_check_alerts_is_pure():
    record = get_fixture("chest_pain")
    before = record_to_dict(record)
    check_alerts(record)
    check_alerts(record)
    assert record_to_dict(record) == before


FIX1_SENTENCES = [
    ("My chest hurts when I walk.", ("chest_pain",)),
    ("My chest is tight.", ("chest_pain",)),
    ("I have chest tightness.", ("chest_pain",)),
    ("Tight chest since this morning.", ("chest_pain",)),
    ("I can\u2019t catch my breath.", ("breathing_difficulty",)),
    ("She is struggling to breathe.", ("breathing_difficulty",)),
    ("Difficulty in breathing since last night.", ("breathing_difficulty",)),
    ("I don't know if it's chest pain.", ("chest_pain",)),
    ("I had chest pain years ago and now it is back.", ("chest_pain",)),
    ("I had chest pain years ago.", ()),
    ("I had a fever for 45 minutes.", ()),
    ("My temperature was 39 for 2 days.", ("high_fever",)),
    ("She had a fit of laughter.", ()),
    ("I don't have chest pain.", ()),
]


@pytest.mark.parametrize("text,expected", FIX1_SENTENCES)
def test_fix1_sentence(text, expected):
    assert [a.code for a in scan_text(text)] == list(expected)
