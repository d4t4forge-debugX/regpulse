import json
import sys
import time

GOLD_FILE = "eval/gold_set.json"
GOLD_DIFF_FILE = "eval/gold_set_diff.json"
DOCS_FILE = "federal_register_docs.json"
DOMAINS_FILE = "federal_register_domains.json"
RETRIEVAL_FILE = "federal_register_retrieval.json"


def load_gold(filename=GOLD_FILE):
    with open(filename, "r") as f:
        return json.load(f)


def check_no_missing(gold, available_ids, source_file):
    """Exit with an error if any gold doc is absent from source_file."""
    missing = [e for e in gold if e["document_number"] not in available_ids]
    if missing:
        print(f"\nERROR: {len(missing)} of {len(gold)} gold docs are missing from {source_file}:")
        for entry in missing:
            print(f"  - {entry['document_number']}: {entry['title']}")
        print("Refusing to score a partial set.")
        sys.exit(1)


def get_predictions_from_existing_file(gold, filename=RETRIEVAL_FILE):
    """Read has_relevant_match straight from the last saved run. 0 Gemini calls."""
    with open(filename, "r") as f:
        results_by_id = {d["document_number"]: d for d in json.load(f)}

    check_no_missing(gold, results_by_id, filename)

    return {
        entry["document_number"]: results_by_id[entry["document_number"]]["has_relevant_match"]
        for entry in gold
    }


def get_predictions_fresh(gold):
    """Actually re-run judge_document on each gold doc. Costs 1 Gemini call per doc."""
    with open(DOMAINS_FILE, "r") as f:
        domains_by_id = {d["document_number"]: d for d in json.load(f)}

    # Check before loading models or making any Gemini call.
    check_no_missing(gold, domains_by_id, DOMAINS_FILE)

    from sentence_transformers import SentenceTransformer
    from pipeline.retrieval_agent import judge_document
    from vectorstore.chroma_store import get_collection

    collection = get_collection()
    model = SentenceTransformer("all-MiniLM-L6-v2")

    predictions = {}
    for entry in gold:
        doc_id = entry["document_number"]
        doc = judge_document(dict(domains_by_id[doc_id]), collection, model)
        predictions[doc_id] = doc["has_relevant_match"]
        print(f"  {doc_id}: {doc['has_relevant_match']}")
        time.sleep(13)
    return predictions


def score(gold, predictions):
    tp = fp = tn = fn = 0
    mismatches = []

    for entry in gold:
        doc_id = entry["document_number"]
        expected = entry["expected_relevant"]
        actual = predictions[doc_id]

        if expected and actual:
            tp += 1
        elif not expected and not actual:
            tn += 1
        elif not expected and actual:
            fp += 1
            mismatches.append((entry["title"], "expected not-relevant, got relevant"))
        elif expected and not actual:
            fn += 1
            mismatches.append((entry["title"], "expected relevant, got not-relevant"))

    total = tp + tn + fp + fn
    accuracy = (tp + tn) / total if total else 0
    precision = tp / (tp + fp) if (tp + fp) else float("nan")
    recall = tp / (tp + fn) if (tp + fn) else float("nan")

    print(f"\n{total} examples scored ({tp} TP, {tn} TN, {fp} FP, {fn} FN)")
    print(f"Accuracy:  {accuracy:.2f}")
    print(f"Precision: {precision:.2f}")
    print(f"Recall:    {recall:.2f}")

    if mismatches:
        print("\nMismatches:")
        for title, reason in mismatches:
            print(f"  - {title}: {reason}")
    else:
        print("\nNo mismatches.")


def diff_eval():
    """Check classify_document against the diff-step gold set. 0 cost, always fresh.
    Exits with an error if any gold doc is missing from the docs file."""
    from pipeline.diff_agent import classify_document

    with open(GOLD_DIFF_FILE, "r") as f:
        gold = json.load(f)
    with open(DOCS_FILE, "r") as f:
        docs_by_id = {d["document_number"]: d for d in json.load(f)}

    check_no_missing(gold, docs_by_id, DOCS_FILE)

    correct = 0
    mismatches = []

    for entry in gold:
        doc = docs_by_id[entry["document_number"]]
        actual = classify_document(doc["title"], doc.get("abstract"))
        expected = entry["expected_category"]

        if actual == expected:
            correct += 1
        else:
            mismatches.append((entry["title"], f"expected {expected}, got {actual}"))

    total = len(gold)
    print(f"\n{correct}/{total} correct ({correct / total:.2%})")
    if mismatches:
        print("\nMismatches:")
        for title, reason in mismatches:
            print(f"  - {title}: {reason}")
    else:
        print("\nNo mismatches.")


if __name__ == "__main__":
    if "--diff" in sys.argv:
        print(f"Checking classify_document against {GOLD_DIFF_FILE} (0 Gemini calls)...")
        diff_eval()
    else:
        gold = load_gold()
        if "--rerun" in sys.argv:
            print(f"Re-running judge_document on {len(gold)} gold examples ({len(gold)} Gemini calls)...\n")
            predictions = get_predictions_fresh(gold)
        else:
            print(f"Scoring against existing {RETRIEVAL_FILE} (0 Gemini calls)...\n")
            predictions = get_predictions_from_existing_file(gold)
        score(gold, predictions)