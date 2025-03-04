

from langgraph.graph import StateGraph
# from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import ToolNode
from langchain_core.messages import AIMessage

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
        tools = get_tools()
        self.MAX_TOOL_CALLS = 3  # Set maximum number of allowed tool calls

        # Create ToolNode with proper state handling
        def tool_node_with_state(state):
            # Execute tools and update state
            result = self.tools_node.invoke(state)
            print("\nTool node result:", result)

            # Update tool calls count in state
            return {
                **result,
                "tool_calls_count": state.get("tool_calls_count", 0) + 1
            }

        # Simple ToolNode initialization
        self.tools_node = ToolNode(tools)

        self.researcher_node = agents.ResearchAgent(tools=tools)
        self.summarization_node = agents.SummarizationAgent()
        self.recommender_node = agents.RecommendationAgent()

        # Build the graph
        graph_builder = StateGraph(agent_states.State)
        # graph_builder = StateGraph(agent_states.State,
        #                            input=agent_states.InputState,
        #                            output=agent_states.OutputState)

        # Add nodes to the graph
        # graph_builder.add_node("input_guardrails",
        #                        self.apply_input_guardrails)
        graph_builder.add_node("researcher", self.researcher_node)
        # Use wrapped tool node
        graph_builder.add_node("tools", tool_node_with_state)
        graph_builder.add_node("summarizer", self.summarization_node)
        graph_builder.add_node("recommender", self.recommender_node)

        # graph_builder.add_node("output_guardrails",
        #                        self.apply_output_guardrails)

        # Define transitions between nodes
        graph_builder.add_edge("tools", "researcher")
        graph_builder.add_edge("summarizer", "recommender")

        # graph_builder.add_conditional_edges("researcher", tools_condition)
        graph_builder.add_conditional_edges(
            "researcher", self.should_continue,
            {
                "continue": "summarizer",
                "tools": "tools"
            }
        )

        # Set entry and finish points
        # graph_builder.set_entry_point("input_guardrails")
        # graph_builder.set_finish_point("output_guardrails")
        graph_builder.set_entry_point("researcher")
        graph_builder.set_finish_point("recommender")

        # Compile the graph
        # memory = MemorySaver()
        self.agent = graph_builder.compile()  # checkpointer=memory)

    def should_continue(self, state: agent_states.State):
        messages = state["messages"]
        last_message = messages[-1]
        tool_calls_count = state.get("tool_calls_count", 0)

        # Check if we've reached the maximum number of tool calls
        if tool_calls_count >= self.MAX_TOOL_CALLS:
            print(f"\nReached maximum tool calls limit ({self.MAX_TOOL_CALLS}), continuing to summarizer")
            return "continue"

        # Check for tool_calls directly on the message
        if isinstance(last_message, AIMessage) and getattr(last_message,
                                                           'tool_calls', None):
            print("\nRouting to tools node")
            print(f"Tool calls: {last_message.tool_calls}")
            return "tools"

        print("\nNo tool calls found, continuing to summarizer")
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

    def run(self, query) -> list:
        initial_state = agent_states.State(
            stock=query,
            messages=[],
            summary=[],
            recommendation=[],
            tool_calls_count=0  # Initialize counter
        )
        response = self.agent.invoke(initial_state)
        return response["recommendation"][-1]
