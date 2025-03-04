import httpx
import os
from enum import Enum

from langgraph.graph.message import add_messages

from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler

# Hyperscalers Retrievers
from langchain_aws.retrievers import AmazonKnowledgeBasesRetriever
from langchain_community.retrievers import AzureAISearchRetriever
from langchain.chains import RetrievalQA

import agent_states
import prompts

LLM_ENDPOINT = os.getenv("LLM_ENDPOINT")
TOKEN = os.getenv("API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME")

# Hyperscaler VectorDBs
class SupportedVectorDBProviders(Enum):
    AMAZON_KNOWLEDGE_BASE = "AmazonKnowledgeBase"
    AZURE_AI_SEARCH = "AzureAISearch"

# Mapping environment variable values to enum members
VECTORDB_PROVIDER_MAPPING = {
    "AWS": SupportedVectorDBProviders.AMAZON_KNOWLEDGE_BASE,
    "AZURE": SupportedVectorDBProviders.AZURE_AI_SEARCH
}

VECTORDB_PROVIDER = VECTORDB_PROVIDER_MAPPING.get(os.getenv("VECTORDB_PROVIDER", "AWS"))

# Azure
AZURE_AI_SEARCH_SERVICE_NAME = os.getenv("AZURE_AI_SEARCH_SERVICE_NAME")
AZURE_AI_SEARCH_API_KEY = os.getenv("AZURE_AI_SEARCH_API_KEY")
AZURE_AI_INDEX_NAME = os.getenv("AZURE_AI_INDEX_NAME")

# AWS
AWS_KNOWLEDGE_BASE_ID = os.getenv("AWS_KNOWLEDGE_BASE_ID")
AWS_REGION_NAME = os.getenv("AWS_REGION_NAME")


def get_retriever(vectordb_provider):
    if vectordb_provider == "AmazonKnowledgeBase":
        return AmazonKnowledgeBasesRetriever(
            knowledge_base_id=AWS_KNOWLEDGE_BASE_ID,
            region_name=AWS_REGION_NAME,
            retrieval_config={
                "vectorSearchConfiguration": {"numberOfResults": 4}},)
    elif vectordb_provider == "AzureAISearch":
        return AzureAISearchRetriever(
            content_key="content", top_k=1, index_name=AZURE_AI_INDEX_NAME)


class ResearchAgent:
    def __init__(self, tools=None):

        self.llm = ChatOpenAI(
            openai_api_key=TOKEN,
            openai_api_base=LLM_ENDPOINT,
            model_name=MODEL_NAME,
            top_p=0.92,
            temperature=0.01,
            max_tokens=2048,
            presence_penalty=1.03,
            streaming=True,
            callbacks=[StreamingStdOutCallbackHandler()],
            async_client=httpx.AsyncClient(verify=False),
            http_client=httpx.Client(verify=False))

        research_prompt = ChatPromptTemplate.from_messages([
            ("system", prompts.system_prompt),
            ("system", prompts.researcher_prompt),
            ])
        research_prompt = research_prompt.partial(
            tool_names=", ".join([tool.name for tool in tools]))

        if tools:
            self.agent = (
                {"stock": RunnablePassthrough(),
                 "messages": RunnablePassthrough(),
                }
                | research_prompt
                | self.llm.bind_tools(tools)
            )
        else:
            self.agent = (
                {"stock": RunnablePassthrough(),
                 "messages": RunnablePassthrough(),
                }
                | research_prompt
                | self.llm
            )

    def __call__(self, state: agent_states.State) -> agent_states.State:
        # Implement your custom logic here
        # Access the state and perform actions
        print("Running Researcher:")
        stock = {
            "stock": state["stock"],
            "messages": state.get("messages", "")
        }
        response = self.agent.invoke([stock])

        if isinstance(response, ToolMessage):
            result = response
        else:
            if isinstance(response, AIMessage):
                result = response
            else:
                # If response is a dict or has dict-like structure
                result = AIMessage(content=response.content if hasattr(response, 'content') else response)

        messages = state.get("messages", [])
        return {
                "messages": add_messages(messages, [result]),
                }


class SummarizationAgent:
    def __init__(self, tools=None):

        self.llm = ChatOpenAI(
            openai_api_key=TOKEN,
            openai_api_base=LLM_ENDPOINT,
            model_name=MODEL_NAME,
            top_p=0.92,
            temperature=0.01,
            max_tokens=2048,
            presence_penalty=1.03,
            streaming=True,
            callbacks=[StreamingStdOutCallbackHandler()],
            async_client=httpx.AsyncClient(verify=False),
            http_client=httpx.Client(verify=False))

        # Azure VectorDB Index
        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)

        self.retriever = get_retriever(VECTORDB_PROVIDER.value)

        self.summary_prompt = ChatPromptTemplate.from_messages([
            ("system", prompts.system_prompt),
            ("user", prompts.summary_prompt),
            ])

        self.agent = (
            {"context": self.retriever | format_docs,
             "messages": RunnablePassthrough(),
             "stock": RunnablePassthrough(),
             }
             | self.summary_prompt
             | self.llm
            )


    def __call__(self, state: agent_states.State) -> agent_states.State:
        print("Running Summarizer:")
        message = {
            "stock": state["stock"],
            "messages": state.get("messages", []),
        }
        if VECTORDB_PROVIDER.value == "AmazonKnowledgeBase":
            response = self.agent.invoke(str(message))
        elif VECTORDB_PROVIDER.value == "AzureAISearch":
            response = self.agent.invoke([message])
        summaries = state.get("summary", [])
        return {
                "summary": add_messages(summaries, [response]),
                }


class RecommendationAgent:
    def __init__(self, tools=None):

        self.llm = ChatOpenAI(
            openai_api_key=TOKEN,
            openai_api_base=LLM_ENDPOINT,
            model_name=MODEL_NAME,
            top_p=0.92,
            temperature=0.01,
            max_tokens=2048,
            presence_penalty=1.03,
            streaming=True,
            callbacks=[StreamingStdOutCallbackHandler()],
            async_client=httpx.AsyncClient(verify=False),
            http_client=httpx.Client(verify=False))

        recommendation_prompt = ChatPromptTemplate.from_messages([
            ("system", prompts.system_prompt),
            ("user", prompts.recommender_prompt)])

        self.agent = (
            {"summary": RunnablePassthrough(),
             "messages": RunnablePassthrough(),
             "stock": RunnablePassthrough(),
            }
            | recommendation_prompt
            | self.llm
        )

    def __call__(self, state: agent_states.State) -> agent_states.State:
        print("Running Recommender:")
        message = {
            "stock": state["stock"],
            "summary": state.get("summary", []),
            "messages": state.get("messages", []),
        }
        response = self.agent.invoke([message])
        recommendations = state.get("recommendation", [])
        return {
                "recommendation": add_messages(recommendations, [response]),
                }
