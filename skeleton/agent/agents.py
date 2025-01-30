from langgraph.graph.message import add_messages

# from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
# from langchain_community.llms import VLLMOpenAI
from langchain_openai import ChatOpenAI
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler

# from langchain.chains import ConversationChain
# from langchain.memory import ConversationBufferMemory
# from langchain.chains import LLMChain
# from langchain.prompts import PromptTemplate
# from langchain_core.messages import BaseMessage

import prompts
import agent_states


class ResearchAgent:
    def __init__(self, llm_endpoint, llm_token, model_name, tools=None):

        self.llm = ChatOpenAI(
            openai_api_key=llm_token,
            openai_api_base=llm_endpoint,
            model_name=model_name,
            top_p=0.92,
            temperature=0.01,
            max_tokens=2048,
            presence_penalty=1.03,
            streaming=True,
            callbacks=[StreamingStdOutCallbackHandler()])

        research_prompt = ChatPromptTemplate.from_messages([
            ("system", prompts.researcher_prompt),
            ])
        research_prompt = research_prompt.partial(
            tool_names=", ".join([tool.name for tool in tools]))

        if tools:
            self.agent = research_prompt | self.llm.bind_tools(tools)
        else:
            self.agent = research_prompt | self.llm

    def __call__(self, state: agent_states.State) -> agent_states.State:
        # Implement your custom logic here
        # Access the state and perform actions
        message = {
            "stock": state["stock"],
            "feedback": state.get("feedback", ""),
            "messages": state.get("messages", []),
        }
        response = self.agent.invoke(message)
        print("********")
        print(response)
        print("********")
        print(response.tool_calls)
        print("********")

        messages = state.get("messages", [])
        return {
                "messages": add_messages(messages, [response]),
                }


class SummarizationAgent:
    def __init__(self, llm_endpoint, llm_token, model_name):

        self.llm = ChatOpenAI(
            openai_api_key=llm_token,
            openai_api_base=llm_endpoint,
            model_name=model_name,
            top_p=0.92,
            temperature=0.01,
            max_tokens=2048,
            presence_penalty=1.03,
            streaming=True,
            callbacks=[StreamingStdOutCallbackHandler()])

        summary_prompt = ChatPromptTemplate.from_messages([
            ("system", prompts.system_prompt),
            ("user", prompts.summary_prompt)])

        self.agent = summary_prompt | self.llm

    def __call__(self, state: agent_states.State) -> agent_states.State:
        message = {
            "stock": state["stock"],
            "context": "",
            "messages": state.get("messages", []),
        }
        response = self.agent.invoke(message)
        summaries = state.get("summary", [])
        return {
                "summary": add_messages(summaries, [response]),
                }


class RecommendationAgent:
    def __init__(self, llm_endpoint, llm_token, model_name):

        self.llm = ChatOpenAI(
            openai_api_key=llm_token,
            openai_api_base=llm_endpoint,
            model_name=model_name,
            top_p=0.92,
            temperature=0.01,
            max_tokens=2048,
            presence_penalty=1.03,
            streaming=True,
            callbacks=[StreamingStdOutCallbackHandler()])

        recommendation_prompt = ChatPromptTemplate.from_messages([
            ("system", prompts.system_prompt),
            ("user", prompts.recommender_prompt)])

        self.agent = recommendation_prompt | self.llm

    def __call__(self, state: agent_states.State) -> agent_states.State:
        message = {
            "stock": state["stock"],
            "summary": state.get("summary", []),
            "messages": state.get("messages", []),
        }
        response = self.agent.invoke(message)
        recommendations = state.get("recommendation", [])
        return {
                "recommendation": add_messages(recommendations, [response]),
                }
