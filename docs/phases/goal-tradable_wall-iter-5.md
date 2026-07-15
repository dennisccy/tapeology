# Goal Iteration 5 — Honest + bounded setups read-surface (J-05 backend enablers: B1 recency-boundary contract, B3 shared scan cache)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** tradable_wall
- **Iteration:** 5
- **Mode:** next
- **Depth:** full
- **Frontend Present:** no
- **Target journeys:** J-05
- **Required-still-passing journeys:** J-01, J-02, J-04, J-07
- **Anti-goal reminders (verbatim from `docs/goal.md`):**
  - **Frozen foundations** — the `v1` strategy, the `default` profile, the tape engine's five states and thresholds, the frozen structure computations, the JSON `BarStore`, and archived-era behaviour stay byte-identical. New work is additive and versioned beside them, never a mutation of them. *(critical)*
  - **No lookahead** — every value computed as-of T uses only events/bars fully completed at T. *(critical)*
  - **Single source of truth** — each shared value is computed once, owned by one canonical endpoint, and read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor hard-fails violations. *(critical)*
  - **Deterministic and seeded** — every random draw uses a config-owned recorded seed; identical requests reproduce byte-identical results; no wall-clock, no unseeded randomness in any research artifact.
  - **No gate bending for a headline.** n≥5 per reported cell, train/hold-out separation, null baseline, and the full PnL register hold everywhere; an empty or all-`insufficient_sample` edge report is a valid, publishable outcome. *(critical)*
  - **New strategy code is additive and registered — never a mutation.** `structure_tape_map` is a new config-owned registry entry beside frozen `v1`/`structure_tape`; no frozen definition, parameter, or output changes; the `config_fingerprint` stays `4d665603569b9dbf`. *(critical)*
  - **Morning-markup discipline.** Any session's map derives only from bars fully completed by the prior session's close; no forming-bar data enters a map, an event, or a chip. *(critical)*

## GOAL

Make the setups read-surface (case registry, per-event drill-in, and the 3-way edge report) **recency-honest** and **latency-bounded** on the populated 12-symbol store, so the J-05 `/structure` UI can render it truthfully and within browser-QA timeouts. Measurable capability (no user-visible change this iteration): boundary touch events disclose their truncated horizon instead of showing a definitive reaction beside `None` returns; the single full-panel scan is served once from a rebuildable, byte-identical cache instead of re-scanning on every request.

## BACKGROUND

The iter-4 evaluator recommended J-05 next and named **two blocking watch-items that must be resolved BEFORE rendering setups events**: audit **B1** (13/801 most-recent-session events carry a definitive reaction label beside `None` forward returns — `setups.py` caps the reaction read at `min(touch_index + horizons[0], len(all_bars)-1)`, so a boundary touch is labeled from a truncated sub-horizon while its horizon-0 return honestly reports `None`) and audit **B3** (`GET /research/setups`, `GET /research/setups/{id}`, and `GET /research/edge-report` each re-run the full-panel `compute_setups` scan — ~4m43s on the populated store — on **every** request; a single J-05 page load would trigger it up to three times, far past browser-QA timeouts).

**Why a backend-only enabler pass, not a bundled J-05 (target-selection deviation, stated per rubric).** The rubric ranks "smallest spec" and "never bundle two risky changes — a joint failure is undiagnosable." B1 mutates the setups value's contract (regression surface on **J-02** which owns the registry and **J-04** whose edge report reads `compute_setups`); B3 introduces a shared cache that must stay **byte-identical + deterministic** (anti-goal #6 single-source, #7 deterministic) across three endpoints. Both are diagnosable only via unit/determinism tests — not via a browser. Bundling them with the large browser-verified `/structure` render (map default + raw toggle + Case Studies browser + drill-in + Edge Report section) would fail across four independent lanes at once. Isolating the two backend risks here — verified by deterministic replay of J-01/J-02/J-04/J-07 plus the auditor's skeptical byte-identity re-check — lets iter-6 render J-05 on a proven-stable, bounded substrate where any browser-QA failure is unambiguously frontend. This is also the cleanest way to honor the evaluator's own "resolve B1 + B3 BEFORE rendering."

**J-05 does NOT flip this iteration** — it stays `failing` by design until iter-6 renders the UI. This is forward progress on J-05's named blockers (the same shape as iter-3 advancing J-03's substrate), not a journey flip.

**Depth = full (trigger cited).** Backend-only, but it "requires new tests beyond a browser smoke" (determinism byte-identity, recency-boundary regression, cache-invalidation, immutable-safety) and is a hardening pass touching a **shared read-path across three endpoints** with **J-02/J-04 regression + single-source coherence surface**. Full runs the 11-step pipeline, giving the auditor's skeptical byte-identity/fingerprint/frozen-file re-verification and the coherence-auditor's single-source check — both of which the lean cycle skips. (No prior `ESCALATE`; full is chosen on the test-depth + coherence triggers.)

## IN SCOPE

### Backend

- [ ] **B1 — additive recency-boundary annotation in `app/research/setups.py`.** For a touch event whose reaction horizon is truncated at the last stored bar (`touch_index + horizons[0] >= len(all_bars)`), additively expose on the event: (a) the **effective reaction horizon in bars** actually used, and (b) a **boundary flag** (e.g. `reaction_boundary_truncated: true`). Do NOT mutate the existing `reaction` label and do NOT drop the event — the label is *disclosed* as truncated-horizon, ready for the iter-6 UI to surface/flag. Non-boundary events get the flag `false` and the full configured horizon; their `reaction` and `forward_returns` are byte-identical to today.
- [ ] **B1 regression test on a populated-store shape.** Assert a boundary event has a definitive `reaction`, its horizon-0 `forward_returns` entry `return_fraction == None`, the new boundary flag `true`, and the effective horizon `< horizons[0]` — with **exact** values. Per the iter-2 + iter-4 lessons, the committed fixtures stop at 2026-06-30 (before the recency boundary), so this test needs a purpose-built fixture (or store shape) whose scan reaches the most-recent-session boundary; a fixture that never produces a boundary event does not exercise B1.
- [ ] **B1 non-boundary byte-identity test.** The pinned AAPL 2026-06-22 event stays `rejected` with its existing forward returns (iter-2 recorded `[-0.462%, -4.269%]`) and `touch_ts 2026-06-22T13:30:00Z`; assert byte-identical to the pre-change `compute_setups` output except for the additive fields.
- [ ] **B3 — memoize the one `compute_setups` full-panel scan** behind a rebuildable, **store-content-keyed** (checksum/signature of the store's series set) in-process cache, implemented **internally to `setups.py`** so `GET /research/setups`, `GET /research/setups/{id}`, and `edge_report.py`'s `compute_setups(...)` call all benefit with **zero change to `routes.py` or `edge_report.py`** (lowest regression surface for J-04). The cache is a rebuildable accelerator (the `bar_index` precedent) — **never persisted as a source of truth**, process-local, and rebuilt whenever the store signature changes.
- [ ] **B3 tests:** (1) **byte-identity** — a cached read of each of the three endpoints' scan output equals a fresh `compute_setups`; (2) **computed-once-per-unchanged-store** — the underlying scan runs exactly once across repeated reads (assert via a call counter / spy, not wall-clock); (3) **checksum-bust** — mutating the store (append a series) re-runs the scan and never serves a stale result; (4) **immutable-safe** — a `/setups/{id}` drill-in read (which enriches with `tape_timeline`) followed by a `/setups` list read returns the **un-enriched** list verbatim (guards the shared cache against caller mutation; `enrich_with_tape_timeline` is already copy-on-write — lock the invariant with a test).
- [ ] **J-03 keyless enrichment unbroken.** `GET /research/setups/{id}` still joins the exact `tape_timeline` over the committed covering `DatasetStore` fixture slice after the cache lands — exact-value test.
- [ ] **Frozen byte-identity re-verification.** `config_fingerprint == 4d665603569b9dbf`; registry order `(v1, structure_tape, structure_tape_map)`; `git diff --name-only -- apps/` shows ONLY `setups.py` (+ any small owned cache helper it introduces) and tests changed — every truly-frozen file absent (`levels.py`, `tradability.py`, `engine/`, `strategies.py`, `bars.py`, `datasets.py`, `adapters/`, and `edge_report.py`/`backtests.py` **existing outputs**).

### Frontend (if applicable)

- None — **Frontend Present: no**. The recency-honesty disclosure and the bounded loads are surfaced by the J-05 `/structure` render in **iter-6**.

### New user-facing capability

None this iteration (backend enabler). In iter-6 the J-05 Case Studies browser will be able to render boundary events honestly (disclosing the truncated horizon) and the whole `/structure` page will load within normal timeouts on the populated store.

### New information displayed

None on-screen this iteration. New data now *available* on the setups value for iter-6 to display: the per-event effective reaction horizon + boundary flag.

### New user actions

None (no UI change).

### UI surface changes

None (no UI change).

### Product surface delta

No visible delta. Measurable capability delta: the setups/edge-report read-surface becomes recency-honest and loads in bounded time on the real 12-symbol store — the precondition for J-05 to ship honestly.

### Blueprint conformance

No new surfaces and no nav change. The additive setups fields + the memoized scan cache attach to the **existing** `Touch events + reaction labels ... + case registry` Data-Contract row (owner `app/research/setups.py`; endpoints `GET /research/setups` + `GET /research/setups/{id}`; also read by `GET /research/edge-report`). `blueprint.md` updated with an additive note on that row (no new row, no nav-skeleton change → no `blueprint.reapproval-requested`).

### Data-contract additions

No NEW value with a new owner/endpoint. Two **additive attributes/notes on the existing setups value** (single computer `setups.py`, unchanged endpoints): (1) per-event *effective reaction horizon* + *boundary flag*; (2) a rebuildable, byte-identical, store-checksum-keyed memoized scan cache — an **internal accelerator, NOT a second source of truth**. No second computation or second endpoint is introduced for any existing value. Registered via the additive note in `blueprint.md`.

## OUT OF SCOPE

- The `/structure` frontend render — Tradable Map as default, raw-levels toggle, Case Studies browser + drill-in, Edge Report section (this is J-05's UI; deferred to **iter-6**).
- Any cockpit change — band overlay + confluence chip (J-06; deferred to iter-7).
- The credentialed ≥10-window recording + pinned-AAPL 06-22 drill-in (J-03's remaining credentialed portion) — operator-gated; NOT re-planned here.
- Changing the `reaction` **value** of any non-boundary event, or **excluding** boundary events — the fix is additive disclosure only.
- Any change to frozen files or outputs (`levels.py`, `tradability.py`, tape `engine/`, `strategies.py`, `backtests.py` existing outputs, `edge_report.py` existing outputs, `bars.py`, `datasets.py`, `adapters/`), the `config_fingerprint`, or the champion pointer.
- Persisting the scan cache to disk as a source of truth — it is process-local and rebuildable only.
- Any new MCP tool (the `setups`/`edge_report` proxies already exist and stay byte-identical).

## DEFINITION OF DONE

- [ ] B1 boundary events additively carry the effective reaction horizon + boundary flag; the boundary regression test passes with **exact** values (definitive label, horizon-0 `return_fraction == None`, boundary flag `true`, effective horizon `< horizons[0]`) on a fixture/shape that actually reaches the recency boundary.
- [ ] Non-boundary `compute_setups` output is byte-identical to pre-change except the additive fields; the pinned AAPL 2026-06-22 event stays `rejected` with its recorded forward returns (test asserts exact values).
- [ ] The shared memoized scan cache serves `/research/setups`, `/research/setups/{id}`, `/research/edge-report`; byte-identity (cached == fresh), computed-once-per-unchanged-store, checksum-bust, and immutable-safety tests all pass.
- [ ] `GET /research/setups/{id}` still returns the exact `tape_timeline` join over the committed fixture (J-03 keyless substrate unbroken).
- [ ] Required-still-passing journeys J-01, J-02, J-04, J-07 remain green via deterministic replay; `config_fingerprint == 4d665603569b9dbf`; frozen files absent from the diff (only `setups.py` + owned cache helper + tests changed).
- [ ] No anti-goal violation introduced; coherence-auditor returns `COHERENCE-PASS` (the cache reads as a rebuildable accelerator of the one owner, not a second source of the setups value).
- [ ] Unit/integration tests pass; no regressions; full backend suite green.
- [ ] Dev handoff written at `docs/handoffs/goal-tradable_wall-iter-5-dev.md`.
- [ ] J-05's browser flip is explicitly deferred to iter-6 (NOT claimed here).

## TESTING REQUIREMENTS

- **Browser:** none required (`Frontend Present: no`; the full pipeline auto-N/A's the UI steps). Deterministic golden replay re-verifies J-01, J-02, J-04, J-07.
- **Unit/integration:**
  - B1: recency-boundary regression (populated-store shape) + non-boundary byte-identity incl. pinned AAPL 2026-06-22.
  - B3: cached==fresh byte-identity for all three endpoints; scan-computed-once (spy/counter); store-change checksum-bust; drill-in-then-list immutable-safety.
  - J-03 keyless: `/setups/{id}` `tape_timeline` join exact on the committed fixture slice.
  - Frozen guards: `config_fingerprint`, registry order, frozen-file diff-absence, `v1`/`structure_tape`/`edge_report` byte-identical outputs.
- **Error cases:** unknown `reaction`/`band_class` filter still 422; unknown `setup_id` still 404; edge-report dataset-integrity failure still 500 (no partial report); a store mutation busts the cache so no stale scan is ever served.

## NOTES

- **Apply lesson iter-2 (directly on-target for B1):** "the J-05 iter ... must resolve the contract: surface the effective horizon, flag/suppress the reaction, or exclude the event, with a boundary regression test ... verify recency-boundary behaviour on the populated store, not just the frozen fixture." → We chose **surface the effective horizon + a boundary flag** (additive disclosure, no label mutation, no exclusion). The regression test must run on a shape that reaches the boundary — the committed fixtures (stop 2026-06-30) do not.
- **Apply lesson iter-4:** "confirm the fixture's symbol/shape satisfies the feature's real-config dependencies, or commit a purpose-built fixture." → the B1 boundary fixture must genuinely produce a boundary event under the real config; a fixture that never truncates a horizon proves nothing.
- **Interpretation call logged** in `runs/goal-session-tradable_wall/state/assumptions.md` (iter-5 — goal-decomposer): the goal is silent on how a truncated-horizon boundary event should be presented; we build on *additive disclosure* (reversible).
- **Single-source watch for the coherence-auditor:** the B3 cache must not read as a second computer/source of the setups value. Implement it inside `setups.py` (memoizing the one `compute_setups` scan), keyed on store content, rebuildable, byte-identical — the same "cache, never a source of truth" contract the `bar_index` already lives under.
- **References:** `runs/goal-session-tradable_wall/iter-4/eval.md` (B1/B3 named as blocking, owned by J-05); backend routes `apps/backend/app/research/routes.py:1851` (`/setups`), `:1892` (`/setups/{id}`), `:2076` (`/edge-report`); `apps/backend/app/research/setups.py:205-234` (boundary/horizon logic), `:376` (`enrich_with_tape_timeline`, copy-on-write).
- **Sequel roadmap (continuity for the next decomposer):** iter-6 = pure-frontend J-05 render on this substrate (flips J-05); iter-7 = J-06 cockpit band overlay + descriptive chip. J-03's credentialed headline stays an operator-gated carry throughout.
