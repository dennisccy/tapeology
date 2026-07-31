# Iteration 36 — Coherence Audit

**Iteration:** goal-desk-iter-36
**Date:** 2026-07-31
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

<!-- COHERENCE-PASS: no objective violations; at most minor advisory notes -->

---

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Screen-pin resolution (new, J-21) | OK | Blueprint registers it BEFORE the build at `runs/goal-session-desk/state/blueprint.md:186` (owner `app/research/desk_screen_pins.py`, endpoint `GET /research/desk/screen/pins`); code matches verbatim — `apps/backend/app/research/desk_screen_pins.py:1-121` new module, `apps/backend/app/research/desk_routes.py:40-56` new route |
| Screen snapshots / rank / skip rows (existing owner `desk_screen.py`) | OK — reused, not duplicated | `desk_screen_pins.resolve_desk_screen_pins` (`apps/backend/app/research/desk_screen_pins.py:541-610`) calls the SAME accessors `run_screen_and_record` already uses — `screen_as_of` (`desk_screen.py:233`), `compute_bar_store_signature` (`desk_screen.py:255`), `ScreenStore.find_by_key` (`desk_screen.py:602`) — verified these are the identical functions imported (`desk_screen_pins.py:537`), not re-implementations. `test_tc6_zero_compute_tradability_calls_and_zero_bar_store_reads` (`test_desk_screen_pins.py:844-859`) poisons every `BarStore` method + `compute_tradability` and the call still succeeds, structurally proving no second computation path |
| Config fingerprint / MCP tool count | OK — unchanged | No diff to `app/meta.py`, `app/mcp/__init__.py`, `config.py`; reviewer report confirms `08e471b10130e1e2` unchanged and no new `Config` field |
| Ranked table (`desk_screen.py` rows, J-16 width contract) | OK — untouched | Diff touches only `DeskProvenance`/`ScreenComputeControl`; no edit to the ranked-table render function |

New UI surfaces (`DeskProvenancePins`, `TodayScreenPinsNote`, `apps/frontend/app/desk/page.tsx:115-231`) fetch exclusively via the new `fetchDeskScreenPins` helper (`apps/frontend/lib/api.ts:421-444`), which hits only `GET /research/desk/screen/pins` — no alternate endpoint, no client-side recomputation. The components render `data.recorded !== null` as a presence/absence check on the server-served field only; they compute no equality of their own (matches the blueprint's explicit "J-20 rule" carry-forward, confirmed in `assumptions.md` iter-36 entry (i)).

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| J-21 screen-pin disclosure | OK | No new route/page — verified zero diff to `app/meta.py` (`UI_ROUTES`, the single nav owner) and to any nav/sidebar component. The two new pieces render inside the already-mounted `DeskProvenance` (`page.tsx:1768-1798`) and `ScreenComputeControl` (`page.tsx:1866-1912`), both already part of `/desk`'s existing Provenance panel and Run Screen control per the blueprint's Feature/journey homes table (`blueprint.md:142`, "existing Provenance panel + one new line beside the existing Run Screen control — no new section, no standalone page"). Reachability unchanged (still whatever click-depth `/desk` already had). |

No duplicate home, no parallel shell: the spec's own "Blueprint conformance" field (`docs/phases/goal-desk-iter-36.md:171-174`) names the existing `/desk` canonical home and the diff confirms zero new component tree/router/layout was introduced.

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- The new "resolved now" `Metric` labels ("Universe snapshot (resolved now)", "Config fingerprint (resolved now)", "Bar-store signature (resolved now)", `page.tsx:140-142`) deliberately differ from the sibling recorded-snapshot labels a few lines above ("Universe snapshot", "Config fingerprint", "Bar-store signature", `page.tsx:1780-1785`). This is a legible disambiguation (two different values — what's recorded on the displayed snapshot vs. what would resolve right now) rather than an inconsistency; noting only for completeness, no action needed.
- `journey-scripts/J-21.json` and the `[NEW]`-flagged demo-narrator walkthrough are not yet present at this point in the pipeline (dev/review complete, browser-QA/demo-narrator steps still pending per `runs/goal-desk-iter-36/status.json`'s `next_action: review`) — expected at this stage, not a coherence gap.
- The blueprint's ASCII navigation-skeleton diagram (`blueprint.md:43-115`) stops narrating at iter-24; iterations 26/29/32/35/36 are documented only in the "Feature / journey homes" table below it (which IS current and correct, including the new J-21 row at `blueprint.md:142`). Purely a documentation-currency nit in the diagram's prose, not a structural drift — no nav/home is actually missing or wrong.
