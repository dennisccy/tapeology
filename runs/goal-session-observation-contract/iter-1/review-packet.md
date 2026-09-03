# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 1. Shown in full: 1.

```diff
diff --git a/apps/backend/app/engine/tape_engine.py b/apps/backend/app/engine/tape_engine.py
index 121abc64..a513d911 100644
--- a/apps/backend/app/engine/tape_engine.py
+++ b/apps/backend/app/engine/tape_engine.py
@@ -29,6 +29,14 @@ from .snapshot import EngineSnapshot, TradeRow
 # research type, so logging a failure leaks no research concept into the engine.
 logger = logging.getLogger(__name__)
 
+# The engine's SEMANTIC identity (Observation Contract v1, Constitution §6/§7): bumped ONLY by
+# an explicit owner act when classifier, feature, aggressor or warm-up semantics change -- never
+# by an automated inference. `app/observation_contract.py`'s `engine_identity.engine_semantics_
+# version` reads this constant verbatim (never a second copy). It is distinct from
+# `implementation_provenance.engine_source_hash` (exact source bytes, changes on comment edits
+# too): a changed source hash never by itself claims a semantic change.
+ENGINE_SEMANTICS_VERSION = "tape-engine-v1"
+
 
 class TapeEngine:
     def __init__(
```

## Excluded-path stat (dependency/lockfile visibility)

 .../goal-session-observation-contract-index.html   | 11 +++--
 reports/qa-scoped-backend-store-manifest.md        | 26 +++++------
 .../.engine.lock/boot_id                           |  2 +-
 .../.engine.lock/epoch                             |  2 +-
 .../.engine.lock/pid                               |  2 +-
 .../dispatch/.pump-alive                           |  4 +-
 runs/goal-session-observation-contract/engine.pid  |  2 +-
 .../goal-session-observation-contract/session.json |  6 +--
 runs/goal-session-observation-contract/summary.md  | 54 ++++++++++++++++++++--
 .../telemetry.jsonl                                | 45 ++++++++++++++++++
 .../trace/trace.jsonl                              |  3 ++
 11 files changed, 127 insertions(+), 30 deletions(-)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
