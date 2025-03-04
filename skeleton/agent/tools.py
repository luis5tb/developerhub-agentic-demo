import os
from typing import Annotated

from langchain_core.tools import tool
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_experimental.utilities import PythonREPL
from tavily import TavilyClient

# Get Tavily API key from environment variable
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

@tool
def tavily_search(query: str) -> str:
    """Use Tavily Search to get information from the internet."""
    client = TavilyClient(api_key=TAVILY_API_KEY)
    search_result = client.search(query=query)
    return str(search_result)

@tool
def python_repl(code: Annotated[
        str, "The python code to execute to generate your calculations."],):
    """Use this to execute python code.
    Execute the code if it's necessary, but give the final result calculated.
    Don't show the code
    If it's needed, search first online
    Your result if calculate is not to give the code, is to provide the
    final result
    """
    try:
        result = PythonREPL().run(code)
    except BaseException as e:
        return f"Failed to execute. Error: {repr(e)}"
    result_str = f"Successfully executed:\n\`\`\`python\n{code}\n\`\`\`\nStdout: {result}"
    return (
        result_str + "\n\nIf you have completed all tasks, respond with FINAL ANSWER."
    )

# Initialize search tools
duckduckgo_search = DuckDuckGoSearchRun()

def get_tools(search_provider="duckduckgo"):
    """Get the tools based on the specified search provider."""
    if search_provider.lower() == "tavily":
        if not TAVILY_API_KEY:
            raise ValueError("Tavily API key not found in environment variables")
        return [tavily_search]
    else:  # default to duckduckgo
        return [duckduckgo_search]
