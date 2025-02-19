

from langgraph.graph import StateGraph
# from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
# from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.prebuilt import ToolNode

# from vector_db import VectorDB
from guardrails import apply_guardrails

from tools import get_tools
import agents
import agent_states


class AgentGraph:
    def __init__(self, llm_endpoint, llm_token, model_name):
        """
        Initialize the agent graph with vLLM and other components.

        Args:
            llm_endpoint (str): URL of the deployed vLLM endpoint.
            llm_token (str): Authorization token for the vLLM endpoint.
        """
        # self.vector_db = VectorDB()

        tools = get_tools()
        self.tools_node = ToolNode(tools)

        self.researcher_node = agents.ResearchAgent(
            llm_endpoint=llm_endpoint,
            llm_token=llm_token,
            model_name=model_name,
            tools=tools)

        self.summarization_node = agents.SummarizationAgent(
            llm_endpoint=llm_endpoint,
            llm_token=llm_token,
            model_name=model_name)

        self.recommender_node = agents.RecommendationAgent(
            llm_endpoint=llm_endpoint,
            llm_token=llm_token,
            model_name=model_name)

        # Build the graph
        graph_builder = StateGraph(agent_states.State)
        # graph_builder = StateGraph(agent_states.State,
        #                            input=agent_states.InputState,
        #                            output=agent_states.OutputState)

        # Add nodes to the graph
        # graph_builder.add_node("input_guardrails",
        #                        self.apply_input_guardrails)
        # graph_builder.add_node("context_retrieval",
        #                        self.retrieve_context)
        graph_builder.add_node("researcher", self.researcher_node)
        graph_builder.add_node("tools", self.tools_node)
        graph_builder.add_node("summarizer", self.summarization_node)
        graph_builder.add_node("recommender", self.recommender_node)

        # graph_builder.add_node("output_guardrails",
        #                        self.apply_output_guardrails)

        # Define transitions between nodes
        graph_builder.add_edge("tools", "researcher")
        # graph_builder.add_edge("input_guardrails", "context_retrieval")
        # graph_builder.add_edge("context_retrieval", "llm")
        # graph_builder.add_edge("llm", "output_guardrails")
        graph_builder.add_edge("summarizer", "recommender")

        # graph_builder.add_conditional_edges("researcher", tools_condition)
        graph_builder.add_conditional_edges(
            "researcher", self.should_continue,
            {"continue": "summarizer", "tools": "tools"})

        # Set entry and finish points
        # graph_builder.set_entry_point("input_guardrails")
        # graph_builder.set_finish_point("output_guardrails")
        graph_builder.set_entry_point("researcher")
        graph_builder.set_finish_point("recommender")

        # Compile the graph
        #memory = MemorySaver()
        self.agent = graph_builder.compile()  # checkpointer=memory)

    def should_continue(self, state: agent_states.State):
        messages = state["messages"]
        last_message = messages[-1]
        if last_message.tool_calls:
            print("Calling tools")
            return "tools"
        print("Calling summarizer")
        return "continue"

    def apply_input_guardrails(
            self, state: agent_states.State) -> agent_states.State:
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

    def apply_output_guardrails(
            self, state: agent_states.State) -> agent_states.State:
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

    def retrieve_context(
            self, state: agent_states.State) -> agent_states.State:
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
        #config = {"configurable": {"thread_id": "1"}}
        initial_state = agent_states.State(stock=query,
                                           messages=[],
                                           summary=[],
                                           recommendation=[])
        response = self.agent.invoke(initial_state)  #, config)
        return response["recommendation"][-1]
