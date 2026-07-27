# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 3. Shown in full: 3.

```diff
diff --git a/apps/backend/tests/test_mcp_server.py b/apps/backend/tests/test_mcp_server.py
index 088d51e..89b1355 100644
--- a/apps/backend/tests/test_mcp_server.py
+++ b/apps/backend/tests/test_mcp_server.py
@@ -263,6 +263,10 @@ async def test_static_live_tools_json_byte_identical_to_rest(mcp_env):
 
 DESK_SCREEN_DATE = "2026-06-22"
 DESK_SCREEN_NONMATCH_DATE = "2020-01-01"
+# audit B1: the ?date= proxy test below seeds its OWN screen under this THIRD, distinct date
+# rather than reusing DESK_SCREEN_DATE's record (seeded by the populated-state test above) --
+# so it now passes standalone (`pytest -k ...`), not just inside the full module.
+DESK_SCREEN_ISOLATED_DATE = "2026-06-23"
 
 
 @pytest.mark.anyio
@@ -369,12 +373,36 @@ async def test_desk_screen_tool_byte_identical_on_a_populated_state(mcp_env, bac
 
 
 @pytest.mark.anyio
-async def test_get_endpoint_desk_screen_date_query_proxies_verbatim(mcp_env):
+async def test_get_endpoint_desk_screen_date_query_proxies_verbatim(mcp_env, backend_paths):
     """TC-6/TC-7: ``get_endpoint`` reaches the ``?date=`` lookup variant ``desk_screen`` itself
-    does not expose -- byte-identical for a matching date (the screen the previous test just
-    recorded), and the honest ``{"screen": null}`` 200 (never a 404, never an error) for a
-    non-matching one."""
-    matching_path = f"/research/desk/screen?date={DESK_SCREEN_DATE}"
+    does not expose -- byte-identical for a matching date (seeded HERE, under its own distinct
+    date -- audit B1 fix, so this test passes standalone, never relying on
+    ``test_desk_screen_tool_byte_identical_on_a_populated_state``'s side effect), and the honest
+    ``{"screen": null}`` 200 (never a 404, never an error) for a non-matching one."""
+    screen_dir = Path(backend_paths["TAPEOLOGY_DESK_SCREEN_DIR"])
+    ScreenStore(screen_dir).record(
+        screen_date=DESK_SCREEN_ISOLATED_DATE,
+        as_of="2026-06-23T21:00:00Z",
+        universe_snapshot_id="universe-2026-07-25-817cc184bbb3",
+        config_fingerprint=CONFIG.config_fingerprint(),
+        bar_store_signature="mcp-test-isolated-date-signature",
+        rows=[
+            {
+                "symbol": "AAPL",
+                "side": "resistance",
+                "band_class": "A",
+                "distance_bps": 12.5,
+                "band_score": 3.1,
+                "price_low": 300.0,
+                "price_high": 302.0,
+                "coverage": {"1d": {"has_bars": True, "latest_window_end_utc": "2026-06-23T00:00:00Z"}},
+                "tick_evidence": True,
+            }
+        ],
+        skipped=[],
+    )
+
+    matching_path = f"/research/desk/screen?date={DESK_SCREEN_ISOLATED_DATE}"
     result = await call_tool("get_endpoint", {"path": matching_path})
     rest = httpx.get(f"{mcp_env}{matching_path}", timeout=5.0)
     assert rest.status_code == 200
diff --git a/apps/frontend/app/desk/page.tsx b/apps/frontend/app/desk/page.tsx
index 0362f78..b9ae0d2 100644
--- a/apps/frontend/app/desk/page.tsx
+++ b/apps/frontend/app/desk/page.tsx
@@ -204,8 +204,10 @@ function deskSkipDrillInTitle(skip: DeskScreenSkip): string {
 // One ranked row: symbol, side, band-class chip, distance-bps chip, band score, per-timeframe
 // coverage badges, tick-evidence badge — the DoD's exact column list, every value read verbatim
 // from the snapshot. Distance and score are DISPLAYED to two decimals (a `0.33523150389608725 bps`
-// cell defeated the scanability the briefing exists for — audit F3); each cell's `title` carries the
-// served value in full, so nothing is lost, only formatted. The band-class chip carries the
+// cell defeated the scanability the briefing exists for — audit F3); the full-precision value is
+// not lost — it is reachable via the row's own drill-in anchor's composite `title`
+// (`deskRowDrillInTitle` above, audit F2 fix), never a per-cell `title` (iter-7 audit F1: this
+// comment used to claim the opposite). The band-class chip carries the
 // "nearest same-class band" caption
 // (assumptions.md iter-4 entry 1 — `_select_best_band` itself stays byte-unchanged; this copy
 // keeps the chip honest about what the ranking actually selects rather than implying it is the
diff --git a/docs/goal.md b/docs/goal.md
index 27ac0fc..6d3bdcb 100644
--- a/docs/goal.md
+++ b/docs/goal.md
@@ -100,6 +100,48 @@ one: `/` and `/structure` (this era adds `/desk`).
 6. The **read-only MCP server** (`app/mcp/`) keeps its byte-identical GET-proxy contract; this era
    adds two GET-proxy tools (15 → 17) and never adds writes.
 
+### OWNER RATIFICATION — 2026-07-27 (price-less-bar repair) — R-1
+
+**Ratified and IN INVENTORY for this era**, in addition to everything named above: the
+price-less-bar repair the chain landed in iteration 4, comprising exactly
+
+- `apps/backend/app/providers/adapters/yahoo.py` — `_is_priced_row` drops a vendor row that
+  carries no price at the fetch seam (an all-priceless window still raises `NoDataForWindow`);
+- `apps/backend/app/research/bars.py` — `BarStore.record` refuses a non-finite price before any
+  write (`NonFiniteBarPriceError`, mapped to 422), and `_merged_rows` excludes already-recorded
+  price-less **rows** on read, reporting them through the existing `integrity_errors` channel;
+- `apps/backend/app/research/routes.py` — one `except NonFiniteBarPriceError` clause on
+  `record_bar_series`, mapping the refusal to the same honest 422 the empty-window refusal already
+  uses (an added `except` + import line; no existing behavior altered);
+- `apps/frontend/components/StructureChart.tsx` — a finite-value guard on the OHLC series
+  (defence in depth);
+- `apps/backend/tests/test_structure_chart_viewport.py` — the one chart-guard assertion relaxed
+  from exact text to a pattern, to match the guarded expression above;
+- `apps/backend/tests/test_bars.py` — six ADDED tests covering the rail (write refusal per field,
+  whole-series refusal, checksum integrity of a planted price-less series, read-time row
+  exclusion + its `integrity_errors` report, append-only file untouched by exclusion, memo
+  preserved). Additions only — no existing test in this file was modified or removed;
+- `apps/backend/tests/test_yahoo_adapter.py` — five ADDED tests for the vendor-seam drop
+  (all-NaN row, real rows undisturbed, all-priceless window raises, NaN volume). Additions only;
+- `apps/backend/tests/test_bars_api.py` — one ADDED test proving the merged read never serves a
+  null-priced candle. Additions only.
+
+**Why:** the vendor genuinely serves a price-less AAPL daily row. Before the repair, one Top-up
+click persisted `NaN`-priced bars into the append-only store, which crashed `/structure`'s chart
+and silently emptied the tradable map (`compute_tradability("AAPL", as_of=2026-07-25)` returned
+`bands: []`). The repair restores honest behavior; it changes nothing for all-finite data, and the
+pinned wall still computes `resistance 300.11–302.2 class A score 171`.
+
+**Scope of the ratification, precisely:** the 60 already-affected bar series stay **on disk,
+untouched** — excluded row-by-row on read, never deleted, re-keyed, or rewritten. The pin
+`08e471b10130e1e2` does not move. `bars.py`'s file format, checksums, append-only immutability and
+split freezing are unchanged; only its write-time refusal and read-time row exclusion are new.
+This ratification does NOT open `bars.py`, `StructureChart.tsx`, `PriceChart.tsx`, or any guard
+test to further edits — anything beyond the eight files above still needs a new ratification.
+
+Where the clauses below say "untouched", "byte-unmodified", or "out-of-inventory", they are read
+subject to **R-1**.
+
 ## Success Criteria
 
 In priority order — kept-value integrity outranks new-surface completeness outranks convenience:
@@ -107,7 +149,8 @@ In priority order — kept-value integrity outranks new-surface completeness out
 1. **Nothing kept regresses.** Full backend suite green (1169 pass / 7 skip at era open — grows,
    never shrinks); engine equivalence proves byte-identical `default` outputs;
    `Config().config_fingerprint()` prints `08e471b10130e1e2` in every iteration; every kept `/`
-   and `/structure` behavior browser-verified as shipped; every guard test passes unmodified.
+   and `/structure` behavior browser-verified as shipped; every guard test passes unmodified
+   (subject to **R-1**).
 2. **The universe is honest.** Membership comes only from registered, dated, checksummed,
    append-only snapshots; the parser validates (charset, count bounds, normalization) or fails
    with an honest error — it NEVER emits a guessed or partial list; the committed fixture keeps
@@ -179,7 +222,8 @@ In priority order — kept-value integrity outranks new-surface completeness out
 - **No tick-data expansion.** No new dataset recording, no credential work; tick evidence badges
   reflect the 11 recorded dataset symbols as they stand.
 - **No engine, chart, or kept-surface work.** `app/engine/` untouched; `StructureChart.tsx`
-  untouched; `PriceChart.tsx` untouched; `/structure` untouched beyond the J-05 prefill.
+  untouched **except R-1's finite-value guard**; `PriceChart.tsx` untouched; `/structure` untouched
+  beyond the J-05 prefill.
 - **No fingerprint epoch bump.** Path A only; the pin `08e471b10130e1e2` does not move.
 - **No second market, no options/sentiment/news data, no paid services.** The one new external
   read is the documented constituents source; membership is universe METADATA, never a signal
@@ -219,7 +263,9 @@ In priority order — kept-value integrity outranks new-surface completeness out
 - **Guard tests (kept, never edited):** `tests/test_no_execution_path.py`,
   `tests/test_no_credential_in_artifacts.py`, the fast_wall source-introspection guards
   (`test_backtests.py`, `test_setups.py` pins), the chart guard suites, and the 13 fingerprint
-  pin assertions (e.g. `test_profile_equivalence.py:114`) all pass byte-unmodified all era.
+  pin assertions (e.g. `test_profile_equivalence.py:114`) all pass byte-unmodified all era — the
+  single exception is **R-1**'s `test_structure_chart_viewport.py` assertion, relaxed to a pattern
+  to match the guarded expression; no further guard-test edit is authorized.
 - **Hermetic tests:** the suite stays keyless on committed fixtures — the universe fixture
   snapshot ships in-repo; NO test performs a network fetch; live constituents fetch + 100-symbol
   top-up + real screens are operator-run verifications, never CI gates.
@@ -441,21 +487,28 @@ order: J-01 → J-02 → J-03 → J-04 → J-05 → J-06, with J-07 guarding con
   - Steps:
     1. Run the full backend suite + engine equivalence; verify every guard test
        (`test_no_execution_path.py`, `test_no_credential_in_artifacts.py`, source-introspection
-       guards, chart guard suites, the 13 pin assertions) passes byte-unmodified;
+       guards, chart guard suites, the 13 pin assertions) passes byte-unmodified — the sole
+       exception is **R-1**'s `test_structure_chart_viewport.py` assertion;
        `Config().config_fingerprint()` prints `08e471b10130e1e2`.
     2. In a real browser (after T-9): walk the kept product — sim cockpit (`SIM-BUYER` settles
        `buyer_control`, chart candles + timeframe switch + band overlay + live tape bars),
        `/structure` Load for pinned AAPL as-of 2026-06-22 (the 300–302.4 wall band renders),
        Case Studies drill-in, Edge Report honest state — screenshots for each.
     3. Verify the desk additions did not perturb kept values: kept-route responses byte-identical
-       on identical inputs vs an era-open baseline capture (per-route `curl --max-time`);
+       on identical inputs vs a baseline captured **from the era-open commit `047c38e`** (check it
+       out into a scratch worktree and capture per-route with `curl --max-time`; no baseline was
+       recorded at era open, so it is reconstructed from git at verification time). Two routes are
+       expected to differ and are exempt, because this era's own inventory changes them:
+       `/meta/ui-routes` (2 → 3 rows) and the MCP tool list (15 → 17). Where a route's body differs
+       for any OTHER reason, the difference is explained against **R-1** or it is a defect.
        `/research/taxonomy` unchanged; WS frame = engine projection only.
     4. Confirm the era's cumulative diff stays inside this goal.md's inventory (new desk modules/
-       routes/page/tools + the named `meta.py`/MCP/test touches + the J-05 prefill) — anything
-       else is surfaced BEFORE it lands.
+       routes/page/tools + the named `meta.py`/MCP/test touches + the J-05 prefill + **R-1**'s eight
+       files) — anything else is surfaced BEFORE it lands.
   - Acceptance: full suite green under the unchanged pin; every browser step evidenced by
-    screenshot (T-10); kept-route byte-identity holds; nav = exactly three routes; MCP = exactly
-    17 tools; zero out-of-inventory changes in the cumulative diff. *(Keyless core;
+    screenshot (T-10); kept-route byte-identity holds on every route outside step 3's two named
+    exemptions; nav = exactly three routes; MCP = exactly 17 tools; zero out-of-inventory changes
+    in the cumulative diff, reading "inventory" as including **R-1**. *(Keyless core;
     browser-verifiable.)*
 
 <!-- AUTO:journeys -->
@@ -478,8 +531,9 @@ audits; only ever grow more specific, never weaker):**
    states and thresholds, the frozen structure computations, the JSON `BarStore`, and every KEPT
    surface's behaviour stay byte-identical. New work is additive and versioned beside them, never
    a mutation of them. (The 5D demolition's removals are final history; this era builds `/desk`
-   BESIDE the kept two pages — the one sanctioned kept-surface edit is J-05's additive
-   `/structure` prefill.) *(critical)*
+   BESIDE the kept two pages — the sanctioned kept-surface edits are J-05's additive `/structure`
+   prefill and **R-1**'s price-less-row repair, which changes no output for finite data and leaves
+   every recorded series on disk untouched.) *(critical)*
 4. **Hold-out-only promotion** — the champion pointer moves only on a genuine hold-out survival
    through the sweep gate (plus the era-6 statistical gates once they exist). Train-only wins are
    labeled overfit. Never lower a minimum sample size, widen a gate, or pool across
```

## Excluded-path stat (dependency/lockfile visibility)

 reports/goal-session-desk-index.html             |  4 +--
 runs/goal-session-desk/.engine.lock/epoch        |  2 +-
 runs/goal-session-desk/.engine.lock/pid          |  2 +-
 runs/goal-session-desk/engine.pid                |  2 +-
 runs/goal-session-desk/journey-scripts/J-07.json |  2 +-
 runs/goal-session-desk/session.json              | 11 +++---
 runs/goal-session-desk/state/assumptions.md      | 21 ++++++++++++
 runs/goal-session-desk/state/blueprint.md        | 17 +++++++++-
 runs/goal-session-desk/summary.md                | 43 ++++++++++++++----------
 runs/goal-session-desk/telemetry.jsonl           | 21 ++++++++++++
 runs/goal-session-desk/trace/trace.jsonl         |  3 ++
 11 files changed, 98 insertions(+), 30 deletions(-)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
