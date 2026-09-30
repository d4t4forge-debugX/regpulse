from typing import TypedDict

from langgraph.graph import StateGraph, START, END

from pipeline.diff_agent import classify_document


class RegState(TypedDict, total=False):
    title: str
    abstract: str
    category: str
    note: str


def diff_node(state):
    category = classify_document(state["title"], state.get("abstract"))
    return {"category": category}


def continue_node(state):
    return {"note": "substantive: classify, retrieve and impact would run next"}


def stop_node(state):
    return {"note": "administrative: pipeline stops here"}


def route_after_diff(state):
    if state["category"] == "substantive":
        return "continue"
    return "stop"


builder = StateGraph(RegState)
builder.add_node("diff", diff_node)
builder.add_node("continue_pipeline", continue_node)
builder.add_node("stop", stop_node)

builder.add_edge(START, "diff")
builder.add_conditional_edges(
    "diff",
    route_after_diff,
    {"continue": "continue_pipeline", "stop": "stop"},
)
builder.add_edge("continue_pipeline", END)
builder.add_edge("stop", END)

graph = builder.compile()

examples = [
    {"title": "Technical Amendment to Rules of Practice", "abstract": "Corrects typographical errors."},
    {"title": "Children's Online Privacy Protection Rule", "abstract": "Updates rules on collecting data from children."},
]

for example in examples:
    result = graph.invoke(example)
    print(result)