import sys

import requests

from ingestion.fetch_federal_register import save_documents

API_URL = "https://www.federalregister.gov/api/v1/documents/{}.json"


def fetch_one(document_number):
    """Fetch a single document's official metadata from the Federal Register API."""
    response = requests.get(API_URL.format(document_number), timeout=30)
    response.raise_for_status()
    result = response.json()
    return {
        "title": result["title"],
        "abstract": result["abstract"],
        "publication_date": result["publication_date"],
        "document_number": result["document_number"],
        "html_url": result["html_url"],
    }


if __name__ == "__main__":
    document_numbers = sys.argv[1:]
    documents = [fetch_one(number) for number in document_numbers]

    for doc in documents:
        print(f"{doc['document_number']} - {doc['title']}")
        print(f"  abstract: {doc['abstract']}\n")

    save_documents(documents)