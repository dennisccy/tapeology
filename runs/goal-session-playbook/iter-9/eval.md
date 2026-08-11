# Iteration 9 Evaluation

**Verdict:** STALLED
**Depth Recommendation For Next Iteration:** full

## Summary

The building work of this era is finished. All ten journeys now pass, and I checked the two new
ones myself rather than trusting the write-ups: Claude can now reach the playbook and its evidence
table (20 tools, up from 18), and the whole kept product — the Cockpit tape, the Structure page,
and every Desk section — still works. The era is not being declared done, for one reason only:
two questions the owner was asked in iteration 6 are still unanswered, and one of them can change
what the product ships. No further machine work can answer them, so the loop stops here and hands
them over.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 The signal contract | passing | passing (replay re-verified) | reports/phase-goal-playbook-iter-9-ui-test-results.md (UT-J-01 row) |
| J-02 Every signal measured | passing | passing (replay re-verified) | reports/phase-goal-playbook-iter-9-ui-test-results.md (UT-J-02 row) |
| J-03 The Playbook lands on /desk | passing | passing (replay re-verified) | reports/phase-goal-playbook-iter-9-ui-test-results.md (UT-J-03 row) |
| J-04 The continuation family | passing | passing (replay re-verified) | reports/phase-goal-playbook-iter-9-ui-test-results.md (UT-J-04 row) |
| J-05 The climax family | passing | passing (replay re-verified) | reports/phase-goal-playbook-iter-9-ui-test-results.md (UT-J-05 row) |
| J-06 The range family | passing | passing (replay re-verified) | reports/phase-goal-playbook-iter-9-ui-test-results.md (UT-J-06 row) |
| J-07 The back-scan | passing | passing (replay re-verified) | reports/phase-goal-playbook-iter-9-ui-test-results.md (UT-J-07 row) |
| J-08 The evidence view | passing | passing (replay re-verified; its own golden script landed this iteration) | reports/phase-goal-playbook-iter-9-ui-test-results.md (UT-J-08 row); runs/goal-session-playbook/journey-scripts/J-08.json |
| J-09 MCP contract v4 | failing | **passing** | UT-J-09 row + evaluator's own live check: `app.mcp` exposes exactly 20 tools including `desk_playbook`/`desk_playbook_evidence`; `EXPECTED_TOOLS` = 20; the empty-state, populated-state and `?date=` proxy byte-identity tests all pass inside the evaluator's own full-suite run |
| J-10 The kept product stands | partial | **passing** | reports/qa/goal-playbook-iter-9-evidence/J-10-cockpit-simtape.png, J-10-structure-aapl.png, J-10-desk-top.png, J-10-desk-screenhistory-forward.png, J-10-desk-briefing-skipped-crop.png, J-10-desk-runs-provenance-crop.png, J-10-desk-playbook-signals-backscan-crop.png, J-10-desk-evidence-signature-crop.png |

### What the evaluator verified first-hand (not read from a report)

- **Full backend suite, run to completion by me:** exit 0, **2163 passed / 8 skipped / 0 failed**
  (character-counted from the raw progress output). Clears the iteration-8 floor (2158) and the
  era-open floor (1926); skip count is exactly 8.
- **Pin unchanged:** `Config().config_fingerprint()` → `08e471b10130e1e2`, and the same string is
  legible in the Provenance panel screenshot.
- **MCP surface:** 20 tools live from the running module, both new names mapping to
  `/research/desk/playbook` and `/research/desk/playbook/evidence`.
- **Zero-diff files:** `desk_forward.py`, `desk_playbook_detect.py`, `desk_playbook.py`,
  `docs/playbook-detector-spec.md`, `docs/goal.md`, `config.py`, `meta.py`,
  `test_no_execution_path.py` — all empty diffs.
- **J-10 step 3/4 (kept-route byte-identity + cumulative inventory), which nobody else checked:**
  the browser-QA agent declined it in writing ("not independently re-verified by this agent") and
  no auditor ran, so I re-derived it. Across the WHOLE era (`ed87dca..HEAD` plus the uncommitted
  tree) the backend app diff touches only the seven new `desk_playbook*` modules, `desk_routes.py`
  (+405/-1, the one deletion being an import line replaced by a longer import list) and
  `app/mcp/__init__.py`. Every kept module — `bars.py`, `levels.py`, `tradability.py`, `setups.py`,
  `edge_report*.py`, `backtests.py`, `profiles.py`, `desk_universe.py`, `desk_screen.py`,
  `desk_forward.py`, `desk_sessions.py`, `desk_meta_cache.py`, `desk_topup*.py`, `config.py`,
  `meta.py`, `main.py` — is absent from the diff, so their served output cannot have changed.
  Non-playbook test files touched across the era are exactly the three named guard-test extensions
  plus `test_mcp_server.py` (the goal's own declared MCP exemption).
- **Live byte-identity data point:** I compared the `/structure` pinned-AAPL levels table in this
  iteration's screenshot against the era-open capture
  (`reports/qa/goal-playbook-iter-0-evidence/J-10-structure-aapl.png`) row by row. Every band,
  score and member count matches exactly (resistance 300.11–302.2 / 171 / 849; 308.63–310.79 /
  100.81191222570533 / 1348; support 224.06–225.62 / 818.4388714733542 / 1097; and the rest).
- **Frontend deletions are not removals:** `apps/frontend/app/desk/page.tsx` shows −112 lines over
  the era; every shipped test id I sampled (`desk-screen-basis-note`, `desk-viewing-indicator`,
  `desk-history-latest-button`, `desk-history-fetch-error`, `desk-history-pending`) is still
  present — the deletions are re-indentation.
- **Store hygiene:** `find apps/backend/.data -newermt "2026-08-11 18:13"` returned exactly one
  file, a derived sqlite sidecar (`playbook_evidence_cache.db-shm`). No playbook record, no screen
  snapshot, no ledger row was written into the operator's own store this run. The guard artifact
  agrees: 9,841 protected files unchanged.

### Findings the evaluator raised that no other agent reported

1. **The J-10 golden replay script was rewritten mid-run, and the rewrite weakens the sentinel.**
   `runs/goal-session-playbook/journey-scripts/J-10.json` step 6 changed from
   `expect: {"text": "Forward Returns"}` to `expect: {"text": "9597251432bd9e75"}`. Two problems:
   (a) the era's kept-product sentinel now asserts none of the shipped Era-B sections — it asserts
   a value this iteration just added; (b) the value is fixture-state dependent, not stable. The
   developer's own capture 40 minutes earlier (`desk-evidence-signature-crop.png`, which I opened)
   reads "Built from signature: `9803f6881e8f86b3`" with n=13/7/9 cells, while the browser-QA
   capture reads `9597251432bd9e75` with n=15/8/11. The next re-seed of the fixture rig will make
   this script fail for no product reason. The stated reason for the swap is legitimate (the old
   string does not render until a screen has been computed), but the replacement should be a
   statically-rendered kept-surface string that renders regardless of data.
2. **The eight `J-0N-verify.png` files cited as evidence are end-of-run viewport captures, not
   acceptance-state captures.** I opened two: `J-08-verify.png` shows the top of `/desk` ("Desk
   screen not computed yet"), not the evidence table; `J-04-verify.png` shows empty run panels.
   The real evidence for those eight journeys is the replay lane's step assertions plus their
   durable prior evidence (their product code is unchanged this iteration apart from one added
   line on the Desk page). The filenames should not be read as showing what they imply.
3. **The `/structure` price chart did not render this run.** The pane reads "No candles to draw for
   this timeframe" / "No recorded candle series available to draw for this symbol", whereas the
   era-open capture shows a full candlestick chart with the band overlay. This is the fixture rig's
   bar scoping, not a code change (the levels beside it are identical to era-open), but it means
   the kept `/structure` chart was not visually re-checked this iteration.
4. **The iteration was planned deep and ran fast — the fourth time this session.** The spec says
   `Depth: full` and names the auditor explicitly; `depth-dispatched` says `lean`. So the era's
   widest regression pass had no auditor, and J-10's steps 3 and 4 would have had no independent
   check at all if I had not re-derived them.
5. **The rig was left in place.** Port `:8301` is still serving the scoped fixture backend, not the
   operator's real one; the browser-QA agent's restore attempt was refused by the permission
   system. The original command line is recorded in the disclosure file it names.

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| Secrets / credentials | OK | `scan-report.md`: CLEAN, no secret findings on added lines; no new config/env file in the 9-file diff |
| Paid / external SaaS | OK | No manifest touched (`package.json`, `requirements*.txt`, `pyproject.toml` absent from the diff); the two new MCP tools proxy local routes |
| License changes | OK | `scan-report.md`: CLEAN; no LICENSE or license-field file in the diff |
| Fabricated / substituted data | OK | Every screenshot's data comes from the scoped fixture rig or the real store, labelled as such; the empty states are honest ("Playbook not computed for this session", "Every cell below is an honest absence, not a zero"); no fixture file appears in a production path |
| No execution path, ever *(critical)* | OK | `test_no_execution_path.py` byte-unmodified and green in my own suite run; the diff adds no client, order, or broker concept |
| No profit claims / no advice *(critical)* | OK | The one new UI line is "Built from signature: `<hash>`"; the register paragraph beside it is unchanged and still states what was NOT measured |
| Frozen foundations *(critical)* | OK | Every kept module absent from the era diff (verified above); pin `08e471b10130e1e2` unchanged; `/structure` levels byte-match the era-open capture |
| Hold-out-only promotion *(critical)* | OK | Champion pointer untouched; no gate, sample floor, or sweep anywhere in the diff |
| No lookahead *(critical)* | OK | No detector or measurement code changed this iteration (`desk_playbook_detect.py`, `desk_playbook.py`, `desk_forward.py` all zero-diff) |
| Single source of truth *(critical)* | OK | `coherence.md`: **COHERENCE-PASS**; the two new tools are dict-entry proxies of already-registered rows and the new UI line reads the served field verbatim |
| Deterministic and seeded | OK | No RNG or wall-clock code added. See finding 1 for a determinism weakness in a *test asset* (not product code) |
| Read-only MCP *(critical)* | OK | Both new entries are `_STATIC_PATHS` GET proxies; byte-identity proven against curl in empty and populated states; no write verb added |
| Immutable data *(critical)* | OK | No recorded file rewritten, pruned or superseded; guard artifact CLEAN over 9,841 protected files |
| Persistence stays scoped *(critical)* | OK — and the standing residual is now CLOSED | All three hardening items verified in source by me: `exit 1` on breach at both call sites (and before the checkpoint in `goal-iter-lean.sh`), `qa-phase.sh` now gated by `store_scope_require`, and `store-scope.env` no-ops outside this project |
| No threshold outside the spec, no sweeping *(critical)* | OK | `docs/playbook-detector-spec.md` and both detector modules are zero-diff this iteration |
| A signal is an observation, not a call *(critical)* | OK | No new signal, chip or cell copy; `invalidation_price` untouched |
| The evidence pools one signature *(critical)* | OK | The change makes the pooled signature *visible* on screen; the fold itself is unchanged |
| No recorded playbook file rewritten *(critical)* | OK | Verified on disk (only a derived cache sidecar was touched) |
| No second measurement rail *(critical)* | OK | `desk_forward.py` zero-diff; no measurement code added |
| Enhancement loop stays in its box *(critical)* | OK | `docs/goal.md` zero-diff |
| Host-guard caps are law *(critical)* | OK | No cap widened, disabled, or bypassed in the diff |
| **The spec is canonical — a developer never improvises a rule** | **OPEN (minor, from iteration 6)** | The `range_trade` "degenerate trigger reference" rule was written by a developer, not the owner. Still awaiting the owner's yes/no. Rejecting it means dropping range trades from the shipped setup list |
| **The spec is canonical — served behaviour matches the spec** | **OPEN (minor, from iteration 6)** | Three places where the shipped code reads the rule book more narrowly than it is written. Each is disclosed and can only produce fewer signals, never invented ones. Still awaiting the owner's ruling |

No new anti-goal violation was introduced this iteration.

## Next-Step Recommendation

Answer the two questions below, then restart the loop with `--resume`. If both answers are "yes,
keep it as shipped", nothing in the product changes and the era can be declared finished on the
next pass. Carry four small clean-up items into that pass: rewrite the J-10 replay script so it
checks a fixed piece of page furniture from a shipped Desk section instead of a hash that changes
whenever the test data is rebuilt; re-take one `/structure` picture on data that actually has price
bars so the chart itself is seen working; put port 8301 back on the operator's real backend; and
run that pass deep, with the auditor, which the plan has now asked for four times without it
happening. If the answer to the first question is "no", the range-trade setup has to be removed,
which is a real code change and needs the deep pass anyway.

## Halt Justification

I am halting because the only thing left between this era and "finished" is two decisions that
belong to the owner, and no machine step can make them. Both have been open since iteration 6 and
were deliberately left alone in iterations 7, 8 and 9.

**Decision 1 — the range-trade rule.** A developer found the rule book silent on one corner case
(it could serve a "buy" whose own invalidation price sat above the entry price). Instead of
dropping the setup, as the project's own rules say to do, he wrote a new paragraph into the rule
book and then wrote the matching code. The paragraph only ever removes signals; it never invents
one. Unblock options, all owner-only:
- (a) **Ratify it.** The paragraph stays, nothing in the code changes, the item closes.
- (b) **Reject it.** Range trades come out of the shipped setup list — the outcome the rule book
  itself sanctions. This changes what J-06 "The range family" delivers and needs one more build
  pass.
- (c) **Change `docs/goal.md`** to say that a written-down, fewer-signals-only clarification does
  not need a separate ruling — which closes the item by definition.

**Decision 2 — three narrower readings.** In three places the shipped code reads the rule book more
narrowly than it is written: which pair a double top is measured from, when the "crossed midrange"
note is shown, and two number choices (the 1.5x jump-to-base rule and which constant the cup's rim
test uses). Each is written down and each only ever produces fewer signals. Unblock options, all
owner-only:
- (a) **Accept the shipped reading** — it gets written into the rule book, no number moves.
- (b) **Ask for the wider reading** — that is a named rule-book revision, which mints new record
  versions and keeps every old record exactly as it is.

Everything else is green and was checked by hand: ten of ten journeys pass, the full test suite
runs clean at 2163 passed / 8 skipped, the pin has not moved, the coherence audit passes, the
security scan is clean, nothing was written into the owner's own records, and the era's whole code
change stays inside the list the goal declared.
