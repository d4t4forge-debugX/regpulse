import chromadb
from sentence_transformers import SentenceTransformer
def chunk_text(text, chunk_size=500, overlap=50):

    chunks = []
    start = 0

    while start < len(text):
        chunk = text[start:start + chunk_size]
        chunks.append(chunk)
        start = start + (chunk_size - overlap)
    return chunks

def get_collection():
    client = chromadb.PersistentClient(path="chroma_db")
    collection = client.get_or_create_collection(name="apple_risk_factors")
    return collection

def build_collection():
    with open("apple_risk_factors_clean.txt", "r", encoding="utf-8") as f:
        text = f.read()

    chunks = chunk_text(text)
    model = SentenceTransformer("all-MiniLM-L6-v2")
    embeddings = model.encode(chunks)

    collection = get_collection()
    ids = [f"chunk_{i}" for i in range(len(chunks))]

    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=chunks
    )

    return collection, model

def query_collection(collection, model, query_text, n_results=3, include_distances=False):
    query_embedding = model.encode([query_text]).tolist()
    results = collection.query(query_embeddings=query_embedding, n_results=n_results)
    documents = results["documents"][0]
    if include_distances:
        distances = results["distances"][0]
        return list(zip(documents, distances))
    return documents

if __name__ == "__main__":
    collection, model = build_collection()
    print(f"Collection count after adding: {collection.count()}")

    query_text = "supply chain risk"
    results = query_collection(collection, model, query_text)

    print("\nQuery:", query_text)
    for i, doc in enumerate(results):
        print(f"\n--- Result {i + 1} ---")
        print(doc)