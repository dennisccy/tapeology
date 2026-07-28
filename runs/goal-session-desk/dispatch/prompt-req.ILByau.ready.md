You are the readme-maintainer agent.

Phase id: goal-desk-iter-12
Target file: README.md (the project-root README of THIS repository)
Agent instructions: .claude/agents/readme-maintainer.md  <-- read this first
Skill: .claude/skills/readme-maintenance.md  <-- the marker-scoped editing method
Run-command source of truth: .claude/project-template.md  <-- Stack, Test commands, Service start commands, URLs
README skeleton (use only if README.md is absent): templates/project-readme.md
Capabilities inputs (read what exists, silently skip what doesn't):
- reports/phase-goal-desk-iter-12-user-visible-changes.md
- reports/phase-goal-desk-iter-12-implementation-summary.md
- reports/phase-goal-desk-iter-12-iteration-summary.md
(CLAUDE.md is already in your system prompt -- do not Read it again.)

Refresh README.md so it reflects the CURRENT project and includes a 'How to run'
section. Edit ONLY the marker-delimited AUTO blocks described in your skill;
never delete human-written prose outside them. Ground every install/run/test
command in .claude/project-template.md — if a needed field is still a template
placeholder (<e.g., ...>), write a 'TODO:' line rather than inventing a command.

When finished, STOP.

Environment note: this pipeline run isolates temp files. Before running tests or any command that writes temporary files, run: export TMPDIR="/home/dennis-chan/.cache/iad/iad.goal-desk-iter-12.154299" TMP="/home/dennis-chan/.cache/iad/iad.goal-desk-iter-12.154299" TEMP="/home/dennis-chan/.cache/iad/iad.goal-desk-iter-12.154299"

Note: your agent definition (the .claude/agents/*.md file named above) is already loaded as your system prompt — do not Read it again; treat its 'read this first' pointer as satisfied.