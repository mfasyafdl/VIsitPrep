import os

import gradio as gr

from ui.layout import build_interface
from ui.theme import THEME_CSS, THEME_HEAD

demo = gr.Blocks(title="VisitPrep")
with demo:
    build_interface()
demo.queue(default_concurrency_limit=4)


def launch_kwargs() -> dict:
    # PORT is read here, at call time, so the environment can still be
    # changed between import and launch.
    return {
        "server_name": "0.0.0.0",
        "server_port": int(os.environ.get("PORT", "7860")),
        "css": THEME_CSS,
        "head": THEME_HEAD,
        "show_error": False,
        "footer_links": [],
        "run_history": False,
    }


if __name__ == "__main__":
    # In gradio 6.31.0 the css/head parameters moved from the Blocks
    # constructor to launch(). run_history is off because patient text
    # must not stay in the browser: with the default run history the
    # story is kept in localStorage and shown at /gradio_api/runs, and
    # Start over does not clear it. footer_links [] removes Gradio's
    # own "Built with Gradio" footer.
    demo.launch(**launch_kwargs())
