# goal-tape_to_profit_support_resistence-iter-1 — Implementation Summary

**Phase:** goal-tape_to_profit_support_resistence-iter-1
**Date:** 2026-07-06
**Written by:** developer

---

## Features Implemented

- **Recording a real historical price-bar series**: An operator (or an automated tool) can now ask
  the system to fetch and permanently save a real historical OHLC ("open/high/low/close") price
  series for a stock symbol — at daily, weekly, monthly, hourly, or several other calendar
  timeframes — and the system keeps that saved copy forever, unchanged. This is the first time the
  product has ever stored anything resembling a "bar chart" of price history; until now it only
  read live/replayed tick-by-tick trades and quotes.
- **Reading back a saved bar series**: Once a bar series is saved, anyone (or any tool) can read it
  back — the symbol, the timeframe, the exact time window it covers, which data feed it came from,
  how many bars it has, and the bars themselves. Reading it back twice always returns byte-for-byte
  the same answer.
- **Tamper detection**: Every saved bar series carries two layers of built-in checksums. If a saved
  file is ever corrupted or hand-edited, the system detects it immediately and reports an explicit
  error rather than silently serving bad data or a partial answer.
- **No duplicate recordings**: Trying to record the exact same bar series twice is refused with a
  clear message pointing at the original recording — nothing is ever silently overwritten or
  duplicated.
- **Honest "please connect your data account" message**: If the system's real-data credentials are
  not configured, asking it to record a new bar series returns a clear, explicit message saying so
  — it never invents fake price data to paper over the missing connection.
- **A machine-readable version of all of the above**: The same "list bar series" information is
  also available through the project's MCP (AI-assistant) tool interface, word-for-word identical
  to what a human would see through the web API.

## Changed Behavior

- None. This is a purely additive capability — nothing that existed before this iteration behaves
  differently. The live cockpit, the journal, the studies, and the performance page are all
  unchanged (confirmed: zero files under the website's frontend code were touched).

## Backend-Only Items

- `POST /research/bars`, `GET /research/bars`, `GET /research/bars/{id}` — recording and reading
  bar series — exist only as machine endpoints (web API + the MCP tool) this iteration. There is no
  new page or panel in the website yet; that is intentionally out of scope for this step (it is a
  data-foundation iteration, meant to be consumed by upcoming capabilities rather than looked at
  directly).

## Incomplete Items

- **Turning bars into support/resistance levels, and everything after that**: this iteration only
  builds the ability to fetch and save the raw price-bar data. The next planned steps — finding
  support/resistance price levels from those bars, grading how strong each level is, building a
  trading strategy that reacts to price reaching those levels, and honestly measuring whether that
  strategy would have made money — are **not** part of this iteration and remain to be built.
- **No screen to view bars yet**: an operator can fetch/read bar data only through the API/MCP
  tools right now, not through a page in the website.

## Config and Environment Changes

- No new environment variables are required to use existing features. One new *optional* override
  is available for operators who want to change where recorded bar data is stored on disk:
  `TAPEOLOGY_BAR_DIR` — where recorded price-bar files are saved. Default: a folder next to the
  backend code (`apps/backend/.data/bars/`), the same pattern already used for other recorded
  research data.
- No database migration was needed (bar series are saved as individual files, the same way other
  recorded research data already works).
- Recording a real bar series requires the same Alpaca market-data account credentials
  (`ALPACA_API_KEY` / `ALPACA_API_SECRET`) the product already uses for live/historical trading
  data — no new account or service is introduced.

## Known Limitations

- **Recording real bars always requires a connected data account.** There is no "practice"/demo
  bar-recording path — unlike some other parts of the system, which can be tried out for free with
  built-in example data, recording an actual price-bar series always requires real market-data
  credentials to be configured. (A small, tiny example bar series is bundled with the product's
  automated tests so its internal machinery can be verified without needing an account — but that
  example is for the test suite, not something an operator interacts with directly.)
- **Not every symbol/timeframe combination has the same amount of history available.** During
  testing with a real account, daily and weekly price history reached back several years as
  requested, but monthly bars were only available from 2016 onward regardless of how far back was
  asked for — this is a limit of the underlying data provider's free plan, not something this
  product controls.
- **Very recent data is deliberately excluded.** To respect the data provider's free-plan rules,
  the system never fetches the most recent roughly 15 minutes of bar data — a recording request
  covering only that very recent window will honestly report "nothing to record" rather than
  guessing or waiting.
- **No safeguard yet distinguishes "that symbol doesn't exist" from "no data in that time window"**
  for bar recordings specifically — both currently show the same "nothing to record" message. (Live
  trading/watching a ticker elsewhere in the product does already tell those two situations apart;
  that distinction just isn't built for this new bar-recording action yet, since nothing in this
  iteration's requirements called for it.)
