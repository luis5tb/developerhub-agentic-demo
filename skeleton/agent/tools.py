from typing import Annotated

from langchain_core.tools import tool

from langchain_community.tools import DuckDuckGoSearchRun
from langchain_experimental.utilities import PythonREPL


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


duckduckgo_search = DuckDuckGoSearchRun()


def get_tools():
    # return [python_repl, duckduckgo_search]
    return [duckduckgo_search]
