# RegPulse: one-page executive summary

## Problem

Public companies list their risks in the Risk Factors section of their annual 10-K. When a regulator publishes a new rule, some of that wording can become outdated, or a new obligation may not be covered at all. Today a compliance analyst finds this by reading every new rule, deciding whether it even applies, and cross-checking it against the filing by hand. Most rules do not apply, so most of that reading is wasted, and the ones that do apply are easy to miss.

## Users

Corporate compliance and securities-disclosure teams, and the legal reviewers who sign off on 10-K risk language.

## Outcome metric

How many rules reach a human reviewer, and how many of those actually matter to the company. Supporting metrics: judge accuracy on blind-labeled gold sets, and how often the review flag catches the judge's mistakes.

## How it works

1. Fetches new rules from the Federal Register for the regulators that matter to the company.
2. Screens out agency housekeeping (corrections, delegations, date extensions, effective-date confirmations) with a keyword rule.
3. Retrieves the 10 closest passages from the company's Risk Factors (local embeddings and vector store).
4. An LLM judge (Gemini) decides in two steps: does the rule materially affect this company, and if so, does a passage already cover it?
5. Writes an "outdated" memo (a passage covers it and may need updating) or a "coverage gap" memo (it applies but nothing covers it). Rules that do not apply get no memo.
6. Flags memos for human review when the verdict rests on a weak match or claims a gap, and shows everything in a dashboard.

It runs on a weekday schedule, is orchestrated with LangGraph and traced in LangSmith, and both evaluations run in CI on every change. All company-specific settings live in one config file.

## Results

| | Apple (SEC rules) | Duke Energy (FERC, EPA, NRC, DOE, PHMSA) |
|---|---|---|
| Rules processed | 31 | 118 |
| Memos written | 5 | 8 |
| Memos flagged for review | 3 | 5 |
| Judge accuracy (blind gold set) | 11/12 | 10/11 |
| Housekeeping screen accuracy | 30/31 | 21/24 |
| Judge mistakes caught by the review flag | 1 of 1 | 1 of 1 |

For Duke Energy, 110 of 118 rules never reached a reviewer: 27 were housekeeping and 83 were judged not to apply. Adding the "does it apply?" step cut Apple's memos from 13 to 5, removing memos about rules such as a ceremonial proclamation.

## Risks

- **Generic catch-all text.** The judge sometimes treats a broad sentence ("environmental, health and safety, including product design") as coverage. Seen once per company; the review flag catches both cases.
- **Partial view.** The judge sees the 10 closest passages, not the whole 10-K, so every claimed gap is flagged for confirmation.
- **Small evaluation sets.** 11 to 12 judge examples per company give wide uncertainty; labels are committed before each run and corrections are documented.
- **Memo wording is not scored.** Memos are drafts for a reviewer, never final advice.

## Next steps

1. Grow both gold sets with cases labeled blind from their abstracts, including more coverage-gap examples.
2. Test a prompt rule for generic catch-all text against those new cases.
3. Record reviewer approve/reject decisions to measure the review flag in use.
4. Move to managed services: Bedrock or Azure OpenAI for the model, a managed vector store, a cloud scheduler.
