from dotenv import load_dotenv
import os
import time
from google import genai

load_dotenv()
_client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

def call_gemini_with_retry(prompt, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = _client.models.generate_content(
                model="gemini-3.5-flash",
                contents=prompt
            )
            return response
        except Exception as e:
            if "503" in str(e) and attempt < max_retries - 1:
                wait = 10 * (attempt + 1)
                print(f"  503 error, retrying in {wait}s...")
                time.sleep(wait)
            else:
                raise

def select_memo_type(doc):
    if doc["has_relevant_match"]:
        return "outdated"
    else:
        return "coverage_gap"

def build_coverage_gap_shell(doc):
    return {
        "regulation_title": doc["title"],
        "regulation_abstract": doc.get("abstract") or "(no abstract available for this document)",
        "publication_date": doc["publication_date"],
        "document_number": doc["document_number"],
        "html_url": doc["html_url"],
        "memo_type": "coverage_gap",
        "judge_reasoning": doc["judge_reasoning"],
        "memo_text": None  # filled in by the LLM step later
    }
def generate_coverage_gap_memo_text(shell):
    prompt = f"""You are assisting a compliance team at Apple. A new SEC/Federal Register regulation was published, and no existing disclosure in Apple's 10-K Risk Factors section addresses it.

Regulation title: {shell['regulation_title']}
Regulation abstract: {shell['regulation_abstract']}

Write a short memo (3-5 sentences) that:
1. States plainly that no existing Risk Factors disclosure covers this regulation.
2. Suggests, at a high level, what a new or updated disclosure might need to address, based on the regulation's content.

Do not present this as final compliance or legal advice — frame it as a starting point for the compliance team to evaluate."""

    response = call_gemini_with_retry(prompt)
    return response.text

def run_impact_agent(input_file="federal_register_retrieval.json", output_file="coverage_gap_memos.json"):
    import json
    import os

    with open(input_file) as f:
        documents = json.load(f)

    if os.path.exists(output_file):
        with open(output_file) as f:
            results = json.load(f)
    else:
        results = []

    already_processed = {r["document_number"] for r in results}

    for doc in documents:
        if doc["document_number"] in already_processed:
            print(f"--- Skipping (already processed): {doc['title']} ---")
            continue

        memo_type = select_memo_type(doc)
        if memo_type == "coverage_gap":
            shell = build_coverage_gap_shell(doc)
            shell["memo_text"] = generate_coverage_gap_memo_text(shell)
        elif memo_type == "outdated":
            shell = build_outdated_shell(doc)
            shell["memo_text"] = generate_outdated_memo_text(shell)

        results.append(shell)
        print(f"--- {shell['regulation_title']} ---")
        print(shell["memo_text"])
        print()
        with open(output_file, "w") as f:
            json.dump(results, f, indent=2)
        time.sleep(13)

    return results

def build_outdated_shell(doc):
    return {
        "regulation_title": doc["title"],
        "regulation_abstract": doc.get("abstract") or "(no abstract available for this document)",
        "publication_date": doc["publication_date"],
        "document_number": doc["document_number"],
        "html_url": doc["html_url"],
        "memo_type": "outdated",
        "matched_chunk_text": doc["relevant_chunk_text"],
        "judge_reasoning": doc["judge_reasoning"],
        "memo_text": None  # filled in by the LLM step later
    }

def generate_outdated_memo_text(shell):
    prompt = f"""You are assisting a compliance team at Apple. A new SEC/Federal Register regulation was published, and an existing disclosure in Apple's 10-K Risk Factors section may now be outdated because of it.

Regulation title: {shell['regulation_title']}
Regulation abstract: {shell['regulation_abstract']}

Existing Risk Factors disclosure that may be affected:
{shell['matched_chunk_text']}

Why this disclosure was flagged as relevant: {shell['judge_reasoning']}

Write a short memo (3-5 sentences) that:
1. States plainly which existing disclosure may now be outdated and why.
2. Points out, at a high level, what may have changed that the current disclosure doesn't reflect.

Do not present this as final compliance or legal advice — frame it as a starting point for the compliance team to evaluate."""

    response = call_gemini_with_retry(prompt)
    return response.text

if __name__ == "__main__":
    run_impact_agent()