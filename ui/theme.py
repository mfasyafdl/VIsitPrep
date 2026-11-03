"""Theme tokens and static CSS for the VisitPrep UI.

Every colour is defined once as a CSS custom property on #vp-root with
light values, and overridden for dark mode under .dark #vp-root (Gradio
adds the dark class to the page when the theme is dark). Dark tokens
come only from the .dark class. The ground and ink tokens are also
defined on :root (light) and .dark (dark) so the page body can use
them. No hex values may appear outside the token blocks.

THEME_CSS is passed to launch(css=...) and THEME_HEAD to launch(head=...)
in gradio 6.31.0 (css/head moved from the Blocks constructor to launch
in gradio 6.0).
"""

THEME_HEAD = (
    '<link rel="preconnect" href="https://fonts.googleapis.com">'
    '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
    '<link href="https://fonts.googleapis.com/css2?family=Atkinson+Hyperlegible'
    '+Next:wght@400;600;700;800&display=swap" rel="stylesheet">'
)

_LIGHT_TOKENS = """\
  --vp-ground: #EEF4F2;
  --vp-surface: #FFFFFF;
  --vp-ink: #15232A;
  --vp-ink-2: #44565E;
  --vp-primary: #0B6B60;
  --vp-on-primary: #FFFFFF;
  --vp-pressed-edge: #06443D;
  --vp-tint: #DCEEEA;
  --vp-on-tint: #0B4F47;
  --vp-input-border: #6B7F84;
  --vp-hairline: #D3E0DD;
  --vp-urgent-band: #C42B1C;
  --vp-urgent-card-border: #C42B1C;
  --vp-attn-band: #FFD84D;
  --vp-urgent-band-text: #FFFFFF;
  --vp-attn-band-text: #15232A;
  --vp-focus: #FFD84D;
"""

_DARK_TOKENS = """\
  --vp-ground: #0E1A1C;
  --vp-surface: #16252A;
  --vp-ink: #E3EEEC;
  --vp-ink-2: #AFC2C1;
  --vp-primary: #4FC1B1;
  --vp-on-primary: #052421;
  --vp-pressed-edge: #2E8C80;
  --vp-tint: #1D3A3A;
  --vp-on-tint: #BDEDE5;
  --vp-input-border: #6F8A8D;
  --vp-hairline: #27393D;
  --vp-urgent-band: #C42B1C;
  --vp-urgent-card-border: #FF8A7A;
  --vp-attn-band: #FFD84D;
  --vp-urgent-band-text: #FFFFFF;
  --vp-attn-band-text: #15232A;
  --vp-focus: #FFD84D;
"""

THEME_CSS = f"""
/* VisitPrep theme tokens (light values). */
#vp-root {{
{_LIGHT_TOKENS}
  background: var(--vp-ground);
  color: var(--vp-ink);
  font-family: "Atkinson Hyperlegible Next", system-ui, sans-serif;
  font-size: 17px;
  line-height: 1.5;
  width: 100%;
  min-height: 100vh;
  gap: 0 !important;
}}

/* Dark tokens when Gradio marks the page as dark. Dark tokens come
   only from the .dark class. */
.dark #vp-root {{
{_DARK_TOKENS}
}}

/* Ground and ink on :root and .dark so the page body can use them
   outside #vp-root. */
:root {{
  --vp-ground: #EEF4F2;
  --vp-ink: #15232A;
}}

.dark {{
  --vp-ground: #0E1A1C;
  --vp-ink: #E3EEEC;
}}

/* Full-bleed page: remove gradio's page padding so #vp-root spans the
   viewport, and give the page body the ground colour in both modes. */
.gradio-container .main {{
  padding: 0 !important;
}}

body {{
  background: var(--vp-ground);
  color: var(--vp-ink);
}}

/* Zero the default padding inside every gr.HTML wrapper in the shell. */
#vp-root .html-container {{
  padding: 0 !important;
}}

#vp-root h1 {{
  margin: 0 0 16px;
  font-size: 26px;
  font-weight: 700;
  color: var(--vp-ink);
}}

@media (min-width: 1024px) {{
  #vp-root h1 {{
    font-size: 34px;
  }}
}}

/* Header bar. */
#vp-root .vp-header {{
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  background: var(--vp-primary);
  color: var(--vp-on-primary);
  padding: 8px 16px;
}}

.dark #vp-root .vp-header {{
  background: var(--vp-surface);
  color: var(--vp-ink);
}}

#vp-root .vp-brand {{
  font-size: 24px;
  font-weight: 800;
  color: inherit;
}}

/* The Start over link sits on the header background, so it takes the
   on-primary colour instead of the usual primary text colour. */
#vp-root .vp-header .vp-btn-link {{
  color: var(--vp-on-primary);
}}

.dark #vp-root .vp-header .vp-btn-link {{
  color: var(--vp-primary);
}}

/* Buttons. */
#vp-root .vp-btn {{
  display: inline-flex;
  align-items: center;
  justify-content: center;
  height: 52px;
  padding: 0 24px;
  border: 0;
  border-radius: 8px;
  font-family: inherit;
  font-size: 17px;
  font-weight: 700;
  line-height: 1;
  cursor: pointer;
  text-decoration: none;
}}

#vp-root .vp-btn-primary {{
  background: var(--vp-primary);
  color: var(--vp-on-primary);
  box-shadow: 0 4px 0 var(--vp-pressed-edge);
}}

#vp-root .vp-btn-primary:active {{
  transform: translateY(2px);
  box-shadow: none;
}}

#vp-root .vp-btn-secondary {{
  background: var(--vp-surface);
  color: var(--vp-primary);
  border: 2px solid var(--vp-primary);
}}

#vp-root .vp-btn-link {{
  background: none;
  color: var(--vp-primary);
  height: auto;
  min-height: 44px;
  padding: 0 8px;
  border-radius: 0;
  text-decoration: underline;
  box-shadow: none;
}}

/* "Call 119": button-style link inside the urgent card body. */
#vp-root .vp-btn-call {{
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 52px;
  margin-top: 16px;
  border-radius: 8px;
  background: var(--vp-urgent-band);
  color: var(--vp-urgent-band-text);
  font-family: inherit;
  font-size: 17px;
  font-weight: 700;
  line-height: 1;
  text-decoration: none;
}}

@media (min-width: 1024px) {{
  #vp-root .vp-btn-call {{
    width: auto;
  }}
}}

/* Focus on every button, input, chip and link. */
#vp-root a:focus,
#vp-root button:focus,
#vp-root input:focus,
#vp-root textarea:focus,
#vp-root select:focus,
#vp-root .vp-chip:focus {{
  outline: 4px solid var(--vp-focus);
  box-shadow: inset 0 0 0 2px var(--vp-ink);
}}

#vp-root .vp-btn-primary:focus {{
  box-shadow: 0 4px 0 var(--vp-pressed-edge), inset 0 0 0 2px var(--vp-ink);
}}

/* Visually hidden but readable by screen readers. */
.vp-sr-only {{
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0 0 0 0);
  white-space: nowrap;
  border: 0;
}}

/* Alert area and care cards. */
#vp-root .vp-alerts {{
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 16px 16px;
}}

/* The always-rendered alert area takes no space when empty. */
#vp-root .vp-alerts.vp-alerts-empty {{
  padding: 0;
}}

@media (min-width: 1024px) {{
  #vp-root .vp-alerts {{
    padding: 16px 24px;
  }}
}}

#vp-root .vp-card {{
  background: var(--vp-surface);
  color: var(--vp-ink);
}}

#vp-root .vp-card-urgent {{
  border: 2px solid var(--vp-urgent-card-border);
}}

#vp-root .vp-card-attention {{
  border: 2px solid var(--vp-attn-band);
}}

#vp-root .vp-card-band {{
  padding: 12px 16px;
}}

#vp-root .vp-band-urgent {{
  background: var(--vp-urgent-band);
  color: var(--vp-urgent-band-text);
}}

#vp-root .vp-band-attention {{
  background: var(--vp-attn-band);
  color: var(--vp-attn-band-text);
}}

#vp-root .vp-card-heading {{
  margin: 0;
  font-size: 17px;
  font-weight: 700;
  color: inherit;
}}

#vp-root .vp-card-body {{
  padding: 16px;
  font-size: 17px;
  color: var(--vp-ink);
}}

/* Errors: surface with a hairline-weight border, never urgent red. */
#vp-root .vp-error {{
  background: var(--vp-surface);
  color: var(--vp-ink);
  border: 2px solid var(--vp-ink-2);
  padding: 16px;
}}

#vp-root .vp-error p {{
  margin: 0;
  font-size: 17px;
  color: var(--vp-ink);
}}

/* Preview banner. */
#vp-root .vp-preview-banner {{
  background: var(--vp-tint);
  color: var(--vp-on-tint);
  padding: 8px 16px;
  font-size: 15px;
}}

/* Step line and progress bar. */
#vp-root .vp-step {{
  padding: 8px 0 0;
}}

#vp-root .vp-step-title {{
  margin: 0 0 8px;
  font-size: 17px;
  font-weight: 600;
  color: var(--vp-ink);
}}

#vp-root .vp-progress {{
  display: flex;
  gap: 8px;
}}

#vp-root .vp-progress-seg {{
  flex: 1 1 0;
  height: 8px;
  border-radius: 4px;
  background: var(--vp-hairline);
  color: var(--vp-ink);
}}

#vp-root .vp-progress-seg.is-done,
#vp-root .vp-progress-seg.is-current {{
  background: var(--vp-primary);
  color: var(--vp-ink);
}}

/* Desktop layout: 250px progress rail on the left, content on the
   right. One column below 1024px with the rail hidden. */
#vp-root #vp-main {{
  display: flex;
  align-items: flex-start;
  gap: 24px;
  width: 100%;
  padding: 8px 16px 16px;
  background: var(--vp-ground);
  color: var(--vp-ink);
}}

@media (min-width: 1024px) {{
  #vp-root #vp-main {{
    padding: 8px 24px 16px;
  }}
}}

#vp-root #vp-rail {{
  display: none;
  min-width: 0;
  background: var(--vp-ground);
  color: var(--vp-ink-2);
}}

#vp-root #vp-content {{
  flex: 1 1 0;
  min-width: 0;
}}

@media (min-width: 1024px) {{
  /* !important is required: gradio's svelte column styles set
     flex-grow and min-width and beat plain ID rules. */
  #vp-root #vp-rail {{
    display: block !important;
    flex: 0 0 250px !important;
    width: 250px !important;
    min-width: 0 !important;
  }}

  #vp-root .vp-rail-item {{
    display: block;
    padding: 12px 16px;
    font-size: 17px;
    color: var(--vp-ink-2);
  }}

  #vp-root .vp-rail-item.is-current {{
    background: var(--vp-tint);
    color: var(--vp-on-tint);
    border-left: 3px solid var(--vp-primary);
    font-weight: 600;
  }}
}}

/* Footer helper text. */
#vp-root .vp-footer {{
  background: var(--vp-ground);
  color: var(--vp-ink-2);
  padding: 16px 16px;
  font-size: 15px;
}}

@media (min-width: 1024px) {{
  #vp-root .vp-footer {{
    padding: 16px 24px;
  }}
}}

#vp-root .vp-footer p {{
  margin: 0 0 8px;
  color: var(--vp-ink-2);
}}

#vp-root .vp-footer p:last-child {{
  margin-bottom: 0;
}}

/* Step 1: helper line, chip buttons, form inputs. */
#vp-root .vp-helper {{
  font-size: 15px;
  color: var(--vp-ink-2);
}}

#vp-root .vp-chip {{
  height: 44px;
  padding: 0 16px;
  font-size: 15px;
  font-weight: 600;
}}

#vp-root .vp-input input,
#vp-root .vp-input textarea {{
  border: 2px solid var(--vp-input-border);
  background: var(--vp-surface);
  color: var(--vp-ink);
  font-size: 17px;
}}

#vp-root .vp-input input::placeholder,
#vp-root .vp-input textarea::placeholder {{
  color: var(--vp-ink-2);
}}

/* Sex choices styled as four buttons. */
#vp-root .vp-sex label {{
  border: 2px solid var(--vp-input-border);
  border-radius: 8px;
  background: var(--vp-surface);
  color: var(--vp-ink);
  font-size: 17px;
  padding: 0 16px;
  height: 44px;
}}

#vp-root .vp-sex label:has(input:checked) {{
  border-color: var(--vp-primary);
  background: var(--vp-tint);
  color: var(--vp-on-tint);
  font-weight: 600;
}}

/* Step 2: question heading, pips, question text, answers list. */
#vp-root .vp-question-heading {{
  margin: 0 0 16px;
  font-size: 26px;
  font-weight: 700;
  color: var(--vp-ink);
}}

@media (min-width: 1024px) {{
  #vp-root .vp-question-heading {{
    font-size: 34px;
  }}
}}

#vp-root .vp-question-text {{
  margin: 0 0 16px;
  font-size: 23px;
  font-weight: 700;
  color: var(--vp-ink);
}}

#vp-root .vp-pips {{
  display: flex;
  gap: 8px;
  margin: 0 0 16px;
}}

#vp-root .vp-pip {{
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: var(--vp-surface);
  color: var(--vp-ink);
  border: 2px solid var(--vp-input-border);
}}

#vp-root .vp-pip-answered {{
  background: var(--vp-primary);
  color: var(--vp-ink);
  border-color: var(--vp-primary);
}}

#vp-root .vp-pip-current {{
  background: var(--vp-tint);
  color: var(--vp-ink);
  border: 2px solid var(--vp-primary);
}}

#vp-root .vp-pip-skipped {{
  background: var(--vp-surface);
  color: var(--vp-ink);
  border: 2px dashed var(--vp-input-border);
}}

#vp-root .vp-answers {{
  display: flex;
  flex-direction: column;
  gap: 12px;
}}

#vp-root .vp-answer p {{
  margin: 0;
  color: var(--vp-ink);
}}

#vp-root .vp-answer-question {{
  font-weight: 600;
  color: var(--vp-ink-2);
}}

#vp-root .vp-answers-none {{
  margin: 0;
  color: var(--vp-ink-2);
}}

/* Step 3: detail rows, Add/Change buttons, section editors. */
#vp-root .vp-detail {{
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}}

#vp-root .vp-detail .html-container {{
  flex: 1 1 auto;
  min-width: 0;
}}

#vp-root .vp-detail-row {{
  min-width: 0;
}}

#vp-root .vp-detail-label {{
  margin: 0 0 4px;
  font-size: 17px;
  font-weight: 700;
  color: var(--vp-ink);
}}

#vp-root .vp-detail-line {{
  margin: 0 0 4px;
  font-size: 17px;
  color: var(--vp-ink);
  overflow-wrap: break-word;
}}

#vp-root .vp-detail-line:last-child {{
  margin-bottom: 0;
}}

#vp-root .vp-detail-sub {{
  font-weight: 600;
  color: var(--vp-ink-2);
}}

#vp-root .vp-not-given {{
  font-style: italic;
  color: var(--vp-ink-2);
}}

#vp-root .vp-editor {{
  display: flex;
  flex-direction: column;
  gap: 12px;
  background: var(--vp-tint);
  color: var(--vp-on-tint);
  border: 2px solid var(--vp-primary);
  border-radius: 8px;
  padding: 16px;
}}

#vp-root .vp-editor-actions {{
  justify-content: flex-end;
}}

/* Step 4: the visit note slip. */
#vp-root .vp-note {{
  background: var(--vp-surface);
  color: var(--vp-ink);
  border-top: 6px solid var(--vp-primary);
  border-radius: 8px;
  padding: 16px;
}}

#vp-root .vp-note-head {{
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 16px;
  margin: 0 0 16px;
}}

#vp-root .vp-note-title {{
  margin: 0;
  font-size: 17px;
  font-weight: 800;
  color: var(--vp-ink);
}}

#vp-root .vp-note-date {{
  font-size: 15px;
  color: var(--vp-ink-2);
}}

#vp-root .vp-stamp {{
  display: inline-block;
  border: 2px solid var(--vp-primary);
  color: var(--vp-primary);
  font-size: 13px;
  font-weight: 700;
  text-transform: uppercase;
  padding: 4px 8px;
  border-radius: 4px;
  transform: rotate(-4deg);
  margin: 0 0 16px;
}}

#vp-root .vp-perforation {{
  border-top: 2px dashed var(--vp-hairline);
  margin: 0 0 16px;
}}

#vp-root .vp-note-row {{
  margin: 0 0 4px;
  font-size: 17px;
  color: var(--vp-ink);
  overflow-wrap: break-word;
}}

#vp-root .vp-note-row strong {{
  font-weight: 700;
  color: var(--vp-ink);
}}

#vp-root .vp-note .vp-helper {{
  margin: 16px 0 0;
}}

/* Step 4: the script and the questions. */
#vp-root .vp-script-heading,
#vp-root .vp-questions-heading {{
  margin: 0 0 8px;
  font-size: 17px;
  font-weight: 800;
  color: var(--vp-ink);
}}

#vp-root #vp-script-text {{
  margin: 0 0 8px;
  font-size: 17px;
  color: var(--vp-ink);
  overflow-wrap: break-word;
}}

#vp-root .vp-questions {{
  margin: 0 0 16px;
  padding-left: 22px;
  font-size: 17px;
  color: var(--vp-ink);
}}

#vp-root .vp-questions li {{
  margin: 0 0 4px;
  color: var(--vp-ink);
}}

#vp-root .vp-questions li:last-child {{
  margin-bottom: 0;
}}

/* Step 4: the two columns stack below 1024px (note first) and sit
   side by side from 1024px. */
#vp-root #vp-step4-grid {{
  display: flex;
  flex-direction: column;
  gap: 16px;
  width: 100%;
  background: var(--vp-ground);
  color: var(--vp-ink);
}}

#vp-root #vp-step4-grid .column {{
  min-width: 0;
  background: var(--vp-ground);
  color: var(--vp-ink);
}}

@media (min-width: 1024px) {{
  #vp-root #vp-step4-grid {{
    flex-direction: row;
    align-items: flex-start;
    gap: 24px;
  }}

  #vp-root #vp-step4-grid .column {{
    flex: 1 1 0 !important;
    min-width: 0 !important;
  }}
}}

/* Step 4: the Download PDF button and its status line. */
#vp-root #vp-pdf-row {{
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 16px;
  width: 100%;
  background: var(--vp-ground);
  color: var(--vp-ink);
}}

#vp-root #vp-pdf-row .column {{
  flex: 0 0 auto;
  min-width: 0;
  background: var(--vp-ground);
  color: var(--vp-ink);
}}

#vp-root #vp-pdf-status p {{
  margin: 0;
}}
"""
