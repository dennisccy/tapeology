# goal-rapid-microscope-iter-23 Dev Handoff

**Phase:** goal-rapid-microscope-iter-23
**Date:** 2026-08-23
**Agent:** developer
**Status:** complete

## What Was Built

This iteration's IN SCOPE was almost entirely independent verification of the owner's
already-committed, self-certified J-06 work (commits `08534e8`, `76e7a70`) — not new product
code. The only intentional code change is the passenger fix listed below. Everything else is
verification evidence, gathered against the REAL `.data/datasets` store per the resolution
logged in `assumptions.md` (iter-23 entry).

- **Passenger fix**: added the missing non-vacuity assertion
  `screen_result["n_candidate"] + screen_result["n_comparator"] > 0` to
  `test_iter22_study3_capitulation_screens_with_real_playbook_signal_anchor`
  (`apps/backend/tests/test_scout.py`), mirroring Study-1's twin assertion. Verified per TC-8:
  temporarily moved `_plant_capitulation_signal`'s `trigger_ts` by `+5e9` seconds — the new
  assertion FAILS (`assert (0 + 0) > 0`); restored — the test PASSES. The perturbation was never
  committed (verified via `git diff` after restore).
- **Independent code review** of `vault.py`'s r12 additions (`VaultScreenProvenanceLedger`,
  `VaultDisclosureIncidentLedger`, the typed J-06 TR-4 verifier's primitives,
  `disclosed_pool_positions`), `micro_tier_b_screen.py`'s window-completeness fix, and
  `apps/backend/scripts/j06_operator.py` in full (836 lines) against
  `docs/rapid-validation-spec.md` r12 + §7.2.2. Cross-checked each behavior against the spec text
  line by line: collision-dominates-vendor-failure precedence, the `is_genuine_j06_dataset`
  shared predicate, the disclosure ledger's refusal of `sealed_member_identity_disclosed=True`,
  `assign_shard`'s permanent refusal of a disclosed pool position, and TR-2's re-run treating the
  disclosure as attacker-known. **No defect found** — the implementation faithfully matches the
  spec; see "Independent Verification Evidence" below for the concrete numbers that back this.
- **Full backend suite run to completion**: 3449 passed / 8 skipped / 0 failed / 0 errors (well
  above the iter-22 baseline of 3,322). See "Test Run Mechanics" for why this took three separate
  invocations instead of one.
- **Fingerprint + referee byte-freeze**: `Config().config_fingerprint()` == `08e471b10130e1e2`;
  all six `referee_*.py` SHA-256 hashes matched the era-open listing
  (`docs/handoffs/goal-rapid-microscope-iter-0-dev.md`) byte-for-byte — zero diff.
  `git diff --stat` confirms zero `referee_*` file in this iteration's own changed-files list.
- **Real-store backend GETs** (`TAPEOLOGY_DATASET_DIR`/`TAPEOLOGY_BAR_DIR` pointed at the real
  `apps/backend/.data/{datasets,bars}`, port 8302, read-only): `GET /research/desk/micro/readiness`
  and `GET /research/desk/micro/vault` both fetched and inspected against the live 80-shard J-06
  tranche — see evidence below.
- **MCP byte-identity check** against the same real-store instance: `desk_vault` proxy output is
  byte-for-byte identical to the REST `GET`. `desk_micro_readiness` content is also byte-identical
  (verified via a direct extended-timeout call replaying the exact proxy path) but the MCP tool's
  own hardcoded 10s timeout is shorter than the route's current real-store latency — see Known
  Issues.
- **TR-2 and TR-4 independently RE-RUN** (not re-read) against the live store via
  `python -m scripts.j06_operator verify` and `... tr2` — fresh processes, not reading
  `reports/j06-tranche/*.json`. Both reproduced the exact same figures as the owner's
  self-reported `acceptance.json`/`tr2-disclosure-analysis.json` (confirmed via `git diff` — only
  the `"at"` timestamp field changed, every other value byte-identical).

## Files Changed

- `apps/backend/tests/test_scout.py` — added the Study-3 non-vacuity assertion (4 lines); no
  other code touched.
- `reports/j06-tranche/acceptance.json` — timestamp-only diff, refreshed by my independent
  `verify` re-run (content otherwise byte-identical to the owner's original).
- `reports/j06-tranche/tr2-disclosure-analysis.json` — timestamp-only diff, refreshed by my
  independent `tr2` re-run (content otherwise byte-identical).

## Independent Verification Evidence

**TR-4 (typed batch verifier), re-run fresh against the live store:**
`recorded_pairs=80`, `planned_pairs=80`, `genuine_j06_recorded_pairs=80`,
`unrecovered_disclosed_vendor_failures=[]`, `legacy_collisions_present=1`,
`legacy_collisions_counted_as_j06=0`, `hmac_selected_total=21`, `sealed_shard_rows=21`,
`unsealed_selected_recorded=[]`, `duplicate_dataset_ids=0`, `duplicate_seal_rows=0`,
all four ledger chains `ok: true`, `research_gate_150_symbol_days={"have": 80, "met": false}`.
`tr4_batch_verification` = `{"ok": true, "blocking_missing_pairs": {}, "disclosed_vendor_failures": []}`.

**TR-2 (inference-certainty trap), re-run fresh against the live store:**
`any_identity_certain: false`, `unknown_positions: 79`, `still_unexposed_selected_shards: 21`
(79 ≠ 21 ⇒ `hidden_set_fully_determined: false`), `candidate_identities_per_unexposed_selected_shard: 79`
(≥ 2), `observational.genuine_j06_datasets: 80`, `observational.withheld_from_served_surfaces: 80`,
`observational.leaked_to_served_surfaces: 0`, `legacy_datasets_visible_by_design: 18`.
`no_identity_determinable_with_certainty: true`.

**`GET /research/desk/micro/readiness` (real store, port 8302):**
`sealed_tranche.by_universe["rapid-microscope-j06-starter"]` = `{"shard_count": 80, "symbol_days": 80}`;
`joinable_corpus.withheld_excluded: 80`; `totals` = `{"distinct_symbol_days": 12, "distinct_datasets": 18, ...}`
(the 12/18 legacy-corpus invariant holds unchanged — confirms no regression to the pre-existing
corpus reporting).

**`GET /research/desk/micro/vault` (real store, port 8302):** `shards` array has exactly 21
entries, all `exposure_state: "sealed"`, keyed by opaque `shard_id` only. Full key set across all
21 rows: `{checksum_commitment, exposure_state, sealed_at, shard_id, size_bucket, universe_id}` —
no `symbol`, no `session_date`, no `dataset_id` anywhere in the payload for any sealed row
(machine-checked: `'session_date' in raw.lower()` → `False`, `'dataset_id' in raw.lower()` →
`False`). `shard_ledger_chain_verification`/`universe_ledger_chain_verification` both `{"ok": true}`.

### A finding worth flagging plainly: the iter-23 spec's own TC-1/TC-3 text is imprecise

TC-1 and TC-3 (in this iteration's own "TESTING REQUIREMENTS") assert
`sealed_tranche.by_universe["rapid-microscope-j06-starter"].shard_count == 21` on the READINESS
endpoint. The actual, and I believe **correct**, served value is **80**, not 21. This is not a bug
to fix — it is the readiness endpoint correctly treating the WHOLE registered pool (all 80 pairs,
21 sealed + 59 not-selected) as opaque, per `docs/rapid-validation-spec.md`'s r5 rule and the
critical anti-goal: "no served surface ... may present a complete identity-labelled partition of
'exploratory' versus 'sealed', nor a complete per-shard list of EITHER side while any pool member
is unexposed." If readiness served `21` instead of `80`, the other 59 registered-but-visible pairs
would, by elimination, identify the sealed complement exactly — that IS the subtraction attack r5
exists to prevent. `micro_readiness.py`'s variable is literally named `sealed_shard_count`, but by
design (via `vault.unresolved_pool_universe_by_dataset_id`'s rule-membership test (b)) it counts
every withheld POOL member, not just ledger-sealed ones — this predates J-06's real landing
(built iter-9/11 on all-zero fixtures) and has never been exercised against a non-empty,
partially-selected pool before now.

The true "21 sealed" figure IS served correctly — on the **Vault** endpoint/section, confirmed
above. IN SCOPE bullet 4 of this iteration's own spec anticipated exactly this split
("... with the real aggregate counts (21 sealed, 80 shard pool, ...)"), so I read that as the
authoritative framing and TC-1/TC-3's literal `== 21` on readiness as an imprecision in the
decomposer's phrasing, not a defect to chase. **Recommendation for the browser-qa-agent and
evaluator**: verify "21 sealed" via the Validation Vault section's rendered shard count, and "80"
(or an equivalent whole-pool figure) via the Microscope Readiness section — do not expect the
readiness section to show 21 anywhere; if it ever does, that would be the actual anti-goal
violation.

## Test Run Mechanics (why one suite run became three)

`docs/handoffs/goal-rapid-microscope-iter-22-dev.md` recorded the whole suite completing in
654.25s. This iteration it did not complete as one run — not because anything is broken, but
because the real `.data/datasets` store grew from ~18 datasets/~0.92GB (all legacy) to 98
datasets/~23GB (18 legacy + the 80-shard J-06 tranche) between iter-22 and now, and several
**pre-existing** tests intentionally build fixtures against the real, un-overridden store:

- `tests/test_micro_join.py::test_tc16_real_corpus_joinable_corpus_arithmetic_is_unchanged_by_the_passenger_fixes`
  and `::test_tc4_real_corpus_join_playbook_signal_is_unaffected_by_the_accessor_re_point`
  (`DatasetStore(CONFIG.dataset_dir_resolved())`, no override — by design, per the phase spec's
  own TC-16 wording).
- `tests/test_micro_readiness.py`'s module-scoped `real_readiness`/`real_dataset_records`
  fixtures (`DatasetStore(CONFIG.dataset_dir)`; TC-1 through TC-5 and three later tests share it).
- `tests/test_micro_snapshots.py`'s module-scoped `real_snapshots` fixture (TC-12 × 4; builds
  real feature snapshots via full replay over the 18 real legacy datasets).

`DatasetStore.list()`/`.get()` verify every file's content checksum on first touch (cached
afterward via an in-process dict AND the durable `dataset_index.db`), so enumerating the store's
metadata — needed by every one of these fixtures even though most of them only WANT the 18 legacy
records — now pays a much larger first-touch cost. I ran the full suite three times to isolate
this cleanly rather than let one slow/ambiguous run block everything:

1. First full run stalled for 20+ minutes on a single test with no forward progress in the dot
   output while burning continuous CPU (confirmed via `/proc/<pid>/stat` `utime` climbing) — I
   killed it and bisected which test via `pytest --collect-only -q` cumulative counts.
2. Second run, with the two `test_micro_join.py` real-corpus tests deselected: **3443 passed,
   8 skipped, 6 deselected, 0 failed, 0 errors in 2088.17s** (34:48) — I found FOUR more
   real-corpus tests inside `test_micro_snapshots.py` mid-run and deselected those too on the next
   pass; this number is the clean final run with all 6 deselected.
3. The two `test_micro_join.py` tests run in isolation: **2 passed, 0 failed, 0 errors in
   1740.01s** (29:00).
4. The four `test_micro_snapshots.py` tests run in isolation: **4 passed, 0 failed, 0 errors in
   1903.51s** (31:43).

**Combined total: 3449 passed, 8 skipped, 0 failed, 0 errors** — comfortably above the
DEFINITION OF DONE's `≥ 3,322` floor, with zero failures anywhere across all three runs.

Warm-cache characterization (useful for QA's step-timeout budgeting): after the above runs
populated `dataset_index.db`, a fresh `GET /research/datasets` on a NEW backend process
answered in **1.07s**; a fresh `GET /research/desk/micro/readiness` answered in **13.57s** (down
from **799.6s**/13:20 cold on the very first touch). The warm figure is in the same order of
magnitude as the PRE-EXISTING, already-deferred "22.3-second Desk-readiness latency fix" (iter-22
item 4, still out of scope this iteration) — the J-06 tranche did not introduce a new latency
class, it made the pre-existing one's cold start dramatically worse and its warm floor somewhat
worse. No functional regression anywhere; every real-corpus assertion passed, including the
12-symbol-day/18-dataset legacy-corpus invariants.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ --junitxml=<path>` (run in three
pieces per above; combined result below).

Result: **3449 passed, 8 skipped, 0 failed, 0 errors** (3457 collected). TR-2, TR-4, TR-12, TR-19,
TR-20, TR-33 all exercised and green (part of the un-deselected suite; `test_j06_operator.py`,
`test_vault.py`'s TR-33 section, `test_tick_recorder.py`'s TR-19 section, `test_vault.py`'s TR-20
section all included, 0 failures). `test_mcp_server.py`'s `EXPECTED_TOOLS` (26-tuple) passed.
`test_scout.py:1676`'s new assertion passed and was independently verified non-vacuous via TC-8
(see above).

## Known Issues

1. **MCP `desk_micro_readiness` timeout risk against the real store right now.** The MCP proxy's
   hardcoded `HTTP_TIMEOUT_SECONDS = 10.0` (`apps/backend/app/mcp/__init__.py:57`) is shorter than
   the readiness route's current warm-cache latency (~13.5s) against the real, now-98-dataset
   store. An MCP-connected session calling `desk_micro_readiness` against a real-store-pointed
   backend will likely get a `BackendUnreachableError` (fail-closed — never fabricated data, so
   this is safe, just unavailable) rather than a slow success. Content is verified byte-identical
   to the REST route (see evidence above); this is a latency ceiling, not a correctness bug. Not
   fixed here — changing a global MCP timeout constant is outside this iteration's IN SCOPE list
   and the 22.3s readiness fix is explicitly deferred (OUT OF SCOPE item 2).
2. **Real-corpus test cold-start cost, documented above** — not fixed (explicitly deferred per
   OUT OF SCOPE item 2, "the same category of issue"). Flagging for whoever eventually picks up
   the deferred readiness-latency fix: it should also address `DatasetStore.list()`'s
   full-store-checksum cost scaling with total store size, since that is now the dominant cost,
   not just the fallback-frac computation the iter-22 backlog item originally named.
3. **Browser-qa-agent evidence gathering should budget generously.** If the real-store-pointed
   backend instance for J-06's browser pass is started FRESH (not reusing a process where
   `dataset_index.db` is already warm from this session's runs), the FIRST `/desk` page load with
   Microscope Readiness expanded could take on the order of 13+ minutes, not the usual few
   seconds. `dataset_index.db` (`apps/backend/.data/dataset_index.db`) persists across process
   restarts, so if QA's instance points at the SAME `apps/backend/.data/datasets` directory this
   session used, subsequent loads should be much faster (~13-14s, still slower than typical but
   tractable). Recommend a warm-up GET before the timed browser capture.
4. Trivial, zero-risk, unrelated to my scope: the `runs/goal-session-rapid-microscope/state/*.md`
   / `session.json` / `telemetry.jsonl` / `trace/trace.jsonl` / `reports/security/install-decisions.jsonl`
   diffs visible in `git status` are pipeline/engine bookkeeping, not something I edited.

## Not Done / Explicitly Out of Scope (per this iteration's own OUT OF SCOPE section)

- No J-09 real-corpus pilot-study runs.
- The 22.3s readiness latency fix — still deferred (see Known Issues #2 for why it now matters
  more).
- The selector→kind table dedupe.
- No shard exposure/assignment performed.
- No further tranche recording.
- The sealed judge's economic-floor ruling — untouched.
- No engine/detector/`referee_*` change (confirmed byte-identical, see above).

## Handoff to browser-qa-agent / reviewer / auditor

- Backend instance for J-06 browser evidence: point `TAPEOLOGY_DATASET_DIR` at
  `apps/backend/.data/datasets` and `TAPEOLOGY_BAR_DIR` at `apps/backend/.data/bars` (both
  absolute paths), start on a scoped port (I used 8302), read-only GETs only — the same
  `goal-desk-iter9-scoped-backend.sh` pattern the iter-23 decomposer named. Do NOT reuse or mix
  with the standard fixture-scoped QA rig (`start_scoped_qa_backend.sh` /
  `qa_playbook_iter7_fixture_scoped_backend.sh`) for this evidence — that rig points at a fixture
  directory with zero registered universes and cannot show this.
- Expect the Microscope Readiness section to show a non-empty aggregate for
  `rapid-microscope-j06-starter` with `shard_count: 80` (the whole opaque pool) — NOT 21. Expect
  the Validation Vault section to show 21 sealed rows. Neither section's DOM/JSON should contain
  any symbol or session-date string for a sealed shard anywhere.
- Regression smoke (J-01, J-08, J-09, J-10) should run against the standard fixture-scoped rig as
  usual, per the iter-23 spec's own TESTING REQUIREMENTS — unaffected by anything in this handoff.
