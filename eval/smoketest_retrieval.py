"""
eval/smoketest_retrieval.py

Throwaway script: runs the retrieval judge against the unlabeled
smoketest batch, for manual spot-checking.

Currently pointed at gemini-3.5-flash-lite (not the real production
model) because gemini-3.5-flash has been persistently 503ing for two
days straight. Lite's verdicts are directional signal only -- Lite is
known to be less reliable (missed the BIS hard case in the gold-set
eval) -- and are never written into federal_register_domains.json or
federal_register_retrieval.json, so they can never leak into the real
eval numbers.
"""

import json
from sentence_transformers import SentenceTransformer

from vectorstore.chroma_store import get_collection
from pipeline.retrieval_agent import retrieve_for_regulation, judge_relevance_llm


def load_smoketest_docs(filename="eval/smoketest_docs.json"):
    with open(filename, "r") as f:
        return json.load(f)


if __name__ == "__main__":
    collection = get_collection()
    model = SentenceTransformer("all-MiniLM-L6-v2")
    documents = load_smoketest_docs()

    for doc in documents:
        matches = retrieve_for_regulation(collection, model, doc)
        verdict = judge_relevance_llm(doc, matches, model="gemini-3.5-flash-lite")
        best_distance = round(min(distance for text, distance in matches), 3)

        print(f"\n[FLASH-LITE — directional only, not authoritative] {doc['publication_date']} - {doc['title']}")
        print(f"  Relevant match found: {verdict['is_relevant']} (best distance={best_distance})")
        print(f"  Reasoning: {verdict['reasoning']}")