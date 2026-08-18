# Tapeology — Project Goal (The Rapid Microscope — many candidates in, few survivors out, every kill on the record)

> Eras 1–6 are the **foundation** of this goal. Eras 1–2 are archived at
> [`docs/goal-archive/goal-2026-07-03.md`](goal-archive/goal-2026-07-03.md); the structure-UI
> interlude at [`docs/goal-archive/goal-2026-07-07.md`](goal-archive/goal-2026-07-07.md);
> **Era 5 "The Library"** at [`docs/goal-archive/goal-2026-07-14.md`](goal-archive/goal-2026-07-14.md);
> the **"Fast Wall" interlude** at [`docs/goal-archive/goal-2026-07-17.md`](goal-archive/goal-2026-07-17.md);
> the **"Clean Slate" demolition** at [`docs/goal-archive/goal-2026-07-25.md`](goal-archive/goal-2026-07-25.md);
> **Era B "The Desk"** at [`docs/goal-archive/goal-2026-08-10.md`](goal-archive/goal-2026-08-10.md);
> **Era B2 "The Playbook"** at [`docs/goal-archive/goal-2026-08-14.md`](goal-archive/goal-2026-08-14.md);
> and **Era 6 "The Referee" (GOAL_ACHIEVED 2026-08-16, session `referee`, J-01–J-12)** at
> [`docs/goal-archive/goal-2026-08-16.md`](goal-archive/goal-2026-08-16.md). Eras 3, 4, 5B, and
> 5C are frozen foundation; their records live in git history and `reports/`.
>
> **This chapter is "The Rapid Microscope" — an operator-directed era
> ([`docs/research-directions.md`](research-directions.md) §5.6, the Era-B/B2 operator-pivot
> precedent) that brings the catalog's Era-9 Wave 1 and Card 5.2 forward and adds the
> rapid-validation machinery the catalog never had.** The product today is exactly
> **Cockpit (`/`) + Structure (`/structure`) + Desk (`/desk`)**, the fingerprint epoch is
> `08e471b10130e1e2`, the MCP surface is **22 read-only tools**, and the honesty machinery
> (stores, gates, registry, Referee, PnL promotion interlock) is fully intact. The Referee is
> deliberately conservative — a registered hypothesis waits ~50–120 calendar days for genuinely
> new sessions, and that is right for FINAL claims. What is missing is the FRONT of the funnel:
> a way to try many intraday microstructure candidate mechanisms and kill most of them quickly
> on historical evidence, so only genuinely promising, provenance-complete candidates ever
> consume real future calendar time. This era builds that funnel:
> **many candidates → cheap Scout falsification → chronological pseudo-forward survival →
> sealed-vault OOS → the untouched Referee.**
>
> **Two hard rails govern everything:** (1) every constant, contract, fold rule, sealing rule,
> ledger schema, graduation gate, and trap test is fixed in advance in
> [`docs/rapid-validation-spec.md`](rapid-validation-spec.md) (the canonical spec; developers
> implement from it, never re-derive or re-tune — a change is a named revision that re-keys
> future results, never a sweep); (2) every research output carries its **evidence class**
> (`historical_exposed_diagnostic` / `historical_oos` / `live_confirmatory`) and classes never
> mix — nothing in this era emits `live_confirmatory`, which remains the untouched Referee's
> exclusive territory. The Playbook detector family, the band-context revision, the engine, and
> every `referee_*` module are FROZEN research vocabulary for this whole era (genuine bug fixes
> excepted, each its own named revision). **The era succeeds if it kills bad ideas honestly; it
> does NOT need to discover an edge.**

## Vision

Era B2 taught the desk to detect the book's chart patterns; the band-context interlude placed
them against the wall map; Era 6 built the judge. But the judge's docket is starved: candidate
mechanisms arrive one hand-written hypothesis at a time, wait months, and (honestly) mostly die.
Meanwhile the project's refined objective — short-horizon, low-capacity intraday microstructure
effects suitable for small capital — lives at a layer the product has never measured: what order
flow DOES inside the structural states the desk already detects. This era builds the Rapid
Microscope in five pillars:

1. **The honest corpus truth.** A readiness surface that states, from disk, what the tick corpus
   actually is (today: 12 symbol-days ≈ 3 full-session equivalents, every one of them exposed
   discovery data; splits hand-assigned; aggressor labels 29–76% tick-test fallbacks) and which
   predeclared study floors are met — so no downstream claim can pretend to power that does not
   exist.
2. **One observer, one pass, honest features.** A research micro-observer on the engine's
   sanctioned observer seam reads the SAME canonical replay stream (never a second replay, never
   a recomputed side), and persists prefix-disciplined feature snapshots: flow (cumulative
   delta, event-time imbalance, runs, bursts), price-response (impact efficiency and its trend,
   failed aggression, response asymmetry), and L1 liquidity (spread change, quote imbalance,
   microprice, depletion, `refill_consistent` replenishment) — each with per-row `side_source`
   and per-window fallback/unknown fractions, because an inferred aggressor label is never
   ground truth.
3. **Structure × Flow × Price Response.** The frozen structural vocabulary (playbook signals,
   band-map walls) joined read-side and lookahead-clean to event-level flow — so the research
   question becomes "what does flow do inside this structural state, and does the interaction
   predict the response?", not "chart pattern → buy/sell" and not "flow feature alone →
   buy/sell".
4. **Validation that replays the research process.** A Scout that screens cheaply against
   dependence-honest nulls and ledgers EVERY trial (the denominator never disappears); a
   chronological walk-forward engine with origin-fenced discovery, exact purge, derived embargo,
   frozen fold geometry, and a temporal-stability view that makes decay visible; a Validation
   Vault whose shards seal at ingest under an opaque committed-secret assignment and expose
   exactly once per family; and a recorder (Card 5.2, at last) that grows the tick corpus with
   pre-registered universes instead of cherry-picked days.
5. **Graduation into the untouched Referee.** Stage vocabulary `exploratory →
   walkforward_survivor → sealed_survivor → referee_handoff_ready`, where only
   `historical_oos`-class evidence advances anything, and the export bundle carries the complete
   exposure history — every trial, every kill, every fold, every shard, every failure — so the
   Referee (byte-untouched this era) receives candidates with nothing laundered.

The deliverable: Tapeology moves from "one hypothesis, months of waiting" to a funnel that can
try many microstructure mechanisms against history, kill most of them in days with auditable
reasons, and hand the survivors to the Referee with their full paper trail. Zero survivors is a
passing grade.

## Target Users

- The project owner (a discretionary intraday trader) who reads the readiness truth, registers
  recording universes, runs the recorder/Scout/fold computes as explicit acts, and reads the
  candidate ledger, decay views, and vault states on `/desk` — knowing every number's evidence
  class and every denominator.
- The same owner through **Claude + MCP**: four new read-only tools beside the existing 22 make
  the readiness, ledger, folds, and vault readable from a conversation.
- AI dev-chain agents (the goal-mode chain) building and browser-verifying the era.

## Foundation invariants (still law — eras 1–6, B, B2, and R-1…R-4)

The era-1–2 constitution ([`docs/goal-archive/goal-2026-07-03.md`](goal-archive/goal-2026-07-03.md))
remains binding on all KEPT code — price-impact-over-aggression; honest uncertainty; **no
fabricated data**; single source of truth; no magic numbers; provider-agnostic engine;
deterministic & reproducible; no secrets in source; research read-only over the engine; record
integrity; source/feed/`config_fingerprint` honesty. Ratifications R-1…R-4 carry forward
unchanged (full text in the archived B2 and Referee goals). The surface inventory is the
post-Referee one: `/`, `/structure`, and `/desk` (this era adds sections to `/desk`, no new
route).

1. The **tape engine** (`app/engine/`) emits byte-identical output under `default` on identical
   inputs; `config_fingerprint` stays **`08e471b10130e1e2`** for this WHOLE era — **zero new
   `Config` fields** (every rapid-microscope constant is a module constant embedded in
   `micro_parameters()` and hashed into result identities); if one is genuinely unavoidable it
   takes §0.4 Path A, and a pin movement is a defect, full stop. The observer attachment is the
   engine's EXISTING `add_observer` seam — proven byte-equivalent by
   `tests/test_observer_equivalence.py`, which stays green unmodified.
2. The **frozen research vocabulary** now includes the whole Referee: the nine Playbook
   detectors and all spec constants, `playbook-band-context-v3`, `playbook-cohort-v1`,
   `levels.py`/`tradability.py`/`setups.py`/`edge_report*.py`/`backtests.py`/`profiles.py`/the
   strategy registry/the champion pointer, **and every `referee_*` module, the referee spec, and
   the `pnl_scan` promotion interlock — all behaviorally byte-identical.** This era READS them;
   it never touches, re-implements, re-tunes, or feeds back into any of them. There is NO
   deliberate exception this era.
3. The **stores** — every EXISTING registered `BarStore`/`DatasetStore` artifact stays
   byte-identical with its checksum verifying; no legacy file is ever rewritten or
   reserialized; append-only immutability, frozen splits, parsing compatibility (absent
   fields parse exactly as before), the accelerator DBs, the desk stores, the playbook store,
   and the referee store family are untouched in discipline. **The one r2-sanctioned additive
   seam:** NEWLY recorded datasets MAY carry the backward-compatible OPTIONAL event/manifest
   fields of [`docs/rapid-validation-spec.md`](rapid-validation-spec.md) §7.1/§2.6
   (conditions/venue preservation, `schema_basis`, `quote_size_unit`) — the frozen engine
   ignores them entirely, and immutability is not weakened anywhere. The era ADDS the micro
   store family (snapshots, scout ledger, fold ledger, vault + exposure ledger, recorder
   runs, graduation ledger) under the same discipline, plus one additive default-`None`
   `observer=` kwarg on `DatasetStore.replay` (counter-tested byte-identical when absent).
4. The **PnL promotion ledger** stays append-only and intact; the champion pointer does not move
   this era; `authorize_promotion` keeps its fail-closed contract untouched.
5. The **kept surfaces as shipped**: the cockpit, `/structure`, and every shipped `/desk`
   section (Playbook, band context, cohorts, Referee Registry/Adjudications/Runs) keep working
   exactly as shipped. Rapid-Microscope sections land as NEW sections below the shipped ones;
   no shipped section, column, or behavior changes.
6. The **read-only MCP server** keeps its byte-identical GET-proxy contract; this era adds four
   GET-proxy tools (**22 → 26**, contract v6) and never adds writes.

## Success Criteria

In priority order — and under scope pressure the order is law: **the scientific core (observer,
recorder/vault, Scout, walk-forward, provenance, leakage traps) is never weakened to save the
product surface; UI/MCP polish and up to two of the three pilot studies are the deferrable
items, in that order.**

1. **Nothing kept regresses.** Full backend suite green (2,691 pass / 8 skip at authoring —
   iteration 0 records the era-open count; grows, never shrinks); engine equivalence and the
   golden feature trace pass byte-unmodified; `Config().config_fingerprint()` prints
   `08e471b10130e1e2` every iteration; every `referee_*` module byte-identical to `main` at
   era open (SHA-256 listing recorded at iteration 0 and re-checked); every kept `/`,
   `/structure`, `/desk` behavior browser-verified as shipped.
2. **No leakage trap fails, ever.** The TR-1…TR-22 suite of
   [`docs/rapid-validation-spec.md`](rapid-validation-spec.md) §9 is implemented and green:
   prefix discipline, origin fencing, sealed-shard sweeps, cherry-pick refusal, class-mixing
   refusal, purge exactness, screening calibration, pool invariance, ledger chain integrity,
   single-shot sealed exposure, geometry freeze, rule identity, tick-corpus refusal, the
   synthetic known-null / known-effect end-to-end oracles — and the r2 traps: TR-17
   future-event availability, TR-18 units gate, TR-19 Card-5.1 preservation prerequisite,
   TR-20 root-family lineage, TR-21 process-label discipline, TR-22 exposure registry.
3. **Every trial is on the record.** The scout ledger is hash-chained append-only; every
   evaluated variant — every kill, with its closed-vocabulary reason — is a permanent row; the
   union-N denominator is served beside every family; "statistically above null" and
   "economically large enough to pursue" are separate served columns, the latter always with
   the cost-proxy sentence.
4. **Evidence classes never mix.** Every study/fold/screen payload carries
   `historical_exposed_diagnostic` / `historical_oos` verbatim; diagnostic-class results award
   zero graduation credit and satisfy zero gates (counter-tested); nothing this era emits
   `live_confirmatory`.
5. **The recorder and the vault are real.** The Card-5.2 recorder proves
   restart/resume/idempotency/failure behavior against real Alpaca historical trades+quotes;
   the starter tranche exists on disk meeting every §7.6 diversity minimum; genuine sealed
   shards exist (sealed at ingest, before any exploratory read, under the HMAC committed-secret
   assignment); the 12 legacy symbol-days are served as permanently exploratory; the
   ~150-symbol-day research gate is reported honestly unmet.
6. **The diagnostic walk-forward run is delivered — and worth zero credit.** The 155-session
   playbook-corpus run completes under the predeclared geometry (40/5/20/20 → 5 folds), its
   every output labeled `historical_exposed_diagnostic`, its fold ledger and temporal-stability
   view rendered, and its results feeding no gate, no certificate, no promotion, no graduation.
7. **The pilot studies run honestly.** The three predeclared studies (range-wall failed
   aggression; delta divergence at level tests; capitulation exhaustion) execute through the
   Scout on the joinable corpus with predeclared mechanism/outcome/comparator, every variant
   ledgered; `no survivor`, `wrong direction`, and `insufficient_n` are all passing outcomes.
8. **Graduation is provenance-complete.** The stage vocabulary and export bundle are
   implemented and proven on fixtures end to end; `referee_handoff_ready` explicitly does not
   claim current-Referee registrability for flow predicates (a future named referee-spec
   revision owns that); the Era-15 evidence line (what would justify the Depth purchase) is
   recorded in the roadmap.

## Key Capabilities

1. **The readiness truth (`micro_readiness.py`).** Served-from-disk corpus inventory: per-shard
   symbol/date/feed/window/counts/coverage/`fallback_frac`/checksum/exposure state; honest
   distinct-symbol-day and RTH-minute totals beside the referee's file-count gate; per-study
   predeclared floors met/unmet; the legacy-corpus exposure statement.
2. **The micro observer + snapshots (`micro_observer.py`, `micro_snapshots.py`).** The additive
   `observer=` seam; prefix-disciplined streaming feature extraction in the ONE replay pass;
   snapshot identity `(dataset_id, dataset_checksum, MICRO_ALGO_VERSION,
   SNAPSHOT_FORMAT_VERSION, feature_source_hash, config_fingerprint, params_hash)` with
   load-time verification; the granularity benchmark that CHOOSES the representation before it
   is frozen.
3. **Wave-1 primitives (`micro_features.py`).** F-FLOW / F-RESPONSE / F-LIQUIDITY per spec §3,
   each with a hand-derived oracle fixture; engine values reused from the snapshot, never
   recomputed; `refill_consistent` as the strongest permitted liquidity label; the closed
   outcome set of spec §4 (mid-basis, session-truncated, spread-proxy column beside).
4. **The structure × flow join (`micro_join.py`).** Frozen playbook signals and band-map wall
   touches joined to snapshot rows at their trigger instants, as-of-clean (features from events
   at or before the trigger only; band basis stays the prior-session discipline); zero diff to
   any detector or context module.
5. **The Scout + exploratory candidate ledger (`scout.py`, `scout_ledger.py`).** Frozen
   candidate specs from bounded pre-registered grids; hash-chained append-only trials with the
   union-N denominator; block-permutation screening (session-clustered, dependence-honest);
   concentration/ToD/fallback-tercile disclosures; the pre-registered economic-relevance floor
   served as its own column with the proxy sentence; the closed kill vocabulary.
6. **The chronological walk-forward engine (`walkforward.py`, `micro_accessor.py`).** The
   origin-fenced accessor as the only data door; Mode A rolling-origin discovery where the
   frozen identity is the fitting RULE (realized fitted values are fold provenance); Mode B
   fixed-hypothesis evaluation; exact purge by session-truncation, per-spec derived embargo
   (E=0 legitimate when no dependency crosses); frozen fold geometry with voiding semantics;
   fail-closed floors; the per-sequence temporal-stability/decay view; evidence-class labeling
   throughout; the 155-session diagnostic acceptance run.
7. **The recorder + Validation Vault (`tick_recorder.py`, `vault.py`).** The Card-5.2 chunked,
   throttled, resumable, operator-gated recorder through the unchanged `DatasetStore.record`;
   pre-registered recording universes with cherry-pick refusal; the published sha256 split
   beside the NEW opaque HMAC seal assignment (committed secret outside the repo); one-way
   `sealed → assigned → exposed` with a hash-chained exposure ledger, sealed-metadata
   minimization, and single-shot family-level exposure; the starter tranche under the §7.6
   minimums; paired bar backfill so band context joins.
8. **Graduation (`micro_graduation.py`).** `exploratory → walkforward_survivor →
   sealed_survivor → referee_handoff_ready` with class-2-only advancement, permanent failed
   verdicts, and the provenance-complete export bundle.
9. **The `/desk` Rapid-Microscope sections + MCP contract v6 (26 tools).** Microscope
   Readiness, Scout Ledger, Walk-Forward, and Validation Vault sections rendered BELOW the
   shipped Referee sections; `desk_micro_readiness` + `desk_scout` + `desk_walkforward` +
   `desk_vault` as byte-identical GET proxies; page-load GETs never compute.

## Non-Goals

- **No L2/depth data, no depth purchase, no heatmap.** `BookLevelEvent` stays reserved; Era 15
  remains gated on its own operator act; this era only RECORDS the survivor evidence that would
  inform that decision.
- **No detector, threshold, or context change of any kind.** The nine detectors, the 42+6 spec
  constants, `playbook-band-context-v3`, and the cohort vocabulary are untouched; no recorded
  playbook file is rewritten; microstructure features join READ-SIDE only.
- **No engine change.** No new engine feature, no classifier change, no `FEATURE_NAMES`
  movement; the observer consumes the existing seam; the golden trace and frozen-default
  equivalence pass byte-unmodified.
- **No Referee change.** Every `referee_*` module, the referee spec, and the promotion
  interlock are byte-identical this era; a flow-context referee predicate is explicitly FUTURE
  work (a named referee-spec revision), and `referee_handoff_ready` says so.
- **No sequential-inference rewrite.** Anytime-valid live monitoring / futility stopping is
  recorded as a candidate future era in the roadmap amendment, not built here.
- **No annotation layer** (Era C remains separate). No manual-input write paths into research
  records.
- **No new vendor, no data purchases, no new runtime dependency.** Alpaca (already
  credentialed) and Yahoo (keyless) only; scipy stays out; stdlib + existing numpy idioms.
- **No universe widening beyond the Card-5.2 panel.** The recorder records the frozen panel
  (Tier A/B/C as specified, with the Tier-B re-screen recorded); no survivorship-blind
  "today's constituents" backfill masquerading as history.
- **No trading, no advice, no sizing, no annualized anything** (guard-tested). Every number is
  a statistical statement about recorded history under stated assumptions.
- **No scheduling.** Every recording, snapshot build, screen, fold run, seal, exposure, and
  graduation act is an explicit operator act; page-load GETs never compute.
- **No fingerprint epoch movement.** Zero new Config fields expected; Path A if one is
  unavoidable; the pin `08e471b10130e1e2` does not move.

## Constraints

- **Stack (carried):** Next.js 15 + TypeScript + Tailwind v3, dark-only; Python 3.12 + FastAPI;
  backend `:8000`, frontend `:3000` (browser-QA rig `:8301`/`:3301` via the store-scope rig);
  no new runtime dependency.
- **The spec is canonical.** [`docs/rapid-validation-spec.md`](rapid-validation-spec.md) fixes
  every constant, contract, fold rule, sealing rule, ledger schema, graduation gate, and trap
  BEFORE the code that uses it. Ambiguous or unimplementable ⇒ DROP the procedure from the
  iteration, record the drop, surface for an owner ruling — never improvise. A spec change is a
  named revision that re-keys future results beside old ones.
- **Parameters discipline (the desk pattern at birth):** `micro_parameters()` reads every
  constant at call time; every persisted record embeds the relevant parameters verbatim and
  keys on their hash; a monkeypatched constant must move the parameters AND the result identity
  (counter-tested). Seed streams follow the spec §0 recipe — never `random.sample` on a global
  RNG, never wall-clock.
- **Store discipline:** frozen, checksummed, append-only records; record id = pure function of
  the key; duplicate key raises; corrupt files surfaced, never overwritten; NO
  update/delete/supersede path (source-scan guard-tested); storage dirs are
  env-var-or-sibling defaults (`TAPEOLOGY_MICRO_*` family — deliberately NOT Config fields);
  the vault secret lives OUTSIDE the repo at `TAPEOLOGY_VAULT_SECRET_FILE`, never committed,
  logged, served, or printed — only its sha256 commitment is recorded.
- **The accessor is the only door:** `micro_accessor.py` is the sole legal reader of snapshot
  and vault event data (import-ban guard, the referee-guards precedent); origin fences and
  sealed-shard refusals are typed errors, never empty results; every registered route is swept
  against a sealed fixture shard.
- **Evidence-class law:** every served research payload carries its class verbatim;
  class-mixing in a pooled statistic is a refusal; diagnostic-class evidence advances no
  gate — all counter-tested.
- **Guard tests are extended, never edited:** `tests/test_mcp_server.py` `EXPECTED_TOOLS` grows
  to the 26-tuple; `tests/test_desk_ui_guards.py` `_PRICE_ARITHMETIC_FIELDS` gains every served
  micro numeric (+ seeded counter-tests); `test_meta_routes.py` (3 routes) passes
  byte-unmodified; `test_no_execution_path.py`, `test_copy_discipline.py` (extended for micro
  copy), the referee guards, the context byte-freeze, the fingerprint pins, and the golden
  traces pass unweakened; new micro modules add their own guards (accessor import-ban,
  threshold-sweep ban extended to `micro_*`/`scout*`/`walkforward*`).
- **Hermetic tests:** keyless on committed fixtures (synthetic corpora with known truth; the
  spec's oracle vectors; fixture shards); no test fetches the network; real recordings and
  tranche acts are operator-run, reported run-or-not-run, never CI gates; heavy suites respect
  the pinned time budgets.
- **Browser evidence:** `rm -rf apps/frontend/.next` + rebuild before any browser pass (T-9);
  every browser acceptance needs a screenshot — none ⇒ `unknown`, never `passing` (T-10);
  element-capture for below-the-fold sections (the era-6 lesson); new sections render BELOW
  shipped ones, reuse no shipped `data-testid` or heading string, and are statically swept
  against the stored replay scripts (T-11).
- **Compute-manager reuse:** snapshot builds, screens, fold runs, and recordings follow the
  shipped desk manager pattern (single-flight, snapshot-pollable progress, cancel,
  CLI-runnable, one shared writer, terminal-state-only ledger writes); page-load GETs never
  compute.
- **Scope-pressure priority (operator ruling, binding):** if the era must shrink, defer in this
  order — UI/MCP polish first, then up to two of the three pilot studies — and NEVER weaken
  the observer, recorder/vault, Scout, walk-forward, provenance, or leakage-trap rails.
- **Iteration hygiene (the era-6 retro):** step timeouts tripped in 13 of 15 referee
  iterations — keep per-iteration scope lean, browser acceptance narrow, and the fixture-scoped
  backend the default for QA.

## Design Direction

Unchanged house style: dark-only, dense, professional, terminal-grade. The Rapid Microscope
reads like a lab bench log: corpus truth first, then trials with denominators, then folds with
their classes, then the vault's one-way states. Honest empty/degraded states are first-class
copy (`"No candidates ledgered."`, `"Fold construction refused: 11 sessions < 105 required."`,
`"Sealed — metadata only until exposure."`). Class labels render verbatim; no color implies
advice; every diagnostic-class number carries its label in the same visual unit.

## Product Shape

Nav unchanged: **Cockpit `/` · Structure `/structure` · Desk `/desk`** (`app/meta.py`
`UI_ROUTES` untouched). The era adds four sections to `/desk`, rendered BELOW the shipped
Referee sections: **Microscope Readiness · Scout Ledger · Walk-Forward · Validation Vault**.

**Data Contract — new rows (each value computed once, one owner):**

| Value | Owner (module) | Serving endpoint |
|---|---|---|
| Corpus readiness truth (inventory, floors, exposure states) | new `app/research/micro_readiness.py` | `GET /research/desk/micro/readiness` |
| Feature snapshot metadata + build progress/runs | new `app/research/micro_snapshots.py` (+ manager) | `GET /research/desk/micro/snapshots`, `POST/GET/POST-cancel /research/desk/micro/snapshots/compute`, `GET .../snapshots/runs` |
| Scout trials, kills, denominators, screens | new `app/research/scout_ledger.py` + `scout.py` | `GET /research/desk/micro/scout`, `POST/GET/POST-cancel /research/desk/micro/scout/compute`, `GET .../scout/runs` |
| Fold specs, folds, sequences, decay view | new `app/research/walkforward.py` + its ledger | `GET /research/desk/micro/walkforward`, `POST/GET/POST-cancel /research/desk/micro/walkforward/compute`, `GET .../walkforward/runs` |
| Vault shards, universes, exposure ledger | new `app/research/vault.py` | `GET /research/desk/micro/vault` |
| Recorder job + tranche progress/runs | new `app/research/tick_recorder.py` | `POST/GET/POST-cancel /research/desk/micro/recorder/compute`, `GET .../recorder/runs` |
| Graduation states + export bundles | new `app/research/micro_graduation.py` | `GET /research/desk/micro/graduation` |

**Unchanged owners (this era reads them verbatim):** datasets/replay → `datasets.py` (one
additive kwarg); engine features/side → the engine snapshot; playbook records →
`desk_playbook.py`; band maps → `desk_playbook_context.BandMapResolver` over the recorded
tradability cache; referee registry/adjudications → the `referee_*` family; everything else
exactly as the archived Referee contract lists.

**Canonical values (single source of truth):** a candidate's trial history (scout ledger); a
fold/sequence result and its evidence class (walkforward ledger); a shard's exposure state
(vault ledger); the corpus readiness floors (micro_readiness) — each computed once, served from
its one endpoint, read verbatim by UI/MCP/reports.

## Build anchors & weak-model traps

Anchors verified on `main` at authoring (2026-08-16) — **re-locate by symbol name (grep), never
by line arithmetic**:

- Observer seam: `app/engine/tape_engine.py` — `add_observer` :123, `_notify_event` :144 (fires
  at END of `process_event` :361); equivalence proof `tests/test_observer_equivalence.py`.
- Replay: `app/research/datasets.py` — `DatasetStore.replay` :376 (the ONE entry point; gains
  the additive `observer=` kwarg), `load_events` :370, `_event_to_row` :151 (trade rows carry
  vendor `side` = `unknown`; quote rows carry `bid_size`/`ask_size`), `record_from_source`
  :498, `record` :391 (split validated :408, frozen at registration).
- Aggressor: `app/engine/aggressor.py` — `classify_aggressor` :36 (quote rule :43, tick test
  :52); measured fallback share 29–76% per dataset (readiness must serve it).
- Engine features: `app/engine/features.py` — `FEATURE_NAMES` :24 (frozen), quote sizes dropped
  at `add_quote` :558 (the observer reads them from the raw event instead); golden trace
  `tests/test_dense_replay_gate.py` :256.
- Vendor: `app/providers/adapters/alpaca.py` — `iter_historical_chunks` :309 (the recorder's
  fetch), `_fetch_trades_quotes` :408 (builds `RawTrade(ts, price, size)` at :369/:475 —
  the Card-5.1 preservation fields extend THESE construction sites plus
  `providers/adapters/base.py` `RawTrade`/`RawQuote` :64-81 and `providers/base.py`
  `TradeEvent`/`QuoteEvent`, all optional-default-None); NO tick throttle/recency clamp exists
  (the recorder adds its own throttle); `historical_chunk_seconds = 900` (`config.py:366`).
  Units fact: Alpaca CTA/UTP displayed quote sizes are SHARES from `2025-11-03`, round lots
  before — per-dataset `quote_size_unit` stamping, never a universal assumption (spec §2.6).
- Precedents to copy: `desk_deep_backfill.py` (credentialed chunked CLI job, resumable);
  `desk_playbook_log.py` (hash-chained append-only ledger); the desk compute-manager pattern;
  `referee_null.py` ToD buckets :132.
- Corpus reality at authoring: tick = 18 datasets / 12 symbol-days / 11 sessions
  (2026-05-27→07-13) / ~3.01 session-equivalents / 0.92 GB, all exposed, splits hand-assigned;
  playbook = 156 sessions / 3,222 signals / 101 symbols (2025-06→2026-08); storage ≈ 76–516 MB
  per full symbol-session (mean ~218 MB).
- Guards: `test_mcp_server.py` `EXPECTED_TOOLS` :58 (22 names, ordered); `test_meta_routes.py`
  :33 (3 routes); `test_desk_ui_guards.py` `_PRICE_ARITHMETIC_FIELDS`; `test_copy_discipline.py`;
  `test_real_data_gate.py` (Alpaca confinement — the recorder passes the string `"alpaca"`
  through the seam, never imports the SDK); referee guards `test_referee_guards.py` :53 (context
  byte-freeze) and :180+ (import bans).

Traps (read before EVERY iteration):

- **T-1 · The spec is law, vagueness is a drop.** Implement from
  `docs/rapid-validation-spec.md` verbatim; an unspecified constant or rule is a drop + owner
  ruling, never an invention.
- **T-2 · The vocabulary minefield.** "survivor" alone belongs to `pnl_scan` — this era's
  states are the full tokens `walkforward_survivor` / `sealed_survivor` /
  `referee_handoff_ready`. "evidence" names the playbook fold and "observations" the referee's —
  micro modules say "snapshot rows" and "trials". "studies" was DEMOLISHED in era 5D — the
  `/studies` route must not return. "sealed" is a vault state, never a marketing word.
  `register/record/set/append` stay banned in MCP tool names.
- **T-3 · The prefix law.** No snapshot row may read the future: no end-of-session normalizer,
  no whole-dataset calibration, no backward fill. TR-1 exists to catch exactly this.
- **T-4 · Classes never mix.** A diagnostic fold in an OOS pool, a diagnostic screen feeding a
  gate, a legacy symbol-day inside a sealed claim — each is the era's cardinal sin; the
  refusals are counter-tested, not aspirational.
- **T-5 · The accessor is the only door.** Any direct `open()`/`sqlite3.connect` on snapshot or
  vault data outside `micro_accessor.py` is a guard-test failure, even in a test helper.
- **T-6 · Bounded grids or nothing.** A loop over threshold candidates outside a registered
  grid is the threshold-sweep ban firing; the union-N denominator includes every grid version
  ever run on the corpus.
- **T-7 · Insufficient is an answer.** Floors never loosen; a below-floor fold serves
  `insufficient` with its arithmetic; the tick family's refusal at today's corpus is a
  FEATURE and is pinned by TR-15.
- **T-8 · Fail closed, never at GET time.** Screens, folds, seals, and exposures are operator
  acts through managers; GETs serve recorded state or typed refusals.
- **T-9 · Clean rebuild before browser evidence** (`rm -rf apps/frontend/.next`, rebuild,
  restart).
- **T-10 · Evidence honesty.** No screenshot ⇒ `unknown`, never `passing`; below-the-fold
  sections need element captures; operator acts are reported run-or-not-run.
- **T-11 · Replay-script collisions.** New sections render BELOW shipped ones, reuse no shipped
  `data-testid` or heading string, and are statically swept against the stored scripts.
- **T-12 · Host-guard caps are law** for every heavy path (snapshot builds, screens, folds,
  recordings) exactly as for the desk's own computes.

## Must-have user journeys

Journeys **J-01 – J-10** form the era. **Frontend is present** (J-01 and J-08 are
browser-verifiable; J-09's results render through J-08's sections; the rest are
keyless/automated with browser reveals landing in J-08). Natural dependency order:
J-01 → J-02 → J-03 → J-04 → J-05 → J-06 → J-07 → J-08 → J-09, with J-10 guarding continuously.
J-09 is the era's honest measurement — `no survivor` is a passing state. J-06's tranche is an
operator-attended act inside the era.

- **J-01: The era transition stands — the corpus truth on the record**
  - Steps:
    1. Verify the transition artifacts on `main`: `docs/goal-archive/goal-2026-08-16.md`
       exists and equals the Referee constitution; `docs/rapid-validation-spec.md` exists;
       `docs/research-directions.md` carries the Rapid-Microscope opening note, the Era-9/
       Card-5.2/Era-15 dated amendments, and the appended era-6 status row;
       `project-extensions/proposer-guidance.md` carries the §5.3 amendments.
    2. Run `cd apps/backend && .venv/bin/pytest -q` and record the era-open count; run the
       fingerprint check and the referee-module SHA-256 listing (the iteration-0 baseline).
    3. Build `micro_readiness.py` + `GET /research/desk/micro/readiness` serving, from disk:
       the per-shard inventory (symbol, session date, feed, window, trade/quote counts, bytes,
       coverage gaps, `fallback_frac`, checksum, split provenance `hand_assigned` for the 18
       legacy files, exposure state `exploratory`), the honest totals (distinct symbol-days,
       RTH minutes, session-equivalents) beside the referee tick gate's file count, and the
       per-study predeclared floors met/unmet.
    4. Render the **Microscope Readiness** section on `/desk` (below the Referee sections)
       showing the totals line, the per-shard table, and the floors table; screenshot via the
       store-scoped rig.
  - Acceptance: `GET /research/desk/micro/readiness` serves `distinct_symbol_days: 12`,
    `session_equivalents` ≈ 3.0, every legacy shard tagged `exploratory` with
    `split_provenance: "hand_assigned"`, and a floors table in which every pilot study reads
    `floor_unmet`; the `/desk` Microscope Readiness section renders those same served values
    verbatim (element screenshot), and the iteration-0 baseline records suite count,
    fingerprint `08e471b10130e1e2`, and the referee SHA-256 listing.

- **J-02: The micro observer — one pass, prefix-honest, benchmarked**
  - Steps:
    1. Add the additive `observer=` kwarg to `DatasetStore.replay` (default `None`
       byte-identical, counter-tested) wiring `TapeEngine.add_observer`.
    2. Implement `micro_observer.py`/`micro_snapshots.py` per spec §2: streaming-only rows,
       flush-before-next-event, snapshot identity with `feature_source_hash` +
       `config_fingerprint`, load-time verification.
    3. Implement the Wave-1 primitives of spec §3 (r2 — every degree of freedom is a frozen §1
       constant: refill M, response K, burst baseline, depletion window, the pinned
       impact-flatness formula, the trailing divergence window + δ) in `micro_features.py`
       with the availability triple `anchor_at`/`observed_through`/`available_at` on every
       value (deferred constructs written at `observed_through`, `unavailable` counted),
       per-row `side_source`, per-window `fallback_frac`/`unknown_frac`, the §2.6 size-unit
       gating on cross-basis liquidity features, and the spec §4 mid-only primary outcome set
       (last-trade basis only as the separately named sensitivity column); hand-derived oracle
       fixtures for every family (TR-16 vectors committed).
    4. Run the spec §2.4 granularity benchmark on ≥2 real datasets including NVDA `72ca8bc0`;
       record bytes amplification, build time, and query latency per candidate representation;
       pin the winner as `micro-snapshot-v1`.
    5. Build snapshots for all 18 legacy datasets through the single-flight manager + CLI.
  - Acceptance: the TR-1 prefix and tail-perturbation traps pass (3 cut points, byte-identical
    prefixes); the TR-17 future-event availability trap and the TR-18 units gate pass (an
    `unverified`-unit fixture refuses every cross-basis feature with a typed error); TR-7
    stale-identity traps pass; every feature oracle fixture passes; the benchmark table is in
    the iteration handoff with the pinned representation named; 18/18 legacy snapshots exist —
    every one carrying `quote_size_unit: "unverified"` — and
    `GET /research/desk/micro/snapshots` lists them with verified identities;
    `tests/test_observer_equivalence.py` and the golden feature trace pass byte-unmodified.

- **J-03: Structure × flow — the join that never looks ahead**
  - Steps:
    1. Implement `micro_join.py`: for a playbook signal (symbol, `trigger_ts`) or a band-map
       wall touch, locate the covering snapshot and serve the feature row(s) at-or-before the
       trigger plus the outcome rows after it; band basis through the recorded
       `BandMapResolver` (compute=False) unchanged.
    2. Enumerate the joinable corpus (signals and touches falling inside recorded tick
       windows) and serve the count honestly.
    3. Prove lookahead-cleanliness: a join at trigger T reads zero snapshot rows with
       event epoch > T (asserted), and detector/context modules show zero diff.
  - Acceptance: a committed fixture join reproduces hand-computed feature-at-trigger and
    outcome-after-trigger values; the joinable-corpus count is served on the readiness
    endpoint with its per-study breakdown; the lookahead assertion and the
    detector/context-byte-freeze guards pass.

- **J-04: The Scout and the ledger — every trial on the record**
  - Steps:
    1. Implement `scout_ledger.py` (hash-chained, append-only, closed kill vocabulary,
       union-N denominators) and `scout.py` (spec §5 screening: session-clustered block
       permutation, non-overlapping anchor subsampling, concentration/ToD/fallback-tercile
       disclosures, the economic-floor column with registration-ordering).
    2. Register a bounded fixture grid, run it end to end through the manager + CLI, kill and
       advance per the recorded results.
    3. Implement TR-8 (calibration on the autocorrelated null fixture, 200 seeds, incl. the
       banned-shuffle counter-test), TR-9, TR-10, TR-11.
  - Acceptance: TR-8/9/10/11 pass; the fixture family's ledger shows every variant with its
    decision and reason, `variants_tried` equals the union over grid versions, and the served
    screen carries `evidence_class`, the best-of-N line, and the economic column with the
    proxy sentence verbatim.

- **J-05: The walk-forward engine — chronology, fences, and the diagnostic run**
  - Steps:
    1. Implement `micro_accessor.py` (origin fence, sealed invisibility, sole-door import ban)
       and `walkforward.py` per spec §6: fold specs, exact purge, derived embargo (E=0
       legitimate, derivation recorded), frozen geometry + voiding, frozen session_date
       clustering (no corpus-size switching), Mode A rule-identity freeze/reveal, Mode B,
       constant-rule sequences, floors, the explicit `WF_SURVIVOR_RULE_V1`, the §6.7 exposure
       registry (initialized with every playbook and legacy-tick window pre-marked exposed),
       the §6.8 `rule_process`/`operator_process` labels, the decay view, class labels.
    2. Prove the synthetic end-to-end oracles (TR-16 known-null and planted-effect corpora)
       and TR-3/5/6/13/14/15.
    3. Run the **diagnostic acceptance run**: the 155-session playbook corpus (2025-06 orphan
       excluded, disclosed), geometry 40/5/20/20, a predeclared frozen set of playbook setup
       definitions; produce the fold ledger and per-sequence decay view.
  - Acceptance: TR-3/5/6/13/14/15/16/21/22 pass; the diagnostic run completes with 5 folds /
    100 validation sessions, every served fold and sequence labeled
    `historical_exposed_diagnostic`, the tick-family fold request returns the typed
    floor-refusal naming `11 < 105`, and counter-tests prove diagnostic-class results and
    `operator_process` sequences award zero graduation credit.

- **J-06: The recorder and the Vault — new tape, sealed at birth**
  - Steps:
    1. **The Card-5.1 preservation prerequisite lands FIRST (spec §7.1, r2)**: optional
       `conditions`/`exchange` (and vendor quote-condition/venue equivalents) on
       `RawTrade`/`RawQuote`/`TradeEvent`/`QuoteEvent` and the dataset rows — absent-key
       backward compatible (every legacy dataset and committed fixture loads byte-identically,
       checksums verify), engine-ignored (equivalence + golden trace byte-unmodified) — plus
       the §2.6 `schema_basis` + `quote_size_unit` stamping from the dated vendor rule
       (Alpaca CTA/UTP shares from `2025-11-03`, round lots before). The recorder structurally
       refuses any universe recording until these ship (TR-19).
    2. Implement `tick_recorder.py` (chunked `iter_historical_chunks` fetch, tick throttle,
       per-chunk checkpoints, resume/idempotency, single-flight manager + CLI, per-chunk
       `failed` outcomes) writing through `DatasetStore.record` under the unchanged store
       discipline; pair with the existing deep-backfill CLI for the same symbol-days' bars.
    3. Implement `vault.py`: universe registration (rule hash committed BEFORE any fetch),
       the published sha256 split beside the HMAC seal assignment
       (`TAPEOLOGY_VAULT_SECRET_FILE`, commitment recorded), one-way
       `sealed → assigned → exposed` exposure ledger keyed on the computed `family_root_id`,
       **opaque pre-exposure metadata (spec §7.5 r3: surrogate shard id, salted commitment,
       no symbol/date until assignment, sealed dataset ids refused on the dataset + MCP
       surfaces — aggregates only on readiness)**, TR-2 join-resistance sweep, TR-4
       cherry-pick refusal, TR-12 single-shot exposure, TR-20 root-lineage refusal.
    4. Operator act, inside the era: resolve Tier-B by the spec §7.2 mandatory order (screen
       by the frozen Card-5.2 criteria → record criteria hash, as-of, provenance, full output,
       resolved list → freeze the list → `symbol_rule` → register the universe → commitment +
       HMAC → only then fetch; no re-screen or substitution afterward — vendor failures are
       disclosed, never swapped), then run the recorder against real Alpaca historical
       trades+quotes to the spec §7.6 minimums (≥30 symbol-days, ≥8 panel symbols incl. PG +
       ≥3 Tier-B + ≥1 ETF, ≥10 dates over ≥6 weeks, the concentration caps, ≥60%
       full-session), with a restart mid-run proving resume.
    5. Refresh readiness: the new shards appear with completeness reporting (including
       `quote_size_unit` and preservation-field presence); sealed members show opaque
       aggregates only.
  - Acceptance: TR-2/4/12/19/20 pass; every legacy dataset and committed fixture loads
    byte-identically with checksums verifying and the engine equivalence/golden-trace tests
    byte-unmodified; the tranche exists on disk meeting every §7.6 minimum (readiness serves
    the arithmetic) with every new shard carrying `schema_basis`, preservation fields, and a
    stamped `quote_size_unit`; at least the HMAC-assigned subset of tranche shards is `sealed`
    with zero exploratory reads recorded before sealing and no symbol/date served
    pre-exposure; the recorder run ledger shows the mid-run restart resuming without duplicate
    registration; the legacy 12 symbol-days remain `exploratory`; the readiness gate line
    still reads the ~150-symbol-day research gate as unmet.

- **J-07: Graduation — provenance in, nothing laundered out**
  - Steps:
    1. Implement `micro_graduation.py` per spec §8: the four states, class-2-only
       advancement, single-shot sealed transitions, voiding semantics, and the export bundle
       (spec hash, complete exposure history incl. kills and failures, proposed boundary,
       family/multiplicity metadata).
    2. Prove the pipeline on fixtures: a fixture candidate walks
       `exploratory → walkforward_survivor → sealed_survivor → referee_handoff_ready` on
       synthetic class-2 evidence; a diagnostic-only twin is refused at the first transition;
       a failed-sealed twin carries its permanent verdict in the bundle.
    3. Record the Era-15 evidence line in the roadmap amendment (what L1 liquidity-family
       survivor evidence would raise/lower the Depth purchase prior).
  - Acceptance: the fixture walk produces a validating `referee_handoff_ready` bundle whose
    provenance lists every trial/fold/shard including the failures; the diagnostic-only and
    failed-sealed refusals are counter-tested; the bundle's own copy states that current-
    Referee registration of a flow predicate awaits a named referee-spec revision; every
    `referee_*` module remains byte-identical.

- **J-08: The surface and MCP v6 — the funnel is visible**
  - Steps:
    1. Render the **Scout Ledger**, **Walk-Forward**, and **Validation Vault** sections on
       `/desk` below Microscope Readiness: trials with denominators and kill reasons; fold
       sequences with per-fold rows, class labels, and the decay line; shards with one-way
       states and universe provenance; every compute behind its own operator button with
       progress + cancel (the shipped manager pattern).
    2. Add `desk_micro_readiness`, `desk_scout`, `desk_walkforward`, `desk_vault` as
       byte-identical GET proxies; bump the MCP contract to v6 and update `EXPECTED_TOOLS`
       to the 26-tuple in the same commit.
    3. Clean rebuild, browser pass via the store-scoped rig, element screenshots per section.
  - Acceptance: all four sections render served values verbatim (screenshots on record, one
    per section, element-captured); the four tools return byte-identical bodies to their GET
    routes; the 26-tool contract test and the replay-script static sweep pass; every
    diagnostic-class number on the page carries its label in the same visual unit.

- **J-09: The pilot studies — three predeclared questions, honest answers**
  - Steps:
    1. Predeclare (as ledgered specs, before any outcome read) the three studies in priority
       order: **(1) range-wall failed aggression** — at band-map wall touches, does high
       aggression-into-the-wall with collapsing impact efficiency and opposite-side
       `refill_consistent` replenishment precede rejection more than comparable touches
       without that signature; **(2) delta divergence at level tests** — at consecutive tests
       of the same zone, does price extending while session cumulative delta does not predict
       rejection (Card 9.1's formula verbatim); **(3) capitulation exhaustion** — do
       event-level exhaustion signatures (extreme sell aggression then collapsing negative
       impact efficiency / replenishment) separate capitulation signals that snap back from
       those that do not. Continuous mechanism-defined representations first; any threshold
       variant from the bounded grid, all ledgered.
    2. Run each through the Scout on the full joinable corpus (legacy exploratory symbol-days
       + any EXPOSED tranche shards; sealed shards untouched), with every disclosure of spec
       §5.4 served.
    3. Where any study's fold floors are met on class-2 data, run walk-forward; where not,
       serve the floor-refusal as the study's honest result.
    4. Record each study's outcome in the ledger (survive / kill with reason) and render it
       through the J-08 sections.
  - Acceptance: three ledgered study families exist with predeclared specs whose
    registration timestamps precede their first outcome read; each serves its screen with
    evidence class, denominators, concentration/ToD/fallback disclosures, and the economic
    column; each carries a recorded decision in the closed vocabulary — with `no survivor`,
    wrong-direction, and `insufficient_n` all acceptable end states — and no study output
    feeds any gate, certificate, or promotion.

- **J-10: The kept product stands — traps armed, sentinel green**
  - Steps:
    1. Land the full TR-1…TR-22 suite (whichever traps did not ship inside J-02…J-07 land
       here — the r2 traps TR-17 availability, TR-18 units, TR-19 preservation, TR-20 root
       lineage, TR-21 process labels, TR-22 exposure registry included) plus the extended
       guard tests (accessor import-ban, micro threshold-sweep ban, copy discipline for micro
       copy, `_PRICE_ARITHMETIC_FIELDS` additions).
    2. Run the deterministic-rerun check (byte-identical snapshot/screen/fold outputs on a
       re-run over unchanged stores).
    3. Run the kept-product sentinel: cockpit `/` live-tape and chart, `/structure` load and
       Tradable Map, every shipped `/desk` section including the three Referee sections,
       browser-verified via the store-scoped rig; full backend suite; fingerprint check;
       referee SHA-256 listing re-check against the iteration-0 baseline.
  - Acceptance: the complete trap suite is green; the deterministic rerun is byte-identical;
    the full suite passes at a count ≥ the era-open baseline with 0 regressions; the
    fingerprint prints `08e471b10130e1e2`; the referee listing matches iteration 0 exactly;
    and the sentinel screenshots show every kept surface as shipped.

<!-- AUTO:journeys -->

<!-- /AUTO:journeys -->

## Anti-goals

**Immutable rails — the identity of the project (from
[`docs/research-directions.md`](research-directions.md) §0.3; enforced by existing tests and
audits; only ever grow more specific, never weaker):**

1. **No execution path, ever** — no brokerage/trading API, no order tickets, no live OR paper
   trading, no "just to test" exceptions. (`apps/backend/tests/test_no_execution_path.py` is
   the tier-1 guard; new research code adds matching guard tests, never weakens them.)
   *(critical)*
2. **No profit claims and no advice** — every $ figure is a simulated measurement carrying R,
   n, fee/slippage assumptions, and its train/hold-out/forward basis. No prediction language,
   no imperative trading cues. *(critical)*
3. **Frozen foundations** — the `v1` strategy, the `default` profile, the tape engine's five
   states and thresholds, the frozen structure computations, the JSON `BarStore`, and every
   KEPT surface's behaviour stay byte-identical. New work is additive and versioned beside
   them, never a mutation of them. *(critical)*
4. **Hold-out-only promotion** — the champion pointer moves only on a genuine hold-out
   survival through the sweep gate PLUS a valid Referee certificate. Train-only wins are
   labeled overfit. Never lower a minimum sample size, widen a gate, or pool across
   feeds/fingerprints to manufacture a survivor. *(critical)*
5. **No lookahead** — every value computed as-of T uses only events/bars fully completed at T.
   *(critical)*
6. **Single source of truth** — each shared value is computed once, owned by one canonical
   endpoint, and read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor hard-fails
   violations. *(critical)*
7. **Deterministic and seeded** — every random draw uses a recorded named seed via per-row
   streams; identical requests reproduce byte-identical results; no wall-clock, no unseeded
   randomness in any research artifact. *(critical)*
8. **Read-only MCP** — MCP tools remain byte-identical proxies of GET endpoints; nothing on
   the MCP surface can change state. *(critical)*
9. **Immutable data** — registered datasets and bar series are append-only, checksummed,
   never re-tagged, never deleted, never content-perturbed. Splits are frozen at
   registration. *(critical)*
10. **Persistence stays scoped** — no ambient recording of live streams; recording/fetching
    is an explicit, logged act. *(critical)*

**Era-B/B2 anti-goals that remain binding:** membership is never a signal; snapshots and
playbook records are append-only and pinned; every run is an explicit operator act; the
briefing and the playbook describe, never advise; the demolition stays demolished; the ledger
never holds orders; the suite stays keyless and hermetic; the fingerprint pin does not move;
no threshold exists outside its spec and no code path sweeps one; the evidence pools one
signature; no recorded playbook file is ever rewritten; no second implementation of the
measurement rail. *(all critical)*

**Referee-era anti-goals that remain binding** (the archived Referee goal's full text governs;
headline rails): no confirmatory claim outside the gauntlet; the historical atlas is
exploratory forever; CI-inversion is never a p-value; never shrink the BH denominator; no gate
loosens mid-era; the Referee never feeds back; promotion is certificate-locked with no bypass;
no confirmatory output without a verified oracle attestation; no annualized metrics anywhere.
*(all critical)*

**Rapid-Microscope anti-goals (added, not weakening any rail above):**

- **No exploratory read of a sealed shard.** Event data and outcome aggregates of a `sealed`
  shard are refused everywhere (routes, MCP, accessor, readiness) until its recorded
  exposure; the refusal is typed, tested, and fail-closed. *(critical)*
- **Sealed exposure is family-level and single-shot — never a second draw.** No more than one
  evaluation per (family, shard) exists, ever; a failed sealed verdict is permanent and
  travels in every later export bundle; no perturbed re-submission resets it. *(critical)*
- **Evidence classes never mix.** No `historical_exposed_diagnostic` output feeds a gate, a
  graduation transition, a certificate, a promotion, or a pooled statistic with
  `historical_oos` rows; nothing in this era emits `live_confirmatory`. *(critical)*
- **No fold geometry change after fold 1** without a recorded voiding event that clears every
  survivor state of that corpus-era. *(critical)*
- **No threshold, grid, formula, embargo, or fold parameter is chosen or revised from
  validation, sealed, or holdout outcomes.** Fitting rules are data functionals frozen before
  reveal; per-origin refits under an unchanged rule are provenance, never a new choice.
  *(critical)*
- **The denominator never shrinks.** Every evaluated variant lands in the hash-chained ledger
  with a closed-vocabulary decision; kills are never deleted; the union-N across grid
  versions is served beside every family. *(critical)*
- **The accessor is the only data door.** No module but `micro_accessor.py` opens snapshot or
  vault event data; origin fences fail closed; import-ban and source-scan guards enforce it.
  *(critical)*
- **No microstructure claim beyond what L1 supports.** `refill_consistent` is the strongest
  liquidity label; "iceberg", institutional-intent, and manipulation language are banned;
  every aggressor-derived quantity is served beside its `fallback_frac` and `unknown_frac`.
  *(critical)*
- **No sub-second outcome horizon** and no latency-sensitive mechanism, per DO-NOT #1.
  *(critical)*
- **No cross-unit liquidity arithmetic.** No feature, screen, or study relates trade shares to
  displayed quote sizes unless the dataset's `quote_size_unit` is verified (spec §2.6);
  unverified or mixed units are a typed refusal; unit normalization exists only as a recorded
  verification act, never silent arithmetic. *(critical)*
- **No value is served before it exists.** Every feature carries
  `anchor_at`/`observed_through`/`available_at`; a deferred construct is `unavailable` until
  its observations exist; no outcome for a conditioned anchor begins before the conditioning
  set's maximum `available_at` (TR-17). *(critical)*
- **The 12 pre-existing tick symbol-days are permanently exploratory** — never sealed, never
  `historical_oos`, never relabeled. *(critical)*
- **The ~150-symbol-day research-readiness gate is never lowered or silently satisfied**; any
  claim whose predeclared floor is unmet fails closed with the floor arithmetic served.
  *(critical)*
- **Referee modules are byte-untouched this era** — `referee_handoff_ready` never implies
  current-Referee registrability of a flow predicate; that awaits a future named revision of
  the referee spec. *(critical)*
- **The vault secret never enters the repo, a log, a payload, or a screenshot** — only its
  sha256 commitment is ever recorded. *(critical)*
- **The enhancement loop stays inside its box.** The goal-proposer may append journeys ONLY
  inside the `AUTO:journeys` marker block above — it MUST NOT edit human-authored journeys,
  this Anti-goals section, or any other part of this file; proposed journeys MUST carry a
  single-source-of-truth acceptance criterion, keep the `default` profile and `v1`
  byte-identical, respect every rail above, and include a `[NEW]`-flagged walkthrough.
  Manufacturing a low-value journey just to keep the loop alive is a failure. *(critical)*

**Host protection (carried verbatim — a physical constraint of the host, not product scope):**

- **Host-guard caps are law.** This host (GEEKOM A7 Max mini-PC) hard-reset five times between
  2026-07-20 and 2026-07-28 under unconfined goal-mode load — instant power/VRM transient
  trips with nothing in the journal; resets #3–#5 struck while tapeology's goal mode ran
  UNGUARDED beside trendora's. When `project-extensions/host-guard/host-guard.env` declares
  ceilings (CPU mask `4-7,12-15` — the complement of trendora's — plus BLAS thread caps and
  memory/task bounds), every heavy path respects them: headless engine runs self-wrap under
  the mask, and interactive pump sessions are auto-confined in place by the engine
  (`host-guard-adopt.sh`; `scripts/automation/host-guard-exec.sh claude` is the optional
  from-birth wrapper) — the engine pauses `AWAITING_HOST_GUARD` (resumable) only when
  confinement cannot be established. Never disable, widen, or bypass these caps to make a run
  faster or a pause go away; widening the mask follows the verification ladder in
  `trendora/project-extensions/host-guard/README.md`. *(critical)*
