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
