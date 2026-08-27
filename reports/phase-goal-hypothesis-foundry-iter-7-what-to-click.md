# Phase goal-hypothesis-foundry-iter-7 — What to Click (Operator Verification Guide)

**Status:** N/A — Backend-only phase (Frontend Present: no)

No operator click-through steps to provide. This iteration made no `apps/frontend/**` changes and
introduced no new, removed, or differently-behaving UI element (see the ui-surface-map for this
phase). An operator wanting to sanity-check the served value directly can run:

```
curl http://localhost:8301/research/desk/micro/foundry
```

and confirm `exhaust_progress.frozen_ready_total == 0` — the same value already shown, unchanged,
on `/desk` → Hypothesis Foundry → Runner/Checkpoint from a prior iteration. That existing subsection
needs no re-verification specific to this iteration's diff.
