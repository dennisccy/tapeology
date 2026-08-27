# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

(no changes)

## Excluded-path stat (dependency/lockfile visibility)

 reports/goal-session-hypothesis-foundry-index.html |   4 +-
 .../.engine.lock/epoch                             |   2 +-
 .../.engine.lock/pid                               |   2 +-
 runs/goal-session-hypothesis-foundry/engine.pid    |   2 +-
 runs/goal-session-hypothesis-foundry/session.json  |  11 +-
 .../state/assumptions.md                           | 179 -------------------
 .../state/lessons.md                               |  63 +------
 runs/goal-session-hypothesis-foundry/summary.md    | 195 ++++++++++++++++++++-
 .../telemetry.jsonl                                |  19 ++
 .../trace/trace.jsonl                              |   3 +
 10 files changed, 226 insertions(+), 254 deletions(-)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
