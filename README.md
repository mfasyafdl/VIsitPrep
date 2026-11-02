# VisitPrep

VisitPrep is a small Python 3.10 + Gradio app that helps a patient prepare for a doctor visit by organizing what the patient reports, in the patient's own words; it never diagnoses and never recommends treatment or medication changes.

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

Public Studio URL: PENDING
