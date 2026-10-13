# Codex CLI context: Ticket Coverage Planner

## Task
Build a complete, working Python Streamlit web app from this specification. Target deployment: GitHub repository plus free Streamlit Community Cloud hosting. Build and test locally first; provide beginner-friendly Windows setup and deployment instructions. Verify current official Streamlit/GitHub documentation before giving version-sensitive deployment guidance. Do not claim deployment occurred unless verified.

User: Mahendra, an electrical engineer who prefers plain English and practical explanations. The tool will be used on a phone while standing at a ticket counter. Keep the app small, fast, readable, and easy to operate. This is a number-selection assistant, not a prediction system or ticket-purchasing service.

## Confirmed facts and preferences
- Numbers are five digits; preserve leading zeros everywhere.
- Current possible first-digit series: 0, 1, 2, 3.
- 00000 is not sold and must never be recommended.
- The currently discussed overall range is 00001–39999. This is a provisional ceiling, not confirmation that all these tickets exist or are sold.
- Books contain 50 consecutive tickets with boundaries 00001–00050, 00051–00100, etc.
- A book may be partly sold. The entered number is the first CURRENTLY available number, not necessarily the original first page.
- The entered first available number itself is eligible.
- Budget: 10 tickets TOTAL, not 10 additional tickets.
- Already purchased: 20397. Seed this once for a fresh user session; allow correcting/removing it. Do not reinsert it on every rerun.
- Ticket price shown on the banner: INR 501. Optional cost display: 10 tickets = INR 5,010. The controlling limit is 10 tickets, not INR 5,000.
- Mandatory selection preference: one ticket ending in each digit 0–9.
- First-digit balance is preferred, NOT mandatory.
- Zero-series availability at the counter is uncertain. User suspects sold out but will check. Provide controls to enable it when found.
- If all four series are available, ideal first-digit counts are any permutation of 3,3,2,2.
- If only 1,2,3 are available, ideal counts are any permutation of 4,3,3.
- Never discard a useful missing final digit solely because its first digit is overrepresented.
- User wants a random recommendation among equally suitable available candidates.
- A suggestion becomes purchased ONLY after explicit confirmation.

## Draw mechanics and mathematical limits
According to the user:
1. Five digits are drawn separately from five bowls after mixing.
2. The rightmost four bowls contain digits 0–9; the leftmost bowl contains eligible first digits depending on issued/sold series.
3. If the resulting complete number is unsold, including 00000, ALL FIVE digits are redrawn.
4. Repeat until a sold number is drawn.

Assuming fair independent bowls, each eligible sold number is equally likely after complete rejection/redraw. For N distinct sold tickets and k user-owned distinct tickets, chance of the first prize is k/N. Do not infer N from available series or maximum printed number.

The earlier banner advertised first-prize suffix-based awards: last four digits (washing machine), last three digits (dinner set), and last two/one digits (special gifts). Detailed exclusions, overlap rules, eligibility and gift values remain unverified. Do not invent them or calculate guaranteed returns.

Different final digits automatically imply different last-two, last-three and last-four digit strings. Separate uniqueness constraints for these suffixes are redundant, although displaying coverage is useful.

Ten distinct endings maximise the number of different suffixes covered at each length. They do not necessarily maximise suffix-event probability if the distribution of SOLD numbers is uneven. Without the complete sold-number distribution, this is a coverage heuristic, not a proven optimiser of money recovered or expected value.

Covering final digits 0–9 guarantees a numerical last-digit match to any accepted winning number; it does NOT guarantee eligibility, payment, recovery of spend, or profit. First-digit balance and random selection confer no jackpot advantage versus any other k distinct sold tickets. Repeated internal digits and visually attractive numbers have no special merit.

Do not display unconditional suffix probabilities of 10%, 1%, 0.1% after unsold-number rejection. Omit an odds calculator in V1 unless N is explicitly supplied and assumptions are stated. No exact “chance of any prize” calculation is possible from the information provided.

## Book boundaries
Use integer arithmetic:
    book_start = ((n - 1) // 50) * 50 + 1
    nominal_book_end = book_start + 49
    effective_end = min(nominal_book_end, configured_max_ticket)
    candidate_range = inclusive range from n through effective_end

Examples:
- 15786 -> original book 15751–15800; search 15786–15800 (15 numbers).
- 15800 -> search 15800 only.
- 15801 -> search 15801–15850.
- 00001 -> search 00001–00050.
- 00050 -> search 00050 only.
- 00051 -> search 00051–00100.
- 00342 -> search 00342–00350.
- 39986 -> search 39986–39999 with current ceiling; never recommend 40000.

IMPORTANT: books can cross first-digit boundaries. The book 09951–10000 contains both series 0 and 1. Check each candidate's first digit, not just the input's first digit. Similarly handle 19951–20000 and 29951–30000.

Permit an optional actual last-available-number override that can shorten the range but cannot extend beyond the nominal book end or configured maximum. Display assumed availability: all numbers in the range except user exclusions; the app cannot know live sales.

## Inputs and mobile UI
Main flow should work with minimal typing:
1. Purchased-ticket list, initially 20397, editable as comma/space/newline-separated numbers.
2. First available number in the current book.
3. First-digit availability settings.
4. Optional sold/unavailable numbers in this book.
5. Optional shortened last-available number.
6. “Suggest number” button.
7. Large five-digit recommendation, explanation, “Suggest another”, and “Confirm purchased”.

Availability design:
- Track each series as Available / Unavailable / Unknown.
- Initial states: 1,2,3 Available as a working default; 0 Unknown.
- Unknown is not equivalent to confirmed sold out.
- A zero-series book entered while 0 is Unknown should show an inline “Series 0 is available here” action. Enable that series upon confirmation; no blocking modal needed.
- Exclude Unavailable/Unknown series from purchasing candidates until enabled.
- Preserve and count previously purchased tickets even if their series later becomes unavailable.
- Availability controls concern purchasing at the counter, not eligibility in the draw.
- If no series are enabled, prompt the user to enable at least one; do not divide by zero.

Dashboard:
- Purchased count / 10 and tickets remaining.
- Purchased numbers with last 1/2/3/4 digits, all as strings.
- Final-digit coverage badges 0–9.
- Missing endings.
- First-digit counts for 0,1,2,3.
- Ideal balance shown as a preference; note when previous purchases or availability make it unattainable.
- Preferred series for the NEXT book, based on least-represented enabled series.
- No “lucky”, “winning prediction”, or guaranteed-return labels.

## Recommendation algorithm
1. Validate inputs and purchased list.
2. If 10 tickets are already purchased, stop recommendations and display coverage. Never suggest an 11th purchase.
3. Compute used final digits and missing final digits.
4. Build the current book's remaining inclusive range.
5. Filter out:
   - 00000 and numbers outside configured bounds;
   - disabled/unconfirmed purchasing series;
   - previously purchased complete numbers;
   - explicitly unavailable numbers;
   - numbers whose final digit is already represented.
6. If candidates remain, rank them by current purchased count of their first digit (smaller count preferred). This is a soft balance preference.
7. Choose uniformly at random from the best-ranked candidates.
8. A candidate in an overrepresented series is still valid if it covers a missing ending. Explain that it improves ending coverage but may weaken the preferred balance; optionally suggest checking a less-represented series.
9. If none remain, explain the actual cause:
   - no missing ending available in this range;
   - every eligible number excluded/unavailable;
   - series needs enabling;
   - invalid range.
   Show “Choose another book” only when appropriate, alongside missing endings and preferred enabled series. Do not invent a specific available book.
10. “Suggest another” should choose a different equally ranked candidate when possible. If only one exists, explain that; do not loop forever.
11. Keep the displayed suggestion stable across unrelated Streamlit reruns. Invalidate it when relevant inputs change.
12. On “Confirm purchased”, revalidate against current state, add exactly once, update coverage and balance, and clear the suggestion. Handle rapid/double clicks safely.

Randomness is only a tie-breaker. There is no need for a machine-learning model or random “lucky score”.

## Purchased-list validation and recovery
- Normalise 1–5 ASCII digits to five characters, e.g. 342 -> 00342.
- Reject negative values, decimals, scientific notation, letters, Unicode lookalike digits, strings longer than 5 digits, 00000, and values beyond configured bounds.
- Report duplicate complete ticket entries clearly; avoid double-counting.
- Do not silently drop real purchased tickets just because final digits repeat. Preserve distinct purchased numbers and warn that coverage is reduced.
- If the user already owns two tickets with the same ending, explain that complete ten-ending coverage is impossible within a ten-ticket total without changing the recorded purchases. Do not claim a bought ticket can be returned.
- Do not delete old purchases when series availability changes.
- Reject a new edit/import with over 10 distinct purchased tickets without overwriting valid existing state.
- Bad imported data must not partially overwrite state.
- Scope unavailable-number lists and manual end overrides to the current book. Clear or explicitly preserve them appropriately when book changes; do not apply stale exclusions accidentally.
- Allow correcting/removing an entry and undoing the last confirmed purchase.

## State and persistence
Use per-user Streamlit session state for the live app. Do not use module globals or shared cached mutable lists for personal records.
Provide:
- Download backup JSON.
- Upload/restore backup JSON.
- Copyable purchased-ticket text.
- Versioned JSON schema containing purchased tickets, series availability, and essential settings.
- Validation on import; no executable deserialisation.
- Exclude personal backups from Git via .gitignore.

A browser refresh, disconnected session, or hosted restart may lose in-memory state. State this briefly in the app and README. Do not describe session_state or a hosted local file as durable storage. V1 may use explicit JSON backup/restore without login or database; show the backup action prominently after purchases. No need to add a backend merely for this small task.

## Technical deliverables
Create a simple repository, for example:
- app.py — Streamlit interface.
- ticket_logic.py — pure parsing, range, coverage and recommendation functions.
- requirements.txt — only necessary dependencies, with versions chosen/verified during implementation.
- tests/test_ticket_logic.py — focused meaningful unit tests.
- README.md — Windows local run, usage, backup/restore, GitHub and Streamlit Community Cloud deployment.
- .gitignore — virtual environments, secrets, caches and user backups.

Use an isolated virtual environment and Python version currently supported by the target host. Prefer standard-library unittest or a minimal test dependency. Keep UI concise and mobile friendly with large numbers/buttons. No custom frontend framework, paid services, authentication, database, analytics or external prediction APIs required.

Document Windows steps in plain language: check Python/Git, create virtual environment, install requirements, run "python -m streamlit run app.py". Give PowerShell activation troubleshooting or direct venv-Python alternative. Never assume tools are already installed. Verify current deployment instructions from official sources. Never commit credentials.

## Required acceptance cases
1. Existing 20397 + range 15786–15800:
   eligible = 15786,15788,15789,15790,15791,15792,15793,15794,15795,15796,15798,15799,15800
   (assuming all these are available and series 1 enabled).
   Exclude 15787 and 15797.
2. First input 15800 includes 15800; it is not an empty range.
3. Existing 20397 + 00342, series 0 enabled:
   search through 00350; exclude 00347.
4. Same input with series 0 Unknown: offer availability confirmation; do not assert sold out.
5. Nine purchases with endings 0–8, and book 15800–15800: no eligible number, since only ending 0 is present.
6. Ten valid purchases: no further recommendation or confirmation.
7. Boundary 09986–10000: classify 10000 as series 1, not 0. With series 0 disabled and 1 enabled, 10000 can remain eligible if ending 0 is missing.
8. 39986 is capped at 39999 under current ceiling.
9. Switching enabled series preserves prior purchases and recalculates soft balance.
10. Repeated existing final digits produce a coverage warning without losing purchased records.
11. An overrepresented first digit never blocks a missing final digit solely for balance.
12. Suggestion stability across reruns; invalidation on input changes; duplicate-confirm prevention.
13. Backup export/import round-trip preserves leading zeros and settings; malformed/oversized purchased lists do not corrupt state.
14. One eligible candidate: “Suggest another” returns/explains the same sole option without failure.

Use deterministic/random-injected tests for selection so assertions do not depend on chance.

## Implementation instructions to Codex CLI
Read this entire file, inspect the project folder and any AGENTS.md instructions, then implement the working app. Do not stop at a plan. Preserve unrelated existing files. Make reasonable implementation decisions from this specification; ask only if a genuine blocker remains.
Run meaningful logic tests and a local Streamlit startup/smoke check. Report what was actually tested and any unresolved limitations. Provide exact local-run commands and beginner-friendly deployment instructions. Do not claim publication or GitHub upload without performing and verifying it with appropriate user authorisation/access.

No further clarification about book boundaries or zero-series availability is needed: those are already resolved by the rules and controls above.

