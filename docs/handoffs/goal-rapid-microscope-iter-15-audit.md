# goal-rapid-microscope-iter-15 Audit Report

**Date:** 2026-08-19
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

J-08's second half genuinely lands: the four new MCP tools are verbatim `response.text`
pass-throughs (byte-identity re-proved by me on a 3-universe / 5-withheld-shard fixture the
shipped tests never build), the widened Microscope Readiness panel discloses nothing its own
already-audited endpoint does not, and all four iteration-14 defects are fixed — each one now
confirmed by a LIVE render of real seeded data, which no prior lane in this iteration achieved
(the browser lane substituted a `window.fetch` response for TC-7, read source for TC-8, skipped
TC-10's unavailable branch, and explicitly SKIPPED the non-zero-fixture pass entirely).

One IMPORTANT defect was found and fixed: the round's own opaque-pool-critical regression test —
`test_tr2_the_new_mcp_tools_leak_nothing_about_a_sealed_shard` — sealed its shard under an
**unregistered** universe, so `vault._serialize_universe` never executed and the sweep was
provably blind to a committed universe's `symbol_rule`/`date_rule` contents leaking onto the MCP
surface (mutation-proved both ways below). TC-4's own scenario line requires a *registered*
universe; the shipped test did not meet that precondition. The remaining gaps are pre-existing or
harness-scope and are documented, not fixed.

---

## 2. Findings

### Backend Findings

**B1 — IMPORTANT (fixed): the new MCP TR-2 sweep was structurally blind to a committed
universe's rule contents — it never registered a universe at all**

`apps/backend/tests/test_mcp_server.py:1188-1195` (pre-fix) sealed the distinctive shard under
`universe_id="starter-tranche-v1"` **without ever calling `vault.register_universe`** — inherited
from `test_vault.py`'s TR-2 family, every member of which does the same (`test_vault.py:882-887`,
`:920-925`). Consequence: `desk_vault`'s `universes` list was `[]` for the entire sweep, so
`vault._serialize_universe` (`app/research/vault.py:1321-1361`) — the function that decides
whether a universe's rule is served as sizes-only (`committed`) or in full (`revealed`) — never
ran. The sweep therefore could not detect the single most direct de-anonymisation the spec names:
spec §7.5's governing trap is stated over "**the registered universe (§7.2)** plus EVERY public
artifact", and `build_vault_state`'s own docstring records that serving the rule beside
`GET /research/datasets` is "a full de-anonymisation from two public GETs". TC-4's scenario line
("a distinctive sealed shard recorded under a **registered universe** whose original pool is not
yet fully released") states the precondition the test did not meet.

*Mutation proof, both directions* (production code temporarily patched to serve
`symbol_rule`/`date_rule` in the `committed` branch of `_serialize_universe`, then restored and
sha256-verified):

| test shape | vault | result |
|---|---|---|
| pre-audit (unregistered universe) | **leaking** | `tests=1 failures=0` — **blind, passes** |
| post-audit (registered universe) | **leaking** | `failures=1` — `tool 'desk_vault' serves the sealed shard's symbol` + `… session date` |
| post-audit | clean | `tests=1 failures=0` — passes |

*Fix applied* (test-only, confined to that one function): register `starter-tranche-v1` with
`symbol_rule=[_SWEEP_SYMBOL]` / `date_rule=[<sealed session date>]` before sealing; add the bare
session date to `forbidden_substrings` (the pre-existing window tokens are full timestamps and
would not catch a date-only disclosure); add five non-vacuity assertions that the universe really
is on the served surface in its `committed` stage with no `symbol_rule`/`date_rule` key. Test
count unchanged (61 in `test_mcp_server.py`); full suite unchanged.

**B2 — OBSERVATION: `sealed_tranche` and the Vault shard list count different populations, so
their difference is derivable — but it identifies nothing**

`micro_readiness.build_readiness` counts every member of an unresolved pool
(`vault.unresolved_pool_universe_by_dataset_id`, i.e. ledger-sealed **or** rule-matched),
`app/research/micro_readiness.py:371-384`, while `build_vault_state` lists only ledger-tracked
shards (`app/research/vault.py:1364-1400`). With this iteration the two are now readable on one
screen. I built exactly that state (universe `audit-tranche-alpha`: 3 ledger-sealed + 1
rule-matched-only member) and confirmed a reader can derive "4 withheld, 3 of them vault-sealed".
That is a count-level fact, not an identity: I verified the rule-matched-only member is refused by
`GET /research/datasets/{id}` ("this dataset is sealed in the validation vault…"), absent from the
`datasets` list, and carries no per-shard row in readiness. §7.5 point 7's governing test ("no
still-unexposed shard identifiable with certainty") holds. Recorded for the record only.

### Frontend Findings

**F1 — GAP (pre-existing, iteration-14 code — not fixed, out of this iteration's scope):
one malformed Scout trial row takes down the entire `/desk` page**

`apps/frontend/app/desk/page.tsx:6315` reads `{trial.feature.name} / {trial.feature.transform}`
with no defensive read, and there is no error boundary around the section. I reproduced this
live: seeding a Scout ledger row through `ScoutLedger.append_row` with the same sparse field set
the iteration's own `test_desk_scout_tool_byte_identical_on_a_populated_state`
(`tests/test_mcp_server.py:1108-1117`) uses replaced the whole page with *"Application error: a
client-side exception has occurred"* —
`Uncaught TypeError: Cannot read properties of undefined (reading 'name') … at
ScoutLedgerSection (page.tsx:11396)`.

Attribution and severity, honestly: line 6315 is unchanged by this iteration
(`git show HEAD:…page.tsx:6239` is identical), and the only production writer,
`scout.register_and_screen_candidate` (`app/research/scout.py:1149-1166`), always writes the full
`spec_fields`, so no shipped code path can produce the crashing shape today. What makes it worth
recording is that this section deliberately renders `chain_verification` to surface a **tampered**
ledger ("a reader is handed the corruption, never denied the evidence" — `micro_routes.get_scout`
docstring), and a tampered row that drops a field would crash the page *before* that verdict could
be shown. I was unsure between GAP and IMPORTANT and chose GAP because no DoD item covers it and
no production writer can reach it; fixing it here would be scope creep.

**F2 — GAP (not fixed, out of scope): `MicroReadinessSection` still drops its section testid in
the loading/unavailable states — the exact inconsistency this iteration fixed on its sibling**

`page.tsx:5892` and `:5896-5898` return `LoadingPanel`/`UnavailablePanel` bare; only the success
path at `:5904` carries `data-testid="micro-readiness-section"`. That is precisely the shape
`ValidationVaultSection` had before this round's fix. Verified live with the backend genuinely
stopped: `validation-vault-section` ✓, `scout-ledger-section` ✓, `walk-forward-section` ✓,
`micro-readiness-section` **✗** (while `micro-readiness-unavailable` was present). The phase spec
names only `ValidationVaultSection`, so this is out of scope for this round — but a future
"section testid always present" guard test would fail on Readiness alone.

### Test Findings

**T1 — OBSERVATION (the reviewer's MINOR, independently checked and confirmed *not* worse than
scored): the two new `_PRICE_ARITHMETIC_FIELDS` clauses ship without a counter-test**

`tests/test_desk_ui_guards.py:326-335`. This file's convention is that every guard clause proves
it can fail (23 `…_can_fail_on_a_seeded_violation` / `…_catches_…_arithmetic` tests). I
mutation-tested the two new clauses directly against the compiled pattern: all six seeded
violations caught (`readiness.sealed_tranche.shard_count - 1`, `… .symbol_days * 2`,
`universeCounts.shard_count + universeCounts.symbol_days`, `withheld_excluded - …`,
`1 - readiness.sealed_tranche.shard_count`, `universeCounts.symbol_days / 3`), zero false
positives on the real `page.tsx`. Functionally sound; the missing proof-test is a convention gap
only. `tests/test_desk_ui_guards.py` re-run fresh: 99 passed, 0 failed.

**T2 — OBSERVATION: J-02–J-05's replay evidence is four byte-identical screenshots from
single-step scripts**

`reports/qa/goal-rapid-microscope-iter-15-evidence/J-0{2,3,4,5}-verify.png` all hash to
`28403a00c2da3d7ec9b3b0957a9afe93`. Their scripts
(`runs/goal-session-rapid-microscope/journey-scripts/J-0{2..5}.json`) are one step each —
`goto /desk` plus one collapsed-section heading assertion ("Top-up Runs", "Index Reconciliation",
"Screen Runs", "Playbook Signals"). TC-13 asks that every cited evidence file exist on disk; all
six do, and J-01 (2 steps) and J-10 (13 steps) are substantive. But "6/6 journeys passed" carries
much less regression weight for J-02–J-05 than the row implies. Harness scope — the phase spec
lists harness issues as explicitly OUT OF SCOPE.

---

## 3. Domain Assessment

**The opaque-pool question, answered by construction and by experiment.** `call_tool`
(`app/mcp/__init__.py:610-620`) hands back `response.text` with no parse/re-serialize step, and
all four new tools are plain `_STATIC_PATHS` entries — no reshaping, enrichment, join or
flattening exists anywhere on the new surface, so it cannot disclose more than the four
already-audited REST routes. I did not take that on trust. I built an isolated fixture store far
harder than any shipped test uses — **3 registered universes (2 `committed`, 1 whole-pool
`revealed`), 4 ledger-sealed shards across 2 universes, 1 shard driven sealed→assigned→exposed,
and 1 member withheld by rule-match alone** — and swept all 26 tools plus 19 adversarial
`get_endpoint` probes (including direct `/research/datasets/{sealed_id}` and `…/events` lookups)
against 20 forbidden tokens and 15 forbidden integers.

Result: **zero disclosures.** No sealed symbol (`ZQXVLT`/`WKPQJRX`/`XVBNMQ`), dataset id, raw
checksum, window bound, or exact trade/quote count appears in any tool body. The only flagged
strings were the caller's own path echoed back in the MCP status note (`HTTP 403 from GET
/research/datasets/<id>`) — the attacker's own input, and the refusal body itself is the typed
§7.5 point-3 message carrying nothing else. Byte-identity re-proved on that same rich state:
`desk_micro_readiness` (2478 B), `desk_scout` (2633 B), `desk_walkforward` (2816 B), `desk_vault`
(3098 B) — all `byte_identical=True`, `isError=False`. Ordered slice confirmed live:
`desk_referee, desk_referee_registry, desk_micro_readiness, desk_scout, desk_walkforward,
desk_vault, pnl_ledger`, `len(TOOL_NAMES) == 26`.

**The widened panel is a true twin of its endpoint.** The new markup interpolates five served
values and nothing else; there is no symbol, session date, dataset id, checksum, or per-shard
`exposure_state` in it. I rendered it against the non-zero fixture — the first live render of that
path in this iteration — and swept the whole `micro-readiness-section` subtree: no withheld
symbol, id, checksum or session date in HTML or text. The one substring hit (`137`) is the public
PG shard's `137,579` bytes. The per-universe aggregate cannot be joined against the vault's
`symbol_rule_size`/`date_rule_size` because `_serialize_universe` withholds rule *contents* until
whole-pool release — the property B1's fix now protects with a regression test.

**Frozen rails hold.** All seven `referee_*.py` + `micro_chain_ledger.py` SHA-256 hashes match the
iteration-0 baseline byte-for-byte; `Config().config_fingerprint()` → `08e471b10130e1e2`;
`git diff` reports zero changes across those seven plus `vault.py`, `scout.py`, `walkforward.py`,
`micro_routes.py`, `micro_readiness.py`, `config.py`. Exactly the five spec'd files are modified.
No new `Config` field, no new HTTP verb, no `_request_path` change, no new dependency. Nothing was
invented that neither the spec nor an owner ruling states (T-1 clean). The operator's real `.data`
store is untouched: `micro_vault` and `micro_scout` do not exist, `datasets` still holds its 18
files, and no entry under `.data` was modified during this audit.

**DEFINITION OF DONE — full trace where risk lives, cited acceptance where two lanes already
executed it:**

| # | Item | Verdict | Basis |
|---|---|---|---|
| 1 | 26 tools, ordered; `EXPECTED_TOOLS`/`TOOL_NAMES` match; docstring names all four | MET | **Full trace** — live `TOOL_NAMES` slice + docstring read (`app/mcp/__init__.py:20-26,146-152`) |
| 2 | Four tools byte-identical, empty + populated (TC-2/TC-3) | MET | **Full trace** — my own live byte-diff on a 3-universe/5-withheld-shard state, plus 61/61 in `test_mcp_server.py` |
| 3 | Extended TR-2 sweep over 26 tools (TC-4) | MET **after B1 fix** | **Full trace** — my 26-tool + 19-probe sweep; shipped test hardened and mutation-proved |
| 4 | Readiness renders `sealed_tranche` + `withheld_excluded`, aggregate-only (TC-5/TC-6) | MET | **Full trace, live** — on-screen `4 / 3 / 4` and `alpha 3,2 · beta 1,1` byte-match the served JSON; subtree sweep clean |
| 5 | Walk-Forward nesting fixed, zero new console errors (TC-7) | MET | **Full trace, live** — `<details>` parent is now `DIV`, opened on a real seeded sequence: 0 console errors/warnings, no "Issues" badge, `<pre>` renders the verdict JSON |
| 6 | `family_root_id` (TC-8); WF empty copy (TC-9); Vault testid (TC-10) | MET | **Full trace, live** — header renders `audit-family-ORB-01 (root 99d7cabbbd54ada5) — 3 variants tried`; TC-10 verified with the backend genuinely **stopped**, wrapper present in the unavailable branch; TC-9 by diff (`page.tsx:6520`) + QA's live observation (QA report §3) |
| 7 | J-07 re-verified (TC-11) | MET | `tests/test_micro_graduation.py` re-run by me: 19 passed / 0 failed; `GET /research/desk/micro/graduation` → HTTP 200 with the stage vocabulary, re-confirmed live |
| 8 | J-01–J-05, J-10 green with real evidence (TC-13) | MET (see T2) | All six cited PNGs exist on disk; J-02–J-05's evidence is thin |
| 9 | No anti-goal violation; auditor re-sweeps MCP + panel | MET | §3 above — the sweep is this report's core work |
| 10 | Zero client-side arithmetic (TC-12) | MET | Guard re-run (99 passed) + my own mutation test of the two new clauses |
| 11 | Frozen rails (TC-14) | MET | Hashes + fingerprint + zero-diff re-verified by me |
| 12 | Suite ≥3228 collected, 0 failures; `tsc` clean (TC-14/TC-15) | MET | My own `--junitxml`: **3237 tests / 0 errors / 0 failures / 8 skipped** (and identical after my fix); `npx tsc --noEmit` exit 0 |
| 13 | Dev handoff + audit report exist (TC-16) | MET | Both on disk |

---

## 4. Fixes Applied During This Audit

| # | Severity | File | Change |
|---|----------|------|--------|
| 1 | Important | `apps/backend/tests/test_mcp_server.py` | `test_tr2_the_new_mcp_tools_leak_nothing_about_a_sealed_shard`: register `starter-tranche-v1` in the universe ledger before sealing (TC-4's own stated precondition), add the sealed shard's bare session date to `forbidden_substrings`, add five non-vacuity assertions that the universe is served in its `committed` stage with no `symbol_rule`/`date_rule` key. Docstring updated to state the reasoning. |

Post-fix verification: `tests/test_mcp_server.py` → **61 passed / 0 failed** (junitxml); full suite
after the fix → **3237 collected / 0 failures / 8 skipped**, identical to before; mutation test
proves the hardened assertion genuinely fails on a leaking `_serialize_universe` and that the
pre-fix shape passed the same mutation; both temporarily-patched files restored and sha256-verified
identical; diff confined to the single test function, no production code touched.

---

## 5. Recommended Next Step

**Proceed.** J-08 is complete end to end and this round's two opaque-pool-critical surfaces are
clean under adversarial probing far beyond what the shipped tests exercise. Carry forward, not
into this round:

1. **F1** — give `ScoutLedgerSection` (and its siblings) a defensive read or an error boundary so
   a corrupt ledger row surfaces the chain-verification failure instead of blanking `/desk`. This
   is the one finding with real teeth; it is iteration-14 code and belongs in its own small round.
2. **F2** — keep `micro-readiness-section` present in the loading/unavailable branches, matching
   the three siblings; cheap, and it makes a future "section testid always present" guard viable.
3. **T1** — add the seeded counter-test for the two new `_PRICE_ARITHMETIC_FIELDS` clauses.
4. **T2** — J-02–J-05's journey scripts assert one collapsed heading each; the next evaluator
   should not read "6/6 passed" as meaningful regression cover for those four.
5. Consider back-porting B1's registered-universe precondition to `test_vault.py`'s own TR-2
   family, which has the identical blind spot on the REST side.
