# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

(no changes)

## Excluded-path stat (dependency/lockfile visibility)

 reports/goal-session-rapid-microscope-index.html   |   4 +-
 .../dispatch/.pump-alive                           |   4 +-
 runs/goal-session-rapid-microscope/session.json    |   6 +-
 .../state/assumptions.md                           | 151 ++++-----------------
 .../state/assumptions.md.archive.md                | 126 +++++++++++++++++
 .../state/blueprint.md                             |  12 ++
 .../goal-session-rapid-microscope/state/lessons.md |  32 +----
 .../state/lessons.md.archive.md                    |  43 ++++++
 runs/goal-session-rapid-microscope/summary.md      |  12 +-
 runs/goal-session-rapid-microscope/telemetry.jsonl |  19 +++
 .../trace/trace.jsonl                              |   2 +
 11 files changed, 247 insertions(+), 164 deletions(-)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
