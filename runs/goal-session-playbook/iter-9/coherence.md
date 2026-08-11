# Iteration 9 — Coherence Audit

**Iteration:** goal-playbook-iter-9
**Date:** 2026-08-11
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

<!-- COHERENCE-PASS: no objective violations; at most minor advisory notes -->

---

## Data Contract check

This iteration touches two registered rows from the blueprint's Data Contract: "Playbook records"
and "Evidence aggregates." Both changes are additive exposure of already-served data, not new
computation.

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Playbook records (signals + measurements + baseline + summary) | OK — new `desk_playbook` MCP tool is a byte-identical `_STATIC_PATHS` proxy of the already-registered endpoint, no new route/computation | `apps/backend/app/mcp/__init__.py:123` maps `"desk_playbook": "/research/desk/playbook"`, which is the pre-existing route at `apps/backend/app/research/desk_routes.py:1006` (`@router.get("/playbook")`, unchanged this iteration) |
| Evidence aggregates | OK — new `desk_playbook_evidence` MCP tool is a byte-identical proxy of the already-registered endpoint; `signature` field now rendered on `/desk` is read straight off the fetched object, no client-side derivation | `apps/backend/app/mcp/__init__.py:129` maps `"desk_playbook_evidence": "/research/desk/playbook/evidence"`, pre-existing route at `apps/backend/app/research/desk_routes.py:1320` (unchanged); UI reads it via the single existing `fetchDeskPlaybookEvidence()` call (`apps/frontend/lib/api.ts:1985-1993`, itself unchanged) and displays `data.signature` verbatim at `apps/frontend/app/desk/page.tsx:319` inside the existing `PlaybookEvidenceSection` |

No new function anywhere in the diff independently computes a playbook signal, a measurement, or
an evidence distribution — `apps/backend/app/mcp/__init__.py`'s only new code is the two
`_STATIC_PATHS` dict entries and two `types.Tool(...)` descriptor blocks (pure metadata/proxy
registration, confirmed by reading the full diff hunk at lines 23-75 of
`runs/goal-session-playbook/iter-9/iter-diff.md`). `apps/backend/tests/test_mcp_server.py`'s new
tests assert byte-identity between the MCP tool response and the direct `curl`/`httpx` call on the
same canonical route — the correct shape for a proxy, not a second implementation. No new
UI-displayed value appears this iteration outside the already-registered "Evidence aggregates" row
(the `signature` field was already typed in `apps/frontend/lib/types.ts:1789` per the iter spec and
is not new).

## Information Architecture check

J-09 has no page (MCP tool surface only, per the blueprint's own J-09 row). J-10 is a
whole-product regression walk, not a new feature. The only frontend diff is one new `<p>` line
inside the pre-existing `PlaybookEvidenceSection` component, which already lives under `/desk`'s
"Playbook Evidence" section (blueprint IA, lines 66-70 of
`runs/goal-session-playbook/state/blueprint.md`). No new route, no new nav entry, no new page
shell was introduced.

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| `/desk` Playbook Evidence signature line | OK — rendered inside the existing section, no new route/nav | `apps/frontend/app/desk/page.tsx:317-321` (new `<p data-testid="desk-evidence-signature">` sits inside the pre-existing `<div data-testid="desk-evidence-section">`); nav is unchanged — no edits to any router/nav component in this diff (only `apps/backend/app/mcp/__init__.py`, `apps/backend/tests/test_mcp_server.py`, `apps/frontend/app/desk/page.tsx`, and four framework/automation scripts changed, per `git diff 113e6f4256b1be98064d170ce7e1474d8df43b2b --stat`) |
| `desk_playbook` / `desk_playbook_evidence` MCP tools | OK — not a UI surface; no IA entry required (blueprint explicitly marks J-09 as "MCP tool surface only; no page") | `runs/goal-session-playbook/state/blueprint.md:84` |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- The iteration also hardens the framework's store-scope guard (`browser-qa-phase.sh`,
  `goal-iter-lean.sh`, `qa-phase.sh`, `project-extensions/store-scope/store-scope.env`) and adds a
  `journey-scripts/J-08.json` golden replay script. These are test/automation infrastructure
  changes, not product UI or Data Contract surfaces, so they carry no coherence implications and
  are out of this audit's scope.
- No unregistered new values found; no formatting drift observed in the one new UI line (uses the
  same `font-mono` treatment as the adjacent "other signatures" list at
  `apps/frontend/app/desk/page.tsx:3896`).
