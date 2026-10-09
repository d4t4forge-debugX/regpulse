from config import COMPANY_NAME
from pipeline.gemini_client import call_gemini_with_retry


def select_memo_type(doc):
    """Map the judge's verdict to a memo route: outdated, coverage_gap, or none."""
    if doc["verdict"] == "covered":
        return "outdated"
    if doc["verdict"] == "uncovered":
        return "coverage_gap"
    return "none"


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
    prompt = f"""You are assisting a compliance team at {COMPANY_NAME}. A new Federal Register regulation was published. An automated review judged that it materially affects {COMPANY_NAME}, and none of the most similar passages retrieved from {COMPANY_NAME}'s 10-K Risk Factors section discusses it.

Why it was judged to affect {COMPANY_NAME}: {shell['judge_reasoning']}

Regulation title: {shell['regulation_title']}
Regulation abstract: {shell['regulation_abstract']}

Write a short memo (3-5 sentences) that:
1. States that none of the reviewed Risk Factors passages appears to cover this regulation (the review checked the closest-matching passages, not every line of the 10-K).
2. Suggests, at a high level, what a new or updated disclosure might need to address, based on the regulation's content.

Do not present this as final compliance or legal advice — frame it as a starting point for the compliance team to evaluate."""

    response = call_gemini_with_retry(prompt)
    return response.text


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
    prompt = f"""You are assisting a compliance team at {COMPANY_NAME}. A new SEC/Federal Register regulation was published, and an existing disclosure in {COMPANY_NAME}'s 10-K Risk Factors section may now be outdated because of it.

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