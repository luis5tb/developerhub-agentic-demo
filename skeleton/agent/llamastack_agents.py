from langgraph.graph.message import add_messages
from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

import agent_states
import prompts

from llama_stack_client import LlamaStackClient
from llama_stack_client.lib.agents.agent import Agent
from llama_stack_client.types.agent_create_params import AgentConfig


def create_client(llamastack_server_endpoint):
    #from llama_stack import LlamaStackAsLibraryClient
    #client = LlamaStackAsLibraryClient(template)
    #client.initialize()
    client = LlamaStackClient(
        base_url=llamastack_server_endpoint
    )
    return client


class LlamaStackResearchAgent:
    def __init__(self, llamastack_server_endpoint, model_name, tools=None):
        self.client = create_client(llamastack_server_endpoint)

        research_prompt = ChatPromptTemplate.from_messages([
            #("system", prompts.system_prompt),
            ("system", prompts.researcher_prompt),
            MessagesPlaceholder(variable_name="stock"),
            ])
        research_prompt = research_prompt.partial(
            tool_names=", ".join([tool.name for tool in tools]))

        self.agent_config = AgentConfig(
            sampling_params = {
                "max_tokens" : 4096,
                "temperature": 0.01
            },
            model=model_name,
            # Define instructions for the agent ( aka system prompt)
            instructions=research_prompt,
            enable_session_persistence=False,
            # Define tools available to the agent
            toolgroups=[
                "builtin::code_interpreter",
                "builtin::websearch"
            ],
            tool_choice="auto",
            input_shields=[],
            output_shields=[],
        )

        self.rag_agent = Agent(self.client, self.agent_config)

        self.session_id = self.rag_agent.create_session("test-session")

    def __call__(self, state: agent_states.State) -> agent_states.State:
        # Implement your custom logic here
        # Access the state and perform actions
        print("Running Researcher:")
        stock = {
            "stock": state["stock"],
            "messages": state.get("messages", "")
        }
        #response = self.agent.invoke([str(stock)])

        response = self.rag_agent.create_turn(
            messages=[{"role": "user", "content": stock}],
            session_id=self.session_id,
            stream=False,)

        if isinstance(response, ToolMessage):
            result = response
        else:
            result = AIMessage(**response.model_dump(exclude={"type", "name"}))

        messages = state.get("messages", [])
        return {
                "messages": add_messages(messages, [result]),
                }
