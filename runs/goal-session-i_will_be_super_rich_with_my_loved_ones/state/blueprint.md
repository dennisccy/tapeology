# App Blueprint — i_will_be_super_rich_with_my_loved_ones

> **Tapeology — research evolution.** Status: APPROVED (human-approved 10-06-2026; `blueprint.approved` marker present).
> Carries forward the APPROVED contract of sessions `i_will_be_rich` + `i_will_be_super_rich`
> (J-01–J-37 built & in force: rows 1–13 below, unchanged) and registers the research evolution
> (J-38–J-68: theses, verdicts, journal, review, excursions, analytics, studies, then cues).
> Source: `docs/goal.md` — Product Shape, Canonical values, Key Capabilities 20–34.
>
> **Governing principles (unchanged):** single-ticker tape cockpit; every value computed exactly
> once and read identically by REST/WS/UI; provider-agnostic engine, one vendor adapter;
> price impact, not raw aggression; honest failure states, never fabricated data; one focused chart.
> **New for this session:** the research layer attaches ONLY via the engine's snapshot observers
> (capability 20) and is read-only over the engine — byte-identical engine outputs with or without
> it (equivalence-tested); journal-scoped SQLite persists research records only (no tape data);
> every research record is stamped with bound source + `data_feed` + `config_fingerprint`;
> **build order is binding: cues (J-63–J-67) only after evidence (J-58–J-62) passes.**

## Information Architecture

**Layout shell:** dark instrument-panel; persistent top bar gains the first multi-page nav:
**Cockpit · Journal · Studies**. The cockpit stays the home and stays one screen.

```
Tapeology (top bar: Cockpit · Journal · Studies)
├── Cockpit  /              — the tape cockpit (HOME; all J-01–J-37 surfaces unchanged)
│     + price chart now renders in ALL modes incl. live, carrying thesis geometry
│     + thesis strip (between chart and panel grid): declare affordance → active thesis
│       (setup, direction, invalidation, statement statuses, verdict + evidence, risk-flag
│       chips, resolve / mark-entry / mark-exit) → later the checklist/stance (cue layer)
│     + hint dock (under the tape-state panel): current setup-forming hint when active
├── Journal  /journal       — filterable thesis table · hint log · analytics view
│   └── /journal/[id]       — review detail: frozen statements + verdict timeline (true clock
│                             time), risk flags, action marks, execution checks, excursions,
│                             outcome × process quadrant, mistake-tag picker, "re-watch window"
└── Studies  /studies       — create/monitor replay studies (job status/progress/cancel);
                              results: occurrences + aggregates vs seeded null baseline,
                              hindsight_level / truncation labels, feed + fingerprint stamps
```

**Feature / journey homes** (≤2 clicks from the nav):

| Feature / journey | Canonical home (route) | Nav section |
|---|---|---|
| J-01–J-37 (cockpit, chart, watch lifecycle, real data) | `/` | Cockpit |
| J-38–J-46, J-49, J-50, J-52, J-53 (declare, verdicts, flags, resolve, marks, stance) | `/` thesis strip | Cockpit |
| J-47 (source binding / survives interruption) | `/` thesis strip + `/journal` row | Cockpit / Journal |
| J-48 (thesis geometry) | `/` chart pane | Cockpit |
| J-51, J-55–J-57 (persistence, review, grades, tags) | `/journal` → `/journal/[id]` | Journal |
| J-54, J-58 (execution checks, excursions) | `/journal/[id]` | Journal |
| J-59 (segregated analytics) | `/journal` analytics view | Journal |
| J-60–J-62 (replay studies + CI reference study) | `/studies` | Studies |
| J-63, J-64 (entry checklist / stance + freshness) — built LAST | `/` thesis strip | Cockpit |
| J-65 (hints, logged) | `/` hint dock + `/journal` hint log | Cockpit / Journal |
| J-66 (copy discipline), J-67 (feed labels) | all research surfaces / live feed badge + stamps | all |
| J-68 (regression sentinel) | `/` cockpit unchanged with no thesis | Cockpit |

No watchlist grid, no multi-symbol view, no execution/order affordance anywhere.

## Data Contract

Rows 1–13 are **built & in force** (approved in prior sessions; owners unchanged — listed compactly).
Rows 14–27 are the research evolution, to be built by this session. `…/summary` and `WS /stream`
re-expose the snapshot and never recompute; no page recomputes or re-fetches any row from elsewhere.

| # | Value / entity | Computed by (single owner) | Served by (single endpoint) | Notes |
|---|---|---|---|---|
| 1 | Tape state + confidence | `TapeStateClassifier` (relative spread/impact gates; spread = graded factor, not veto; SIP historical / IEX live feed inside the one adapter) | `GET /tape/{t}/state` | re-exposed by `/summary`, WS |
| 2 | 14 core features × 5 windows | `FeatureEngine` | `GET /tape/{t}/features` | re-exposed by `/summary`, WS |
| 3 | bid / ask / spread / last | `MarketState` (spread = ask − bid) | `GET /tape/{t}/summary` | re-exposed by WS |
| 4 | Recent trades (price/size/side) | Aggressor classifier (quote rule + tick-test fallback) | `GET /tape/{t}/events` | re-exposed by WS |
| 5 | Observations + event-log messages | Engine transition emitter | `GET /tape/{t}/events` | re-exposed by WS |
| 6 | Watched source + stream status (connecting/waiting/live/stale/paused/failed/closed) | Engine/feeder — one writer | `GET /tape/{t}/summary` | re-exposed by WS; lifecycle via `/watch` + pause/resume/speed |
| 7 | Symbol search results | Vendor adapter (warmed `_ASSET_UNIVERSE`) | `GET /symbols/search?q=` | hiccup ⇒ empty list |
| 8 | Market clock | Vendor adapter clock module | `GET /market/clock` | live status indicator |
| 9 | Real-data failure states (unavailable / unknown symbol / no data / closed / provider_timeout) | Providers + adapter (real call-level deadline; backend bound < frontend timeout) | `POST /watch/{t}` error path | UI non-cockpit states |
| 10 | OHLC bars + tape-state markers | Engine history buffer | `GET /tape/{t}/history?bar=` | chart reads verbatim, all modes |
| 11 | Paused state | Engine/feeder | `/summary` (set via pause/resume) | re-exposed by WS |
| 12 | Resolved historical window (local tz, quick-picks) | `apps/frontend/lib/datetime.ts` resolver (once, pre-fetch) | `POST /watch/{t}` body | no second tz conversion |
| 13 | Display/epoch anchor (true-clock axis; live = first record's epoch) | Engine/feeder (display metadata only) | `GET /tape/{t}/history` projection + snapshot | chart stamps axis verbatim |
| 14 | **`delivery_lag_seconds`** | Feeder (latest record epoch vs wall clock) | snapshot via `GET /tape/{t}/summary` + WS | UI lag readout AND the `tape_lag_ok` check read this same value |
| 15 | **Thesis projection** (fields, frozen expected-behaviour statements + live statuses, verdict + evidence, risk flags, monitor_status) | Research monitor (engine snapshot observer; exception-isolated) | `GET /research/thesis/active?ticker=` | WS `thesis` key MUST equal it verbatim; thesis strip + chart geometry read it; `thesis: null` is normal. **Iter-9 (additive):** a surviving entry-marked active thesis with no live monitor (ticker unwatched, or watched on a mismatched source) is served by this SAME endpoint via the SAME projection builder from the persisted record, flagged with an explicit not-evaluated `monitor_status` + bound-source notice — never a second computation path or endpoint. **Iter-10 (additive):** the projection gains a **`geometry`** key — chart-ready thesis geometry (labeled invalidation/level price-lines at the declared prices; verdict-transition, entry/exit, and first-confirmation markers with their logical + wall timestamps) — computed ONLY inside the same single `build_projection` as a pure projection of the thesis fields + the row-16 append-only timeline + row-18 marks (current evaluation segment only: events before the latest `watch_restarted` gap are omitted from geometry, never misplaced on a foreign axis); served by this same endpoint + the WS `thesis` key; the chart draws it verbatim on the row-13 epoch anchor and computes no state/side/price/time basis of its own. **Iter-11 (additive):** the projection gains a **`risk_flags`** key — the row-17 entry risk flags (flag name + measured plain-language evidence values), computed ONCE at declaration by the research monitor's single flag function inside `POST /research/thesis`, frozen on the persisted thesis (schema v4 migration, never backfilled), and re-exposed VERBATIM by this same single `build_projection` (live and surviving paths alike) + the WS `thesis` key + `GET /research/journal/{id}`; chip labels/evidence copy from row-24 taxonomy; key ABSENT = never assessed (pre-migration row), empty list = assessed-and-clean; never recomputed at read, never a second computation or serving path |
| 16 | **Published verdict timeline** (append-only, with gap events; `rule_first_true` + `published_at`) | Verdict engine → journal repository (single writer queue; repo exposes no update/delete) | `GET /research/journal/{id}` | rendered verbatim; never recomputed at read. **Iter-9 (additive):** gap events (e.g. `watch_restarted` on matching-source re-attach) are appended timeline rows written by the same single writer — never edits or backfill |
| 17 | **Entry risk flags** | Computed once at declaration by the research monitor; frozen on the thesis | `POST /research/thesis` response → row 15 / journal | advisory, never blocking; incoherent input = 422, never a flag |
| 18 | **Action marks** (entry/exit, verbatim price + logical & wall time + **spread-at-mark stamped once at recording** from the current snapshot — a moment value, never recomputed) | `POST /research/thesis/{id}/action` (recorded as stated, never inferred) | row 15 projection + `GET /research/journal/{id}` | chart marks + strip read it; entry-marked ⇒ no Abandon |
| 19 | **Thesis resolution + execution checks + outcome × process grades** | Computed once at resolution (`POST /research/thesis/{id}/resolve`); persisted | `GET /research/journal/{id}` | user resolutions = `played_out \| abandoned` ONLY (system owns `invalidated`/`expired` → 422); 409 already-resolved; entry-marked refuses abandon; the resolution is an APPENDED timeline event + status flip (logical + wall timestamps), never an edit; enum labels from evidence-backed checks; never numeric scores |
| 20 | **Excursion outcomes** (R-unit ternary per horizon; spread-at-mark; truncation flags; confirmation- vs entry-anchored populations never pooled) | Excursion calculator at marks / first confirmation / stream end; persisted | `GET /research/journal/{id}` | analytics aggregates persisted rows only |
| 21 | **Journal rows + analytics aggregates** (segregated by `data_feed` + `config_fingerprint`; abandonment bucket always visible; "insufficient sample" under min-n) | Analytics module over persisted rows ONLY | `GET /research/journal`, `GET /research/analytics` | `/journal` renders; no pooling across feeds/fingerprints |
| 22 | **Hints** (pattern, evidence, baseline citation or "no studied baseline") | Hint engine — produced once when shown; every shown hint logged | hint log (journal store; read via `/journal` hint log) | hint dock + log read the same record; sustain-dwell + cooldown gated |
| 23 | **Study results** (occurrence rows, aggregates, seeded null baseline, status/progress) | Study runner (cancellable background job); persisted | `POST/GET /research/studies`, `GET /research/studies/{id}`, `POST …/cancel` | `/studies` renders stored results; deterministic re-runs |
| 24 | **Taxonomies + research display copy** (setups, flags, tags, verdict/stance enums) | Backend taxonomy module | `GET /research/taxonomy` | frontend hardcodes none of them |
| 25 | **Entry checklist + management stance** (named checks with live margins; `conditions_met/…/no_fresh_tape`; `thesis_intact/…`) — **cue layer, built LAST (after J-58–J-62 pass)** | Stance evaluator, computed once server-side; publishes through its own dwell | row 15 projection (additive keys) | UI renders margins verbatim, derives nothing |
| 26 | **Source / `data_feed` / `config_fingerprint` stamps** | Assigned once at record creation (fingerprint hashed over the ENTIRE frozen config) | stored on every research record; shown wherever the record is shown | a thesis is never evaluated against a different source than declared |
| 27 | **Realized move in R + R basis + spread-at-mark display** (R = \|entry − invalidation\|; realized move signed by direction; present ONLY when the marks exist — no marks ⇒ no realized metric, no dishonest zero) | ONE research projection function, computed once server-side from row-18 recorded marks + the thesis invalidation (no client-side arithmetic) | row 15 projection + `GET /research/journal/{id}` | strip renders verbatim, labeled a journaled measurement with spread-at-mark beside it — never currency P&L; distinct from row 20 (excursion horizon populations); feeds row 21's acted-trade R distribution later via the same computed values, never a second path |

**Persistence (scoped).** Journal store = stdlib `sqlite3` (WAL, `busy_timeout`, `BEGIN IMMEDIATE`,
one writer queue — never written from event processing or the WS serialization path). Tables:
theses, verdict_events (append-only), hints, actions, studies, study_occurrences, schema_version.
Env-configured DB path; tests inject a temp path. No tape data persisted (committed fixtures excepted).
**Schema evolution ships a versioned migration** (bump `journal_schema_version` + in-place `ALTER`
of older DBs in one writer transaction, never backfilling append-only rows), proven by a test against
a committed old-schema fixture — `CREATE TABLE IF NOT EXISTS` alone is never a migration (iter-4 lesson).

**New sim scenarios.** `SIM-SHIFT` and `SIM-REVERSAL` (capability 21) are provider-level only —
seeded, documented like the existing five; the engine is untouched.

**Config.** Every new research value (per-setup dwell, stance dwell, chase threshold, invalidation
ε / k robustness, hint sustain + cooldown, excursion horizons, timeline cap, min sample size,
delivery-lag bound, study null-arm count) lives in config as a documented research default —
no magic numbers in research code.
