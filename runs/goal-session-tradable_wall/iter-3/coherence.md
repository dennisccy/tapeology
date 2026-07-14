# Iteration 3 — Coherence Audit

**Iteration:** goal-tradable_wall-iter-3
**Date:** 2026-07-14
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

<!-- COHERENCE-PASS: no objective violations; at most minor advisory notes -->

---

## Data Contract check

J-03 is backend-only (`Frontend Present: no`) and, per its "Data-contract additions" field,
realizes two already-registered rows rather than adding a new one. Verified directly against the
diff (`git diff d95b7d5957fcb086016bd60d38a7fee072c3ceeb`) and the code, not just the spec's claim.

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Touch events / case registry (`compute_setups`) | OK — byte-identical | `apps/backend/app/research/setups.py` diff touches only new code below the existing `compute_setups`; `test_compute_setups_itself_never_touches_the_dataset_store` (`tests/test_setups.py`) statically asserts the shared scan loop is dataset-store-free. `GET /research/setups` (list) route unmodified in `routes.py`. |
| Drill-in `tape_timeline` on `GET /research/setups/{id}` | OK — single computation path | New `enrich_with_tape_timeline` (`apps/backend/app/research/setups.py:376-385`) is called ONLY from `get_setup` (`apps/backend/app/research/routes.py:1892-1907`), never from the list route. It replays via the pre-existing `DatasetStore.replay` (`apps/backend/app/research/datasets.py:268-278`, unmodified — confirmed absent from the diff), which itself constructs the FROZEN `TapeEngine` — never a second engine. Guard test `test_setups_join_reuses_dataset_store_replay_never_a_second_tape_engine` greps the module source for `TapeEngine(` / `TapeStateClassifier` and asserts neither appears. |
| Recorded tick datasets (append-only, checksummed, feed-stamped, split-frozen) | OK — canonical write path reused | New driver `apps/backend/scripts/record_event_windows.py` records exclusively via `POST /research/datasets` (through `TestClient(app)`, `record_event_windows.py:181-185`) — the existing registered endpoint, not a new write path. `record_from_source`/`DatasetStore` (`datasets.py`) are absent from the diff (confirmed via `git diff --stat` against `app/research/datasets.py`, zero changes). |
| Confidence / state fields inside `tape_timeline` entries | OK — re-format, not recompute | `_tape_timeline` (`setups.py:350-373`) reads `snapshot.tape_state`/`snapshot.confidence` verbatim from the `TapeEngine` snapshot stream (the same engine that owns `GET /tape/{ticker}/history`) and only reconstructs the UTC timestamp (`epoch_anchor + logical_ts`, the same scheme `serializers.serialize_history` already uses). No new classification. |
| Split assignment for newly recorded datasets (`split_for_event`) | OK — genuinely new, not a duplicate | Grepped every existing `SPLIT_TRAIN`/`SPLIT_HOLDOUT` use site (`pnl_scan.py`, `pnl_baseline.py`, `edge_report.py`, `pnl_ledger.py`, `generate_dataset_fixtures.py`): all either consume an already-assigned `record["split"]` or hardcode a literal split for two specific era-3 fixtures. No pre-existing "assign a split to a new dataset" algorithm exists to duplicate; this is a new, config-owned, deterministic helper local to the new operator script, not a Data-Contract-registered displayed value. |

No new UI-displayed value is introduced this iteration (`New information displayed` field in the
spec: only the already-registered `tape_timeline`; "No new numeric metric is introduced" — matches
what the diff actually adds).

## Information Architecture check

Zero UI/frontend files are touched (`apps/frontend` absent from `git status`; the UI surface map at
`reports/phase-goal-tradable_wall-iter-3-ui-surface-map.md` states "No UI surfaces affected"). No
new route is added — `GET /research/setups/{id}` already existed and is enhanced internally only.
Its canonical home per the blueprint ("shown inside the Case Studies drill-in (tape timeline)"
under Structure) is unchanged; actual browser rendering is explicitly deferred to J-05, matching
the blueprint row and the iteration's own "Blueprint conformance" field. No IA check applies this
iteration — there is nothing new to place in navigation.

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| `GET /research/setups/{id}` (tape_timeline enrichment) | OK — no new surface, backend-only | N/A — no nav file changed; `reports/phase-goal-tradable_wall-iter-3-ui-surface-map.md` confirms no UI surfaces affected |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- The dev handoff, QA report, and implementation summary characterize the credentialed
  ≥10-window headline as "MET," while the iteration's own auditor report (already written,
  `docs/handoffs/goal-tradable_wall-iter-3-audit.md`, verdict PASS_WITH_GAPS) more skeptically
  scores it `partial`/`unknown` (integration test interrupted before a pytest PASS; the 15
  recorded datasets live in an ephemeral pytest temp dir, not the persistent
  `apps/backend/.data/datasets/` store). This is an evidence-honesty / DoD-completeness question,
  already surfaced and owned by the auditor — it is not a Data Contract or Information
  Architecture violation (no duplicate computation, no second endpoint, no scattered nav), so it
  is out of this gate's scope and is not repeated here as a coherence finding.
- README.md's `<!-- AUTO:capabilities -->` block gained a new "Touch-event scanner and case-study
  registry" bullet describing J-02's (prior iteration's) capability, only now during iter-3. This
  is the routine readme-maintainer catch-up (non-blocking showcase step) and accurately describes
  already-shipped capability — not a new surface, not a coherence concern.
