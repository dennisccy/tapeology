# Phase goal-clean_slate-iter-2 — What to Click (Operator Verification Guide)

**Phase:** goal-clean_slate-iter-2 (J-02: "Frontend + WS demolition — the two-page product")
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Backend running at `http://localhost:8301` and frontend running at `http://localhost:3301`
- The frontend must have been **rebuilt clean** after this iteration's changes (its `.next` build
  folder deleted and rebuilt, process restarted) — otherwise you will see the OLD pre-iteration UI
  and every check below will look "broken" when it isn't
- No login required
- No seed data required — the ticker `SIM-BUYER` is a built-in scripted simulation

---

## What changed, in one sentence

Three pages (Journal, Studies, Performance) and the Cockpit's thesis/hint/sound controls were
**deleted outright** — nothing was added. The product is now exactly two pages: Cockpit and
Structure, and both should look and work exactly as before, just without the deleted extras.

---

## Verification Steps

1. Open `http://localhost:3301/` in your browser
   - **Expect:** The Cockpit page loads with no error screen. The top nav bar (just below the
     "Tapeology" wordmark) shows **exactly two** links: "Cockpit" and "Structure" — no "Journal",
     "Studies", or "Performance" link anywhere.

2. Type each of these three addresses into the URL bar, one at a time: `http://localhost:3301/journal`,
   `http://localhost:3301/studies`, `http://localhost:3301/performance`
   - **Expect:** All three show the same "404" heading with the text "This page could not be
     found." underneath — not a blank page, not the old journal table, not the old studies
     workbench, not the old performance dashboard.

3. Go back to `http://localhost:3301/`. Type `SIM-BUYER` into the ticker field (it shows the grey
   placeholder text "Ticker e.g. SIM-BUYER" when empty), then click the green "Watch" button.
   - **Expect:** The page briefly shows "Connecting to SIM-BUYER…", then six panels appear —
     "Tape State", "Quote", "Features", "Recent Trades", "Observations", "Event Log" — with a
     candlestick price chart above them. Nowhere on the page is there a "Declare thesis" button, a
     hint card, or a sound/mute icon.

4. In the price chart's header row, click the "30s" button (in the small button group on the left,
   under the label "Tape")
   - **Expect:** The chart redraws using 30-second bars — the "30s" button highlights — and new
     candlestick bars keep appearing at the right edge of the chart every few seconds as the
     simulated tape streams. The chart is moving, not frozen.

5. Wait until the "Tape State" panel's large heading reads "Buyer Control" (this can take a minute
   or two), then click the red "Stop" button in the top-right of the header.
   - **Expect:** The screen returns directly to the plain "No ticker watched" screen with the hint
     "Try: SIM-BUYER" — no extra panel appears first, no matter what state the tape was in when you
     clicked Stop.

6. Navigate to `http://localhost:3301/structure`. Type `AAPL` into the "Symbol" field and
   `2026-06-22T21:00:00Z` into the "As-of (UTC, ISO-8601)" field, then click "Load".
   - **Expect:** The "Tradable Map" panel and the chart below it populate with a resistance band
     roughly in the 300–302 price range, labeled "Class A" — the same wall this page has always
     shown for this exact symbol/date. This page's own chart code was not touched this iteration,
     so it should look identical to before.

---

## What "Working Correctly" Looks Like

- The nav bar shows exactly two links, everywhere, always — never five
- `/journal`, `/studies`, `/performance` always show the "404" / "This page could not be found."
  page — never their old content
- The Cockpit's chart and six-panel grid work exactly as before, just without the thesis strip,
  hint panel, and sound toggle
- The Structure page's wall band for AAPL looks exactly like it always has

## Common Issues

- **Nav still shows 5 links, or `/journal`/`/studies`/`/performance` still show real content**: the
  frontend is serving a stale build. Run a clean rebuild (`rm -rf apps/frontend/.next`, rebuild) and
  restart the frontend process — this is a known, expected gotcha for this iteration specifically.
- **Cockpit is stuck on "Connecting to SIM-BUYER…" and never proceeds**: the backend likely isn't
  running or isn't reachable at `http://localhost:8301` — check it's up before assuming this
  iteration broke something.
- **The Structure page's wall band for AAPL looks different, shifted, or is missing**: this page's
  chart component (`StructureChart.tsx`) was explicitly required to stay byte-for-byte unchanged
  this iteration — treat any visible difference here as a high-priority regression, not routine
  data drift.
