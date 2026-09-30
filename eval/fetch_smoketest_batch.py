"""
eval/fetch_smoketest_batch.py

Throwaway script: pulls a small, recent, cross-agency batch of real
Federal Register documents (no agency/type filter, no cherry-picking)
to smoke-test retrieval_agent.py against genuinely unpredictable
phrasing -- not documents we chose because we expected a certain answer.

Saves to eval/smoketest_docs.json, separate from federal_register_docs.json,
so it never touches the real gold-set corpus.
"""

import requests
from datetime import date, timedelta

from ingestion.fetch_federal_register import extract_relevant_fields, deduplicate_documents, save_documents


def fetch_recent_all_agencies(days_back=14, per_page=20):
    url = "https://www.federalregister.gov/api/v1/documents.json"
    start_date = (date.today() - timedelta(days=days_back)).isoformat()

    params = {
        "conditions[publication_date][gte]": start_date,
        "order": "newest",
        "per_page": per_page,
    }

    response = requests.get(url, params=params)
    return response.json()


if __name__ == "__main__":
    data = fetch_recent_all_agencies()
    print(f"Total matches in range: {data['count']}")

    documents = extract_relevant_fields(data)
    documents = deduplicate_documents(documents)

    for doc in documents:
        print(doc["publication_date"], "-", doc["title"])

    save_documents(documents, filename="eval/smoketest_docs.json")
    print(f"\nSaved {len(documents)} documents to eval/smoketest_docs.json")