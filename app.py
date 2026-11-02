import os

import gradio as gr

demo = gr.Blocks(title="VisitPrep")
with demo:
    gr.Markdown("VisitPrep is being built.")

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=int(os.environ.get("PORT", "7860")))
