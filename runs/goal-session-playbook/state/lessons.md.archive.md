# lessons.md — archive

Entries moved out of `lessons.md` by scripts/automation/lib/condense.sh (maintenance protocol §4).
Append-only: nothing here is ever deleted or rewritten.

<!-- condense.sh 2026-08-11T22:10:59Z: moved 9 entries (keep-iters=5) -->

## iter-0 — 2026-08-10T07:12:37Z

**Verdict:** CONTINUE
**Lesson:** The four "route not found" screenshots (`J-01/J-02/J-07/J-08-route-404.png`) are the
same file byte-for-byte (md5 `a11b5066…`): a raw JSON body capture contains no address bar, so it
cannot prove WHICH endpoint was probed — fine for recording an absence, useless once these routes
ship and the acceptance becomes "the endpoint serves the honest empty payload". Capture the URL in
frame (or a body that names its own route) from J-01 onward. Separately: J-10's acceptance text
spans the whole era ("MCP = exactly 20 tools"), so it stays `partial` until J-09 lands — and a
`partial` sentinel does not auto-trip the regression halt, so a kept-screen break must be halted on
manually.
**Applies to:** any iteration capturing browser evidence for a `/research/desk/playbook*` endpoint,
and any iteration reading J-10's status to decide whether the kept product is safe.

## iter-1 — 2026-08-10T11:05:00Z

**Verdict:** CONTINUE
**Lesson:** A backend-only iteration silently drops its Required-still-passing replay. The DoD
named TC-14 (replay `journey-scripts/J-10.json`), but the browser lane self-disables on
`Frontend Present: no` ("Browser QA Verdict: SKIPPED"), the dev handoff deferred it to browser-qa,
and the QA report marked it "DEFERRED … N/A" — three lanes each believed another owned it, so
nobody ran it. Any backend-only iteration with a required-still-passing browser journey must ask
for the replay explicitly.
**Applies to:** every iteration whose spec says `Frontend Present: no` while listing a
browser-verifiable journey in Required-still-passing (J-02 next).

## iter-1 — 2026-08-10T11:05:00Z

**Verdict:** CONTINUE
**Lesson:** Positional slot indexing fabricates data on gapped sessions, and unit tests cannot see
it. `opening_range`'s 5m fallback took `session_5m[:3]` positionally, so a session missing its
09:30/09:35 bars got an "opening range" built from 09:40/09:45/09:50 and disclosed as genuine —
all 42 tests, the review, and QA passed over it. It surfaced only when the auditor drove
`compute_playbook` end-to-end through a real `BarStore` with a deliberately gapped member. Spec §4's
`halted_formation` policy (the prescribed cure, audit B2) is still entirely unimplemented and must
land before J-07's back-scan touches real recorded sessions.
**Applies to:** any playbook detector/primitive work that indexes bars by position
(`desk_playbook_features.py`, `desk_playbook_detect.py`), and J-07's back-scan.

## iter-2 — 2026-08-10T19:40:00Z

**Verdict:** CONTINUE
**Lesson:** The baseline-anchor draw in `desk_playbook.py:557` hard-codes `k = min(1, len(bars))`
and rebuilds `random.Random(f"{seed}:playbook-{date}:{symbol}:{setup_id}")` *inside* the per-signal
branch. That is correct today only because an opening-range break can fire at most once per symbol
per session; the moment a family fires twice for one (symbol, setup_id), the same seed string will
draw the SAME anchor index twice and the baseline pool will silently duplicate instead of growing.
**Applies to:** any iteration adding a detector family that can fire more than once per
symbol-session (J-04 JBE/DBI/cup-and-handle, J-05 capitulation, J-06 range/double-top) — fix the
draw before adding the family, not after.

## iter-2 — 2026-08-10T19:40:00Z

**Verdict:** CONTINUE
**Lesson:** A golden-replay FAIL is not evidence of a product regression until the services are
proven alive by a REQUEST, not by a PID. This iteration's first replay reported `step 05 expected
"300.11" did not appear` while the backend process existed at 99% CPU but had already closed its
listening socket (post-SIGTERM uvicorn): `ss -ltnp` had no row for 8301 and `curl /health` returned
HTTP 000. Re-run on clean services it passed four times with the golden script byte-unedited.
**Applies to:** every iteration whose Required-still-passing set includes a browser/replay journey —
check `curl /health` (and the 3301/8301 pair, not 3000/8000) before believing a replay failure, and
never relax a golden assertion to make it green.

## iter-3 — 2026-08-10T21:20:00Z

**Verdict:** ESCALATE
**Lesson:** The browser-QA lane exercised the legacy-record state by planting a synthetic
`payload_version` 1 record straight into the operator's REAL store
(`apps/backend/.data/playbook/playbook-2026-08-04-e0f249f57785.json`) and by running real computes
over the live 101-member universe — both outside the iteration spec's own "fixture-scoped only"
line. The store has no delete path by design (v1, deliberately), so a QA artifact planted there is
permanent until someone removes the file by hand. The era-5B scoped-keyless recipe already solves
this: set `TAPEOLOGY_DESK_PLAYBOOK_DIR` (and the log dirs) to a scratch path for the rig.
**Applies to:** every browser-QA pass that needs a planted record or a compute — J-04/J-05/J-06
fixture signals, J-07's back-scan runs, J-08's evidence cells; scope the store env vars before the
first plant, and never rely on a delete path the design intentionally omits.

## iter-3 — 2026-08-10T21:20:00Z

**Verdict:** ESCALATE
**Lesson:** `/desk` is now ~37,000px tall with the Playbook section populated, and headless Chrome
paints blank/black at any deep `scrollTo` and truncates `fullpage:true` captures — so the shipped
tail sections could not be photographed at all. The working technique (used and documented by the
browser-qa agent) is to `display:none` the sibling `<section>`s above the target via `eval` for the
duration of the capture only, never touching source. Every functional assertion still runs against
the fully-rendered DOM.
**Applies to:** any iteration adding another `/desk` section (J-07 Backscan, J-08 Playbook
Evidence) — plan the capture technique up front, and treat a blank deep-scroll screenshot as a
capture defect to work around, never as evidence of a missing section.

## iter-4 — 2026-08-11T02:20:00Z

**Verdict:** CONTINUE
**Lesson:** A "must not fire" fixture can pass for the wrong reason. Iter-4's TC-4/TC-5 near-miss
tests asserted `results == []` and documented the jump gate as the cause, but the fixtures' lookback
leg sat inside `base_max_range_mbr`, so `consolidation_range`'s MAXIMAL window swallowed it back to
bar 0 and every candidate was rejected earlier at `start_idx - jump_lookback_bars < 0` — the audit
proved it by zeroing BOTH jump gates and still getting zero signals. A silence test is only evidence
if it also carries a gate-relaxed control showing exactly one signal fires when (and only when) the
named gate is relaxed.
**Applies to:** every future detector's near-miss fixture (J-05 capitulation/euphoria, J-06
range/double-top) — pair each "silent" assertion with a relaxed-gate control asserting the intended
gate is the decisive rejecter.

## iter-4 — 2026-08-11T02:20:00Z

**Verdict:** CONTINUE
**Lesson:** Extending the setup families silently invalidated the product's own summary copy, and the
guard test made it worse rather than catching it: `PLAYBOOK_REGISTER` (`desk_playbook.py:159`) and the
`/desk` section blurb (`page.tsx:5079`) both still say "opening-range-break signals", and that
register is embedded verbatim into every new record — including the real `playbook-2026-06-22-b698c3871e62.json`
whose five signals are all `jbe`/`dbi`. `test_copy_discipline.py` asserts the register is UNMODIFIED,
so leaving it stale passes and widening it fails; no lane (review, QA, browser-QA, coherence, audit)
flagged it.
**Applies to:** any iteration that adds a setup family, a measure, or a served pool (J-05, J-06,
J-08) — widen the register/blurb in the same commit and deliberately re-derive the
register-unmodified assertion, exactly like the refresh-chain effect-count guard.

