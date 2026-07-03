# Goal Iteration 6 — Versioned indicator profiles: register a candidate, keep `default` byte-identical (J-06)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** tape_to_profit
- **Iteration:** 6
- **Mode:** next
- **Depth:** lean
- **Frontend Present:** no (no frontend code change; the existing `/performance` panel renders the new registry row generically — see Frontend below)
- **Target journeys:** J-06
- **Required-still-passing journeys:** J-01, J-02, J-03, J-04, J-05, J-08
- **Anti-goal reminders (verbatim from `docs/goal.md`):**
  - **No live execution path.** Tapeology MUST NOT place, route, or transmit orders anywhere — no brokerage integration, no trading API, **no paper-trading API**, no order tickets, no recommendation to execute. The ONLY permitted "fill" is the offline backtester's simulated fill computed against recorded historical tape, clearly labeled simulated and sent nowhere. *(critical)*
  - **No profit claims and no advice.** Simulated PnL is a caveated measurement: it MUST always appear with its R counterpart, its n, its fee/slippage assumptions, its train-or-hold-out basis, and its null baseline — and MUST never be presented as expected live results, an edge claim, or a reason to trade. No imperative cues, no prediction language. *(critical)*
  - **Default engine outputs are frozen.** Indicator evolution is additive and versioned only: candidate profiles may add feature keys or alternate thresholds, but the `default` profile's outputs stay byte-identical (equivalence-tested), the live cockpit uses `default` only, and no enhancement may mutate an archived-era behavior to pass. *(critical)*
  - **No train-only promotion.** Nothing becomes the champion, a proposed journey, or a claimed improvement on the strength of train data alone: hold-out survival (net R AND net $, with the configured minimum n) is the only promotion gate; overfit results are labeled overfit. *(critical)*
  - **No ML, no online tuning.** Candidate search is bounded, config-enumerated, offline, and deterministic; no fitted models, no optimizer loops inside the engine, no thresholds that move at runtime.
  - **No fabricated data — honest failure states.** No synthesized trades, quotes, fills, datasets, or PnL to force a green journey; every failure mode (backend down, corrupt dataset, empty window, missing credentials, insufficient n) surfaces an explicit, distinct state. *(critical)*
  - **Single source of truth.** Every canonical value in the Data Contract is computed once and read verbatim by every surface — REST, WebSocket, UI, markdown reports, and MCP. A second computation path or a diverging number across surfaces is a defect. *(critical)*
  - **MCP is read-only.** The MCP server exposes no mutating tools, proxies only the canonical GET surface (plus the allowlisted `get_endpoint`), and MUST NOT become a second implementation of any computation. *(critical)*
  - **Persistence stays scoped.** SQLite holds research records (now including backtests and the PnL ledger); the dataset store holds explicitly recorded historical tape for research replay. The live cockpit's tape remains unpersisted; no ambient recording. *(critical)*
  - **The enhancement loop stays inside its box.** The goal-proposer may append journeys ONLY inside the AUTO:journeys marker block above — it MUST NOT edit human-authored journeys, this Anti-goals section, or any other part of this file; proposed journeys MUST carry a PnL-ledger acceptance criterion, keep the default profile byte-identical, and include a [NEW]-flagged walkthrough. Manufacturing a low-value journey just to keep the loop alive is a failure. *(critical)*

## GOAL

A researcher (and the MCP agent) can list a **candidate indicator profile** registered beside the frozen `default`, backtest the committed fixture dataset under **both** profiles, and see the two reports differ only where the candidate legitimately changes behavior — while the `default` read stays provably byte-identical (equivalence-pinned) and no surface offers a way to select a candidate for the live cockpit.

## BACKGROUND

Passing: J-01–J-05, J-08. Remaining: **J-06** (versioned profiles) and **J-07** (candidate sweep). Target selection follows the priority rubric: no journey regressed (rule 1), the last coherence verdict (`iter-5/coherence.md`) was **COHERENCE-PASS** so no consolidation is owed (rule 2), and J-06 is the head of the last dependency chain **J-06 → J-07** — the sweep has nothing to evaluate until a candidate profile exists, so J-06 is the unblocker (rule 3). J-06 and J-07 are the two remaining *risky* journeys (engine/config seam vs. promotion-gate harness); they are **never bundled** (rule 5) — J-07 is deferred to iter-7.

**Depth = lean** (justified): backend-only with no frontend code change — one config-additive change + one route validation + one backtest-runner overlay + tests, the same machine-surface shape as J-02/J-03/J-04 which all shipped lean. It touches `config.py`'s fingerprint and the engine warm-up gate (the one risky seam this iteration), but that is a single risky journey travelling alone, guarded by a pinned byte-equivalence suite. The prior evaluator explicitly recommended lean (`iter-5/eval.md`) and the evaluator log emitted **no ESCALATE**, so `full` is not forced.

**Resume posture — VERIFY-AND-COMPLETE, do NOT rebuild (lesson iter-5).** HEAD is the iter-5 commit (`9173a7d`) and the working tree already contains a complete, uncommitted J-06 implementation: `apps/backend/app/config.py` (candidate `candidate-faster-warmup` + `profile_definition`/`profile_registry`/`resolved_for_profile`), `apps/backend/app/research/backtests.py` (per-run resolved config + fingerprint stamping), `apps/backend/app/research/profiles.py`, `apps/backend/app/research/routes.py` (registry-backed 422 validation), and `apps/backend/tests/test_profile_equivalence.py` (new) plus updated `test_profiles_api.py` / `test_backtests_api.py`. The decomposer ran the 32 targeted J-06 tests — all pass. The developer's job is to **verify every DoD check independently and change only what a failed check requires** (as in iter-5's zero-churn resume), not to re-implement.

**Failing-baseline framing (lesson iter-5):** `GET /research/profiles` already returned `200` at J-05 with a *zero-candidate* registry — that `200` was NOT J-06 credit. J-06 passes only when the candidate is registered, backtests run under it stamped with its profile id + distinct fingerprint, and the live cockpit is provably locked to `default`.

## IN SCOPE

### Backend
- [ ] **Config-owned profile registry** (Data Contract row 33): `Config.profile_definition(id)` / `Config.profile_registry()` / `_PROFILE_IDS_IN_ORDER` register `default` (frozen, `is_default`) plus exactly ONE additive candidate `candidate-faster-warmup` — an alternate threshold value for the EXISTING `warmup_min_events` gate (40→30, `based_on: default`), value from config (no magic number). This is the ONE allowlist that BOTH `GET /research/profiles` and the backtest route consult — never a second allowlist.
- [ ] **Registry-backed route validation:** `POST /research/backtests` validates `body.profile` against `Config.profile_definition` — a registered candidate is accepted and the job starts; an unregistered/unknown profile returns an honest `422` listing the registered profiles. (The old hardcoded `!= PROFILE_DEFAULT` refusal is already replaced in the working tree — verify it is gone, not restore it.)
- [ ] **Per-run profile overlay, applied inside the fresh backtest engine only:** `Config.resolved_for_profile(id)` returns the identical `Config` object for `default` (strongest byte-identical guarantee) and a fresh `dataclasses.replace` overlay for a candidate — applied ONLY to that one replay, never mutating the shared `CONFIG` singleton. Fees, slippage, the strategy grammar, and the null baseline still read the base config (a profile is an engine/classifier concern — row 33 — never a strategy-grammar one — row 34).
- [ ] **Fingerprint through the ONE existing hasher:** the candidate report carries a distinct `config_fingerprint` (`8c2c0fbf978228e3`) folded from its overlaid, always-hashed `warmup_min_events`; the `default` fingerprint stays the pinned `4d665603569b9dbf` (archived-era records + the founding PnL-ledger row's fingerprint unmoved). The serving-only registry-metadata field `profile_candidate_warmup_min_events` is excluded from the fingerprint so its mere presence moves nothing. Each report stamps its resolved `profile` id (row 31 already carries `profile`).
- [ ] **Pinned default-equivalence test** (J-06's acceptance): replay fixed event streams under `default` and assert **byte-identical** state / confidence / features against pinned **pre-profile** outputs (`tests/test_profile_equivalence.py`). Keep the observer-equivalence suite (7/7) and the full engine suite green.
- [ ] **Candidate-difference test:** a fixture-dataset backtest under the candidate differs from the default backtest **only** where the candidate legitimately changes behavior (a real `tape_state` flip and a materially different hold-out entry — candidate net R `-0.1728` vs default `+0.3334`, never a metadata relabel), and both are individually deterministic (byte-identical re-runs).

### Frontend (if applicable)
- None. The existing read-only `/performance` registry panel renders the profiles array generically (proven at J-05 and re-asserted by `test_performance_page_offers_no_profile_selection_control` — no `<select>`, no hardcoded candidate id), so the candidate row appears with **zero page changes**. Add no selection affordance, no new endpoint, no client-side computation.

### New user-facing capability
The research/MCP surface gains its first additive, versioned candidate indicator profile and the ability to backtest a dataset under `default` vs. the candidate — the mechanism J-07's hold-out sweep will later evaluate — while guaranteeing the live read is frozen.

### New information displayed
`GET /research/profiles` now lists `default` **and** `candidate-faster-warmup` (read-only registry). The `/performance` registry panel reflects it as a second read-only row (`based_on: default`, `overrides: {warmup_min_events}`). Candidate backtest reports are stamped with the candidate profile id and a distinct `config_fingerprint`.

### New user actions
`POST /research/backtests` now accepts `profile: candidate-faster-warmup` (previously `422`); MCP `get_endpoint("/research/profiles")` returns the candidate. No new UI control — profile selection is a backtest-run parameter only, never a cockpit/UI affordance.

### UI surface changes
None. The existing `/performance` read-only registry panel gains one data row via its generic renderer (a display consequence of row 33; no new control, no selection).

### Product surface delta
The product gains additive, versioned indicator evolution: a candidate lives beside the frozen `default`, selectable solely by backtest runs, with the live cockpit and every archived-era surface proven byte-identical on `default`.

### Blueprint conformance
No new surfaces. J-06 lives on its pre-declared **machine** home in the blueprint IA table (`GET /research/profiles` + MCP `get_endpoint`); the read-only display rides the already-registered `/performance` page (Performance nav section). No Information-Architecture or nav-skeleton change — no `blueprint.reapproval-requested`.

### Data-contract additions
**None.** J-06 realizes the *candidate side* of the already-registered **row 33** ("Indicator profiles + champion pointer … additive-only candidates; profile id folds into `config_fingerprint`", served ONLY by `GET /research/profiles`) and stamps backtests under **row 31** (which already carries `profile` id + `config_fingerprint` in provenance). No value gains a new computing module or a new serving endpoint, so `blueprint.md` needs no edit. Never introduce a second registrable-profile list or a second fingerprint path — read the one config-owned registry (`Config.profile_definition`) and the one `config_fingerprint()` hasher.

## OUT OF SCOPE

- The candidate sweep harness `python -m app.research.pnl_scan` and any promotion / champion-movement mechanics — that is **J-07** (risk isolation: the two remaining risky journeys are never bundled).
- Appending any PnL-ledger row (no promotion happens in J-06; the ledger stays exactly the founding row) and moving the champion pointer (stays `v1/default`; only a hold-out survivor may move it — J-07).
- Any change to the `default` profile's outputs, the live cockpit, or any archived-era behavior.
- Any new MCP tool (`/research/profiles` is read via the existing `get_endpoint` allowlist; `app/mcp/__init__.py` stays untouched, docstring-at-most).
- Any change to `pnl_min_sample_size` or the committed fixture datasets (the J-05 golden script pins "insufficient sample (n < 5)"; lesson iter-4 — the fixtures arm n=1 per split).
- Any second candidate profile — exactly ONE candidate proves the mechanism (goal capability 2 / J-06 asks for "at least one"); keep the change set small.

## DEFINITION OF DONE

- [ ] **J-06 passes:** `GET /research/profiles` (and MCP `get_endpoint("/research/profiles")`) lists `default` + the candidate `candidate-faster-warmup`; the committed fixture-dataset backtest runs to `done` under **both** `default` and the candidate; `tests/test_profile_equivalence.py` (pinned default equivalence + candidate-fires difference + fingerprint pins + source-scan guards), `test_profiles_api.py`, and `test_backtests_api.py` are green — verified via browser-qa-agent (Chrome MCP in-page API legs) and the automated suite.
- [ ] The `default`-profile backtest report on the fixture is **byte-identical** to the pre-J-06 default report and `config_fingerprint()` for `default` is **unchanged** (`4d665603569b9dbf` — archived-era records + founding PnL-ledger row unmoved); the candidate report carries a **distinct** fingerprint (`8c2c0fbf978228e3`) + its profile id.
- [ ] An unknown/unregistered profile id is rejected with an honest `422` listing the registered profiles.
- [ ] A source-scan test proves `resolved_for_profile` is called only by the backtest runner (`research/backtests.py`) — the live cockpit and every archived-era engine path are locked to `default`; `/performance` has no profile-selection control.
- [ ] Required-still-passing **J-01, J-02, J-03, J-04, J-05, J-08 remain green** — J-01/J-05/J-08 via golden replay with an explicit per-journey result row (lesson iter-1); J-02/J-03/J-04 via the automated suite (lesson iter-2).
- [ ] **No anti-goal violation:** default byte-identical (equivalence green); no UI path selects a candidate; no promotion, no ledger append, champion still `v1/default`; MCP read-only (`app/mcp/__init__.py` diff docstring-at-most); no execution path (`test_no_execution_path.py` green).
- [ ] Unit tests pass; **no regressions** — full backend suite green with the new J-06 tests added and none deleted (≥ iter-5's 988-passed baseline).
- [ ] Dev handoff written at `docs/handoffs/goal-tape_to_profit-iter-6-dev.md` (verify-and-complete: state which checks were re-run independently and that no rebuild was needed, or list exactly what a failed check required).

## TESTING REQUIREMENTS

- **Browser** (demand an explicit result row per journey — lesson iter-1):
  - **J-06** (own journey, machine-surface — no golden replay script exists, lesson iter-2): Chrome MCP in-page `fetch()` from a backend-origin page — `GET /research/profiles` shows `default` + candidate; `POST /research/backtests` under `default` → started/`done`; under `candidate-faster-warmup` → accepted/`done` (report stamped with the candidate profile id + distinct fingerprint); under an unknown profile → `422` honest refusal.
  - **J-05** (golden script + in-page page-equals-API): `/performance` registry panel lists `default` + candidate, **read-only, NO selection control**; ledger + champion unchanged (still `v1/default`).
  - **J-01** (golden nav script + MCP): `get_endpoint("/research/profiles")` JSON byte-identical to the REST payload; nav unchanged (4 links).
  - **J-08** (golden regression script + suite): cockpit `/`, `/journal`, `/studies` intact; full backend suite green; observer-equivalence 7/7.
- **Unit/integration:** registry lists `default` + candidate; route consults the registry (candidate accepted, unknown → `422`); `default` backtest byte-identical to pre-J-06 (pinned state/confidence/features); candidate backtest deterministic and differing only on the legitimate change; `config_fingerprint` — `default` unchanged (`4d665603569b9dbf`), candidate distinct (`8c2c0fbf978228e3`), registry-metadata field excluded while a real classifier threshold still moves the fingerprint; a source-scan test that `resolved_for_profile` is called only by the backtest runner and that no cockpit/`/performance` control selects a profile.
- **Error cases:** unknown/unregistered profile id → `422` honest (lists registered profiles); `resolved_for_profile(default)` returns the identical `Config` object (never a drifting copy); an unregistered id → `None` (never a silent coercion to `default`); the frozen `default` cannot be mutated or re-defined; backend-down MCP → explicit tool error (unchanged).

## NOTES

- **Coherence watchpoints** (last verdict was PASS — keep it): (1) `config_fingerprint` folds the profile through the **one** existing `config_fingerprint()` hasher — the `default` fingerprint must not move (else archived records + the founding PnL row drift → J-08 fail + a never-pool honesty break); (2) **one** registry source (`Config.profile_definition`) feeds both `GET /research/profiles` and the backtest route's validation — no second profile allowlist; (3) `default` engine byte-identity via *overlay-only-inside-the-backtest-engine* — no engine default constant changes, no shared mutable config (the shared `CONFIG` singleton is never mutated); (4) `/research/profiles` stays the single serving endpoint and no Data-Contract row is added (row 33 already covers candidates; row 31 already carries the profile id + fingerprint); (5) no UI selection path; (6) `app/mcp/__init__.py` untouched — profiles reach MCP via the existing `get_endpoint`.
- **Make the candidate fire on the fixture** (lesson iter-4): the committed fixture pair arms only n=1 per split, so the candidate's additive change (lower `warmup_min_events`) is calibrated to demonstrably and deterministically move at least one classified output on the fixture (a real `tape_state` flip earlier, and a materially different hold-out entry/R) — never a vacuous no-op. J-06's acceptance is byte-identity of `default` + a *real* legitimate difference for the candidate + determinism, NOT any sample-size gate (that is J-07). The candidate's hold-out net R turning negative (`-0.1728`) vs default's `+0.3334` is a legitimate measured difference under disclosed assumptions — NOT a promotion, an edge claim, or a profit claim.
- **Machine-surface regression lane** (lesson iter-2): J-06 gets no golden replay script (`demo_runner.py` is goto/click/fill only, no POST); its durable regression lane is the backend suite, and browser verification of the API legs uses Chrome MCP in-page `fetch()`. J-02/J-03/J-04 likewise ride the suite; the browser replay lane carries J-01/J-05/J-08 golden scripts.
- **Environment caution** (lesson iter-3): before diagnosing "flaky browser" / `net::ERR_INSUFFICIENT_RESOURCES` / sqlite `Disk quota exceeded`, run `du -sh /tmp/pytest-of-dennis-chan` against the per-user tmpfs quota; at planning time it was healthy (2.4G of 6.5G, 50%). If large-suite or browser lanes flake, point pytest `TMPDIR` + `--basetemp` off tmpfs to a root-filesystem dir (the decomposer's targeted J-06 run used `/home/dennis-chan/.cache/tapeology-pytest`).
- **References:** evaluator next-step `runs/goal-session-tape_to_profit/iter-5/eval.md`; the registry + overlay + fingerprint live in `apps/backend/app/config.py`; registry serving side `apps/backend/app/research/profiles.py`; route validation + report stamping `apps/backend/app/research/routes.py` + `apps/backend/app/research/backtests.py`; the pinned equivalence + candidate-difference + source-scan tests in `apps/backend/tests/test_profile_equivalence.py`.
- **After J-06:** J-07 (the candidate sweep harness `python -m app.research.pnl_scan`), whose promotion-gate tests must control the configured minimum-n both ways since the fixtures arm only n=1 per split (lesson iter-4).
