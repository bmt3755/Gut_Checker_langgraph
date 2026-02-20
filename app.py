import os
os.system("playwright install --with-deps chromium")

import gradio as gr
from gutchecker import GutChecker

async def setup():
    agent = GutChecker()
    await agent.setup()
    return agent

async def process_message(agent, message, history):
    criteria = "Analyze product safety. Calculate average score. Keep summary under 1 sentence."
    results = await agent.run_superstep(message, criteria, history)
    return results, agent

async def reset():
    new_agent = GutChecker()
    await new_agent.setup()
    return "", None, new_agent

def free_resources(agent):
    print("Cleaning up browser resources...")
    try:
        if agent:
            agent.cleanup()
    except Exception as e:
        print(f"Exception during cleanup: {e}")

with gr.Blocks(title="GutChecker", theme=gr.themes.Soft(primary_hue="emerald")) as ui:
    gr.Markdown("# 🛡️ GutChecker AI")
    
    # The state manages the agent and safely cleans up Playwright on exit
    agent_state = gr.State(delete_callback=free_resources)

    with gr.Row():
        chatbot = gr.Chatbot(label="Auditor Transcript", height=500, type="messages")
    
    with gr.Row():
        message = gr.Textbox(show_label=False, placeholder="Paste product URL or ingredients list here...", scale=4)
        go_button = gr.Button("🚀 Run Audit", variant="primary", scale=1)
    
    with gr.Row():
        reset_button = gr.Button("🗑️ Reset Chat", variant="stop")

    # Initialize the agent asynchronously when the web page loads
    ui.load(setup, [], [agent_state])
    
    # Event Handlers
    message.submit(
        process_message, [agent_state, message, chatbot], [chatbot, agent_state]
    )
    go_button.click(
        process_message, [agent_state, message, chatbot], [chatbot, agent_state]
    )
    reset_button.click(reset, [], [message, chatbot, agent_state])

ui.launch()