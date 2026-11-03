"""Rule-based red-flag alerts: scan_text(*texts) scans free patient text and check_alerts(record) scans a PatientRecord; both return list[Alert] deduplicated by code, urgent first then sorted by code, with no model call, no network and no state, per docs/data_contract.md."""

import re

from core.schema import Alert, PatientRecord

# Match "can't" in every accepted spelling; the curly apostrophe is normalised
# to the straight one before matching, so only the straight form is written.
_CANT = r"(?:can'?t|cant|cannot|can not)"

URGENT_TAIL = (
    " In Indonesia, emergency medical services can be reached on 119. "
    "Please seek medical care now or tell the doctor immediately."
)
ATTENTION_TAIL = " Please make sure to tell your doctor about this during the visit."

_LEVELS: dict[str, str] = {
    "breathing_difficulty": "urgent",
    "chest_pain": "urgent",
    "heavy_bleeding": "urgent",
    "allergic_reaction": "urgent",
    "seizure": "urgent",
    "altered_consciousness": "urgent",
    "cannot_drink": "urgent",
    "neck_stiffness": "urgent",
    "infant_fever": "urgent",
    "pregnancy_danger": "urgent",
    "high_fever": "attention",
    "persistent_vomiting": "attention",
}

_MESSAGES: dict[str, str] = {
    "breathing_difficulty": "You reported trouble breathing.",
    "chest_pain": "You reported chest pain or tightness.",
    "heavy_bleeding": "You reported heavy bleeding or blood where it should not be.",
    "allergic_reaction": (
        "You reported swelling of the face, lips, tongue or throat, "
        "or trouble swallowing."
    ),
    "seizure": "You reported a seizure or convulsion.",
    "altered_consciousness": "You reported fainting, confusion or being hard to wake.",
    "cannot_drink": "You reported being unable to drink or breastfeed.",
    "neck_stiffness": "You reported a stiff neck.",
    "high_fever": "You reported a high fever.",
    "persistent_vomiting": (
        "You reported vomiting many times or not keeping food or water down."
    ),
    "infant_fever": "You reported a fever in a baby under one year old.",
    "pregnancy_danger": "You reported a warning sign during pregnancy.",
}

# "fever" or "temperature" followed within 3 words by a number of 39 or more
# (integers from 39 up, decimals from 39.0 up); numbers below 39 never match.
# The number does not count when it is followed (after optional spaces) by a
# duration or count unit.
_FEVER_NUMBER = (
    r"\b(?:fever|temperature)\b(?:\s+\w+){0,2}\s+"
    r"(?:39(?:\.\d+)?|[4-9]\d(?:\.\d+)?|\d{3,}(?:\.\d+)?)"
    r"(?!\s*(?:minutes|mins|hours|hrs|days|weeks|months|years|times)\b)"
)

TRIGGERS: dict[str, tuple[re.Pattern, ...]] = {
    "breathing_difficulty": (
        re.compile(r"\bdifficulty breathing\b", re.IGNORECASE),
        re.compile(r"\btrouble breathing\b", re.IGNORECASE),
        re.compile(r"\bhard to breathe\b", re.IGNORECASE),
        re.compile(r"\bshortness of breath\b", re.IGNORECASE),
        re.compile(r"\bshort of breath\b", re.IGNORECASE),
        re.compile(r"\bout of breath at rest\b", re.IGNORECASE),
        re.compile(r"\bbreathless\b", re.IGNORECASE),
        re.compile(rf"\b{_CANT} breathe\b", re.IGNORECASE),
        re.compile(r"\bchest indrawing\b", re.IGNORECASE),
        re.compile(r"\bstridor\b", re.IGNORECASE),
        re.compile(r"\bdifficulty in breathing\b", re.IGNORECASE),
        re.compile(r"\bstruggling to breathe\b", re.IGNORECASE),
        re.compile(r"\bstruggle to breathe\b", re.IGNORECASE),
        re.compile(rf"\b{_CANT} catch (?:my|his|her) breath\b", re.IGNORECASE),
        re.compile(r"\bgasping for air\b", re.IGNORECASE),
    ),
    "chest_pain": (
        re.compile(r"\bchest pain\b", re.IGNORECASE),
        re.compile(r"\bpain in (?:my|his|her|the) chest\b", re.IGNORECASE),
        re.compile(r"\b(?:tight|tightness) in (?:my|his|her|the) chest\b", re.IGNORECASE),
        re.compile(r"\bchest feels tight\b", re.IGNORECASE),
        re.compile(r"\bpressure (?:on|in) (?:my|his|her|the) chest\b", re.IGNORECASE),
        re.compile(r"\bchest hurts\b", re.IGNORECASE),
        re.compile(r"\bchest is hurting\b", re.IGNORECASE),
        re.compile(r"\bchest is tight\b", re.IGNORECASE),
        re.compile(r"\btight chest\b", re.IGNORECASE),
        re.compile(r"\bchest tightness\b", re.IGNORECASE),
        re.compile(r"\bchest feels heavy\b", re.IGNORECASE),
    ),
    "heavy_bleeding": (
        re.compile(r"\b(?:heavy|severe|uncontrolled) bleeding\b", re.IGNORECASE),
        re.compile(r"\bbleeding that won'?t stop\b", re.IGNORECASE),
        re.compile(r"\bvomiting blood\b", re.IGNORECASE),
        re.compile(r"\bcoughing up blood\b", re.IGNORECASE),
        re.compile(r"\bblood in (?:the )?(?:stool|vomit|urine)\b", re.IGNORECASE),
    ),
    "allergic_reaction": (
        re.compile(
            r"\bswelling of the (?:face|lips|tongue|throat|eyes|mouth)\b",
            re.IGNORECASE,
        ),
        re.compile(r"\bswollen (?:face|lips|tongue|throat)\b", re.IGNORECASE),
        re.compile(r"\bthroat feels tight\b", re.IGNORECASE),
        re.compile(r"\bthroat is closing\b", re.IGNORECASE),
        re.compile(r"\bdifficulty swallowing\b", re.IGNORECASE),
        re.compile(rf"\b{_CANT} swallow\b", re.IGNORECASE),
    ),
    "seizure": (
        re.compile(r"\bseizures?\b", re.IGNORECASE),
        re.compile(r"\bconvulsions?\b", re.IGNORECASE),
        re.compile(r"\bconvulsing\b", re.IGNORECASE),
        re.compile(r"\bhaving a fit\b(?!\s+of\b)", re.IGNORECASE),
        re.compile(r"\bhad a fit\b(?!\s+of\b)", re.IGNORECASE),
    ),
    "altered_consciousness": (
        re.compile(r"\bunconscious\b", re.IGNORECASE),
        re.compile(r"\bfainted\b", re.IGNORECASE),
        re.compile(r"\bfainting\b", re.IGNORECASE),
        re.compile(r"\bpassed out\b", re.IGNORECASE),
        re.compile(r"\bblacked out\b", re.IGNORECASE),
        re.compile(r"\bis confused\b", re.IGNORECASE),
        re.compile(r"\bseems confused\b", re.IGNORECASE),
        re.compile(r"\bvery confused\b", re.IGNORECASE),
        re.compile(r"\blethargic\b", re.IGNORECASE),
        re.compile(r"\bhard to wake\b", re.IGNORECASE),
    ),
    "cannot_drink": (
        re.compile(
            rf"\b(?:{_CANT}|won'?t|refuses to) (?:drink|breastfeed)\b",
            re.IGNORECASE,
        ),
        re.compile(r"\bnot drinking anything\b", re.IGNORECASE),
    ),
    "neck_stiffness": (
        re.compile(r"\bstiff neck\b", re.IGNORECASE),
        re.compile(r"\bneck is stiff\b", re.IGNORECASE),
        re.compile(rf"\b{_CANT} touch chin to chest\b", re.IGNORECASE),
    ),
    "high_fever": (
        re.compile(r"\bhigh fever\b", re.IGNORECASE),
        re.compile(_FEVER_NUMBER, re.IGNORECASE),
    ),
    "persistent_vomiting": (
        re.compile(r"\bvomiting all day\b", re.IGNORECASE),
        re.compile(r"\bvomiting (?:many|multiple|several) times\b", re.IGNORECASE),
        re.compile(rf"\b{_CANT} keep (?:food|water|anything) down\b", re.IGNORECASE),
    ),
}

_NEGATIONS = frozenset(
    {
        "no",
        "not",
        "never",
        "without",
        "don't",
        "doesn't",
        "didn't",
        "isn't",
        "wasn't",
        "denies",
        "none",
    }
)

_PAST_MARKERS = re.compile(
    r"\b(?:as a child|as a baby|as a kid|years ago|last year|in the past|used to)\b",
    re.IGNORECASE,
)

# A past marker does not suppress when the same sentence also contains a
# present marker.
_PRESENT_MARKERS = re.compile(
    r"\b(?:right now|this morning|since yesterday|now|again|today|still|back)\b",
    re.IGNORECASE,
)

_SENTENCE_SPLIT = re.compile(r"[.!?|\n]+")

_FEVER_WORD = re.compile(r"\bfever\b", re.IGNORECASE)

_PREGNANCY_MARKERS: tuple[re.Pattern, ...] = (
    re.compile(r"\bbleed(?:ing|s|ed)?\b", re.IGNORECASE),
    re.compile(r"\bsevere headache\b", re.IGNORECASE),
    re.compile(r"\bsevere (?:abdominal|belly) pain\b", re.IGNORECASE),
    re.compile(r"\btrouble breathing\b", re.IGNORECASE),
    re.compile(r"\bseizures?\b", re.IGNORECASE),
    re.compile(r"\bconvulsions?\b", re.IGNORECASE),
    *TRIGGERS["high_fever"],
)


def _is_uncertainty(words: list[str], index: int) -> bool:
    # "don't know", "do not know", "not sure" and "no idea" are uncertainty,
    # not denial; a negation word inside one of these phrases does not
    # suppress. ("unsure" is not a negation word and never suppresses.)

    def at(offset: int) -> str:
        j = index + offset
        if 0 <= j < len(words):
            return words[j].casefold()
        return ""

    word = at(0)
    if word == "don't" and at(1) == "know":
        return True
    if word == "not" and at(1) == "sure":
        return True
    if word == "not" and at(-1) == "do" and at(1) == "know":
        return True
    if word == "no" and at(1) == "idea":
        return True
    return False


def _negated(sentence: str, start: int) -> bool:
    words = sentence[:start].split()
    for index in range(max(0, len(words) - 4), len(words)):
        if words[index].casefold() in _NEGATIONS and not _is_uncertainty(words, index):
            return True
    return False


def _past_suppressed(sentence: str) -> bool:
    return bool(_PAST_MARKERS.search(sentence)) and not _PRESENT_MARKERS.search(
        sentence
    )


def _codes_in_sentence(sentence: str) -> set[str]:
    if not sentence.strip() or _past_suppressed(sentence):
        return set()
    found: set[str] = set()
    for code, patterns in TRIGGERS.items():
        for pattern in patterns:
            for match in pattern.finditer(sentence):
                if not _negated(sentence, match.start()):
                    found.add(code)
                    break
    return found


def _codes_in_text(text: str) -> set[str]:
    normalized = text.replace("\u2019", "'")
    found: set[str] = set()
    for sentence in _SENTENCE_SPLIT.split(normalized):
        found |= _codes_in_sentence(sentence)
    return found


def _unsuppressed_any(texts: list[str], patterns: tuple[re.Pattern, ...]) -> bool:
    for text in texts:
        normalized = text.replace("\u2019", "'")
        for sentence in _SENTENCE_SPLIT.split(normalized):
            if not sentence.strip() or _past_suppressed(sentence):
                continue
            for pattern in patterns:
                for match in pattern.finditer(sentence):
                    if not _negated(sentence, match.start()):
                        return True
    return False


def _alerts_from_codes(codes: set[str]) -> list[Alert]:
    ordered = sorted(
        codes, key=lambda code: (0 if _LEVELS[code] == "urgent" else 1, code)
    )
    return [
        Alert(
            code=code,
            message=_MESSAGES[code]
            + (URGENT_TAIL if _LEVELS[code] == "urgent" else ATTENTION_TAIL),
            level=_LEVELS[code],
        )
        for code in ordered
    ]


def _record_texts(record: PatientRecord) -> list[str]:
    texts: list[str] = []
    if record.complaint:
        texts.append(record.complaint)
    texts.extend(symptom for symptom in record.symptoms if symptom)
    if record.severity_note:
        texts.append(record.severity_note)
    texts.extend(concern for concern in record.concerns if concern)
    return texts


def scan_text(*texts: str) -> list[Alert]:
    codes: set[str] = set()
    for text in texts:
        if text:
            codes |= _codes_in_text(text)
    return _alerts_from_codes(codes)


def check_alerts(record: PatientRecord) -> list[Alert]:
    texts = _record_texts(record)
    codes: set[str] = set()
    for text in texts:
        codes |= _codes_in_text(text)
    if record.patient_age == 0:
        baby_texts: list[str] = []
        if record.complaint:
            baby_texts.append(record.complaint)
        baby_texts.extend(symptom for symptom in record.symptoms if symptom)
        if _unsuppressed_any(baby_texts, (_FEVER_WORD,)):
            codes.add("infant_fever")
    if record.pregnant is True and _unsuppressed_any(texts, _PREGNANCY_MARKERS):
        codes.add("pregnancy_danger")
    return _alerts_from_codes(codes)
