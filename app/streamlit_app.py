import json
import sys
from pathlib import Path

import streamlit as st

# Streamlit puts app/ (this file's folder) on the import path, not the project root,
# so add the root explicitly to be able to import config.py from there.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import COMPANY_NAME
from pipeline.decisions import clear_decision, load_decisions, save_decision
from pipeline.review import review_reason

STATUS_LABELS = {"approved": "✅ Approved", "rejected": "❌ Rejected"}
PENDING_LABEL = "🕓 Pending"


def status_label(decision):
    return STATUS_LABELS[decision["decision"]] if decision else PENDING_LABEL


st.title("RegPulse — Compliance Memos")

with open("graph_results.json") as f:
    results = json.load(f)
decisions = load_decisions()

# Only covered and uncovered regulations get a memo. Keep each memo together with the
# reason (if any) it needs a human check, and the human decision made on it so far.
rows = [
    {
        "memo": r["memo"],
        "review": review_reason(r),
        "decision": decisions.get(r["document_number"]),
    }
    for r in results
    if r.get("memo")
]

filter_choice = st.sidebar.radio(
    "Show memo type:",
    options=["All", "outdated", "coverage_gap"]
)
only_review = st.sidebar.checkbox("Only memos that need review")
only_pending = st.sidebar.checkbox("Only memos not yet decided")

filtered = [
    row for row in rows
    if (filter_choice == "All" or row["memo"]["memo_type"] == filter_choice)
    and (not only_review or row["review"])
    and (not only_pending or not row["decision"])
]

review_count = sum(1 for row in rows if row["review"])
approved_count = sum(1 for row in rows if row["decision"] and row["decision"]["decision"] == "approved")
rejected_count = sum(1 for row in rows if row["decision"] and row["decision"]["decision"] == "rejected")
pending_count = len(rows) - approved_count - rejected_count

flagged_tile, approved_tile, rejected_tile, pending_tile = st.columns(4)
flagged_tile.metric("⚠ Flagged for review", review_count)
approved_tile.metric("✅ Approved", approved_count)
rejected_tile.metric("❌ Rejected", rejected_count)
pending_tile.metric("🕓 Pending", pending_count)

st.write(f"Showing {len(filtered)} of {len(rows)} memos")
administrative_count = sum(1 for r in results if r["category"] == "administrative")
not_applicable_count = sum(1 for r in results if r.get("verdict") == "not_applicable")
st.caption(
    f"{administrative_count} regulations were screened out as administrative, "
    f"and {not_applicable_count} were judged not applicable to {COMPANY_NAME}, so neither got a memo."
)

table_data = [
    {
        "Review": "⚠ Needs review" if row["review"] else "",
        "Status": status_label(row["decision"]),
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
    decision = row["decision"]
    doc = memo["document_number"]
    marker = "⚠ " if row["review"] else ""
    with st.expander(f"{marker}{memo['regulation_title']} — {memo['memo_type']} — {status_label(decision)}"):
        if row["review"]:
            st.warning(f"Needs review: {row['review']}")
        st.write(memo["memo_text"])
        if memo.get("judge_reasoning"):
            st.caption(f"Judge reasoning: {memo['judge_reasoning']}")
        st.link_button("View source regulation", memo["html_url"])

        st.markdown("**Human decision**")
        if decision:
            st.write(f"{status_label(decision)} on {decision['decided_at']}")
            if decision["note"]:
                st.caption(f"Note: {decision['note']}")
            if st.button("Undo decision", key=f"undo_{doc}"):
                clear_decision(doc)
                st.rerun()
        else:
            note = st.text_input("Note (optional)", key=f"note_{doc}")
            approve_col, reject_col = st.columns(2)
            if approve_col.button("Approve", key=f"approve_{doc}", type="primary"):
                save_decision(doc, "approved", note)
                st.rerun()
            if reject_col.button("Reject", key=f"reject_{doc}"):
                save_decision(doc, "rejected", note)
                st.rerun()