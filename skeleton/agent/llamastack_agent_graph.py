import uuid

from langgraph.graph import StateGraph
# from langgraph.graph import StateGraph, END
# from langgraph.graph.message import add_messages
# from langgraph.checkpoint.memory import MemorySaver
# from langgraph.prebuilt import ToolNode, tools_condition
# from langgraph.prebuilt import ToolNode

# from vector_db import VectorDB
# from guardrails import apply_guardrails

from llama_stack_client import LlamaStackClient

# from tools import get_tools
import llamastack_agents
import agent_states


VECTOR_DB_ID = f"vector-db-{uuid.uuid4().hex}"

TOOLS = {
    "builtin::websearch": {
        "provider_id": "tavily-search-0",
        "args": {"max_results": 5}},
    "builtin::rag": {
        "provider_id": "rag-runtime-2",
        "args": {"vector_db_ids": [VECTOR_DB_ID]},
    },
    "builtin::code_interpreter": {
        "provider_id": "code-interpreter-1"},
}

VECTORDB = {"provider_id": "chromadb-1"}


class LLamaStackAgentGraph:
    def __init__(self, llamastack_endpoint, model):
        """
        Initialize the agent graph with vLLM and other components.

        Args:
            llm_endpoint (str): URL of the deployed vLLM endpoint.
            llm_token (str): Authorization token for the vLLM endpoint.
        """
        # self.vector_db = VectorDB()

        self.initialize_components(llamastack_endpoint, model)

        research_tools = ["builtin::websearch", "buildin::code_interpreter"]
        self.researcher_node = llamastack_agents.ResearchAgent(
            llamastack_server_endpoint=llamastack_endpoint,
            model_name=model,
            tools=research_tools)

        summarization_tools = [{
            "name": "builtin::rag",
            "args": TOOLS["builtin::rag"]["args"],
        }]
        self.summarization_node = llamastack_agents.SummarizationAgent(
            llamastack_server_endpoint=llamastack_endpoint,
            model_name=model,
            tools=summarization_tools)

        recommender_tools = []
        self.recommender_node = llamastack_agents.RecommendationAgent(
            llamastack_server_endpoint=llamastack_endpoint,
            model_name=model,
            tools=recommender_tools)

        # Build the graph
        graph_builder = StateGraph(agent_states.State)

        graph_builder.add_node("researcher", self.researcher_node)
        graph_builder.add_node("summarizer", self.summarization_node)
        graph_builder.add_node("recommender", self.recommender_node)

        graph_builder.add_edge("researcher", "summarizer")
        graph_builder.add_edge("summarizer", "recommender")

        graph_builder.set_entry_point("researcher")
        graph_builder.set_finish_point("recommender")

        # Compile the graph
        # memory = MemorySaver()
        self.agent = graph_builder.compile()  # checkpointer=memory)

    def initialize_components(self, llamastack_endpoint, model):
        client = LlamaStackClient(base_url=llamastack_endpoint)

        # Register Model
        client.models.register(model_id=model,
                               provider_id="vllm",
                               model_type="llm")

        # Register Tools
        for toolgroup_id, tool_args in TOOLS.items():
            args = tool_args.get("args")
            if args:
                client.toolgroups.register(
                    toolgroup_id=toolgroup_id,
                    provider_id=tool_args.get("provider_id"),
                    args=args)
            else:
                client.toolgroups.register(
                    toolgroup_id=toolgroup_id,
                    provider_id=tool_args.get("provider_id"))

        # Register VectorDB
        # It requires embedding_model
        embeddings_model = "all-MiniLM-L6-v2"
        client.models.register(model_id=embeddings_model,
                               provider_id="sentence-transformers",
                               model_type="embedding",
                               metadata={"embedding_dimension": 384})

        client.vector_dbs.register(provider_id=VECTORDB["provider_id"],
                                   vector_db_id=VECTOR_DB_ID,
                                   embedding_model="all-MiniLM-L6-v2",
                                   embedding_dimension=384)

        # TODO: Populate vectordb

        # TODO: Register Shields

    def run(self, query) -> list:
        # config = {"configurable": {"thread_id": "1"}}
        initial_state = agent_states.State(stock=query,
                                           messages=[],
                                           summary=[],
                                           recommendation=[])
        response = self.agent.invoke(initial_state)  # , config)
        return response["recommendation"][-1]
