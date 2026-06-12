# goal-i_will_be_super_rich_with_my_loved_ones-iter-23 Dev Handoff

**Phase:** goal-i_will_be_super_rich_with_my_loved_ones-iter-23 (J-65 — setup-forming hints: descriptive, gated, logged)
**Date:** 2026-06-12
**Agent:** developer
**Status:** complete

## What Was Built

The last unbuilt cue surface (J-65): a descriptive, dwell-gated "setup forming" hint on the watched ticker — logged, baseline-cited, never imperative — plus its hint dock on `/` and hint log in `/journal`.

### Backend
- **Hint engine, single owner** — new `apps/backend/app/research/hints.py`: a pure, deterministic, **logical-time** evaluator (`HintEngine`) driven by the research monitor's `on_event` / `on_status` observer seam. Observer-only — NO engine/classifier/feature file touched; runs inside the monitor's existing exception isolation (a hint failure surfaces `monitor_status: failed`, never a dead feeder). Attached per watched ticker at monitor creation **regardless of any thesis**, so hints fire with no thesis declared.
- **State-native patterns** (existing engine states + logical time only): sustained `bid_absorption` → absorption_reversal/long; sustained `ask_absorption` → absorption_reversal/short; sustained `buyer_control` → trend_continuation/long; sustained `seller_control` → trend_continuation/short. `unclear` never fires; level setups have no state-native arming.
- **Config-owned dwell + cooldown** (`hint_sustain_dwell_seconds=5.0`, `hint_cooldown_seconds=180.0`) — documented research defaults, logical-time, deterministic, **IN `config_fingerprint`** (they shape persisted records — the study-arming precedent). A serving-only `hint_log_max=200` is **excluded** from the fingerprint (the page-size precedent). Calibrated so SIM-BIDABS fires within a browser-verifiable wait (10 sustained events ≈ 0.4s wall) and SIM-CHOP's flapping never sustains.
- **Fire-once record** — when a pattern sustains past the dwell, the hint is produced ONCE (pattern id, plain-language evidence with the measured sustain duration, setup context + direction, baseline citation, bound source + `data_feed` + `config_fingerprint`, logical + wall ts) and persisted to the existing **v7** `hints` table via the single writer queue (never from the event/WS path). No duplicate on continued sustain; the cooldown gates same-pattern re-fires.
- **Baseline citation, produced once at fire** — reads the user's most recent PERSISTED `done` study matching that setup_type + `data_feed` + `config_fingerprint` (hindsight_level excluded) and cites the STORED aggregates verbatim (n + first-horizon ternary distribution); when none exists the citation is exactly **"no studied baseline — unvalidated pattern"**.
- **Active-hint lifecycle** — the hint stays active while its pattern's state persists; clears on state-leave, on any non-live status flip (paused/stale/closed/failed), and on a non-live event (J-64 freshness). Clearing never touches the persisted log record.
- **Serving** — `GET /research/hints/active?ticker=` (`hint: null` is normal) == the additive **WS `hint` key** verbatim (the `thesis`-key precedent; merged at the send site so engine serializers stay byte-identical); `GET /research/hints?ticker=&limit=&offset=` for the log (newest-first, config-owned serving-only page size).
- **Declared-from linkage** — `POST /research/thesis` gains an optional additive `declared_from_hint_id`: unknown/invalid id → **422**; a valid id links the created thesis and flips the hint record's payload (`declared_from`) via the writer queue, recorded ONLY when the declaration completes (one click never creates a thesis).
- **Taxonomy (additive)** — `GET /research/taxonomy` gains a `hints` block: pattern labels, present-tense evidence templates, the exact unvalidated string, the dock title + register line, the declared-from label, hint-log column labels, and the honest empty-state copy. Frontend hardcodes none.

### Frontend
- **`HintDock`** under the tape-state panel on `/` (its blueprint home): renders the served active hint VERBATIM (pattern + evidence, baseline citation, declare affordance), visible only when a hint is active (no empty-state chrome). Amber/neutral design-system styling.
- **Declare affordance** prefills the thesis strip's declare form (setup + direction via a `prefill` prop lifted to the page); `invalidation_price` stays empty + required; submit passes `declared_from_hint_id`. Hidden while a thesis is already active (no dead control / no 409).
- **`/journal` hint log** — a third in-page view (theses | analytics | hints), NO new route, NO nav change: rows verbatim (time via the shared `dd-MM-yyyy` formatter, ticker, pattern, evidence, baseline citation, declared-from), labels + empty-state from taxonomy.

## Files Changed
- `apps/backend/app/config.py` -- two hint timing keys (IN fingerprint) + serving-only `hint_log_max` (excluded).
- `apps/backend/app/research/hints.py` -- NEW: the hint engine + baseline-citation helper.
- `apps/backend/app/research/store.py` -- `HintRecord` + `insert_hint` / `get_hint` / `list_hints` / `mark_hint_declared_from` / `latest_done_study_for`.
- `apps/backend/app/research/monitor.py` -- wires the `HintEngine` into `on_event`/`on_status` (thesis-independent) + `hint_projection()`; constructor takes the ticker.
- `apps/backend/app/research/taxonomy.py` -- the `hints` copy block + helpers; added to `taxonomy_payload`.
- `apps/backend/app/research/routes.py` -- `GET /research/hints/active`, `GET /research/hints`, `registry.hint_projection_for`, `declared_from_hint_id` (422 + linkage), monitor ticker.
- `apps/backend/app/main.py` -- the additive WS `hint` key (`_hint_projection`).
- `apps/backend/tests/test_research_hints.py` -- NEW: 29 unit tests.
- `apps/backend/tests/test_research_hints_api.py` -- NEW: 13 API/WS integration tests.
- `apps/frontend/lib/types.ts` -- `Hint`, `HintsTaxonomy`, the snapshot `hint` key, taxonomy `hints`.
- `apps/frontend/lib/api.ts` -- `fetchActiveHint`, `fetchHints`, `declared_from_hint_id` on `declareThesis`.
- `apps/frontend/components/HintDock.tsx` -- NEW: the cockpit hint dock.
- `apps/frontend/components/HintLog.tsx` -- NEW: the journal hint-log table.
- `apps/frontend/components/Cockpit.tsx` -- renders `HintDock` under the tape-state panel.
- `apps/frontend/components/ThesisStrip.tsx` -- `prefill` prop + `declared_from_hint_id` on submit.
- `apps/frontend/app/page.tsx` -- the prefill state + `handleHintDeclare` wiring.
- `apps/frontend/app/journal/page.tsx` -- the third "Hints" in-page view.

## Tests Run
Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -v`
Result: **801 passed, 1 skipped** (exit 0; 7m00s). +42 new tests (29 unit + 13 API/WS). Observer-equivalence green with the hint engine attached and firing (byte-identical snapshots; zero re-pins). The 1 skip is the pre-existing credentialed live-integration test.

Command: `cd apps/frontend && npm run build`
Result: exit 0 — type-check + compile clean, all routes built.

### Coverage of the spec's testing requirements
- Dwell fires deterministically at exactly the configured logical-time dwell; flapping/unclear never fire; cooldown suppresses a same-pattern re-fire — covered.
- Pattern→setup/direction for all four states; `unclear` produces nothing — covered (parametrized).
- Citation: matching study cited verbatim; no study / feed mismatch / fingerprint mismatch / hindsight-only all → the exact unvalidated string — covered.
- Persistence: stamps + writer queue + fire-once (no duplicate on continued sustain) — covered.
- REST == WS verbatim (incl. `hint: null`); log paginates + filters by ticker — covered.
- Declared-from: valid id links + flips; prefill alone creates nothing; unknown id → 422 — covered.
- Freshness: paused/stale/closed/failed clear the active hint; the log record survives — covered (parametrized + live pause integration).
- Observer-equivalence with the hint engine; a hint exception → `monitor_status: failed`, feeder alive — covered.

## Known Issues
- **Bound-socket service smoke test could not run in this sandbox.** A real `uvicorn` listening on a port is blocked here (the server process exits before binding; curl gets connection-refused). The full HTTP/WS path is instead proven by the in-process ASGI `TestClient` integration suite (13 tests), which drives the real app: watch → warm → hint fire → REST → WS → declare-from → pause-clears. This is an environment limitation, not a code defect. An operator with a normal shell can verify live via `bash scripts/dev.sh`.
- Two `next dev` processes from the unrelated **trendora** project (port 3835) were already running before this session and were left untouched (out of scope — different repo). No tapeology server processes are left running.
- Browser QA (the J-65 four-leg acceptance + the required-still-passing journeys) is the next pipeline step — not run here. The iter-22 evidence-bookkeeping lesson applies: the browser agent must checksum the evidence directory and verify each capture actually shows the claimed state (the hint card past the dwell, the exact unvalidated string, SIM-CHOP showing no hint, the log row with its declared-from flag).
- **Blueprint:** rows 22/24, the config-defaults registration, the IA, and the J-65 feature-homes row were already updated by the goal-decomposer to describe exactly this build-out; what shipped matches them — no blueprint edit was needed.
