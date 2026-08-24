# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

(no changes)

## Excluded-path stat (dependency/lockfile visibility)

 .../state/assumptions.md                           | 83 +++++++---------------
 .../state/assumptions.md.archive.md                | 61 ++++++++++++++++
 .../state/blueprint.md                             | 22 ++++++
 .../goal-session-rapid-microscope/state/lessons.md | 21 +-----
 .../state/lessons.md.archive.md                    | 30 ++++++++
 runs/goal-session-rapid-microscope/telemetry.jsonl | 15 ++++
 .../trace/trace.jsonl                              |  3 +
 7 files changed, 158 insertions(+), 77 deletions(-)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
