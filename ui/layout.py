"""Builds the Gradio component tree for VisitPrep.

This module only builds components and wires events to the plain
handler functions in ui/handlers.py. All HTML content comes from
ui/components.py; all session logic lives in ui/handlers.py. No
business logic here.
"""

import datetime
from functools import partial

import gradio as gr

import ui.backend as backend
from core.schema import Alert
from ui import handlers
from ui.components import (
    ALERTS_ERROR_MESSAGE,
    DETAIL_ROWS,
    STEP_NAMES,
    answers_list_html,
    alerts_error_html,
    alerts_html,
    change_label,
    detail_row_html,
    footer_html,
    header_html,
    pips_html,
    preview_banner_html,
    progress_html,
    question_heading_html,
    question_text_html,
    questions_html,
    rail_html,
    script_html,
    visit_note_html,
)
from ui.state import new_state

STEP_1 = 1
STEP_2 = 2
STEP_3 = 3
STEP_4 = 4

WORKING_LABEL = "Working… this can take up to a minute"
SUMMARY_WORKING_LABEL = "Writing your note… this can take up to a minute"

COPY_SCRIPT_JS = (
    "() => { const el = document.querySelector('#vp-script-text'); "
    "const b = document.querySelector('#vp-copy-script'); "
    "if (!el || !b) return; "
    "navigator.clipboard.writeText(el.innerText).then(() => { "
    "b.textContent = 'Copied'; "
    "setTimeout(() => { b.textContent = 'Copy what to say'; }, 2000); "
    "}, () => { b.textContent = 'Select the text to copy'; }); }"
)

SCROLL_TO_TOP_JS = (
    "() => { const r = document.querySelector('#vp-root'); "
    "if (r) r.scrollIntoView({block: 'start'}); }"
)

SEVERITY_CHOICES = (
    ("Mild", "mild"),
    ("Moderate", "moderate"),
    ("Severe", "severe"),
    ("Not sure", "not-sure"),
)

SEX_CHOICES = (
    ("Female", "female"),
    ("Male", "male"),
    ("Other", "other"),
    ("Prefer not to say", "not-specified"),
)

# Editor field order per section; the keys match handlers.editor_values.
EDITOR_FIELDS = {
    "problem": ("complaint", "symptoms"),
    "timing": ("onset", "duration", "severity"),
    "medicines": ("lines", "none"),
    "allergies": ("lines", "none"),
    "history": ("lines", "none"),
    "concerns": ("lines",),
    "about": ("age_text", "sex"),
}


def _alerts_area(state: dict) -> str:
    """The alert area: the care cards, or the check-failure card."""
    if state["alerts_error"]:
        return alerts_error_html(ALERTS_ERROR_MESSAGE)
    return alerts_html([Alert(**alert) for alert in state["alerts"]])


def _error_box(state: dict) -> str:
    """The step error card; empty when there is no error."""
    if state["error"]:
        return alerts_error_html(state["error"])
    return ""


def _question_number(state: dict) -> int:
    return min(len(state["asked"]) + len(state["skipped"]) + 1, 5)


def _question_text(state: dict) -> str:
    if state["step"] == STEP_2 and state["question"]:
        return question_text_html(state["question"])
    return ""


def _empty_editor(section: str) -> dict:
    """Placeholder editor values while the record is not available."""
    values = {}
    for key in EDITOR_FIELDS[section]:
        if key == "none":
            values[key] = False
        elif key in ("severity", "sex"):
            values[key] = None
        else:
            values[key] = ""
    return values


def _editor_field_values(state: dict, section: str) -> list:
    """The field updates for one section editor.

    While that editor is open and a save failed, the fields keep what
    the patient typed (no-change updates). In every other case the
    fields get the values of the stored record (or empty placeholders
    while the record is not available).
    """
    if state["editing"] == section and state["error"] is not None:
        return [gr.update() for _ in EDITOR_FIELDS[section]]
    merged = state["step"] == STEP_3 and state["merged"] is True
    if merged and state["record"] is not None:
        editor = handlers.editor_values(state["record"], section)
    else:
        editor = _empty_editor(section)
    return [gr.update(value=editor[key]) for key in EDITOR_FIELDS[section]]


def _step3_values(state: dict) -> list:
    """The step 3 outputs: the checking line, the rows, the editors."""
    at_step3 = state["step"] == STEP_3
    merged = at_step3 and state["merged"] is True
    record = state["record"] if merged else None
    values = [gr.update(visible=at_step3 and not state["merged"])]
    for section, _label in DETAIL_ROWS:
        if record is not None:
            row = detail_row_html(record, section)
            label = change_label(record, section)
        else:
            row = ""
            label = "Change"
        values.append(row)
        values.append(gr.update(value=label, interactive=merged))
        values.append(gr.update(visible=state["editing"] == section))
        values.extend(_editor_field_values(state, section))
        values.append(gr.update(interactive=merged))
        values.append(gr.update(interactive=merged))
    return values


def _step4_values(state: dict) -> list:
    """The step 4 outputs: the note, the script, the questions."""
    summary = state["summary"]
    if summary is None:
        return ["", "", ""]
    return [
        visit_note_html(summary, datetime.date.today()),
        script_html(summary),
        questions_html(summary),
    ]


def _summary_button_update(state: dict):
    """The Write my summary button: interactive only on merged step 3."""
    if state["step"] == STEP_3 and state["merged"] is True:
        return gr.update(interactive=True, value="Write my summary")
    return gr.update(interactive=False, value="Write my summary")


def _render(state: dict) -> list:
    """Map the state dict to the values of render_outputs."""
    step = state["step"]
    number = _question_number(state)
    skipped_positions = [entry["position"] for entry in state["skipped"]]
    return [
        _alerts_area(state),
        _error_box(state),
        progress_html(step),
        rail_html(step),
        gr.update(visible=step == STEP_1),
        gr.update(visible=step == STEP_2),
        gr.update(visible=step == STEP_3),
        gr.update(visible=step == STEP_4),
        question_heading_html(number),
        pips_html(len(state["asked"]), skipped_positions, number),
        _question_text(state),
        answers_list_html(state["asked"]),
        gr.update(label=f"Your answers so far ({len(state['asked'])})"),
    ] + _step3_values(state) + _step4_values(state) + [_summary_button_update(state)]


def _answer_box_value(state: dict):
    """Clear the answer box on success; keep the typed text on error."""
    if state["error"] is None:
        return ""
    return gr.update()


def _render_after_answer(state: dict) -> list:
    return _render(state) + [_answer_box_value(state)]


def _disable_step1() -> list:
    return [
        gr.update(interactive=False),
        gr.update(interactive=False),
        gr.update(interactive=False),
        gr.update(interactive=False, value=WORKING_LABEL),
    ]


def _enable_step1(state: dict) -> list:
    return (
        [
            gr.update(interactive=True),
            gr.update(interactive=True),
            gr.update(interactive=True),
            gr.update(interactive=True, value="Continue"),
        ]
        + _render(state)
    )


def _disable_summarize() -> list:
    """The instant step before on_summarize: working label plus the
    seven Change buttons made not interactive."""
    updates = [
        gr.update(interactive=False, value=SUMMARY_WORKING_LABEL)
    ]
    updates.extend(gr.update(interactive=False) for _ in DETAIL_ROWS)
    return updates


def _reset(state: dict) -> list:
    """Start over: fresh state, render, and cleared step 1 inputs."""
    fresh = handlers.on_reset(state)
    values = [fresh] + _render(fresh)
    values += ["", "", None, ""]
    values += [gr.update(interactive=True) for _ in range(3)]
    values.append(gr.update(interactive=True, value="Continue"))
    return values


def _open_editor(section: str, state: dict) -> dict:
    """Wire a section's Change button to open_editor."""
    return handlers.open_editor(state, section)


def _save_section(section: str, state: dict, *field_values) -> dict:
    """Wire a section's Save button to save_section."""
    return handlers.save_section(
        state, section, dict(zip(EDITOR_FIELDS[section], field_values))
    )


def build_interface() -> None:
    """Build the four-step app inside the surrounding Blocks.

    Page order: header bar, preview banner (preview builds only),
    alert area, step line with progress bar, step content, footer.
    The desktop rail sits on the left from 1024px.
    """
    state = gr.State(new_state())

    with gr.Column(elem_id="vp-root"):
        with gr.Row(elem_id="vp-header", elem_classes="vp-header"):
            gr.HTML(header_html(), scale=0)
            start_over_btn = gr.Button(
                "Start over",
                elem_classes="vp-btn vp-btn-link",
                elem_id="vp-start-over",
                scale=0,
            )
        if backend.PREVIEW:
            gr.HTML(preview_banner_html(), elem_id="vp-preview")
        config_message = backend.config_problem()
        if config_message is not None:
            gr.HTML(
                alerts_error_html(
                    config_message
                    + " Warning-sign checks still work, "
                    "but VisitPrep cannot write your questions "
                    "or your note."
                ),
                elem_id="vp-config-error",
            )
        alerts_area = gr.HTML(alerts_html([]), elem_id="vp-alerts")
        with gr.Row(elem_id="vp-main"):
            with gr.Column(elem_id="vp-rail"):
                rail = gr.HTML(rail_html(STEP_1), elem_id="vp-rail-nav")
            with gr.Column(elem_id="vp-content"):
                progress = gr.HTML(progress_html(STEP_1), elem_id="vp-progress")
                error_box = gr.HTML("", elem_id="vp-error")
                with gr.Column(elem_id="vp-step-1", visible=True) as step1_col:
                    gr.Markdown(f"# {STEP_NAMES[0]}")
                    gr.Markdown(
                        "Write it the way you'd tell a friend. "
                        "We'll turn it into a clear note for your doctor."
                    )
                    story_box = gr.Textbox(
                        label="Your symptoms",
                        lines=5,
                        max_lines=20,
                        elem_classes="vp-input",
                        elem_id="vp-story",
                    )
                    with gr.Row(elem_id="vp-chips"):
                        chip_started = gr.Button(
                            "It started…",
                            elem_classes="vp-btn vp-btn-secondary vp-chip",
                        )
                        chip_feels = gr.Button(
                            "It feels…",
                            elem_classes="vp-btn vp-btn-secondary vp-chip",
                        )
                        chip_takes = gr.Button(
                            "I take…",
                            elem_classes="vp-btn vp-btn-secondary vp-chip",
                        )
                    age_box = gr.Textbox(
                        label="Age, if you want to share it",
                        elem_classes="vp-input",
                    )
                    sex_radio = gr.Radio(
                        label="Sex",
                        choices=SEX_CHOICES,
                        value=None,
                        elem_classes="vp-sex",
                    )
                    continue_btn = gr.Button(
                        "Continue",
                        elem_classes="vp-btn vp-btn-primary",
                        elem_id="vp-continue",
                    )
                with gr.Column(elem_id="vp-step-2", visible=False) as step2_col:
                    q_heading = gr.HTML(
                        question_heading_html(1), elem_id="vp-q-heading"
                    )
                    pips = gr.HTML(pips_html(0, [], 1), elem_id="vp-pips")
                    question = gr.HTML("", elem_id="vp-question")
                    answer_box = gr.Textbox(
                        label="Your answer",
                        lines=3,
                        max_lines=10,
                        elem_classes="vp-input",
                        elem_id="vp-answer",
                    )
                    with gr.Row():
                        save_btn = gr.Button(
                            "Save answer",
                            elem_classes="vp-btn vp-btn-primary",
                            elem_id="vp-save-answer",
                        )
                        skip_btn = gr.Button(
                            "Skip this question",
                            elem_classes="vp-btn vp-btn-secondary",
                            elem_id="vp-skip",
                        )
                    done_btn = gr.Button(
                        "I'm done, check my details",
                        elem_classes="vp-btn vp-btn-link",
                        elem_id="vp-done",
                    )
                    gr.HTML(
                        '<p class="vp-helper">'
                        "Skipping still uses one of the five questions."
                        "</p>"
                    )
                    with gr.Accordion(
                        "Your answers so far (0)", open=False
                    ) as accordion:
                        answers = gr.HTML(
                            answers_list_html([]), elem_id="vp-answers"
                        )
                with gr.Column(elem_id="vp-step-3", visible=False) as step3_col:
                    gr.Markdown(f"# {STEP_NAMES[2]}")
                    gr.Markdown(
                        "Your own words are kept. "
                        "Press Change on anything that's wrong."
                    )
                    step3_checking = gr.HTML(
                        '<p class="vp-helper">Checking your answers… this can '
                        "take up to a minute</p>",
                        elem_id="vp-step3-checking",
                    )
                    step3_parts = {}
                    for section, _label in DETAIL_ROWS:
                        with gr.Row(elem_classes="vp-detail"):
                            row = gr.HTML(
                                "", elem_id=f"vp-step3-row-{section}"
                            )
                            change = gr.Button(
                                "Change",
                                elem_classes="vp-btn vp-btn-link",
                                elem_id=f"vp-step3-change-{section}",
                            )
                        fields = {}
                        with gr.Column(
                            elem_id=f"vp-step3-editor-{section}",
                            elem_classes="vp-editor",
                            visible=False,
                        ) as editor_group:
                            if section == "problem":
                                fields["complaint"] = gr.Textbox(
                                    label="Main problem",
                                    elem_classes="vp-input",
                                    elem_id="vp-edit-problem-complaint",
                                )
                                fields["symptoms"] = gr.Textbox(
                                    label="Symptoms (one per line)",
                                    lines=3,
                                    max_lines=8,
                                    elem_classes="vp-input",
                                    elem_id="vp-edit-problem-symptoms",
                                )
                            elif section == "timing":
                                fields["onset"] = gr.Textbox(
                                    label="When did it start?",
                                    elem_classes="vp-input",
                                    elem_id="vp-edit-timing-onset",
                                )
                                fields["duration"] = gr.Textbox(
                                    label="How long has it been going on?",
                                    elem_classes="vp-input",
                                    elem_id="vp-edit-timing-duration",
                                )
                                fields["severity"] = gr.Radio(
                                    label="How bad is it?",
                                    choices=SEVERITY_CHOICES,
                                    value=None,
                                    elem_classes="vp-sex",
                                    elem_id="vp-edit-timing-severity",
                                )
                            elif section == "medicines":
                                fields["lines"] = gr.Textbox(
                                    label=(
                                        "Medicines (one per line, for example: "
                                        "Amlodipine, every morning)"
                                    ),
                                    lines=3,
                                    max_lines=8,
                                    elem_classes="vp-input",
                                    elem_id="vp-edit-medicines-lines",
                                )
                                fields["none"] = gr.Checkbox(
                                    label="I take no medicines",
                                    elem_id="vp-edit-medicines-none",
                                )
                            elif section == "allergies":
                                fields["lines"] = gr.Textbox(
                                    label="Allergies (one per line)",
                                    lines=3,
                                    max_lines=8,
                                    elem_classes="vp-input",
                                    elem_id="vp-edit-allergies-lines",
                                )
                                fields["none"] = gr.Checkbox(
                                    label="No allergies",
                                    elem_id="vp-edit-allergies-none",
                                )
                            elif section == "history":
                                fields["lines"] = gr.Textbox(
                                    label="Health conditions (one per line)",
                                    lines=3,
                                    max_lines=8,
                                    elem_classes="vp-input",
                                    elem_id="vp-edit-history-lines",
                                )
                                fields["none"] = gr.Checkbox(
                                    label="No known health conditions",
                                    elem_id="vp-edit-history-none",
                                )
                            elif section == "concerns":
                                fields["lines"] = gr.Textbox(
                                    label=(
                                        "Your questions and worries "
                                        "(one per line)"
                                    ),
                                    lines=3,
                                    max_lines=8,
                                    elem_classes="vp-input",
                                    elem_id="vp-edit-concerns-lines",
                                )
                            elif section == "about":
                                fields["age_text"] = gr.Textbox(
                                    label="Age",
                                    elem_classes="vp-input",
                                    elem_id="vp-edit-about-age",
                                )
                                fields["sex"] = gr.Radio(
                                    label="Sex",
                                    choices=SEX_CHOICES,
                                    value=None,
                                    elem_classes="vp-sex",
                                    elem_id="vp-edit-about-sex",
                                )
                            with gr.Row(elem_classes="vp-editor-actions"):
                                save = gr.Button(
                                    "Save",
                                    elem_classes="vp-btn vp-btn-secondary",
                                    elem_id=f"vp-step3-save-{section}",
                                )
                                cancel = gr.Button(
                                    "Cancel",
                                    elem_classes="vp-btn vp-btn-link",
                                    elem_id=f"vp-step3-cancel-{section}",
                                )
                        step3_parts[section] = {
                            "row": row,
                            "change": change,
                            "editor": editor_group,
                            "fields": fields,
                            "save": save,
                            "cancel": cancel,
                        }
                    summary_btn = gr.Button(
                        "Write my summary",
                        elem_classes="vp-btn vp-btn-primary",
                        interactive=False,
                        elem_id="vp-step3-summary",
                    )
                with gr.Column(elem_id="vp-step-4", visible=False) as step4_col:
                    gr.Markdown(f"# {STEP_NAMES[3]}")
                    gr.HTML('<p class="vp-helper">Show this to your doctor.</p>')
                    with gr.Row(elem_id="vp-step4-grid"):
                        with gr.Column():
                            visit_note = gr.HTML("", elem_id="vp-visit-note")
                        with gr.Column():
                            script_block = gr.HTML("", elem_id="vp-script")
                            copy_btn = gr.Button(
                                "Copy what to say",
                                elem_classes="vp-btn vp-btn-secondary",
                                elem_id="vp-copy-script",
                            )
                            questions_block = gr.HTML("", elem_id="vp-questions")
                    change_details_btn = gr.Button(
                        "Change my details",
                        elem_classes="vp-btn vp-btn-secondary",
                        elem_id="vp-change-details",
                    )
        gr.HTML(footer_html(), elem_id="vp-footer")

    step3_outputs = [step3_checking]
    for section, _label in DETAIL_ROWS:
        part = step3_parts[section]
        step3_outputs.append(part["row"])
        step3_outputs.append(part["change"])
        step3_outputs.append(part["editor"])
        for key in EDITOR_FIELDS[section]:
            step3_outputs.append(part["fields"][key])
        step3_outputs.append(part["save"])
        step3_outputs.append(part["cancel"])

    render_outputs = [
        alerts_area,
        error_box,
        progress,
        rail,
        step1_col,
        step2_col,
        step3_col,
        step4_col,
        q_heading,
        pips,
        question,
        answers,
        accordion,
    ] + step3_outputs + [visit_note, script_block, questions_block, summary_btn]

    chip_started.click(
        partial(handlers.append_chip, chip="It started…"),
        inputs=story_box,
        outputs=story_box,
    )
    chip_feels.click(
        partial(handlers.append_chip, chip="It feels…"),
        inputs=story_box,
        outputs=story_box,
    )
    chip_takes.click(
        partial(handlers.append_chip, chip="I take…"),
        inputs=story_box,
        outputs=story_box,
    )

    # Every event that can move to step 3 runs its handler, renders,
    # then runs enter_review and renders again. The steps that call the
    # model are kept in variables so Start over can cancel them.
    continue_model_step = continue_btn.click(
        _disable_step1,
        outputs=[chip_started, chip_feels, chip_takes, continue_btn],
    ).then(
        handlers.on_continue,
        inputs=[state, story_box, age_box, sex_radio],
        outputs=[state],
    )
    continue_model_step.then(
        _enable_step1,
        inputs=[state],
        outputs=[chip_started, chip_feels, chip_takes, continue_btn]
        + render_outputs,
    ).then(
        handlers.enter_review,
        inputs=[state],
        outputs=[state],
    ).then(
        _render,
        inputs=[state],
        outputs=render_outputs,
    ).then(None, js=SCROLL_TO_TOP_JS)

    save_model_step = save_btn.click(
        handlers.on_answer,
        inputs=[state, answer_box],
        outputs=[state],
    )
    save_merge_step = save_model_step.then(
        _render_after_answer,
        inputs=[state],
        outputs=render_outputs + [answer_box],
    ).then(
        handlers.enter_review,
        inputs=[state],
        outputs=[state],
    )
    save_merge_step.then(
        _render,
        inputs=[state],
        outputs=render_outputs,
    ).then(None, js=SCROLL_TO_TOP_JS)

    skip_model_step = skip_btn.click(
        handlers.on_skip,
        inputs=[state],
        outputs=[state],
    )
    skip_merge_step = skip_model_step.then(
        _render_after_answer,
        inputs=[state],
        outputs=render_outputs + [answer_box],
    ).then(
        handlers.enter_review,
        inputs=[state],
        outputs=[state],
    )
    skip_merge_step.then(
        _render,
        inputs=[state],
        outputs=render_outputs,
    ).then(None, js=SCROLL_TO_TOP_JS)

    done_merge_step = done_btn.click(
        handlers.on_finish,
        inputs=[state],
        outputs=[state],
    ).then(
        _render,
        inputs=[state],
        outputs=render_outputs,
    ).then(
        handlers.enter_review,
        inputs=[state],
        outputs=[state],
    )
    done_merge_step.then(
        _render,
        inputs=[state],
        outputs=render_outputs,
    ).then(None, js=SCROLL_TO_TOP_JS)

    for section, _label in DETAIL_ROWS:
        part = step3_parts[section]
        part["change"].click(
            partial(_open_editor, section),
            inputs=[state],
            outputs=[state],
        ).then(
            _render,
            inputs=[state],
            outputs=render_outputs,
        )
        part["save"].click(
            partial(_save_section, section),
            inputs=[state]
            + [part["fields"][key] for key in EDITOR_FIELDS[section]],
            outputs=[state],
        ).then(
            _render,
            inputs=[state],
            outputs=render_outputs,
        )
        part["cancel"].click(
            handlers.cancel_editor,
            inputs=[state],
            outputs=[state],
        ).then(
            _render,
            inputs=[state],
            outputs=render_outputs,
        )

    change_buttons = [
        step3_parts[section]["change"] for section, _label in DETAIL_ROWS
    ]
    summarize_model_step = summary_btn.click(
        _disable_summarize,
        outputs=[summary_btn] + change_buttons,
    ).then(
        handlers.on_summarize,
        inputs=[state],
        outputs=[state],
    )
    summarize_model_step.then(
        _render,
        inputs=[state],
        outputs=render_outputs,
    ).then(None, js=SCROLL_TO_TOP_JS)

    copy_btn.click(fn=None, js=COPY_SCRIPT_JS)

    change_details_btn.click(
        handlers.on_change_details,
        inputs=[state],
        outputs=[state],
    ).then(
        _render,
        inputs=[state],
        outputs=render_outputs,
    ).then(None, js=SCROLL_TO_TOP_JS)

    start_over_btn.click(
        _reset,
        inputs=[state],
        outputs=[state]
        + render_outputs
        + [
            story_box,
            age_box,
            sex_radio,
            answer_box,
            chip_started,
            chip_feels,
            chip_takes,
            continue_btn,
        ],
        cancels=[
            continue_model_step,
            save_merge_step,
            skip_merge_step,
            done_merge_step,
            summarize_model_step,
        ],
    ).then(None, js=SCROLL_TO_TOP_JS)
