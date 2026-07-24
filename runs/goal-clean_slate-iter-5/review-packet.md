# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 1. Shown in full: 1.

```diff
diff --git a/apps/frontend/app/structure/page.tsx b/apps/frontend/app/structure/page.tsx
index 2f299bb..165a09b 100644
--- a/apps/frontend/app/structure/page.tsx
+++ b/apps/frontend/app/structure/page.tsx
@@ -332,7 +332,7 @@ const SETUP_REACTIONS = ["rejected", "broke", "chopped"];
 // the Structure page — flip to `true` to bring it back. Typed as `boolean` (not the `false` literal)
 // so the render-time gate below is a normal conditional, not narrowed to dead code. All Case Studies
 // state/handlers are kept intact; only its rendered section is withheld.
-const SHOW_CASE_STUDIES: boolean = false;
+const SHOW_CASE_STUDIES: boolean = true;
 
 type LoadState<T> =
   | { phase: "idle" }
@@ -2031,8 +2031,10 @@ export default function StructurePage() {
           <p data-testid="structure-framing" className="mt-2 max-w-3xl text-xs text-slate-600">
             Tradable Map is the default view, read verbatim from GET /research/tradability; toggle
             &quot;Show raw levels&quot; for the underlying S/R levels and confluence zones (off by
-            default). Edge Report compares v1, structure_tape, and structure_tape_map over recorded
-            windows, register included. Fetching bars below (Yahoo Finance, with Alpaca for history
+            default). Case Studies lists every band-touch event with its reaction, forward returns,
+            and — once recorded — its tape timeline; Edge Report compares v1, structure_tape, and
+            structure_tape_map over recorded windows, register included. Fetching bars below (Yahoo
+            Finance, with Alpaca for history
             beyond Yahoo&apos;s limits) is this page&apos;s one explicit write action — everything else, including the
             strategy registry/champion and the structure_tape-vs-v1 comparison, is read-only. Every
             value on this page is read verbatim from its canonical endpoint — nothing here is
```

## Excluded-path stat (dependency/lockfile visibility)

 runs/goal-session-clean_slate/telemetry.jsonl   | 6 ++++++
 runs/goal-session-clean_slate/trace/trace.jsonl | 3 +++
 2 files changed, 9 insertions(+)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
