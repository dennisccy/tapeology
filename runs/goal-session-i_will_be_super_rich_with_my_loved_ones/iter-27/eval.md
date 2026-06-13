# Iteration 27 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** lean

## Summary

Iter-27 was a verification/evidence-capture sweep (app source byte-identical; 848 passed / 1 skipped, exit 0; zero re-pins; coherence COHERENCE-PASS). The operator supplied `ALPACA_API_SECRET`, so the credentialed historical path was genuinely exercised (real AAPL SIP windows, 24,619 trades, unknown-aggressor ≈0.004%) and the browser captures show populated cockpits with real values, true-clock chart axes, resolved buy/sell side columns, the local-zone picker, three distinct honest-failure panels, and an in-progress 1×→10× speed change continuing from position. Six target legs flip `partial → passing`; two remain `partial` (J-23 lacks a visible "couldn't connect" pixel — DOM-text + unit only; J-29 re-watch ~35s vs the <3s cache target). J-15 and J-67's live-IEX pixel leg stay legitimately deferred to the Monday open — scheduled, not stalled — so GOAL_ACHIEVED is not yet warranted.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-11 Replay a real historical session | partial | passing | reports/qa/.../iter-27-evidence/UT-J11-historical-cockpit-populated.png (real SIP AAPL cockpit: bid/ask/spread/last, features, recent trades, chart, observations, event log; feed SIP, window descriptor) |
| J-14 Real-data edge cases handled honestly | partial | passing | UT-J14a-market-closed.png + UT-J14b-unknown-symbol.png + UT-J14c-empty-window.png (three distinct honest states; no fabricated cockpit) |
| J-16 Historical recent-trades show resolved side | partial | passing | UT-J11 recent-trades Buy/Sell column, 0% unknown; dev credentialed buy=14,091/sell=10,527/unknown=1 (≈0.004%); test_aggressor.py 14 pass |
| J-18 Tape-state prediction on real historical chart | partial | passing | UT-J18-chart-with-markers.png (green/red markers at transitions, true-clock axis 08-06-2026 14:30:00…, epoch_anchor via REST, `…/history` single-source); test_history*.py 18 pass |
| J-20 Pick historical window in local time w/ quick-picks | partial | passing | UT-J20-timezone-picker.png (Europe/London label, quick-picks annotated with local equivalents; fetched window matches selected local window) |
| J-22 Slow/hung request → explicit error, no infinite spinner | partial | passing | config: vendor_http 6.0 ≤ vendor_call 8.0 < frontend 12.0, enforced at vendor-call HTTP boundary; test_vendor_timeout.py 5 + test_vendor_responsiveness.py 32 pass (acceptance permits test-proof for the backend bound) |
| J-23 Failed connection/stream → explicit error | partial | partial | "couldn't connect to the tape stream" found via `await_text` (DOM) + test_stream_lifecycle.py 9 pass; BUT no single PNG visibly contains the error panel (UT-J23-couldnt-connect-panel.png shows a populated cockpit; transient text replaced). Visible-element rule unmet. |
| J-27 No usable data → explicit honest state, bounded | partial | passing | UT-J27-stream-closed-state.png (replay exhaustion → status dot Closed; never fabricated live, never stuck connecting); test_stream_lifecycle.py 9 pass |
| J-29 Historical busy window loads within bound | partial | partial | UT-J29-busy-window-loaded.png (loads within 30s — met); UT-J29-rewatch.png (~35s re-watch vs <3s near-instant cache target — unmet). Functional, slower than spec. |
| J-32 Replay-speed change takes effect immediately | partial | passing | UT-J32-before-speed-change.png + UT-J32-after-speed-10x.png (1×→10× on in-progress replay, continued from position, no re-fetch/re-Watch, window descriptor unchanged) |

Required-still-passing journeys (J-01, J-02, J-08, J-10, J-17, J-19, J-31, J-35, J-36, J-37, J-38, J-65, J-66, J-67) remain green — backend suite byte-identical, anchor suites confirmed by name+count in dev handoff and QA. J-67 stays `passing` (live-IEX pixel leg deferred, not failed). J-15 stays `unknown`/gated (Monday). J-68 stays `partial` on its "all J-01–J-37 green" clause (J-23/J-29 partial, J-15 gated).

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| No fabricated data | OK | Unknown-symbol → SymbolNotTradable (no tape); closed-market → honest panel + next open, no synthesized cockpit; quiet window → honest `unclear` at conf 0.20, never a forced directional call; empty window → "no data for that window". No `live` fabricated over an empty tape (verified across UT-J14a/b/c, UT-J27). |
| No trading advice / not profitable | OK | No copy changed; "Descriptive only — not trading advice" present in every capture; tape state read as `Unclear`/`Buyer Control` descriptively. |
| Single source of truth | OK | Chart + cockpit read `…/history`/`…/state`/`…/features`/`…/summary` verbatim; coherence-auditor confirms no second computation/serving path (no app code changed). |
| No persistence of market/tape data | OK | Engine in-memory; only committed test fixtures persist vendor bytes. |
| No new market indicators / scanning / multi-pane | OK | Verification only; zero new capability, endpoint, component, or config key. |

No anti-goal violation introduced. `anti_goal_violations` remains empty.

## Next-Step Recommendation

Schedule the **Monday market-hours live-feed capture pass** at/after the next US open (15-06-2026 14:30 UTC+01:00). It should be a focused, lean iteration that closes the last gating legs:

- **J-67 live leg** — capture the FeedBasisBadge IEX disclosure pixels over a real live feed + the live-declared `iex`-stamped journal row (the only remaining sub-leg; J-67 is otherwise `passing`).
- **J-15** — observe a real live-feed lull flipping status to `stale`, then recovering to `live` (no fabricated trades during the gap).
- **J-23 visible-pixel close-out** — re-capture the backend-killed-mid-watch flow so a single PNG visibly contains the "couldn't connect to the tape stream" panel (use a held/await-stable capture; the logic is already unit-proven). This is the only blocker keeping J-23 at `partial`.
- **J-29 cache target** — either capture a genuinely <3s re-watch (pre-warmed in-memory snapshot) OR, if the ~35s re-watch reflects a real design limit, the decomposer should decide whether the <3s "near-instant" target is a hard acceptance criterion or a soft P2 aspiration; do NOT loop indefinitely on it. If it is soft, J-29 can be scored `passing` on the busy-window-loads-within-bound criterion with the cache gap noted; if hard, scope a minimal caching fix.

Once J-15, J-67's live leg, J-23, and J-29 carry positive evidence, J-68's "all J-01–J-37 green" clause closes and GOAL_ACHIEVED is reachable. No new feature work remains — this is the final verification gate.

## Halt Justification (if halting)

Not halting. Substantial journey progress this iteration (6 target legs flipped `partial → passing`), no regression, no anti-goal violation, COHERENCE-PASS. The two remaining-partial legs (J-23 visible-pixel, J-29 cache) and the gated legs (J-15, J-67 live, behind the Monday open) are tractable and scheduled — not a stall.
