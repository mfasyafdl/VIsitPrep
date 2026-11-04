# Deployment — ModelScope Studio

How to deploy VisitPrep to a public ModelScope Studio (free CPU). The
deployed app is English only.

## 1. Create the Studio

1. On modelscope.ai, go to **Studios** → **New Studio**.
2. Name the Studio using letters, numbers, hyphens and underscores only
   (no spaces or other symbols).
3. Visibility: **Public** (required for the competition).
4. Framework: **Gradio**. Resources: **free CPU** only. Environment: choose
   Python **3.10** (the guide's example version).
5. Wait for the Studio shell to be created, then open its **Contents** page.

UNVERIFIED: the exact entry-point field, start command and expected port in
the Studio settings, and whether ModelScope metadata in README.md is needed.
The official ModelScope documentation pages are JavaScript-rendered and could
not be read as static content (checked
<https://modelscope.ai/docs/studios/intro> and
<https://www.modelscope.ai/docs> on 2026-11-04). This app is written to run
as `python app.py`, binding 0.0.0.0 on port 7860 (or the `PORT` environment
variable, read at launch). README.md is uploaded as part of the list below.

## 2. Upload the files

Upload on the **Contents** page, or use "Upload via Git". Only uploaded files
are deployed. Upload exactly:

| Upload | Notes |
| --- | --- |
| `app.py` | entry point, run as `python app.py` |
| `requirements.txt` | `gradio==6.31.0`, `fpdf2==2.8.9` |
| `core/` | the whole folder |
| `ui/` | the whole folder, including `ui/assets/fonts/AtkinsonHyperlegibleNext-wght.ttf` and `ui/assets/fonts/OFL.txt` |
| `README.md` | |

Never upload (they contain secrets, local state, test-only code or output):
`.env`, `.venv/`, `__pycache__/`, `tests/`, `scripts/`, `*.pdf`.

## 3. Add the secrets

In the Studio deployment settings (Variables / Secrets), add exactly two
variables. Type the key into Studio only — never into a file, a commit or
this document.

| Variable | Value |
| --- | --- |
| `MODELSCOPE_API_KEY` | the team's ModelScope API key (typed only into Studio) |
| `MODELSCOPE_MODEL` | `Qwen/Qwen3.8-27B` |

**Never set VISITPREP_PREVIEW on Studio.** `VISITPREP_PREVIEW` is a local
development mode; the deployed app must call the live model.

## 4. Deploy

1. Save the secrets, then deploy (publish) the Studio.
2. Publishing takes about 10 minutes. Open **"View log"** and watch the build
   logs until the deployment finishes.

Public URL once it is live:
`https://modelscope.ai/studios/<username>/<space-name>`.

## 5. After-deploy checks

Run these on the public URL:

1. The page opens in an incognito window and on a phone.
2. The teal header bar (brand "VisitPrep") and the Atkinson Hyperlegible Next
   font are visible. If the page looks like plain Gradio, Studio did not run
   `python app.py` → see the troubleshooting table below.
3. There is no "Built with Gradio" footer. The VisitPrep footer text
   ("Before you type: …") is still shown.
4. The full flow works up to Download PDF: example story → Continue → answer
   the questions → I'm done, check my details → Write my summary → Download
   PDF.
5. `<public URL>/gradio_api/runs` shows **Not found** (run history is off, so
   patient text is not stored in the browser).

## 6. Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Build fails while installing dependencies | The free-CPU build could not install `requirements.txt` | Re-upload an unchanged `requirements.txt` (`gradio==6.31.0`, `fpdf2==2.8.9`), redeploy, re-read "View log" |
| "The AI service is not configured on this server." banner | `MODELSCOPE_API_KEY` missing or misspelt in the Studio secrets | The variable name must be exactly `MODELSCOPE_API_KEY` and the value must be the team's key; then redeploy |
| "The free AI quota for today may be used up. Please try again later." | ModelScope free quota or rate limit reached | Wait and try again later |
| Port error in the logs (port already in use / wrong port) | The Studio expects a different port than 7860 | Add a `PORT` variable in the Studio secrets with the port the Studio expects; the app reads `PORT` when it launches |
| Blank page after deploy | The app process crashed at startup | Read "View log" for the traceback; most often a missing uploaded file (e.g. the font in `ui/assets/fonts/`) or a secret name typo |
| Plain Gradio look, no teal header, no Atkinson font | Studio did not run `python app.py` (wrong start command or entry point) | Set the start command / entry point to `python app.py` in the Studio settings and redeploy |

## 7. Pre-upload token scan

Run both commands from the repo root before uploading anything.

```sh
git grep -n -E "ms-[0-9a-f]{8}"
```

Expected: empty (no output).

```sh
git grep -n "MODELSCOPE_API_KEY="
```

Expected: only the empty line in `.env.example`
(`.env.example:2:MODELSCOPE_API_KEY=`).

If either command shows anything else, stop and fix it before uploading: no
API key or token may ever be in the source code.
