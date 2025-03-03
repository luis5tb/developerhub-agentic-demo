import gradio as gr

from agent_graph import AgentGraph

agent = AgentGraph()

def run_agent(query, history):
    response = agent.run(query)
    return response.content

def create_ui():
    return gr.ChatInterface(fn=run_agent)
