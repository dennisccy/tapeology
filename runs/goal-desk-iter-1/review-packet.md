# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 3. Shown in full: 3.

```diff
diff --git a/apps/backend/app/config.py b/apps/backend/app/config.py
index e533e70..0a56b18 100644
--- a/apps/backend/app/config.py
+++ b/apps/backend/app/config.py
@@ -1101,6 +1101,38 @@ class Config:
         default_factory=lambda: {"A": 2.0, "B": 1.0, "C": 0.5}
     )
 
+    # --- Era B "The Desk": UNIVERSE INGESTION (Key Capability 1, J-01) --------------------------
+    # Every field below governs ONLY the brand-new universe-snapshot capability (fetch, parse,
+    # validate, register S&P 100 membership) — none of them are read by the tape engine, a
+    # backtest, a study, or the PnL ledger, so they take Path A: each one lands in the
+    # ``config_fingerprint`` exclusion set below (the ``bar_timeframes``/``bar_dir`` precedent),
+    # with a stability test proving the pin is unchanged and a counter-test proving the field
+    # genuinely shapes the NEW path's output (``tests/test_desk_universe.py``). Namespaced
+    # ``desk_universe_*`` so it never collides with the unrelated ``sr_*`` / ``structure_tape_*`` /
+    # ``setups_*`` research families above.
+    #
+    # SOURCE URL: the ONE documented public constituents source (goal.md Key Capability 1 — "one
+    # documented source URL as a Path-A Config field"). A pure validation/fetch-target value — it
+    # selects WHERE to fetch from, never what a fetched member list contains (membership is never a
+    # signal, per the desk-era anti-goals), so it cannot affect any persisted research value.
+    desk_universe_source_url: str = "https://en.wikipedia.org/wiki/S%26P_100"
+    # MEMBER-COUNT BOUNDS: the sanity window a parsed membership list must fall inside (goal.md's
+    # "count sanity 90-110") — a page that returns far too few or far too many rows almost
+    # certainly means the table shape changed underneath the parser, so refusing outside this
+    # window is the honest failure T-1 requires (never a partial or guessed list). Defaults measured
+    # against the real S&P 100 index, which — because of dual-class share lines (e.g. GOOG/GOOGL) —
+    # legitimately runs a few names past 100.
+    desk_universe_min_members: int = 90
+    desk_universe_max_members: int = 110
+    # STORAGE DIRECTORY: where the universe store persists frozen, checksummed snapshot JSON files
+    # (one file per registered snapshot) — mirrors ``bar_dir``/``dataset_dir`` exactly (the
+    # era-4/era-3 capability-1 precedent). ONLY a default here — the operator overrides it with the
+    # ``TAPEOLOGY_DESK_UNIVERSE_DIR`` env var (read in ``desk_universe_dir_resolved`` below, the
+    # ``bar_dir_resolved`` pattern) and tests point it at a temp dir the same way. Package-anchored
+    # (``apps/backend/.data/universe/``, covered by the repo's ``.data/`` gitignore entry) so it
+    # resolves identically whatever the process cwd is.
+    desk_universe_dir: str = str(Path(__file__).resolve().parents[1] / ".data" / "universe")
+
     def profile_definition(self, profile_id: str) -> dict | None:
         """The config-owned descriptor for ``profile_id`` (Data Contract row 33) — the
         ``strategy_definition`` pattern applied to profiles: THIS method is the ONE place that
@@ -1309,6 +1341,13 @@ class Config:
         code change, while tests point it at a temp dir via the env var."""
         return os.environ.get("TAPEOLOGY_BAR_DIR", self.bar_dir)
 
+    def desk_universe_dir_resolved(self) -> str:
+        """The effective universe-store directory: the ``TAPEOLOGY_DESK_UNIVERSE_DIR`` env var if
+        set, else the package-anchored config default (the ``bar_dir_resolved`` pattern, era-B
+        J-01). Read at store-construction time so an operator can point the universe store at a
+        real location without code change, while tests point it at a temp dir via the env var."""
+        return os.environ.get("TAPEOLOGY_DESK_UNIVERSE_DIR", self.desk_universe_dir)
+
     def config_fingerprint(self) -> str:
         """A stable hash over the ENTIRE frozen config (capability 28 / honesty stamps).
 
@@ -1512,6 +1551,23 @@ class Config:
             "structure_tape_stop_bps_by_class",
             "structure_tape_reward_r_multiple_by_class",
             "structure_tape_size_multiple_by_class",
+            # Era B "The Desk" universe ingestion (Key Capability 1, J-01): the SAME
+            # ``bar_timeframes``/``bar_dir`` "brand-new, unrelated capability" rationale directly
+            # above -- the universe subsystem (fetch source, member-count sanity bounds, storage
+            # directory) is a SEPARATE, additive capability that selects WHICH symbols the desk
+            # screens; it never enters the tape engine, a backtest, a study, or the PnL ledger (the
+            # desk-era anti-goal "membership is never a signal"), so none of these three fields can
+            # affect any persisted research value. Two journals identical in every FINGERPRINTED
+            # threshold but configured with a different universe source URL, member-count bounds,
+            # or storage directory MUST share a fingerprint (else every temp-dir test of this
+            # brand-new capability would mint a different fingerprint and falsely fragment the
+            # tape/backtest/PnL pools those OTHER thresholds exist to protect). Pinned by a
+            # fingerprint-stability test + the real-threshold counter-test in
+            # ``tests/test_desk_universe.py``.
+            "desk_universe_source_url",
+            "desk_universe_min_members",
+            "desk_universe_max_members",
+            "desk_universe_dir",
         }
         payload = {k: v for k, v in asdict(self).items() if k not in excluded}
         encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
diff --git a/apps/backend/app/main.py b/apps/backend/app/main.py
index c95d1e5..cbeb917 100644
--- a/apps/backend/app/main.py
+++ b/apps/backend/app/main.py
@@ -39,6 +39,7 @@ from .providers.adapters.base import (
 )
 from .providers.historical import HistoricalProvider
 from .providers.live import LiveProvider
+from .research.desk_routes import router as desk_router
 from .research.routes import (
     ResearchRegistry,
     get_registry_or_none,
@@ -196,6 +197,10 @@ app.add_middleware(
 # router; the engine snapshot endpoints above are untouched.
 app.include_router(research_router)
 
+# Era B "The Desk" (J-01): the universe-ingestion namespace, under the SAME /research prefix but
+# its own module (routes.py is already large) — mounted separately, alongside research_router.
+app.include_router(desk_router)
+
 # The meta namespace (Data Contract row 35, J-01): the canonical UI route map. The rendered nav
 # and the MCP ``ui_route_map`` tool read it — never a hand-maintained duplicate list.
 app.include_router(meta_router)
diff --git a/apps/backend/pyproject.toml b/apps/backend/pyproject.toml
index f52272c..d8844b2 100644
--- a/apps/backend/pyproject.toml
+++ b/apps/backend/pyproject.toml
@@ -8,5 +8,5 @@ requires-python = ">=3.12"
 testpaths = ["tests"]
 addopts = "-q"
 markers = [
-    "integration: hits the REAL Alpaca live socket (operator/gated; needs credentials + market hours + TAPEOLOGY_LIVE_INTEGRATION=1). Skipped by default.",
+    "integration: hits a REAL external system -- Alpaca live socket/recording, Yahoo Finance, or Wikipedia (operator/gated; TAPEOLOGY_LIVE_INTEGRATION=1, some also need credentials + market hours). Skipped by default.",
 ]
```

## Excluded-path stat (dependency/lockfile visibility)

 runs/goal-session-desk/telemetry.jsonl   | 6 ++++++
 runs/goal-session-desk/trace/trace.jsonl | 3 +++
 2 files changed, 9 insertions(+)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
