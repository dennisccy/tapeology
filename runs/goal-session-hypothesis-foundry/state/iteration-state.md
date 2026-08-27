# Iteration State — hypothesis-foundry

**After iteration:** 6 · **Date:** 2026-08-27 · **Verdict:** CONTINUE

## Journeys

7 passing (J-01..J-07) · 1 failing (J-08) — 8 total

## Active blockers

- **COHERENCE-FAIL (dev, freeze-boxed):** `frozen_ready_total` has two owners — `micro_routes.py:901`
  (`variant_count`) vs `scripts/run_hypothesis_foundry_real_exhaust.py:225` (`len(variants)`). The CLI
  is SEALED so the auditor's fix is illegal. Legal route: one owner in a NON-sealed module called by
  `micro_routes.py` + a test pinning the sealed CLI's line to it; else stop and ask the owner.
- **FREEZE BOUNDARY (binding):** the 59 files in `docs/hypothesis-foundry/freeze-set.json` are
  sealed since the first-read lock (06:55:51Z); sha256s pinned in the immutable `epoch_open` row.
  NOT sealed: `micro_routes.py`, `apps/backend/tests/`, `qa_playbook_*.sh`, all frontend.
- **J-08 (dev):** era's last journey — final-truth surface, drill-ins, zero-survivor state, the
  `withheld_excluded = 80` count J-07 omits, T-9/T-10/T-11 guards. Touches no sealed file.
- **OWNER (3 rulings; era cannot close without them):** ratify/reject the discarded first real epoch;
  accept the duplicated count or sanction breaking the seal; accept the page-load lock-file write.
  Ledger: total=4 / resolved=1 / blocking=3 / non-blocking=0 / critical=0.
- **PERMANENT, unfixable (record in closure):** B2 — no §8.5 runtime-environment metadata on the
  epoch-opening row; B3 — nothing re-verifies the ledger chain (chain clean, 1 row).

## Last 2 verdicts

- iter 6: CONTINUE — J-07 done and evaluator-verified end to end (one `epoch_open` row, real-corpus
  hash `da7488f8…` independently recomputed = MATCH, seal repairs B1/B2/B7 closed), but coherence
  FAILED on a duplicate computation whose fix site is now sealed.
- iter 5: ESCALATE — the one real epoch was frozen (zero candidates, an honest valid ending).

## Do not redo

- Real epoch frozen/one-way: `epoch:afd19e9c11a6534f`, registry+manifest byte-identical since
  `dff64eaa`. Never regenerate; never write a second first-read lock.
- Seal bookkeeping B1/B2/B7 closed: 59 relative-path entries, all bytes at `freeze_commit 5b41d9ef`
  (ancestor of HEAD), `era_open_evidence_class_contract` present. Manifest-store deletion bypass
  closed too (`ManifestStoreMissingError`, TC-7 + positive control).
- J-01..J-07 replay green. J-07's proof = `.../iter-6-evidence/UT-02-result.png`, NOT the QA report's own citations (one blank image reused 4x — audit T1).
