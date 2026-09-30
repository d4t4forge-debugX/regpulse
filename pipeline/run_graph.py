import json
import os
import sys
import time

from sentence_transformers import SentenceTransformer
from transformers import pipeline

from pipeline.graph import build_graph
from vectorstore.chroma_store import get_collection

INPUT_FILE = "federal_register_docs.json"
OUTPUT_FILE = "graph_results.json"


def load_results(output_file):
    """Load results saved by a previous run, keyed by document_number."""
    if os.path.exists(output_file):
        with open(output_file, "r") as f:
            return {r["document_number"]: r for r in json.load(f)}
    return {}


def save_results(results_by_id, output_file):
    with open(output_file, "w") as f:
        json.dump(list(results_by_id.values()), f, indent=2)


if __name__ == "__main__":
    force_rerun = "--all" in sys.argv

    # Load the slow models once, then reuse them for every regulation
    classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
    model = SentenceTransformer("all-MiniLM-L6-v2")
    collection = get_collection()
    app = build_graph(classifier, model, collection)

    with open(INPUT_FILE, "r") as f:
        documents = json.load(f)

    results_by_id = load_results(OUTPUT_FILE)

    for doc in documents:
        doc_id = doc["document_number"]

        if doc_id in results_by_id and not force_rerun:
            print(f"Skipping (already done): {doc['title']}")
            continue

        result = app.invoke(doc)

        memo = result.get("memo")
        memo_type = memo["memo_type"] if memo else "none"
        print(f"\n{result['publication_date']} - {result['title']}")
        print(f"  category={result['category']}  memo={memo_type}")

        # Save after every document so a crash never loses finished work
        results_by_id[doc_id] = result
        save_results(results_by_id, OUTPUT_FILE)

        # Only substantive docs call Gemini, so only they need the rate-limit pause
        if result["category"] == "substantive":
            time.sleep(13)

    print(f"\nDone. {len(results_by_id)} results in {OUTPUT_FILE}")