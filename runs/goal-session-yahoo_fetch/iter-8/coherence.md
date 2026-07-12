# Iteration 8 — Coherence Audit

**Iteration:** goal-yahoo_fetch-iter-8
**Date:** 2026-07-12
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Scope of this iteration (why the check is short)

Confirmed via `git diff 2873e47b35f6411c4ca2b4e4250d4050041a2ba5 -- . <noise-excludes>`: **empty**
— zero change under `apps/` (backend or frontend). The `--stat` of the excluded paths shows the
entire delta lives in `runs/**` (journey-scripts, state bookkeeping, telemetry/trace, dispatch
prompts, iter-7 demo artifacts committed alongside) and `reports/**`/`docs/handoffs/**`. The one
substantive line of the whole diff is:

```
runs/goal-session-yahoo_fetch/journey-scripts/J-06.json
-    {"n": 3, ... "url": "/studies"}, "expect": {"text": "Absorption reversal"}},
+    {"n": 3, ... "url": "/studies"}, "expect": {"text": "Replay studies"}},
```

This matches the iter-8 spec exactly (Mode: next, Depth: lean, "Frontend Present: no," IN SCOPE
= "None — zero product source change" for both backend and frontend, the only listed edit target
being the J-06 golden replay script's step-3 assertion). The dev handoff
(`docs/handoffs/goal-yahoo_fetch-iter-8-dev.md`) and review
(`reports/reviews/goal-yahoo_fetch-iter-8-review.md`, Verdict: PASS) both independently confirm
`git diff -- apps/` is empty and no other file was touched. No `ui-surface-map.md` was produced for
this iteration (consistent with "Frontend Present: no") and none was needed — there is no new UI
surface to map.

This is the blueprint no-op case: "iteration changed no frontend and registered no values (pure
infra/test iteration)."

## Data Contract check

No registered value was touched by new computation, a new endpoint, or a new UI fetch — nothing in
`apps/` changed, so there is no code path to check for duplication. The edited string, "Replay
studies," is not a new displayed value; it is a test assertion added to a golden **replay script**
(harness artifact, not product surface), and it targets a string that already exists verbatim in the
product today — the `/studies` page's own `<h1>` shell title, sourced from
`apps/backend/app/research/taxonomy.py:648` (`STUDY_COPY["title"]`) and rendered in
`apps/frontend/app/studies/page.tsx:114-116` — per the dev handoff's and reviewer's independent
confirmation (including a raw `curl`/`grep` of the SSR HTML). No second computation or second
endpoint was introduced for it.

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| (none touched — zero `apps/` diff) | N/A | `git diff 2873e47b...` → empty for all non-excluded paths |
| "Replay studies" `/studies` title (pre-existing, unregistered decoration, not this iteration's concern) | OK (read verbatim, not recomputed; only a test's *assertion target* changed) | `apps/backend/app/research/taxonomy.py:648`, `apps/frontend/app/studies/page.tsx:114-116` (unchanged by this iteration) |

## Information Architecture check

No new page, route, or feature this iteration — the nav skeleton, `/structure` page, and all other
routes are byte-identical (confirmed by the empty `apps/` diff). Nothing to place in the IA, nothing
to check for reachability or duplicate homes.

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| (none — no new route/page/feature) | N/A | n/a — `apps/frontend/components/NavBar.tsx` and the route tree are unchanged per the diff |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- None. The one line this iteration changed swaps a golden-script assertion from a
  taxonomy-owned-but-async-rendered data string to a taxonomy-owned, statically-rendered shell
  title — it does not introduce a hardcoded frontend literal, a new computed value, or a second
  source of truth, so it is consistent with (rather than a drift from) the blueprint's Data
  Contract discipline. Purely a test-harness fix; no coherence concern.
