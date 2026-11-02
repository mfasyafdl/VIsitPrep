"""Builds the Gradio component tree for VisitPrep.

This module only builds components and wires events. All HTML content
comes from ui/components.py; all event handler logic will live in
ui/handlers.py. No business logic here.
"""

import gradio as gr

from ui.components import (
    STEP_NAMES,
    alerts_html,
    footer_html,
    header_html,
    progress_html,
    rail_html,
)


def build_interface() -> None:
    """Build the static four-step shell inside the surrounding Blocks.

    Page order: header bar, alert area, step line with progress bar,
    step content (only step 1 visible), footer. The desktop rail and
    the action buttons area are wired in a later task.
    """
    with gr.Column(elem_id="vp-root"):
        gr.HTML(header_html(), elem_id="vp-header")
        gr.HTML(alerts_html([]), elem_id="vp-alerts")
        with gr.Row(elem_id="vp-main"):
            with gr.Column(elem_id="vp-rail"):
                gr.HTML(rail_html(1))
            with gr.Column(elem_id="vp-content"):
                gr.HTML(progress_html(1), elem_id="vp-progress")
                with gr.Column(elem_id="vp-step-1", visible=True):
                    gr.Markdown(f"# {STEP_NAMES[0]}")
                with gr.Column(elem_id="vp-step-2", visible=False):
                    gr.Markdown(f"# {STEP_NAMES[1]}")
                with gr.Column(elem_id="vp-step-3", visible=False):
                    gr.Markdown(f"# {STEP_NAMES[2]}")
                with gr.Column(elem_id="vp-step-4", visible=False):
                    gr.Markdown(f"# {STEP_NAMES[3]}")
        gr.HTML(footer_html(), elem_id="vp-footer")
