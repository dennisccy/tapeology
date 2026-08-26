# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 1. Shown in full: 1.

```diff
diff --git a/project-extensions/host-guard/host-guard.env b/project-extensions/host-guard/host-guard.env
index a9c37ab2..06a6a40d 100644
--- a/project-extensions/host-guard/host-guard.env
+++ b/project-extensions/host-guard/host-guard.env
@@ -53,7 +53,19 @@ HOST_GUARD_CPUQUOTA="1600%"
 # 2026-07-29 (was 14G): 14G + 14G = 28G was over the 27.3G installed, and no
 # per-project check could see that. 10G + 10G = 20G fits the 22G machine budget
 # with ~7G left for desktop/Chrome/page cache.
-HOST_GUARD_MEMORY_HIGH="10G"
+#
+# 2026-08-26 LOWERED 10G -> 6G (owner-authorized). A THIRD guarded project went
+# live (tensteps `ten-steps-v1`, 6G) alongside trendora (12G): 12 + 6 + 10 = 28G
+# exceeded HOST_GUARD_GLOBAL_MEMORY_BUDGET=24G, which paused this session
+# (AWAITING_HOST_GUARD) at the start of the Hypothesis Foundry era. Narrowing
+# THIS project — rather than widening the machine budget past the 26.7G
+# installed, or stopping another project's run — puts the live sum at exactly
+# 12 + 6 + 6 = 24G (the check is strict `>`, so == passes). MemoryHigh throttles
+# and reclaims, never OOM-kills, so the cost is slower heavy computes, not
+# failure; tapeology's heaviest observed worker (edge-report sweep) measures
+# ~3-4G. Raise back toward 10G once trendora or tensteps finishes AND the
+# machine budget still covers the sum.
+HOST_GUARD_MEMORY_HIGH="6G"
 # Fork-storm bound; the whole box normally runs ~1500-1700 tasks in goal mode.
 HOST_GUARD_TASKS_MAX=2048
 
```

## Excluded-path stat (dependency/lockfile visibility)

(no changes in excluded paths)
