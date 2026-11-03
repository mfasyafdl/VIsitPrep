# Data contract

Version 1

## Conventions

- null means unknown. An empty list with a null `*_denied` flag means "not asked / not answered". An explicit denial ("I have no allergies") keeps the list empty and sets the `*_denied` flag to true.
- Text fields keep the patient's own wording, including uncertainty.
- core/ is stateless and has no gradio dependency. ui/ has no business logic.
- There is no patient name field anywhere (privacy: users are told not to enter identifying details).

## PatientRecord

Dataclass; `record_to_dict` / `record_from_dict` round-trip exactly.

| Field | Type | Notes |
| --- | --- | --- |
| patient_age | int or null | years, 0–130 |
| patient_age_text | str or null | patient's wording, e.g. "7 years old" |
| patient_sex | str or null | one of SEX_VALUES = ("female", "male", "other", "not-specified") |
| reporting_on_behalf | bool or null | true when the reporter is not the patient |
| reporter_relationship | str or null | reporter's wording, e.g. "mother" |
| complaint | str or null | chief complaint, patient's words |
| symptoms | list[str] | each in the patient's words |
| onset | str or null | e.g. "yesterday afternoon" |
| duration | str or null | e.g. "about a week" |
| severity | str or null | one of SEVERITY_LEVELS = ("mild", "moderate", "severe") |
| severity_note | str or null | |
| medicines | list[Medicine] | |
| medicines_denied | bool or null | |
| allergies | list[str] | |
| allergies_denied | bool or null | |
| medical_history | list[str] | |
| medical_history_denied | bool or null | |
| pregnant | bool or null | only when the patient states it |
| concerns | list[str] | the patient's own questions or worries |
| missing_information | list[str] | recomputed by core; values from MISSING_FIELD_KEYS |

`MISSING_FIELD_KEYS = ("severity", "onset", "duration", "medicines", "allergies", "medical_history", "age", "sex", "concerns")`

A field is missing when its value is None, or for lists when the list is empty and the `*_denied` flag is not true.

## Example: full PatientRecord

```json
{
  "patient_age": 34,
  "patient_age_text": "34 years old",
  "patient_sex": "female",
  "reporting_on_behalf": false,
  "reporter_relationship": null,
  "complaint": "sore throat and mild cough",
  "symptoms": [
    "sore throat, worse when swallowing",
    "mild dry cough, mostly at night"
  ],
  "onset": "Tuesday morning",
  "duration": "about 3 days",
  "severity": "mild",
  "severity_note": "annoying, but I can eat and sleep",
  "medicines": [
    {
      "name": "honey and lemon tea",
      "medicine_type": "unknown",
      "dose": "one cup",
      "frequency": "twice a day",
      "duration": "2 days",
      "notes": "helps a little"
    }
  ],
  "medicines_denied": null,
  "allergies": [],
  "allergies_denied": true,
  "medical_history": [
    "mild asthma as a child"
  ],
  "medical_history_denied": null,
  "pregnant": null,
  "concerns": [
    "is this something to worry about?"
  ],
  "missing_information": []
}
```

## Medicine

Dataclass.

| Field | Type | Notes |
| --- | --- | --- |
| name | str | |
| medicine_type | str | one of MEDICINE_TYPES = ("prescription", "over-the-counter", "herbal", "supplement", "unknown") |
| dose | str or null | |
| frequency | str or null | |
| duration | str or null | |
| notes | str or null | |

## QuestionAnswer

Dataclass: `question: str`, `answer: str`.

## Alert

Dataclass: `code: str`, `message: str`, `level: str` ("urgent" or "attention").

## SummaryOutput

Dataclass: `doctor_card: str`, `patient_script: str`, `priority_questions: list[str]` (1 to 3 items).

## Validation

`validate_record(record) -> list[str]` of English error strings (empty = valid). Checks: enum values, non-empty strings, age 0–130, and a `*_denied` flag of true together with a non-empty list is an error. `SchemaError(ValueError)` is raised by `record_from_dict` on invalid input.

## Callable interfaces

All in core/, exact signatures:

```
core.llm.load_config() -> LLMConfig
core.llm.chat_json(system: str, user: str, *, validate: Callable[[dict], list[str]], config: LLMConfig | None = None, max_tokens: int = 4000, timeout: float = 120.0, max_retries: int = 2, max_repairs: int = 1) -> dict
core.redflag.scan_text(*texts: str) -> list[Alert]                  # rule-based, no network
core.redflag.check_alerts(record: PatientRecord) -> list[Alert]     # rule-based, no network
core.extract.extract_record(story: str, details: dict | None = None, *, config: LLMConfig | None = None) -> PatientRecord
    # details may hold patient_age, patient_age_text, patient_sex from the form; they override extracted values
core.interview.next_question(record: PatientRecord, asked: list[QuestionAnswer], skipped: list[str], max_questions: int = 5) -> str | None
    # rule-based, no network; None when len(asked) + len(skipped) >= max_questions or nothing useful is missing
core.interview.merge_answers(record: PatientRecord, asked: list[QuestionAnswer], *, config: LLMConfig | None = None) -> PatientRecord
    # ONE model call for all answers; returns a new record; never drops a known fact
core.summarize.generate_summary(record: PatientRecord, asked: list[QuestionAnswer], *, config: LLMConfig | None = None) -> SummaryOutput
```

## Errors (core.llm)

LLMError base, with ConfigError, LLMAuthError, LLMQuotaError, LLMNetworkError, LLMServerError, LLMResponseError and LLMContentFilterError (the provider's content filter rejected the text). Each has a safe English message with no API key and no patient text. On any error the caller's inputs are unchanged.

## Alerts

Urgent messages end with " In Indonesia, emergency medical services can be reached on 119. Please seek medical care now or tell the doctor immediately." No message ever says or implies that the patient is safe. Alerts are never part of any model input or output.

## Session flow the UI follows

1. story typed → alerts = scan_text(story) (instant) → record = extract_record(story, details)
2. loop: q = next_question(record, asked, skipped); answer → asked.append(QuestionAnswer(q, answer)); skip → skipped.append(q)
3. on entering review: record = merge_answers(record, asked); alerts = scan_text(story, *answers) + check_alerts(record)
4. patient edits the record in review → alerts recomputed → confirm
5. summary = generate_summary(record, asked)

At most 3 model calls per session: extract, merge, summary.

## Fixtures (tests and preview only)

All people and details in core/fixtures.py are fictional. The module defines:

- `FIXTURE_NAMES = ("fever_adult", "child_cough", "chest_pain")`
- `FIXTURE_EMPTY` — the empty record with missing_information recomputed
- `FIXTURE_FEVER_ADULT` — fictional 34-year-old female with a fever and headache; allergies explicitly denied
- `FIXTURE_CHILD_COUGH` — fictional 7-year-old male with a cough worse at night, reported by his mother
- `FIXTURE_CHEST_PAIN` — fictional 52-year-old female with a tight chest pain that comes and goes
- `FIXTURE_STORIES` — dict keyed by FIXTURE_NAMES; one first-person story per fixture, copied exactly
- `FIXTURE_SUMMARIES` — dict keyed by FIXTURE_NAMES; fictional example output for the UI preview only
- `all_fixtures() -> dict[str, PatientRecord]` — keys "empty" plus FIXTURE_NAMES; values are deep copies
- `get_fixture(name: str) -> PatientRecord` — deep copy; "empty" is allowed; unknown name raises KeyError
- `get_summary(name: str) -> SummaryOutput` — deep copy; unknown name raises KeyError
- `match_story(story: str) -> str | None` — exact match after stripping and collapsing all runs of whitespace to one space; no fuzzy matching

UI code uses get_fixture and get_summary (copies), never the module constants directly.

## Follow-up questions (rule-based)

`PRIORITY_FIELDS = ("severity", "onset", "duration", "medicines", "allergies", "medical_history", "age", "sex", "concerns")`

Questions asked when the patient reports about themself (`reporting_on_behalf` is false or null):

| Field | Question |
| --- | --- |
| severity | How bad is it: mild, moderate or severe? |
| onset | When did it start? |
| duration | How long has it been going on? |
| medicines | Are you taking any medicines, herbal remedies or supplements? Please name them. |
| allergies | Do you have any allergies? |
| medical_history | Do you have any ongoing or past health conditions? |
| age | How old are you? |
| sex | What is your sex? |
| concerns | Is there anything you are worried about or want to ask the doctor? |

Questions asked when the reporter answers on behalf of the patient (`reporting_on_behalf` is true):

| Field | Question |
| --- | --- |
| severity | How bad is it: mild, moderate or severe? |
| onset | When did it start? |
| duration | How long has it been going on? |
| medicines | Is the patient taking any medicines, herbal remedies or supplements? Please name them. |
| allergies | Does the patient have any allergies? |
| medical_history | Does the patient have any ongoing or past health conditions? |
| age | How old is the patient? |
| sex | What is the patient's sex? |
| concerns | Is there anything you are worried about or want to ask the doctor? |

Rules:

- `next_question` returns None when `max_questions` is 0 or less, or when the number of asked questions plus skipped questions is already at least `max_questions`.
- The question table is chosen by `reporting_on_behalf`: true selects the on-behalf table; null or false selects the self table.
- A field counts as missing using the same rules as `missing_information` (recomputed with `missing_fields`, never read from `record.missing_information`, which may be stale).
- Walking `PRIORITY_FIELDS` in order, the question of the first missing field is returned, unless that question has already been asked or skipped. A question counts as already asked or skipped when its text equals the text of an asked or skipped question after lowercasing and trimming.
- When no missing field is left, `next_question` returns None.

## Red-flag alerts (rule-based)

`scan_text(*texts)` scans free patient text; `check_alerts(record)` scans complaint, symptoms, severity_note and concerns (never medical_history, which is past by definition). Both return `list[Alert]` deduplicated by code, urgent first, then sorted by code. Matching is case-insensitive with word boundaries; the straight apostrophe ' and the curly apostrophe ’ are treated the same; wherever "can't" appears, "cant", "cannot" and "can not" are also accepted.

| code | level | triggers | message |
| --- | --- | --- | --- |
| breathing_difficulty | urgent | difficulty breathing, difficulty in breathing, trouble breathing, hard to breathe, shortness of breath, short of breath, out of breath at rest, breathless, can't breathe, chest indrawing, stridor, struggling to breathe, struggle to breathe, can't catch my/his/her breath, gasping for air | You reported trouble breathing. |
| chest_pain | urgent | chest pain, pain in my/his/her/the chest, tight/tightness in my/his/her/the chest, chest feels tight, pressure on/in my/his/her/the chest, chest hurts, chest is hurting, chest is tight, tight chest, chest tightness, chest feels heavy | You reported chest pain or tightness. |
| heavy_bleeding | urgent | heavy/severe/uncontrolled bleeding, bleeding that won't stop, vomiting blood, coughing up blood, blood in (the) stool/vomit/urine | You reported heavy bleeding or blood where it should not be. |
| allergic_reaction | urgent | swelling of the face/lips/tongue/throat/eyes/mouth, swollen face/lips/tongue/throat, throat feels tight, throat is closing, difficulty swallowing, can't swallow | You reported swelling of the face, lips, tongue or throat, or trouble swallowing. |
| seizure | urgent | seizure(s), convulsion(s), convulsing, having a fit, had a fit ("had a fit" and "having a fit" do not count when followed by " of") | You reported a seizure or convulsion. |
| altered_consciousness | urgent | unconscious, fainted, fainting, passed out, blacked out, is confused, seems confused, very confused, lethargic, hard to wake | You reported fainting, confusion or being hard to wake. |
| cannot_drink | urgent | can't/won't/refuses to drink, can't/won't/refuses to breastfeed, not drinking anything | You reported being unable to drink or breastfeed. |
| neck_stiffness | urgent | stiff neck, neck is stiff, can't touch chin to chest | You reported a stiff neck. |
| high_fever | attention | high fever; "fever" or "temperature" followed within 3 words by a number of 39 or more (for example "temperature of 39", "my temperature was 39", "fever is 39.5", "fever reached 40 degrees"), including decimals and an optional "degrees", "°C" or "C"; numbers below 39 never trigger; the number does not count when it is followed (after optional spaces) by minutes, mins, hours, hrs, days, weeks, months, years or times | You reported a high fever. |
| persistent_vomiting | attention | vomiting all day, vomiting many/multiple/several times, can't keep food/water/anything down | You reported vomiting many times or not keeping food or water down. |
| infant_fever | urgent | record-only: patient_age is 0 and the word "fever" appears unsuppressed in complaint or symptoms | You reported a fever in a baby under one year old. |
| pregnancy_danger | urgent | record-only: pregnant is true and the record text has an unsuppressed bleeding, severe headache, severe abdominal or belly pain, trouble breathing, seizure or convulsion, or high fever trigger | You reported a warning sign during pregnancy. |

Urgent messages end with " In Indonesia, emergency medical services can be reached on 119. Please seek medical care now or tell the doctor immediately." Attention messages end with " Please make sure to tell your doctor about this during the visit."

Suppression: the text is split into sentences on ".", "!", "?" and line breaks. A trigger is suppressed when a negation word (no, not, never, without, don't, doesn't, didn't, isn't, wasn't, denies, none) appears within the 4 words before it in the same sentence, unless that negation word is part of the uncertainty phrases "don't know", "do not know", "not sure", "unsure" or "no idea", which are uncertainty, not denial. A trigger is also suppressed when the same sentence contains a past marker (as a child, as a baby, as a kid, years ago, last year, in the past, used to), unless the same sentence also contains a present marker (now, again, today, still, back, this morning, since yesterday, right now).

Record-only rules: `check_alerts` adds infant_fever (urgent) when patient_age is 0 and the word "fever" appears unsuppressed in complaint or symptoms, and adds pregnancy_danger (urgent) when pregnant is true and the record text has an unsuppressed bleeding, severe headache, severe abdominal or belly pain, trouble breathing, seizure or convulsion, or high fever trigger.

Sources: Kemenkes RI danger signs (https://www.kemkes.go.id/), PSC 119 (https://psc119.kemkes.go.id/), IDAI child danger signs (https://www.idai.or.id/), WHO IMCI danger signs (https://www.who.int/).

Alerts are a safety prompt based on fixed rules, not a diagnosis.
