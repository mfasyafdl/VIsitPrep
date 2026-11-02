# AGENTS.md — VisitPrep

## Product rules

- English only: all user-facing text is English.
- The app helps a patient prepare for a doctor visit by organizing what the patient reports. It never diagnoses, and never recommends treatment or medication changes.
- No database, no login, no training, no local model downloads.
- Deployment target: ModelScope Studio free CPU.

## Ownership

| Person | Owns |
| --- | --- |
| Person 1 | AGENTS.md, requirements*.txt, .gitignore, .env.example, docs/data_contract.md, core/, tests/test_core/, README.md, scripts/, docs/submission_checklist.md, docs/key_prompts_draft.md, docs/prompt_log_person1.md |
| Person 2 | app.py, ui/, tests/test_ui/, docs/deployment.md, docs/prompt_log_person2.md |

- Never edit the other person's files; write a handoff.

## Code generation and logging

- Generate code through the approved coding session; hand-written lines are marked `# MANUAL` (max 30 in total).
- Log every prompt verbatim with the model name in your own prompt log.
- Run checks and report actual results.
