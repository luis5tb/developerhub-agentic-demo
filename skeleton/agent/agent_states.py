from typing import Annotated
from typing_extensions import TypedDict

from langgraph.graph.message import add_messages


class State(TypedDict):
    # messages have the type "list".
    # The add_messages function appends messages to the list,
    # rather than overwriting them
    stock: str
    messages: Annotated[list, add_messages]
    summary: Annotated[list, add_messages]
    # feedback: Annotated[list, add_messages]
    recommendation: Annotated[list, add_messages]

# class InputState(TypedDict):
#     stock: str

# class OutputState(TypedDict):
#     recomendation: str
