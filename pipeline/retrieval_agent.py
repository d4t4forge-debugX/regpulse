import json
import time
import sys
from sentence_transformers import SentenceTransformer
from vectorstore.chroma_store import get_collection, query_collection

def load_domain_documents(filename="federal_register_domains.json"):
    with open(filename, "r") as f:
        return json.load(f)

def retrieve_for_regulation(collection, model, doc, n_results=10):
    abstract = doc.get("abstract") or ""
    query_text = doc["title"] + " " + abstract
    return query_collection(collection, model, query_text, n_results=n_results, include_distances=True)

def save_retrieval_results(documents, filename="federal_register_retrieval.json"):
    with open(filename, "w") as f:
        json.dump(documents, f, indent=2)


from dotenv import load_dotenv
import os
from google import genai
from google.genai import types

load_dotenv()
_client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

def call_gemini_with_retry(prompt, model="gemini-3.5-flash", max_retries=5, temperature=0):
    for attempt in range(max_retries):
        try:
            response = _client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(temperature=temperature)
            )
            return response
        except Exception as e:
            if "503" in str(e) and attempt < max_retries - 1:
                wait = 15 * (attempt + 1)
                print(f"  503 error, retrying in {wait}s...")
                time.sleep(wait)
            else:
                raise

def judge_relevance_llm(doc, matches, model="gemini-3.5-flash"):
    n = len(matches)
    chunks_text = "\n\n".join(
        f"Chunk {i+1} (embedding distance={distance:.3f}):\n{text}"
        for i, (text, distance) in enumerate(matches)
    )

    valid_numbers = ", ".join(str(i) for i in range(1, n + 1))

    abstract_text = doc.get("abstract") or "(no abstract available for this document)"

    prompt = f"""You are assisting a compliance team at Apple in reviewing whether a new regulation makes an existing Risk Factors disclosure outdated.

Regulation title: {doc['title']}
Regulation abstract: {abstract_text}

Below are the top {n} candidate excerpts retrieved from Apple's 10-K Risk Factors section, ranked by embedding similarity (lower distance = more similar). Similarity ranking is not a guarantee of topical relevance.

{chunks_text}

Judge whether any of these excerpts is genuinely, substantively relevant to the regulation above -- meaning it discusses the same specific risk area, not just a loosely related topic.

Respond with ONLY a JSON object, no other text, no markdown code fences, in exactly this format:
{{"is_relevant": true or false, "relevant_chunk_number": {valid_numbers}, or null, "reasoning": "one sentence explanation"}}"""

    response = call_gemini_with_retry(prompt, model=model)

    raw_text = response.text.strip()
    raw_text = raw_text.replace("```json", "").replace("```", "").strip()

    return json.loads(raw_text)


def judge_document(doc, collection, model):
    """Retrieve candidate chunks for one regulation, judge them, and record the verdict on doc."""
    matches = retrieve_for_regulation(collection, model, doc)
    verdict = judge_relevance_llm(doc, matches)

    doc["has_relevant_match"] = verdict["is_relevant"]
    doc["relevant_chunk_number"] = verdict["relevant_chunk_number"]
    doc["judge_reasoning"] = verdict["reasoning"]
    doc["best_distance"] = round(min(distance for text, distance in matches), 3)

    if verdict["is_relevant"] and verdict["relevant_chunk_number"]:
        doc["relevant_chunk_text"] = matches[verdict["relevant_chunk_number"] - 1][0]

    return doc


if __name__ == "__main__":
    force_rerun = "--all" in sys.argv
    output_file = "federal_register_retrieval.json"

    collection = get_collection()
    model = SentenceTransformer("all-MiniLM-L6-v2")
    documents = load_domain_documents()

    # Load any results saved by a previous run, keyed by document_number
    results_by_id = {}
    if os.path.exists(output_file):
        with open(output_file, "r") as f:
            results_by_id = {d["document_number"]: d for d in json.load(f)}

    for doc in documents:
        doc_id = doc["document_number"]

        if doc_id in results_by_id and not force_rerun:
            print(f"\nSkipping (already judged): {doc['title']}")
            continue

        judge_document(doc, collection, model)

        print(f"\n{doc['publication_date']} - {doc['title']}")
        print(f"  Relevant match found: {doc['has_relevant_match']} (best distance={doc['best_distance']})")
        print(f"  Reasoning: {doc['judge_reasoning']}")

        # Save after every document so a crash never loses finished work
        results_by_id[doc_id] = doc
        save_retrieval_results(list(results_by_id.values()), output_file)

    print(f"\nDone. Results in {output_file}")