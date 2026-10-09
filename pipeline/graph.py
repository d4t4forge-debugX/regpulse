from typing import Optional, TypedDict

from langgraph.graph import StateGraph, START, END
from sentence_transformers import SentenceTransformer
from transformers import pipeline

from pipeline.classify_agent import classify_domain
from pipeline.diff_agent import classify_document
from pipeline.impact_agent import (
    build_coverage_gap_shell,
    build_outdated_shell,
    generate_coverage_gap_memo_text,
    generate_outdated_memo_text,
    select_memo_type,
)
from pipeline.retrieval_agent import judge_document
from vectorstore.chroma_store import get_collection


class RegulationState(TypedDict, total=False):
    """One regulation as it moves through the graph. Each node adds its own fields."""
    # Fields that come from the Federal Register ingestion
    title: str
    abstract: Optional[str]
    publication_date: str
    document_number: str
    html_url: str
    # Added by the diff node
    category: str
    # Added by the classify node
    domain: str
    domain_score: float
    domain_confidence_gap: float
    # Added by the judge node
    verdict: str
    has_relevant_match: bool
    relevant_chunk_number: Optional[int]
    judge_reasoning: str
    best_distance: float
    relevant_chunk_text: str
    # Added by whichever memo node runs
    memo: dict


JUDGE_FIELDS = [
    "verdict",
    "has_relevant_match",
    "relevant_chunk_number",
    "judge_reasoning",
    "best_distance",
    "relevant_chunk_text",
]


def build_graph(classifier, model, collection):
    """Build and compile the RegPulse graph, reusing models that are already loaded."""

    def diff_node(state):
        return {"category": classify_document(state["title"], state.get("abstract"))}

    def classify_node(state):
        text = state["title"] + " " + (state.get("abstract") or "")
        label, score, gap = classify_domain(classifier, text)
        return {
            "domain": label,
            "domain_score": round(score, 2),
            "domain_confidence_gap": round(gap, 2),
        }

    def judge_node(state):
        doc = dict(state)  # copy, because judge_document writes its verdict onto the dict it gets
        judge_document(doc, collection, model)
        return {key: doc[key] for key in JUDGE_FIELDS if key in doc}

    def outdated_memo_node(state):
        shell = build_outdated_shell(dict(state))
        shell["memo_text"] = generate_outdated_memo_text(shell)
        return {"memo": shell}

    def coverage_gap_memo_node(state):
        shell = build_coverage_gap_shell(dict(state))
        shell["memo_text"] = generate_coverage_gap_memo_text(shell)
        return {"memo": shell}

    graph = StateGraph(RegulationState)
    graph.add_node("diff", diff_node)
    graph.add_node("classify", classify_node)
    graph.add_node("judge", judge_node)
    graph.add_node("outdated_memo", outdated_memo_node)
    graph.add_node("coverage_gap_memo", coverage_gap_memo_node)

    graph.add_edge(START, "diff")
    # The diff node stored "administrative" or "substantive" in state["category"]; that string picks the route
    graph.add_conditional_edges(
        "diff",
        lambda state: state["category"],
        {"substantive": "classify", "administrative": END},
    )
    graph.add_edge("classify", "judge")
    # select_memo_type (from impact_agent.py) returns "outdated", "coverage_gap", or "none"
    graph.add_conditional_edges(
        "judge",
        select_memo_type,
        {"outdated": "outdated_memo", "coverage_gap": "coverage_gap_memo", "none": END},
    )
    graph.add_edge("outdated_memo", END)
    graph.add_edge("coverage_gap_memo", END)

    return graph.compile()


if __name__ == "__main__":
    import json

    classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
    model = SentenceTransformer("all-MiniLM-L6-v2")
    collection = get_collection()
    app = build_graph(classifier, model, collection)

    with open("federal_register_docs.json", "r") as f:
        docs = json.load(f)

    by_id = {d["document_number"]: d for d in docs}
    administrative_doc = next(
        d for d in docs if classify_document(d["title"], d.get("abstract")) == "administrative"
    )
    test_docs = [
        administrative_doc,        # should stop right after the diff node
        by_id["2025-05904"],       # COPPA: known positive, should end with an outdated memo
        by_id["2026-19334"],  # POW/MIA proclamation: not_applicable, should end with no memo
    ]

    for doc in test_docs:
        result = app.invoke(doc)
        print(f"\n=== {result['title']}")
        print(f"  category: {result['category']}")
        print(f"  domain: {result.get('domain')}")
        print(f"  has_relevant_match: {result.get('has_relevant_match')}")
        memo = result.get("memo")
        print(f"  memo type: {memo['memo_type'] if memo else None}")
        if memo:
            print(f"  memo text: {memo['memo_text']}")