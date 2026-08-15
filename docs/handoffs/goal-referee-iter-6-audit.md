# goal-referee-iter-6 Audit Report

**Date:** 2026-08-15
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

J-05's mechanism is genuinely built, not staged: four append-only stores with no update/delete
method, a family definition frozen at first sighting with structural membership enforcement, a
DST-correct boundary that reuses `referee_evidence._et_session_date` rather than re-deriving it,
post-boundary filtering on `session_date` (never `recorded_at`, per spec §5's deep-backfill
clause), and an accrual fold pooled through the shared T-6 primitives on a single `PlaybookStore`
scan. But the boundary the whole journey exists to make immutable was **caller-choosable through
the shipped POST route**: `RetroactiveBoundary` bolted the front door (`confirmation_start_boundary`)
while a sibling field on the same request (`registered_at`) let a caller backdate the boundary to
any date — proven live, with three pre-existing historical sessions then accruing as post-boundary
confirmation, into an append-only record with no delete path. That is fixed here, along with a
partial-write on the duplicate-hypothesis refusal path, both with regression tests. Full suite
after the fixes: 2595 collected / 2587 passed / 0 failed / 8 skipped.

---

## 2. Findings

### Backend Findings

**B1 — CRITICAL (fixed): the immutable boundary was caller-choosable via `registered_at` — the
`RetroactiveBoundary` refusal was bypassable through a sibling field on the same request**

`referee_routes.py:289` exposed `registered_at: Optional[str]` on the registration body and
`:304` forwarded it verbatim into `register_hypothesis`, where `referee_registry.py:660`
(`registered_at = payload.get("registered_at") or _iso_utc_now()`) makes it the sole input to the
boundary derivation. The operator CLI carried the same knob (`referee_registry.py:884`,
`--registered-at`, help text "testing only", writing to the operator's REAL registry dir).

Verified live against the running app before the fix (probe via `TestClient`, isolated tmp stores,
three historical `capitulation:long` playbook sessions planted at 2025-03-03/04/05 **before** the
registration):

```
POST /research/desk/referee/registry/hypotheses {"registered_at": "2025-01-01T00:00:00Z", ...}
  -> 200
  stored confirmation_start_boundary: 2024-12-31
GET  /research/desk/referee/registry
  -> accrual: {"informative_post_boundary_sessions": 3, "target_sessions": 12, "is_proxy": true}
```

Three consequences, each independently disqualifying: (a) the phase GOAL's "immutable boundary
date derived **honestly from the registration instant**" is not enforced — the caller names the
instant; (b) TC-4 / `RetroactiveBoundary` — the iteration's own anti-backdating check — is
trivially defeated by using the other field; (c) the era's critical anti-goal "the historical
atlas is exploratory forever… no historical observation is ever counted as forward confirmation"
is breached, demonstrably, and lands in an append-only record that J-06's adjudication and J-08's
certificate will later read as a legitimate pre-registration. The same field also produced an
unhandled `ValueError` → **HTTP 500** on a malformed value (`{"registered_at": "garbage"}`),
where the spec requires a distinct honest refusal.

The irony is documented in the iteration's own `state/assumptions.md` iter-6 entry, which reasons
carefully that honoring a *later* `confirmation_start_boundary` "would let an operator quietly
choose a later start date than their registration instant actually earned" — the identical
argument that was never applied to the field that actually sets it.

**Fix applied.** `registered_at` removed from `RefereeHypothesisRegistrationRequest`
(`referee_routes.py`), so the POST surface cannot express it; `--registered-at` and its payload
key removed from the CLI (`referee_registry.py`). The payload-level override survives as a
hermetic **test seam only** (TC-8's 23:30-ET fixture needs it); no operator-reachable surface can
reach it. `referee_registry.py`'s module docstring corrected — it claimed the "after" case is
"refused as `RetroactiveBoundary`" and that an equal value is "honored", when the code refuses
`override <= computed` and ignores anything later. Post-fix probe:

```
POST {"registered_at": "2025-01-01T00:00:00Z"} -> 200, boundary 2026-08-15 (today, ET),
                                                  accrual informative_post_boundary_sessions: 0
POST {"registered_at": "garbage"}              -> 200 (field not part of the API), no 500
```

Regression tests added: `test_post_cannot_backdate_the_boundary_via_a_caller_supplied_registered_at`
(asserts the stored boundary equals today's ET date and that three planted historical sessions
accrue **zero**) and `test_cli_register_has_no_registered_at_backdating_flag` (argparse exit 2).
Both fail against the pre-fix code. TC-13 was rewritten to establish CLI/POST byte-identity by
freezing the shared server clock (`_iso_utc_now`) instead of handing both paths an instant —
the stronger property, and the only one still available once neither surface can name the instant.

**B2 — IMPORTANT (fixed): a duplicate `hypothesis_id` under a new `family_id` wrote a permanent
phantom FAMILY record behind the refusal**

The iteration spec lists duplicate `hypothesis_id`/`family_id` as a refusal class with "**no record
written**". In `register_hypothesis` the family write (`referee_registry.py:672-680`) ran before
the hypothesis write (`:715`), so the one ordering where the family is NEW and the hypothesis id
already exists appended the FAMILY record and only then raised. Verified pre-fix:

```
families after 1st registration: ['fam-probe']
refused as expected: HypothesisAlreadyRecorded
families AFTER the refusal:      ['fam-probe', 'fam-probe-v2']   <- written behind a refusal
```

Realistic path: the family-consistency check refuses reusing a `family_id` with a different `q`,
so the natural operator retry is "same hypothesis, new family id" — which lands exactly here. The
store is append-only with no delete, so every such retry permanently pollutes the BH-denominator
record set. Every existing refusal test uses a fresh family whose creation is blocked *earlier* in
the sequence, which is why review (`spec_alignment: complete`) and QA ("store-listing before/after
verification") both read clean.

**Fix applied.** A duplicate-`hypothesis_id` pre-check now runs immediately after the confirm gate
and before any write; the store's own raise stays as the backstop. Regression test:
`test_duplicate_hypothesis_id_under_a_new_family_id_writes_no_family_record` (asserts
`[f["family_id"] for f in families] == ["fam-b2"]` — no phantom). Post-fix probe shows
`families AFTER the refusal: ['fam-probe']`.

**B3 — GAP (not fixed): `WithdrawalStore.record()` reports a corrupted withdrawal file as
"already withdrawn"** — `referee_registry.py:436-441` only checks `path.exists()`, unlike
Family/Hypothesis/Certificate stores which load-then-raise `RegistryIntegrityError`; it also
declares `-> dict` while returning `None`. Fail-closed (the withdrawal is refused either way), so
no data harm — but the operator is told the wrong reason, and `list()` drops the file so the
folded `status` reads `active` while a withdrawal file exists on disk. Matches the reviewer's
MINOR issue #2; fixing it is a store-shape change beyond this audit's remit.

**B4 — GAP (not fixed): `registry_response()` discards all four stores' `integrity_errors`** —
`referee_registry.py:819-822` unpacks `_family_errors`/`_hypothesis_errors`/`_withdrawal_errors`/
`_certificate_errors` and drops them. A corrupted hypothesis file therefore vanishes silently from
`GET /registry` in an era whose own T-6 convention is to disclose mismatches, never to fold them
away. The family record still carries `candidate_hypothesis_ids`, so the BH denominator m is not
shrunk by this — the harm is invisibility, not arithmetic. Not fixed: the four-key GET shape is
pinned in `state/blueprint.md`, so a fifth key would breach the contract; a log warning (the
reviewer's NOTE #3) is the non-breaking option for J-06 to carry.

**B5 — OBSERVATION (not fixed): three dead imports** — `sys` (`referee_registry.py:88`), `Config`
(`:92`), `resolve_desk_playbook_dir` (`:93`) are never referenced. The reviewer's
`no_dead_code: fail`. Unchanged by this audit (still dead after my edits).

**B6 — OBSERVATION (not fixed): `_resolve_boundary` compares the override as a string** —
`referee_registry.py:600` (`override <= computed`) means a non-date string such as `"not-a-date"`
sorts above any ISO date and is silently ignored rather than refused. No integrity impact (the
stored value is always the computed one), but it is a refusal class that quietly does not fire.

### Frontend Findings

None — zero frontend files changed (`git status --porcelain` shows only backend `.py` files plus
docs/runs artifacts). `Frontend Present: no` is correct for this iteration; J-09 remains the
registry's first UI reveal.

### Test Findings

**T1 — GAP (not fixed): TC-15's "hand-verified" subset is not hand-verified** —
`tests/test_referee_null.py` builds its expectation by calling the production selector itself
(`expected_drawn = _draw_anchor_indices(stream, 7, 4)`), so a deterministic-but-incorrect selector
(e.g. an off-by-one in the Fisher–Yates walk) passes. What the rider *does* genuinely establish,
and what iteration 5's lesson actually asked for, is real: `eligible_count == 7 > K == 4` so the
degenerate "draw all of them" case no longer masks the RNG; the repeat draw is identical; a
different observation key draws a different subset; and `assert expected_indices != [1, 2, 3, 4]`
kills a selector that ignores the stream. Residual: the drawn subset is not pinned to a literal.
One-line follow-up for J-06 — replace the re-derivation with the observed 4-element literal.

**T2 — OBSERVATION: the store-scope gate's pinned baseline is stale** — the DoD/TC-20 cite
"11,274 files at the last recorded count"; the live tree holds 11,305, a delta accumulated
*before* this iteration. The meaningful property was verified directly instead: only two files
under `apps/backend/.data/` have mtimes after the iteration start (07:40Z) — `dataset_index.db-wal`
(0 bytes) and `dataset_index.db-shm` — exactly the SQLite sidecars the dev handoff disclosed, from
the unmodified `/evidence` route. No `.json` record was created or modified, and
`find .data -iname "*referee_registry*"` returns nothing (no real registration touched production).

**T3 — GAP: DoD item 2 (required-still-passing journeys, "deterministic replay + LLM fallback")
was never exercised this iteration** — `status.json` records `browser_checks_run: false`, the QA
report skips browser checks, `reports/phase-goal-referee-iter-6-ui-test-results.md` reads
`SKIPPED`, and the dev handoff states the J-10 sentinel was not performed. J-05 itself carries no
browser acceptance, so this is not a J-05 failure — but the iteration's own TESTING REQUIREMENTS
ask for J-10's kept-product half to be re-verified "through the standard regression replay + a
fresh screenshot", and nothing did. Code-level mitigation I verified myself: `git diff --numstat`
shows `referee_routes.py` at **125 insertions / 0 deletions** (no existing route body touched) and
`referee_null.py` at 8/1 (the one-line Rider 1 fix plus its comment), with zero frontend diff — so
the regression risk is confined to `GET /nulls`' `backing_bucket_eligibility_rate` field, which is
the spec-mandated rider and is covered by two new tests including a can-fail counter-test. The
replay lane should still run before the iteration closes.

---

## 3. Domain Assessment

The statistical-integrity core is sound and, unusually for a first cut, not stubbed anywhere.

- **Boundary derivation** genuinely reuses `referee_evidence._et_session_date` (no second DST
  implementation), and TC-8 samples the regime that actually breaks a naive version: 23:30 ET on
  2026-06-22 → 03:30 UTC 2026-06-23, asserted to store `2026-06-22`. The fixture is chosen where
  the bug would live, per the carried iter-3/iter-4 lesson.
- **Post-boundary admission is on `session_date`, never `recorded_at`** (`_hypothesis_accrual`,
  `referee_registry.py:773-775`), which is spec §5's explicit deep-backfill clause. TC-11
  counter-tests it by construction: every playbook record is planted *after* the registration
  call, and the pre-boundary date still does not count.
- **Accrual is a disclosed proxy, not a competing computation.** It walks the same
  `_newest_per_session_date` map through the same `_is_stale_basis` T-6 predicate that
  `playbook_occurrence_readiness()` uses, on **one** `PlaybookStore.list()` per GET shared across
  every hypothesis, and counts a strict subset (boundary-filtered) of the same pooled population.
  Served with `is_proxy: true` and `basis_current`. No single-source-of-truth violation.
- **"No candidate joins a family retroactively" is structural**, not documentation: membership in
  `family_candidate_hypothesis_ids` is checked at registration, and a family's `q`/candidate list
  must match its recorded values exactly on every later call. **Immutability is structural too** —
  `dir()`-asserted `{root, get, list, record}` on all four store classes.
- **Withdrawal** refuses on the injected `post_boundary_evaluation_exists` signal, on an unknown
  id, and on a second attempt, and never mutates the hypothesis record — the injectable-signal
  design is the honest choice given no evaluation store exists until J-06.
- The `null_spec_id`-only-for-A/C interpretation call is substantively right (spec §3.2 defines
  Estimand B as cell-vs-complement with no null population; §7's S-4 row names none) and — contra
  the dev handoff's own Known Issue #2, which says it was "not logged" — it **is** recorded in
  `runs/goal-session-referee/state/assumptions.md`'s iter-6 entry. The handoff line is stale; the
  artifact is correct.

What was wrong was never the statistics — it was the **provenance of the instant** the whole
immutable boundary derives from. That is what B1 fixes.

---

## 4. Fixes Applied During This Audit

| # | Severity | File | Change |
|---|----------|------|--------|
| 1 | Critical | `apps/backend/app/research/referee_routes.py` | Removed `registered_at` from `RefereeHypothesisRegistrationRequest` so the POST surface cannot express a caller-chosen registration instant; docstrings state why the instant is server-stamped |
| 2 | Critical | `apps/backend/app/research/referee_registry.py` | Removed the CLI `--registered-at` flag and its payload key (same hole, operator surface); corrected the module docstring, which misstated both the override semantics and which surfaces expose it |
| 3 | Important | `apps/backend/app/research/referee_registry.py` | Duplicate-`hypothesis_id` pre-check placed before the family write, so a refused registration writes no FAMILY record |
| 4 | — (test) | `apps/backend/tests/test_referee_registry.py` | TC-13 now freezes the shared server clock instead of passing an instant to both paths; +3 regression tests (POST cannot backdate and accrues zero historical sessions; CLI flag gone; no phantom family behind a duplicate refusal) |

**Verification of these fixes**

- `.venv/bin/python -m pytest tests/test_referee_registry.py` → **35 passed, 0 failed** (32 dev
  tests + 3 audit regressions).
- Full suite `.venv/bin/python -m pytest tests/ --junit-xml=…` → **2595 collected / 2587 passed /
  0 failed / 8 skipped** in 250.6s (exit 0) — exactly +3 over the dev/QA run (2592/2584/8), i.e.
  my three regression tests and no collateral breakage. Comfortably above the iter-5 floor.
- Re-ran the referee + MCP modules after the docstring edit →
  `tests=215 failures=0 errors=0 skipped=0`.
- `Config().config_fingerprint()` → `08e471b10130e1e2` (unchanged). `EXPECTED_TOOLS` parsed by AST
  → **20** names.
- The independent pre/post probe transcripts quoted in B1/B2 are the primary evidence that each
  fix changed the real behavior, not just the tests.
- Diff self-review: my changes are confined to the two fixed defects plus the docstring they
  invalidated; nothing else was touched. `apps/backend/.data/` remains untouched by this audit
  (only the two disclosed WAL sidecars post-date the iteration start; `-wal` is 0 bytes).

---

## 5. Recommended Next Step

**Proceed to J-06**, carrying four documented items:

1. **B4 first** — J-06 is the first code that reads the registry for adjudication; it should not
   inherit a read path that silently drops corrupted records. A log warning keeps the pinned
   four-key contract intact.
2. **B3** — mirror the other three stores' load-then-raise in `WithdrawalStore.record()` and fix
   its `-> dict` annotation.
3. **T1** — pin TC-15's drawn subset to a literal so the seeded selector is verified, not merely
   re-executed.
4. **T3** — run the deterministic replay for the required-still-passing journeys before this
   iteration is treated as closed; it is the one DoD checkbox no artifact in this run evidences.

B5/B6 are cosmetic and can ride along with any future edit to the module. Nothing here blocks the
era; the registry's append-only identity layer is now genuinely a commitment device rather than a
record of whatever instant the caller preferred.
