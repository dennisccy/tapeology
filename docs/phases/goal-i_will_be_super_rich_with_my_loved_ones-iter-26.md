# Goal Iteration 26 — J-66 sound-cue toggle: move out of the thesis-conditional branch so it is visible on a fresh cockpit

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_will_be_super_rich_with_my_loved_ones
- **Iteration:** 26
- **Mode:** next
- **Depth:** lean
- **Frontend Present:** yes
- **Target journeys:** J-66
- **Required-still-passing journeys:** J-01, J-08, J-38, J-53, J-63, J-65, J-67, J-68
- **Anti-goal reminders (verbatim from `docs/goal.md`):**
  - No stock scanning or screening.
  - No news, theme, or sentiment analysis.
  - No chart-pattern scanning, technical-indicator studies, drawing tools, or multi-symbol / multi-pane charting. *(The one allowed chart is the focused price candlestick + tape-state-marker overlay for simulated/historical replay, used to evaluate whether a state predicts direction — not a general charting platform.)*
  - No fundamental analysis.
  - No trade execution, order placement, or broker/brokerage integration.
  - No portfolio or position management.
  - No machine learning in the first version — the MVP classifier is rule/threshold-based.
  - No multi-ticker dashboard or watchlist grid — the UI shows one ticker at a time.
  - No persistence of market/tape data. (Amended: a journal-scoped SQLite store is in scope for research records only; trades/quotes/candles/feature series remain unpersisted, committed test fixtures excepted.)
  - No claim or implication that the system is profitable, and nothing presented as trading advice.
  - No auto-detection or scanning: theses are user-declared on the one watched ticker; hints exist only there; studies run only over explicitly chosen windows; nothing watches the market for you.
  - No position sizing, account, capital, or P&L management; no currency P&L, equity curves, or win-rate-as-edge presentation anywhere — R statistics are journaled measurements with visible caveats and baselines, never performance claims.
  - No parameter optimizer, grid search, or auto-tuning of thresholds — research defaults are config-owned and validated by studies, never fitted by a machine.
  - No new market indicators: confirmation, stance, hints, and studies compose the EXISTING engine features and states only.

## GOAL

On a fresh `/` cockpit with no thesis declared, the optional sound-cue toggle is visibly present and OFF, so J-66's "its toggle is explicit" precondition passes — without changing any cue behaviour, copy, or anything else already green in J-66.

## BACKGROUND

J-66 (cue-discipline sweep) landed in iter-25 with 10/11 sub-legs green: the all-surface copy walk is clean on every research surface, the comprehensive copy-lint + seeded-violation counter-tests are committed and green, the iter-24 feed-stamp NOTE consolidated to `registry.config.historical_feed` with zero re-pins, and the sound cue's behaviour is correct (default OFF, transition-only fire, served cooldown, visible fired-indicator). The single failure is **placement only**: `SoundCue` is mounted inside the `ActiveThesis` branch (`apps/frontend/components/ThesisStrip.tsx:916`), which renders only when a thesis exists, so a fresh no-thesis cockpit shows no toggle anywhere (pixel-confirmed: `UT-J-66-cockpit-buyer-control.png` shows the declare-thesis line and no toggle). The iter-25 evaluator's next-step recommendation is to move the `SoundCue` mount into an always-rendered cockpit cue area so the toggle is discoverable on a fresh load; `cueKeyFor(thesis)` already returns `null` for a null/idle thesis, so the no-thesis toggle is inert (no live verdict ⇒ no fire) but visible. Depth is lean: a single frontend component, no backend, no data-contract change, no nav change; iter-25 coherence was COHERENCE-PASS so no consolidation pass is required.

## IN SCOPE

### Backend
- [ ] None. No backend file changes. The served taxonomy `sound_cue` copy and `sound_cue_cooldown_seconds` (row 24) are already in place from iter-25 and are read verbatim — do not add, rename, or re-serve anything.

### Frontend (if applicable)
- [ ] In `apps/frontend/components/ThesisStrip.tsx`, move the `SoundCue` mount **out of** the thesis-conditional `ActiveThesis` branch (currently `~line 916`, inside `ActiveThesis`'s `StripShell`) so it renders on **every** `ThesisStrip` state — including the idle no-thesis form state, the active-thesis state, and the not-evaluated surviving-thesis state. It must still receive `cueKey={cueKeyFor(thesis)}` (which is `null` when there is no thesis) and `taxonomy={taxonomy?.sound_cue}`.
- [ ] The toggle must default OFF on every fresh load (existing `SoundCue` behaviour — the toggle state is a client-local UI preference, never served or persisted). Do not change the OFF-by-default semantics, the transition-only fire, the served-cooldown enforcement, or the fired-indicator.
- [ ] Ensure the taxonomy load that supplies `sound_cue` copy is available in the idle no-thesis state. Today the taxonomy `useEffect` only fetches when the form is open or a thesis is active (`if ((!open && !thesis) || taxonomy) return;`). If the always-rendered toggle needs its copy on a fresh idle cockpit, extend that fetch condition (or the `SoundCue`'s own copy fallback) so the toggle renders its taxonomy-owned label even with no thesis and the form closed — without fabricating any copy client-side (a pre-J-66 backend that omits `sound_cue` ⇒ the toggle is silently absent, never hardcoded copy). Keep the idle-line zero-request promise intact only insofar as the cue toggle genuinely needs its copy; prefer fetching the already-cached taxonomy over inventing strings.

### New user-facing capability
The optional sound-cue toggle is now reachable from the cockpit cue area at all times — including immediately on a fresh `/` load before any thesis is declared — so a user can opt the cue ON (or confirm it is OFF) without first declaring a thesis.

### New information displayed
None beyond what iter-25 already shipped. The same toggle (label + OFF-by-default control + fired-indicator) is simply now also visible in the no-thesis cockpit state.

### New user actions
None new. The existing toggle control is relocated to an always-rendered position; flipping it ON/OFF is the same action as in iter-25.

### UI surface changes
`/` cockpit thesis-strip / cue area only. The `SoundCue` control moves from the thesis-conditional `ActiveThesis` `StripShell` to an always-rendered position so it appears in the idle, active, and not-evaluated strip states alike. No other panel, page, or layout changes.

### Product surface delta
The cue control becomes consistently discoverable: previously it appeared only once a thesis existed; now it is a stable part of the cockpit cue area regardless of thesis state. Behaviour is identical (inert with no live verdict, fires only on a real verdict/stance transition once a thesis is live).

### Blueprint conformance
No new surfaces and no nav-skeleton change. The sound-cue toggle's canonical home is the `/` Cockpit cue area ("J-66 (copy discipline) | all research surfaces | all" in `blueprint.md` Information Architecture; iter-25 coherence already confirmed the Cockpit cue area as its pre-registered home). This iteration only relocates the toggle within that same home so it is rendered unconditionally. An additive iter-26 build-out note is added to `blueprint.md` recording the always-rendered placement.

### Data-contract additions
None. No new displayed value, no new computing module, no new serving endpoint. The toggle reads the already-registered row-24 taxonomy `sound_cue` copy + `sound_cue_cooldown_seconds` verbatim, and the change-detection `cueKey` is derived (as in iter-25) from the row-15 projection's `verdict` / `management_stance` / `entry_checklist.stance` values served verbatim — no second computation or fetch.

## OUT OF SCOPE

- Any backend change (taxonomy, config, routes, research modules, engine, providers). The suite must stay byte-identical — zero re-pins.
- Re-litigating the J-66 copy walk, the copy-lint test, the seeded-violation counter-tests, or the false-positive guards — all already green; do not touch them.
- Re-litigating the feed-stamp consolidation (already closed in iter-25).
- Changing the sound cue's fire logic, cooldown, default-OFF semantics, or fired-indicator.
- The J-68 backlog (the J-11 / J-14 / J-16 / J-18 / J-20 / J-22 / J-23 / J-27 / J-28 / J-29 / J-32 partial legs and J-15 gated) — a separate later market-hours iteration.
- The J-67 market-hours-gated live-IEX pixel legs (next US open 15-06-2026 14:30 UTC+01:00) — out of scope on a closed market; do not fake them.
- Any nav, route, or new-page change.

## DEFINITION OF DONE

- [ ] J-66 passes via browser-qa-agent, with **both** previously failing preconditions re-verified in fresh pixels: (1) a fresh `/` load with **no thesis** shows the sound-cue toggle visibly present and OFF (`aria-checked=false`); (2) once a thesis is declared and a real verdict/stance transition occurs, the toggle still fires the indicator (transition-only) and respects the served cooldown.
- [ ] Required-still-passing journeys remain green: J-01, J-08, J-38, J-53, J-63, J-65, J-67, J-68 — in particular J-68's regression-sentinel clause: the always-rendered toggle is an additive cue-area surface at its pre-registered home, not a sentinel violation, and the no-thesis cockpit is otherwise unchanged (thesis strip still idles as the single declare affordance, all panels in place).
- [ ] No anti-goal violation introduced (no imperative/prediction/profit copy; the toggle copy is the unchanged taxonomy-owned descriptive register).
- [ ] Unit tests pass with no regressions; backend suite stays byte-identical (zero re-pins; no app/engine/ or app/providers/ change). Frontend type-checks/builds clean.
- [ ] Dev handoff written at `docs/handoffs/goal-i_will_be_super_rich_with_my_loved_ones-iter-26-dev.md`.

## TESTING REQUIREMENTS

- Browser (by ID): **J-66** — capture (a) a fresh no-thesis `/` cockpit showing the toggle present and OFF, and (b) the toggle firing its indicator on a real verdict/stance transition once a thesis is live (re-use the iter-25 SIM-BUYER declare host). Spot-confirm **J-68**'s no-thesis cockpit is otherwise unchanged and the always-rendered toggle is the only additive cue-area surface. Confirm **J-01 / J-08 / J-38 / J-53 / J-63 / J-65** are not visually disrupted by the relocated toggle (it must not displace the entry checklist, management stance, hint dock, or panel grid).
- Unit/integration: this is a frontend-only relocation; the existing backend suite (`cd apps/backend && .venv/bin/python -m pytest tests/ -v`) must still pass with the same counts and zero re-pins. If `SoundCue` or `ThesisStrip` has any existing frontend assertion/type contract, keep it satisfied; the frontend must `npm run build` clean.
- Error cases: a backend that omits `sound_cue` from the taxonomy payload (pre-J-66 shape) ⇒ the toggle is silently absent (no fabricated copy). With no thesis, the toggle is inert (`cueKey` null ⇒ no fire) but visible and OFF.

## NOTES

- Exact target: `apps/frontend/components/ThesisStrip.tsx`. The `SoundCue` mount is at `~line 916` inside the `ActiveThesis` `StripShell` (`return (<StripShell> … <SoundCue … /></StripShell>)` at lines `615`–`917`). The three other strip render branches (idle/form `StripShell` ending `~line 1204`; the early `NotEvaluatedThesis` and the taxonomy-error/loading `StripShell`s) currently do **not** render `SoundCue`. The cleanest relocation is to render `SoundCue` once in a position that all states share — e.g. inside the shared `StripShell` wrapper, or appended to each branch's `StripShell` — so the toggle is unconditional while `cueKeyFor(thesis)` stays the single source of the change-detection key (it already returns `null` for `null`/idle theses, per `cueKeyFor` at `lines 25–30`, so an idle toggle is inert).
- `cueKeyFor(thesis)` reads `thesis.verdict`, `thesis.management_stance?.value`, and `thesis.entry_checklist?.stance.value` — all row-15-projection values served verbatim (confirmed COHERENCE-PASS in iter-25). Do not add any new derivation; concatenating two served values for change-detection is a re-format, not a recomputation.
- Lesson applied (QA frontend build caution, from auto-memory): do **not** run `npm run build` against the live QA-harness dev server's shared `.next`, and do **not** `git checkout` unstaged iter files — let the harness manage the frontend build/server.
- Evaluator next-step (iter-25) drives this scope verbatim: "lean, placement-only fix for J-66 — move the SoundCue mount out of the thesis-conditional ActiveThesis branch … into an always-rendered `/` cockpit cue/status area … Re-verify only the two failing preconditions in pixels; do not re-litigate the copy walk or lint."
- After J-66 flips green, the only remaining work before GOAL_ACHIEVED consideration is the J-68 backlog (the listed partial legs + J-15 gated) and J-67's market-hours-gated live-IEX pixel legs (next US open 15-06-2026 14:30 UTC+01:00). Both are out of scope here; flag for a later market-hours iteration.
