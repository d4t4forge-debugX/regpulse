"""Human review decisions on memos, kept apart from pipeline output.

graph_results.json is rewritten by the scheduled pipeline run, so decisions a
reviewer makes in the dashboard live in their own file, keyed by the
regulation's document_number. The pipeline never reads or writes this file,
so a pipeline run can never overwrite a human decision.
"""
import json
from datetime import datetime
from pathlib import Path

# Always the project root, no matter which folder the code is run from.
DECISIONS_FILE = Path(__file__).resolve().parent.parent / "review_decisions.json"
VALID_DECISIONS = ("approved", "rejected")


def load_decisions():
    """Return {document_number: {decision, note, decided_at}}, or {} if nothing saved yet."""
    if not DECISIONS_FILE.exists():
        return {}
    with open(DECISIONS_FILE) as f:
        return json.load(f)


def _write(decisions):
    with open(DECISIONS_FILE, "w") as f:
        json.dump(decisions, f, indent=2, sort_keys=True)


def save_decision(document_number, decision, note=""):
    """Record a reviewer's approve/reject for one memo, replacing any earlier decision."""
    if decision not in VALID_DECISIONS:
        raise ValueError(f"decision must be one of {VALID_DECISIONS}, got {decision!r}")
    decisions = load_decisions()
    decisions[document_number] = {
        "decision": decision,
        "note": note.strip(),
        "decided_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }
    _write(decisions)


def clear_decision(document_number):
    """Undo: remove a memo's decision so it goes back to pending."""
    decisions = load_decisions()
    decisions.pop(document_number, None)
    _write(decisions)