import json
import sys
import time

GOLD_FILE = "eval/gold_set.json"
GOLD_DIFF_FILE = "eval/gold_set_diff.json"
DOCS_FILE = "federal_register_docs.json"
DOMAINS_FILE = "federal_register_domains.json"
RETRIEVAL_FILE = "graph_results.json"
VERDICTS = ("covered", "uncovered", "not_applicable")


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
    """Read the 3-way verdict straight from the last saved run. 0 Gemini calls."""
    with open(filename, "r") as f:
        results_by_id = {d["document_number"]: d for d in json.load(f)}

    check_no_missing(gold, results_by_id, filename)

    no_verdict = [e["document_number"] for e in gold if "verdict" not in results_by_id[e["document_number"]]]
    if no_verdict:
        print(f"\nERROR: {len(no_verdict)} gold docs in {filename} were judged before the 3-way judge existed:")
        for doc_id in no_verdict:
            print(f"  - {doc_id}")
        print("Re-run them through the graph first. Refusing to score old verdicts.")
        sys.exit(1)

    return {
        entry["document_number"]: results_by_id[entry["document_number"]]["verdict"]
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
        predictions[doc_id] = doc["verdict"]
        print(f"  {doc_id}: {doc['verdict']}")
        time.sleep(13)
    return predictions


def score(gold, predictions):
    """Compare 3-way verdicts against the gold labels and print a confusion matrix."""
    confusion = {(expected, actual): 0 for expected in VERDICTS for actual in VERDICTS}
    mismatches = []

    for entry in gold:
        expected = entry["expected_verdict"]
        actual = predictions[entry["document_number"]]
        confusion[(expected, actual)] += 1
        if expected != actual:
            mismatches.append((entry["title"], f"expected {expected}, got {actual}"))

    total = len(gold)
    correct = sum(confusion[(v, v)] for v in VERDICTS)
    print(f"\n{correct}/{total} verdicts correct ({correct / total:.2%})")

    print("\nConfusion matrix (rows = expected, columns = predicted):")
    print(" " * 16 + "".join(f"{v:>16}" for v in VERDICTS))
    for expected in VERDICTS:
        print(f"{expected:<16}" + "".join(f"{confusion[(expected, actual)]:>16}" for actual in VERDICTS))

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