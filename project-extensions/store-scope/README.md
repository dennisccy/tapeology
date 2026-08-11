# Store-scope guard — the QA lanes cannot reach the operator's real store

## Why this exists

`goal-playbook-iter-8` shipped a launcher — `apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh`
— that stands up a fully fixture-scoped backend (own bars, own universe, own playbook/ledger dirs,
own caches) so a browser pass can click **Run Playbook** or **Run Backscan** without touching
`apps/backend/.data/`. The launcher was correct. Nothing was obliged to use it.

In that same iteration's own pipeline run, the deterministic replay lane replayed J-07 — whose
golden contains a real "Run Backscan" click — against whatever was listening on the QA port: the
operator's ambient backend. It computed three real S&P-100 playbook records and appended a back-scan
run-ledger row:

```
apps/backend/.data/playbook/playbook-2026-06-22-fc4182ae9bb8.json          14:45:30
apps/backend/.data/playbook/playbook-2026-06-23-e496c53902bc.json          14:45:45
apps/backend/.data/playbook/playbook-2026-06-24-e5f41a0c720e.json          14:45:47
apps/backend/.data/playbook_backscan_runs/backscanrun-2026-08-11-…json     14:45:47
```

Those files are append-only by the project's own immutable-data rail, so they stay. The audit's
verdict on the deliverable was exact: **the fix was a launcher, not a mechanism.** This directory is
the mechanism.

## What it does

`store-scope.env` is read by the framework guard
(`incredible_auto_dev/scripts/automation/store-scope/store-scope.sh`), which the goal-mode browser
lanes call around every run — `browser-qa-phase.sh` at full depth and `goal-iter-lean.sh` at lean:

| Phase | Call | Effect |
|-------|------|--------|
| Before any lane | `store_scope_require` | Runs `assert_scoped_qa_backend.py`. If the QA backend is not the fixture rig it runs `start_scoped_qa_backend.sh` once and re-asserts. Still not scoped ⇒ **neither the replay lane nor the LLM browser dispatch runs at all** (journeys are tokenised `pending-infra`, never reported as verified). |
| Before any lane | `store_scope_snapshot` | Manifest (size + mtime) of every file under `STORE_SCOPE_PROTECTED_PATHS`. |
| After the lanes | `store_scope_verify` | Re-scans and hard-fails on ANY delta — added, removed, or modified — writing `reports/qa/<iter>-store-scope-guard.md` either way, plus a loud section in the authoritative `ui-test-results.md` and a `store_scope_breach` telemetry event on a breach. |

The disclosure artifact is the point: "the operator's store was untouched" stops being a sentence in
a report and becomes an executed check with a file list behind it.

## The two project-owned commands

* **`apps/backend/scripts/assert_scoped_qa_backend.py`** — reads `GET /research/desk/universe` and
  requires the LATEST snapshot's `source_url` to start with `fixture-rig`. Every fixture seeder
  registers its universe that way; a real fetch registers the Wikipedia S&P-100 URL. Anything it
  cannot prove (no snapshot, unreadable body, connection refused) is **not scoped**. Unit-tested in
  `apps/backend/tests/test_qa_scoped_backend_guard.py`.
* **`apps/backend/scripts/start_scoped_qa_backend.sh`** — frees the QA port (recording the replaced
  process's command line in `<log-dir>/replaced-listener-<port>.txt` so the operator can restart it
  verbatim),
  seeds a fresh scoped root through the one mandatory launcher, and waits for `/health`.

## Running it by hand

```bash
bash incredible_auto_dev/scripts/automation/store-scope/store-scope.sh require
bash incredible_auto_dev/scripts/automation/store-scope/store-scope.sh snapshot /tmp/base.manifest
#   … browser / replay work …
bash incredible_auto_dev/scripts/automation/store-scope/store-scope.sh verify /tmp/base.manifest \
     reports/qa/<iter>-store-scope-guard.md
```

## What is deliberately NOT protected

The derived accelerator DBs (`bar_index.db`, `*_meta_cache.db`, `tradability_cache.db`,
`setups_scan_cache.db`, `edge_report_*.db`, `playbook_evidence_cache.db`, `journal.db`). They are
stat-keyed projections that own nothing and are rebuilt on demand, and a legitimate read path
updates them. Listing them would make every clean run a false breach — and a guard that cries wolf
is a guard the next reader ignores.
