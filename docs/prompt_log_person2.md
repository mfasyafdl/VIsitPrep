# Prompt log — Person 2

## P2-1

- Model: Qwen/Qwen3.8-27B
- Date: 2026-11-02

### Prompt (verbatim)

```
ROLE: You are the coding agent for Person 2 of VisitPrep, a new Python 3.10 + Gradio app, English only, that helps a patient prepare for a doctor visit. It organizes what the patient reports. It never diagnoses, never recommends treatment or medication changes.

TEAM: Two people build this in parallel. Person 2 (you) owns app.py, ui/, tests/test_ui/, docs/deployment.md and docs/prompt_log_person2.md. Person 1 owns AGENTS.md, requirements*.txt, .gitignore, .env.example, docs/data_contract.md, core/, tests/test_core/, README.md and scripts/. Never edit Person 1's files, even to fix a bug; write a handoff with an exact reproduction instead. If you need a new dependency, ask for it in the handoff.

BEFORE YOU WRITE CODE:
1. Read AGENTS.md and docs/data_contract.md in full. Then read only the files listed under "Files to read" in the task.
2. Write a short plan: the files you will change and one line per file on what changes. Then continue; do not wait for approval unless a rule below says stop.

HARD RULES (breaking any of these means the task failed):
- Only edit files listed under "Files you may change".
- ui/ has no business logic. Alerts come only from core.redflag. Questions come only from core.interview. Summaries come only from core.summarize. Never reimplement any of them, and never write red-flag trigger words in ui/.
- Event handlers live in ui/handlers.py as plain functions that take the session state dict plus inputs and return a new state dict; they never import gradio. ui/layout.py only builds components and wires events to those functions.
- null means unknown. Never turn null into False, 0, "" or "none".
- Escape every piece of patient text before it goes into gr.HTML or the PDF.
- No catch-all `except Exception` that hides a failure. Show a visible English message instead.
- Never print, log or hard-code MODELSCOPE_API_KEY. Tests never use the network.
- Do not commit, push, merge or change git config. Do not touch any app I am running on port 7860; if you launch the app, use port 7861.
- All user-facing text is English.

WORK STYLE:
- Do the steps in order. If one is impossible, say why in the report and continue with the next.
- Make the smallest change that meets the acceptance criteria. No unrelated refactors.
- After each file change, run `python -m pytest -q tests/test_ui` and fix failures before moving on. If the same command fails twice for a reason you cannot fix, stop and report the full error.
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
## Handoff for Person 1
Exact reproductions or requests (file, function, input, expected, actual), or "None".
## prompt_log
Confirm you appended this whole prompt verbatim (Block A2, any extra block, and the task card, exactly as pasted) to docs/prompt_log_person2.md under the section id in the task title, with the model name "Qwen/Qwen3.8-27B", and that earlier sections are unchanged. DESIGN RULES (exact values from the approved UI preview; do not invent other colours or sizes):

Colour tokens: define each once as a CSS custom property on #vp-root (light values), and override them under `.dark #vp-root` (Gradio's dark class) AND inside `@media (prefers-color-scheme: dark)`. No hard-coded hex anywhere else. Every rule that sets a background also sets color.
  token                    light      dark
  --vp-ground              #EEF4F2    #0E1A1C
  --vp-surface             #FFFFFF    #16252A
  --vp-ink                 #15232A    #E3EEEC
  --vp-ink-2               #44565E    #AFC2C1
  --vp-primary             #0B6B60    #4FC1B1
  --vp-on-primary          #FFFFFF    #052421
  --vp-pressed-edge        #06443D    #2E8C80
  --vp-tint                #DCEEEA    #1D3A3A
  --vp-on-tint             #0B4F47    #BDEDE5
  --vp-input-border        #6B7F84    #6F8A8D   (2px)
  --vp-hairline            #D3E0DD    #27393D
  --vp-urgent-band         #C42B1C    #C42B1C   (band text #FFFFFF in both)
  --vp-urgent-card-border  #C42B1C    #FF8A7A
  --vp-attn-band           #FFD84D    #FFD84D   (band text #15232A in both)
  Focus on every button, input, chip and link: outline 4px solid #FFD84D plus an inner 2px edge in --vp-ink (box-shadow inset).
  Header bar: --vp-primary background with --vp-on-primary text in light mode; --vp-surface with --vp-ink text in dark mode.

Type: "Atkinson Hyperlegible Next" from Google Fonts (weights 400, 600, 700, 800), fallback system-ui, sans-serif. Body 17px, helper text 15px, h1 26px below 1024px and 34px from 1024px. Inputs at least 17px.

Buttons: 52px tall, radius 8px. Primary: filled --vp-primary, text --vp-on-primary, 4px bottom edge in --vp-pressed-edge (box-shadow 0 4px 0) that disappears while pressed (translateY 2px). Secondary: --vp-surface background, 2px --vp-primary border, --vp-primary text. Link-style: no background, underlined --vp-primary text, at least 44px tall. Exactly one primary button per step.

Alerts are care cards: a coloured band whose heading names the action, then a body on --vp-surface.
  Urgent: band --vp-urgent-band, heading "Get medical help now", preceded by a visually hidden "Urgent advice:" (class vp-sr-only). Card border 2px --vp-urgent-card-border. Body = core's alert message verbatim, escaped. Exactly one link-button "Call 119" with href="tel:119".
  Attention: band --vp-attn-band, heading "Tell your doctor about this", hidden "Attention:", body verbatim, no call button.
  Container: role="alert" when any urgent alert is present, otherwise aria-live="polite". With no alerts it shows nothing and never says "no alerts" or "you are safe".

Errors use --vp-surface with a 2px --vp-ink-2 border, never urgent red.

Page order on every step: header bar (brand "VisitPrep" left, "Start over" link-style right) → alert area → "Step N of 4, <step name>" with a 4-segment progress bar → step content → action buttons → footer.
Footer text: "Before you type: your notes are sent to ModelScope to be organized. Leave out your name, address and phone number. The provider doesn't promise to delete them, and closing this tab doesn't delete them right away." then "VisitPrep doesn't diagnose, give medical advice or suggest treatment."
Desktop from 1024px: a 250px progress rail on the left (current step: --vp-tint background, 3px --vp-primary left border, aria-current="step") and the content on the right. Below 1024px: one column, rail hidden. TASK P2-1 — Theme tokens and the static layout shell. Log section: P2-1.

Files to read: AGENTS.md, app.py, requirements.txt (read only, to see the installed gradio version).
Files you may change: app.py, ui/theme.py (new), ui/components.py (new), ui/layout.py (new), tests/test_ui/test_components.py (new), docs/prompt_log_person2.md.

Steps:
1. Check the installed gradio version (`pip show gradio`) and find in that version where custom CSS and extra <head> HTML are passed (gr.Blocks(css=..., head=...) or launch(css=..., head=...)). Use that. Say which in the report.
2. ui/theme.py: CSS string with the tokens from DESIGN RULES (light, `.dark #vp-root`, and prefers-color-scheme dark), the button classes vp-btn-primary / vp-btn-secondary / vp-btn-link, the focus style, the vp-sr-only class, the care-card classes, the progress bar, and the 1024px desktop rail. HEAD string with the Google Fonts link for Atkinson Hyperlegible Next.
3. ui/components.py: pure functions returning escaped HTML strings: header_html(), progress_html(step: int), alerts_html(alerts: list[Alert]), alerts_error_html(), footer_html(), preview_banner_html(). alerts_html follows the care-card rules exactly.
4. ui/layout.py: build_interface() builds, inside gr.Column(elem_id="vp-root"), the header, the alert area (gr.HTML), the progress (gr.HTML), four gr.Column step containers (only step 1 visible) each with a placeholder heading ("What's bothering you today?", "Question 1 of 5", "Is this right?", "Your visit note is ready"), and the footer. No event logic yet.
5. app.py: demo = gr.Blocks(title="VisitPrep", …) with build_interface(), created at module level; launch under __main__ with server_name "0.0.0.0" and PORT (default 7860).

Acceptance criteria:
AC1. Tests: urgent alerts_html contains href="tel:119", "Urgent advice:" inside a vp-sr-only element and "Get medical help now"; attention contains "Tell your doctor about this" and no "tel:"; an alert message "<script>x</script>" appears escaped; alerts_html([]) contains no visible text; progress_html(2) marks segment 2 as current.
AC2. `grep -n "#[0-9A-Fa-f]\{3,6\}" ui/*.py` shows hex values only inside the token blocks of ui/theme.py.
AC3. App on port 7861, light and ?__theme=dark: report the computed rgb of body text on the page background and of footer text, with the contrast ratio (≥ 4.5:1).
AC4. At 375px width there is no horizontal scroll (scrollWidth equals 375). Say how you checked (Playwright if `python -c "import playwright"` works, else Chrome DevTools by hand).
AC5. `python -m pytest -q` passes.
```

## P2-1-FIX-1

- Model: Qwen/Qwen3.8-27B
- Date: 2026-11-02

### Prompt (verbatim)

```
ROLE: You are the coding agent for Person 2 of VisitPrep, a new Python 3.10 + Gradio app, English only, that helps a patient prepare for a doctor visit. It organizes what the patient reports. It never diagnoses, never recommends treatment or medication changes.

TEAM: Two people build this in parallel. Person 2 (you) owns app.py, ui/, tests/test_ui/, docs/deployment.md and docs/prompt_log_person2.md. Person 1 owns AGENTS.md, requirements*.txt, .gitignore, .env.example, docs/data_contract.md, core/, tests/test_core/, README.md and scripts/. Never edit Person 1's files, even to fix a bug; write a handoff with an exact reproduction instead. If you need a new dependency, ask for it in the handoff.

BEFORE YOU WRITE CODE:
1. Read AGENTS.md and docs/data_contract.md in full. Then read only the files listed under "Files to read" in the task.
2. Write a short plan: the files you will change and one line per file on what changes. Then continue; do not wait for approval unless a rule below says stop.

HARD RULES (breaking any of these means the task failed):
- Only edit files listed under "Files you may change".
- ui/ has no business logic. Alerts come only from core.redflag. Questions come only from core.interview. Summaries come only from core.summarize. Never reimplement any of them, and never write red-flag trigger words in ui/.
- Event handlers live in ui/handlers.py as plain functions that take the session state dict plus inputs and return a new state dict; they never import gradio. ui/layout.py only builds components and wires events to those functions.
- null means unknown. Never turn null into False, 0, "" or "none".
- Escape every piece of patient text before it goes into gr.HTML or the PDF.
- No catch-all `except Exception` that hides a failure. Show a visible English message instead.
- Never print, log or hard-code MODELSCOPE_API_KEY. Tests never use the network.
- Do not commit, push, merge or change git config. Do not touch any app I am running on port 7860; if you launch the app, use port 7861.
- All user-facing text is English.

WORK STYLE:
- Do the steps in order. If one is impossible, say why in the report and continue with the next.
- Make the smallest change that meets the acceptance criteria. No unrelated refactors.
- After each file change, run `python -m pytest -q tests/test_ui` and fix failures before moving on. If the same command fails twice for a reason you cannot fix, stop and report the full error.
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
## Handoff for Person 1
Exact reproductions or requests (file, function, input, expected, actual), or "None".
## prompt_log
Confirm you appended this whole prompt verbatim (Block A2, any extra block, and the task card, exactly as pasted) to docs/prompt_log_person2.md under the section id in the task title, with the model name "Qwen/Qwen3.8-27B", and that earlier sections are unchanged. DESIGN RULES (exact values from the approved UI preview; do not invent other colours or sizes):

Colour tokens: define each once as a CSS custom property on #vp-root (light values), and override them under `.dark #vp-root` (Gradio's dark class) AND inside `@media (prefers-color-scheme: dark)`. No hard-coded hex anywhere else. Every rule that sets a background also sets color.
  token                    light      dark
  --vp-ground              #EEF4F2    #0E1A1C
  --vp-surface             #FFFFFF    #16252A
  --vp-ink                 #15232A    #E3EEEC
  --vp-ink-2               #44565E    #AFC2C1
  --vp-primary             #0B6B60    #4FC1B1
  --vp-on-primary          #FFFFFF    #052421
  --vp-pressed-edge        #06443D    #2E8C80
  --vp-tint                #DCEEEA    #1D3A3A
  --vp-on-tint             #0B4F47    #BDEDE5
  --vp-input-border        #6B7F84    #6F8A8D   (2px)
  --vp-hairline            #D3E0DD    #27393D
  --vp-urgent-band         #C42B1C    #C42B1C   (band text #FFFFFF in both)
  --vp-urgent-card-border  #C42B1C    #FF8A7A
  --vp-attn-band           #FFD84D    #FFD84D   (band text #15232A in both)
  Focus on every button, input, chip and link: outline 4px solid #FFD84D plus an inner 2px edge in --vp-ink (box-shadow inset).
  Header bar: --vp-primary background with --vp-on-primary text in light mode; --vp-surface with --vp-ink text in dark mode.

Type: "Atkinson Hyperlegible Next" from Google Fonts (weights 400, 600, 700, 800), fallback system-ui, sans-serif. Body 17px, helper text 15px, h1 26px below 1024px and 34px from 1024px. Inputs at least 17px.

Buttons: 52px tall, radius 8px. Primary: filled --vp-primary, text --vp-on-primary, 4px bottom edge in --vp-pressed-edge (box-shadow 0 4px 0) that disappears while pressed (translateY 2px). Secondary: --vp-surface background, 2px --vp-primary border, --vp-primary text. Link-style: no background, underlined --vp-primary text, at least 44px tall. Exactly one primary button per step.

Alerts are care cards: a coloured band whose heading names the action, then a body on --vp-surface.
  Urgent: band --vp-urgent-band, heading "Get medical help now", preceded by a visually hidden "Urgent advice:" (class vp-sr-only). Card border 2px --vp-urgent-card-border. Body = core's alert message verbatim, escaped. Exactly one link-button "Call 119" with href="tel:119".
  Attention: band --vp-attn-band, heading "Tell your doctor about this", hidden "Attention:", body verbatim, no call button.
  Container: role="alert" when any urgent alert is present, otherwise aria-live="polite". With no alerts it shows nothing and never says "no alerts" or "you are safe".

Errors use --vp-surface with a 2px --vp-ink-2 border, never urgent red.

Page order on every step: header bar (brand "VisitPrep" left, "Start over" link-style right) → alert area → "Step N of 4, <step name>" with a 4-segment progress bar → step content → action buttons → footer.
Footer text: "Before you type: your notes are sent to ModelScope to be organized. Leave out your name, address and phone number. The provider doesn't promise to delete them, and closing this tab doesn't delete them right away." then "VisitPrep doesn't diagnose, give medical advice or suggest treatment."
Desktop from 1024px: a 250px progress rail on the left (current step: --vp-tint background, 3px --vp-primary left border, aria-current="step") and the content on the right. Below 1024px: one column, rail hidden. TASK P2-1-1 — Make the shell match the approved design. Log section: P2-1-FIX-1.

Files to read: AGENTS.md, docs/data_contract.md, ui/theme.py, ui/components.py, ui/layout.py, app.py.
Files you may change: ui/theme.py, ui/components.py, ui/layout.py, tests/test_ui/test_components.py, docs/prompt_log_person2.md.

Audit result: all five P2-1 acceptance criteria were re-tested and pass. Six visual and accessibility defects remain. Two of them come from mistakes in the earlier design rules; where this prompt and DESIGN RULES differ, this prompt wins.

Steps:
1. Full-bleed page. Gradio adds padding and a max width around the app, so at 375px the text column is only 255px and a white (light) or near-black (dark) frame shows around #vp-root. Remove that padding and max width for this app, and give the page body the --vp-ground colour in both modes (define the tokens so body can use them too, for example on :root/body with the dark values under .dark). Inside #vp-root, use 16px side padding below 1024px and 24px from 1024px.
2. Remove the @media (prefers-color-scheme: dark) token block. In gradio 6.31.0 the "system" theme already adds the dark class when the OS is dark (verified), and the media block makes ?__theme=light on a dark OS show dark tokens next to light Gradio components. Dark tokens must come only from the .dark class.
3. Empty alert area takes no space: with no alerts, the distance from the bottom of the header bar to the "Step N of 4" line is at most 24px.
4. Step names. Keep the step headings as they are, but add separate labels. The "Step N of 4, <label>" line uses: "describe your symptoms", "a few questions", "check your details", "your summary". The desktop rail uses: "Describe", "Questions", "Check details", "Your summary". Put "Step N of 4" in bold.
5. Care cards. The band heading becomes an h2 that contains the hidden prefix: <h2 class="vp-card-heading"><span class="vp-sr-only">Urgent advice:</span> Get medical help now</h2> (same pattern with "Attention:" and "Tell your doctor about this"). "Call 119" becomes a real button-style link inside the card body padding: href="tel:119", --vp-urgent-band background, white text, 52px tall, radius 8px, full width below 1024px, with the focus style. No other change to card text.
6. Live region. The alert area always renders a container, also when empty: <div class="vp-alerts" aria-live="polite"></div> with no visible text. With an urgent alert the container gets role="alert". The empty container must not add height (step 3 still holds).
7. preview_banner_html() text: "Preview mode: example answers only. Nothing is sent to ModelScope."
8. Tests: update tests/test_ui/test_components.py for steps 4 to 7 (labels in progress_html and rail_html, h2 with sr-only prefix, tel:119 link has the button class, alerts_html([]) has the aria-live container and no visible text, banner text). Keep every existing assertion that still applies.
9. Append this prompt verbatim to docs/prompt_log_person2.md as section "## P2-1-FIX-1" with the line "Model: Qwen/Qwen3.8-27B", and put the prompt inside a ``` code block. Also wrap the existing P2-1 prompt text in a ``` code block without changing any of its words, so its "## Plan vs done" lines stop being real headings.

Acceptance criteria:
AC1. `python -m pytest -q` passes; report the count.
AC2. Playwright on port 7861 at 375x900 and 1280x900, light and ?__theme=dark: report the computed background colour of document.body and the width of #vp-root (must equal the viewport width), and the pixel distance from the header bottom to the step line (≤ 24px).
AC3. Playwright with colorScheme "dark" and ?__theme=light: #vp-root background is rgb(238, 244, 242) and body text is rgb(21, 35, 42).
AC4. `grep -n "#[0-9A-Fa-f]\{3,6\}" ui/*.py` still shows hex values only in the token blocks of ui/theme.py.
AC5. Save screenshots of all five Playwright cases to a folder outside the repo and give the paths; do not describe what they look like.
```

## P2-2

- Model: Qwen/Qwen3.8-27B
- Date: 2026-11-03

### Prompt (verbatim)

```
ROLE: You are the coding agent for Person 2 of VisitPrep, a new Python 3.10 + Gradio app, English only, that helps a patient prepare for a doctor visit. It organizes what the patient reports. It never diagnoses, never recommends treatment or medication changes.

TEAM: Two people build this in parallel. Person 2 (you) owns app.py, ui/, tests/test_ui/, docs/deployment.md and docs/prompt_log_person2.md. Person 1 owns AGENTS.md, requirements*.txt, .gitignore, .env.example, docs/data_contract.md, core/, tests/test_core/, README.md and scripts/. Never edit Person 1's files, even to fix a bug; write a handoff with an exact reproduction instead. If you need a new dependency, ask for it in the handoff.

BEFORE YOU WRITE CODE:
1. Read AGENTS.md and docs/data_contract.md in full. Then read only the files listed under "Files to read" in the task.
2. Write a short plan: the files you will change and one line per file on what changes. Then continue; do not wait for approval unless a rule below says stop.

HARD RULES (breaking any of these means the task failed):
- Only edit files listed under "Files you may change".
- ui/ has no business logic. Alerts come only from core.redflag. Questions come only from core.interview. Summaries come only from core.summarize. Never reimplement any of them, and never write red-flag trigger words in ui/.
- Event handlers live in ui/handlers.py as plain functions that take the session state dict plus inputs and return a new state dict; they never import gradio. ui/layout.py only builds components and wires events to those functions.
- null means unknown. Never turn null into False, 0, "" or "none".
- Escape every piece of patient text before it goes into gr.HTML or the PDF.
- No catch-all `except Exception` that hides a failure. Show a visible English message instead.
- Never print, log or hard-code MODELSCOPE_API_KEY. Tests never use the network.
- Do not commit, push, merge or change git config. Do not touch any app I am running on port 7860; if you launch the app, use port 7861.
- All user-facing text is English.

WORK STYLE:
- Do the steps in order. If one is impossible, say why in the report and continue with the next.
- Make the smallest change that meets the acceptance criteria. No unrelated refactors.
- After each file change, run `python -m pytest -q tests/test_ui` and fix failures before moving on. If the same command fails twice for a reason you cannot fix, stop and report the full error.
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
## Handoff for Person 1
Exact reproductions or requests (file, function, input, expected, actual), or "None".
## prompt_log
Confirm you appended this whole prompt verbatim (Block A2, any extra block, and the task card, exactly as pasted) to docs/prompt_log_person2.md under the section id in the task title, with the model name "Qwen/Qwen3.8-27B", and that earlier sections are unchanged.

DESIGN RULES v2 (exact values from the approved UI preview; do not invent other colours or sizes):

Colour tokens: define each once as a CSS custom property on #vp-root (light values), and override them under `.dark #vp-root` (Gradio's dark class). Dark tokens come ONLY from the .dark class; never add a @media (prefers-color-scheme) block (Gradio already sets .dark in system mode, and the media block breaks ?__theme=light). --vp-ground and --vp-ink are also defined on :root and .dark so the page body uses the ground colour. No hard-coded hex anywhere else. Every rule that sets a background also sets color.
  token                    light      dark
  --vp-ground              #EEF4F2    #0E1A1C
  --vp-surface             #FFFFFF    #16252A
  --vp-ink                 #15232A    #E3EEEC
  --vp-ink-2               #44565E    #AFC2C1
  --vp-primary             #0B6B60    #4FC1B1
  --vp-on-primary          #FFFFFF    #052421
  --vp-pressed-edge        #06443D    #2E8C80
  --vp-tint                #DCEEEA    #1D3A3A
  --vp-on-tint             #0B4F47    #BDEDE5
  --vp-input-border        #6B7F84    #6F8A8D   (2px)
  --vp-hairline            #D3E0DD    #27393D
  --vp-urgent-band         #C42B1C    #C42B1C   (band text #FFFFFF in both)
  --vp-urgent-card-border  #C42B1C    #FF8A7A
  --vp-attn-band           #FFD84D    #FFD84D   (band text #15232A in both)
  Focus on every button, input, chip and link: outline 4px solid #FFD84D plus an inner 2px edge in --vp-ink (box-shadow inset).
  Header bar: --vp-primary background with --vp-on-primary text in light mode; --vp-surface with --vp-ink text in dark mode.

Type: "Atkinson Hyperlegible Next" from Google Fonts (weights 400, 600, 700, 800), fallback system-ui, sans-serif. Body 17px, helper text 15px, h1 26px below 1024px and 34px from 1024px. Inputs at least 17px.

Buttons: 52px tall, radius 8px. Primary: filled --vp-primary, text --vp-on-primary, 4px bottom edge in --vp-pressed-edge (box-shadow 0 4px 0) that disappears while pressed (translateY 2px). Secondary: --vp-surface background, 2px --vp-primary border, --vp-primary text. Link-style: no background, underlined --vp-primary text, at least 44px tall. Exactly one primary button per step.

Alerts are care cards: a coloured band whose heading names the action, then a body on --vp-surface.
  Urgent: band --vp-urgent-band, an h2 heading "Get medical help now" that starts with a visually hidden "Urgent advice:" (class vp-sr-only). Card border 2px --vp-urgent-card-border. Body = core's alert message verbatim, escaped. Exactly one "Call 119" link with href="tel:119" styled as a button (class vp-btn-call: --vp-urgent-band background, white text, 52px, radius 8px, full width below 1024px) inside the card body.
  Attention: band --vp-attn-band, heading "Tell your doctor about this", hidden "Attention:", body verbatim, no call button.
  Container: always rendered; role="alert" when any urgent alert is present, otherwise aria-live="polite". With no alerts it is an empty container with no height and never says "no alerts" or "you are safe".

Errors use --vp-surface with a 2px --vp-ink-2 border, never urgent red.

Page order on every step: header bar (brand "VisitPrep" left, "Start over" link-style right) → alert area → "**Step N of 4**, <label>" with a 4-segment progress bar (labels: describe your symptoms / a few questions / check your details / your summary) → step content → action buttons → footer.
Full-bleed page: no Gradio padding around #vp-root; 16px side padding below 1024px, 24px from 1024px.
Footer text: "Before you type: your notes are sent to ModelScope to be organized. Leave out your name, address and phone number. The provider doesn't promise to delete them, and closing this tab doesn't delete them right away." then "VisitPrep doesn't diagnose, give medical advice or suggest treatment."
Desktop from 1024px: a 250px progress rail on the left (current step: --vp-tint background, 3px --vp-primary left border, aria-current="step") and the content on the right. Below 1024px: one column, rail hidden. Rail labels: Describe / Questions / Check details / Your summary.
ui/theme.py and ui/components.py already implement all of the above (merged in P2-1 and P2-1-FIX-1). Reuse their classes and functions; do not rewrite or duplicate the theme.

TASK P2-2 — Session state, backend switch, and steps 1–2. Log section: P2-2.

Files to read: AGENTS.md, docs/data_contract.md, core/schema.py, core/fixtures.py, core/llm.py, core/interview.py, core/redflag.py (all read only), ui/theme.py, ui/components.py, ui/layout.py, app.py.
Files you may change: ui/state.py (new), ui/backend.py (new), ui/handlers.py (new), ui/layout.py, ui/components.py, ui/theme.py (only to add classes for the new parts), tests/test_ui/test_handlers_steps12.py (new), tests/test_ui/test_components.py, docs/prompt_log_person2.md.

Facts about the current code (checked on main):
- core.fixtures provides FIXTURE_NAMES, FIXTURE_STORIES, get_fixture(name), get_summary(name) and match_story(story). get_fixture/get_summary return copies. Never use the FIXTURE_* record constants directly.
- core.redflag.scan_text/check_alerts and core.interview.next_question/merge_answers, core.extract.extract_record and core.summarize.generate_summary may still raise NotImplementedError; Person 1 is implementing them. Tests must fake them; never edit core/.
- core.llm.LLMError is the base of every model error (including LLMContentFilterError and ConfigError); its str() is a safe English message for the user.
- Gradio 6.31.0: gr.update(...) exists; chain events with .click(...).then(...).

Steps:
1. ui/state.py: new_state() -> dict with step=1, story="", details={}, alert_texts=[], alerts=[], alerts_error=False, record=None, asked=[], skipped=[], question=None, summary=None, pdf_path=None, error=None, busy=False, token=0. bump(state) returns a copy with token + 1. The state holds only plain JSON-like data: record as record_to_dict(...), alerts as dicts {"code","message","level"}, asked as dicts {"question","answer"}, summary as a dict. Convert to dataclasses only when calling core or components.
2. ui/backend.py: PREVIEW = os.environ.get("VISITPREP_PREVIEW") == "1", decided once at import. DEFAULT_PREVIEW_FIXTURE = "chest_pain".
   extract(story, details) -> PatientRecord. Preview: name = match_story(story) or DEFAULT_PREVIEW_FIXTURE; record = get_fixture(name); then apply details exactly like the contract says for extract_record (patient_age, patient_age_text, patient_sex from details override when not None) and return recompute_missing_information(record). Real: core.extract.extract_record(story, details).
   merge(record, asked) -> PatientRecord. Preview: return a copy of record unchanged. Real: core.interview.merge_answers(record, asked).
   summarize(record, asked, story) -> SummaryOutput. Preview: get_summary(match_story(story) or DEFAULT_PREVIEW_FIXTURE). Real: core.summarize.generate_summary(record, asked).
   Alerts and next_question are NOT in backend: handlers always call core.redflag and core.interview.next_question directly, in both modes. No try/except in backend.py.
3. ui/handlers.py, plain functions (no gradio import), each returns a NEW state dict and never mutates its input:
   - recompute_alerts(state): alerts = scan_text(*alert_texts) + (check_alerts(record) if record), dedup by code keeping the first, urgent first then by code. This is the only place where a broad `except Exception` is allowed, because the failure is shown: keep the previous alerts and set alerts_error True. On success set alerts_error False.
   - on_continue(state, story, age_text, sex): strip story; empty → error "Please describe your symptoms first." Else: details from the form (age_text "" or not a whole number 0–130 → patient_age None; patient_age_text = stripped age_text or None; sex None when not chosen), store story, alert_texts=[story], run recompute_alerts BEFORE extract, then backend.extract. On LLMError: keep story, details and alerts, error = str(err) + " Your text is kept. Press Continue to try again.", stay on step 1. On success: store record, question = next_question(record, asked, skipped), step 2 (or step 3 when question is None), error None.
   - on_answer(state, answer): empty after strip → error "Type an answer, or press Skip this question." Else append {"question","answer"} to asked and the answer to alert_texts, recompute_alerts, then the next question; None → step 3.
   - on_skip(state): append the current question to skipped, then the next question; None → step 3.
   - on_finish(state): go to step 3 (merge happens in task P2-3, not here).
   - append_chip(text, chip) -> str: "" → chip; text ending with "." → text + "\n" + chip; otherwise text + " " + chip. Never replaces text.
   - Every handler returns the state unchanged when called from the wrong step, and clears error on success.
4. ui/components.py: add pips_html(answered: int, skipped_positions: list[int], current: int) for the five pips (answered filled --vp-primary, skipped dashed border, current --vp-tint with a --vp-primary border, upcoming empty with --vp-input-border), answers_list_html(asked) (escaped), question_heading_html(n) "Question N of 5". Alerts from state dicts become Alert objects before alerts_html. When alerts_error is True, show alerts_error_html("We could not check your answers for warning signs. If you feel very unwell, call 119.") in the alert area.
5. ui/layout.py, wiring only:
   Step 1: h1 "What's bothering you today?", line "Write it the way you'd tell a friend. We'll turn it into a clear note for your doctor.", textarea "Your symptoms" (at least 5 lines), chips "It started…", "It feels…", "I take…" as small secondary buttons that call append_chip, textbox "Age, if you want to share it", gr.Radio "Sex" with choices Female/Male/Other/Prefer not to say mapped to female/male/other/not-specified, no default value, styled as four buttons; primary "Continue".
   Step 2: question heading, pips, the question text at 23px bold, textarea "Your answer", primary "Save answer", secondary "Skip this question", link-style "I'm done, check my details", the note "Skipping still uses one of the five questions.", and a closed gr.Accordion "Your answers so far (N)".
   Step 3 and 4 stay placeholders (task P2-3).
   The preview banner shows on every step only when backend.PREVIEW is True.
   Progress line, rail and alert area update on every handler.
   While a handler that calls the backend runs, every button of that step is disabled and the primary button reads "Working… this can take up to a minute"; chain: an update that disables → the handler → an update that re-enables (also after an error).
   Exactly one primary button per step.

Acceptance criteria:
AC1. Handler tests with a faked backend and faked core functions (monkeypatch): recompute_alerts runs before extract (assert call order); extract raising LLMNetworkError keeps story and alerts, sets the error ending with "Press Continue to try again." and stays on step 1; 3 answers + 2 skips → step 3 and next_question not called a sixth time; empty answer sets the error; wrong-step calls return the state unchanged; sex None when not chosen; age "" → patient_age None and patient_age_text None; age "34" → 34 and "34"; handlers never mutate the input state (compare a deepcopy).
AC2. Test: recompute_alerts keeps previous alerts and sets alerts_error True when check_alerts raises; scan_text and check_alerts both returning the same code gives one alert.
AC3. Test: append_chip appends and never replaces (the three cases).
AC4. Backend tests with PREVIEW forced True: each FIXTURE_STORIES text (also with extra spaces) gives that fixture's complaint; an unknown story gives the chest_pain fixture; details age 40 overrides the fixture age; mutating the returned record does not change the next extract result; summarize returns the matching get_summary.
AC5. `grep -rn -i "breath\|chest\|faint\|seizure" ui/ --exclude=backend.py` is empty, and in ui/backend.py the word "chest" appears only in the line DEFAULT_PREVIEW_FIXTURE = "chest_pain".
AC6. Manual with VISITPREP_PREVIEW=1 on port 7861 at 375px and 1280px: paste the child_cough story, press Continue. Report: the alert area content, whether step 2 appears, the first question, and each step's single primary button label. If core.interview.next_question or core.redflag still raise NotImplementedError, report exactly what the screen shows and mark the affected part NOT RUN; do not work around it.
AC7. `python -m pytest -q` passes; report the count.
AC8. `git status --short` shows only files from "Files you may change".
```

## P2-2-FIX-1

- Model: Qwen/Qwen3.8-27B
- Date: 2026-11-03

### Prompt (verbatim)

```
FIX P2-2-1 — four defects found in an independent re-test. Log section: P2-2-FIX-1. Do not commit.

Files to read: AGENTS.md, docs/data_contract.md, core/fixtures.py, core/redflag.py, ui/backend.py, ui/handlers.py, ui/layout.py, tests/test_ui/test_handlers_steps12.py.
Files you may change: ui/backend.py, ui/handlers.py, ui/layout.py, tests/test_ui/test_handlers_steps12.py, docs/prompt_log_person2.md.

Audit result: 116 tests pass, the log is verbatim and the step 1–2 flow works at 375px and 1280px. Four defects remain; two come from the task card itself, so where this prompt and task P2-2 differ, this prompt wins.

Steps:
1. Answers accordion. In ui/layout.py the accordion is created as `accordion = gr.Accordion(...)` without `with`, so it is empty and the answers list always shows below it. Build it as `with gr.Accordion("Your answers so far (0)", open=False) as accordion:` and create the answers gr.HTML inside it. Keep updating its label with the count.
2. Clear the answer box. After "Save answer" succeeds (state error is None) and after "Skip this question", the "Your answer" textbox becomes empty. When on_answer sets an error (empty answer), the textbox keeps what was typed. Do this in ui/layout.py wiring only (for example an extra output of the render step that returns "" or gr.update()); handlers stay free of gradio.
3. Record alerts right after extract. In on_continue keep the recompute_alerts call BEFORE backend.extract, and after extract succeeds and the record is stored, call recompute_alerts again so check_alerts(record) is reflected when step 2 appears. When extract fails, only the first call happens.
4. Preview default fixture. In ui/backend.py set DEFAULT_PREVIEW_FIXTURE = "child_cough". A story that is not one of the example stories must never produce an alert the person did not report.
5. Tests in tests/test_ui/test_handlers_steps12.py:
   - on_continue with a faked check_alerts that returns an alert only when given a record: after on_continue the state contains that alert, and the call order is scan_text, extract, check_alerts;
   - extract raising LLMNetworkError: check_alerts is never called with a record;
   - preview: an unknown story gives the child_cough fixture (replace the chest_pain test); each example story still gives its own fixture;
   - keep every other existing test.
6. Append this prompt verbatim to docs/prompt_log_person2.md as section "## P2-2-FIX-1" with the line "Model: Qwen/Qwen3.8-27B", inside a ``` code block. Do not change earlier sections.

Acceptance criteria:
AC1. `python -m pytest -q` passes; report the count and the tests/test_ui count.
AC2. `grep -rn -i "breath\|chest\|faint\|seizure" ui/` is empty (ui/backend.py included).
AC3. Manual with VISITPREP_PREVIEW=1 on port 7861 at 375px: paste the child_cough example story, Continue, answer "No medicines." and press Save answer. Report: the answer box content after saving (must be empty), whether the saved answer is visible before opening the accordion (must not be), and what shows after opening it.
AC4. Same setup, story "I have a headache.", Continue, answer the first question. Report the alert area text (must not mention chest pain).
AC5. `git status --short` shows only files from "Files you may change".
```

## P2-3a

- Model: Qwen/Qwen3.8-27B
- Date: 2026-11-03

### Prompt (verbatim)

```
ROLE: You are the coding agent for Person 2 of VisitPrep, a new Python 3.10 + Gradio app, English only, that helps a patient prepare for a doctor visit. It organizes what the patient reports. It never diagnoses, never recommends treatment or medication changes.

TEAM: Two people build this in parallel. Person 2 (you) owns app.py, ui/, tests/test_ui/, docs/deployment.md and docs/prompt_log_person2.md. Person 1 owns AGENTS.md, requirements*.txt, .gitignore, .env.example, docs/data_contract.md, core/, tests/test_core/, README.md and scripts/. Never edit Person 1's files, even to fix a bug; write a handoff with an exact reproduction instead. If you need a new dependency, ask for it in the handoff.

BEFORE YOU WRITE CODE:
1. Read AGENTS.md and docs/data_contract.md in full. Then read only the files listed under "Files to read" in the task.
2. Write a short plan: the files you will change and one line per file on what changes. Then continue; do not wait for approval unless a rule below says stop.

HARD RULES (breaking any of these means the task failed):
- Only edit files listed under "Files you may change".
- ui/ has no business logic. Alerts come only from core.redflag. Questions come only from core.interview. Summaries come only from core.summarize. Never reimplement any of them, and never write red-flag trigger words in ui/.
- Event handlers live in ui/handlers.py as plain functions that take the session state dict plus inputs and return a new state dict; they never import gradio. ui/layout.py only builds components and wires events to those functions.
- null means unknown. Never turn null into False, 0, "" or "none".
- Escape every piece of patient text before it goes into gr.HTML or the PDF.
- No catch-all `except Exception` that hides a failure. Show a visible English message instead.
- Never print, log or hard-code MODELSCOPE_API_KEY. Tests never use the network.
- Do not commit, push, merge or change git config. Do not touch any app I am running on port 7860; if you launch the app, use port 7861.
- All user-facing text is English.

WORK STYLE:
- Do the steps in order. If one is impossible, say why in the report and continue with the next.
- Make the smallest change that meets the acceptance criteria. No unrelated refactors.
- After each file change, run `python -m pytest -q tests/test_ui` and fix failures before moving on. If the same command fails twice for a reason you cannot fix, stop and report the full error.
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
## Handoff for Person 1
Exact reproductions or requests (file, function, input, expected, actual), or "None".
## prompt_log
Confirm you appended this whole prompt verbatim (Block A2, any extra block, and the task card, exactly as pasted) to docs/prompt_log_person2.md under the section id in the task title, with the model name "Qwen/Qwen3.8-27B", and that earlier sections are unchanged.

DESIGN RULES v2 (exact values from the approved UI preview; do not invent other colours or sizes):

Colour tokens: define each once as a CSS custom property on #vp-root (light values), and override them under `.dark #vp-root` (Gradio's dark class). Dark tokens come ONLY from the .dark class; never add a @media (prefers-color-scheme) block (Gradio already sets .dark in system mode, and the media block breaks ?__theme=light). --vp-ground and --vp-ink are also defined on :root and .dark so the page body uses the ground colour. No hard-coded hex anywhere else. Every rule that sets a background also sets color.
  token                    light      dark
  --vp-ground              #EEF4F2    #0E1A1C
  --vp-surface             #FFFFFF    #16252A
  --vp-ink                 #15232A    #E3EEEC
  --vp-ink-2               #44565E    #AFC2C1
  --vp-primary             #0B6B60    #4FC1B1
  --vp-on-primary          #FFFFFF    #052421
  --vp-pressed-edge        #06443D    #2E8C80
  --vp-tint                #DCEEEA    #1D3A3A
  --vp-on-tint             #0B4F47    #BDEDE5
  --vp-input-border        #6B7F84    #6F8A8D   (2px)
  --vp-hairline            #D3E0DD    #27393D
  --vp-urgent-band         #C42B1C    #C42B1C   (band text #FFFFFF in both)
  --vp-urgent-card-border  #C42B1C    #FF8A7A
  --vp-attn-band           #FFD84D    #FFD84D   (band text #15232A in both)
  Focus on every button, input, chip and link: outline 4px solid #FFD84D plus an inner 2px edge in --vp-ink (box-shadow inset).
  Header bar: --vp-primary background with --vp-on-primary text in light mode; --vp-surface with --vp-ink text in dark mode.

Type: "Atkinson Hyperlegible Next" from Google Fonts (weights 400, 600, 700, 800), fallback system-ui, sans-serif. Body 17px, helper text 15px, h1 26px below 1024px and 34px from 1024px. Inputs at least 17px.

Buttons: 52px tall, radius 8px. Primary: filled --vp-primary, text --vp-on-primary, 4px bottom edge in --vp-pressed-edge (box-shadow 0 4px 0) that disappears while pressed (translateY 2px). Secondary: --vp-surface background, 2px --vp-primary border, --vp-primary text. Link-style: no background, underlined --vp-primary text, at least 44px tall. Exactly one primary button per step.

Alerts are care cards: a coloured band whose heading names the action, then a body on --vp-surface.
  Urgent: band --vp-urgent-band, an h2 heading "Get medical help now" that starts with a visually hidden "Urgent advice:" (class vp-sr-only). Card border 2px --vp-urgent-card-border. Body = core's alert message verbatim, escaped. Exactly one "Call 119" link with href="tel:119" styled as a button (class vp-btn-call: --vp-urgent-band background, white text, 52px, radius 8px, full width below 1024px) inside the card body.
  Attention: band --vp-attn-band, heading "Tell your doctor about this", hidden "Attention:", body verbatim, no call button.
  Container: always rendered; role="alert" when any urgent alert is present, otherwise aria-live="polite". With no alerts it is an empty container with no height and never says "no alerts" or "you are safe".

Errors use --vp-surface with a 2px --vp-ink-2 border, never urgent red.

Page order on every step: header bar (brand "VisitPrep" left, "Start over" link-style right) → alert area → "**Step N of 4**, <label>" with a 4-segment progress bar (labels: describe your symptoms / a few questions / check your details / your summary) → step content → action buttons → footer.
Full-bleed page: no Gradio padding around #vp-root; 16px side padding below 1024px, 24px from 1024px.
Footer text: "Before you type: your notes are sent to ModelScope to be organized. Leave out your name, address and phone number. The provider doesn't promise to delete them, and closing this tab doesn't delete them right away." then "VisitPrep doesn't diagnose, give medical advice or suggest treatment."
Desktop from 1024px: a 250px progress rail on the left (current step: --vp-tint background, 3px --vp-primary left border, aria-current="step") and the content on the right. Below 1024px: one column, rail hidden. Rail labels: Describe / Questions / Check details / Your summary.
ui/theme.py and ui/components.py already implement all of the above (merged in P2-1 and P2-1-FIX-1). Reuse their classes and functions; do not rewrite or duplicate the theme.

TASK P2-3a — Step 3 "Is this right?": merge on entry, the details list and the section editors. Log section: P2-3a.

Files to read: AGENTS.md, docs/data_contract.md, core/schema.py, core/interview.py (all read only), ui/state.py, ui/backend.py, ui/handlers.py, ui/components.py, ui/layout.py, ui/theme.py, tests/test_ui/test_handlers_steps12.py.
Files you may change: ui/state.py, ui/handlers.py, ui/components.py, ui/layout.py, ui/theme.py (only to add classes for the new parts), tests/test_ui/test_handlers_steps34.py (new), tests/test_ui/test_components.py, docs/prompt_log_person2.md.

Facts about the current code (checked on main 0ecdb0e, 259 tests pass):
- ui/handlers.py has recompute_alerts, _parse_age, on_continue, on_answer, on_skip, on_finish, append_chip and the _NOT_READY message. Reuse them; do not change their behaviour or their tests.
- ui/backend.py has merge(record, asked) and summarize(record, asked, story). In preview mode merge returns a copy unchanged. In real mode core.interview.merge_answers still raises NotImplementedError (Person 1 task P1-5b); core.summarize.generate_summary too (P1-6).
- Step 4, the summary call, the PDF and "Start over" are task P2-3b. Do not build them here.

Steps:
1. ui/state.py: add two keys to new_state(): merged=False (the merge for this session has run, successfully or not) and editing=None (the key of the open editor, or None). Nothing else changes.
2. ui/handlers.py, plain functions (no gradio), each returns a NEW state dict, never mutates its input, returns the state unchanged when called from the wrong step, and keeps every list it changes as a new list:
   a. enter_review(state): only when step == 3 and merged is False, otherwise unchanged. Calls backend.merge(record, [QuestionAnswer(**qa) for qa in asked]) exactly once. Success: store record_to_dict(merged record). LLMError: keep the record, error = str(err) + " Your answers are kept. You can still check and change your details below." NotImplementedError: keep the record, error = _NOT_READY. In every case set merged True, then run recompute_alerts.
   b. SECTIONS = ("problem", "timing", "medicines", "allergies", "history", "concerns", "about").
   c. open_editor(state, section): step 3 and merged True only; unknown section → unchanged. Sets editing = section (so only one editor is open) and clears error. cancel_editor(state): editing None, error None.
   d. editor_values(record: dict, section) -> dict: the values that prefill the open editor:
      problem → {"complaint": text or "", "symptoms": one item per line}
      timing → {"onset": text or "", "duration": text or "", "severity": "mild"/"moderate"/"severe" or "not-sure" when None}
      medicines → {"lines": one medicine per line as "name, frequency" (just "name" when frequency is None), "none": medicines_denied is True}
      allergies / history → {"lines": one item per line, "none": the matching *_denied is True}
      concerns → {"lines": one item per line}
      about → {"age_text": patient_age_text or (str(patient_age) if not None) or "", "sex": patient_sex or None}
   e. save_section(state, section, values: dict): step 3, merged True and editing == section only. Builds a new record dict from the current one:
      - text fields: stripped; "" → None. List fields: split on newlines, strip, drop empty lines, keep order.
      - problem: complaint, symptoms. timing: onset, duration, severity ("not-sure" or None → None; severity_note is not changed).
      - medicines: each line "name, frequency" split on the FIRST comma; the part after it is frequency (None when empty); a line without a comma is a name with frequency None. A name equal to an existing medicine's name (casefold, stripped) keeps that medicine's medicine_type, dose, duration and notes, and its frequency unless a new one is given. New names get medicine_type "unknown" and None for dose, duration and notes.
      - allergies / history: the list, and the flag: "none" ticked → True; not ticked → None (never False). Ticked together with at least one item → error "Remove the items, or untick the box." and the record is not changed. The same rule for medicines with "I take no medicines".
      - concerns: the list.
      - about: patient_age and patient_age_text from _parse_age(age_text); patient_sex = sex when it is in SEX_VALUES, else None. reporting_on_behalf and reporter_relationship are never changed.
      - Rebuild with record_from_dict and recompute_missing_information; when validate_record reports a problem, error = "This could not be saved. Please check what you typed." and nothing changes.
      - On success: store the record, append every non-empty new text value of this section (each text field and each list line, medicines by name) to alert_texts (alerts only ever get stricter after an edit), run recompute_alerts, set editing None, error None, summary None and pdf_path None, and bump the token.
3. ui/components.py:
   - DETAIL_ROWS: the seven sections in order with their row labels: problem "Main problem" (complaint, then symptoms), timing "When and how bad" (Started / How long / How bad), medicines "Medicines", allergies "Allergies", history "Medical history", concerns "Your questions and worries", about "About the patient" (age, sex, and "Reported by: <reporter_relationship>" only when reporting_on_behalf is True and a relationship is known).
   - detail_row_html(record: dict, section) -> str: the section label, then the values escaped. An unknown value shows "Not given" (class vp-not-given: italic, --vp-ink-2). A list with its *_denied flag True shows "None (you confirmed)". A list with a None flag and no items shows "Not given". Medicines show "name, frequency" per line. Severity shows the level, plus the severity_note in quotes when present.
   - Keep the escaping rule: every patient value goes through html.escape.
4. ui/layout.py (wiring only):
   - Step 3: h1 "Is this right?", the line "Your own words are kept. Press Change on anything that's wrong." While merged is False, show only the line "Checking your answers… this can take up to a minute" (class vp-helper) instead of the rows.
   - For each of the seven sections: a gr.HTML with detail_row_html and a link-style gr.Button "Change" ("Add" when the whole section is unknown), then a gr.Group editor (class vp-editor: --vp-tint background, 2px --vp-primary border, radius 8px, 16px padding) that is visible only when editing == that section, with a "Save" (secondary inside the editor) and a "Cancel" (link-style) button. Editor fields:
     problem: textbox "Main problem", textarea "Symptoms (one per line)".
     timing: textbox "When did it start?", textbox "How long has it been going on?", gr.Radio "How bad is it?" with Mild/Moderate/Severe/Not sure mapped to mild/moderate/severe/not-sure.
     medicines: textarea "Medicines (one per line, for example: Amlodipine, every morning)", checkbox "I take no medicines".
     allergies: textarea "Allergies (one per line)", checkbox "No allergies".
     history: textarea "Health conditions (one per line)", checkbox "No known health conditions".
     concerns: textarea "Your questions and worries (one per line)".
     about: textbox "Age", the same Sex radio as step 1 (no default).
     Opening an editor fills its fields from editor_values.
   - Below the sections: the primary "Write my summary" button, shown but not interactive in this task (task P2-3b wires it). Exactly one primary button on step 3.
   - Chain: every event that can move to step 3 (Save answer, Skip this question, I'm done) runs its handler, renders, then runs enter_review and renders again. While enter_review runs, the step 3 Change buttons are not interactive.
   - The alert area, progress line and rail update after every handler, as in P2-2.
5. tests/test_ui/test_handlers_steps34.py (fake backend and core with monkeypatch; neutral fictional data):
   - enter_review calls merge exactly once with QuestionAnswer objects; a second call does nothing; it does nothing on step 2;
   - merge raising LLMNetworkError keeps the record, sets the error ending "You can still check and change your details below.", sets merged True;
   - merge raising NotImplementedError sets the _NOT_READY error and merged True;
   - after enter_review, check_alerts receives the merged record;
   - open_editor("medicines") then open_editor("allergies") leaves editing == "allergies"; cancel_editor sets None;
   - medicines: "Amlodipine, every morning" on an empty list → Medicine(name="Amlodipine", medicine_type="unknown", dose=None, frequency="every morning", duration=None, notes=None); an existing "Ginger tea" with dose "one cup" keeps its dose and type when the line "ginger tea, twice a day" is saved; empty lines are ignored; "Paracetamol" without a comma → frequency None;
   - for medicines, allergies and history: ticked with an empty list → flag True; not ticked with an empty list → flag None (not False); ticked with an item → the exact error and an unchanged record;
   - timing: severity "not-sure" → None and severity_note unchanged;
   - about: age "" → patient_age None and patient_age_text None; sex None → None; reporting_on_behalf unchanged;
   - a successful save sets summary None, pdf_path None, editing None, recomputes missing_information, adds the new text to alert_texts and calls recompute_alerts;
   - save_section for a section that is not open → state unchanged;
   - no handler mutates its input (compare a deepcopy).
6. tests/test_ui/test_components.py: detail_row_html escapes "<img src=x onerror=alert(1)>" in every text field; shows "Not given" for unknown values; shows "None (you confirmed)" for a denied list; the about row shows "Reported by: mother" only when reporting_on_behalf is True.
7. Append this prompt verbatim to docs/prompt_log_person2.md as section "## P2-3a" with the line "Model: Qwen/Qwen3.8-27B", inside a ``` code block. Do not change earlier sections.

Acceptance criteria:
AC1. `python -m pytest -q` passes; report the count and the tests/test_ui count.
AC2. `grep -rn -i "breath\|chest\|faint\|seizure" ui/` is empty.
AC3. Manual with VISITPREP_PREVIEW=1 on port 7861 at 375px: paste the fever_adult example story, Continue, answer the first question "No", press "I'm done, check my details". Report: the text of each of the seven rows, whether the "Checking your answers…" line disappeared, and the number of primary buttons on step 3.
AC4. Same session: Change on Medicines, add the line "Paracetamol, when needed" under the existing line, Save. Report the Medicines row text. Then open Allergies and report whether the Medicines editor closed.
AC5. At 375px and 1280px on step 3 with one editor open: report document.documentElement.scrollWidth (must equal the viewport width).
AC6. `git status --short` shows only files from "Files you may change".
```

## P2-3a-FIX-1

- Model: Qwen/Qwen3.8-27B
- Date: 2026-11-03

### Prompt (verbatim)

```
FIX P2-3a-1 — keep what the patient typed when a section save fails. Log section: P2-3a-FIX-1. Do not commit.

Files to read: ui/layout.py, ui/handlers.py, tests/test_ui/test_handlers_steps34.py.
Files you may change: ui/layout.py, tests/test_ui/test_components.py or a new tests/test_ui/test_layout_step3.py, docs/prompt_log_person2.md.

Audit result: everything else in P2-3a passed an independent re-test (358 tests together with the latest main, real merge through core with a fake model, merge failure, alerts after an edit, dark mode). One defect: _step3_values in ui/layout.py writes editor_values(record, section) into every editor field on every render. After a failed save (for example "peanuts" typed with "No allergies" ticked → "Remove the items, or untick the box."), the render resets the open editor to the stored record, so the typed text and the tick disappear, and a second Save stores "Not given".

Steps:
1. In _step3_values, for the section whose editor is open (state["editing"] == section) while state["error"] is not None, return gr.update() (no change) for every field of that editor instead of the record values. In every other case keep the current behaviour (opening an editor still prefills it from the record).
2. Move that decision into a small pure helper in ui/layout.py, for example _editor_field_values(state, section) -> list, so it can be tested without a browser, and add tests: open editor with no error → record values; open editor with an error → every value is a no-change update; a closed editor → record values.
3. Append this prompt verbatim to docs/prompt_log_person2.md as section "## P2-3a-FIX-1" with the line "Model: Qwen/Qwen3.8-27B", inside a ``` code block. Do not change earlier sections.

Acceptance criteria:
AC1. `python -m pytest -q` passes; report the count.
AC2. Manual with VISITPREP_PREVIEW=1 on port 7861 at 375px: child_cough story → Continue → "I'm done, check my details" → Change on Allergies → type "peanuts", tick "No allergies", Save. Report the textbox content and the tick state after the error (must still be "peanuts" and ticked). Untick, Save, report the Allergies row (must show peanuts).
AC3. `git status --short` shows only files from "Files you may change".
```

## P2-3b

- Model: Qwen/Qwen3.8-27B
- Date: 2026-11-03

### Prompt (verbatim)

```
ROLE: You are the coding agent for Person 2 of VisitPrep, a new Python 3.10 + Gradio app, English only, that helps a patient prepare for a doctor visit. It organizes what the patient reports. It never diagnoses, never recommends treatment or medication changes.

TEAM: Two people build this in parallel. Person 2 (you) owns app.py, ui/, tests/test_ui/, docs/deployment.md and docs/prompt_log_person2.md. Person 1 owns AGENTS.md, requirements*.txt, .gitignore, .env.example, docs/data_contract.md, core/, tests/test_core/, README.md and scripts/. Never edit Person 1's files, even to fix a bug; write a handoff with an exact reproduction instead. If you need a new dependency, ask for it in the handoff.

BEFORE YOU WRITE CODE:
1. Read AGENTS.md and docs/data_contract.md in full. Then read only the files listed under "Files to read" in the task.
2. Write a short plan: the files you will change and one line per file on what changes. Then continue; do not wait for approval unless a rule below says stop.

HARD RULES (breaking any of these means the task failed):
- Only edit files listed under "Files you may change".
- ui/ has no business logic. Alerts come only from core.redflag. Questions come only from core.interview. Summaries come only from core.summarize. Never reimplement any of them, and never write red-flag trigger words in ui/.
- Event handlers live in ui/handlers.py as plain functions that take the session state dict plus inputs and return a new state dict; they never import gradio. ui/layout.py only builds components and wires events to those functions.
- null means unknown. Never turn null into False, 0, "" or "none".
- Escape every piece of patient text before it goes into gr.HTML or the PDF.
- No catch-all `except Exception` that hides a failure. Show a visible English message instead.
- Never print, log or hard-code MODELSCOPE_API_KEY. Tests never use the network.
- Do not commit, push, merge or change git config. Do not touch any app I am running on port 7860; if you launch the app, use port 7861.
- All user-facing text is English.

WORK STYLE:
- Do the steps in order. If one is impossible, say why in the report and continue with the next.
- Make the smallest change that meets the acceptance criteria. No unrelated refactors.
- After each file change, run `python -m pytest -q tests/test_ui` and fix failures before moving on. If the same command fails twice for a reason you cannot fix, stop and report the full error.
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
## Handoff for Person 1
Exact reproductions or requests (file, function, input, expected, actual), or "None".
## prompt_log
Confirm you appended this whole prompt verbatim (Block A2, any extra block, and the task card, exactly as pasted) to docs/prompt_log_person2.md under the section id in the task title, with the model name "Qwen/Qwen3.8-27B", and that earlier sections are unchanged.

DESIGN RULES v2 (exact values from the approved UI preview; do not invent other colours or sizes):

Colour tokens: define each once as a CSS custom property on #vp-root (light values), and override them under `.dark #vp-root` (Gradio's dark class). Dark tokens come ONLY from the .dark class; never add a @media (prefers-color-scheme) block (Gradio already sets .dark in system mode, and the media block breaks ?__theme=light). --vp-ground and --vp-ink are also defined on :root and .dark so the page body uses the ground colour. No hard-coded hex anywhere else. Every rule that sets a background also sets color.
  token                    light      dark
  --vp-ground              #EEF4F2    #0E1A1C
  --vp-surface             #FFFFFF    #16252A
  --vp-ink                 #15232A    #E3EEEC
  --vp-ink-2               #44565E    #AFC2C1
  --vp-primary             #0B6B60    #4FC1B1
  --vp-on-primary          #FFFFFF    #052421
  --vp-pressed-edge        #06443D    #2E8C80
  --vp-tint                #DCEEEA    #1D3A3A
  --vp-on-tint             #0B4F47    #BDEDE5
  --vp-input-border        #6B7F84    #6F8A8D   (2px)
  --vp-hairline            #D3E0DD    #27393D
  --vp-urgent-band         #C42B1C    #C42B1C   (band text #FFFFFF in both)
  --vp-urgent-card-border  #C42B1C    #FF8A7A
  --vp-attn-band           #FFD84D    #FFD84D   (band text #15232A in both)
  Focus on every button, input, chip and link: outline 4px solid #FFD84D plus an inner 2px edge in --vp-ink (box-shadow inset).
  Header bar: --vp-primary background with --vp-on-primary text in light mode; --vp-surface with --vp-ink text in dark mode.

Type: "Atkinson Hyperlegible Next" from Google Fonts (weights 400, 600, 700, 800), fallback system-ui, sans-serif. Body 17px, helper text 15px, h1 26px below 1024px and 34px from 1024px. Inputs at least 17px.

Buttons: 52px tall, radius 8px. Primary: filled --vp-primary, text --vp-on-primary, 4px bottom edge in --vp-pressed-edge (box-shadow 0 4px 0) that disappears while pressed (translateY 2px). Secondary: --vp-surface background, 2px --vp-primary border, --vp-primary text. Link-style: no background, underlined --vp-primary text, at least 44px tall. Exactly one primary button per step.

Alerts are care cards: a coloured band whose heading names the action, then a body on --vp-surface.
  Urgent: band --vp-urgent-band, an h2 heading "Get medical help now" that starts with a visually hidden "Urgent advice:" (class vp-sr-only). Card border 2px --vp-urgent-card-border. Body = core's alert message verbatim, escaped. Exactly one "Call 119" link with href="tel:119" styled as a button (class vp-btn-call: --vp-urgent-band background, white text, 52px, radius 8px, full width below 1024px) inside the card body.
  Attention: band --vp-attn-band, heading "Tell your doctor about this", hidden "Attention:", body verbatim, no call button.
  Container: always rendered; role="alert" when any urgent alert is present, otherwise aria-live="polite". With no alerts it is an empty container with no height and never says "no alerts" or "you are safe".

Errors use --vp-surface with a 2px --vp-ink-2 border, never urgent red.

Page order on every step: header bar (brand "VisitPrep" left, "Start over" link-style right) → alert area → "**Step N of 4**, <label>" with a 4-segment progress bar (labels: describe your symptoms / a few questions / check your details / your summary) → step content → action buttons → footer.
Full-bleed page: no Gradio padding around #vp-root; 16px side padding below 1024px, 24px from 1024px.
Footer text: "Before you type: your notes are sent to ModelScope to be organized. Leave out your name, address and phone number. The provider doesn't promise to delete them, and closing this tab doesn't delete them right away." then "VisitPrep doesn't diagnose, give medical advice or suggest treatment."
Desktop from 1024px: a 250px progress rail on the left (current step: --vp-tint background, 3px --vp-primary left border, aria-current="step") and the content on the right. Below 1024px: one column, rail hidden. Rail labels: Describe / Questions / Check details / Your summary.
ui/theme.py and ui/components.py already implement all of the above (merged in P2-1 and P2-1-FIX-1). Reuse their classes and functions; do not rewrite or duplicate the theme.

TASK P2-3b — "Write my summary", step 4 visit note, "Change my details" and a working "Start over". Log section: P2-3b.

Files to read: AGENTS.md, docs/data_contract.md, core/schema.py (SummaryOutput, read only), ui/state.py, ui/backend.py, ui/handlers.py, ui/components.py, ui/layout.py, ui/theme.py, tests/test_ui/test_handlers_steps34.py, tests/test_ui/test_components.py.
Files you may change: ui/handlers.py, ui/components.py, ui/layout.py, ui/theme.py (only to add classes for the new parts), tests/test_ui/test_handlers_step4.py (new), tests/test_ui/test_components.py, docs/prompt_log_person2.md.

Facts about the current code (checked on main 752bb2b, 427 tests pass):
- core.summarize.generate_summary works in real mode now (P1-6); ui/backend.py already has summarize(record, asked, story) -> SummaryOutput (preview: the fixture's summary). Do not change ui/backend.py or ui/state.py.
- SummaryOutput has doctor_card (str, one "Label: value" per line), patient_script (str) and priority_questions (list[str]).
- The state already has summary=None and pdf_path=None. save_section already clears both.
- The header's "Start over" is an <a href="#"> inside header_html and does nothing.
- STEP_NAMES[3] is "Your visit note is ready". The step 4 column exists with only its heading.
- The PDF is task P2-4. Do not build it, and do not add a download button.

Steps:
1. ui/handlers.py, plain functions (no gradio), same rules as before: return a NEW state dict, never mutate the input, return the state unchanged when called from the wrong step.
   a. on_summarize(state): only when step == 3 and merged is True, otherwise unchanged. When editing is not None: error "Save or cancel your change first." and do not call the backend. Otherwise call backend.summarize(record_from_dict(record), [QuestionAnswer(**qa) for qa in asked], story) exactly once.
      Success: summary = {"doctor_card", "patient_script", "priority_questions"} (plain dict, a new list for the questions), step 4, error None.
      LLMError: stay on step 3, summary None, error = str(err) + " Your details are kept. Press Write my summary to try again."
      NotImplementedError: stay on step 3, error = _NOT_READY.
      Always bump the token.
   b. on_change_details(state): only when step == 4. Step 3, summary None, pdf_path None, editing None, error None; merged stays True, so the merge does not run again.
   c. on_reset(state): returns new_state(), from any step.
2. ui/components.py (every patient value through html.escape, as before):
   a. header_html(): the brand only (<span class="vp-brand">VisitPrep</span>), no link. The Start over control becomes a real button in ui/layout.py.
   b. note_date(d: datetime.date) -> str: "3 November 2026" (day without a leading zero, full month name, year).
   c. visit_note_html(summary: dict, prepared_on: datetime.date) -> str: a slip (class vp-note: --vp-surface background, --vp-ink text, 6px --vp-primary top border, radius 8px, 16px padding) with the title "Visit note" and note_date(prepared_on) on one line; a stamp "For the doctor" (class vp-stamp: 2px --vp-primary border, --vp-primary text, uppercase 13px, rotated -4deg, inline-block); a dashed 2px --vp-hairline line (class vp-perforation); then one row per doctor_card line, split on the FIRST ": " into a bold label and the value (a line without ": " is shown whole); then the line "Written by the patient with VisitPrep. Not a diagnosis." (class vp-helper).
   d. read_time_seconds(script: str) -> int: round(len(script.split()) / 150 * 60).
   e. script_html(summary: dict) -> str: an h2 "What to say", the script in <p id="vp-script-text">, then "About N seconds when read aloud" (class vp-helper) only when N > 0.
   f. questions_html(summary: dict) -> str: an h2 "Questions to ask" and an <ol> with one <li> per question; "" when the list is empty.
3. ui/layout.py (wiring only):
   a. Header: replace the header gr.HTML with gr.Row(elem_id="vp-header", elem_classes="vp-header") holding gr.HTML(header_html()) and gr.Button("Start over", elem_classes="vp-btn vp-btn-link", elem_id="vp-start-over"), both scale=0 so the row stays on one line at 375px with the brand left and the button right. Keep the existing header colours in light and dark mode.
   b. Step 3: the "Write my summary" button (primary, elem_id vp-step3-summary) becomes interactive when step == 3 and merged is True. Pressing it: first an instant step that sets it to interactive=False with the label "Writing your note… this can take up to a minute" and makes every step 3 Change button not interactive; then on_summarize; then render, which restores the label "Write my summary" and the buttons.
   c. Step 4 (inside the existing step 4 column, below the h1): the line "Show this to your doctor." (vp-helper); then gr.Row(elem_id="vp-step4-grid") with a left gr.Column holding gr.HTML visit note (elem_id vp-visit-note), and a right gr.Column holding gr.HTML script (elem_id vp-script), a secondary gr.Button "Copy what to say" (elem_id vp-copy-script) and gr.HTML questions (elem_id vp-questions). Below 1024px the two columns stack (note first) at full width; from 1024px they sit side by side. Then the secondary button "Change my details" (elem_id vp-change-details). No primary button on step 4 until task P2-4 adds "Download PDF"; this is the only exception to "exactly one primary button per step".
   d. Render: when summary is not None the three gr.HTML get visit_note_html(summary, datetime.date.today()), script_html(summary) and questions_html(summary); otherwise "".
   e. Copy: "Copy what to say".click(fn=None, js=...) with this exact JavaScript (no Python call):
      () => { const el = document.querySelector('#vp-script-text'); const b = document.querySelector('#vp-copy-script'); if (!el || !b) return; navigator.clipboard.writeText(el.innerText).then(() => { b.textContent = 'Copied'; setTimeout(() => { b.textContent = 'Copy what to say'; }, 2000); }, () => { b.textContent = 'Select the text to copy'; }); }
   f. "Change my details": on_change_details, then render.
   g. Start over: on_reset, then render, and in the same handler also clear the story box, the age box, the sex radio (None) and the answer box, and set the three chips and Continue to interactive with the label "Continue". Pass cancels= with the event objects of every step that calls the model: the .then(handlers.on_continue, ...) step, the three .then(handlers.enter_review, ...) steps (after Save answer, Skip this question and I'm done) and the .then(handlers.on_summarize, ...) step. Keep each of those steps in a variable and chain the next .then from it. Tested with Gradio 6.31.0: cancelling a step drops its output, and the later .then steps of that chain still run with the fresh state, which is harmless because enter_review and on_summarize do nothing on step 1.
4. tests/test_ui/test_handlers_step4.py (fake backend with monkeypatch; neutral fictional data):
   - on_summarize calls backend.summarize exactly once with a PatientRecord, a list of QuestionAnswer and the story; it stores the summary dict and goes to step 4;
   - with an open editor: the exact error, the backend is not called, step stays 3;
   - merged False, or step 2 or 4: state unchanged;
   - LLMNetworkError: step 3, summary None, error ends "Press Write my summary to try again.", record unchanged;
   - NotImplementedError: _NOT_READY on step 3;
   - on_change_details: step 3, summary None, pdf_path None, merged True; on step 3 it does nothing;
   - on_reset from steps 1, 2, 3 and 4 equals new_state();
   - no handler mutates its input (compare a deepcopy).
5. tests/test_ui/test_components.py (keep every test; in test_header_and_footer_text replace the "Start over" assertion with: 'href="#"' not in header_html()):
   - note_date: date(2026, 11, 3) → "3 November 2026"; date(2027, 1, 12) → "12 January 2027";
   - visit_note_html, script_html and questions_html escape "<img src=x onerror=alert(1)>" in the doctor card, the script and a question;
   - visit_note_html contains "Visit note", "For the doctor", the date, the bold label "Patient" for the line "Patient: 7 years old", and "Written by the patient with VisitPrep. Not a diagnosis.";
   - read_time_seconds: 150 words → 60, 35 words → 14, "" → 0; script_html has no "seconds when read aloud" for an empty script;
   - questions_html with two questions has one <ol> and two <li>; with no questions it returns "".
6. Append this prompt verbatim to docs/prompt_log_person2.md as section "## P2-3b" with the line "Model: Qwen/Qwen3.8-27B", inside a ``` code block. Do not change earlier sections.

Acceptance criteria:
AC1. `python -m pytest -q` passes; report the count and the tests/test_ui count.
AC2. `grep -rn -i "breath\|chest\|faint\|seizure" ui/` is empty.
AC3. Manual with VISITPREP_PREVIEW=1 on port 7861 at 375px: paste the child_cough example story, Continue, press "I'm done, check my details", then "Write my summary". Report: the "Step N of 4" line, the visit note title line with its date, the first two doctor card lines, the read-time line, the number of questions, the number of primary buttons on step 4 (must be 0), and document.documentElement.scrollWidth (must be 375).
AC4. Same story at 1280px: report the x position of #vp-visit-note and #vp-script (the note must be left of the script) and scrollWidth (must be 1280). Repeat at 1280px with ?__theme=dark and report whether the note, the stamp and the header are readable.
AC5. With clipboard permission (or by hand in Chrome): press "Copy what to say". Report the button text right after (must be "Copied") and whether the clipboard equals the script.
AC6. "Change my details" → report the step line and whether the seven rows show; then "Write my summary" again → step 4.
AC7. "Start over" on step 4 → report the step line and the story box content (must be "Step 1 of 4" and empty). Then paste the chest_pain example story and press Continue (an urgent alert shows), press "Start over" again and report whether the alert area is empty. At 375px report whether the header (brand and Start over) is on one line.
AC8. `git status --short` shows only files from "Files you may change".
```
