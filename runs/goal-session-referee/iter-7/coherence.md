# Iteration 7 — Coherence Audit

**Iteration:** goal-referee-iter-7
**Date:** 2026-08-15
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-WARN

---

## Data Contract check

This is a backend/CLI-only iteration (`Frontend Present: no`) delivering J-06:
`referee_adjudicate.py` (new, 1584 lines) plus three riders on already-owned modules
(`referee_evidence.py`, `referee_registry.py`) and one new export from `referee_null.py`.

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Evaluation records + runs (owner `referee_adjudicate.py`) | OK — first field-level shape of a pre-registered stub; routes match blueprint exactly | `apps/backend/app/research/referee_routes.py:303-402` (`GET /evaluations`, `POST/GET/POST-cancel /evaluate`, `GET /evaluate/runs`) vs. `runs/goal-session-referee/state/blueprint.md:55` |
| Adjudications (snapshots + pending fold) | OK — `adjudications_response()` is the sole computer, mounted at the registered endpoint | `apps/backend/app/research/referee_adjudicate.py:1394-1425`; `referee_routes.py:405-417` vs. `blueprint.md:56` |
| Promotion authorization verdict (`authorize_promotion`) | OK — pure function, correctly left unwired; no second promotion-check path introduced | `apps/backend/app/research/referee_adjudicate.py:1431-1521`; confirmed `pnl_scan.py` untouched (`git status --porcelain`) |
| Stats core (permutation test, BH fold, bootstrap CI, sign-flip, equal-weight, oracle attestation) | OK — single definition site preserved | `grep '^def '` for all 9 names returns exactly one hit each, all in `apps/backend/app/research/referee_stats.py` (223/324/360/416/587/635/650/747/783); zero hits in `referee_adjudicate.py`. The new `_pool_against_null`/`_pool_cell_vs_complement` (`referee_adjudicate.py:324-440`) only gather `(group1, group2)` session dicts and hand off to the imported `_t_statistic` — no reimplementation of the weight formula. |
| Band-context / backing-bucket resolution | OK — single canonical function reused, not reimplemented | `band_context_block` defined once at `apps/backend/app/research/desk_playbook_context.py:457`; the new `resolve_occurrence_backing_bucket` (`referee_null.py:137-162`) imports and calls that same function (`referee_null.py:88,648`) rather than recomputing a bucket independently. `_pool_cell_vs_complement` (`referee_adjudicate.py:407`) calls this new export transitively — the module's own import-topology guard test (`test_referee_guards.py:506-514`) confirms `referee_adjudicate.py` never imports `desk_playbook_context` directly. |
| Registry (families/hypotheses/withdrawals/certificates) — Rider 2's new `integrity_errors` field | OK in code (single computation, canonical endpoint) / STALE in blueprint documentation — see Advisory notes | `apps/backend/app/research/referee_registry.py:824-866` reuses the `get_referee_nulls` `{"records"/"...": [...], "integrity_errors": [...]}` disclosure pattern (not a second shape); `blueprint.md:149-151` still documents the pre-Rider-2 four-key shape |
| Strategy-observation `excluded_missing_epoch_anchor` (Rider 1) | OK — internal disclosure field on the J-02 evidence adapter, single computation site, not independently a served/displayed value | `apps/backend/app/research/referee_evidence.py:793-105` (the only place `epoch_anchor` exclusion is computed); blueprint explicitly registers J-02 as "library module, no page of their own \| n/a — consumed by J-04–J-09" |

No duplicate computation and no non-canonical source found anywhere in this iteration's diff.

## Information Architecture check

No new page/route/feature this iteration. `git status --porcelain` confirms zero files under
`apps/frontend/**` changed — every touched file is backend Python (`apps/backend/app/research/**`)
or a test file. This matches the iteration spec's own declarations verbatim (`Frontend Present: no`;
`### UI surface changes` → `None`; `### Blueprint conformance` → "No new UI surface... unchanged
this iteration"). Nothing to check for nav-reachability, duplicate homes, or parallel shells — Part
B is vacuously satisfied.

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| n/a — no UI surface this iteration | OK | git status shows no `apps/frontend/**` changes |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- **Stale blueprint documentation, and a false handoff claim about it.** Rider 2
  (`apps/backend/app/research/referee_registry.py:824-866`) adds a fifth `integrity_errors` key to
  `GET /research/desk/referee/registry`'s response. `runs/goal-session-referee/state/blueprint.md`
  lines 149-151 (the iter-6 note documenting that response's shape) still show only the original
  four keys (`families`, `hypotheses`, `withdrawals`, `certificates`) — I confirmed this directly by
  reading those lines and by `grep -c integrity_errors runs/goal-session-referee/state/blueprint.md`
  returning zero matches anywhere in the file. `docs/handoffs/goal-referee-iter-7-dev.md:102`
  explicitly claims "the four-key GET shape pinned in `state/blueprint.md` is now five keys —
  updated as part of this fix" — that claim is factually false; no such edit exists in the working
  tree or in `git status`. The reviewer already caught and filed this independently
  (`reports/reviews/goal-referee-iter-7-review.md:22-33`, severity MINOR/standards) with the same
  fix I'd recommend. This does **not** rise to a Part A FAIL: the Data Contract's actual table row
  (owner `referee_registry.py`, endpoint `GET /research/desk/referee/registry`) is unchanged and
  accurate, no value is computed twice, and nothing is served from a non-canonical source — only a
  descriptive sub-note beneath the table is out of date, exactly the class of drift the
  iter-4/5/6 notes' own "field addition, not a new value or a new canonical source" convention
  already treats as routine. Left uncorrected across further iterations, though, a future
  decomposer skimming only that note could wrongly conclude the registry endpoint has no
  integrity-error disclosure and build a second, parallel one — so it is worth fixing promptly, not
  indefinitely deferring. **Fix (one-line doc edit, no code change):** amend `blueprint.md:149-151`
  to `GET /research/desk/referee/registry response: {families: [...], hypotheses: [...],
  withdrawals: [...], certificates: [...], integrity_errors: [...] (iter-7 Rider 2)}`, or append a
  short "iter-7 rider note" beneath the existing iter-6 note; either satisfies the contract. Also
  correct or retract the false claim in the dev handoff prose.
- Reviewer's own NOTE-severity item (`referee_adjudicate.py:990` — a `BandMapResolver` constructed
  for both estimands "B" and "C" when only B's pooling path reads it) is a harmless code-quality nit
  (`compute=False`, no side effects, no duplicate computation) — not a coherence issue, mentioned
  only for completeness.
