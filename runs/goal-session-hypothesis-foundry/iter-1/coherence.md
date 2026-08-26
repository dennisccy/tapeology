# Iteration 1 — Coherence Audit

**Iteration:** goal-hypothesis-foundry-iter-1
**Date:** 2026-08-26
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Data Contract check

Blueprint rows 1-3 (era/session identity + era-open baseline; source dispositions; `CandidateSpec`
+ hash) are the only rows this iteration's "Iteration note" and the spec's "Data-contract
additions: None" claim to finalize. Verified against the diff:

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Era/session identity + methodology/spec version + era-open baseline block | OK | Computed once in `apps/backend/app/research/foundry_source_registry.py` (`foundry_era_identity()`, `record_era_open_baseline()`/`read_era_open_baseline()`) — the exact module the blueprint row 1 names. Served only by the new `GET /research/desk/micro/foundry` (`apps/backend/app/research/micro_routes.py:752-766`). Frontend fetches only that URL — `apps/frontend/lib/api.ts:2795` (`fetch(\`${API_BASE}/research/desk/micro/foundry\`)`) — and renders every field verbatim in `HypothesisFoundrySection` (`apps/frontend/app/desk/page.tsx:7367-7461`), no client-side derivation. |
| Source dispositions / closed §7.1 vocabulary / compile precedence | OK | `apps/backend/app/research/foundry_source_registry.py:924-941` (`compile_source_disposition`) — matches blueprint row 2's named module exactly. Not yet served to the UI this iteration (deferred by design, per goal.md Binding Execution Order step 5) — no second fetch/compute path exists for it. |
| `CandidateSpec` + `candidate_spec_hash` | OK | `apps/backend/app/research/foundry_compiler.py:601-689` (`compile_sources`) — matches blueprint row 3's named module. Hash computed once in `CandidateSpec.compute_hash()`/`with_hash()`; no second hashing implementation found. Not yet served to the UI this iteration. |
| `config_fingerprint` (embedded field inside the new baseline bundle) | OK | Read live from the existing canonical `CONFIG.config_fingerprint()` (`apps/backend/scripts/record_foundry_era_open_baseline.py:56`) — the same singleton every other `/desk` section already embeds per-record (`page.tsx:3523,3556,7282,9855` from prior eras). This is the established per-record-snapshot pattern in this codebase, not a new independent computation. |
| Referee-module SHA-256 hashes | OK | Computed once in `record_era_open_baseline()` (`foundry_source_registry.py:1019-1054`) via a fixed 6-module list; grepped the rest of `apps/backend/app/research` for any pre-existing hashing of these same six files — none found, so this is not a duplicate of an existing computation. |

No new displayed value falls outside these three rows — every field in `DeskFoundryResponse`
(`apps/frontend/lib/types.ts:2967-2993`) traces to blueprint row 1's "era-open baseline (full-suite
pass/skip/failed counts, config fingerprint, SHA-256 of each of the six referee_*.py modules)"
bundle. No unregistered-value WARN needed.

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| Hypothesis Foundry panel header on `/desk` | OK | `apps/frontend/components/NavBar.tsx` is untouched this iteration (confirmed via `git diff` — no hits) — no new top-level route was introduced, matching the blueprint's "Foundry adds no new top-level route." The new `<section aria-label="Hypothesis Foundry">` (`page.tsx:12836-12851`) reuses the page's existing `CollapsibleSection` component and `expandedSections`/`toggleSection` state — the same accordion pattern every other Desk section already uses — rather than inventing a parallel shell. Reachable in 1 click (top-level `Desk` nav link, unchanged) + 1 click (expand the accordion) = ≤2 clicks, matching blueprint row "J-01 ... → `/desk` → Hypothesis Foundry panel header". Not a duplicate home — this is a genuinely new panel, no prior `/desk` section covers Foundry era identity. |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- The reviewer (`reports/reviews/goal-hypothesis-foundry-iter-1-review.md`) flagged a MINOR,
  non-coherence spec-accuracy issue: `SourceRecord` (`foundry_source_registry.py:854`) omits two
  §1.4 fields (`source_hash`, `alternatives`) that `docs/hypothesis-foundry-spec.md` §1.4 claims
  the dataclass mirrors "verbatim." This is a documentation-completeness gap, not a coherence
  violation — no duplicate computation or non-canonical fetch results from it, and no TC depends on
  it. Left for a future iteration (before J-06) per the reviewer's own note.
- Rows 2 and 3 of the Data Contract (source dispositions, `CandidateSpec`) are implemented and
  tested but intentionally not yet served through any UI this iteration — this is the
  decomposer's stated, in-scope deferral (Binding Execution Order step 5), not a gap this auditor
  needs to flag.
