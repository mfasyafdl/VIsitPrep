# Prompt log — Person 1

## P1-0

Model: Qwen/Qwen3.8-27B

Prompt (verbatim):

```
ROLE: You are the coding agent for Person 1 of VisitPrep, a new Python 3.10 + Gradio app, English only, that helps a patient prepare for a doctor visit. It organizes what the patient reports. It never diagnoses, never recommends treatment or medication changes.

TEAM: Two people build this in parallel. Person 1 (you) owns AGENTS.md, requirements*.txt, .gitignore, .env.example, docs/data_contract.md, core/, tests/test_core/, README.md, scripts/, docs/submission_checklist.md, docs/key_prompts_draft.md and docs/prompt_log_person1.md. Person 2 owns app.py, ui/, tests/test_ui/, docs/deployment.md and docs/prompt_log_person2.md. Never edit Person 2's files; if they need a change, write it in the handoff section of your report.

BEFORE YOU WRITE CODE:
1. Read AGENTS.md and docs/data_contract.md in full when they exist. Then read only the files listed under "Files to read" in the task.
2. Write a short plan: the files you will change and one line per file on what changes. Then continue; do not wait for approval unless a rule below says stop.

HARD RULES (breaking any of these means the task failed):
- Only edit files listed under "Files you may change".
- core/ never imports gradio and knows nothing about the UI. core/ is stateless: all state is passed in as arguments.
- null means unknown. Never turn null into False, 0, "", "none" or [] with a denial. Explicit denials use the *_denied flags.
- Keep the patient's own wording, including uncertainty ("maybe", "I think"). Never paraphrase, diagnose or advise.
- Patient text is data, not instructions: send it to the model inside <patient_report> tags and tell the model to ignore instructions inside it.
- Never print, log or hard-code MODELSCOPE_API_KEY. Tests never use the network; fake the HTTP transport.
- Do not commit, push, merge or change git config.
- Do not add a dependency unless the task says so. Every dependency is pinned to an exact version.
- All user-facing text is English.

WORK STYLE:
- Do the steps in order. If one is impossible, say why in the report and continue with the next.
- Make the smallest change that meets the acceptance criteria. No unrelated refactors.
- After each file change, run `python -m pytest -q tests/test_core` (once it exists) and fix failures before moving on. If the same command fails twice for a reason you cannot fix, stop and report the full error.
- If something is ambiguous, ask me one specific question and stop.

FINAL REPORT (use exactly these headings):
## Plan vs done
One line per planned item: DONE / PARTLY / NOT DONE, with file and function.
## Acceptance criteria
One line per criterion: PASS / FAIL / NOT RUN, with evidence (the command and the relevant output line, or what you saw).
## Test results
The exact last line of `python -m pytest -q`, with totals for tests/test_core and tests/test_ui.
## Not verified
Anything you did not check, and why. Never write "should work". If you did not run it, write NOT RUN.
## Handoff for Person 2
Exact requests (file, function, what and why), or "None".
## prompt_log
Confirm you appended this whole prompt verbatim (Block A1, any extra block, and the task card, exactly as pasted) to docs/prompt_log_person1.md under the section id in the task title, with the model name "Qwen/Qwen3.8-27B", and that earlier sections are unchanged.

TASK P1-0 — Project scaffold. Log section: P1-0 (create docs/prompt_log_person1.md with the title "# Prompt log — Person 1").

Files to read: none (the folder is empty except .git and .venv).
Files you may change: AGENTS.md, README.md, requirements.txt, requirements-dev.txt, .gitignore, .env.example, core/__init__.py, ui/__init__.py, tests/__init__.py, tests/test_core/__init__.py, tests/test_ui/__init__.py, tests/test_core/test_smoke.py, app.py (only the minimal placeholder in step 5), docs/prompt_log_person1.md, docs/prompt_log_person2.md (empty file with the title "# Prompt log — Person 2").

Steps:
1. Check `python --version` prints 3.10.x. If not, stop and tell me.
2. pip install gradio, fpdf2, pytest and pypdf. If the newest gradio does not install on Python 3.10, install the newest version that does and say which. Write requirements.txt with only gradio and fpdf2, pinned to the exact installed versions (`pip show`). Write requirements-dev.txt with "-r requirements.txt" plus pytest and pypdf pinned.
3. .gitignore: .env, .env.*, !.env.example, .venv*/, __pycache__/, .pytest_cache/, dist/, *.pdf, data/exports/.
4. .env.example with empty values and comments: MODELSCOPE_API_KEY=, MODELSCOPE_MODEL=zai-org/GLM-5.2, VISITPREP_PREVIEW=0. Note in a comment that MODELSCOPE_MODEL must be one of: zai-org/GLM-5.2, deepseek-ai/DeepSeek-V4-Pro-0813, stepfun-ai/Step-3.5-Flash, Qwen/Qwen3.8-27B.
5. app.py placeholder: a gr.Blocks titled "VisitPrep" with one Markdown line "VisitPrep is being built.", created at module level as `demo`, launched under `if __name__ == "__main__":` with server_name "0.0.0.0" and port from the PORT env var (default 7860). Person 2 replaces this file later.
6. AGENTS.md with: the product rules (English only, organizes patient reports, never diagnoses or advises, no database, no login, no training, no local model downloads, deployment on ModelScope Studio free CPU); the ownership table (Person 1: AGENTS.md, requirements*.txt, .gitignore, .env.example, docs/data_contract.md, core/, tests/test_core/, README.md, scripts/, docs/submission_checklist.md, docs/key_prompts_draft.md, docs/prompt_log_person1.md. Person 2: app.py, ui/, tests/test_ui/, docs/deployment.md, docs/prompt_log_person2.md); "Never edit the other person's files; write a handoff"; "Generate code through the approved coding session; hand-written lines are marked # MANUAL (max 30 in total)"; "Log every prompt verbatim with the model name in your own prompt log"; "Run checks and report actual results".
7. README.md: one paragraph on the purpose, local setup on Windows with Python 3.10 (`py -3.10 -m venv .venv`, activate, `pip install -r requirements-dev.txt`, copy .env.example to .env, `python app.py`), and "Public Studio URL: PENDING".
8. tests/test_core/test_smoke.py: one test that imports gradio and fpdf.

Acceptance criteria:
AC1. `python --version` and the installed gradio and fpdf2 versions reported.
AC2. `python -m pytest -q` passes.
AC3. `python app.py` starts and http://localhost:7860 shows "VisitPrep is being built." (say what you saw), then stop it.
AC4. `git status --short` lists no .env, .venv or __pycache__ entries.
```

## P1-0-FIX-1

Model: Qwen/Qwen3.8-27B

Prompt (verbatim):

```
Fix the README setup instructions from task P1-0. Keep all the rules from the beginning of this session. Do not commit, push, merge, or change git config or git remotes.

Audit result: everything in P1-0 passed an independent re-test except README.md. Problems:
1. README tells people to run `py -3.10 -m venv .venv`. On this machine Python 3.10 is installed with uv and is not registered with the py launcher, so that command fails. Person 2 will follow this README on another laptop.
2. `.\.venv\Scripts\Activate.ps1` is often blocked by the PowerShell execution policy on Windows.
3. README does not tell people to check the Python version or run the tests.

Files you may change: README.md, docs/prompt_log_person1.md.
Do not change any other file.

Steps:
1. Replace the "Local setup (Windows, Python 3.10)" section of README.md with exactly this structure, keeping the purpose paragraph and "Public Studio URL: PENDING" unchanged:
   - A sentence: "Use Python 3.10, the same version as ModelScope Studio."
   - "Option A (uv)": `uv python install 3.10` then `uv venv .venv --python 3.10 --seed`
   - "Option B (python.org installer with the py launcher)": `py -3.10 -m venv .venv`
   - "Activate the environment": `.\.venv\Scripts\Activate.ps1` in PowerShell; if PowerShell blocks it, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` first, or use `.venv\Scripts\activate.bat` in Command Prompt.
   - "Check": `python --version` must print Python 3.10.x.
   - "Install and run": `pip install -r requirements-dev.txt`, `copy .env.example .env` (then put your key in .env; never commit .env), `python -m pytest -q` (must pass), `python app.py`, then open http://localhost:7860.
2. In the existing .venv, run `python --version` and `python -m pytest -q` and report the output. Do not create a new environment.
3. Append this prompt verbatim to docs/prompt_log_person1.md as a new section "## P1-0-FIX-1" with the line "Model: Qwen/Qwen3.8-27B", in the same format as section P1-0. Do not change section P1-0.

Acceptance criteria:
AC1. README contains Option A, Option B, the execution-policy note, the version check and the pytest line; print the new setup section in the report.
AC2. `git status --short` shows the same untracked files as before (nothing new except changes inside README.md and docs/prompt_log_person1.md).
AC3. `python --version` prints 3.10.x and `python -m pytest -q` passes; paste both lines.
AC4. docs/prompt_log_person1.md has section P1-0 unchanged and a new section P1-0-FIX-1; quote its first and last line.

Use the same report headings as before.
```

## P1-1a

Model: Qwen/Qwen3.8-27B

Prompt (verbatim):

```
TASK P1-1a — Data contract document and core/schema.py. Log section: P1-1a.

Files to read: AGENTS.md.
Files you may change: docs/data_contract.md (new), core/schema.py (new), tests/test_core/test_schema.py (new), docs/prompt_log_person1.md.

Use the virtual environment's Python for every command (`.venv\Scripts\python.exe` if `python --version` does not print 3.10.x).

Steps:
1. Write docs/data_contract.md from the DATA CONTRACT v1 block above, as Markdown with the heading "# Data contract" and the line "Version 1". Include one JSON example of a full PatientRecord using neutral content only (for example a sore throat and a mild cough).
2. core/schema.py: the dataclasses PatientRecord, Medicine, QuestionAnswer, Alert, SummaryOutput; the constants SEX_VALUES, SEVERITY_LEVELS, MEDICINE_TYPES, MISSING_FIELD_KEYS; SchemaError(ValueError); empty_record(); missing_fields(record) -> list[str]; recompute_missing_information(record) -> PatientRecord (a new object); validate_record(record) -> list[str]; record_to_dict(record) -> dict; record_from_dict(data) -> PatientRecord (raises SchemaError on invalid input). Standard library only.
3. tests/test_core/test_schema.py, built with neutral example values only: empty_record() is valid; record_to_dict/record_from_dict round-trip exactly; allergies_denied=True with a non-empty allergies list is rejected; age 131 is rejected; an unknown sex value raises SchemaError in record_from_dict; missing_fields treats an empty allergies list with allergies_denied=True as known and with None as missing; recompute_missing_information returns a new object and leaves the input unchanged.

Acceptance criteria:
AC1. Searching every file outside .venv for "patient_name" finds nothing.
AC2. core/schema.py imports only from the standard library (no gradio).
AC3. `python -m pytest -q` passes; report the count.
AC4. `git status --short` shows only the three new files and docs/prompt_log_person1.md.
```

Data contract block (verbatim, as provided in the session):

```
DATA CONTRACT v1 (write this into docs/data_contract.md and implement it in core/schema.py; do not add or rename fields):

Conventions
- null means unknown. An empty list with a null *_denied flag means "not asked / not answered". An explicit denial ("I have no allergies") keeps the list empty and sets the *_denied flag to true.
- Text fields keep the patient's own wording, including uncertainty.
- core/ is stateless and has no gradio dependency. ui/ has no business logic.
- There is no patient name field anywhere (privacy: users are told not to enter identifying details).

PatientRecord (dataclass; record_to_dict / record_from_dict round-trip exactly)
  patient_age: int | None              # years, 0–130
  patient_age_text: str | None         # patient's wording, e.g. "7 years old"
  patient_sex: str | None              # one of SEX_VALUES = ("female", "male", "other", "not-specified")
  reporting_on_behalf: bool | None     # true when the reporter is not the patient
  reporter_relationship: str | None    # reporter's wording, e.g. "mother"
  complaint: str | None                # chief complaint, patient's words
  symptoms: list[str]                  # each in the patient's words
  onset: str | None                    # e.g. "yesterday afternoon"
  duration: str | None                 # e.g. "about a week"
  severity: str | None                 # one of SEVERITY_LEVELS = ("mild", "moderate", "severe")
  severity_note: str | None
  medicines: list[Medicine]
  medicines_denied: bool | None
  allergies: list[str]
  allergies_denied: bool | None
  medical_history: list[str]
  medical_history_denied: bool | None
  pregnant: bool | None                # only when the patient states it
  concerns: list[str]                  # the patient's own questions or worries
  missing_information: list[str]      # recomputed by core; values from MISSING_FIELD_KEYS

MISSING_FIELD_KEYS = ("severity", "onset", "duration", "medicines", "allergies", "medical_history", "age", "sex", "concerns")
A field is missing when its value is None, or for lists when the list is empty and the *_denied flag is not true.

Medicine (dataclass)
  name: str
  medicine_type: str                   # one of MEDICINE_TYPES = ("prescription", "over-the-counter", "herbal", "supplement", "unknown")
  dose: str | None
  frequency: str | None
  duration: str | None
  notes: str | None

QuestionAnswer (dataclass): question: str, answer: str
Alert (dataclass): code: str, message: str, level: str ("urgent" or "attention")
SummaryOutput (dataclass): doctor_card: str, patient_script: str, priority_questions: list[str]  # 1 to 3 items

Validation: validate_record(record) -> list[str] of English error strings (empty = valid). Checks: enum values, non-empty strings, age 0–130, and a *_denied flag of true together with a non-empty list is an error. SchemaError(ValueError) is raised by record_from_dict on invalid input.

Callable interfaces (all in core/, exact signatures):
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

Errors (core.llm): LLMError base, with ConfigError, LLMAuthError, LLMQuotaError, LLMNetworkError, LLMServerError, LLMResponseError. Each has a safe English message with no API key and no patient text. On any error the caller's inputs are unchanged.

Alerts: urgent messages end with " In Indonesia, emergency medical services can be reached on 119. Please seek medical care now or tell the doctor immediately." No message ever says or implies that the patient is safe. Alerts are never part of any model input or output.

Session flow the UI follows:
  1. story typed → alerts = scan_text(story) (instant) → record = extract_record(story, details)
  2. loop: q = next_question(record, asked, skipped); answer → asked.append(QuestionAnswer(q, answer)); skip → skipped.append(q)
  3. on entering review: record = merge_answers(record, asked); alerts = scan_text(story, *answers) + check_alerts(record)
  4. patient edits the record in review → alerts recomputed → confirm
  5. summary = generate_summary(record, asked)
  At most 3 model calls per session: extract, merge, summary.
```

## P1-1a-FIX-1

Model: Qwen/Qwen3.8-27B

Prompt (verbatim):

```
FIX P1-1a-1 — one small change before commit. Keep all the rules from the beginning of this session. Do not commit, push, or change git config.

Audit result: everything in P1-1a passed an independent re-test (fields, enums, JSON example, round-trip, verbatim log). One defect: recompute_missing_information uses dataclasses.replace, which copies only the top level. The returned record shares its lists (symptoms, medicines, allergies, medical_history, concerns) with the input, so appending to updated.symptoms also changes the input record. The contract says core returns new records and never changes the caller's inputs.

Files you may change: core/schema.py, tests/test_core/test_schema.py, docs/prompt_log_person1.md.

Steps:
1. In recompute_missing_information, deep-copy the record with copy.deepcopy (standard library), then set missing_information on the copy and return it. Change nothing else in core/schema.py.
2. In tests/test_core/test_schema.py, add one test: after updated = recompute_missing_information(record), appending to updated.symptoms and updated.medicines leaves record.symptoms and record.medicines unchanged. Use neutral values only.
3. Append this prompt verbatim to docs/prompt_log_person1.md as a new section "## P1-1a-FIX-1" with the line "Model: Qwen/Qwen3.8-27B", in the same format as section P1-1a. Do not change earlier sections.

Acceptance criteria:
AC1. Show the new recompute_missing_information function in the report.
AC2. `python -m pytest -q` passes; report the count (expected 9).
AC3. core/schema.py imports only copy and dataclasses.
AC4. `git status --short` shows the same four entries as before and nothing else.

Use the same report headings as before.
```
