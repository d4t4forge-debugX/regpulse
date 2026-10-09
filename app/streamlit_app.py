import json
import sys
from pathlib import Path

import streamlit as st

# Streamlit puts app/ (this file's folder) on the import path, not the project root,
# so add the root explicitly to be able to import config.py from there.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import COMPANY_NAME

st.title("RegPulse — Compliance Memos")

with open("graph_results.json") as f:
    results = json.load(f)

# Only substantive regulations reach the judge and get a memo; administrative
# ones have no "memo" key at all, so this line both selects and unwraps them.
memos = [r["memo"] for r in results if r.get("memo")]

filter_choice = st.sidebar.radio(
    "Show memo type:",
    options=["All", "outdated", "coverage_gap"]
)

if filter_choice == "All":
    filtered_memos = memos
else:
    filtered_memos = [m for m in memos if m["memo_type"] == filter_choice]

st.write(f"Showing {len(filtered_memos)} of {len(memos)} memos")
administrative_count = sum(1 for r in results if r["category"] == "administrative")
not_applicable_count = sum(1 for r in results if r.get("verdict") == "not_applicable")
st.caption(
    f"{administrative_count} regulations were screened out as administrative, "
    f"and {not_applicable_count} were judged not applicable to {COMPANY_NAME}, so neither got a memo."
)
table_data = [
    {
        "Title": memo["regulation_title"],
        "Type": memo["memo_type"],
        "Date": memo["publication_date"],
    }
    for memo in filtered_memos
]
st.dataframe(
    table_data,
    width="stretch",
    column_config={"Title": st.column_config.TextColumn(width="large")},
)

st.divider()
st.subheader("Full memos")

for memo in filtered_memos:
    with st.expander(f"{memo['regulation_title']} — {memo['memo_type']}"):
        st.write(memo["memo_text"])
        if memo.get("judge_reasoning"):
            st.caption(f"Judge reasoning: {memo['judge_reasoning']}")
        st.link_button("View source regulation", memo["html_url"])