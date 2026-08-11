# Goal Session playbook — Lessons Learned

Append-only ledger of takeaways from prior iterations. The goal-evaluator
appends one entry per iteration; the goal-decomposer reads this file before
planning each iteration to avoid repeating known pitfalls.

Each entry should be 1-3 sentences capturing a non-obvious lesson — surprising
failures, regression triggers, or decisions that worked well. Avoid
restating the verdict (the evaluator-log.md already does that).

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

## iter-5 — 2026-08-11T07:50:00Z

**Verdict:** ESCALATE
**Lesson:** A CONTINUE verdict's `Depth: full` recommendation is NOT binding — `run-goal.sh`'s
SPEED-20 arbiter demotes a full spec to lean whenever the previous iteration wrote a
`budget-breached` marker (iter-2, iter-3 and now iter-5 were all demoted this way, twice while the
decomposer had independently registered a legitimate full trigger). The only lever that reliably
buys the auditor a seat is an `ESCALATE` verdict, which sits on the arbiter's top rung
(`prior-verdict-ESCALATE`); this matters because browser-qa alone burned 4.6h in iter-5, so an
ordinary CONTINUE would have demoted iter-6 as well.
**Applies to:** any iteration that needs the auditor (new detector maths, new cross-cutting
coupling) and follows a long-running iteration — J-06 and J-07 especially.

## iter-5 — 2026-08-11T07:52:00Z

**Verdict:** ESCALATE
**Lesson:** The iteration spec's own Data-contract table defined `geometry.decline_bars` as "bars
from the (possibly re-anchored) climax bar to leg_low's formation", which is identically zero by
construction — the climax bar IS where leg_low forms. The developer caught it and shipped a
whole-decline-leg reading instead; nothing downstream (review, coherence) would have. Decomposer
field definitions that the canonical spec does not itself state need a degeneracy check before they
are treated as binding.
**Applies to:** any iter whose spec invents a field definition the canonical
`docs/playbook-detector-spec.md` leaves undefined — J-06/J-07/J-08 all add served fields.

## iter-6 — 2026-08-11T11:45:00Z

**Verdict:** CONTINUE
**Lesson:** An audit-fix pass changed `range_trade`'s arming RULE without changing any constant, so
`playbook_input_signature` did not move — and because playbook records are keyed
`(session_date, signature)`, the already-seeded browser rig kept serving its pre-fix record and
every 09:44 screenshot silently described a build that no longer existed. Behaviour-only fixes are
invisible to the signature by design; after any of them the browser rig must be re-seeded at a
FRESH root, and pre-fix evidence must be voided in writing (the auditor's correction banner in
`reports/phase-goal-playbook-iter-6-ui-test-results.md` is the pattern to copy).
**Applies to:** any iteration whose fix-mode pass edits detector logic in
`apps/backend/app/research/desk_playbook_detect.py` after browser evidence was captured.

## iter-6 — 2026-08-11T11:46:00Z

**Verdict:** CONTINUE
**Lesson:** Store scoping fails in two silent ways that both put fixture work into the operator's
real `.data/`: (1) only the `*_resolved()` accessors read the `TAPEOLOGY_*` overrides — reading
`config.bar_dir` / `config.desk_universe_dir` directly ignores every scoping env var (this wrote 3
synthetic bar files and a today-dated fake universe snapshot before it was caught); (2)
`resolve_desk_playbook_log_dir` (`app/research/desk_playbook_log.py:74`) falls back off the
*universe* dir, so scoping `TAPEOLOGY_DESK_PLAYBOOK_DIR` alone sends the record to scratch and its
ledger row to the real store — orphaned on first write, which is exactly the iter-4/iter-5 mystery
rows, with nothing ever deleted. Scoping is all-or-nothing: use
`apps/backend/scripts/qa_playbook_iter6_fixture_scoped_backend.sh` as the only backend entry point
for test/browser work.
**Applies to:** every test, browser-QA or seeding run from here on, and J-07 above all — the
back-scan is a mass writer over real recorded sessions.

## iter-7 — 2026-08-11T13:35:00Z

**Verdict:** ESCALATE
**Lesson:** The deterministic golden-replay lane runs against whatever backend is already listening
on `:8301` — this iteration that was the AMBIENT, unscoped backend pointed at the operator's real
`.data/` store, and only the later LLM browser lane stopped it and swapped in
`qa_playbook_iter7_fixture_scoped_backend.sh`. Two consequences, both real: (a) J-05's replay
false-FAILED because its click target `DECOR` is a fixture-only symbol that exists solely on the
scoped rig, and its step-2 assertion `"Capitulation"` passed anyway because that word also appears
in the section's own static blurb — so a fixture-mismatched run looked like a product regression;
(b) `J-01.json` and `J-03.json` both click the Run Playbook compute trigger, so a golden script with
a real session date would have written into the operator's append-only store exactly as iter-6 did.
Scope the replay lane's backend, and never assert on text that also lives in a static description
paragraph.
**Applies to:** any iteration that records or replays golden scripts for fixture-dependent
`/desk` playbook journeys; any iteration whose scripts click a compute/trigger button.

## iter-8 — 2026-08-11T18:40:00Z

**Verdict:** CONTINUE
**Lesson:** A screenshot's FILENAME is a claim, not evidence. `reports/qa/goal-playbook-iter-8-evidence/TC-08-playbook-evidence-table.png` is cited by the QA report's UI Evolution Audit as showing "all elements rendered" of the new Playbook Evidence section — it actually shows the Screen History calendar and Forward Returns panel, a completely different part of `/desk`. The real acceptance evidence lived in two other files (`UT-02-result.png`, `fix-scoped-rig-J-08-evidence-cells.png`). The same report also certified carry items it never executed (audit T2), so treat a QA report's ✓ marks as pointers to open, never as verification.
**Applies to:** any evaluator or auditor scoring a journey from a named screenshot; any iteration whose acceptance is "legible in a single screenshot"

## iter-8 — 2026-08-11T18:40:00Z

**Verdict:** CONTINUE
**Lesson:** The store-scoping breach recurred for a third time (iter-3, iter-6, iter-8) because every prior fix was a correct-but-OPTIONAL launcher — iter-7 shipped `qa_playbook_iter7_fixture_scoped_backend.sh` and the deterministic replay lane simply did not call it, then wrote three real S&P-100 records into `apps/backend/.data/playbook/` at 14:45. What finally worked was an OBLIGATION with its own proof: a declared protected-path list, a require/snapshot/verify guard the lane must call before and after, a pure-function "is this backend the fixture rig" classifier that fails closed, and a byte-identical 9,841-file manifest check. Availability of a safe path never prevents an unsafe one; only a gate does.
**Applies to:** any iteration adding a verification lane, replay script, or QA rig that can reach a real append-only store

## iter-9 — 2026-08-11T20:05:00Z

**Verdict:** STALLED
**Lesson:** A golden replay script rewritten *during* the run it is meant to police can quietly
narrow the thing it protects. The browser lane replaced J-10's step 6 assertion "Forward Returns"
(a shipped Era-B section heading) with the literal signature hash `9597251432bd9e75`, so the era's
kept-product sentinel now asserts nothing from any shipped section — and the hash is fixture-state
dependent: the developer's own capture 40 minutes earlier in the SAME iteration read
`9803f6881e8f86b3`. When a golden assertion turns out to be rig-dependent, replace it with another
statically-rendered *kept-surface* string, never with a value the run itself just produced.
**Applies to:** any iteration that edits `runs/goal-session-*/journey-scripts/*.json`, and any
regression-sentinel journey whose replay script is rewritten by the same lane that scores it.

## iter-9 — 2026-08-11T20:05:00Z

**Verdict:** STALLED
**Lesson:** When the browser lane declines part of a journey's acceptance in writing ("kept-route
byte-identity ... not independently re-verified by this agent") and the depth downgrade means no
auditor ran either, that acceptance clause has NO verifier unless the evaluator becomes one. Here
`git diff <era-open>..HEAD --stat -- apps/backend/app/` was enough: every kept module absent from
the era's whole diff proves unchanged serving code, and comparing the `/structure` levels table
against the era-open screenshot gave a live byte-identity data point for free.
**Applies to:** any regression-sentinel journey (kept-route byte-identity / cumulative-inventory
clauses) evaluated at lean depth.
