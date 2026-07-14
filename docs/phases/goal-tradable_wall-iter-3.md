# Goal Iteration 3 — J-03: tape-at-the-wall — the keyless recording + engine-replay join substrate

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** tradable_wall
- **Iteration:** 3
- **Mode:** next
- **Depth:** full
- **Frontend Present:** no
- **Target journeys:** J-03
- **Required-still-passing journeys:** J-01, J-02, J-07
- **Anti-goal reminders (verbatim — the rails this iteration must respect):**
  - **No execution path, ever** — no brokerage/trading API, no order tickets, no live OR paper trading, no "just to test" exceptions. (`apps/backend/tests/test_no_execution_path.py` is the tier-1 guard; new research code adds matching guard tests, never weakens them.) *(critical)*
  - **Frozen foundations** — the `v1` strategy, the `default` profile, the tape engine's five states and thresholds, the frozen structure computations, the JSON `BarStore`, and archived-era behaviour stay byte-identical. New work is additive and versioned beside them, never a mutation of them. *(critical)*
  - **No lookahead** — every value computed as-of T uses only events/bars fully completed at T. *(critical)*
  - **Single source of truth** — each shared value is computed once, owned by one canonical endpoint, and read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor hard-fails violations. *(critical)*
  - **Read-only MCP** — MCP tools remain byte-identical proxies of GET endpoints; nothing on the MCP surface can change state. *(critical)*
  - **Immutable data** — registered datasets and bar series are append-only, checksummed, never re-tagged, never deleted, never content-perturbed. Splits are frozen at registration. *(critical)*
  - **Persistence stays scoped** — no ambient recording of live streams; recording/fetching is an explicit, logged act. *(critical)*
  - **Recording stays explicit, windowed, and logged** — only around registered scan events with config-owned padding; no ambient, scheduled, or full-day bulk recording; every dataset append-only, checksummed, split-frozen at registration. *(critical)*
  - **Feed honesty — never pool across feeds.** The `feed` stamp comes verbatim from the adapter/key tier; `iex`, `sip`, and Yahoo-bar lineages are never pooled in any analysis cell, report row, or claim; `iex` is never presented as the consolidated tape. *(critical)*
  - **Keys never committed, never logged.** Alpaca credentials live only in the operator's environment; no secret in source, fixtures, logs, artifacts, or reports. *(critical)*

## GOAL

Put the frozen five-state tape at the wall: a recording driver captures event-window trade/quote datasets around the top-ranked band-touch events, and each recorded window's tape timeline is joined onto the case-study drill-in (`GET /research/setups/{id}`) — delivered and CI-verified **keyless**, with the ≥10-window credentialed recording honestly gated behind operator Alpaca credentials.

## BACKGROUND

J-03 is the dependency-order unblocker (J-01→J-02→**J-03**→J-04, then J-05/J-06 surface them): J-04 backtests over the recorded event datasets and J-05 renders the drill-in tape timeline — both are downstream of the substrate this iteration builds, so building J-03's keyless substrate before J-04/J-05 avoids double rework (rubric rule 3). The evaluator (iter-2) recommended J-03 at depth **full** and explicitly handed the decomposer the credential-split decision; **I verified `ALPACA_API_KEY`/`ALPACA_API_SECRET`/`TAPEOLOGY_LIVE_INTEGRATION` are all unset in this environment**, so the credentialed acceptance headline (≥10 windows across ≥5 symbols incl. the pinned AAPL 06-22 real recording) is operator-blocked — it will be honestly recorded as blocked, never simulated — while the keyless join substrate (recorder wiring + `TapeEngine`-replay join + ONE committed tick-fixture slice + full keyless CI) is agent-buildable now and is this iteration's deliverable. Depth = full: this is a credentialed provider integration touching the `DatasetStore` immutable-data path, the frozen-engine replay, and the critical feed-honesty / no-pooling / keys-never-committed rails, and it needs new integration tests beyond browser smoke (prior depth was full; evaluator recommended full). The infrastructure already exists and is REUSED, not rebuilt: `record_from_source` (datasets.py:362, injectable `historical_fetch` seam + keyless `SOURCE_REFERENCE` path), `POST/GET /research/datasets` + `/{id}`, and `GET /research/setups/{id}` whose `tape_timeline` field is already "present but honestly empty until J-03 records."

## IN SCOPE

### Backend
- [ ] **Event-window recording driver** (new script under `apps/backend/scripts/`, mirroring the iter-2 `populate_panel_bars.py` operator-script precedent): enumerate the top-ranked scan events from `GET /research/setups`, compute each event's window with **config-owned padding** (touch −60 min … +90 min), and record each window via the **existing** `record_from_source` into a registered `DatasetStore` dataset (append-only, checksummed, `feed` stamped verbatim from the adapter tier, split assigned at registration by the config-owned seeded rule). The credentialed full run uses the existing Alpaca `historical_fetch` seam; CI drives the keyless `SOURCE_REFERENCE` / committed-fixture path. Recording is explicit and logged — no ambient/scheduled/bulk recording.
- [ ] **Tape-at-the-wall join** onto `GET /research/setups/{id}`: for a recorded event, replay its recorded `DatasetStore` window through the **frozen `TapeEngine`** and attach the five-state timeline (states + transition times around the touch) to the drill-in's existing `tape_timeline` field. `setups.py` joins the engine replay **verbatim** — it never reimplements the state machine and never recomputes a tape state. Events with no recorded dataset keep an honestly-empty `tape_timeline`.
- [ ] **ONE new small committed tick-fixture slice** under `apps/backend/tests/fixtures/` (a short recorded event window; may reuse/slice an existing committed fixture) — honestly `feed`-stamped verbatim, used ONLY to exercise the join-path mechanics keyless in CI (never pooled with, or presented as, a different feed).
- [ ] **Config-owned constants** (pre-registered, no magic numbers): recording pre/post padding, the top-ranked event-selection cap, reusing the existing seeded split rule — added to the `config_fingerprint` **exclusion set** (mirroring the `tradability_*` / `setups_*` precedent) so the fingerprint stays `4d665603569b9dbf`.
- [ ] **Tests** (see TESTING REQUIREMENTS): keyless join-path assertion, `DatasetStore` immutable-data discipline, feed-stamp-verbatim, no-credential-in-artifacts grep, frozen-foundation byte-identity + fingerprint, and an `integration`-marked credentialed recording test that SKIPS honestly when keys are absent.

### Frontend (if applicable)
- None. Backend + fixture only (`Frontend Present: no`). J-05 later renders the drill-in tape timeline in the browser; J-03 delivers and verifies it by API/test reproduction, exactly as backend-only J-01 (iter-1) and J-02 (iter-2) were verified.

### New user-facing capability
Via the API/MCP (surfaced in the browser by the later J-05 iteration): opening a recorded event's drill-in (`GET /research/setups/{id}`) returns the five-state tape timeline at the touch (`ask_absorption` into a rejection, `buyer_control` through a break, …) instead of an empty list — the tape evidence at the wall.

### New information displayed
The recorded event's five-state `tape_timeline` (states + transition times around the touch) on the setups drill-in; recorded event-window datasets listed via the existing `GET /research/datasets` (append-only, checksummed, feed-stamped, split-frozen). No new numeric metric is introduced.

### New user actions
None in the browser this iteration. The recording driver is an explicit, logged operator/integration action (credentialed full run) — not a UI control and not an ambient process.

### UI surface changes
None. The `/structure` case browser and the drill-in tape-timeline rendering are J-05's scope.

### Product surface delta
The case-study registry gains its tape evidence: a recorded event's drill-in now carries the frozen engine's five-state timeline at the touch, joined from the recorded window. Everything else is unchanged.

### Blueprint conformance
No new surfaces. J-03's canonical home per `blueprint.md` is "shown inside the Case Studies drill-in (tape timeline)" under **Structure** — realized here at the API/data layer, rendered by J-05.

### Data-contract additions
**None** — J-03 *realizes* two already-registered Data-Contract rows rather than adding an unregistered value: (1) "Recorded tick datasets (append-only, checksummed, feed-stamped, split-frozen)" owned by the existing `DatasetStore`, served by `GET /research/datasets` + `/{id}`; and (2) the drill-in `tape_timeline` on the "Touch events … case registry" row owned by `setups.py`, served by `GET /research/setups/{id}`, with tape **states** owned by the frozen `TapeEngine` replay. The blueprint's `setups` row Notes cell is refined (additive clarification only) to register precisely that the recorded event's `tape_timeline` = the frozen `TapeEngine` replayed over that event's recorded `DatasetStore` window (setups.py joins verbatim, never reimplements the state machine). No new endpoint and **no new MCP proxy** are introduced (the `datasets` and `setups` GETs already exist; capability #9's new proxies were tradability/setups/edge_report).

## OUT OF SCOPE

- **J-04** (register `structure_tape_map`, the 3-way edge report, `edge_report.py`, `GET /research/edge-report`) — the next iteration. When it lands, it MUST **extend** the existing era-3 `edge_report.py` additively, never fork a second edge computation (carried watch-item), and must never pool across feeds (`iex`/`sip`/yahoo).
- **J-05** (`/structure` declutter: map-default view, Case Studies browser, Edge Report section, browser rendering of the drill-in tape timeline) — later; front-running its UI now would require re-work once J-04 lands.
- **J-06** (cockpit band overlay + confluence chip) — later; credential-gated for its AAPL replay.
- **Audit B1 boundary fix** — the 13/801 most-recent-session events that carry a definitive `rejected`/`broke`/`chopped` label beside `None` forward returns (reaction horizon capped past the store end) are a **J-05-iteration** contract fix (the evaluator scoped B1 to J-05, "not J-03/J-02"). Do not resolve it here; do NOT regress it either while touching the drill-in.
- **Any change to frozen internals** — the `TapeEngine`, `record_from_source`/`DatasetStore` internals, the Alpaca adapter, `levels.py`, `tradability.py`, `backtests.py`, and the `BarStore` are REUSED byte-identically, never modified.
- **Simulating the credentialed recording** — when Alpaca keys are absent, the ≥10-window headline honestly reports blocked; it is never fabricated or fixture-substituted to manufacture a pass.
- **Scan-latency caching (audit B2)** — the ~4m43s full-panel scan is a J-04/J-05 hot-path optimization; the recording driver may reuse a persisted scan if trivially available, but building the cache is not this iteration's scope.

## DEFINITION OF DONE

- [ ] The recording driver selects the top-ranked scan events from `GET /research/setups` and records each event window (config-owned padding, touch −60 min … +90 min) via the existing `record_from_source`, registering each as a `DatasetStore` dataset — exercised keyless in CI against the committed reference/fixture source.
- [ ] A keyless test asserts each registered dataset is append-only, checksum-verified, `feed`-stamped verbatim from the adapter tier, and split-frozen at registration.
- [ ] A keyless test asserts the committed fixture event's `GET /research/setups/{id}` drill-in returns a **non-empty** five-state timeline (states + transition times around the touch) produced by replaying the recorded window through the frozen `TapeEngine`; a non-recorded event's `tape_timeline` stays honestly empty.
- [ ] ONE new small committed tick-fixture slice exists under `apps/backend/tests/fixtures/`, honestly `feed`-stamped, and the join path passes keyless in CI.
- [ ] `config_fingerprint` re-computes to `4d665603569b9dbf`; the frozen `TapeEngine`, `record_from_source`/`DatasetStore`, and the Alpaca adapter are absent from the product diff (reused, byte-identical); the new recording constants are in the fingerprint exclusion set.
- [ ] A grep-based test asserts **no credential literal** appears in any source file, fixture, log, test artifact, or report.
- [ ] Required-still-passing J-01, J-02, J-07 remain green (frozen-foundation byte-identity + fingerprint re-verified; the `GET /research/setups` + `/{id}` contract still serves J-02's registry verbatim).
- [ ] Full backend suite passes keyless; no regressions.
- [ ] **Credentialed headline (operator-gated):** under the `integration` marker with `ALPACA_API_KEY`/`ALPACA_API_SECRET` set, ≥10 event-window datasets across ≥5 symbols (incl. the pinned AAPL 2026-06-22 ~300 test) are recorded and the pinned event's drill-in shows the five-state timeline at the 300-test. **With keys absent (current state), this step is skipped and honestly recorded as `blocked` — never simulated.** (This is the portion that keeps J-03 short of full `passing` until the operator supplies credentials.)
- [ ] Dev handoff written at `docs/handoffs/goal-tradable_wall-iter-3-dev.md`, explicitly stating whether the credentialed recording ran or was blocked (keys absent).

## TESTING REQUIREMENTS

- **Browser:** N/A — `Frontend Present: no`; J-03 is backend + fixture only. No `/structure` UI ships this iteration (that is J-05). Verification is by backend tests + `GET /research/setups/{id}` API reproduction, the same way backend-only J-01/J-02 were verified.
- **Unit/integration (keyless, hermetic — the default suite):**
  - Join path: recorded fixture window → frozen `TapeEngine` replay → non-empty five-state `tape_timeline` on the drill-in, asserting exact states/transition ordering around the touch (not merely "non-empty").
  - `DatasetStore` immutable-data discipline: append-only, checksum verified, `feed` stamped verbatim, split frozen at registration; re-registration/mutation refused.
  - Single-source-of-truth guard: a static/behavioral test that `setups.py` calls the frozen `TapeEngine` for the timeline and never reimplements a tape state (mirrors iter-2's "never a second map engine" guard).
  - Frozen-foundation byte-identity: `TapeEngine`, recorder/`DatasetStore`, Alpaca adapter absent from the diff; `config_fingerprint` == `4d665603569b9dbf`; the era-5B constants sit in the exclusion set.
  - No-credential-in-artifacts grep test over source, fixtures, logs, and reports.
- **Integration (marked `@pytest.mark.integration`, `TAPEOLOGY_LIVE_INTEGRATION=1` + Alpaca keys):** the ≥10-window/≥5-symbol credentialed recording incl. pinned AAPL 06-22; **skips honestly (recorded as blocked) when keys are absent** — never fabricated (per `.claude/core.md` External Integration Testing: the mocked suite alone is not sufficient evidence; the blocked state is documented in the handoff, not silently passed over).
- **Error cases:** empty window (no events → nothing recorded, explicit error — existing `EmptyWindowError`); missing credentials on the historical source → the neutral adapter seam's explicit error surfaces (honestly blocked, never fixture-substituted); unknown `setup_id` → 404 (no fabricated event); malformed padding/selection config → rejected at load.

## NOTES

- **Credential reality (decision record):** `ALPACA_API_KEY` / `ALPACA_API_SECRET` / `TAPEOLOGY_LIVE_INTEGRATION` are all unset here (verified by presence check, values never read). J-03 therefore ships as its **keyless substrate**; the credentialed headline is honestly blocked. This is NOT re-planning human-blocked work (rubric rule 6): it is the FIRST build of J-03, its keyless portion is substantial and unblocks J-04/J-05, and the credentialed act is the operator-gated step the goal explicitly designed for. The evaluator should expect J-03 to move toward `partial` (keyless join path + fixture + tests delivered; credentialed recording blocked), not full `passing`, until the operator supplies keys (in this env or a later `integration`-marker run). No assumption-ledger entry: this is a routine, goal-sanctioned scoping/sequencing pick (the goal's own test discipline mandates the keyless committed fixture + credentialed full run), not a novel interpretation of ambiguous goal text.
- **Lesson (iter-2, applies here — touches `setups.py`):** `setups.py` caps its reaction classification at the last stored bar, so 13/801 most-recent-session events carry a definitive reaction label beside `None` forward returns. That boundary fix is **J-05's** scope, not this iteration's — but since J-03 edits the `/research/setups/{id}` drill-in, do **not** regress this behaviour and keep the tape-timeline join orthogonal to the reaction-horizon logic.
- **Lesson (iter-1, morning-markup as-of):** recording windows are captured around EXISTING scan events (which already carry their prior-session-close morning maps from J-02); the tape join replays completed historical ticks through the frozen engine — no forming-bar/lookahead data enters a window, a dataset, or the timeline. Preserve the no-lookahead rail; the recorder reads only events fully completed at the window's end.
- **Watch-items handed forward (not this iteration):** (1) J-04 must EXTEND `edge_report.py` additively, never fork; (2) J-04/J-05 hit the ~4m43s full-panel scan (audit B2) — plan the persisted/cached scan result there; (3) the J-05 iteration owns the audit-B1 boundary-label contract fix before it renders setups events.
- **Feed honesty:** the committed fixture and any credentialed recording are `feed`-stamped verbatim (`iex` on free keys — thinner than SIP, labeled as such); no pooling happens in J-03 (single feed per dataset), but the no-pooling rail becomes actively load-bearing at J-04's edge report — carried.
- References: iter-2 eval `runs/goal-session-tradable_wall/iter-2/eval.md` (Next-Step Recommendation + watch-items); iter-2 coherence `runs/goal-session-tradable_wall/iter-2/coherence.md` (COHERENCE-PASS, no consolidation owed).
