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
| `PLAYBOOK_NARROW_OR_MAX_MBR` | 3.0 | ADAPTATION — relative form of the ≤25c narrow range |
| `PLAYBOOK_JUMP_MIN_MULT` | 1.5 | BOOK — jump ≥ 1.5–2× base; stated minimum |
| `PLAYBOOK_JUMP_MIN_MOVE_MBR` | 3.0 | ADAPTATION — floor so tiny/tiny can't satisfy the ratio |
| `PLAYBOOK_JUMP_LOOKBACK_BARS` | 6 | ADAPTATION — jump low read from the 30 min before the base |
| `PLAYBOOK_BASE_MIN_BARS` | 3 | ADAPTATION — book gives no consolidation duration |
| `PLAYBOOK_BASE_MAX_BARS` | 12 | ADAPTATION — 60-min cap; beyond it the "base" is the day's range |
| `PLAYBOOK_BASE_MAX_RANGE_MBR` | 2.0 | ADAPTATION — relative form of the ≤25c narrow base |
| `PLAYBOOK_NEAR_EXTREME_MBR` | 1.0 | ADAPTATION — mechanical "near the high/low" |
| `PLAYBOOK_PIVOT_LOOKBACK_BARS` | 3 | ADAPTATION — 5m intraday N for the strict-pivot rule |
| `PLAYBOOK_CUP_MIN_BARS` | 6 | BOOK — cup ≥ 30 min |
| `PLAYBOOK_CUP_OPTIMAL_BARS` | 12 | BOOK — ≥ 1 h optimal (disclosure only) |
| `PLAYBOOK_HANDLE_MAX_RETRACE_FRAC` | 0.5 | BOOK — handle ≤ 50% of cup depth |
| `PLAYBOOK_HANDLE_MAX_DURATION_FRAC` | 0.30 | BOOK — handle ≤ 30% of cup duration (25% desirable → disclosure) |
| `PLAYBOOK_RIM_MATCH_MBR` | 1.0 | ADAPTATION — "cup edges at the day's high" tolerance |
| `PLAYBOOK_MIN_STRUCTURE_DEPTH_MBR` | 2.0 | ADAPTATION — min cup depth AND min valley depth |
| `PLAYBOOK_VERTICAL_WINDOW_BARS` | 3 | ADAPTATION — "near-vertical" window (15 min) |
| `PLAYBOOK_VERTICAL_MOVE_MBR` | 4.0 | ADAPTATION — net move for capitulation/euphoria |
| `PLAYBOOK_VERTICAL_BAR_MBR` | 2.5 | ADAPTATION — single-bar spike (spiky-approach flag) |
| `PLAYBOOK_BOUNCE_MAX_BARS` | 3 | ADAPTATION — reversal confirmation must come fast |
| `PLAYBOOK_RANGE_MIN_WIDTH_MBR` | 4.0 | ADAPTATION — narrower = breakout-only per Ch 13 |
| `PLAYBOOK_RANGE_HOLD_TOL_MBR` | 0.5 | ADAPTATION — "held" tolerance; also the absorption-bar max range |
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
  `open_vs_prior_close_pct` (gap context), `slots_to_break`. Principles: P4 when pre-break
  pullbacks were shallow and dry, else structural-only.
- **Edge cases.** `gap_open` triggers at slot 3 are common on trend opens —
  `gapped_beyond_chase` does the honesty work. No 1m and no 5m OR ⇒ silent symbol-session
  (disclosed absence).

### 3.3 `jbe` / 3.4 `dbi` (exact mirror; JBE described)
- **Formation** (windows ending at `t−1`): base = `consolidation_range` with
  `PLAYBOOK_BASE_MIN_BARS ≤ len ≤ PLAYBOOK_BASE_MAX_BARS` and
  `base_range = U − L ≤ PLAYBOOK_BASE_MAX_RANGE_MBR · MBR` (ADAPTATION). Jump: `jump_low` =
  min low of the `PLAYBOOK_JUMP_LOOKBACK_BARS` bars before base start; `jump = U − jump_low`;
  gates `jump ≥ PLAYBOOK_JUMP_MIN_MULT · base_range` (BOOK ≥1.5×) AND
  `jump ≥ PLAYBOOK_JUMP_MIN_MOVE_MBR · MBR` (ADAPTATION floor). Near the high:
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
- **`euphoria`** — exact mirror UP with the same constants, emitted as a **marker, not a
  signal**: no side, no band, never measured (BOOK: an exit/avoid signal; the authors do not
  short strong stocks on euphoria). It sets `euphoria_recent: true` on any signal triggering
  within `PLAYBOOK_MARKER_DECAY_BARS`; capitulation events symmetrically set
  `capitulation_recent`.

### 3.6 `cup_handle` (long only in v1 — the book presents the long form)
- **Formation.** Left rim = confirmed swing-high pivot within `PLAYBOOK_RIM_MATCH_MBR · MBR`
  of session-high-so-far. Cup bottom = min low after it; depth ≥
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
  instruction; this reading is the pre-registered choice):** a bar `b` touches the low zone;
  the first bar `t` with `b < t ≤ b + PLAYBOOK_BOUNCE_MAX_BARS`, `high > high[t−1]`, and
  `min(low[b..t−1]) ≥ SL − RANGE_HOLD_TOL·MBR`. `T = high[t−1]` — the same reversal-bar
  grammar as the capitulation bounce (one shared mechanism, not a second vague one).
  Resistance-fade mirrored.
- **Invalidation.** Long `S = SL`, `SL − 0.30·(T − SL)` (BOOK: just outside the range
  bounds). Short mirrored.
- **Caps.** 1 per side per symbol-session.
- **Disclosures.** `range_width_mbr`, per-zone touch counts, `crossed_midrange` on the
  approach + whether the prior swing turned at midrange (BOOK midrange rule),
  `absorption_bar_present` — a zone bar with `RVOL ≥ PLAYBOOK_RVOL_ELEVATED` and range ≤
  `RANGE_HOLD_TOL·MBR` (P6 passive accumulation/distribution, mechanical ADAPTATION).
  Principles: P6 when absorption present; P5 at the high side.
- **Edge cases.** A strict break beyond a zone by > `HOLD_TOL` dissolves range-mode (re-arms
  only on a new twice-tested range).
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
- **Caps.** 1 per detector per symbol-session (the first valid valley break; a triple top
  cannot re-fire the same valley).
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
