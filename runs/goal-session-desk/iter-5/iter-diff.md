# Iteration diff (bounded)

Files changed: 2. Shown in full: 2.

```diff
diff --git a/README.md b/README.md
index d27b38b..db14c7a 100644
--- a/README.md
+++ b/README.md
@@ -5,7 +5,7 @@ Standalone real-time tape-reading system for US stocks — given one ticker, it
 <!-- AUTO:capabilities -->
 ## What it does
 
-Tapeology watches a single US equity ticker and answers one question: what is the tape doing right now, and how confident are we? It distinguishes genuine directional control from absorption — high one-sided aggression with no corresponding price progress is absorption, not control. The engine is the single source of truth; REST, WebSocket, the UI, and a read-only machine-readable connection all read the same computed values. The app has two pages — a live Cockpit and a Structure view — linked by a persistent top navigation bar.
+Tapeology watches a single US equity ticker and answers one question: what is the tape doing right now, and how confident are we? It distinguishes genuine directional control from absorption — high one-sided aggression with no corresponding price progress is absorption, not control. The engine is the single source of truth; REST, WebSocket, the UI, and a read-only machine-readable connection all read the same computed values. The app has three pages — a live Cockpit, a Structure view, and a Desk daily-screening briefing — linked by a persistent top navigation bar.
 
 Current capabilities:
 
@@ -61,8 +61,9 @@ Current capabilities:
 - **Operator-run edge report compute** — beneath the "Edge report not computed yet." message, a "Compute edge report" button starts the full three-strategy comparison as a background job without leaving the page. While it runs, a live counter shows how many of the comparison's individual backtests have finished so far — including how many were reused from already-completed work rather than recomputed — updating automatically with no manual refresh needed. When the computation completes, the finished report renders in place automatically, using the same table already shown for a previously-computed report. If the computation fails partway through, the panel shows the specific error message instead of a generic failure, and the button relabels itself so a fresh attempt is one more click away. Reloading the page, or landing on it, while a compute is running, or after one has already finished or failed, immediately shows the matching state rather than resetting to idle. A compute that is interrupted — by a server restart, a crash, or a cancellation — resumes cleanly when re-triggered: it skips every result already durably saved and computes only what's left, finishing far faster than starting over. The same computation can also be started, unattended, from the command line for long background runs, where it can be spread across several worker processes at once for a further speedup; the on-page button always runs single-process by design.
 - **Cockpit price-chart tradable bands and a descriptive confluence chip** — the tradable support/resistance bands from the Structure page's map now also draw directly on the live cockpit price chart while watching a symbol in Simulated or Historical mode: one or two solid price lines per band (rose for resistance, emerald for support), each labeled with side, class, quality score, and whether it sits on a round number — alongside the existing tape-state markers, without changing how those render. A small descriptive banner appears beneath the chart only when the last traded price sits inside one of those bands AND the live tape reading matches that band's configured rejection-or-breakthrough state — for example "Inside R-band 300.05–300.17 (class A) · tape: Ask Absorption (rejection) · measured history: edge report." The banner states the current condition and points to the edge report as measured history; it never tells you to buy or sell and never predicts an outcome. A simulated ticker with no real recorded price history shows an honest "No tradable map for TICKER" note instead of a fabricated band. Live mode is unchanged — the price chart, and therefore the bands and banner, stay hidden there exactly as before.
 - **S&P 100 universe snapshot fetch and registry (research API)** — on explicit request, fetch the current S&P 100 constituent list from a public source (Wikipedia) and validate it (a real company-symbol table, roughly 90–110 names, no garbled entries), refusing with a specific explanation on any anomaly rather than guessing or saving a partial list. A valid fetch is saved as a permanent, checksummed, dated snapshot; fetching identical membership again is recognized and refused rather than silently duplicated or overwritten. Dual-class tickers are normalized for use elsewhere in the app (for example `BRK.B` → `BRK-B`) while the original source form is kept in the snapshot's own record. A second call lists every saved snapshot and returns the most recent membership, honestly reporting that nothing has been fetched yet before the first run. There is no browser page for this yet; it is reachable through the research API and the matching machine-readable tool.
-- **Bar coverage check and resumable top-up over the universe (research API + command-line tool)** — for every member of the most recently registered S&P 100 universe snapshot, see instantly — read from a lookup index, never by re-scanning the underlying bar files — whether hourly, 4-hour, daily, and weekly price bars are already on file and how fresh each one is. A single operator-triggered job then walks every member of that universe and fills in whichever of those four windows are missing, reusing the exact same fetch-and-record path a single manual bar request already uses, so behavior is identical; it reports live progress per symbol/timeframe (newly fetched, already on file, or failed), can be cancelled mid-run, and safely resumes without re-downloading anything already recorded. A command-line version runs the same job unattended for a real, full pass over the whole universe. There is no browser page for this yet; the coverage check and the top-up job are both reachable through the research API, and the top-up job also from the command line.
-- **A daily screening desk over the fetched universe (research API + command-line tool)** — for the latest registered S&P 100 universe snapshot, run a "screen" as of a chosen date: for every member, read its own already-computed tradable level map and summarize the closest support/resistance band into one ranked list — that band's inherited A/B/C conviction class, how far the screen date's closing price sits from it in basis points, and the band's quality score, ranked strongest and closest first. A member with no recorded price bars for that date is reported as an honest "skipped" entry rather than guessed at. Every run is pinned to its exact inputs — the screen date, which universe snapshot was used, the exact configuration in effect, and the bar data on file at the time — so repeating an identical request returns the same saved result instead of writing a duplicate, and a corrupted or tampered saved run is refused rather than silently overwritten. A run reports live progress as it works through the list and can be cancelled mid-flight; only one run proceeds at a time. Past runs can be browsed as lightweight summaries, or fetched in full by date or as the latest recorded result. Triggered explicitly from the command line or the research API — never automatically. There is no browser page for this yet.
+- **Bar coverage check and resumable top-up over the universe (research API + command-line tool)** — for every member of the most recently registered S&P 100 universe snapshot, see instantly — read from a lookup index, never by re-scanning the underlying bar files — whether hourly, 4-hour, daily, and weekly price bars are already on file and how fresh each one is. A single operator-triggered job then walks every member of that universe and fills in whichever of those four windows are missing, reusing the exact same fetch-and-record path a single manual bar request already uses, so behavior is identical; it reports live progress per symbol/timeframe (newly fetched, already on file, or failed), can be cancelled mid-run, and safely resumes without re-downloading anything already recorded. A command-line version runs the same job unattended for a real, full pass over the whole universe. The top-up job is also reachable from the Desk page's "Top-up" button (below), in addition to the research API and the command line; the coverage check itself has no dedicated page yet, though each screen's briefing row shows a per-timeframe coverage badge — it otherwise remains reachable through the research API.
+- **A daily screening desk over the fetched universe (research API + command-line tool)** — for the latest registered S&P 100 universe snapshot, run a "screen" as of a chosen date: for every member, read its own already-computed tradable level map and summarize the closest support/resistance band into one ranked list — that band's inherited A/B/C conviction class, how far the screen date's closing price sits from it in basis points, and the band's quality score, ranked strongest and closest first. A member with no recorded price bars for that date is reported as an honest "skipped" entry rather than guessed at. Every run is pinned to its exact inputs — the screen date, which universe snapshot was used, the exact configuration in effect, and the bar data on file at the time — so repeating an identical request returns the same saved result instead of writing a duplicate, and a corrupted or tampered saved run is refused rather than silently overwritten. A run reports live progress as it works through the list and can be cancelled mid-flight; only one run proceeds at a time. Past runs can be browsed as lightweight summaries, or fetched in full by date or as the latest recorded result. Triggered explicitly from the command line, the research API, or the Desk page's "Run Screen" button (below) — never automatically.
+- **Desk page** — the third top-level page, reachable from the top navigation bar alongside Cockpit and Structure. Before any screen has ever been run it shows the plain message "Desk screen not computed yet." with enabled "Run Screen" and "Top-up" buttons. Run Screen starts today's screen over the registered universe and shows live progress — how many members have been checked so far and which symbol is currently being processed — with a Cancel control; clicking it again while a run is already in progress does not start a second one, it just shows the same run already under way. Top-up is the first on-screen control for the bar-fetching job described above, with the same live-progress and cancel behavior. Once a screen has run, the page shows four sections in order: a **Provenance** line naming which universe snapshot and date were used, the as-of timestamp, and the app's own internal settings fingerprint and bar-store signature, so two screens can always be told apart or confirmed identical; the **Briefing** — the ranked table itself, with each symbol's side, A/B/C class (captioned "nearest same-class band"), distance from that level in basis points, band score, a badge per timeframe the symbol has bar coverage for, and a tick-evidence badge where a recorded trade-by-trade dataset exists; **Skipped Members**, split into an honest "no bars" group and a "no basis session" group, each shown only when it has entries; and a read-only **Screen History** list of every past run (date, row/skipped counts, and its own provenance summary). Clicking Run Screen before any universe has ever been registered shows an inline error message instead of silently starting a job, and if the backend becomes unreachable while a run's progress is being checked, the page keeps showing the last progress it knew about rather than going blank. Opening a past entry in the Screen History list, and jumping from a ranked symbol straight to its chart on the Structure page, are both planned for a future update — today the history list shows only its summary line.
 - **REST and WebSocket API** — `POST /watch/{ticker}`, `DELETE /watch/{ticker}`, `POST /watch/{ticker}/pause`, `POST /watch/{ticker}/resume`, `POST /watch/{ticker}/speed`, `GET /tape/{ticker}/state`, `GET /tape/{ticker}/features`, `GET /tape/{ticker}/events`, `GET /tape/{ticker}/summary`, `GET /tape/{ticker}/history?bar=<10|30|60>`, `WS /tape/{ticker}/stream`, `GET /symbols/search`, `GET /market/clock`, `GET /research/taxonomy`, `POST /research/datasets`, `GET /research/datasets`, `GET /research/datasets/{id}`, `POST /research/backtests`, `GET /research/backtests`, `GET /research/backtests/{id}`, `POST /research/backtests/{id}/cancel`, `GET /research/pnl/ledger`, `GET /research/profiles`, `GET /research/strategies`, `POST /research/bars`, `GET /research/bars`, `GET /research/bars/{id}`, `GET /research/bars/{id}/candles`, `GET /research/candles`, `GET /research/levels`, `GET /research/tradability`, `GET /research/setups`, `GET /research/setups/{id}`, `GET /research/edge-report`, `POST /research/edge-report/compute`, `GET /research/edge-report/compute`, `POST /research/edge-report/compute/cancel`, `POST /research/desk/universe/fetch`, `GET /research/desk/universe`, `GET /research/desk/coverage`, `POST /research/desk/topup/compute`, `GET /research/desk/topup/compute`, `POST /research/desk/topup/compute/cancel`, `GET /research/desk/screen`, `POST /research/desk/screen/compute`, `GET /research/desk/screen/compute`, `POST /research/desk/screen/compute/cancel`, `GET /meta/ui-routes`.
 - **Machine-readable access for AI tools** — alongside the browser UI and REST API, a read-only connection (Model Context Protocol) lets AI assistants and other external tools query the exact same tape state, datasets, backtests, strategy registry, PnL ledger, bar series, support/resistance levels, tradable level maps, touch-event case studies, profit edge reports, and navigation data the REST API serves. Every value it returns matches the REST API exactly, nothing can ever be written or changed through it, and it surfaces an explicit error — never fabricated data — when the backend isn't reachable. The site's own top navigation bar is generated from that same canonical list of live pages rather than a hand-maintained one, and shows an honest notice instead of guessing if that list can't be reached.
 <!-- /AUTO:capabilities -->
diff --git a/apps/backend/scripts/qa_desk_iter5_fixture_scoped_backend.sh b/apps/backend/scripts/qa_desk_iter5_fixture_scoped_backend.sh
new file mode 100644
index 0000000..ffda7b3
--- /dev/null
+++ b/apps/backend/scripts/qa_desk_iter5_fixture_scoped_backend.sh
@@ -0,0 +1,97 @@
+#!/usr/bin/env bash
+# desk-iter5-fixture-scoped-backend.sh — Stand up a FIXTURE-SCOPED backend for the goal-desk
+# iter-5 browser-QA pass (J-04 evidence gap). Never touches the ambient apps/backend/.data/
+# store: every desk/bar/dataset directory this backend reads or writes lives under a fresh
+# temp root, never under apps/backend/.data/ (see docs/handoffs/goal-desk-iter-5-dev.md for the
+# rationale — the iter-4 near-miss that wrote 60 real bar records into the ambient store).
+#
+# Usage:
+#   bash apps/backend/scripts/qa_desk_iter5_fixture_scoped_backend.sh [root_dir] [port]
+#
+#   root_dir  Fresh temp root to seed (default: ${TMPDIR:-/tmp}/desk-iter5-fixture-qa). MUST be a
+#             root nobody else has written screen snapshots into yet if you need TC-1's empty
+#             state ("Desk screen not computed yet.") — this dev's own verification run already
+#             recorded 2 screen snapshots into ITS root; use a DIFFERENT path for the actual
+#             browser-QA pass. Re-using an existing (untouched) root reuses whatever it already
+#             contains (the universe/bar stores refuse re-registration of identical content, so a
+#             re-run over the SAME still-empty root is a safe no-op reseed).
+#   port      Backend port (default: 8301, the era's browser-QA rig convention — pair with
+#             `CHAIN_BACKEND_PORT=8301 CHAIN_FRONTEND_PORT=3301 bash scripts/start-frontend.sh`
+#             for the frontend so NEXT_PUBLIC_API_URL points at this backend).
+#
+# Lives under apps/backend/scripts/ (the project's own script tree — never under scripts/, which
+# is a symlink into the vendored incredible_auto_dev/ framework tree that gets content-synced from
+# upstream and must not carry project-specific QA tooling).
+#
+# What this seeds (verbatim copies, never re-derived):
+#   - universe dir  <- tests/fixtures/universe/universe-2026-07-25-817cc184bbb3.json (103 members)
+#   - bar dir       <- tests/fixtures/bars/{009371c9c02f46338bafef47148f92ad,
+#                                            b08b1a55ef4a45b2a1adad8fa82ccdf1}.json (PG 1h + 1d)
+#   - bar_index.db  <- rebuilt via BarIndex.reindex() over the seeded bar dir (T-4: coverage
+#                      reads the index, never the store, so the index must exist before any
+#                      GET /research/desk/coverage call)
+#   - screen dir, dataset dir, dataset index  <- left empty (honest "not computed yet" /
+#     no-tick-evidence states; this iteration adds no screen/dataset fixtures)
+#
+# Exec's `scripts/start-backend.sh` at the end (inherits every exported env var below).
+set -euo pipefail
+
+SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
+BACKEND_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
+REPO_ROOT="$(cd "$BACKEND_DIR/../.." && pwd)"
+
+ROOT="${1:-${TMPDIR:-/tmp}/desk-iter5-fixture-qa}"
+PORT="${2:-8301}"
+
+UNIVERSE_DIR="$ROOT/universe"
+BAR_DIR="$ROOT/bars"
+SCREEN_DIR="$ROOT/screen"
+DATASET_DIR="$ROOT/datasets"
+BAR_INDEX_DB="$ROOT/bar_index.db"
+DATASET_INDEX_DB="$ROOT/dataset_index.db"
+JOURNAL_DB="$ROOT/journal.db"
+
+mkdir -p "$UNIVERSE_DIR" "$BAR_DIR" "$SCREEN_DIR" "$DATASET_DIR"
+
+# Verbatim fixture seeds — never re-derived, never re-registered through record() (that would
+# mint a NEW checksum/id; the point is to reproduce the exact committed fixture files).
+cp "$BACKEND_DIR/tests/fixtures/universe/universe-2026-07-25-817cc184bbb3.json" "$UNIVERSE_DIR/"
+cp "$BACKEND_DIR/tests/fixtures/bars/009371c9c02f46338bafef47148f92ad.json" "$BAR_DIR/"
+cp "$BACKEND_DIR/tests/fixtures/bars/b08b1a55ef4a45b2a1adad8fa82ccdf1.json" "$BAR_DIR/"
+
+# Rebuild the derived bar_index.db from the seeded bar dir (coverage/screen reads ONLY the
+# index per T-4 — dropping raw JSON into the bar dir alone would leave the index empty and
+# every member, including PG, would show as "no bars").
+"$BACKEND_DIR/.venv/bin/python" -c "
+import sys
+sys.path.insert(0, '$BACKEND_DIR')
+from app.research.bars import BarStore
+from app.research.bar_index import BarIndex
+store = BarStore('$BAR_DIR')
+index = BarIndex('$BAR_INDEX_DB')
+index.reindex(store)
+records, errors = store.list()
+print(f'[desk-iter5-fixture-scoped-backend] bar_index seeded: {len(records)} series, {len(errors)} errors', file=sys.stderr)
+"
+
+export TAPEOLOGY_DESK_UNIVERSE_DIR="$UNIVERSE_DIR"
+export TAPEOLOGY_BAR_DIR="$BAR_DIR"
+export TAPEOLOGY_DESK_SCREEN_DIR="$SCREEN_DIR"
+export TAPEOLOGY_DATASET_DIR="$DATASET_DIR"
+export TAPEOLOGY_BAR_INDEX_DB="$BAR_INDEX_DB"
+export TAPEOLOGY_DATASET_INDEX_DB="$DATASET_INDEX_DB"
+# Not one of the six the spec names, but scoped for the same reason (belt-and-suspenders —
+# main.py's lifespan opens this at startup regardless of any desk route being hit): keeps the
+# ambient apps/backend/tapeology_journal.db untouched too.
+export TAPEOLOGY_JOURNAL_DB="$JOURNAL_DB"
+
+echo "[desk-iter5-fixture-scoped-backend] root=$ROOT port=$PORT" >&2
+echo "[desk-iter5-fixture-scoped-backend] TAPEOLOGY_DESK_UNIVERSE_DIR=$UNIVERSE_DIR" >&2
+echo "[desk-iter5-fixture-scoped-backend] TAPEOLOGY_BAR_DIR=$BAR_DIR" >&2
+echo "[desk-iter5-fixture-scoped-backend] TAPEOLOGY_DESK_SCREEN_DIR=$SCREEN_DIR" >&2
+echo "[desk-iter5-fixture-scoped-backend] TAPEOLOGY_DATASET_DIR=$DATASET_DIR" >&2
+echo "[desk-iter5-fixture-scoped-backend] TAPEOLOGY_BAR_INDEX_DB=$BAR_INDEX_DB" >&2
+echo "[desk-iter5-fixture-scoped-backend] TAPEOLOGY_DATASET_INDEX_DB=$DATASET_INDEX_DB" >&2
+echo "[desk-iter5-fixture-scoped-backend] TAPEOLOGY_JOURNAL_DB=$JOURNAL_DB" >&2
+
+exec env CHAIN_BACKEND_PORT="$PORT" bash "$REPO_ROOT/scripts/start-backend.sh"
```
