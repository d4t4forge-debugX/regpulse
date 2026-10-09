import json

from config import COMPANY_NAME, GEMINI_MODEL
from pipeline.gemini_client import call_gemini_with_retry
from vectorstore.chroma_store import query_collection

VERDICTS = ("covered", "uncovered", "not_applicable")


def retrieve_for_regulation(collection, model, doc, n_results=10):
    abstract = doc.get("abstract") or ""
    query_text = doc["title"] + " " + abstract
    return query_collection(collection, model, query_text, n_results=n_results, include_distances=True)


def judge_relevance_llm(doc, matches, model=GEMINI_MODEL):
    n = len(matches)
    chunks_text = "\n\n".join(
        f"Chunk {i+1} (embedding distance={distance:.3f}):\n{text}"
        for i, (text, distance) in enumerate(matches)
    )

    valid_numbers = ", ".join(str(i) for i in range(1, n + 1))

    abstract_text = doc.get("abstract") or "(no abstract available for this document)"

    prompt = f"""You are assisting a compliance team at {COMPANY_NAME} in reviewing how a new regulation relates to {COMPANY_NAME}'s existing 10-K Risk Factors disclosures.

Regulation title: {doc['title']}
Regulation abstract: {abstract_text}

Below are the top {n} candidate excerpts retrieved from {COMPANY_NAME}'s 10-K Risk Factors section, ranked by embedding similarity (lower distance = more similar). Similarity ranking is not a guarantee of topical relevance.

{chunks_text}

Decide in two steps:

Step 1 -- Does this regulation materially affect {COMPANY_NAME}'s own business, operations, or legal obligations? A regulation that targets other companies or industries, kinds of products or issuers that {COMPANY_NAME} is not, government-internal matters, or ceremonial matters does NOT materially affect {COMPANY_NAME}, even if {COMPANY_NAME}'s Risk Factors discuss the same general topic. If it does not, the verdict is "not_applicable" and you stop here.

Step 2 -- Only if it does affect {COMPANY_NAME}: if at least one excerpt discusses that specific risk area, the verdict is "covered" (that disclosure may need updating); if none does, the verdict is "uncovered".
Respond with ONLY a JSON object, no other text, no markdown code fences, in exactly this format:
{{"verdict": "covered" or "uncovered" or "not_applicable", "relevant_chunk_number": {valid_numbers}, or null, "reasoning": "one sentence explanation"}}
Give a relevant_chunk_number only when the verdict is "covered"; otherwise use null."""

    # Ask up to twice: a reply that is not valid JSON is usually a one-off formatting slip
    for attempt in range(2):
        response = call_gemini_with_retry(prompt, model=model)
        raw_text = (response.text or "").strip()
        raw_text = raw_text.replace("```json", "").replace("```", "").strip()
        try:
            return json.loads(raw_text)
        except json.JSONDecodeError:
            print(f"  Judge reply was not valid JSON (attempt {attempt + 1} of 2): {raw_text[:200]!r}")
    raise ValueError(f"Judge returned invalid JSON twice for {doc['document_number']}")


def judge_document(doc, collection, model):
    """Retrieve candidate chunks for one regulation, judge them, and record the verdict on doc."""
    matches = retrieve_for_regulation(collection, model, doc)
    result = judge_relevance_llm(doc, matches)

    if result["verdict"] not in VERDICTS:
        raise ValueError(f"Judge returned an unknown verdict: {result['verdict']!r}")

    doc["verdict"] = result["verdict"]
    doc["has_relevant_match"] = result["verdict"] == "covered"
    doc["relevant_chunk_number"] = result["relevant_chunk_number"]
    doc["judge_reasoning"] = result["reasoning"]
    doc["best_distance"] = round(min(distance for text, distance in matches), 3)

    if doc["has_relevant_match"] and result["relevant_chunk_number"]:
        doc["relevant_chunk_text"] = matches[result["relevant_chunk_number"] - 1][0]

    return doc