"""
pipeline/review.py

Decides which memos a human should check before anyone acts on them.

The threshold comes from the evaluation data, not a guess. Across the Apple and
Duke gold sets, every correct "covered" verdict had a closest-passage distance of
1.055 or less (0.59, 0.729, 0.837, 0.846, 1.055), and both wrong "covered" verdicts
(Title V at 1.007, button batteries at 1.235) were ones where the judge leaned on a
generic catch-all sentence. A cut at 1.0 flags both wrong ones and one correct one
(COPPA, 1.055).
"""

REVIEW_DISTANCE_THRESHOLD = 1.0


def review_reason(result):
    """Return a sentence saying why this result needs human review, or None if it does not."""
    verdict = result.get("verdict")
    if verdict == "covered" and result["best_distance"] >= REVIEW_DISTANCE_THRESHOLD:
        return (
            f"Covered verdict rests on a weak match (closest passage at distance {result['best_distance']}, "
            f"threshold {REVIEW_DISTANCE_THRESHOLD}). Check that the passage is about this rule and not a "
            "generic catch-all sentence."
        )
    if verdict == "uncovered":
        return (
            "Coverage gap judged from the 10 closest Risk Factors passages only. Confirm the risk is not "
            "disclosed elsewhere in the 10-K before drafting new language."
        )
    return None
