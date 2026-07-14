# goal-tradable_wall-iter-2 Audit Report

**Date:** 2026-07-14
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

J-02's touch-event scanner + case-study registry is genuinely delivered: `setups.py` is the sole
owner, reuses `compute_tradability` verbatim per session (never a second map/levels engine), and
serves its output byte-identically over `GET /research/setups`, `GET /research/setups/{id}`, and a
read-only MCP `setups` proxy. Every one of the 12 DEFINITION OF DONE items was independently
re-verified against source and a live scan (801 events across 12/12 panel symbols; the pinned AAPL
2026-06-22 event `rejected` at [-0.46%, -4.27%]; fingerprint `4d665603569b9dbf`; frozen foundations
diff-empty). One real, honestly-disclosed GAP is carried forward — a boundary inconsistency where
the 13 most-recent-session events (of 801) carry a definitive reaction label computed from a capped
sub-horizon bar while both forward-return fields report `None` — which must be resolved before J-05
renders these events, but does not compromise the J-02 goal and is outside its DoD.

---

## 2. Findings

### Backend Findings

**B1 — GAP (gap): a definitive reaction label is emitted alongside `None` forward returns when the reaction horizon is unreached (boundary, 13/801, live-verified, untested by the committed suite)**

`apps/backend/app/research/setups.py:185` caps the reaction-classification read at the last stored
bar:
```python
reaction_index = min(touch_index + horizons[0], len(all_bars) - 1)
```
When the touch is in the most-recent stored session, `touch_index + horizons[0]` (78 bars ≈ one
full NYSE session) runs past the end of the store, so the reaction is classified from whatever the
*last available* bar is — possibly only a handful of bars after the touch, at an undisclosed,
data-dependent sub-horizon — rather than the config-owned 78-bar horizon the module docstring
(setups.py:52-61) and `config.py` (`setups_forward_return_horizons_bars`) pre-register. Meanwhile
`forward_returns` for that same horizon honestly reports `None` (setups.py:199-207). The result is
an event with, e.g., `reaction: "rejected"` and `forward_returns: [None, None]` — a definitive
classification with no forward-return evidence beside it.

I reproduced this directly against the live populated store: **exactly 13 of 801 events exhibit it,
all dated 2026-07-13** (the boundary session per symbol) — `AAPL/chopped`, `AMZN/rejected`,
`GOOGL/rejected`, `JPM/rejected`, `META/rejected`, `MSFT/rejected`, `TSLA/broke`, etc. The committed
test fixtures (AAPL 5m through 2026-06-30) do **not** reach this boundary — I confirmed 0 such events
on the committed fixture — so the behavior ships **untested**. The reviewer independently flagged
the same issue (`reports/reviews/...-review.md`, MINOR at setups.py:185) and scoped the fix to
"before the case-browser UI (J-05) consumes these events."

Why this is a GAP and not IMPORTANT: it is not lookahead (reads only stored bars), not fabrication
(the reaction reads a real bar), deterministic, self-healing (the label recomputes at the true
horizon once later bars are fetched), affects 1.6% of events at the true recency boundary, and the
forward returns are already honest (`None`). The spec's DoD requires only that forward returns be an
honest `None` past the store's end — which is met — and is silent on capping the reaction horizon.
No UI consumes these events this iteration (J-05 renders them).

**Not fixed** — deliberately. Every available fix is a contract change, not a surgical edit:
suppressing the reaction breaks the always-one-of-three-enums contract the route validates; excluding
the event changes the registry count and drops a real touch; adding a "reaction_horizon_reached"
flag is a new served field the spec did not request. Each risks the byte-identical-determinism
discipline this module prizes, for a spec-silent boundary case with honest forward returns and no
current consumer. Fixing it here would be scope creep. **Recommendation:** resolve it in the J-05
iteration (surface the effective horizon, flag/suppress the reaction, or exclude the event) with a
regression test that locks the boundary — before any UI renders a definitive label with no
supporting returns.

**B2 — GAP (observation, already disclosed): full-panel `GET /research/setups` latency ~4m35s against the populated store**

I reproduced the dev handoff's disclosed latency: a full 12-symbol scan of the live store took
**4m35s** wall-clock (measured), because `compute_setups` re-runs `compute_tradability` once per
(symbol, session) — ~12 symbols × ~38 sessions — with no caching. This is architecturally forced by
the critical anti-goal ("the tradable map is a lens, never a second levels engine… consumes
`compute_levels` output verbatim") and is out of J-02's scope (no DoD performance bullet). The dev
flagged it prominently and honestly rather than shipping it silently, with actionable guidance for
downstream verifiers and for J-04/J-05 (both of which will call this function). Noted here as a
confirmed, carried limitation — not a new defect.

### Frontend Findings

None — Frontend Present: no. J-02 is backend + MCP only; the case-browser UI is J-05. Verified the
diff contains no `/structure`, cockpit, or nav change.

### Test Findings

**T1 — OBSERVATION (observation): the multi-symbol scan fixture is delivered as inline Python literals, not a committed file under `tests/fixtures/`**

The spec's IN SCOPE (line 39) asks to "commit ONE small multi-session, multi-symbol 5m scan fixture
under `apps/backend/tests/fixtures/`." The multi-symbol synthetic fixture (`SYN-SETUPS-A` /
`SYN-SETUPS-B`) is inline in `apps/backend/tests/test_setups.py:68-134`; the committed fixture file
`AAPL_5m_20260615_20260630.json` is single-symbol (the pinned end-to-end case). This is a literal
deviation from the spec wording, but the intent of that DoD line — "the scan path, no-lookahead, and
reaction-classification tests run keyless in CI" — is fully met (I ran the whole suite keyless, no
network), it matches the `test_tradability.py` `_SYN_TRADABILITY` precedent the execution plan
explicitly endorsed (plan.md:78-84), and the reviewer rated it MINOR. Informational; no fix needed
(relocating inline literals to a JSON file changes nothing functional and diverges from the endorsed
codebase precedent).

---

## 3. Domain Assessment

The core domain logic is correct and, in the one place that mattered most, genuinely well-built.

- **The central no-lookahead risk is truly controlled, not merely claimed.** `compute_setups`
  threads `as_of_epoch = session_bars[0].epoch` **per session** (setups.py:269), so each session's
  morning map derives only from prior-session data via `compute_tradability`'s own `_resolve_basis`
  discipline. This is proven by a *positive* test I ran green
  (`test_2026_01_06_session_gains_a_swing_pivot_band_2026_01_05_did_not_have`): a 5m swing-pivot band
  that only confirms once a later session's bars are visible appears in the 2026-01-06 map and is
  correctly absent from the 2026-01-05 map computed one session earlier — the exact bug a
  shared/fixed `as_of` would produce. The consecutive-session truncation test
  (`test_no_lookahead_extending_the_5m_series_forward_never_changes_an_earlier_session_event`) locks
  the DoD's byte-identity clause. Both pass.
- **Single source of truth holds.** `setups.py` calls `compute_tradability` (never `compute_levels`,
  never a pivot/extreme/cluster internal) — enforced by a static-analysis guard test and confirmed by
  my reading. Both routes and the MCP proxy serve `compute_setups` output verbatim; the MCP tool
  proxies the *unfiltered* list byte-identically to `GET /research/setups` with no query string (the
  non-trivial byte-comparison test seeds real fixtures and asserts the pinned event is present).
- **Reaction classification is honest under intraday density.** The `chopped`-despite-a-huge-wick
  regression guard proves classification reads the reaction-horizon CLOSE only — never the touch
  bar's wick extent or its 50,000-volume — so a loud shallow poke is not misclassified as a
  rejection. The live reaction distribution is non-degenerate (306 rejected / 309 broke / 186
  chopped), not a collapsed single label.
- **Determinism is structural.** Event ids are a sha256 digest of identity fields (no `uuid4`, no
  wall-clock); the served list has an explicit total order. Repeat-scan determinism is tested on both
  synthetic and real fixtures.
- **Honest empty states are distinct and real** — four separate tests cover no-basis session, no-5m
  series, no-1d series, and empty store, each contributing zero events rather than a fabricated one.
- **Descriptive-only discipline** is respected: `rejected`/`broke`/`chopped` are measured-history
  labels, forward returns are measured fractions (not "expected return" predictions), and
  `tape_timeline` is present-but-empty pending J-03. No imperative/predictive copy.
- **Frozen foundations are byte-identical** — the diff touches only `config.py`, `mcp/__init__.py`,
  `routes.py`, `test_mcp_server.py` (plus new setups files/fixtures/scripts); `levels.py`,
  `tradability.py`, `backtests.py`, the tape engine, `BarStore`, and Alpaca paths are absent. I re-ran
  33 observer/profile-equivalence + dense-replay guards and 20 tradability tests — all green.
  `config_fingerprint` independently computed to `4d665603569b9dbf`; all five new `setups_*` fields
  are in the exclusion set with a stability + real-threshold counter-test.

The one blemish (B1) is confined to the true recency boundary and is honest about the *returns*; the
inconsistency is in labeling those boundary touches with a definitive reaction. It is the right
thing to carry into J-05, not a J-02 blocker.

---

## 4. Fixes Applied During This Audit

None. No CRITICAL or IMPORTANT finding was identified; the two GAPs and one OBSERVATION are documented
as carried limitations. Fixing B1 within J-02 would be a contract change (scope creep) for a
spec-silent boundary case with no current consumer, and the reviewer independently scoped it to J-05.

| # | Severity | File | Change |
|---|----------|------|--------|
| — | — | — | No fixes applied. |

---

## 5. Recommended Next Step

**Proceed.** J-02 fully meets its DEFINITION OF DONE and its goal is achieved; the required-still-
passing journeys J-01 and J-07 remain green. Two items to carry forward:

1. **Before J-05 renders these events (blocking for J-05, not J-02):** resolve B1 — decide the honest
   contract for a boundary touch whose reaction horizon is unreached (surface the effective horizon,
   flag/suppress the reaction, or exclude the event) and add a regression test that locks it, so the
   case browser never shows a definitive `rejected`/`broke`/`chopped` label beside empty
   forward-return fields.
2. **For J-04/J-05 (performance):** the ~4m35s full-panel scan (B2) will be on the hot path for the
   edge report and the case browser; plan the persisted/cached scan result the dev handoff already
   proposes.

The dev handoff's suggested next phase (J-03, credentialed Alpaca event-window tape recording onto
the now-real 801-event registry) is the correct dependency-order continuation.
