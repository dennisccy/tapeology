# Iteration 1 — Coherence Audit

**Iteration:** goal-referee-iter-1
**Date:** 2026-08-14
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| "Referee evidence coverage + per-family readiness" (blueprint row) | OK | `apps/backend/app/research/referee_evidence.py:267-281` (`referee_evidence()`, the owning module) serves `apps/backend/app/research/referee_routes.py:320-338` (`GET /research/desk/referee/evidence`), mounted `apps/backend/app/main.py:205-207`. Owner + endpoint match `blueprint.md:51` verbatim. |
| New `detector_basis` field vs. existing `playbook_input_signature` | OK — not a duplicate | Checked directly for a near-miss: `referee_evidence.py:147-153` (`current_playbook_detector_basis`) hashes ONLY `sha256(canonical(playbook_parameters()))[:16]`. The pre-existing `desk_playbook.py:345-358` (`compute_playbook_input_signature`) additionally hashes bar-series `(symbol, timeframe, id, checksum)` tuples + `config_fingerprint`. Different formula, different value, deliberately (module docstring explains the pooling-stability rationale, verified against the actual source, not just the comment). |
| New `strategy_trade.dataset_count` vs. pre-existing `edge_report.py` `dataset_count` field | OK — same canonical source, no divergence risk | Checked directly for a near-miss: `referee_evidence.py:242-243` computes `len(datasets)` from `dataset_store.list()`. Pre-existing `edge_report.py:137-150` (`_verified_records`, unchanged this iteration) is `dataset_store.list()[0]` with errors raised instead of returned; `edge_report.py:885` uses `len(records)` from that same helper. Both trace to the identical `DatasetStore.list()` read (blueprint's declared owner, `store.py`/`datasets.py`) — no independent logic, so the two numbers cannot diverge. This is single-source-of-truth compliance, not a violation. |
| Playbook records / strategy datasets & trades (blueprint "Unchanged owners") | OK — read verbatim, zero re-implementation | `referee_evidence.py` imports `PlaybookStore`/`playbook_parameters` from `desk_playbook.py` (line 98), `DatasetStore` from `datasets.py` (line 97), `JournalStore` from `store.py` (line 99). Field access (`record["parameters"]`, `record["config_fingerprint"]`, `record["session_date"]`, `signal["setup_id"]`/`signal["side"]`) verified against the real store schema in `desk_playbook.py:1001-1019` (`PlaybookStore.record`'s own `meta` dict) and `desk_playbook_detect.py` (signal shape) — no fabricated schema. |
| `config_fingerprint` (blueprint "Unchanged owner" `app/config.py`) | OK | `referee_routes.py:337` calls `CONFIG.config_fingerprint()` directly; no re-derivation. |
| MCP tool count (blueprint "Unchanged owner," 20 today / 22 after J-09) | OK | Zero diff to `apps/backend/app/mcp/__init__.py` or `tests/test_mcp_server.py`. The new route is auto-reachable through the existing generic `get_endpoint` proxy (`ALLOWED_GET_PREFIXES = ("/tape/", "/research/", "/meta/")`, `apps/backend/app/mcp/__init__.py:58`) — verified this claim against the actual allowlist rather than trusting `main.py`'s comment; no new named MCP tool was needed or added. |

No new displayed value outside the contract: this iteration is backend-only (confirmed below), so Data Contract rule A4/A5 ("new value the iteration displays") does not trigger — nothing is rendered to a user yet.

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| `GET /research/desk/referee/evidence` | OK — matches the blueprint's declared "no page yet" home | `blueprint.md:34` explicitly assigns this journey **no dedicated page** ("backend fold; surfaces inside the J-07 shortlist"). Iter spec confirms `UI surface changes: None` / `New information displayed: None`. Verified independently: `git diff <snapshot-sha> --stat` shows only `apps/backend/app/main.py` changed among tracked files (plus 4 wholly new backend files); `grep -rli referee apps/frontend/` returns nothing — no parallel shell, no hidden/duplicate UI surface exists anywhere in the frontend tree. |

No new page/route with a UI surface was introduced this iteration, so reachability/duplicate-home/parallel-shell checks have nothing further to evaluate.

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- `integrity_errors` appears in both the `playbook_occurrence` and `strategy_trade` response blocks (`referee_evidence.py:213`, `:263`) but is not listed in the iteration spec's pinned JSON shape (`docs/phases/goal-referee-iter-1.md:132-153`). It is honest error-propagation plumbing — it satisfies the iteration's own testing requirement that "a corrupted/unparseable store file must propagate the existing store's surfaced error, never be silently dropped" — not a competing computation of a registered value, so this is not a Data Contract violation. Worth folding into the pinned response shape the next time this endpoint's contract is touched (e.g., when J-02 extends it) so the documented shape stays the complete source of truth for the field list.
