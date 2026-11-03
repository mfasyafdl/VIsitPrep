"""Builds the Gradio component tree for VisitPrep.

This module only builds components and wires events to the plain
handler functions in ui/handlers.py. All HTML content comes from
ui/components.py; all session logic lives in ui/handlers.py. No
business logic here.
"""

from functools import partial

import gradio as gr

import ui.backend as backend
from core.schema import Alert
from ui import handlers
from ui.components import (
    ALERTS_ERROR_MESSAGE,
    STEP_NAMES,
    answers_list_html,
    alerts_error_html,
    alerts_html,
    footer_html,
    header_html,
    pips_html,
    preview_banner_html,
    progress_html,
    question_heading_html,
    question_text_html,
    rail_html,
)
from ui.state import new_state

STEP_1 = 1
STEP_2 = 2
STEP_3 = 3
STEP_4 = 4

WORKING_LABEL = "Working… this can take up to a minute"


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
    ]


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


def build_interface() -> None:
    """Build the four-step app inside the surrounding Blocks.

    Page order: header bar, preview banner (preview builds only),
    alert area, step line with progress bar, step content, footer.
    The desktop rail sits on the left from 1024px.
    """
    state = gr.State(new_state())

    with gr.Column(elem_id="vp-root"):
        gr.HTML(header_html(), elem_id="vp-header")
        if backend.PREVIEW:
            gr.HTML(preview_banner_html(), elem_id="vp-preview")
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
                        choices=[
                            ("Female", "female"),
                            ("Male", "male"),
                            ("Other", "other"),
                            ("Prefer not to say", "not-specified"),
                        ],
                        value=None,
                        elem_classes="vp-sex",
                    )
                    continue_btn = gr.Button(
                        "Continue",
                        elem_classes="vp-btn vp-btn-primary",
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
                    )
                    with gr.Row():
                        save_btn = gr.Button(
                            "Save answer",
                            elem_classes="vp-btn vp-btn-primary",
                        )
                        skip_btn = gr.Button(
                            "Skip this question",
                            elem_classes="vp-btn vp-btn-secondary",
                        )
                    done_btn = gr.Button(
                        "I'm done, check my details",
                        elem_classes="vp-btn vp-btn-link",
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
                with gr.Column(elem_id="vp-step-4", visible=False) as step4_col:
                    gr.Markdown(f"# {STEP_NAMES[3]}")
        gr.HTML(footer_html(), elem_id="vp-footer")

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
    ]

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

    continue_btn.click(
        _disable_step1,
        outputs=[chip_started, chip_feels, chip_takes, continue_btn],
    ).then(
        handlers.on_continue,
        inputs=[state, story_box, age_box, sex_radio],
        outputs=[state],
    ).then(
        _enable_step1,
        inputs=[state],
        outputs=[chip_started, chip_feels, chip_takes, continue_btn]
        + render_outputs,
    )

    save_btn.click(
        handlers.on_answer,
        inputs=[state, answer_box],
        outputs=[state],
    ).then(
        _render_after_answer,
        inputs=[state],
        outputs=render_outputs + [answer_box],
    )

    skip_btn.click(
        handlers.on_skip,
        inputs=[state],
        outputs=[state],
    ).then(
        _render_after_answer,
        inputs=[state],
        outputs=render_outputs + [answer_box],
    )

    done_btn.click(
        handlers.on_finish,
        inputs=[state],
        outputs=[state],
    ).then(
        _render,
        inputs=[state],
        outputs=render_outputs,
    )
