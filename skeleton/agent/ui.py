import os

import gradio as gr

#from agent_graph import AgentGraph
from llamastack_agent_graph import LLamaStackAgentGraph


LLM_ENDPOINT = os.getenv("LLM_ENDPOINT")
TOKEN = os.getenv("API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME")

LLAMASTACK_ENDPOINT = os.getenv("LLAMASTACK_ENDPOINT")
LLAMASTACK_MODEL = os.getenv("LLAMASTACK_MODEL")

#agent = AgentGraph(llm_endpoint=LLM_ENDPOINT, llm_token=TOKEN, model_name=MODEL_NAME)
agent = LLamaStackAgentGraph(llamastack_endpoint=LLAMASTACK_ENDPOINT, model=LLAMASTACK_MODEL)

def run_agent(query, history):
    response = agent.run(query)
    return response.content

def create_ui():
    return gr.ChatInterface(fn=run_agent)
