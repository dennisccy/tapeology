# The Playbook — detector specification (Era B2)

Canonical formation/trigger/stop definitions for the intraday setups of Graifer & Schumacher,
*Techniques of Tape Reading* (McGraw-Hill, 2004), adapted to 5-minute OHLCV bars over the desk
universe. **This file is the single source of the detector rules and the pre-registered constant
set.** Goal-mode developers implement from here; they never re-derive, re-name, or re-tune a
threshold. Every constant is tagged **BOOK** (the book's own number) or **ADAPTATION** (a single
named choice where the book is vague — the tag records the book basis and the rationale).
Changing any constant is a **named revision**: the new value lands in code, re-keys every future
record through the parameters signature, and never touches a recorded file. Threshold sweeps are
banned outright (`docs/research-directions.md` DO-NOT #5).

Target modules (desk family naming): `app/research/desk_playbook_features.py` (primitives),
`app/research/desk_playbook_detect.py` (detectors), `app/research/desk_playbook.py`
(constants + parameters + signature + store + walker). Bars are read through
`BarStore.merged_bars(symbol, timeframe)` (`app/research/bars.py:883`) only.

---

## 0. Shared conventions (binding on every detector)

**Bars and session.** The detection series is the symbol's 5m bars for the session date,
extracted with the `_session_slice` semantics (`app/research/desk_forward.py:295`) and then
filtered to regular trading hours: ET 09:30 ≤ bar open < 16:00. `slot(bar)` = index in the RTH
5m sequence (0..77 on a full day; fewer on half-days — `session_bar_count` is disclosed on every
signal). 1m bars are read by the opening-range builder only.

**MBR — the scale unit.** `MBR` = median(high − low) over all RTH 5m bars of the prior
`PLAYBOOK_BASELINE_SESSIONS` sessions of the same symbol. One number per symbol-session,
entry-time legal by construction (prior sessions only). Every price-distance threshold below is
an MBR multiple. This is the deliberate ADAPTATION replacing the book's absolute-cents scale
(2002–04 Nasdaq: "25 cents" on ~$20 stocks ≈ 1.25%); modern S&P100 5m bars are calmer, so
relative-to-recent-range beats a fixed percent. `MBR = 0` or fewer than
`PLAYBOOK_MIN_BASELINE_SESSIONS` prior sessions ⇒ the symbol-session emits **no signals**
(fail-closed, disclosed as an honest absence row).

**RVOL — the one relative-volume definition.** `RVOL(bar) = bar.volume / median(volume of the
same RTH slot over the prior PLAYBOOK_BASELINE_SESSIONS sessions)`, requiring at least
`PLAYBOOK_MIN_BASELINE_SESSIONS` observations of that slot, else RVOL is null and any condition
needing it fails closed. This is `docs/research-directions.md` Card 5.5's `rvol_m` formula at 5m
granularity. Every volume condition in every detector is expressed on this RVOL — no second
volume normalization exists anywhere in the playbook.

**Entry convention — modeled stop-through fill.** Every playbook entry models a stop order
electing at the trigger price `T`: long `entry = max(trigger_bar.open, T)`, short
`entry = min(trigger_bar.open, T)`. `entry_kind = "level"` when the bar opened on the near side
of `T`, `"gap_open"` when it opened beyond. This is a named ADAPTATION of the wall rail's
resting-limit convention (`desk_forward.py` support `min(open, price_high)`): a limit-at-edge
model would systematically credit breakout fills better than achievable. The trigger band served
to the measurement is `(T, T·(1+PLAYBOOK_MAX_CHASE_FRAC))` for longs, mirrored for shorts —
the band width is BOOK (the 3–5-cent no-chase rule ≈ 0.2% of price). A trigger bar opening
beyond the band still fires, with `gapped_beyond_chase: true` (the book would skip; we record
and flag rather than suppress — suppression would hide exactly the fills the rule warns about).

**Measurement.** Each signal is measured with the desk's existing conventions by calling
`_measure_from(session_bars, anchor_index, entry, entry_kind, tf_minutes, sign)`
(`desk_forward.py:451`) on the finest series the session holds (1m when present, else 5m; the
5m→1m anchor mapping takes the first 1m bar of the trigger 5m window whose [low, high] contains
`T`, falling back to the window's first 1m bar). `sign = +1` long / `−1` short, passed
explicitly. Horizons, measures, dual MDD, truncation honesty, and the seeded random-anchor
baseline are the rail's, unchanged.

**Lookahead law (the one argument, holding for all detectors).** Formation conditions read bars
`[session start .. t−1]` only — including pivot-confirmation delay: a swing pivot is not known
until `PLAYBOOK_PIVOT_LOOKBACK_BARS` bars after its center (the `levels.py:_swing_pivots` strict
rule, `app/research/levels.py:325`), and if price crosses the would-be trigger before the
defining pivot is confirmed, no signal fires (fail-closed). The trigger predicate at bar `t`
uses ONLY the price-crossing fact (`high > T` / `low < T`) — knowable at the moment it happens
intrabar. Every other bar-`t` quantity (close, range, volume, RVOL) appears **only in
disclosures, never in gates** — gating a fill on the trigger bar's own completed volume is
lookahead-at-fill and is banned. Baselines (MBR, RVOL denominators) are prior-sessions-only.
Market context reads index bars strictly before the trigger bar's epoch.

**Break strictness.** A break is strict (`high > U`, `low < L`). Equality is a touch, never a
break (mirrors `_swing_pivots`' tie discipline).

**Invalidation level (the book's stop).** Every signal carries `invalidation_price` — the
book's structure rule (under/over the structure whose break kills the thesis) padded by
`PLAYBOOK_STOP_PAD_FRAC` of the nominal distance: long `S − PAD·(T − S)`, short mirrored,
where `S` is the structural level (base low, handle bottom, leg low, range extreme, pattern
top). BOOK: the book pads obvious stops by ~20–40% of nominal distance; the midpoint 0.30 is
pre-registered. `invalidation_price` is a **disclosure level** — the rail never simulates
stop-outs; the served register states returns are not stop-adjusted. A same-pass
`invalidation_breached` block (per-horizon boolean + `first_breach_minutes`) is computed
OUTSIDE `_measure_from` (so the rail's shape never changes) — a boolean fact, never an exit
model.

**Market context (disclosure, never a gate).** Index = SPY 5m bars (already frozen in the
store; `market_direction.source: "SPY"`). `market_move` = (idx close[t−1] − idx
close[t−1−PLAYBOOK_MKT_LOOKBACK_BARS]) in index-MBR units. Alignment: `supportive` when signed
with the signal beyond `PLAYBOOK_MKT_NEUTRAL_BAND_MBR`; `against` when signed opposite beyond
the band; else `neutral`. `book_would_skip_market: true` when `against` (Trader's Action step 5
— the book skips; we disclose). Relative-strength disclosure (Ch 13 narrow-range rule):
`relative_strength_strong: true` when the stock's last pre-trigger close is within
`PLAYBOOK_NEAR_EXTREME_MBR` of its session high while SPY's last close is within the same
tolerance (index-MBR) of its session low — mirrored for shorts. No SPY bars for the session ⇒
`market_direction: null` + reason (honest absence, never a crash).

**Volume-into-trigger discriminator (Part Three, Example 3 — shared, defined once).** Over the
`PLAYBOOK_APPROACH_BARS` bars strictly before the trigger bar:
- `exhausted_spike` — some approach bar has `RVOL ≥ PLAYBOOK_RVOL_SURGE` AND its high is within
  `PLAYBOOK_NEAR_EXTREME_MBR · MBR` of `T` AND it failed to close beyond `T` (volume spent AT
  the level without eating it — the book says do NOT buy this break);
- `constructive` — approach RVOLs non-decreasing and none ≥ SURGE (steady climb/base; the
  spike, if any, lands on the trigger bar itself, disclosed post-hoc via `rvol_trigger_bar`);
- `neutral` — otherwise.
Disclosure only, never a gate.

**Provenance ("the parameters hash").** Every served playbook payload already carries
`playbook_input_signature` (the sha256[:16] over the recorded series' `(symbol, timeframe, id,
checksum)` tuples, `config_fingerprint`, and the canonical `parameters` blob — see §1's closing
paragraph) beside `config_fingerprint` and the verbatim `parameters` object itself. Together these
three already-served fields ARE the goal's own "parameters hash" line — the signature is a hash
*of* the parameters (among other inputs), and the parameters themselves are served alongside it in
full, so nothing is hidden and nothing is re-derivable-but-undisclosed. This is a documentation-only
ruling, not a new field: no source constant moves and no payload key is added or renamed by it (J-04
carries this ruling forward from the iteration that raised it, mirroring the `PLAYBOOK_OR_MIN_1M_BARS`
prose-to-table promotion pattern below).

**Shared disclosure block on every signal:** `rvol_trigger_bar` (post-hoc),
`approach_rvol_max`, `spike_into_trigger_verdict` (the discriminator), `spiky_approach`
(single-bar vertical into the level), the market block, `attempt_count` at `T` (pre-trigger
zone touches of `[T − NEAR_EXTREME·MBR, T]` with the re-arm rule — the book's 2nd/3rd-attempt
rule as data), `bars_to_close`, `concurrent_signals` (other detector ids sharing the trigger
bar), `euphoria_recent`/`capitulation_recent` (marker within `PLAYBOOK_MARKER_DECAY_BARS`),
`gapped_beyond_chase`, `session_bar_count`, `opening_range_basis` where relevant, and
`principles` — which of the book's six Ch-9 principles the formation exemplifies
(P1 euphoria/capitulation, P2 trend beginning, P3 trend confirmation, P4 shallow-retracement
continuation, P5 decreasing-volume reversal, P6 passive accumulation/distribution).

---

## 1. Pre-registered constants (the COMPLETE tunable surface — nothing else exists)

| Constant | Value | Source |
|---|---|---|
| `PLAYBOOK_BASELINE_SESSIONS` | 20 | ADAPTATION — Card 5.5's RVOL convention |
| `PLAYBOOK_MIN_BASELINE_SESSIONS` | 10 | ADAPTATION — minimum honest median |
| `PLAYBOOK_RVOL_SURGE` | 2.0 | ADAPTATION — book's "volume surge / pace pickup" unquantified |
| `PLAYBOOK_RVOL_ELEVATED` | 1.5 | ADAPTATION — Card 5.5 high-RVOL bucket boundary |
| `PLAYBOOK_RVOL_DRYUP` | 0.7 | ADAPTATION — Card 5.5 low-RVOL bucket boundary |
| `PLAYBOOK_VOL_CONTRAST_RATIO` | 0.6 | ADAPTATION — mechanical "dries on pullback vs advance" |
| `PLAYBOOK_MAX_CHASE_FRAC` | 0.002 | BOOK — 3–5c chase on ~$20 ≈ 0.2% |
| `PLAYBOOK_STOP_PAD_FRAC` | 0.30 | BOOK — 20–40% stop padding; midpoint |
| `PLAYBOOK_OR_MINUTES` | 15 | BOOK — opening range = first 15–20 min; lower endpoint |
| `PLAYBOOK_OR_MIN_1M_BARS` | 10 | ADAPTATION — §2 primitive 2's own floor: fewer than 10 of the 15 one-minute bars on file degrades the opening range to the 5m basis (J-01 audit B3: named in code from birth, tabulated here) |
| `PLAYBOOK_NARROW_OR_MAX_MBR` | 3.0 | ADAPTATION — relative form of the ≤25c narrow range |
| `PLAYBOOK_JUMP_MIN_MULT` | 1.5 | BOOK — jump ≥ 1.5–2× base; stated minimum. **Inert** (2026-08-11, R-3.2(c)): dominated by `PLAYBOOK_JUMP_MIN_MOVE_MBR`/`PLAYBOOK_BASE_MAX_RANGE_MBR` (§3.3) — has never independently rejected a `jbe`/`dbi` formation |
| `PLAYBOOK_JUMP_MIN_MOVE_MBR` | 3.0 | ADAPTATION — floor so tiny/tiny can't satisfy the ratio |
| `PLAYBOOK_JUMP_LOOKBACK_BARS` | 6 | ADAPTATION — jump low read from the 30 min before the base |
| `PLAYBOOK_BASE_MIN_BARS` | 3 | ADAPTATION — book gives no consolidation duration |
| `PLAYBOOK_BASE_MAX_BARS` | 12 | ADAPTATION — 60-min cap; beyond it the "base" is the day's range |
| `PLAYBOOK_BASE_MAX_RANGE_MBR` | 2.0 | ADAPTATION — relative form of the ≤25c narrow base |
| `PLAYBOOK_BASE_FLATLINE_MAX_MBR` | 1.0 | ADAPTATION — §3.3/§3.4's own prose ("base range ≤ 1.0 MBR — the flatline-at-the-high variation") named as a constant (J-04, the `PLAYBOOK_OR_MIN_1M_BARS` precedent) |
| `PLAYBOOK_NEAR_EXTREME_MBR` | 1.0 | ADAPTATION — mechanical "near the high/low" |
| `PLAYBOOK_PIVOT_LOOKBACK_BARS` | 3 | ADAPTATION — 5m intraday N for the strict-pivot rule |
| `PLAYBOOK_CUP_MIN_BARS` | 6 | BOOK — cup ≥ 30 min |
| `PLAYBOOK_CUP_OPTIMAL_BARS` | 12 | BOOK — ≥ 1 h optimal (disclosure only) |
| `PLAYBOOK_HANDLE_MAX_RETRACE_FRAC` | 0.5 | BOOK — handle ≤ 50% of cup depth |
| `PLAYBOOK_HANDLE_MAX_DURATION_FRAC` | 0.30 | BOOK — handle ≤ 30% of cup duration (25% desirable → disclosure) |
| `PLAYBOOK_HANDLE_DESIRABLE_DURATION_FRAC` | 0.25 | BOOK — this row's own "25% desirable" parenthetical, named as a constant (J-04, the `PLAYBOOK_OR_MIN_1M_BARS` precedent) so `handle_duration_desirable` reads through `playbook_parameters()` like every other threshold |
| `PLAYBOOK_RIM_MATCH_MBR` | 1.0 | ADAPTATION — "cup edges at the day's high" tolerance |
| `PLAYBOOK_MIN_STRUCTURE_DEPTH_MBR` | 2.0 | ADAPTATION — min cup depth AND min valley depth |
| `PLAYBOOK_VERTICAL_WINDOW_BARS` | 3 | ADAPTATION — "near-vertical" window (15 min) |
| `PLAYBOOK_VERTICAL_MOVE_MBR` | 4.0 | ADAPTATION — net move for capitulation/euphoria |
| `PLAYBOOK_VERTICAL_BAR_MBR` | 2.5 | ADAPTATION — single-bar spike (spiky-approach flag) |
| `PLAYBOOK_BOUNCE_MAX_BARS` | 3 | ADAPTATION — reversal confirmation must come fast |
| `PLAYBOOK_RANGE_MIN_WIDTH_MBR` | 4.0 | ADAPTATION — narrower = breakout-only per Ch 13 |
| `PLAYBOOK_RANGE_HOLD_TOL_MBR` | 0.5 | ADAPTATION — "held" tolerance; also the absorption-bar max range and (2026-08-11, R-3.2(b)) the `turned_at_midrange` "at the midpoint" tolerance |
| `PLAYBOOK_TOPS_MATCH_MBR` | 1.0 | ADAPTATION — two tops "at the same level" |
| `PLAYBOOK_TOPS_MIN_SEPARATION_BARS` | 4 | ADAPTATION — tops ≥ 20 min apart |
| `PLAYBOOK_LADDER_HEALTHY_LOW` / `_HIGH` | 0.50 / 0.75 | BOOK — ladder step 50–75% of prior step (disclosure only) |
| `PLAYBOOK_MKT_LOOKBACK_BARS` | 6 | ADAPTATION — 30-min index-direction window |
| `PLAYBOOK_MKT_NEUTRAL_BAND_MBR` | 1.0 | ADAPTATION — neutral band, index-MBR units |
| `PLAYBOOK_MARKER_DECAY_BARS` | 6 | ADAPTATION — euphoria/capitulation marker decorates for 30 min |
| `PLAYBOOK_APPROACH_BARS` | 3 | ADAPTATION — volume-into-trigger window |
| `PLAYBOOK_MAX_JBE_SIGNALS_PER_SESSION` | 2 | ADAPTATION — ladder steps; every other detector caps at 1 (per side where sided) |

Companion structural constants (shape, not thresholds): `PLAYBOOK_SETUPS` (the setup-id tuple),
`PLAYBOOK_MARKET_SYMBOL = "SPY"`, `PLAYBOOK_BASELINE_SEED = DESK_FORWARD_BASELINE_SEED`,
`PLAYBOOK_RETURN_SIGN_CONVENTION = "side_relative"`, `PLAYBOOK_SIGNAL_MEASURES`,
`PLAYBOOK_MIN_N_DISCLOSURE = 12` (evidence low-n tag — a disclosure floor, never a gate).
All of the above are embedded in `playbook_parameters()` and hashed into
`playbook_input_signature` (the `forward_parameters()` pattern, `desk_forward.py:225`).

---

## 2. Shared primitives (`desk_playbook_features.py` — eight functions, nothing more)

1. `rth_session_slice(bars_5m, session_date)` — `_session_slice` semantics + RTH filter,
   slots attached. (Attribution comment to `desk_forward._session_slice`.)
2. `opening_range(bars_1m, session_date, minutes)` — `{high, low, width, basis: "1m"|"5m",
   bars_used}` over ET 09:30–09:45; fewer than 10 of the 15 one-minute bars on file ⇒ fall back
   to the first 3 five-minute bars with `basis: "5m"`; neither ⇒ null (fail-closed, disclosed).
3. `baselines(symbol, session_date)` — one pass over the prior 20 sessions' RTH 5m bars
   returning `MBR` + the per-slot volume-median vector (the RVOL denominators). The only
   baseline builder.
4. `swing_pivots(bars, lookback)` — the `levels.py:_swing_pivots` strict-extreme rule (strictly
   greater/less than all ±N neighbours; ties are not pivots; series ends unconfirmable). The
   confirmation delay IS the lookahead guard.
5. `consolidation_range(bars, end_idx, min_bars, max_bars, max_range)` — the maximal window
   ending at `end_idx` with `max(high) − min(low) ≤ max_range`; returns `(start_idx, U, L)` or
   null. Shared geometry for JBE/DBI base, handle, flatline.
6. `vertical_move(bars, end_idx, n, k, direction, require_volume)` — net move over the last `n`
   bars ≥ `k·MBR` in `direction`, ≥ `n−1` of `n` closes in that direction; with
   `require_volume`: `RVOL(last) ≥ PLAYBOOK_RVOL_SURGE` and ≥ `RVOL(first)` (rising). Powers
   capitulation/euphoria and (n=1, k=`PLAYBOOK_VERTICAL_BAR_MBR`, no volume clause) the
   spiky-approach flag.
7. `zone_touches(bars, lo, hi)` — overlap + full-exit-re-arm semantics (attribution to
   `desk_forward._touch_scan`); powers attempt counts, tested-twice-and-held, second-top
   support.
8. `market_context(index_bars_5m, session_date, before_epoch)` — §0's market block.

---

## 3. Detectors

Format per detector: formation → trigger → invalidation → caps → extra disclosures → edge
cases. Side/band/entry/measurement always follow §0.

### 3.1 `open_high_break` / 3.2 `open_low_break`
- **Formation.** OR per primitive 2 (`PLAYBOOK_OR_MINUTES` BOOK). Narrowness gate:
  `or_width ≤ PLAYBOOK_NARROW_OR_MAX_MBR · MBR` (ADAPTATION for the book's ≤25c). Eligible
  trigger bars: 5m slots ≥ 3 (the OR occupies slots 0–2).
- **Trigger.** First 5m bar with `high > or_high` ⇒ `open_high_break`, `T = or_high`, long;
  or `low < or_low` ⇒ `open_low_break`, `T = or_low`, short. First break wins; **one
  opening-range signal per symbol-session total.** A bar strictly breaking BOTH sides with
  neither previously broken ⇒ no signal; `ambiguous_outside_bar` recorded as a formation
  diagnostic.
- **Invalidation.** Long: `S = or_low`, `invalidation = or_low − 0.30·(or_high − or_low)`
  (BOOK structure + BOOK pad). Short mirrored.
- **Disclosures.** `or_width_mbr`, `or_bars_used`, `opening_range_basis`,
  `open_vs_prior_close_pct` (gap context), `slots_to_break`. Principles: `["P4"]` exactly when
  `spike_into_trigger_verdict == "constructive"` (§0's already-defined discriminator — pre-break
  pullbacks were shallow and dry); `[]` (structural-only) otherwise (J-01 audit B4: this mechanical
  reading is the pre-registered rule, matching `desk_playbook_detect.py`'s implementation verbatim).
- **Edge cases.** `gap_open` triggers at slot 3 are common on trend opens —
  `gapped_beyond_chase` does the honesty work. No 1m and no 5m OR ⇒ silent symbol-session
  (disclosed absence).

### 3.3 `jbe` / 3.4 `dbi` (exact mirror; JBE described)
- **Formation** (windows ending at `t−1`): base = `consolidation_range` with
  `PLAYBOOK_BASE_MIN_BARS ≤ len ≤ PLAYBOOK_BASE_MAX_BARS` and
  `base_range = U − L ≤ PLAYBOOK_BASE_MAX_RANGE_MBR · MBR` (ADAPTATION). Jump: `jump_low` =
  min low of the `PLAYBOOK_JUMP_LOOKBACK_BARS` bars before base start; `jump = U − jump_low`;
  gates `jump ≥ PLAYBOOK_JUMP_MIN_MULT · base_range` (BOOK ≥1.5×) AND
  `jump ≥ PLAYBOOK_JUMP_MIN_MOVE_MBR · MBR` (ADAPTATION floor). **The BOOK ratio gate is inert**
  (2026-08-11 annotation, R-3.2(c) — doc text only, no code or constant VALUE changed): `base_range`
  is itself capped at `PLAYBOOK_BASE_MAX_RANGE_MBR · MBR` (2.0) by the base-formation gate above, so
  `PLAYBOOK_JUMP_MIN_MULT · base_range` (1.5×) can never exceed `1.5 × 2.0 = 3.0` MBR — exactly
  `PLAYBOOK_JUMP_MIN_MOVE_MBR` — meaning the ADAPTATION floor always binds at least as tightly. The
  BOOK ratio has never independently rejected a formation (min observed ratio across the 32 recorded
  `jbe`/`dbi` signals: 1.735). Both gates stay implemented verbatim; the back-scan must not credit
  the BOOK ratio with a rejection it structurally cannot make. Near the high:
  `U ≥ session_high_so_far − PLAYBOOK_NEAR_EXTREME_MBR · MBR` at `t−1`. Volume: median
  RVOL(jump bars) ≥ 1.0 with max ≥ `PLAYBOOK_RVOL_ELEVATED` (P3), and median RVOL(base bars)
  ≤ `PLAYBOOK_VOL_CONTRAST_RATIO` × median RVOL(jump bars) (P4 dry base; ADAPTATION ratio).
- **Trigger.** First bar `t` with `high > U`. `T = U`.
- **Invalidation.** `S = L`; `L − 0.30·(U − L)` (BOOK: under the range's lower limit, padded).
- **Caps.** ≤ `PLAYBOOK_MAX_JBE_SIGNALS_PER_SESSION` (2) per side — ladder steps; a second
  base must start after the first trigger bar.
- **Disclosures.** `jump_mbr`, `base_range_mbr`, `base_bars`, `base_flatline` (base range
  ≤ 1.0·MBR — the flatline-at-the-high variation), `base_lows_ascending` (the
  ascending-triangle variation), `ladder_step_ratio` vs `PLAYBOOK_LADDER_HEALTHY_LOW/_HIGH`
  (BOOK: <0.50 trend exhausting, >0.75 break likely fails). Principles: P3 + P4.
- **Edge cases.** A base still open at session close emits nothing.

### 3.5 `capitulation` (entry) + `euphoria` (marker only)
- **Formation.** `vertical_move` DOWN ending at climax bar `v`: net decline ≥
  `PLAYBOOK_VERTICAL_MOVE_MBR · MBR` over `PLAYBOOK_VERTICAL_WINDOW_BARS` bars, ≥ n−1 down
  closes, `RVOL(v) ≥ PLAYBOOK_RVOL_SURGE` and rising (all ADAPTATION — the book's "fast sharp
  vertical decline + volume/pace pickup" is unquantified). `leg_low` = min low through `t−1`;
  a new low after `v` re-anchors `v` (the panic still running).
- **Trigger.** First bar `t` with `t − v ≤ PLAYBOOK_BOUNCE_MAX_BARS` and `high > high[t−1]`
  (first-strength reversal bar). `T = high[t−1]` — fully known at `t−1`; the crossing is the
  only bar-`t` fact. No trigger within the window ⇒ formation expires.
- **Invalidation.** `S = leg_low`; `leg_low − 0.30·(T − leg_low)` (BOOK: under the bounce low;
  "any new low should be considered trade failure").
- **Caps.** 1 per symbol-session (first).
- **Disclosures.** `decline_mbr`, `decline_bars`, `climax_rvol`,
  `bars_from_climax_to_trigger`. Principle: P1.
  **`decline_bars`/`decline_mbr`, precisely (goal-playbook-iter-6 doc-only closure of the OPEN
  minor anti-goal item iter-5 carried — zero constant/behavior change, transcribing the reading
  `desk_playbook_detect.py`'s `_find_climax_formation`/`detect_capitulation` already ship).**
  Re-anchoring (above) means the climax bar `v` used for these two disclosures is not always the
  RAW candidate the `vertical_move` window first found — a new low forming after `v` (before any
  trigger) re-anchors `v` to that later bar, since the panic is still running. `decline_bars`
  spans the WHOLE decline leg: from the ORIGINAL `vertical_move` window's own start bar through
  the (possibly re-anchored) climax bar `v` — a formation that re-anchors therefore reports a
  LONGER decline than the raw `PLAYBOOK_VERTICAL_WINDOW_BARS` constant, never a fixed value.
  `decline_mbr` is the net decline, in MBR units, from the close of the bar immediately BEFORE the
  vertical-move window began through to the eventual (possibly re-anchored) `leg_low` — the same
  "how far did price actually fall" reading `vertical_move`'s own net-move check uses internally,
  extended through whatever re-anchoring occurred. Both disclosures always describe the FINAL,
  re-anchored leg, never the raw candidate's own (possibly shorter/shallower) window.
- **`euphoria`** — exact mirror UP with the same constants, emitted as a **marker, not a
  signal**: no side, no band, never measured (BOOK: an exit/avoid signal; the authors do not
  short strong stocks on euphoria). It sets `euphoria_recent: true` on any signal triggering
  within `PLAYBOOK_MARKER_DECAY_BARS`; capitulation events symmetrically set
  `capitulation_recent`.

### 3.6 `cup_handle` (long only in v1 — the book presents the long form)
- **Formation.** Left rim = confirmed swing-high pivot within `PLAYBOOK_NEAR_EXTREME_MBR · MBR`
  of session-high-so-far (2026-08-11, R-3.2(d): named to match the shipped code — this
  session-high-so-far test has never read `RIM_MATCH_MBR`; doc text only, `cup_handle` unchanged).
  Cup bottom = min low after it; depth ≥
  `PLAYBOOK_MIN_STRUCTURE_DEPTH_MBR · MBR` (ADAPTATION). Right rim = later confirmed
  swing-high pivot within `RIM_MATCH` of the left rim, itself near the session high. Cup
  duration ≥ `PLAYBOOK_CUP_MIN_BARS` (BOOK ≥ 30 min; ≥ `PLAYBOOK_CUP_OPTIMAL_BARS` disclosed
  as `cup_optimal`). Cup volume (BOOK shape, ADAPTATION ratio): median RVOL of the middle
  third of cup bars ≤ `PLAYBOOK_VOL_CONTRAST_RATIO` × median RVOL of the outer thirds (dry at
  the bottom, alive at the edges). Handle: bars after the right rim with min low ≥
  `rim − PLAYBOOK_HANDLE_MAX_RETRACE_FRAC · cup_depth` (BOOK ≤ 50%), duration ≤
  `PLAYBOOK_HANDLE_MAX_DURATION_FRAC` × cup duration (BOOK ≤ 30%; ≤ 25% flagged
  `handle_duration_desirable`), median RVOL(handle) ≤ contrast × outer-third median (BOOK dry
  handle).
- **Trigger.** First bar after ≥ 1 handle bar with `high > T`,
  `T = max(left_rim_high, right_rim_high)` (BOOK: break of the rim). Both rims
  pivot-confirmed strictly before `t`.
- **Invalidation.** `S = handle_bottom`; `S − 0.30·(T − S)` (BOOK: below the handle bottom).
- **Caps.** 1 per symbol-session.
- **Disclosures.** `cup_bars`, `cup_depth_mbr`, `handle_retrace_frac`,
  `handle_duration_frac`, `cup_optimal`, the three RVOL medians. Principles: P4 + P5-inverse.
- **Edge cases.** A handle dipping below 50% of cup depth voids the formation (it is now a
  range or a double top — detectors are independent hypotheses and both may evaluate). A
  handle still open at close emits nothing.

### 3.7 `range_trade` (support-bounce long + resistance-fade short) — PROVISIONAL TIER
- **Arming (BOOK: "test the low and high twice and hold").** At `t−1`: session range
  `SH − SL ≥ PLAYBOOK_RANGE_MIN_WIDTH_MBR · MBR` (ADAPTATION — narrower is breakout-only per
  Ch 13); high zone `[SH − NEAR_EXTREME·MBR, SH]` and low zone `[SL, SL + NEAR_EXTREME·MBR]`
  each with `zone_touches ≥ 2` (re-arm semantics), each later touch extending the extreme by
  ≤ `PLAYBOOK_RANGE_HOLD_TOL_MBR · MBR` ("held").
- **Trigger — the mechanical reading of "first sign of strength" (the book's vaguest
  instruction; this reading is the pre-registered choice):** `b` = the arming-completing touch of
  the low zone specifically — the LAST of the `≥ 2` touches the Arming clause above requires, not
  any earlier touch in that same sequence (2026-08-11, R-3.2(e): narrowed to name the shipped
  anchor exactly, `_range_trade_side`, `desk_playbook_detect.py:1068-1153`; doc text only, zero
  code change). From `b`: the first bar `t` with `b < t ≤ b + PLAYBOOK_BOUNCE_MAX_BARS`,
  `high > high[t−1]`, and `min(low[b..t−1]) ≥ SL − RANGE_HOLD_TOL·MBR`. `T = high[t−1]` — the same
  reversal-bar grammar as the capitulation bounce (one shared mechanism, not a second vague one).
  Resistance-fade mirrored (`b` = the high zone's own arming-completing touch).
- **Invalidation.** Long `S = SL`, `SL − 0.30·(T − SL)` (BOOK: just outside the range
  bounds). Short mirrored.
- **Caps.** 1 per side per symbol-session.
- **Disclosures.** `range_width_mbr`, per-zone touch counts, `absorption_bar_present` — a zone
  bar with `RVOL ≥ PLAYBOOK_RVOL_ELEVATED` and range ≤ `RANGE_HOLD_TOL·MBR` (P6 passive
  accumulation/distribution, mechanical ADAPTATION) — plus two named midrange disclosures
  (2026-08-11, R-3.2(b): split spec-first, BEFORE any code change, into the two fields below; the
  shipped boolean answered only the first). Both read over the SAME approach window
  `session_bars[b0..b]` (`b0` = the armed zone's own FIRST touch, `b` = the Trigger clause's
  arming-completing touch above) — entry-time legal by construction, since neither reads past `b`:
  - `crossed_midrange` — did price cross the range midpoint on the approach: any bar's high
    (long) / low (short) within the window reaches `(SH + SL)/2` or beyond.
  - `turned_at_midrange` — whether the prior swing turned at midrange (the BOOK midrange rule):
    the swing's OWN extreme within the SAME window (`max(high)` long / `min(low)` short — the
    furthest point price reached before returning to complete the arming touch `b`) lies within
    `PLAYBOOK_RANGE_HOLD_TOL_MBR · MBR` of `(SH + SL)/2` — this detector's own already-registered
    "held" tolerance, reused verbatim for an "at the midpoint" reading; no new constant. Optional
    key (absent on every record recorded before this field shipped); disclosure-only — it never
    gates, suppresses, or creates a signal.
  Principles: P6 when absorption present; P5 at the high side.
- **Edge cases.** A strict break beyond a zone by > `HOLD_TOL` dissolves range-mode (re-arms
  only on a new twice-tested range).
  **Degenerate trigger reference (clarification, 2026-08-11 — ADAPTATION, narrowing only, no
  new constant).** The Invalidation clause above is arithmetic on `T − SL`: it pads the range
  bound by 30% of the distance from the range low to the trigger reference, and therefore
  presupposes `T > SL` (long; `T < SH` short). That premise is not automatic — the Trigger
  clause tolerates the pre-trigger bars dipping to `SL − RANGE_HOLD_TOL·MBR`, so a reversal bar
  whose reference `high[t−1]` sits entirely below the arming-time `SL` is reachable, and there
  `SL − 0.30·(T − SL)` INVERTS: a long's invalidation lands ABOVE its own entry and the signal
  is recorded born-invalidated. That is a degenerate formation, not a signal: following §4's
  own class of degenerate/edge rules ("formation open at session end ⇒ nothing emitted"; thin
  data ⇒ silent, never a guess), the formation is **voided, fail-closed** — `T ≤ SL` (long) /
  `T ≥ SH` (short) emits nothing, and the detector continues its walk for a later arming.
  No threshold is involved; the clause can only remove signals, never create one.
- **Provisional status.** First candidate for removal in a named revision if its forward
  distributions do not separate from the random-anchor baseline.

### 3.8 `double_top` / 3.9 `double_bottom` (mirror; double_top described)
- **Formation.** Two confirmed swing-high pivots `p1 < p2` with
  `|high(p1) − high(p2)| ≤ PLAYBOOK_TOPS_MATCH_MBR · MBR`, separation ≥
  `PLAYBOOK_TOPS_MIN_SEPARATION_BARS`, both within `NEAR_EXTREME·MBR` of the session high at
  their times (all ADAPTATION). Valley = min low strictly between them; depth ≥
  `PLAYBOOK_MIN_STRUCTURE_DEPTH_MBR · MBR`.
- **Trigger.** First bar `t` with `low < valley_low`, `p2` pivot-confirmed strictly before
  `t` (fail-closed if price collapses through the valley inside `p2`'s confirmation window).
  `T = valley_low`, short. **Never triggered at the second top itself** — BOOK: short the
  valley break, never the retest.
- **Invalidation.** `S = max(high(p1), high(p2))`; `S + 0.30·(S − T)` (BOOK: above the top).
  Nominal risk is the full pattern height — disclosed as `nominal_risk_mbr`, never shrunk.
- **Caps.** 1 per detector per symbol-session (2026-08-11, R-3.2(a) — rewritten to the shipped
  reading; doc text only, zero change to `_find_double_extreme`/`desk_playbook_detect.py`): every
  confirmed-pivot pair `(p1, p2)` is searched in chronological order, and the FIRST pair whose full
  formation validates AND triggers wins — never the earliest valley break scanned in isolation from
  which pair produced it. A triple top cannot re-fire the same valley once its own pair has already
  triggered.
- **Disclosures.** `tops_gap_mbr`, `tops_separation_bars`, `valley_depth_mbr`,
  `second_top_rvol_vs_first` (median RVOL of p2±1 / p1±1 — P5's drying retest, disclosed not
  gated), `attempt_count` (≥ 3 attempts before the valley break is the book's
  third-attempt-succeeds warning, as data). Principles: P5; the attempt rule.
- **Edge cases.** `p2` exceeding `p1` by more than `TOPS_MATCH` ⇒ not a double top (possibly
  a JBE base — independent detectors).

---

## 4. Shared degenerate/edge policy

- **Formation open at session end** ⇒ nothing emitted. Signals only; no "armed" rows in v1.
- **Halted/missing bars**: a timestamp discontinuity > 5 minutes inside a formation window
  voids that formation (`halted_formation` diagnostic, ADAPTATION). Missing baseline slots
  fall out of the medians under the `MIN_BASELINE_SESSIONS` floor.
- **Late triggers** are never suppressed — the rail's truncation honesty (`truncated`,
  `effective_minutes`) covers short runways; `bars_to_close` disclosed.
- **Overlapping setups on the same bars** are allowed — independent hypotheses;
  `concurrent_signals` cross-lists them so analysis can de-duplicate downstream.
- **Thin data** (MBR = 0, null RVOL baseline, < 10 baseline sessions, no 5m bars) ⇒ the
  symbol-session is silent with a disclosed absence, never a guess.

## 5. Expected frequency (~101 members × 78 bars/session; validated on real data by the
back-scan — validation may DEMOTE a detector in a named revision, never tune constants)

| Detector | Est. signals/day (universe) | Note |
|---|---|---|
| `open_high_break` / `open_low_break` | 10–25 | Most frequent; simplest lookahead story — build first |
| `jbe` / `dbi` | 5–15 | The workhorse |
| `range_trade` | 5–20 | Provisional tier (vaguest book rule) |
| `double_top` / `double_bottom` | 5–15 | Pivot-confirmation delay drops fast collapses (fail-closed, honest) |
| `capitulation` | 0–3 | Rare on calm S&P100 5m; clusters on news days — low n expected, disclosed |
| `euphoria` (marker) | 0–3 | Marker only, never measured |
| `cup_handle` | 0–2 | Rarest; exercises every primitive |

---

## 6. Band context (v2 — the bracket frame; read-side lens, never part of a record or its signature)

> **Supersession.** §6 v2 (`playbook-band-context-v2`) replaces the v1 nearest-band lens shipped
> 2026-08-12, which reported the nearest band in ANY direction plus an `aligned`/`opposed` label.
> That frame could call a trade with no structure within 300 bps "aligned" with a wall it had no
> relationship to, and never named which band it meant. v1's full text remains in git history; the
> algorithm-version constant is the version pointer. No recorded byte, no `playbook_input_signature`,
> and no detector changed in either direction.

Frames every ALREADY-RECORDED signal (and every baseline anchor drawn beside one) against the desk's
own tradable band map (`tradability.compute_tradability`, frozen) at that event's own session basis,
at **serve time only**. Nothing here re-detects, re-measures, or writes back.

Three separations make that safe, and all three are guard-tested:

1. **`compute_playbook` still makes zero `compute_tradability`/`compute_levels` calls.** The lens is
   a different module the walk never reaches (TC-7 stays green unchanged; an import-direction guard
   is its structural companion).
2. **These constants are deliberately NOT in `playbook_parameters()`** — adding them would move
   `playbook_input_signature` and orphan the recorded corpus from its own evidence pool.
3. **Serving never computes.** Every read path is lookup-only against the durable tradability cache;
   `python -m app.research.desk_playbook_context --warm` is the explicit operator act.

**Cache invalidation is basis-bounded (v3).** A context row is keyed on the recordings that can
actually reach its own basis: `_resolve_basis` picks a prior daily bar whose session date is
strictly before the basis day, and `_PriorSessionBarView` then bounds every timeframe to that bar,
so a recording whose coverage STARTS at or after the basis day contributes nothing to the map and
is excluded from the key. Bars recorded after a setup's own session therefore cannot invalidate
that setup's context, while a backfill of OLDER bars still does, and a recording that does not
disclose its coverage is kept rather than assumed irrelevant. Before v3 the key inherited the
tradability cache's whole-symbol store signature, so every daily top-up re-keyed the entire corpus
and the desk's band columns fell back to "not computed yet" after each refresh — recomputing
identical maps to reach identical answers. The tradability cache's own key is unchanged (it is
shared with `GET /research/tradability` and stays frozen); only what a CONTEXT row is keyed on
narrowed, and a context hit never consults the map at all.

### Pre-registered constants

| Constant | Value | Class | Source |
|---|---|---|---|
| `PLAYBOOK_CONTEXT_NEAR_BAND_BPS` | 70.0 | **ADAPTATION** | One band-width — the tolerance the desk already uses to CLUSTER levels into one wall (`tradability_band_width_bps`), read outward as "the trade is at the wall behind it". Echoed as a module constant, never read from `Config`. |
| `PLAYBOOK_CONTEXT_ROOM_R_EDGES` | (1.0, 2.0) | **ADAPTATION** | The book's own reward-to-risk vocabulary, in multiples of the trade's OWN recorded invalidation distance — not values fitted to any outcome. |

Structural (shape, not thresholds): `PLAYBOOK_CONTEXT_ALGORITHM_VERSION = "playbook-band-context-v2"`,
`PLAYBOOK_CONTEXT_DISTANCE_FROM = "entry"`, `PLAYBOOK_CONTEXT_STATUSES`,
`PLAYBOOK_CONTEXT_BACKING_BUCKETS`, `PLAYBOOK_CONTEXT_ROOM_BUCKETS`.

**No sweep exists here.** The two tunables are the rows above; changing either is a named revision
that re-keys every cached context (the algorithm version moves with it) and never rewrites a record.

### The frame — three slots, one pass

Read from the signal's own recorded **`entry`** (an anchor's `entry_price`) — the price every forward
measurement starts from, and the one field signals and anchors both carry, so the lens is identical
on both sides of the comparison. The partition is total, exhaustive, and exclusive:

| Slot | Rule | Distance |
|---|---|---|
| `containing_band` | `price_low <= entry <= price_high`, **both edges inclusive** | — (backing is 0.0) |
| `wall_below` | `price_high < entry`, strictly | to its **top** edge, bps |
| `wall_above` | `price_low > entry`, strictly | to its **bottom** edge, bps |

An entry sitting exactly on an edge is **inside** the band, never a wall a hair's breadth away: the
edge is a real level, and calling it "0.1 bps below" would invent a gap the map does not have.

Both sides and all classes participate — a `class: null` band is still a band; class is a quality
projection inherited from the zone engine, never a test of whether structure exists. The side LABEL
is disclosed on every slot but **never gates one**: side is assigned by splitting levels around the
prior session's close, a daily-basis fact that says where a band came from rather than what price is
doing to it intraday.

Tie-breaks (unreachable on a real map — same-side bands are disjoint and the two sides' pools are
split around prior close — but pinned so the answer can never depend on dict order): containing →
`(class rank desc, quality_score desc, price_low asc)`; nearest wall → `(distance asc, class rank
desc, quality_score desc, price_low asc)`.

### Side-relative readings

| Reading | Long | Short |
|---|---|---|
| `backing_bps` (the wall BEHIND) | 0.0 if containing, else `wall_below` distance | 0.0 if containing, else `wall_above` distance |
| `headroom_bps` (the wall AHEAD) | `wall_above` distance | `wall_below` distance |

`risk_bps` = `|entry − invalidation_price| / entry × 10_000`, read off the two fields
`compute_playbook` already recorded — never a stop this lens invents. `risk_source` is `own` for a
signal. An anchor records no invalidation of its own and **borrows the paired signal's** (already
attributed and close-price-verified, below), disclosed as `risk_source: "paired_signal"`, so both
halves of the comparison are measured in the same R units.

`room_r` = `headroom_bps / risk_bps`; null when either is null or `risk_bps == 0`. Room is expressed
in R rather than raw bps deliberately: 100 bps of headroom means one thing to a setup risking 30 bps
and quite another to one risking 100.

### The two axes, and the states that are not on them

| Backing axis | Meaning |
|---|---|
| `at_wall` | `backing_bps <= 70.0` (**inclusive**) |
| `off_wall` | `> 70.0` |
| `no_wall_behind` | nothing behind the trade on this map |

| Room axis | Meaning |
|---|---|
| `room_lt_1r` | `room_r < 1.0` |
| `room_1r_2r` | `1.0 <= room_r < 2.0` (**exactly 1.0 lands here**) |
| `room_ge_2r` | `room_r >= 2.0` (**exactly 2.0 lands here**) |
| `no_wall_ahead` | nothing ahead on this map — a measured fact, not an absence |

Every located event carries exactly one backing bucket and exactly one room state, so each axis
independently sums to the located total.

Three states are **exclusions** — counted in the payload's own basis the way `n_truncated` and
`n_unmeasured` already are, never distribution cells:

| State | Meaning |
|---|---|
| `not_computed` | the map for this (symbol, basis session) has not been computed yet |
| `no_band_context` | a map WAS resolved and puts no band anywhere around the price — or the event cannot be framed at all (no recorded price/instant/side, or an anchor that could not be attributed) |
| `room_unmeasured` | headroom measured, but no invalidation distance is derivable to divide by |

`no_band_context` and `not_computed` are never conflated: the first is a measured absence of
structure, the second an absence of work. Conflating them would let an un-warmed cache masquerade as
evidence about where setups fire.

### Baseline-anchor attribution — positional, then verified

A recorded anchor carries no symbol of its own. `compute_playbook` appends exactly one anchor per
in-cap signal, in walk order, into that signal's own pool, so `baseline_anchors[pool][i]` belongs to
the i-th in-cap signal of that pool. The lens attributes positionally and then **checks the anchor's
own recorded `close_price` against that signal's `forward.close_price`** — both were measured on the
same symbol's same session series, so they must agree. Any pool whose counts or close prices
disagree attributes **every** one of its anchors `None` (a partial attribution is the one shape that
could pair an anchor with the wrong symbol's wall) and is counted as `n_anchors_unattributable`.
Verified across the whole recorded corpus at authoring time: 234 pools, 1,790 anchors, zero
disagreements.

### `n_positive` and `positive_share` (evidence cells)

`n_positive` = the count of pooled **untruncated** side-relative returns **strictly greater than
zero**, over the same value list the cell's own median and mean come from — so "positive: k of n" and
"median of n" always describe one pool. `positive_share` = `n_positive / n`, served so no surface
divides two served numbers of its own. Both are the five directional measures only (`1m`, `5m`, `1h`,
`4h`, `to_close`) and **null** on the ten `mdd_*` measures, which are clamped ≤ 0 by construction so
"greater than zero" is not a fact they can carry. A recorded `0.0` is a real measured "went nowhere"
and is not counted in either direction.

They are **counts of recorded outcomes**, not probabilities, expectancies, or claims about any
future signal.

### The evidence split

The full cross product setups × sides × **backing(3) × room(4)** × the **five directional measures**
= 1,080 cells, every one present even at `n: 0`, `below_min_n` tagging a thin cell and never
filtering it. The joint grid is the point: "backed by structure" and "with room to travel" are two
different questions, and a trade is taken on both at once. Drawdown measures stay in the unsplit
table (splitting a clamped-≤0 quantity by location multiplies rows without adding a reading).
Baseline anchors are split by the SAME lens at their own instants, so each cohort is compared
against a location-matched null.

---

## 7. Cohorts of the band context (read-side, per record)

The desk's Playbook section carries two composed display filters. Narrowing a row list is trivial;
narrowing the per-setup **summary** is not, because those are pooled means and a browser may not
re-pool a served aggregate. So the pooling for a narrowed cohort happens read-side, at serve time
(`desk_playbook_cohort.py`), through the measurement rail's own helpers.

**No new threshold exists here.** The cohorts compose buckets §6 already registered. This section
pre-registers a *vocabulary* — which compositions the product offers — not a tunable.
`PLAYBOOK_COHORT_ALGORITHM_VERSION` is a shape pointer for the same reason.

### The two axes

| Axis | Values |
|---|---|
| backing | `all` · `at_wall` · `at_wall_room_ge_1r` |
| inside | `all` · `inside` · `not_inside` |

Composed as `"<backing>:<inside>"` → **9 declared cohorts**, declared order, with
`all:all` the **unfiltered** cohort.

| Membership | Rule (reads served §6 fields only) |
|---|---|
| `backing: at_wall` | `status == located` and `backing_bucket == at_wall` |
| `backing: at_wall_room_ge_1r` | the above **and** `room_bucket ∈ {room_1r_2r, room_ge_2r}` |
| `inside: inside` | `status == located` and a containing band |
| `inside: not_inside` | `status == located` and **no** containing band |
| either axis `all` | every eligible signal, including ones with no location |

Two rules that are load-bearing rather than incidental:

1. **`not_inside` requires `status == located`.** §6 serves `containing_band: null` for *every*
   absence too, so a bare "no containing band" test would file every un-warmed signal under "not
   inside a band" — claiming a location for an event that has none. The backend owns this predicate
   so no reader can restate it that way.
2. **`at_wall_room_ge_1r` excludes `no_wall_ahead` and `room_unmeasured`.** Room is a statement
   about a wall ahead; neither state has one. Both are counted, never folded in.

### The pooling rule — in-cap only, paired anchors

A cohort pools the record's **own in-cap prefix** (`rail_max_touches_per_row`, cross-checked against
`signals_beyond_cap`) — exactly the signals `compute_playbook` pooled — and each pooled signal
brings the one seeded anchor drawn beside it (via §6's close-price-verified attribution). Therefore:

- narrowing can only *reduce* how many signals a cell covers, never add one;
- both lines of a pool describe the same signals, so `n_baseline < n` here means an anchor was
  missing or its attribution refused — **not** the pooling cap. (This reads differently from §6's
  evidence table, where a smaller baseline count discloses exactly that cap.)
- the anchor rule is deliberately **paired**, not location-matched as in §6's split: this table's
  baseline line is a per-signal null drawn beside that signal, and location-matching here would let
  the two lines describe disjoint sets.

**The unfiltered cohort never consults the band context at all** — it is the record's own in-cap
prefix pooled by the record's own rule. It is therefore **byte-identical to the record's recorded
`summary`**, verified across the whole corpus (198 of 198 records that carry one; the other 12 are
zero-signal sessions), and stays so even when the context is missing, un-warmed, or refused. An
operator switching a filter back to "all" cannot be shown numbers that differ from the record's.

Signals recorded **beyond** the cap never fed the recorded summary and never feed a cohort of it;
§6's cross-session evidence fold is where every recorded signal is pooled.

### Exclusions — counted, never dropped

`n_excluded_not_computed` · `n_excluded_no_band_context` · `n_excluded_room_unmeasured` ·
`n_excluded_other_location` · `n_excluded_no_context`, per pool, with
`n_eligible == n_signals + Σ excluded` guard-tested. This is what separates *"no signal was at a
wall"* from *"no map has been computed yet"* — both produce an `n: 0` cell and nothing else
distinguishes them.

### Serving

`GET /research/desk/playbook/context?id=<id>&cohorts=true` adds a sibling `cohort_summaries` block.
**Default false**, so the body without the flag is byte-identical to what it has always served —
the `/structure` drill-in reads this route for one caption and must not pay for a block it never
renders. The fold takes no store, resolver, cache or config: it is structurally incapable of
computing a map, reading a bar, or writing a record.
