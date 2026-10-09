import requests
import json
import os
from config import FEDERAL_REGISTER_AGENCIES

def save_documents(documents, filename="federal_register_docs.json"):
    """Merge newly fetched documents into the existing file, keyed by document_number,
    instead of overwriting it. A document already on file is kept even if a later,
    narrower fetch (different date range, different query) doesn't return it again."""
    existing = {}
    if os.path.exists(filename):
        with open(filename, "r") as f:
            existing = {d["document_number"]: d for d in json.load(f)}

    before = len(existing)
    for doc in documents:
        existing[doc["document_number"]] = doc

    merged = list(existing.values())
    with open(filename, "w") as f:
        json.dump(merged, f, indent=2)

    new_count = len(existing) - before
    print(f"Merged: {new_count} new document(s), {len(merged)} total now in {filename}")

def extract_relevant_fields(api_response):
    documents = []
    for result in api_response["results"]:
        documents.append({
            "title": result["title"],
            "abstract": result["abstract"],
            "publication_date": result["publication_date"],
            "document_number": result["document_number"],
            "html_url": result["html_url"],
        })
    return documents

def deduplicate_documents(documents):
    deduped = {doc["document_number"]: doc for doc in documents}
    return list(deduped.values())

def fetch_recent_sec_rules(per_page=100, days_back=365):
    from datetime import date, timedelta

    url = "https://www.federalregister.gov/api/v1/documents.json"
    start_date = (date.today() - timedelta(days=days_back)).isoformat()

    params = {
           "conditions[agencies][]": FEDERAL_REGISTER_AGENCIES,
        "conditions[type][]": "RULE",
        "conditions[publication_date][gte]": start_date,
        "order": "newest",
        "per_page": per_page,
    }

    all_results = []
    response = requests.get(url, params=params)
    data = response.json()
    total_count = data["count"]
    all_results.extend(data["results"])

    next_page_url = data.get("next_page_url")
    while next_page_url:
        if len(all_results) >= 2000:
            print("Warning: hit the Federal Register API's 2000-result pagination cap. "
                  "Returning partial results — narrow the date range to get the rest.")
            break
        response = requests.get(next_page_url)
        data = response.json()
        all_results.extend(data["results"])
        next_page_url = data.get("next_page_url")

    return {"count": total_count, "results": all_results}

if __name__ == "__main__":
    data = fetch_recent_sec_rules(days_back=365)
    print(f"Total matches: {data['count']}")
    documents = extract_relevant_fields(data)
    documents = deduplicate_documents(documents)
    for doc in documents:
        print(doc["publication_date"], "-", doc["title"])
    save_documents(documents)