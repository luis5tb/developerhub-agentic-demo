import gradio as gr

#from agent_graph import AgentGraph
from llamastack_agent_graph import LLamaStackAgentGraph

#agent = AgentGraph()
agent = LLamaStackAgentGraph()

def run_agent(query, history):
    response = agent.run(query)
    return response.content

def create_ui():
    return gr.ChatInterface(fn=run_agent)
