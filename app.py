import os

import gradio as gr

from ui.layout import build_interface
from ui.theme import THEME_CSS, THEME_HEAD

demo = gr.Blocks(title="VisitPrep")
with demo:
    build_interface()
demo.queue(default_concurrency_limit=4)

if __name__ == "__main__":
    # In gradio 6.31.0 the css/head parameters moved from the Blocks
    # constructor to launch().
    demo.launch(
        server_name="0.0.0.0",
        server_port=int(os.environ.get("PORT", "7860")),
        css=THEME_CSS,
        head=THEME_HEAD,
        show_error=False,
    )
