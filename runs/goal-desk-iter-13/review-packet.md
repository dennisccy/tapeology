# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 1. Shown in full: 1.

```diff
diff --git a/README.md b/README.md
index 93676a0..664ffc1 100644
--- a/README.md
+++ b/README.md
@@ -109,7 +109,8 @@ git subtree push --prefix incredible_auto_dev auto_dev main
 - Python 3.12+
 - Node.js (for Next.js frontend)
 - A Python virtual environment at `apps/backend/.venv/` (stdlib `venv`, or `uv`, which is pip-compatible)
-- (Optional) Alpaca API credentials in environment for real-data modes (`ALPACA_API_KEY`, `ALPACA_API_SECRET`); without them the app runs simulator-only.
+- (Optional) Alpaca API credentials in environment (`ALPACA_API_KEY`, `ALPACA_API_SECRET`) enable the cockpit's Live and Historical tape-reading modes; without them those two modes report "provider unavailable" and the cockpit runs Simulated-only.
+- No credentials needed for the Structure or Desk pages — their real price history, levels, and screens are fetched from Yahoo Finance for free, with no account or API key required.
 
 ### Install
 
```

## Excluded-path stat (dependency/lockfile visibility)

 .../dispatch/prompt-req.ILByau.ready.md            | 25 ----------------------
 runs/goal-session-desk/telemetry.jsonl             |  7 ++++++
 runs/goal-session-desk/trace/trace.jsonl           |  3 +++
 3 files changed, 10 insertions(+), 25 deletions(-)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
