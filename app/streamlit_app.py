import json
import sys
from pathlib import Path

import streamlit as st

# Streamlit puts app/ (this file's folder) on the import path, not the project root,
# so add the root explicitly to be able to import config.py from there.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import COMPANY_NAME
from pipeline.review import review_reason

st.title("RegPulse — Compliance Memos")

with open("graph_results.json") as f:
    results = json.load(f)

# Only covered and uncovered regulations get a memo. Keep each memo together with the
# reason (if any) it needs a human check, which comes from the full result.
rows = [
    {"memo": r["memo"], "review": review_reason(r)}
    for r in results
    if r.get("memo")
]

filter_choice = st.sidebar.radio(
    "Show memo type:",
    options=["All", "outdated", "coverage_gap"]
)
only_review = st.sidebar.checkbox("Only memos that need review")

filtered = [
    row for row in rows
    if (filter_choice == "All" or row["memo"]["memo_type"] == filter_choice)
    and (not only_review or row["review"])
]

review_count = sum(1 for row in rows if row["review"])
st.write(f"Showing {len(filtered)} of {len(rows)} memos ({review_count} flagged for review)")
administrative_count = sum(1 for r in results if r["category"] == "administrative")
not_applicable_count = sum(1 for r in results if r.get("verdict") == "not_applicable")
st.caption(
    f"{administrative_count} regulations were screened out as administrative, "
    f"and {not_applicable_count} were judged not applicable to {COMPANY_NAME}, so neither got a memo."
)

table_data = [
    {
        "Review": "⚠ Needs review" if row["review"] else "",
        "Title": row["memo"]["regulation_title"],
        "Type": row["memo"]["memo_type"],
        "Date": row["memo"]["publication_date"],
    }
    for row in filtered
]
st.dataframe(
    table_data,
    width="stretch",
    column_config={"Title": st.column_config.TextColumn(width="large")},
)

st.divider()
st.subheader("Full memos")

for row in filtered:
    memo = row["memo"]
    marker = "⚠ " if row["review"] else ""
    with st.expander(f"{marker}{memo['regulation_title']} — {memo['memo_type']}"):
        if row["review"]:
            st.warning(f"Needs review: {row['review']}")
        st.write(memo["memo_text"])
        if memo.get("judge_reasoning"):
            st.caption(f"Judge reasoning: {memo['judge_reasoning']}")
        st.link_button("View source regulation", memo["html_url"])
