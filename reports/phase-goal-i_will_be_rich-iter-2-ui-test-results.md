# Phase goal-i_will_be_rich-iter-2 — UI Test Results

**Phase:** goal-i_will_be_rich-iter-2
**Date:** 2026-06-02
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** FAIL

<!-- FAIL: P1 test UT-06 fails its explicit expected result (positive buy_price_impact is NOT rendered
     in the required emerald color). One real, reproduced, root-caused CSS rendering defect surfaced by
     this first-ever browser run. ALL DATA/BEHAVIOR assertions pass — see "Verdict rationale" below. -->

**Overall:** 10/12 tests passed (0 skipped, 2 failed)

**Precondition gate (UT-01):** PASS — `/` served **HTTP 200** (not the iter-1 HTTP 500), cockpit shell rendered. The browser run is **VALID**; no SKIP is recorded as a pass.

---

## Verdict rationale (read first)

This is a **verification-closure** iteration whose purpose is to browser-prove the never-QA'd `SIM-BUYER` cockpit (iter-1 SKIPPED all 18 UI tests on a cached HTTP 500). The run succeeded at that purpose: it executed end-to-end **and surfaced a real defect**.

- **The data / behavior layer fully passes.** Every journey's *data* requirement is met and screenshot-backed:
  - **J-01** — all six panels populate with live numeric values; values updated over WebSocket **without a page reload** (Bid 115.18 → 118.43 → 122.60; Last 115.19 → 122.62; impacts/ratios shifting — `href` constant, no `navigate`/reload between observations).
  - **J-02** — tape state settles on **buyer_control** at **confidence 0.888** (≥ threshold); `aggressive_buy_ratio` 0.955 (high); `buy_price_impact` **+0.390 (positive)** — the price-impact guard is intact; Event Log shows **"Tape state changed to buyer_control"**.
  - **J-08** — UI tape_state / confidence / every compared feature **match `GET /tape/SIM-BUYER/state` and `/features` exactly** (single source of truth, no divergence).
  - Both backend cleanups are visibly behavior-preserving (spread = ask − bid; `average_spread` ≈ 0.020 stable).

- **One real UI defect was found** (the reason for FAIL): the Tailwind classes **`.text-emerald-400` and `.bg-emerald-500` are absent from the served CSS bundle**, because they are referenced *only* as dynamically-returned strings in `lib/format.ts` (never as a static `className` in a scanned component), so Tailwind's content scanner never emits them. Consequence: the product's **"green = buy-side / positive impact / buyer_control"** visual language renders as neutral **slate-200** (text) / **transparent** (the confidence-bar fill). This hits the headline **"Buyer Control"** state label, the confidence-bar fill, every **BUY** trade row, and the positive **Buy price impact** / **Net aggressive volume** readouts. The rose/sell/negative half renders correctly. **All underlying data is correct** — only the emerald color layer is broken.

This defect violates the **explicit P1 color assertion in UT-06** ("rendered in the positive/emerald color") and degrades UT-05 (accent color + bar fill) and UT-11 (emerald semantics). Per the UI test plan ("P1 tests UT-01 … UT-08 must all pass") and this iteration's stated purpose ("if browser QA surfaces a real defect — fix the minimal root cause and let the full review/audit loop cover it"), the correct verdict is **FAIL**, not a clean pass. The fix is small, isolated to Tailwind class generation (no data/behavior change), and preempts the same latent breakage for `text-amber-400` / `bg-*-500` that would otherwise bite J-04/J-05 (absorption) and J-06 (unclear). Full root-cause + measurements: `reports/qa/goal-i_will_be_rich-iter-2-evidence/DEFECT-emerald-css-color.txt`.

> **Note (not a defect to fix this iteration):** REST `/state` reports `stream_status: "closed"` (the deterministic SIM-BUYER scenario completed at timestamp 2499.5) while the top-bar dot still reads **"live"** (driven by the client `connStatus`). This is the **explicitly deferred** coherence advisory recorded in the phase spec OUT OF SCOPE (consolidate the dot onto the engine's `snapshot.stream_status` in the J-04/J-05 or J-09 iteration). UT-08 does not compare `stream_status`. Flagged here so it is not lost.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | Shell loads (no HTTP 500) — precondition gate | smoke | P1 | HTTP 200; cockpit shell, title, ticker input, Watch button, idle state, footer disclaimer | HTTP 200; "Tapeology", input placeholder "Ticker e.g. SIM-BUYER", green Watch, "No ticker watched" + "Try: SIM-BUYER", footer present; no error overlay/console errors | **PASS** | `reports/qa/goal-i_will_be_rich-iter-2-evidence/UT-01-result.png` |
| UT-02 | Watch SIM-BUYER → cockpit populates | happy-path | P1 | "Watching SIM-BUYER"; all 6 panels render live values (Quote not "—", Recent Trades rows, Features numeric, Event Log non-empty) | Top bar "Watching **SIM-BUYER**"; Quote Bid 115.18/Ask 115.20/Spread 0.02/Last 115.19; Recent Trades table with rows; Features all numeric; Event Log non-empty; status dot emerald "Live"; all 6 panels, no crash | **PASS** | `reports/qa/goal-i_will_be_rich-iter-2-evidence/UT-02-result.png` |
| UT-03 | Live WS updates without reload | happy-path | P1 | At least one value changes on its own with no page reload; stream stays connected | Bid 115.18→118.43→122.60, Last 115.19→122.62, impacts/ratios shifted across the session with **no reload** (`href` constant, status "live"); froze on scenario end (`stream_status: closed`) — no fabricated post-stream updates | **PASS** | `UT-02-result.png` (Last 115.19) vs `UT-05-result.png` (Last 122.62) |
| UT-04 | Spread = ask − bid after cleanup | validation | P1 | Displayed Spread = Ask − Bid; Average spread small positive (≈0.020), no jump/negative/"—" | Spread 0.02 = 115.20−115.18 (and 122.62−122.60); Average spread 0.020 stable → spread-producer cleanup behavior-preserving | **PASS** | `UT-02-result.png`, `UT-05-result.png` |
| UT-05 | Tape state settles on buyer_control | happy-path | P1 | Panel reads "Buyer Control" **in accent color**; Confidence ≥ ~0.80; bar filled to ~that proportion | Label "Buyer Control" ✓; Confidence **0.888** ✓; bar **width 89%** (correct proportion) ✓. **Caveat:** accent color + bar fill NOT rendered (label computes slate-200; bar fill `bg-emerald-500` computes transparent) — emerald CSS missing; see UT-06 defect | **PASS** *(with color caveat)* | `reports/qa/goal-i_will_be_rich-iter-2-evidence/UT-05-result.png` |
| UT-06 | Feature evidence supports buyer_control | validation | P1 | Aggressive buy ratio high (≈0.90); **Buy price impact positive AND rendered in positive/emerald color** | Aggressive buy ratio 0.955 ✓; Buy price impact +0.390 positive ✓ (guard intact); **BUT rendered slate-200 (rgb 226,232,240), NOT emerald** — `.text-emerald-400` absent from CSS. Explicit color assertion **not met** | **FAIL** | `UT-05-result.png`, `DEFECT-emerald-css-color.txt` |
| UT-07 | Event log records the transition | happy-path | P1 | Log contains "Tape state changed to buyer_control"; monospace, non-empty | Event Log shows exactly **"Tape state changed to buyer_control"** (monospace, non-empty) | **PASS** | `UT-05-result.png` |
| UT-08 | UI matches REST exactly (J-08) | happy-path | P1 | UI tape_state/confidence/features match `/state` + `/features` within rounding; no divergence | Exact match: state buyer_control; confidence UI 0.888 = REST 0.8882…; aggr_buy_ratio 0.955=0.9545; net_aggr_vol 14000; buy_impact 0.390; sell_impact −0.120; avg_spread 0.020 (UI 30s window = REST primary_window) | **PASS** | `reports/qa/goal-i_will_be_rich-iter-2-evidence/UT-08-result.png`, `UT-08-rest-json.txt` |
| UT-09 | Idle state renders pre-watch | regression | P2 | "No ticker watched" + ▦ glyph + body text + "Try: SIM-BUYER"; no panels, no error | Idle state renders on fresh load and after bad-ticker error; ▦ glyph, body text, "Try: SIM-BUYER"; no panels; no error | **PASS** | `reports/qa/goal-i_will_be_rich-iter-2-evidence/UT-09-result.png` |
| UT-10 | Bad ticker → watch-error, no crash | error | P2 | Rose error under top bar; no crash/blank; no half-populated cockpit; can retry | Rose error "'NOPE_UNKNOWN' is not a known simulated ticker" (text-rose-400); 0 panels; idle state preserved; input/Watch still usable | **PASS** | `reports/qa/goal-i_will_be_rich-iter-2-evidence/UT-10-result.png` |
| UT-11 | Colors, monospace, disclaimer intact | ux | P2 | Dot emerald "Live"; **buy-side/positive impacts emerald**, sell-side/negative rose; monospace; disclaimer present | Dot emerald "Live" ✓; numerics monospaced ✓; disclaimer present ✓; sell-side/negative **rose** ✓; **BUT buy-side trades + positive impacts render slate-200, NOT emerald** — `.text-emerald-400` absent | **FAIL** *(emerald half)* | `UT-05-result.png`, `DEFECT-emerald-css-color.txt` |
| UT-12 | No new route/panel/control (scope guard) | regression | P2 | Exactly iter-1 surfaces: 6 panels, 1 watch form, 1 status dot, 1 footer; no new route/panel/control | Exactly 6 panels (Tape State, Quote, Features, Recent Trades, Observations, Event Log); 1 form; 1 input; **0 nav links/routes**; buttons = [Watch, 10s, 30s, 60s, 180s, 300s] (iter-1 window selectors); 1 dot; 1 footer disclaimer | **PASS** | `UT-05-result.png` |

---

## Passed Tests

### UT-01 — Cockpit shell loads without the iter-1 HTTP 500 (precondition gate)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_will_be_rich-iter-2-evidence/UT-01-result.png`
- `/` served **HTTP 200** (backend `:8650` + frontend `:3650` both 200). Top bar: bold **"Tapeology"**, ticker input placeholder **"Ticker e.g. SIM-BUYER"**, green **"Watch"** button, slate **"Idle"** dot. Center: **"No ticker watched"** + ▦ glyph + **"Try: SIM-BUYER"**. Footer disclaimer present. No Next.js error overlay, no uncaught console errors. **The browser run is VALID.**

### UT-02 — Watch SIM-BUYER and the cockpit populates live (J-01)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_will_be_rich-iter-2-evidence/UT-02-result.png`
- Typed `SIM-BUYER`, clicked Watch. Top bar shows **"Watching SIM-BUYER"** (monospace) + `scenario: buyer_control` chip. All six panels rendered with live values: Quote (Bid 115.18 / Ask 115.20 / Spread 0.02 / Last 115.19 — monospace, not "—"), Recent Trades (Price/Size/Side rows), Features (all numeric), Observations (3 descriptors), Event Log (non-empty). Status dot emerald **"Live"**. No crash, no blank panel.

### UT-03 — Values update over WebSocket without a page reload (J-01)
**Verdict:** PASS
**Evidence:** `UT-02-result.png` (Last 115.19, Bid 115.18) vs `UT-05-result.png` (Last 122.62, Bid 122.60) — same browser session, **no reload between them**.
- Across repeated DOM reads with no `navigate`/reload (`location.href` constant at `http://localhost:3650/`), live values advanced on their own: **Bid 115.18 → 118.43 → 122.60**, **Last 115.19 → 122.62**, Buy price impact 0.430 → 0.390, Aggressive buy ratio 0.932 → 0.960 → 0.955, Sell price impact −0.140 → −0.120. Stream-status stayed "live" during updates. When the deterministic scenario completed (`stream_status: closed`), values correctly **froze** at the final snapshot — no fabricated post-stream updates (anti-goal respected).

### UT-04 — Spread equals ask − bid after the spread-producer cleanup (J-01)
**Verdict:** PASS
**Evidence:** `UT-02-result.png`, `UT-05-result.png`
- Spread **0.02** = Ask − Bid at both observed quotes (115.20 − 115.18; 122.62 − 122.60). **Average spread 0.020** displayed and stable — consistent with the live spread, confirming the `tape_engine.py:54` single-producer cleanup is behavior-preserving (no jump, negative, or "—").

### UT-05 — Tape state settles on buyer_control with confidence bar (J-02)
**Verdict:** PASS *(with documented color caveat — see UT-06)*
**Evidence:** `reports/qa/goal-i_will_be_rich-iter-2-evidence/UT-05-result.png`
- Tape State panel reads **"Buyer Control"**; **Confidence 0.888** (≥ ~0.80 threshold); confidence-bar element sized to **89% width** (correct proportion, `inline width: "89%"`, not empty/pinned at 0).
- **Caveat (same root cause as UT-06):** the label's intended emerald **accent color is not applied** (computes slate-200), and the bar's **fill color is transparent** (`bg-emerald-500` not generated) — so the bar is correctly *sized* but not visibly *filled* in emerald. State + confidence (the J-02 data substance) are fully correct.

### UT-07 — Event log records the buyer_control transition (J-02)
**Verdict:** PASS
**Evidence:** `UT-05-result.png`
- Event Log contains the exact line **"Tape state changed to buyer_control"** (monospace), list non-empty.

### UT-08 — UI matches REST exactly for SIM-BUYER (J-08, single source of truth)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_will_be_rich-iter-2-evidence/UT-08-result.png` (UI), `UT-08-rest-json.txt` (REST JSON)
- Compared at the frozen scenario-end snapshot (both UI and REST stable):

  | Metric | UI | REST (`/state`, `/features` 30s) | Match |
  |---|---|---|---|
  | tape_state | Buyer Control | buyer_control | ✓ |
  | confidence | 0.888 | 0.8882575… | ✓ |
  | aggressive_buy_ratio | 0.955 | 0.95454… | ✓ |
  | aggressive_sell_ratio | 0.045 | 0.04545… | ✓ |
  | net_aggressive_volume | 14000 | 14000.0 | ✓ |
  | buy_price_impact | 0.390 | 0.39000… | ✓ |
  | sell_price_impact | −0.120 | −0.11999… | ✓ |
  | average_spread | 0.020 | 0.0199999… | ✓ |
  | trade_speed | 2.03/s | 2.0333… | ✓ |
  | volume_speed | 513.3/s | 513.333… | ✓ |
  | large_print_count | 8 | 8.0 | ✓ |

  The UI's selected window ("30s") equals REST `primary_window` ("30s"). **No divergence** — one engine value per metric.

### UT-09 — Idle state renders before any ticker is watched (J-01)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_will_be_rich-iter-2-evidence/UT-09-result.png`
- On a fresh load (and again after the bad-ticker error), the center shows **"No ticker watched"** with the ▦ glyph, the body instruction text, and the **"Try: SIM-BUYER"** hint. No panels rendered, no error.

### UT-10 — Bad ticker shows a watch-error, not a crash (J-01)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_will_be_rich-iter-2-evidence/UT-10-result.png`
- Typed `NOPE_UNKNOWN`, clicked Watch. A **rose** message appears under the top bar: **"'NOPE_UNKNOWN' is not a known simulated ticker"** (`text-rose-400`). App did not crash, screen not blank, **0 panels** rendered (no half-populated cockpit), idle state preserved. Input + Watch button remain usable for a retry.

### UT-12 — No new route, panel, or control was introduced (scope guard)
**Verdict:** PASS
**Evidence:** `UT-05-result.png`
- Structural census while watching SIM-BUYER: exactly **6 panels** (Tape State, Quote, Features, Recent Trades, Observations, Event Log), **0 unexpected panels**, **1** watch form, **1** input, **0** nav links/routes, buttons = `[Watch, 10s, 30s, 60s, 180s, 300s]` (the 5 window selectors are iter-1's `FeaturesPanel`), **1** status dot, **1** footer disclaimer. No new page/route/panel/control/displayed value — consistent with this iteration's zero-frontend-code-change scope.

---

## Failed Tests

### UT-06 — Feature evidence supports buyer_control (color assertion)
**Verdict:** FAIL
**Failure:** The positive **Buy price impact** value is **not rendered in the required emerald color**. Its element carries the correct class `text-emerald-400`, but the computed color is **rgb(226,232,240) (slate-200)** because **`.text-emerald-400` does not exist in the served CSS bundle**. The substantive data check passes (Buy price impact = **+0.390**, positive → the price-impact guard was not relaxed; Aggressive buy ratio = 0.955, high), but UT-06's explicit expected result — *"rendered in the positive/emerald color (sign-colored)"* — is not met.
**Evidence:** `reports/qa/goal-i_will_be_rich-iter-2-evidence/UT-05-result.png` (Buy price impact 0.390 in slate vs Sell price impact −0.120 in rose), `DEFECT-emerald-css-color.txt`

**Steps taken:**
1. Watched SIM-BUYER; stream stabilized to buyer_control.
2. Read Aggressive buy ratio (0.955) and Buy price impact (+0.390) in the Features panel.
3. Measured the computed style of the Buy price impact value element via Chrome MCP eval.

**Expected:** Buy price impact positive **and** rendered emerald (sign-colored).
**Actual:** Positive ✓ (+0.390), but computed color slate-200 (rgb 226,232,240) — `.text-emerald-400` absent from CSS. Sell price impact (negative) correctly rose. Control check: `.text-rose-400` and `.text-emerald-300` rules **exist** in the bundle; `.text-emerald-400` rule lookup returned **null**.

---

### UT-11 — Color semantics, monospace, and disclaimer (emerald half)
**Verdict:** FAIL *(partial — emerald/buy-side semantics broken; rose/monospace/disclaimer correct)*
**Failure:** UT-11 requires *"buy-side trades / positive impacts render emerald."* They do not — every BUY trade row and every positive impact readout (Buy price impact, Net aggressive volume) carries `text-emerald-400` but computes to **slate-200**, due to the same missing-CSS-class root cause. The rest of UT-11 passes: stream-status dot is emerald **"Live"**, sell-side/negative render **rose** correctly, numeric readouts are monospaced, and the footer disclaimer **"Descriptive only — not trading advice."** is present with no profit/advice language.
**Evidence:** `reports/qa/goal-i_will_be_rich-iter-2-evidence/UT-05-result.png` (BUY rows slate vs SELL rows rose), `DEFECT-emerald-css-color.txt`

**Steps taken:**
1. Watched SIM-BUYER; inspected Recent Trades side cells and the dot/footer.
2. Measured computed colors of "buy"/"sell" cells, Bid/Ask, and the price-impact rows.

**Expected:** Buy-side/positive emerald; sell-side/negative rose; monospace; disclaimer present.
**Actual:** Sell-side/negative rose ✓; monospace ✓; disclaimer ✓; dot emerald "Live" ✓ — **but buy-side/positive render slate-200, not emerald** (`.text-emerald-400` absent).

---

## Root Cause (for the dev/review loop — not fixed by QA)

**`.text-emerald-400` (and `.bg-emerald-500`) are missing from the generated Tailwind CSS**, so every element relying on them falls back to inherited slate-200 (text) / transparent (background). Confirmed by computed-style measurement and stylesheet probe (`DEFECT-emerald-css-color.txt`).

- **Why these and not their rose/emerald-300 siblings:** `text-emerald-300`/`text-rose-300` are static literals in `components/QuotePanel.tsx:8-9`; `text-rose-400` is a static literal in `components/TopBar.tsx:75` (the error banner) — so Tailwind's content scanner emits all three, and the rose-400 rule also covers the dynamic `format.ts` rose usages. **`text-emerald-400` is referenced *only* as dynamic return values in `lib/format.ts`** (`stateColor` L24, `sideColor` L36, `impactColor` L42) and **never as a static `className`** in any scanned file → Tailwind never generates it. Same dynamic-only pattern affects `bg-emerald-500` (`stateBarColor` L29 — confirmed transparent), and the as-yet-unexercised `text-amber-400` / `bg-rose-500` / `bg-amber-500` (latent breakage for J-04/J-05 absorption and J-06 unclear).
- **User-visible impact:** the headline **"Buyer Control"** state label, the confidence-bar fill, all **BUY** trade rows, and positive **Buy price impact** / **Net aggressive volume** readouts are not green — the cockpit's primary "green = bullish/buy-control" signal is absent. **All data is correct** (values, signs, label text, bar width) and matches REST exactly.
- **Suggested minimal fix (not applied):** emit the dynamically-returned `format.ts` color classes (e.g. a Tailwind safelist for `text-emerald-400`, `text-amber-400`, `bg-emerald-500`, `bg-rose-500`, `bg-amber-500`) or reference them statically. No data/behavior change required.

---

## Skipped Tests

None. All 12 test cases executed against a live frontend and backend.

---

## Environment

- **Frontend URL:** http://localhost:3650 (HTTP 200)
- **Backend URL:** http://localhost:8650 (`/health` 200; REST `/tape/SIM-BUYER/state` + `/features` used for UT-08)
- **Browser:** Chrome via `mcp__plugin_superpowers-chrome_chrome__use_browser` (viewport 1440×900)
- **Test Date:** 2026-06-02
- **Evidence directory:** `reports/qa/goal-i_will_be_rich-iter-2-evidence/`
- **Evidence files:** `UT-01-result.png`, `UT-02-result.png`, `UT-05-result.png`, `UT-08-result.png`, `UT-08-rest-json.txt`, `UT-09-result.png`, `UT-10-result.png`, `DEFECT-emerald-css-color.txt`
- **Note:** SIM-BUYER is a deterministic, finite scenario; it ramped the price ~115 → ~122 (live, no reload) and then reported `stream_status: "closed"` at its end, freezing the final snapshot (confidence 0.888, buyer_control). All J-01/J-02/J-08 *data* assertions were captured both during the live phase and at the frozen end-state.
