from langgraph.graph.message import add_messages
from langchain_core.messages import AIMessage, ToolMessage

import agent_states
import prompts

from llama_stack_client import LlamaStackClient
from llama_stack_client.lib.agents.agent import Agent
from llama_stack_client.types import AgentConfig, UserMessage
# from llama_stack_client.types.agents import Session, SessionCreateResponse


class ResearchAgent:
    def __init__(self, llamastack_server_endpoint: str, model_name: str,
                 tools: list):
        self.client = LlamaStackClient(
            base_url=llamastack_server_endpoint,
        )

        self.agent_config = AgentConfig(
            model=model_name,
            instructions=prompts.llamastack_researcher_prompt,
            toolgroups=tools,
            enable_session_persistence=False,
            tool_choice="auto",
            input_shields=[],
            output_shields=[],
            sampling_params={
                "max_tokens": 4096,
                "temperature": 0.01
            },
        )

        self.agent = Agent(self.client, self.agent_config)

        self.agent_id = self.agent.agent_id
        self.session_id = self.agent.create_session("research-session")

    def __call__(self, state: agent_states.State) -> agent_states.State:
        print("Running Researcher:")
        stock = {
            "stock": state["stock"],
            "messages": state.get("messages", "")
        }

        response = self.agent.create_turn(
            session_id=self.session_id,
            messages=[
                UserMessage(content=str(stock), role="user"),
            ],
            stream=False,)

        if isinstance(response.output_message, ToolMessage):
            result = response
        else:
            result = AIMessage(**response.output_message.model_dump(
                exclude={"type", "name"}))
        messages = state.get("messages", [])
        return {"messages": add_messages(messages, [result]), }


class SummarizationAgent:
    def __init__(self, llamastack_server_endpoint: str, model_name: str,
                 tools: list):
        self.client = LlamaStackClient(
            base_url=llamastack_server_endpoint,
        )

        self.agent_config = AgentConfig(
            model=model_name,
            instructions=prompts.llamastack_summary_prompt,
            toolgroups=tools,
            enable_session_persistence=False,
            tool_choice="auto",
            input_shields=[],
            output_shields=[],
            sampling_params={
                "max_tokens": 4096,
                "temperature": 0.01
            },
        )

        self.agent = Agent(self.client, self.agent_config)

        self.agent_id = self.agent.agent_id
        self.session_id = self.agent.create_session("summarization-session")

    def __call__(self, state: agent_states.State) -> agent_states.State:
        print("Running Summarizer:")
        context = ""  # TO DO: to be obtained from vectordb
        message = {
            "stock": state["stock"],
            "context": context,
            "messages": state.get("messages", []),
        }

        response = self.agent.create_turn(
            session_id=self.session_id,
            messages=[
                UserMessage(content=str(message), role="user"),
            ],
            stream=False)

        result = response.output_message.model_dump(exclude={"type", "name"})
        summaries = state.get("summary", [])
        return {"summary": add_messages(summaries, [result]), }


class RecommendationAgent:
    def __init__(self, llamastack_server_endpoint: str, model_name: str,
                 tools: list):
        self.client = LlamaStackClient(
            base_url=llamastack_server_endpoint,
        )

        self.agent_config = AgentConfig(
            model=model_name,
            instructions=prompts.llamastack_recommender_prompt,
            toolgroups=tools,
            enable_session_persistence=False,
            tool_choice="auto",
            input_shields=[],
            output_shields=[],
            sampling_params={
                "max_tokens": 4096,
                "temperature": 0.01
            },
        )

        self.agent = Agent(self.client, self.agent_config)

        self.agent_id = self.agent.agent_id
        self.session_id = self.agent.create_session("summarization-session")

    def __call__(self, state: agent_states.State) -> agent_states.State:
        print("Running Recommender:")
        message = {
            "stock": state["stock"],
            "summary": state.get("summary", []),
            "messages": state.get("messages", []),
        }

        response = self.agent.create_turn(
            session_id=self.session_id,
            messages=[
                UserMessage(content=message, role="user"),
            ],
            stream=False)

        result = response.output_message.model_dump(exclude={"type", "name"})
        recommendations = state.get("recommendation", [])
        return {
                "recommendation": add_messages(recommendations, [result]),
                }
