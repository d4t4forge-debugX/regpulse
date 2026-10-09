import json
import os

ADMINISTRATIVE_PHRASES = [
    "Technical Amendment",
    "Delegation of Authority",
    "Delegations of Authority",
    "Delegated Authority",
    "List of Rules To Be Reviewed",
    "Extension of Compliance Date",
    "Correction",
    "EDGAR Filer Manual",
]

def load_documents(filename="federal_register_docs.json"):
    with open(filename, "r") as f:
        return json.load(f)

def classify_document(title, abstract):
    abstract = abstract or ""
    combined_text = (title + " " + abstract).lower()
    for phrase in ADMINISTRATIVE_PHRASES:
        if phrase.lower() in combined_text:
            return "administrative"
    return "substantive"

def save_classified_documents(documents, filename="federal_register_classified.json"):
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
    documents = load_documents()
    for doc in documents:
        doc["category"] = classify_document(doc["title"], doc["abstract"])
        print(f"[{doc['category']}] {doc['publication_date']} - {doc['title']}")
    save_classified_documents(documents)
    print("Saved to federal_register_classified.json")