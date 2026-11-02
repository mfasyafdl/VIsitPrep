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
