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
