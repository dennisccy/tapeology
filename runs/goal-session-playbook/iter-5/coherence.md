# Iteration 5 — Coherence Audit

**Iteration:** goal-playbook-iter-5
**Date:** 2026-08-11
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

<!-- COHERENCE-PASS: no objective violations; at most minor advisory notes -->

---

## Data Contract check

All six J-05 changes land as new/newly-real fields inside the already-registered "Playbook records"
row (owner `apps/backend/app/research/desk_playbook.py` + `desk_playbook_detect.py`, served by the
unchanged `GET /research/desk/playbook`, `apps/backend/app/research/desk_routes.py:993`). Verified
the route (`get_playbook`, `desk_routes.py:993-1028`) returns `store.get(id)` / the newest record
verbatim with no field allow-list, so no route diff was needed and none appeared in the diff — one
owner, one server, confirmed.

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| `geometry.decline_mbr` / `decline_bars` / `climax_rvol` / `bars_from_climax_to_trigger` (capitulation) | OK | computed once in `detect_capitulation`, `apps/backend/app/research/desk_playbook_detect.py:292-398`; frontend renders verbatim via `fmt()`, `apps/frontend/app/desk/page.tsx:4629-4640` (no client recompute) |
| `disclosures.euphoria_recent` / `capitulation_recent` (any signal) | OK | computed once in `_decorate_markers`, `apps/backend/app/research/desk_playbook.py:466-495` (single per-member walk, same in-memory `detected_signals` list — not a second pass or a second endpoint); chips already wired pre-iteration, only real data changed |
| `_rvol` (RVOL primitive `detect_capitulation`/`detect_euphoria` reuse) | OK | pre-existing helper at `desk_playbook_detect.py:74`; new `_rvol_series` (`:221`) is a thin wrapper over it, not a second implementation |
| `entry`/`entry_kind`/`invalidation_price`/`market` block (capitulation signal) | OK | reuses the shared stop-through-fill convention and `_market_block` primitive already used by `detect_jbe`/`detect_dbi`/`detect_cup_handle` — no new geometry-derivation path |
| Forward measurement (`forward`, `invalidation_breached`) for capitulation signals | OK | flows through the SAME unmodified `_measure_signal`/`desk_forward.py` pass (verified zero diff to `desk_forward.py` and to `desk_routes.py`, `config.py`, `mcp/__init__.py`, `setups.py`, `bars.py`, `levels.py` — confirmed via `git diff <snapshot-sha> --stat`, only the 8 files below changed) |
| `PLAYBOOK_REGISTER` (backend) vs. the two `/desk` copy spots (frontend) | OK (same content, cross-checked) | `desk_playbook.py:159-165` register text and `page.tsx:4993-4994` (empty-state) / `page.tsx:5091-5092` (populated blurb) name the identical five-family list; a pinned-text test (`test_desk_playbook.py`, `test_playbook_register_pinned_text_names_every_shipped_setup_family`) locks the backend string so a future drift (J-06) fails loudly — this closes the exact register/blurb drift the iter-4 coherence review would have flagged |
| Detector thresholds (`PLAYBOOK_VERTICAL_MOVE_MBR`, `PLAYBOOK_VERTICAL_WINDOW_BARS`, `PLAYBOOK_BOUNCE_MAX_BARS`, `PLAYBOOK_RVOL_SURGE`, `PLAYBOOK_MARKER_DECAY_BARS`) | OK | all five pre-registered in `docs/playbook-detector-spec.md` §1's constants table and §3.5 BEFORE this iteration — confirmed `git diff <snapshot-sha> -- docs/playbook-detector-spec.md` is empty (spec untouched this iteration, it already carried §3.5 in full) |

No new function/service/endpoint independently recomputes any already-registered value (bars,
sessions, universe membership, forward-measurement helpers, levels/tradability) — the blueprint's
"unchanged owners" list stays untouched: confirmed zero diff to `desk_forward.py`, `desk_screen*.py`,
`setups.py`, `bars.py`, `levels.py`, `config.py`, `mcp/__init__.py` via the noise-excluded
`git diff 55697d07975fa132fb41853be1d2ddd9198e03b3 --stat` (only the 8 files below appear, matching
the iteration spec's own "expected zero diff" claims exactly).

## Information Architecture check

No new page, route, or section. This iteration adds one new setup-type branch and two decoration
chips (already wired, now fed real data) inside the already-registered Desk → Playbook Signals home.

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| Capitulation geometry line, `/desk` Playbook Signals | OK | new conditional branch inside the pre-existing `PlaybookSignalDetail`, `apps/frontend/app/desk/page.tsx:4632-4640` — same component, same section, no new route; nav (`app/meta.py` `UI_ROUTES`, per blueprint) unchanged, confirmed no diff to any nav/router file in this iteration's 8-file changeset |
| `euphoria_recent`/`capitulation_recent` decoration chips | OK | pre-existing render at `page.tsx:4647-4648` (per iter spec — verified untouched in the diff), now driven by real backend values |
| Register/blurb copy widening | OK | in-place text edits at the two already-registered spots (`page.tsx:4993`, `page.tsx:5091`), no new component or shell |

No duplicate home, no parallel shell, no new nav-reachable surface — the "no nav-skeleton edit"
claim in the iteration spec's Blueprint-conformance section checks out against the actual diff.

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- `geometry.decline_bars` and `geometry.bars_from_climax_to_trigger` are both plain bar counts (not
  price-arithmetic), consistent with the existing `base_bars`/`cup_bars` precedent for staying
  outside `_PRICE_ARITHMETIC_FIELDS` in `test_desk_ui_guards.py`. `bars_from_climax_to_trigger` is
  arguably a closer cousin to `decline_bars` (a bar-count) than to `decline_mbr`/`climax_rvol` (price
  arithmetic), and the diff does add it to the regex list anyway (`test_desk_ui_guards.py:1064`) — a
  slightly stricter-than-necessary but harmless choice, not a coherence issue.
- The euphoria marker's data shape (`{"trigger_idx": int}`) is intentionally minimal and structurally
  incapable of matching the served-signal shape — this is a deliberate asymmetry (marker vs. signal),
  not an inconsistency; noted only so a future reader doesn't mistake it for an oversight.
