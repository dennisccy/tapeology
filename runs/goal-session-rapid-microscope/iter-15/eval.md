# Iteration 15 Evaluation

**Verdict:** ESCALATE
**Depth Recommendation For Next Iteration:** full

## Summary

J-08 "The surface and MCP v6" is finished. The four Desk panels built last round now have their
four matching read-only conversation tools, the tool list grew from 22 to 26, and the readiness
panel finally shows the two hidden-batch numbers it had been throwing away. I checked every part
of that myself instead of reading the reports: I opened the pictures, ran the whole test set
(3,237 collected, 3,229 passed, 8 skipped, 0 failures), ran the tool tests (61, all pass), and
re-read the frozen parts by hand. J-07 "Graduation" was properly re-checked at last, after two
rounds where it was dropped for time. The most important thing this round is not a product fault
at all: the round's own safety test — the one written to prove the four new tools cannot reveal a
hidden recording — was set up in a way that made it unable to notice the very leak it existed to
catch. The independent checker proved that both ways, then fixed it. Nothing was actually
revealed, but a safety test that passes for the wrong reason is the worst thing that can hide in
this project, and the next round is entirely made of safety tests.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 The era transition stands | passing | passing | reports/qa/goal-rapid-microscope-iter-15-evidence/J-01-verify.png; reports/qa/goal-rapid-microscope-iter-15-evidence/UT-02-result.png (opened — full readiness panel, totals, floors, no integrity errors) |
| J-02 The micro observer | passing | passing | reports/qa/goal-rapid-microscope-iter-15-evidence/J-02-verify.png (opened — thin one-step replay; md5 identical to J-03/04/05) |
| J-03 Structure x flow | passing | passing | reports/qa/goal-rapid-microscope-iter-15-evidence/J-03-verify.png (same thin replay) |
| J-04 The Scout and the ledger | passing | passing | reports/qa/goal-rapid-microscope-iter-15-evidence/UT-05-result.png; UT-07-partA-result.png (opened — Scout section renders, chain ok, honest empty) |
| J-05 The walk-forward engine | passing | passing | reports/qa/goal-rapid-microscope-iter-15-evidence/UT-06-result.png; UT-07-partA-result.png (opened — "No walk-forward sequences run." live) |
| J-06 The recorder and the Vault | partial | partial (not re-verified; out of scope by the phase spec) | no fresh evidence; zero backend research files changed — evaluator confirmed via `git status` |
| J-07 Graduation | passing (stale stamp, deferred twice) | passing — genuinely re-verified, stamp refreshed | reports/qa/goal-rapid-microscope-iter-15-evidence/UT-10-result.png (opened — HTTP 200, honest-empty body verbatim) + evaluator's own `tests/test_micro_graduation.py` run, 19/19 |
| J-08 The surface and MCP v6 | partial | **passing** | reports/qa/goal-rapid-microscope-iter-15-evidence/UT-07-partA-result.png (opened — all four sections), UT-02-result.png (opened — served values byte-matched to curl), UT-11-result.png; evaluator's own `tests/test_mcp_server.py` run, 61/61 |
| J-09 The pilot studies | failing | failing (out of scope; confirmed unbuilt on disk by the evaluator) | no pilot-study module under `app/research/`; Scout Ledger reads "No candidates ledgered." in UT-05 |
| J-10 The kept product stands | partial | partial (sentinel green, traps 24 of 29 by the evaluator's own count) | reports/qa/goal-rapid-microscope-iter-15-evidence/J-10-verify.png, UT-09-cockpit-result.png, UT-09-result.png (all opened) |

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| Secrets/credentials | OK | `iter-15/scan-report.md` CLEAN on added lines. The only secret-shaped literals in the diff are test fixtures (`b"mcp-test-vault-secret"`, `_FIXTURE_SECRET` imported from `test_vault.py`) — never the real `TAPEOLOGY_VAULT_SECRET_FILE`, which is untouched. No env/config file in the diff. |
| Paid/external SaaS · new dependency | OK | No manifest changed — `git status` shows exactly 5 product files, none of them `package.json`/`requirements*`/`pyproject.toml`. The four new tools are HTTP proxies of local routes. |
| License changes | OK | scan-report CLEAN; no LICENSE file in the diff file list. |
| Fabricated/substituted data | OK | No new data path. The new UI numbers come straight from `GET /research/desk/micro/readiness`, which is byte-unchanged; UT-02 cross-checked the on-screen values against a curl of that endpoint. Honest-empty everywhere (`sealed_tranche` all zero, "No sealed shards recorded.", "No candidates ledgered."). |
| No execution path, ever | OK | No brokerage/order code in the diff; `test_no_execution_path.py` green inside the evaluator's own full-suite run (3237/3229/8/0). |
| No profit claims / no advice | OK | New copy is descriptive only ("Sealed shard count", "Sealed symbol-days", "Joinable corpus — withheld (excluded)", "A recorded tranche is one opaque pool until its shards are exposed…"). `test_copy_discipline.py` green in the same run. |
| Frozen foundations | OK | Evaluator re-derived: `Config().config_fingerprint()` = `08e471b10130e1e2`; all six `referee_*.py` SHA-256 identical to the iteration-0 baseline listing in `docs/handoffs/goal-rapid-microscope-iter-0-dev.md:75-81`, plus `micro_chain_ledger.py`; zero new `Config` fields; no engine file in the diff. |
| Read-only MCP | OK | All four new entries are `_STATIC_PATHS` GET proxies dispatched by the unmodified generic `call_tool` → `_proxy_get`; no new verb, no per-tool logic. Byte-identity proved on empty AND seeded states by 8 tests the evaluator ran. |
| One opaque research pool (spec r5) | OK | New markup is aggregate-only: two totals, one withheld count, and a per-**universe** (not per-shard) breakdown — evaluator read the diff and the rendered screenshot. The 26-tool TR-2 sweep asserts zero disclosure of a sealed shard's dataset id, raw checksum, symbol, window bounds, session date and exact counts, with five non-vacuity assertions (`test_mcp_server.py:1260-1303`); evaluator read them and ran the test. |
| No exploratory read of a sealed shard | OK | Same sweep; the `datasets` tool serves 2 public siblings with the sealed one excluded. No product module that touches sealed data changed. |
| Evidence classes never mix | OK | No class-bearing computation added; `walkforward.py`/`scout.py`/`micro_readiness.py` byte-unchanged. |
| Denominator never shrinks | OK | Scout ledger code untouched; the change is one extra field (`family_root_id`) in a header. |
| Accessor is the only data door | OK | No new `open()`/`sqlite3.connect` in product code; the guard tests are green in the full-suite run. |
| 12 legacy symbol-days permanently exploratory · ~150-day gate never lowered | OK | On screen in UT-02/J-10-verify: legacy shards `hand_assigned`, referee tick-gate 150 shown unmet, all three study floors `floor_unmet` at 1 available vs 60 required. |
| Referee modules byte-untouched | OK | Hash listing verified above. |
| Proposer stays inside its marker block | OK | `docs/goal.md` is not in `git status`; no `journeys-changed.md` exists for this iteration. |
| Host-guard caps | OK | No change to the host-guard config; no cap widened. |
| **Guard-quality (this round's finding)** | **MINOR — fixed in-round** | The round's own TR-2 sweep sealed its shard under an *unregistered* universe, so `vault._serialize_universe` never ran and the sweep could not see a committed universe's rule leaking. Mutation-proved both directions by the independent checker and fixed test-only. No disclosure ever occurred. Ledgered as `iter-15`, minor, resolved. |
| **Guard-quality (open)** | **MINOR — open** | The two new `_PRICE_ARITHMETIC_FIELDS` clauses ship with no seeded-violation counter-test, against this file's own convention. Mechanically proved working (six seeded mutations all caught); only the standing proof is missing. Ledgered as `iter-15`, minor, unresolved. |

Coherence: **COHERENCE-WARN** (not FAIL) — `MicroReadinessSection` still drops its section testid
in its loading and unavailable states, the exact inconsistency this round fixed one section over.
No structural veto; carried as a passenger item below.

## Next-Step Recommendation

Do the leakage-trap round next, as a FULL round with the independent checker. That is why my
verdict line says "escalate" and not "continue": in this session a request written only in prose
has been cut for time twice (round 11 asked for a full round in words and round 12 was downgraded
to a light one), and the record shows only the verdict line is honoured.

The reason it matters here is exact, not general. Five safety tests are still missing — the ones
that prove the data door refuses to read past its own date, that a question asked too late is
automatically marked "already seen", that nobody can claim a sealed result passed by simply
saying so, that a killed sibling's knowledge cannot be laundered into a survivor's paperwork, and
that a liquidity reading is stamped at the quote that actually reveals it. Those five ARE the
remaining work of J-10 "The kept product stands", and this round just proved, on its own new
test, that a safety test can look green while being unable to fail. Only the independent checker
found that, by attacking the test rather than reading it — the seventh time in this session it has
caught something after the review and the quality check both passed the same code.

Split it in two so the round stays small enough that the clock cannot drop the checker. Round 16:
the data-door fence, the "asked too late" rule, and the liquidity timing stamp — that last one
also closes a small item that has been open since round 2. Round 17: the sealed-verdict ownership
test and the killed-sibling boundary test, which belong together.

Carry three small passengers, never a round of their own: make the readiness panel keep its
section marker while loading or unavailable (the one reason this round's coherence check is a
warning, and a two-line fix already proven one section over); make the Scout table survive a
damaged row instead of blanking the whole Desk page (there is no error boundary anywhere on that
page, and I confirmed a second undefended read beside the one the checker found); and add the
small proof-test for the two new number guards.

Do NOT record real tape yet, and do not start J-09 "The pilot studies" first — one of the five
missing safety tests is the one that keeps J-09's own questions honest by marking a question
asked too late, so it must exist before the studies are written down. Nothing waits on your
answer. One thing would still help if you agree with it: tell the machine that when I ask for a
full round with the independent checker, that request cannot be cut for time.

## Halt Justification (if halting)

Not halting — ESCALATE only sets the next round's depth.
