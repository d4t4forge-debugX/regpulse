import json
import re

import pymupdf

from vectorstore.colpali_store import load_colqwen2_model, embed_query, rank_pages


def normalize(text):
    # Make PDF text and chunk text comparable: straight quotes, lowercase, single spaces
    text = text.replace("\u2019", "'").replace("\u2018", "'")
    text = text.replace("\u201c", '"').replace("\u201d", '"')
    text = text.lower()
    return re.sub(r"\s+", " ", text)


with open("federal_register_retrieval.json") as f:
    documents = json.load(f)

positives = [d for d in documents if d["has_relevant_match"] and d.get("relevant_chunk_text")]

pdf = pymupdf.open("apple_10k.pdf")
page_texts = [normalize(page.get_text()) for page in pdf]

colpali_model, colpali_processor = load_colqwen2_model()

for doc in positives:
    chunk = normalize(doc["relevant_chunk_text"])
    middle = len(chunk) // 2
    snippet = chunk[middle - 30 : middle + 30]

    chunk_pages = [i + 1 for i, text in enumerate(page_texts) if snippet in text]

    query_text = doc["title"] + " " + (doc.get("abstract") or "")
    query_embedding = embed_query(query_text, colpali_model, colpali_processor)
    ranked = rank_pages(query_embedding, "vectorstore/colpali_embeddings", 61, first_page=8, last_page=19)
    top5 = [page for page, score in ranked[:5]]

    print(f"\n=== {doc['title']} ===")
    print(f"  Judge-chosen chunk found on PDF page(s): {chunk_pages if chunk_pages else 'NOT FOUND'}")
    print(f"  ColPali top 5 pages (restricted to 8-19): {top5}")
    for page in chunk_pages:
        position = [p for p, s in ranked].index(page) + 1
        print(f"  ColPali rank of page {page}: {position} of {len(ranked)}")