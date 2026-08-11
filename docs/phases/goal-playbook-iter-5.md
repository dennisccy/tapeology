# Goal Iteration 5 — The climax family: capitulation entry + euphoria marker (J-05)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** playbook
- **Iteration:** 5
- **Mode:** next
- **Depth:** full
- **Full trigger:** 1 — Structural/cross-cutting: the euphoria/capitulation marker-decoration pass
  is a NEW kind of coupling — it reads across ALL FIVE already-shipped signal shapes
  (`open_high_break`/`open_low_break`/`jbe`/`dbi`/`cup_handle`) within the SAME symbol-session to
  decide `euphoria_recent`/`capitulation_recent`, a cross-detector dependency no single existing
  journey's test covers. It touches `desk_playbook_detect.py` (two new detector functions, one of
  them a non-signal marker), `desk_playbook.py` (the compute-walk's decoration pass + `PLAYBOOK_SETUPS`
  + the register/blurb widening that closes iter-4's open anti-goal item), and the frontend
  (`types.ts` + `page.tsx`'s already-wired-but-unproven decoration chips). Independently also
  satisfies trigger 4 (brand-new full-stack journey, never implemented, real backend + frontend
  Data-contract additions).
- **Frontend Present:** yes
- **Target journeys:** J-05
- **Required-still-passing journeys:** J-01, J-02, J-03, J-04, J-10
- **Anti-goal reminders:**
  - **No execution path, ever** — no brokerage/trading API, no order tickets, no live OR paper
    trading, no "just to test" exceptions. (`apps/backend/tests/test_no_execution_path.py` is the
    tier-1 guard; new research code adds matching guard tests, never weakens them.) *(critical)*
  - **No profit claims and no advice** — every $ figure is a simulated measurement carrying R, n,
    fee/slippage assumptions, and its train/hold-out/forward basis. No prediction language, no
    imperative trading cues. *(critical)*
  - **Frozen foundations** — the `v1` strategy, the `default` profile, the tape engine's five
    states and thresholds, the frozen structure computations, the JSON `BarStore`, and every KEPT
    surface's behaviour stay byte-identical. New work is additive and versioned beside them, never
    a mutation of them. *(critical)*
  - **No lookahead** — every value computed as-of T uses only events/bars fully completed at T.
    *(critical)*
  - **Single source of truth** — each shared value is computed once, owned by one canonical
    endpoint, and read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor hard-fails
    violations. *(critical)*
  - **Deterministic and seeded** — every random draw uses a config-owned recorded seed; identical
    requests reproduce byte-identical results; no wall-clock, no unseeded randomness in any
    research artifact.
  - **Immutable data** — registered datasets and bar series are append-only, checksummed, never
    re-tagged, never deleted, never content-perturbed. Splits are frozen at registration.
    *(critical)*
  - **Era-B desk anti-goals that remain binding:** membership is never a signal; snapshots are
    append-only and pinned; every run is an explicit operator act; the briefing describes, never
    advises; no new statistics, gates, or strategies; the demolition stays demolished; the ledger
    never holds orders; the suite stays keyless and hermetic; the fingerprint pin does not move.
    *(all critical)*
  - **No threshold exists outside the spec, and no code path sweeps one.** Every detector rule and
    threshold exists in [`docs/playbook-detector-spec.md`](../playbook-detector-spec.md) BEFORE the
    code that uses it; no code path iterates thresholds against outcomes (source-scan
    guard-tested); a threshold change is a spec revision + new signature, never an edit of recorded
    signals and never a sweep. *(critical)*
  - **A signal is an observation, not a call.** No signal, chip, or evidence cell uses advice,
    imperative, prediction, probability, expectancy, edge, or significance language; the served
    registers state what was NOT measured (no fills, no costs, returns not stop-adjusted);
    `invalidation_price` is geometry, never an order concept. *(critical)*
  - **No recorded playbook file is ever rewritten, backfilled, pruned, or superseded in v1.** New
    signatures mint new versions beside old ones; a corrupt file is surfaced loudly, never
    overwritten; the store exposes no update or delete method (source-scan guard-tested).
    *(critical)*
  - **No second implementation of the measurement rail.** Measurement helpers are imported from
    `desk_forward.py` with a zero diff to that file; no playbook module re-implements horizons,
    MDD, truncation, or the seed discipline (import-graph guard-tested). *(critical)*

## GOAL

The project owner runs the Playbook on a session and now sees the book's climax family — a
capitulation entry after a vertical decline reverses, plus a euphoria marker that (without ever
appearing as its own row) visibly decorates any nearby signal as "euphoria recent" — beside the
already-shipped opening-range-break, JBE, DBI, and cup-and-handle families in the same `/desk`
Playbook Signals section.

## BACKGROUND

Per the priority rubric: nothing regressed (rule 1 n/a — J-01..J-04 all re-verified passing at
iter-4), the iter-4 coherence audit was `COHERENCE-PASS` with zero blocking violations (rule 2
n/a — no consolidation pass owed), and J-05 is both the iter-4 evaluator's explicit next-step
recommendation and the natural dependency-order pick (`docs/goal.md`: "the detector families
J-04/J-05/J-06 (each lands visibly on the J-03 section)") — it is also the smaller of the two
remaining families (two detectors, one of which is a marker with no measurement, versus J-06's
three: range_trade PROVISIONAL plus double_top/double_bottom), satisfying rule 4. Only one risky
journey is in scope this iteration (rule 5). Depth is `full` per the evaluator's own binding
recommendation, independently justified below (trigger 1).

**Three lessons apply directly and are binding on this iteration's design:**
- *iter-4 lesson (a "must not fire" fixture can pass for the wrong reason)* — the "high-volume
  decline that never reverses" near-miss fixture must ship WITH a gate-relaxed control that proves
  the reversal-bar-within-`PLAYBOOK_BOUNCE_MAX_BARS` gate specifically is what rejects it, not an
  earlier, coincidental gate (e.g. the vertical-move/RVOL-surge gate never being met at all).
- *iter-4 lesson (extending the setup families silently invalidated the product's own summary
  copy)* — this iteration closes that OPEN minor anti-goal violation itself rather than deferring
  it again: `PLAYBOOK_REGISTER` (`desk_playbook.py:159`) and BOTH `/desk` copy spots
  (`page.tsx:4982`'s empty-state sentence, `page.tsx:5079`'s populated-section blurb) are widened to
  name every shipped family, and a NEW pinned-text assertion (the `_EXPECTED_EFFECT_COUNT`
  re-derivation pattern: exact text + a mandatory rationale paragraph) is added so the next family
  (J-06) cannot silently repeat the drift.
- *iter-1 lesson (positional slot indexing fabricates data on gapped sessions)* — the climax
  `leg_low`/re-anchoring logic must read bars by explicit index/comparison, never by an assumed
  contiguous offset from session start.

**One carried item rides inside this same cycle** (iter-4's next-step recommendation, item 2): the
DBI ("Drop-Base Implosion") signal row screenshot in `reports/qa/goal-playbook-iter-4-evidence/`
predates the base-shape label fix ("ascending base" → "descending base") — re-take it in this
iteration's own clean-rebuilt browser pass, alongside J-05's new screenshots.

**Not resolved this iteration (surfaced for the operator, not decided here):** the iter-4
evaluator's two owner-ruling questions — whether spec §3.3's 1.5x jump-to-base gate is reachable
under the current `BASE_MAX_RANGE_MBR`/`JUMP_MIN_MOVE_MBR` pairing, and whether the cup's rim test
should read the spec-named `RIM_MATCH_MBR` constant rather than the code's `near_extreme_mbr` (both
currently 1.0, zero behavior delta) — are genuine judgment calls about already-shipped J-04 code,
not documentation catch-up the decomposer can safely resolve the way the iter-2 B3/B4 precedent did.
They stay in `iteration-state.md`'s "Owner rulings pending" list, unblocked by and unrelated to
J-05's own scope.

## IN SCOPE

### Backend

- [ ] `desk_playbook_detect.py`: implement `detect_capitulation` per spec §3.5 — formation via
  `vertical_move` DOWN (`PLAYBOOK_VERTICAL_MOVE_MBR`·MBR net decline over
  `PLAYBOOK_VERTICAL_WINDOW_BARS` bars, ≥ n−1 down closes, `require_volume=True` with
  `PLAYBOOK_RVOL_SURGE` and the rising-RVOL clause — the primitive's existing, previously-unused
  `require_volume`/`rvols`/`rvol_surge` parameters); `leg_low` = min low through `t−1`, RE-ANCHORING
  the climax bar `v` whenever a new low forms after it (the panic still running); trigger on the
  first bar `t` with `t − v ≤ PLAYBOOK_BOUNCE_MAX_BARS` and `high > high[t−1]` (`T = high[t−1]`, no
  formation expiring silently if no such bar appears in the window); invalidation
  `leg_low − 0.30·(T − leg_low)`; cap 1 per symbol-session (first); disclosures `decline_mbr`,
  `decline_bars`, `climax_rvol`, `bars_from_climax_to_trigger`; principle `["P1"]`. Follows the SAME
  signal-assembly shape as `detect_opening_range_breaks`/`detect_jbe` (entry/entry_kind via the
  shared stop-through-fill convention, `market` via the shared `market_context` primitive,
  `principles`, `disclosures`) so it flows through the existing `_measure_signal` pass unmodified.
- [ ] `desk_playbook_detect.py`: implement `detect_euphoria` as the exact mirror UP of
  `detect_capitulation` (same constants, same cap of 1 per symbol-session), but returning MARKER
  events only — no side, no entry, no invalidation, no geometry, no principles, never measured,
  never appended to `signals`/`signal_pool`/`baseline_pool`, and never given a `setup_id`. Its only
  output is each firing's trigger-bar position, consumed exclusively by the decoration pass below
  and discarded afterward — structurally incapable of becoming a served row.
- [ ] `desk_playbook.py`: wire `detect_capitulation` into the compute walk beside the existing four
  detector calls (adds to `detected_signals`, measured identically); extend `PLAYBOOK_SETUPS` to
  `("open_high_break", "open_low_break", "jbe", "dbi", "cup_handle", "capitulation")` —
  **`"euphoria"` is deliberately never added**, since it is never a recorded setup.
- [ ] `desk_playbook.py`: the marker-decoration pass — within the SAME per-symbol-session walk,
  after `detected_signals` (now including any `capitulation` firing) is assembled and
  `detect_euphoria`'s marker events are collected, set `capitulation_recent`/`euphoria_recent` on
  every signal (of ANY setup, including `capitulation` itself, but never self-decorating a marker
  onto its own firing) whose trigger bar falls STRICTLY AFTER a same-symbol-session marker's trigger
  bar and within `PLAYBOOK_MARKER_DECAY_BARS` bars of it — see NOTES for why the window is
  forward-only (a lookahead-honesty reading, not a free choice). Decoration is same-symbol-session
  only; it never reads another member's bars or signals.
- [ ] `desk_playbook.py`: widen `PLAYBOOK_REGISTER` (`:159`) to name every shipped setup family
  (opening-range breaks, jump-base-explosion, drop-base-implosion, cup-and-handle, capitulation) —
  the register text is NOT part of `playbook_parameters()`, so this does not move
  `playbook_input_signature`.
- [ ] Zero new primitive in `desk_playbook_features.py` — `vertical_move`'s `require_volume` clause
  already exists (built ahead of need, per its own docstring: "only capitulation/euphoria, J-05,
  ever sets it"); this iteration calls it, it does not extend the file (expected zero diff).
- [ ] Structural guard test (new): `setup_id == "euphoria"` appears in zero recorded signal, zero
  `signal_pool`/`baseline_pool` entry, and zero `summary` key, anywhere — the concrete, testable
  form of "the marker never appears as a measurable signal row anywhere" (`docs/goal.md`'s own
  acceptance line for J-05).
- [ ] Structural guard test (new): a fixture where a marker's trigger bar occurs AFTER another
  signal's own trigger bar (in bar-index order) proves that EARLIER signal is never decorated by
  the LATER marker — the decay window's forward-only, lookahead-clean reading, machine-checked.
- [ ] `tests/test_desk_ui_guards.py`: extend `_PRICE_ARITHMETIC_FIELDS` (:152) with this iteration's
  new served numerics (`decline_mbr`, `climax_rvol`, `bars_from_climax_to_trigger`), plus seeded
  counter-test additions proving the extension actually catches an injected violation.
- [ ] `tests/test_copy_discipline.py` (or the sibling test file the existing register assertion
  lives in): a NEW pinned-text assertion on the widened `PLAYBOOK_REGISTER` string, carrying the
  mandatory rationale paragraph (the `_EXPECTED_EFFECT_COUNT` re-derivation pattern) — this is what
  makes the next widening (J-06) fail loudly instead of silently, closing the exact gap iter-4's own
  audit found.

### Frontend

- [ ] `apps/frontend/lib/types.ts`: extend `DeskPlaybookGeometry` with `decline_mbr: number`,
  `decline_bars: number`, `climax_rvol: number`, `bars_from_climax_to_trigger: number` (capitulation
  only, all served under the SAME `signal.geometry` object on the unchanged
  `GET /research/desk/playbook` payload). `playbookSetupLabel` (`page.tsx:4401`) gains `"capitulation"`
  → `"Capitulation"`.
- [ ] `apps/frontend/app/desk/page.tsx`: `PlaybookSignalDetail` (the renderer around line 4562)
  gains a `capitulation` geometry branch showing `decline_mbr`, `decline_bars`, `climax_rvol`,
  `bars_from_climax_to_trigger` beside the already-shipped disclosures/volume/market lines. The
  `euphoria_recent`/`capitulation_recent` decoration chips (`page.tsx:4647-4648`) are ALREADY wired
  and render whenever the field is `true` — no code change needed there, only real firing data to
  prove them for the first time.
- [ ] `apps/frontend/app/desk/page.tsx`: widen the empty-state sentence (`:4982`, "Run Playbook
  detects and measures the opening-range-break family on...") and the populated-section blurb
  (`:5079`, "The book's opening-range-break signals...") to name every shipped setup family — the
  frontend half of the register-widening item above.
- [ ] T-9 discipline: `rm -rf apps/frontend/.next`, rebuild, restart before any browser evidence
  capture — explicitly re-instated after iter-4 skipped it (carried item 3 from iter-4's next-step
  recommendation).
- [ ] T-11 discipline: no new `data-testid`/heading string collides with any of the 20 stored
  `goal-session-desk` golden scripts or this session's `J-10.json`; statically swept before capture.

### New user-facing capability

On the same Playbook Signals section, the operator now sees a fifth setup type — capitulation entry
after a vertical decline reverses — with its own geometry disclosures, plus (for the first time,
across ANY setup type) a live "euphoria recent" / "capitulation recent" decoration chip on any
signal that fired shortly after a climax event on the same symbol.

### New information displayed

Per capitulation signal: `decline_mbr`, `decline_bars`, `climax_rvol`, `bars_from_climax_to_trigger`.
Across every setup type: `disclosures.euphoria_recent`/`disclosures.capitulation_recent` — fields
that already existed and were always served `false`; this iteration is the first to compute them for
real. No other already-shipped field, section, or behavior changes.

### New user actions

None beyond the already-shipped session-date input + Run Playbook trigger/poll/cancel — the same act
now surfaces one more setup type and real decoration flags.

### UI surface changes

No new section. The existing Playbook Signals section (`/desk`) renders one additional setup-specific
geometry line (capitulation) and, for the first time with real data, the already-built decoration
chips on any signal.

### Product surface delta

The operator's Playbook Signals table can now contain five setup types instead of four, and any row
may now carry a "recent climax" decoration; every shipped section (`/`, `/structure`, every `/desk`
section, and every already-shipped setup family) behaves exactly as before.

### Blueprint conformance

Lands inside the already-registered **Desk → Playbook Signals** home
(`runs/goal-session-playbook/state/blueprint.md`'s Information Architecture, which already names
"J-03, extended visibly by the detector families J-04/J-05/J-06"). No nav-skeleton edit; no
`blueprint.reapproval-requested` entry; no `blueprint.md` edit — the "Playbook records" row's target
shape already covers this (same precedent iter-1 through iter-4 set: no edit when nothing new is
introduced at the row/owner/endpoint level).

### Data-contract additions

New fields within the ALREADY-REGISTERED "Playbook records" row (owner `app/research/desk_playbook.py`
+ `desk_playbook_detect.py`, endpoint `GET /research/desk/playbook`, unchanged) — no new value, no
new owner, no new endpoint:

| Field | Type/shape | On |
|---|---|---|
| `setup_id` | now also `"capitulation"` (`"euphoria"` is NEVER a value — structural test) | `signal` |
| `geometry.decline_mbr` | `number` (MBR units, ≥ `PLAYBOOK_VERTICAL_MOVE_MBR`) | capitulation signal |
| `geometry.decline_bars` | `int` (bars from the — possibly re-anchored — climax bar to `leg_low`'s formation) | capitulation signal |
| `geometry.climax_rvol` | `number` | capitulation signal |
| `geometry.bars_from_climax_to_trigger` | `int` (0..`PLAYBOOK_BOUNCE_MAX_BARS`) | capitulation signal |
| `disclosures.euphoria_recent` | `boolean` (field already existed, always `false`; now a real computed value) | any signal |
| `disclosures.capitulation_recent` | `boolean` (same) | any signal |

`playbook_input_signature` moves the moment `PLAYBOOK_SETUPS` gains `"capitulation"` (expected,
disclosed, versioned — never a silent reinterpretation of old records).

## OUT OF SCOPE

- The range family (range trades, double top/bottom — J-06). Lands into this SAME Playbook Signals
  section with zero structural UI rework once its own detectors ship.
- The back-scan (J-07), the evidence view (J-08 — the forward-guard against detect importing it
  already exists from iter-4 and stays untouched), and MCP contract v4 (J-09; MCP stays at exactly
  18 tools, zero diff to `app/mcp/__init__.py`).
- `disclosures.concurrent_signals` — stays `[]` (unaddressed by any journey's acceptance text so
  far; not part of J-05's own steps).
- Spec §4's `halted_formation` policy — still open per the iter-1 lesson; binds before J-07's
  back-scan touches real recorded sessions.
- Spec §3.7-3.9 (range_trade, double_top, double_bottom) — J-06.
- The two carried owner-ruling questions from iter-4 (1.5x jump-to-base reachability; cup rim
  constant naming) — surfaced for the operator, not resolved by this iteration.
- Any diff to `desk_forward.py` itself — imported from only, zero diff, verified by `git diff`.
- Any diff to `desk_screen*.py`, `setups.py`, `bars.py`, or `levels.py` — read/mirrored only.
- Any new primitive in `desk_playbook_features.py` — `vertical_move`'s `require_volume` clause
  already exists; expected zero diff to that file this iteration.
- Any change to any shipped `/desk` section's own behavior, columns, or copy outside the two named
  register-widening spots, or to the J-03 Playbook Signals shell's session-date input, Run/poll/cancel
  wiring, or absence/refusal states, or to the already-shipped `open_high_break`/`open_low_break`/
  `jbe`/`dbi`/`cup_handle` detection logic itself — render-only verification this iteration
  (Required-still-passing J-01/J-02/J-03/J-04/J-10).
- Any new `Config` field or fingerprint-epoch change; pin stays `08e471b10130e1e2`.
- Real (non-fixture) compute runs over the live recorded universe — fixture-scoped only.
- Cross-symbol marker decoration — decoration reads only the SAME symbol-session's own signals and
  markers, never another member's.

## DEFINITION OF DONE

- [ ] Target journey J-05 passes via browser-qa-agent — a capitulation signal and a marker-decorated
  signal both legible in the J-03 Playbook Signals section on the fixture rig, in the same
  clean-rebuilt pass: TC-1, TC-2, TC-3.
- [ ] Required-still-passing journeys J-01, J-02, J-03, J-04 remain passing with zero change to
  their own signals or content: TC-9, TC-14.
- [ ] Required-still-passing journey J-10 remains at least `partial`, browser-verified in the SAME
  clean-rebuilt pass: TC-17, TC-19.
- [ ] No anti-goal violation introduced — no threshold sweep (TC-11), the euphoria marker never
  appears as a measurable signal row (TC-4), marker decoration is lookahead-clean and forward-only
  (TC-5), lookahead property test extended for capitulation including climax re-anchoring (TC-6,
  TC-7), append-only/no-rewrite record discipline holds — duplicate keys still raise (TC-15) and a
  signature change re-keys rather than rewrites, proven by SHA-256 (TC-9, TC-10), no advice/
  probability language in new disclosures or decoration chips (TC-16).
- [ ] The OPEN minor anti-goal violation carried from iter-4 (stale "opening-range-break signals"
  register/blurb) is CLOSED, with a pinned-text guard so the next widening cannot silently drift
  again: TC-8.
- [ ] Unit tests pass; no regressions — full backend suite ≥ 2061 pass / 8 skip (the iter-4 floor),
  `Config().config_fingerprint()` prints `08e471b10130e1e2`, zero new `Config` fields: TC-13.
- [ ] The carried DBI screenshot item closed (re-taken with the corrected "descending base" label,
  in this iteration's own clean-rebuilt pass): TC-18.
- [ ] Dev handoff written at `docs/handoffs/goal-playbook-iter-5-dev.md`.

## TESTING REQUIREMENTS

- Browser: J-05 needs a real browser pass with screenshots showing a capitulation signal and a
  marker-decorated signal (its `euphoria_recent` or `capitulation_recent` chip visible) inside the
  Playbook Signals section. Required-still-passing J-01/J-02/J-03/J-04 replay via the full backend
  suite (their own behavior is not touched by this iteration; no browser re-capture needed for them
  specifically, beyond the one carried DBI screenshot). Required J-10 MUST be replayed via its
  stored golden script (`runs/goal-session-playbook/journey-scripts/J-10.json`) in the SAME
  clean-rebuilt pass, walking every shipped `/desk` section including the lower ones (sibling-
  `display:none`-collapse technique, per the iter-3 lesson). Before trusting any browser-qa FAIL,
  verify the backend is alive by REQUEST (`curl :8301/health`), not by PID (iter-2 lesson). Scope
  every browser-QA compute/plant to `TAPEOLOGY_DESK_PLAYBOOK_DIR` (+ its log-dir env vars), never
  the operator's real `.data/playbook/` store (iter-3 lesson).
- Unit/integration:
  - `desk_playbook_detect.py`: fixture goldens for `capitulation` (canonical firing: hand-computed
    `decline_mbr`, `decline_bars`, `climax_rvol`, `bars_from_climax_to_trigger`, trigger,
    invalidation) and a re-anchoring fixture (a new low forms after the initial climax bar before
    any trigger — `leg_low`/disclosures must reflect the re-anchored bar, not the original one).
  - `desk_playbook_detect.py`: a near-miss fixture (high-volume decline that meets the vertical-move
    and RVOL-surge gates but produces no reversal bar within `PLAYBOOK_BOUNCE_MAX_BARS`) paired with
    a gate-relaxed control that fires exactly one signal when (and only when) the bounce-window gate
    is relaxed — proving that gate, specifically, is the rejecter (the iter-4 lesson).
  - `desk_playbook_detect.py`: `detect_euphoria` fixture proving a firing produces a marker event
    only (no side/entry/invalidation/geometry/setup_id) and that it decorates a LATER same-symbol
    signal's `euphoria_recent` field.
  - `desk_playbook.py`: a forward-only decoration fixture — a marker firing AFTER another signal's
    own trigger bar must NOT decorate that earlier signal (lookahead-clean by construction).
  - Extend the generic truncate-after-trigger + mutate-post-trigger-bars lookahead property test
    with the capitulation canonical-firing fixture (own file/list, mirroring `_LOOKAHEAD_FIXTURES`/
    `_CONTINUATION_LOOKAHEAD_FIXTURES`).
  - New structural guards: `setup_id == "euphoria"` never appears in any signal/pool/summary; the
    marker-decoration forward-only property, both green from the moment they are added.
  - `test_desk_ui_guards.py`: `_PRICE_ARITHMETIC_FIELDS` extended with the new geometry numerics +
    seeded counter-test(s).
  - The register/blurb pinned-text assertion, with its mandatory rationale paragraph, updated to the
    new widened text.
  - A back-dated fixture re-run (before vs. after this iteration's `PLAYBOOK_SETUPS` change) shows
    the new-signature version recorded beside the old, with the old file's SHA-256 unchanged.
  - Suite-wide: `Config().config_fingerprint()` unchanged; `git diff` empty against
    `desk_forward.py`/`desk_screen*.py`/`setups.py`/`bars.py`/`levels.py`/`config.py`/
    `mcp/__init__.py`/`desk_playbook_features.py`; full suite green at ≥ 2061 pass / 8 skip.
- Error cases:
  - A capitulation formation that meets the vertical-move/RVOL gates but never produces a reversal
    bar within `PLAYBOOK_BOUNCE_MAX_BARS` emits nothing — no partial/guessed signal.
  - A euphoria formation with the same non-reversal shape (mirrored) emits no marker.
  - Thin/absent baseline or no bars for a symbol-session ⇒ disclosed absence row, never a guess
    (already-shipped absence machinery, exercised again for `capitulation`).
  - A marker whose trigger bar is AFTER a candidate signal's own trigger bar decorates nothing (the
    forward-only lookahead property, tested explicitly — see TC-5).

Test-first contract:

- TC-1: given the fixture rig with a canonical capitulation firing session (vertical decline meeting
  the gates, followed by a reversal bar within `PLAYBOOK_BOUNCE_MAX_BARS`), when the operator runs
  the Playbook for that session and reads the signals table, then a `"capitulation"` signal row
  renders with setup chip "Capitulation", side long, and its geometry line showing `decline_mbr`,
  `decline_bars`, `climax_rvol`, `bars_from_climax_to_trigger` matching the hand-computed fixture
  values (screenshot).
- TC-2: given a high-volume decline fixture that meets the vertical-move/RVOL-surge gates but never
  produces a reversal bar within `PLAYBOOK_BOUNCE_MAX_BARS` of the climax bar, when
  `compute_playbook` runs over it, then no `"capitulation"` signal is recorded for that
  symbol-session (the formation expires silently), and the gate-relaxed control fires exactly one
  signal when the bounce-window gate alone is relaxed.
- TC-3: given a fixture session with an early euphoria mirror-formation followed within
  `PLAYBOOK_MARKER_DECAY_BARS` bars by a later same-symbol signal's own trigger bar, when the
  Playbook runs and the operator reads that later signal's row, then it renders with
  `disclosures.euphoria_recent == true` and the signals table contains no `"euphoria"` row of any
  kind (screenshot of the decorated signal and its decoration chip).
- TC-4: given every recorded signal, `signal_pool`/`baseline_pool` entry, and `summary` key after
  this iteration, when the new structural guard test scans them, then it finds zero entry with
  `setup_id == "euphoria"` anywhere.
- TC-5: given a fixture where a marker's own trigger bar occurs AFTER another signal's trigger bar
  (in bar-index order) but within `PLAYBOOK_MARKER_DECAY_BARS` bars, when `compute_playbook` runs,
  then the EARLIER signal is NOT decorated (`capitulation_recent`/`euphoria_recent` stay `false`).
- TC-6: given the capitulation canonical-firing fixture added to the generic lookahead fixture list,
  when the truncate-after-trigger + mutate-post-trigger-bars property test runs against it, then the
  detector's trigger, invalidation, and geometry are unchanged by the post-trigger mutation.
- TC-7: given a fixture where price makes a new low after the initial climax bar `v` before any
  trigger fires, when `detect_capitulation` runs, then `leg_low` and the disclosed `decline_*`/
  `climax_rvol` fields re-anchor to the new climax bar rather than the original one.
- TC-8: given `PLAYBOOK_REGISTER` and the `/desk` empty-state (`page.tsx:4982`) and populated-section
  (`page.tsx:5079`) copy after this iteration, when they are read, then both name every shipped setup
  family (open-range breaks, jump-base-explosion, drop-base-implosion, cup-and-handle, capitulation)
  instead of only "opening-range-break", and the new pinned-text test asserts the exact register
  string with its rationale paragraph.
- TC-9: given every currently-recorded J-01/J-02/J-03/J-04-era playbook file, when this iteration's
  `"capitulation"` setup id joins `PLAYBOOK_SETUPS` and a fresh compute runs over the SAME fixture
  inputs used to record them (no capitulation formation present in those fixtures), then the output
  is byte-identical to what is already on disk and every existing file's SHA-256 is unchanged.
- TC-10: given a back-dated fixture recomputed after this iteration ships, when compared to its
  pre-iteration recorded version, then `playbook_input_signature` differs (new version minted beside
  the old) while the OLD file on disk is byte-identical (SHA-256 unchanged).
- TC-11: given the two structural guards shipped in iter-4 (no-threshold-sweep source-scan;
  detect-never-imports-evidence import-graph), when they run after this iteration's new detector code
  lands, then both stay green with zero relaxation.
- TC-12: given `_PRICE_ARITHMETIC_FIELDS` extended with `decline_mbr`, `climax_rvol`,
  `bars_from_climax_to_trigger`, when the seeded counter-test injects a client-side arithmetic
  violation on one of them, then the guard catches it.
- TC-13: given the full backend test suite, when it is run after this iteration's changes, then it
  reports a pass count ≥ 2061 and skip count == 8, `Config().config_fingerprint()` prints
  `08e471b10130e1e2`, and `git diff` shows zero changes to `desk_forward.py`, `desk_screen*.py`,
  `setups.py`, `bars.py`, `levels.py`, `config.py`, `mcp/__init__.py`, and
  `desk_playbook_features.py`.
- TC-14: given J-01's/J-02's/J-03's/J-04's own already-shipped test suites and the J-03 Playbook
  Signals section's shipped session-date/Run/poll/cancel/absence/refusal behavior plus the three
  J-04 setup renderers, when this iteration ships, then all of it still passes/renders with zero
  change to their own signals or content.
- TC-15: given the append-only playbook store, when a duplicate `(session_date,
  playbook_input_signature)` key is attempted, then it still raises exactly as J-01 shipped (zero
  diff to the store's write path this iteration).
- TC-16: given the new capitulation geometry disclosures and the decoration chips rendered on
  `/desk`, when `test_copy_discipline.py`'s frontend-literal walk scans them, then zero
  probability/expectancy/significance/advice language is found.
- TC-17: given the T-9 clean-rebuild discipline (skipped in iter-4), when `apps/frontend/.next` is
  removed/rebuilt/restarted before this iteration's browser pass, then the dev handoff records the
  rebuild timestamp preceding every screenshot's own timestamp.
- TC-18: given the iter-4 carried item (the DBI screenshot predates the "descending base" label
  fix), when this iteration's browser pass runs, then a fresh DBI signal screenshot showing the
  corrected label is captured in the SAME clean-rebuilt pass.
- TC-19: given J-10's stored golden script and every shipped `/desk` section, when this iteration's
  browser pass replays it (sibling-`display:none`-collapse technique for the lower sections), then
  it passes with zero heading/`data-testid` collisions against any stored script, with screenshots
  for every shipped section.

## NOTES

- **Why the decay window is forward-only (a lookahead-honesty reading, logged as an assumption).**
  `docs/goal.md` says a marker "sets `euphoria_recent: true` on any signal triggering within
  `PLAYBOOK_MARKER_DECAY_BARS`" without stating a direction. The only reading consistent with the
  era's critical "no lookahead" rail is marker-leads-signal (a later signal may be decorated by an
  earlier marker; a marker can never reach back and decorate a signal that already triggered before
  it) — the opposite reading would make a signal's own served fields depend on bars strictly after
  its own trigger. Logged to `runs/goal-session-playbook/state/assumptions.md`.
- **Function names are this decomposer's concrete proposal** (`detect_capitulation`,
  `detect_euphoria`), consistent with the module's existing `detect_jbe`/`detect_dbi`/
  `detect_cup_handle` convention. If the developer finds a clearer name, keep euphoria's
  marker-only, non-served nature unambiguous in the name and note the actual names chosen in the dev
  handoff — no ledger entry needed (routine scoping, not a goal ambiguity).
- If the spec is found ambiguous or unimplementable for either detector as literally written, drop
  it from this iteration, record the drop, and surface it for an owner ruling (Constraints
  §"The spec is canonical") — do not improvise a rule to keep J-05 fully green.
- **Key anchors for the developer** (verified against the current tree at authoring; re-locate by
  symbol name, never by line arithmetic): `desk_playbook_features.py` — `vertical_move` :216 (the
  `require_volume`/`rvols`/`rvol_surge` clause this iteration is the first to exercise). `desk_playbook_detect.py`
  — `detect_jbe`/`detect_dbi`/`detect_cup_handle` (the detector-function shape to mirror), the
  `"euphoria_recent"`/`"capitulation_recent"` stub-`False` sites already present at three call sites
  (search the string) marking exactly where real values must flow. `desk_playbook.py` —
  `PLAYBOOK_SETUPS` :147, `playbook_parameters()`'s `vertical_*`/`bounce_max_bars`/
  `marker_decay_bars` entries (already embedded, unused until now), `PLAYBOOK_REGISTER` :159, the
  compute walk's `detected_signals` assembly :590-601. `docs/playbook-detector-spec.md` — §1's
  constants table (all five capitulation/euphoria constants already tabulated), §3.5. Frontend —
  `apps/frontend/app/desk/page.tsx`'s `playbookSetupLabel` :4401, the signal-detail renderer near
  :4562, the decoration chips :4647-4648 (already rendering, needs real data only), the two copy
  spots :4982/:5079; `apps/frontend/lib/types.ts`'s `DeskPlaybookGeometry` :1485.
- **Scope-creep check:** every IN SCOPE item traces to J-05's own steps/acceptance text in
  `docs/goal.md`, or the iter-4 evaluator's next-step recommendation's carried items — nothing here
  reaches outside `docs/goal.md`'s Key Capabilities or Constraints.
