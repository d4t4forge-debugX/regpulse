import json
import os
from transformers import pipeline
from config import DOMAIN_LABELS


def load_substantive_documents(filename="federal_register_classified.json"):
    with open(filename, "r") as f:
        documents = json.load(f)
    return [doc for doc in documents if doc["category"] == "substantive"]

def classify_domain(classifier, text):
    result = classifier(text, DOMAIN_LABELS)
    top_label = result["labels"][0]
    top_score = result["scores"][0]
    runner_up_score = result["scores"][1]
    gap = top_score - runner_up_score
    return top_label, top_score, gap

def save_domain_classified(documents, filename="federal_register_domains.json"):
    """Merge into the existing file, keyed by document_number, instead of overwriting it."""
    existing = {}
    if os.path.exists(filename):
        with open(filename, "r") as f:
            existing = {d["document_number"]: d for d in json.load(f)}

    for doc in documents:
        existing[doc["document_number"]] = doc

    with open(filename, "w") as f:
        json.dump(list(existing.values()), f, indent=2)

    print(f"{len(existing)} total documents now in {filename}")

if __name__ == "__main__":
    classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
    documents = load_substantive_documents()

    for doc in documents:
        combined_text = doc["title"] + " " + (doc["abstract"] or "")
        label, score, gap = classify_domain(classifier, combined_text)
        doc["domain"] = label
        doc["domain_score"] = round(score, 2)
        doc["domain_confidence_gap"] = round(gap, 2)
        print(f"{doc['publication_date']} - {doc['title']}")
        print(f"    → {label} (score={score:.2f}, gap={gap:.2f})")

    save_domain_classified(documents)
    print("Saved to federal_register_domains.json")