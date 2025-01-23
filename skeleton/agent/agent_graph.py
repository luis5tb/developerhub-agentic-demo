import httpx

from typing import Annotated
from typing_extensions import TypedDict

from langgraph.graph import StateGraph
from langgraph.graph.message import add_messages
# from langgraph.llms import vLLM
from langchain_community.llms import VLLMOpenAI

# from vector_db import VectorDB
from guardrails import apply_guardrails


class LLMNode:
    def __init__(self,  llm_endpoint, llm_token, model_name):
        self.llm = VLLMOpenAI(
            openai_api_key=llm_token,
            openai_api_base=llm_endpoint,
            model_name=model_name,
            async_client=httpx.AsyncClient(verify=False),
            http_client=httpx.Client(verify=False))

    def __call__(self, state):
        # Implement your custom logic here
        # Access the state and perform actions
        messages = state["messages"]
        response = self.llm.invoke(messages)
        return {"messages": add_messages(messages, [response])}


class State(TypedDict):
    # messages have the type "list".
    # The add_messages function appends messages to the list,
    # rather than overwriting them
    messages: Annotated[list, add_messages]


class AgentGraph:
    def __init__(self, llm_endpoint, llm_token, model_name):
        """
        Initialize the agent graph with vLLM and other components.

        Args:
            llm_endpoint (str): URL of the deployed vLLM endpoint.
            llm_token (str): Authorization token for the vLLM endpoint.
        """
        # self.vector_db = VectorDB()
        self.llm = LLMNode(llm_endpoint=llm_endpoint, llm_token=llm_token,
                           model_name=model_name)

        # Build the graph
        graph_builder = StateGraph(State)

        # Add nodes to the graph
        # graph_builder.add_node("input_guardrails",
        #                        self.apply_input_guardrails)
        # graph_builder.add_node("context_retrieval",
        #                        self.retrieve_context)
        graph_builder.add_node("llm", self.llm)
        # graph_builder.add_node("output_guardrails",
        #                        self.apply_output_guardrails)

        # Define transitions between nodes
        # graph_builder.add_edge("input_guardrails", "context_retrieval")
        # graph_builder.add_edge("context_retrieval", "llm")
        # graph_builder.add_edge("llm", "output_guardrails")

        # Set entry and finish points
        # graph_builder.set_entry_point("input_guardrails")
        # graph_builder.set_finish_point("output_guardrails")
        graph_builder.set_entry_point("llm")
        graph_builder.set_finish_point("llm")

        # Compile the graph
        self.agent = graph_builder.compile()

    def apply_input_guardrails(self, state: State) -> State:
        """
        Apply input guardrails to validate or preprocess the query.

        Args:
            state (State): State containing the messages.

        Returns:
            State: Updated state with processed messages.
        """
        state["messages"] = [apply_guardrails(msg)
                             for msg in state["messages"]]
        return state

    def apply_output_guardrails(self, state: State) -> State:
        """
        Apply output guardrails to validate or postprocess the response.

        Args:
            state (State): State containing the messages.

        Returns:
            State: Updated state with processed response.
        """
        state["messages"] = [apply_guardrails(msg)
                             for msg in state["messages"]]
        return state

    def retrieve_context(self, state: State) -> State:
        """
        Retrieve context from the vector database.

        Args:
            state (State): State containing the messages.

        Returns:
            State: Updated state with retrieved context added to messages.
        """
        query = state["messages"][-1]  # Use the last message as the query
        context = self.vector_db.retrieve_context(query)
        state["messages"] = add_messages(state["messages"], [context])
        return state

    def run(self, query) -> list:
        """
        Run the agent with the given messages.

        Args:
            messages (list): List of conversation messages.

        Returns:
            list: Updated messages with responses.
        """
        # initial_state = {"messages": messages}
        # #final_state = self.agent.run(initial_input=initial_state)
        # final_state = self.agent(initial_state)
        response = self.agent.invoke({"messages": [query]})
        return response["messages"][-1]
        # return final_state["messages"]
