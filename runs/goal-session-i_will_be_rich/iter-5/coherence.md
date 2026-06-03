# Coherence Audit — goal-i_will_be_rich-iter-5

**Verdict:** COHERENCE-PASS

- **Session:** i_will_be_rich · **Iteration:** 5 (absorption pair: `bid_absorption` J-04 / `ask_absorption` J-05 + stream-status-dot consolidation)
- **Auditor:** coherence-auditor
- **Date:** 2026-06-03
- **Diff base:** `git diff 4497ca1bd4bd6667cbb4d17d177abf9dcd1a7c98` (working tree; iteration uncommitted)
- **Surfaces audited:** ui-surface-map present; 2 frontend components (`FeaturesPanel.tsx`, `TopBar.tsx`) on the single `/` cockpit + 2 newly-reachable states surfaced through existing panels; backend `features.py` / `classifier.py` / `observations.py` / `tape_engine.py` / `config.py` / `simulated.py`.

---

## Step 1 — Data Contract check (the "numbers don't match" gate) → PASS

Every value this iteration adds rides an **existing** contract row through its **registered single producer and single endpoint**. No duplicate computation, no non-canonical source found.

**Row "14 core features × 5 windows" (producer `FeatureEngine` → `GET /tape/{ticker}/features`).**
- The three new features `absorption_score` / `bid_refresh_score` / `ask_refresh_score` are added to `FEATURE_NAMES` and computed **inside `FeatureEngine._Window.compute()`** (`features.py:_refresh_fraction`, `features.py:_absorption_score`) — the one registered producer. No second producer, no new endpoint. ✔
- Frontend reads them by **key-lookup on the canonical features prop** — `FeaturesPanel.tsx:54` `const value = active[key]`, then `value.toFixed(decimals)`. Pure re-format for display (allowed); no client recomputation. ✔
- The existing 9 feature computations are preserved; `average_spread` still reads `q[3]` after the bid/ask were threaded into the quote tuple additively (`features.py` `_Window`/`add_quote`, `tape_engine.py:54` quote branch). No existing value changed its producer.

**Row "Tape state + confidence" (producer `TapeStateClassifier` → `GET /tape/{ticker}/state`).**
- `STATE_BID_ABSORPTION` / `STATE_ASK_ABSORPTION` are **already-enumerated values** of this row, produced by the two new gates in `TapeStateClassifier.classify` (`classifier.py`). Served via `/state`, re-exposed read-only by `/summary` + `WS /stream` (unchanged serializer paths). ✔
- **Not a duplicate computation:** `classifier._absorption_confidence` (the absorption *state confidence*, a weighted sum of 4 components clamped to `max_confidence`) is a distinct value from the `absorption_score` *feature* (`ratio_strength * flatness` in `FeatureEngine`). This mirrors the established `buy_price_impact` (feature) vs `_buyer_confidence` (state confidence) split — feature and state-confidence are separate registered concerns, each with one owner. No value is computed twice.

**Row "Observations + event-log messages" (producer = engine observation/transition emitter → `GET /tape/{ticker}/events`).**
- The absorption event-log line is emitted **once** in `ObservationEmitter._absorption_messages` (`observations.py`), driven from real in-window evidence (held bid/ask + `large_print_count`) threaded in from `tape_engine.py:_build_snapshot`. Per-tick absorption observations live in the classifier alongside the existing buyer/seller observations — same pattern, single source. The emitter imports `STATE_BID_ABSORPTION`/`STATE_ASK_ABSORPTION` from `classifier` rather than re-declaring the strings (single source of the state constants). ✔

**Row "Watched-scenario label + watch/stream status" — the consolidation (this is a coherence *improvement*).**
- `stream_status` remains a single canonical engine field: set in `tape_engine.py` (`connecting → live`) and `watch_manager.py` (`closed`), serialized identically from `snap.stream_status` across all three serializer paths (`serializers.py:51,80,96`), read into the snapshot in `api.ts:52`.
- `TopBar.tsx` now reads `snapshot.stream_status` via `STREAM_DOT` whenever a snapshot is present, **falling back to the client `connStatus` only for the pre-snapshot idle/connecting affordance** (`TopBar.tsx` `const dot = snapshot ? STREAM_DOT[...] : CONN_DOT[connStatus]`). This **removes** the parallel client-side "is the stream live" source rather than adding one — exactly the singularity fix the Data Contract's stream-status row calls for. No recomputation; the dot maps the canonical value to color/label (re-format). ✔

No new displayed value is unregistered: the absorption features and states are the previously-deferred fills of existing rows, now documented in the blueprint's additive realization note (below).

## Step 2 — Information Architecture check → PASS

- **No new route/page/shell.** All changes are within the single `/` cockpit HOME. ui-surface-map confirms: 0 new pages, 0 navigation changes.
- New feature readouts → existing **Features panel** (canonical home for features). New states → existing **Tape-state panel**. Absorption messages → existing **Observations / Event-log panels**. Stream-status → existing **top-bar dot**. Every new readout lands in a panel already registered as its canonical home in the blueprint IA. ✔
- No duplicate home (no second features/state/results page), no parallel shell/nav. Reachability unchanged: everything visible in ≤1 click after a ticker is watched. ✔

## Step 3 — Advisory observations → none

- Labels "Absorption score" / "Bid refresh score" / "Ask refresh score" are consistent with the existing feature-row label style; numerics are neutral 3-decimal (not color-by-sign), matching `average_spread`.
- The status-dot's amber for `stale`/`connecting` is a separate top-bar convention from the tape-state amber (absorption/unclear) on a different surface — no cross-surface label/color conflict introduced.
- `STREAM_DOT[...] ?? { color: "bg-slate-600", label: snapshot.stream_status }` is a benign defensive fallback; all four canonical `stream_status` values are mapped.

## Blueprint edit (additive-only governance) → conformant

The `blueprint.md` change is additive and requires no reapproval: (1) a clarifying note that the app-shell stream-status dot is driven by the canonical `snapshot.stream_status`, and (2) a new "Feature-set realization (additive log)" paragraph that explicitly records **no new contract row / no nav change** — the absorption triplet completes the existing "14 core features" row via `FeatureEngine` → `/features`, and the five tape states are already-enumerated values of the Tape-state row. Matches the iter spec's "Data-contract additions: None (rides existing contract rows)" and "Blueprint conformance: No new IA surface."

---

## Summary

Net-new absorption backend (features + classifier + provider + config + emitter) plus a frontend feature-row addition and the thrice-deferred stream-status-dot consolidation — all additive on existing Data-Contract rows, **one producer / one endpoint per value**, no new route or parallel shell, no recomputation in the API or frontend. The stream-status change **eliminates** a parallel client-side source. No objective Step 1 or Step 2 violation; no advisory issues. Matches the decomposer's predicted COHERENCE-PASS.
