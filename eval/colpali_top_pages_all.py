import json
from collections import Counter

from vectorstore.colpali_store import load_colqwen2_model, embed_query, rank_pages

with open("federal_register_retrieval.json") as f:
    documents = json.load(f)

model, processor = load_colqwen2_model()

page_counts = Counter()

for doc in documents:
    query_text = doc["title"] + " " + (doc.get("abstract") or "")
    query_embedding = embed_query(query_text, model, processor)
    ranked = rank_pages(query_embedding, "vectorstore/colpali_embeddings", 61, first_page=8, last_page=19)
    top3 = ranked[:3]
    page_counts.update(page for page, score in top3)

    print(f"\n{doc['title'][:60]} | text judge: {doc['has_relevant_match']}")
    print("  ColPali top 3:", [(page, round(float(score), 2)) for page, score in top3])

print(f"\nHow often each page appeared in a top 3 (out of {len(documents)} regulations):")
for page, count in page_counts.most_common():
    print(f"  Page {page}: {count}")
