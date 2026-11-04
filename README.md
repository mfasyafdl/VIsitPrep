# VisitPrep

VisitPrep is a small Python 3.10 + Gradio app that helps a patient prepare for a doctor visit by organizing what the patient reports, in the patient's own words; it never diagnoses and never recommends treatment or medication changes.

The problem it solves: at a short doctor visit a patient forgets details and worries. VisitPrep organizes what the patient reports before the visit, so the patient arrives with a clear note instead of a half-remembered story.

## How it works

1. **Describe** — the patient types what is wrong, in their own words.
2. **Up to five questions** — the app asks short follow-up questions only about details that are missing (severity, onset, duration, medicines, allergies, medical history, age, sex, concerns).
3. **Check details** — the patient reviews and edits the organized details.
4. **Visit note** — the app writes a visit note for the doctor, with a "what to say" script and priority questions, and can save it as a PDF.

## Safety design

- Rule-based warning signs based on Indonesian emergency guidance; urgent signs end with the 119 emergency number. Every text the patient types is checked by these rules before any model call, and alerts are never part of any model input or output.
- No diagnosis or advice: the app organizes the patient's report; it never says the patient is safe.
- null means unknown: an unknown field stays unknown; the app never guesses.
- The patient's own words are kept, including uncertainty ("maybe", "I think").
- The doctor card is built by code, never by the model, so it can never invent, drop or reword a fact.
- A merge guard never drops a known fact when follow-up answers are merged in.

## Configuration

Environment variable names (set on the server; values are never committed):

- `MODELSCOPE_API_KEY`
- `MODELSCOPE_MODEL`
- `VISITPREP_PREVIEW`

## Models used

- Runtime model: `Qwen/Qwen3.8-27B` through ModelScope API-Inference with `enable_thinking` false.
- Tested fallback: `deepseek-ai/DeepSeek-V4-Pro-0813`.
- `zai-org/GLM-5.2` is in the allowed model list but was not used in testing.
- Coding model for the recorded prompts: `Qwen/Qwen3.8-27B` (OpenCode).

Public Studio URL: PENDING

## Limitations

- English only.
- Not a medical device: it organizes the patient's report, it does not diagnose or advise.
- Runs on the free ModelScope API quota, so the service may be unavailable when the quota is used up.
- Notes are sent to ModelScope to be organized; leave out your name, address and phone number.

## Licences

- Atkinson Hyperlegible Next — SIL OFL 1.1 (ui/assets/fonts/OFL.txt)
- Gradio — Apache-2.0
- fpdf2 — LGPL-3.0
- pypdf — BSD-3-Clause (tests only)

## Local setup (Windows, Python 3.10)

Use Python 3.10, the same version as ModelScope Studio.

**Option A (uv)**

```powershell
uv python install 3.10
uv venv .venv --python 3.10 --seed
```

**Option B (python.org installer with the py launcher)**

```powershell
py -3.10 -m venv .venv
```

**Activate the environment**

In PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks it, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` first, or use `.venv\Scripts\activate.bat` in Command Prompt.

**Check**

```powershell
python --version
```

This must print Python 3.10.x.

**Install and run**

```powershell
pip install -r requirements-dev.txt
copy .env.example .env
```

Then put your key in .env (never commit .env). Then:

```powershell
python -m pytest -q
python app.py
```

`python -m pytest -q` must pass, then open http://localhost:7860.
