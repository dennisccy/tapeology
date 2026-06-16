# Phase goal-i_will_be_super_rich_with_my_loved_ones-iter-29 — What to Click (Operator Verification Guide)

**Phase:** goal-i_will_be_super_rich_with_my_loved_ones-iter-29
**Time required:** ~5 minutes (market-hours-only steps noted)
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3650`
- Backend running with `apps/backend/.env` loaded (so Alpaca IEX credentials are in the environment)
- US regular market session is OPEN (Mon-Fri, 9:30 AM–4:00 PM US Eastern) — steps 3–7 require a live IEX feed and cannot be executed outside market hours
- Probe backend is healthy before starting: `curl http://localhost:8000/health` should return HTTP 200

---

## Verification Steps

1. Open `http://localhost:3650` in your browser
   - **Expect:** Cockpit home loads — full panel grid visible (status area, bid/ask, recent-trades, confidence, thesis strip). Sound toggle visible. No red error banner.

2. Type `ZZZNOEXIST` into the symbol input field and click "Watch" (or press Enter)
   - **Expect:** Within 15 seconds the cockpit shows an explicit failure or error message — text like "not a tradable symbol" or a visible error panel. No bid/ask prices, no tape state label, no trade list appears. The cockpit does NOT hang on "connecting" indefinitely.
   - **Broken looks like:** A blank white panel, a stuck "connecting" spinner, or any tape state label (`buyer_control`, etc.) appearing for a nonexistent symbol.

3. Clear the symbol input, type `F`, and click "Watch" (or press Enter)
   - **Expect:** Within 15 seconds the status dot turns green and the label reads `live`. The recent-trades count begins ticking upward as real IEX prints arrive.
   - **Broken looks like:** Status stays on "connecting" for more than 30 seconds, or shows a red/error state instead of green `live`.

4. Look at the status area immediately to the right of (or below) the status dot
   - **Expect:** A badge reading `IEX (live)` (or `iex`) is visible. Directly below or beside it, the disclosure line reads: "live verdicts read the single-venue IEX feed; historical replay and studies use SIP — spreads and prints differ". The disclosure text is visible in the viewport without scrolling.
   - **Broken looks like:** Badge is missing, reads "sim" or "sip" instead of "iex", or the disclosure line is absent or requires expanding a tooltip to read.

5. Watch the status indicator continuously without interacting with the page. Wait for a natural IEX feed lull (no new prints for more than 10 seconds).
   - **Expect:** The status dot changes from green to amber (or neutral) and the label changes from `live` to `stale`. At the exact moment `stale` appears, the recent-trades count is frozen — no new rows appear in the trades list while the status reads `stale`. When the next real market print arrives, the dot returns to green and the label returns to `live`, and the trades count resumes advancing.
   - **Broken looks like:** The indicator never shows `stale` after a long wait (possible if the feed is very active), OR it shows `stale` but new trades keep appearing (would indicate fabricated data), OR the dot color does not change (only the label changes — both must change).

6. In the cockpit thesis strip (bottom of the cockpit), click the thesis input field, type `absorption_reversal long`, and submit the thesis by clicking the "Declare" or "Submit" button (or pressing Enter)
   - **Expect:** The thesis strip updates to show the declared thesis in an active or pending state — no error message appears. The cockpit continues showing live data.

7. Navigate to `http://localhost:3650/journal`
   - **Expect:** The journal table loads and shows at least one row. Locate the most recently created row (top of the list or the one matching the thesis just declared). The `data_feed` column for that row shows `iex`. No row in the table shows a mix of `iex` and `sip` for the same session.
   - **Broken looks like:** The `data_feed` column is blank, shows `sip` for a live-declared thesis, or the column is missing from the table entirely.

---

## What "Working Correctly" Looks Like

- The status dot is clearly green with the label `live` during an active IEX watch — the color contrast is immediately obvious without reading the text
- The `stale` state uses a different (amber or neutral) color so operators can see the feed degraded at a glance
- The FeedBasisBadge reads `IEX (live)` and the disclosure line is visible inline — no extra clicks required to read it
- The journal row for a live-declared thesis carries `data_feed = iex`, proving live and historical data are kept separate

## Common Issues

- **"connecting" never transitions to "live"**: Verify the backend was started with `.env` loaded — `config.py` does not auto-load `.env`; restart with `cd apps/backend && source .env && uvicorn ...` (or however the project starts). Also confirm the market is open.
- **Badge reads "sim" instead of "iex"**: The backend may have started without credentials, falling back to simulated mode. Restart with `.env` loaded.
- **"stale" never appears during step 5**: The symbol `F` may be printing frequently enough that no 10-second gap occurs. Switch to a quieter symbol or wait for an off-peak minute; do not manufacture a lull artificially.
- **Frontend not loading at port 3650**: Verify the dev server is running (`ps aux | grep next` or `lsof -i :3650`).
