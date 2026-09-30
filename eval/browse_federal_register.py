"""
eval/browse_federal_register.py

Throwaway script to browse the Federal Register API by keyword.
Used to find real candidate regulations (with real document numbers)
for the eval gold set. Does not touch the pipeline or any data files.
"""

import sys
import requests


def search_federal_register(keyword, per_page=10):
    url = "https://www.federalregister.gov/api/v1/documents.json"
    params = {
        "conditions[term]": keyword,
        "per_page": per_page,
        "order": "relevance",
        "fields[]": ["title", "document_number", "publication_date", "abstract", "html_url", "type"],
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()["results"]


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('Usage: python -m eval.browse_federal_register "<keyword>"')
        sys.exit(1)

    keyword = sys.argv[1]
    results = search_federal_register(keyword)

    print(f"\nFound {len(results)} results for '{keyword}':\n")
    for doc in results:
        print(f"Document number: {doc.get('document_number')}")
        print(f"Date: {doc.get('publication_date')}")
        print(f"Type: {doc.get('type')}")
        print(f"Title: {doc.get('title')}")
        abstract = doc.get("abstract") or "(no abstract)"
        print(f"Abstract: {abstract[:300]}")
        print(f"URL: {doc.get('html_url')}")
        print("-" * 80)