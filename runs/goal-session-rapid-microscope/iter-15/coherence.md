# Iteration 15 — Coherence Audit

**Iteration:** goal-rapid-microscope-iter-15
**Date:** 2026-08-20
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-WARN

---

## Summary

Both pieces of this bundled round hold up. The four new MCP tools (`desk_micro_readiness`,
`desk_scout`, `desk_walkforward`, `desk_vault`) run through the SAME generic, unmodified
`call_tool` → `_request_path` → `_proxy_get` dispatch (`apps/backend/app/mcp/__init__.py:603-613`,
untouched by this diff) every other proxy tool already uses — a pure path-lookup into
`_STATIC_PATHS` followed by a verbatim `response.text` pass-through. No per-tool logic was added,
so byte-identity holds by construction, not merely by the new tests' assertions (which independently
confirm it empirically, and which the independent auditor re-proved a third way on its own richer
fixture). Each `_STATIC_PATHS` entry maps 1:1 onto an already-registered Data Contract endpoint
(readiness/scout/walkforward/vault), so the iter-15 blueprint note's decision to add no new Data
Contract row is correct — verified against real precedent, not just the note's own claim: `desk_playbook`
and `desk_referee` (both prior-era MCP additions) genuinely have no MCP-specific row in blueprint.md
either.

The Microscope Readiness disclosure fix — `sealed_tranche` and `joinable_corpus.withheld_excluded` —
genuinely closes the WARN carried since iteration 9/10 and restated in iteration 14's coherence.md.
Both fields are already computed, unchanged, in `micro_readiness.py` (`build_readiness`, lines
463-495: `joinable_corpus` and `sealed_tranche` are both already keys of the returned dict before
this iteration touched anything). This iteration's diff only adds a frontend reader: `types.ts`
transcribes the shapes verbatim, and `page.tsx` renders them with direct property access
(`{readiness.sealed_tranche.shard_count}` etc.) — no arithmetic, no second fetch, no recomputation.
The widened `_PRICE_ARITHMETIC_FIELDS` guard specifically targets these new bindings and the
independent auditor mutation-tested it against six seeded violations, all caught.

Zero backend product-computation files were touched (`micro_readiness.py`, `vault.py`, `scout.py`,
`scout_ledger.py`, `walkforward.py`, `walkforward_ledger.py`, `micro_routes.py` — none appear in
`git status`), which is the strongest structural evidence against a Part A duplicate-computation
FAIL: there is no second implementation anywhere for any touched value to have diverged from.

The one substantive issue is a genuine cross-sibling inconsistency, independently found by direct
code inspection before cross-checking the independent auditor's own report (which flags the same
thing as its finding F2): `MicroReadinessSection` still drops its section-level `data-testid` in the
loading/unavailable branches — the exact defect this same iteration fixed on `ValidationVaultSection`,
left in place on the sibling section this iteration's own diff extensively edits (the new Sealed
Tranche block sits inside this same function). It is not a Part A/B FAIL under this gate's objective
rules (see below), so it is recorded as WARN, not FAIL — consistent with the independent auditor's
own GAP (non-blocking) classification of the identical finding.

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| `desk_micro_readiness` MCP tool | OK | `apps/backend/app/mcp/__init__.py:28` `_STATIC_PATHS["desk_micro_readiness"] = "/research/desk/micro/readiness"` (already-registered endpoint); dispatched by the unmodified generic `call_tool` (`:603-613`); byte-identity proved live by `test_desk_micro_readiness_tool_byte_identical_on_the_honest_empty_state`/`..._on_a_populated_state` (`apps/backend/tests/test_mcp_server.py:209-252`) |
| `desk_scout` MCP tool | OK | `_STATIC_PATHS["desk_scout"] = "/research/desk/micro/scout"` (`mcp/__init__.py:29`); byte-identity proved by `test_desk_scout_tool_byte_identical_on_the_honest_empty_state`/`..._on_a_populated_state` (`test_mcp_server.py:256-296`), populated state seeded via `ScoutLedger.append_row` directly (never a live compute run) |
| `desk_walkforward` MCP tool | OK | `_STATIC_PATHS["desk_walkforward"] = "/research/desk/micro/walkforward"` (`mcp/__init__.py:30`); byte-identity proved by `test_desk_walkforward_tool_byte_identical_on_the_honest_empty_state`/`..._on_a_populated_state` (`test_mcp_server.py:300-352`), populated state seeded via `walkforward_ledger.append_fold_result` directly |
| `desk_vault` MCP tool | OK | `_STATIC_PATHS["desk_vault"] = "/research/desk/micro/vault"` (`mcp/__init__.py:31`); byte-identity proved by `test_desk_vault_tool_byte_identical_on_the_honest_empty_state`/`..._on_a_populated_state` (`test_mcp_server.py:356-414`), populated state seeded via `vault.register_universe`/`vault.seal_shard` directly; sealed-shard projection asserted to be exactly the 6-field opaque whitelist (`shard_id`/`universe_id`/`size_bucket`/`checksum_commitment`/`sealed_at`/`exposure_state`), never raw identity |
| MCP surface TR-2 join-resistance (all 26 tools, sealed shard under a **registered** universe) | OK (fixed this iteration) | `test_mcp_server.py:418-557` `test_tr2_the_new_mcp_tools_leak_nothing_about_a_sealed_shard`; the pre-fix version sealed under an unregistered universe (never exercising `vault._serialize_universe`'s committed/revealed branch) — the independent audit's B1 finding, mutation-proved both ways and fixed in this diff (the `vault.register_universe(...)` call + `sealed_session_date` addition to `forbidden_substrings` + the 5 non-vacuity assertions at the end of the test are all present) |
| `EXPECTED_TOOLS` / `TOOL_NAMES` contract | OK | `test_mcp_server.py:165-176` — 26-entry ordered tuple, `desk_micro_readiness`/`desk_scout`/`desk_walkforward`/`desk_vault` inserted immediately after `desk_referee_registry` and before `pnl_ledger`, matching the identical insertion point in `mcp/__init__.py:419-464`'s `TOOLS` tuple and `_STATIC_PATHS`; two downstream `get_endpoint` tests re-derived their tracked total 22→26 (`test_mcp_server.py:573`, `:587`) |
| `sealed_tranche` (readiness) | OK — REGISTERED-NOT-RENDERED WARN from iter-9/10/14 now CLOSED | Already computed unchanged in `app/research/micro_readiness.py:477-495` (`build_readiness`); `apps/frontend/lib/types.ts:763-767` transcribes the shape verbatim; `apps/frontend/app/desk/page.tsx:599-673` renders `shard_count`/`symbol_days`/per-universe breakdown via direct property access, no arithmetic |
| `joinable_corpus.withheld_excluded` (readiness) | OK — same WARN, now CLOSED | Already computed unchanged in `micro_readiness.py:463-475` (owned by `micro_join.joinable_corpus_counts`, called from `micro_readiness.py` — no second endpoint, matching the Data Contract row's own parenthetical); `types.ts:754-761`; rendered `page.tsx:630-637`, direct property access |
| Zero client-side arithmetic on the two newly-rendered numerics | OK (executed, not just read) | `apps/backend/tests/test_desk_ui_guards.py:326-335` widened `_PRICE_ARITHMETIC_FIELDS`; independent auditor mutation-tested 6 seeded violations (`readiness.sealed_tranche.shard_count - 1`, `.symbol_days * 2`, `universeCounts.shard_count + universeCounts.symbol_days`, `withheld_excluded - …`, `1 - readiness.sealed_tranche.shard_count`, `universeCounts.symbol_days / 3`) — all caught, zero false positives; `test_desk_ui_guards.py` re-run fresh 99 passed |
| `family.family_root_id` (Scout header) | OK — not a new/duplicate value | Pre-existing field on `ScoutFamily`, unchanged by this diff (`apps/frontend/lib/types.ts:2565`, confirmed outside the diff hunks); already fetched by the one canonical `GET /research/desk/micro/scout` call; `page.tsx:6274-6284` interpolates it directly, no new fetch |
| `micro_readiness.py`/`vault.py`/`scout.py`/`scout_ledger.py`/`walkforward.py`/`walkforward_ledger.py`/`micro_routes.py` | OK — confirmed untouched | Absent from `git status --short`; only 5 files modified this iteration (`mcp/__init__.py`, `test_desk_ui_guards.py`, `test_mcp_server.py`, `desk/page.tsx`, `lib/types.ts`) |
| No new Data Contract row for the 4 MCP tools | OK — judgment verified, not just asserted | blueprint.md's iter-15 note claims MCP proxies of already-registered endpoints don't need their own row, citing `desk_playbook`/`desk_referee` as precedent; independently grepped blueprint.md and confirmed neither has an MCP-specific row of its own anywhere in the Data Contract section |

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| No new route / no nav change | OK | `git status --short` shows no `apps/backend/app/meta.py` (`UI_ROUTES`) or `NavBar` component touched; nav still resolves to exactly Cockpit / Structure / Desk |
| Microscope Readiness "Sealed Tranche" block | OK | `page.tsx:599-673`, inserted inside the existing `MicroReadinessSection` return (`:5904` wrapper `data-testid="micro-readiness-section"`), between the pre-existing Corpus Totals block and Legacy Tick Shards block — no new section, matches blueprint IA row "Era transition + corpus readiness truth (J-01) \| `/desk` → Microscope Readiness" |
| Scout Ledger family-header addition | OK | `page.tsx:6274-6284`, inside the existing `scout-ledger-section` wrapper (`:6199`) — matches blueprint IA row "Scout + candidate ledger (J-04) \| `/desk` → Scout Ledger" |
| Walk-Forward copy fix + HTML-tag fix | OK | `page.tsx:6517-6710`, inside the existing `walk-forward-section` wrapper (`:6427`) — matches blueprint IA row "Walk-forward engine + diagnostic run (J-05) \| `/desk` → Walk-Forward" |
| Validation Vault testid fix | OK — improves, does not change, reachability | `page.tsx:6682-6699`; both early returns now wrap `LoadingPanel`/`UnavailablePanel` in `<div data-testid="validation-vault-section">`, matching `ScoutLedgerSection`'s and `WalkForwardSection`'s own always-render-the-wrapper pattern (confirmed at `page.tsx:6199`+`:6252/6254` and `:6427`+`:6479/6481` — both render the wrapper unconditionally and handle the loading/unavailable ternary as a child) — same home, same click depth, purely an internal DOM-contract consistency fix |
| 4 new MCP tools | N/A — not a nav-skeleton surface | blueprint.md's own IA section states the MCP surface is goal.md's "Target Users" bullet 2 (Claude + MCP), not a nav entry; confirmed no page/button/link references any of the 4 new tool names (`grep -rn "desk_micro_readiness\|desk_scout\|desk_walkforward\|desk_vault" apps/frontend/` returns nothing under `apps/frontend/`) |
| No duplicate home / no parallel shell | OK | All edits sit inside the four already-registered `/desk` sections' existing wrapper elements; no new `CollapsibleSection` id, no new top-level route, no second "readiness"/"scout"/"walkforward"/"vault" surface introduced anywhere |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- **`MicroReadinessSection` still drops its section testid in the loading/unavailable states — the
  exact inconsistency this same iteration fixed on `ValidationVaultSection`.** `page.tsx:5891-5893`
  (`if (readinessResult === null) return <LoadingPanel testid="micro-readiness-loading" />;`) and
  `:5894-5901` (`if (!readinessResult.ok || ...) return <UnavailablePanel testid="micro-readiness-
  unavailable" .../>;`) both return bare, with no wrapping `<div data-testid="micro-readiness-
  section">` — only the success path at `:5904` carries that wrapper. This is precisely the shape
  `ValidationVaultSection` had before this round's fix (`page.tsx:6682-6699`), and `ScoutLedgerSection`
  /`WalkForwardSection` never had it in the first place (both wrap unconditionally, per the IA table
  above). Independently verified by direct code read before cross-checking; the independent auditor's
  own report (`docs/handoffs/goal-rapid-microscope-iter-15-audit.md` finding F2) confirms the same
  thing live with the backend stopped: `validation-vault-section`/`scout-ledger-section`/`walk-forward-
  section` all present, `micro-readiness-section` absent (only `micro-readiness-unavailable` renders).
  **Not a Part A/B FAIL**: the value itself is not duplicated or mis-sourced (Data Contract clean, per
  the table above), and the feature's reachability/click-depth/home are completely unaffected — this
  is a DOM/test-tooling attribute missing in 2 of 3 render branches, which is Part C territory
  (structural/contract drift across sibling surfaces) by the skill's own definition, not a nav or
  data-sourcing violation. Worth closing promptly because this iteration's own diff extensively edits
  this exact function (the whole Sealed Tranche block lives inside it) and just finished applying the
  identical fix one section over — the fix is a one-line-per-branch, finite, already-proven pattern:
  wrap both early returns in `<div data-testid="micro-readiness-section">` exactly as
  `ValidationVaultSection` now does at `:6682-6699`.
- For completeness, not as a new item: `joinable_corpus.total`/`playbook_signal_count`/
  `band_touch_count`/`by_setup_id` remain typed and fetched but unrendered
  (`types.ts:754-761`/`page.tsx`). This is NOT a new WARN — it is the same accepted, blueprint-
  documented pattern established at iteration 2/3 ("the joinable-corpus field above is served ahead
  of its UI wiring... this is not an orphan feature," blueprint.md's iter-3 note) and explicitly
  scoped out of this iteration by both the phase spec's OUT OF SCOPE section and
  `state/assumptions.md`'s iter-15 first entry. Recorded only so a future reader doesn't mistake
  silence for an oversight.
- The independent audit's B2 observation (`sealed_tranche`'s unresolved-pool count vs. the Vault
  shard list's ledger-tracked-only count are two different populations, now readable on the same
  screen, so their difference is derivable) is not a Data Contract violation — the two are legitimately
  different values with different already-registered owners (`micro_readiness.py`'s pool-membership
  logic vs. `vault.py`'s ledger-tracked-shards logic), not one value computed twice. The auditor
  already verified the derivable count-level fact does not amount to an identity disclosure against
  spec §7.5 point 7's governing test. No action needed from this gate.

## Verification performed this audit (for the record)

- Read `apps/backend/app/mcp/__init__.py:603-613` (`call_tool`) directly and confirmed it is
  unmodified by this diff and fully generic — no per-tool branch exists for any of the 4 new tools.
- Read `apps/backend/app/research/micro_readiness.py` (grep `sealed_tranche|joinable_corpus|
  withheld_excluded`) and confirmed both fields are already keys of `build_readiness`'s return dict,
  unchanged this iteration (lines 463-495).
- Read `MicroReadinessSection` (`page.tsx:5886-5935`), `ScoutLedgerSection` (`:6182-6221`),
  `WalkForwardSection` (`:6410-6448`) in full to compare their loading/unavailable-branch wrapper
  patterns directly, rather than taking the phase spec's characterization on trust.
- Grepped `apps/frontend/lib/types.ts` for `family_root_id` and confirmed it predates this diff
  (line 2565, on `ScoutFamily`, outside any changed hunk).
- Grepped `runs/goal-session-rapid-microscope/state/blueprint.md` for `desk_playbook`/`desk_referee`
  and confirmed neither has an MCP-specific Data Contract row, corroborating the iter-15 note's
  claimed precedent rather than accepting it unverified.
- `git status --short` and `git diff 711580a3965d070354371a825718c13ba73b0043 --stat` (noise-excluded
  + excluded-paths-only): confirmed exactly 5 product files changed, all backend `research/*` modules
  and `micro_routes.py` untouched, and the only excluded-path churn is harness bookkeeping
  (`runs/goal-session-rapid-microscope/*`, `reports/goal-session-rapid-microscope-index.html`, one
  prior-iteration summary/iteration-summary pair) — no lockfile, no dependency-file change.
- Cross-read `docs/handoffs/goal-rapid-microscope-iter-15-audit.md` (independent auditor,
  PASS_WITH_GAPS) after forming my own findings independently, to corroborate rather than substitute
  for direct verification — its B1 (fixed), F2, and B2 findings all match what direct code inspection
  above already found.
