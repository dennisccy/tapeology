# goal-i_will_be_super_rich_with_my_loved_ones-iter-29 Audit Report

**Date:** 2026-06-16
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

The two market-hours-gated legs (J-15 `unknown → passing`, J-67 live IEX pixel leg) are genuinely achieved on a real Alpaca IEX socket and verified in actual code, REST evidence, the gated credentialed integration run, and pixels — not just summaries. J-68 byte-identity holds (re-confirmed live three times: `git status --porcelain apps/` and `git diff --stat HEAD -- apps/` both empty). One pre-existing live-mode gap surfaced by a spot-check (UT-08: an unknown symbol in Live mode surfaces an honest empty `stale` watch rather than an explicit "not a tradable symbol" message) is documented as a GAP for the goal-evaluator's J-14 scoping decision; it is correctly NOT fixed here because doing so would violate this iteration's prime byte-identity directive and is out of scope.

---

## 2. Findings

### Backend Findings

**B1 — OBSERVATION (verified): Stale watchdog logic is real and correct in code**
`apps/backend/app/watch_manager.py:548-657` (`_feed_live`). Verified the stale seam is genuinely implemented, not merely claimed: the feeder `await asyncio.wait_for(queue.get(), stale_gap)` (line 622) flips `engine.set_stream_status("stale")` on a >`stale_gap_seconds` timeout (line 628) and, on the next real event, flips back to `live` (line 640-641, "owns the stale->live recovery flip"). `config.stale_gap_seconds = 10.0` confirmed at `apps/backend/app/config.py:338`. No application code was changed to produce the live evidence. This is the binding backend logic behind J-15 and it is correct.

**B2 — OBSERVATION (verified): J-67 feed-basis stamp flows from a single canonical source**
The live IBM snapshot (`reports/qa/…-iter-29-evidence/ibm-live-summary.json`) carries `data_feed: "iex"`, the journal row (`journal-iex-row.json`) is stamped `data_feed: "iex"` / `bound_source: "live IBM"`, and the disclosure (`taxonomy-feed-basis.json`) is served verbatim from `GET /research/taxonomy`'s `feed_basis` block ("live verdicts read the single-venue IEX feed; historical replay and studies use SIP — spreads and prints differ"). No SIP/IEX pooling on any single row. The real IBM top-of-book reads a wide spread (bid 260.68 / ask 284.24) and honestly classifies `unclear` — correct, not fabricated.

**B3 — GAP (not fixed — out of scope, would break byte-identity): Live-mode unknown symbol surfaces honest `stale`, not an explicit "not a tradable symbol" message**
`apps/backend/app/main.py:259-303` (`_watch_live`). The live watch endpoint gates only on credentials (503) and an authoritative closed clock (409); it deliberately does NOT pre-validate symbol tradability before opening the socket (docstring lines 262-272). An untradable symbol therefore opens a live IEX socket that delivers no records, and the stale watchdog honestly flips to `stale` with an empty quote (all `—`) and `Unclear` + "Warming up" — confirmed in pixels (`UT-08-unknown-symbol.png`: amber `Stale` dot, empty dashes, no fabricated values). The "not a tradable symbol" 404 (`main.py:380-381`, `SymbolNotTradable`) lives only on the **historical** path. This behavior is pre-existing since **iter-4** (`git log -S` → commit `495c70e`, 2026-06-04) and was NOT introduced by iter-29 (which changed zero source). The browser QA verdict is FAIL on this single P1 (UT-08), and the spec's error-case list (spec line 88) asserted as a carry that "An unknown symbol in Live mode still returns 'not a tradable symbol'." **Disposition:** documented GAP, NOT fixed. Rationale: (a) the no-fabricated-data anti-goal — the critical one — IS respected (honest empty `stale`, no invented tape/quote); (b) a fix would mutate `apps/backend/` and violate J-68 byte-identity, the explicit prime directive of this verification-only iteration ("a non-empty application diff is a DEFECT unless it is a justified live-feed bug fix" — plan line 165); (c) this is not a live-feed bug, it is a long-standing live-mode validation-design choice; (d) the spec escalation clause (line 99) and the ux-regression reviewer both route the J-14 live-leg scoping to the goal-evaluator. Fixing it here would itself be the defect.

### Frontend Findings

**F1 — OBSERVATION (verified): live status indicator and FeedBasisBadge render correctly on a real feed**
`UT-03-live-status.png` shows the green `Live` dot over a live IBM watch; `UT-08-unknown-symbol.png` shows the amber `Stale` dot — visibly distinct in the same status area, matching the DESIGN SYSTEM (`bg-emerald-400` live vs `bg-amber-400` stale, confirmed in `TopBar.tsx` per UT-07). The `FeedBasisBadge` "feed IEX (live)" + the verbatim IEX-vs-SIP disclosure render inline in the cockpit viewport (`UT-04`, `UT-11`: `isInViewport: true`, `textTruncated: false`). No frontend source changed (`git diff --stat HEAD -- apps/frontend/` empty).

### Test Findings

**T1 — OBSERVATION (verified): gated live-integration test is correctly triple-gated and asserts the binding contract**
`apps/backend/tests/test_live_integration.py:36-64`. Gated on `TAPEOLOGY_LIVE_INTEGRATION=1` (line 36), creds present (line 40), and market-open (line 43); asserts `stream_status == "live"`, `event_count > 0`, and `scenario == f"live {symbol}"`. Dev/QA report it ran green against the real socket (1 passed). This is the authoritative non-hermetic pipeline proof required by `.claude/core.md` External Integration Testing — verified present and asserting exact values, not loose outcomes.

**T2 — OBSERVATION (verified): observer-equivalence (J-68 automated clause) and full suite are intact**
`apps/backend/tests/test_observer_equivalence.py` exists (J-68's automated byte-identity clause; reported 7 passed). The full backend suite is reported green (848 passed, 1 skipped = the correctly-skipped gated test), zero re-pins. I did not re-run the 6.5-minute suite (the binding byte-identity question is settled by the live `git diff` being empty), but confirmed the test files exist and the gate mechanism is sound.

**T3 — OBSERVATION (file-naming only): the binding J-15 `stale` still is filed under the wrong name**
The file named `UT-05-stale-state.png` actually shows a green `Live` dot (the F-watch `stale` was confirmed by DOM label reads, not a held still). The still that VISIBLY contains the transient amber `stale` indicator is `UT-08-unknown-symbol.png`. So J-15's binding pixel requirement ("a still that visibly contains the `stale` indicator, distinct from `live`") IS satisfied by the evidence directory — it is merely mislabeled. No fix needed; the evidence exists. (This is the exact transient-capture-discipline risk the spec flagged from iter-27/22/14; here the evidence was captured, just filed under the wrong test id.)

**T4 — OBSERVATION (minor, no action): two byte-identical idle frames**
`md5sum` over the evidence dir shows `UT-01-initial.png` and `UT-01-result.png` are byte-identical (`a15886…`). These are smoke/idle frames, not the load-bearing J-15/J-67 evidence, so the duplication is harmless. The load-bearing stills (`UT-03` live, `UT-08` stale, `UT-04` badge, `UT-06` journal row) are all distinct hashes.

---

## 3. Domain Assessment

The core domain logic is correct and honest. The heart of J-15 — that the engine fabricates NO trade during a real feed lull — is proven both in code (`_feed_live` sets `stale` and lets the next REAL event recover; nothing synthesizes catch-up) and in the captured REST sequence (snapshot `timestamp` and `recent_trades` count frozen across every `stale` span, e.g. `recent_trades=9` held through a 15s stale span and still 9 on recovery). The single-source-of-truth discipline holds: `stream_status` (row 6) is read identically by REST, WS, and the UI; the `data_feed` stamp (row 29) flows from the one canonical snapshot to the badge and to journal persistence with no recomputation and no SIP/IEX pooling. The honest-uncertainty principle is upheld even in the degraded case: an untradable live symbol produces `stale` + empty dashes + `Unclear`, never a fabricated verdict (B3). The only domain-shaped open question is purely a *messaging* one — whether live mode should additionally tell the user *why* there is no data ("not a tradable symbol") rather than only showing honest absence — and that is a deliberate scoping decision the spec defers to the evaluator, not a correctness defect.

---

## 4. Fixes Applied During This Audit

| # | Severity | File | Change |
|---|----------|------|--------|
| — | — | — | None. This is a verification-only iteration with a binding J-68 byte-identity directive; no CRITICAL or IMPORTANT defect was found, and the one GAP (B3) is explicitly out of scope and would break byte-identity if "fixed" here. Applying no source change is the correct auditor action. |

---

## 5. Recommended Next Step

Accept this iteration. J-15 flips `unknown → passing` (real `live→stale→live` on a credentialed live socket, no fabrication, backed by the gated integration run and a visible amber-`stale` still), J-67's live leg is captured (IEX badge + verbatim disclosure + `data_feed=iex` journal row, no pooling), and J-68 byte-identity holds. With these two legs landed, every Must-have journey is `passing`/`already_passing` and J-68's "all J-01–J-37 green" sentinel clause closes — the goal-evaluator should now consider **GOAL_ACHIEVED**.

Before declaring done, the goal-evaluator should make one explicit scoping ruling on the single open GAP (B3): decide whether J-14's acceptance criteria require the **Live-mode UI** to surface an explicit "not a tradable symbol" message, or whether the existing REST/Historical "not a tradable symbol" 404 plus the honest live `stale`/empty-quote behavior (which respects the no-fabricated-data anti-goal) is sufficient. If the Live-mode explicit message is deemed in scope, it is a small, well-bounded follow-up iteration (surface the existing backend rejection in the cockpit) — NOT an iter-29 fix, since iter-29's mandate was byte-identity. No other remaining work is anticipated; the J-29 `<3s` re-watch cache fast-path remains correctly soft/P2 and out of scope.
