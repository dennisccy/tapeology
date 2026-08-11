# Phase goal-playbook-iter-6 — UI Surface Map

**Phase:** goal-playbook-iter-6
**Date:** 2026-08-11
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/desk` | Playbook Signals table row + detail-panel setup chip (`data-testid="desk-playbook-signal-setup"`, `playbookSetupLabel()` in `page.tsx:4401`) | Changed behavior (chip now takes 3 additional values) | `PLAYBOOK_SETUPS` extended to a 9-tuple; `playbookSetupLabel` gains `"range_trade"` → "Range Trade", `"double_top"` → "Double Top", `"double_bottom"` → "Double Bottom" | Run Playbook for the compute-walk wiring fixture (symbol `RTAAA`, session date `2026-06-22`, per `test_range_trade_wired_into_compute_playbook_is_measured_like_every_other_setup`); verify the row's setup cell renders the chip text "Range Trade" exactly (not the raw string `range_trade`). Repeat for symbol `DTAAA` on the same date and verify "Double Top" (and, for the mirrored fixture, "Double Bottom") render exactly |
| `/desk` | Playbook signal detail panel, range_trade geometry line (`data-testid="desk-playbook-signal-range-trade-geometry"`, inside `PlaybookSignalDetail`, `page.tsx:4648-4655`) | New content (new conditional render branch) | J-06 adds the `range_trade` detector with its own geometry shape (range width, per-zone touch counts, two boolean disclosure flags) | Click a `range_trade` row to select it; verify a `<p>` with `data-testid="desk-playbook-signal-range-trade-geometry"` appears directly below the trigger/invalidation line, reading "range `<N>` MBR wide · low zone touches `<N>` · high zone touches `<N>` · broke at slot `<N>`"; if `crossed_midrange` is true, verify "· crossed midrange" is appended; if `absorption_bar_present` is true, verify "· absorption bar present" is appended |
| `/desk` | Playbook signal detail panel, double_top/double_bottom geometry line (`data-testid="desk-playbook-signal-double-extreme-geometry"`, inside `PlaybookSignalDetail`, `page.tsx:4660-4667`) | New content (new conditional render branch) | J-06 adds the `double_top`/`double_bottom` detector pair, sharing one geometry shape (gap, separation, valley/peak depth, nominal risk, second-pivot RVOL ratio) | Click a `double_top` or `double_bottom` row to select it; verify a `<p>` with `data-testid="desk-playbook-signal-double-extreme-geometry"` appears reading "gap `<N>` MBR · separation `<N>` bar(s) · depth `<N>` MBR · nominal risk `<N>` MBR · broke at slot `<N>`"; when `second_top_rvol_vs_first` is not null, verify "· second RVOL vs first `<N>`" is appended; when it is null, verify that suffix is absent entirely (not "null" or blank text) |
| `/desk` | Playbook Signals section — the "not computed yet" empty-state sub-text (plain `<p>` inside the `record === null` branch, `page.tsx:5020-5022`) | Changed behavior (copy widened) | The register-widening carried item (third occurrence this session, per the iter-4/iter-5 lesson) | Enter a session date with no recorded playbook (or clear the store's fixture directory), load `/desk`, and read the amber panel's sub-text; verify it reads "Run Playbook detects and measures the opening-range-break, jump-base-explosion, drop-base-implosion, cup-and-handle, capitulation, range-trade, double-top, and double-bottom families on `<date>`'s own recorded bars — an explicit operator act, nothing runs on page load." (all eight family names present, comma-separated, ending "double-bottom") |
| `/desk` | Playbook Signals section — the populated-section intro paragraph (plain `<p>` at the top of `PlaybookSection`, `page.tsx:5117-5123`) | Changed behavior (copy widened) | Same register-widening item, frontend half | Load `/desk` with any computed playbook record visible; read the paragraph directly above the session-date input; verify it reads "The book's opening-range-break, jump-base-explosion, drop-base-implosion, cup-and-handle, capitulation, range-trade, double-top, and double-bottom signals, detected on this session's own recorded 5m/1m bars and measured with the desk forward rail's own conventions — read verbatim from GET /research/desk/playbook. Nothing here is recomputed in the browser." |
| `/desk` | Playbook record's amber "register" footer note (`data-testid="desk-playbook-register"`, `page.tsx:5082-5087`, served from `record.register`) | Changed behavior (backend-served text widened, but NOT retroactive) | `PLAYBOOK_REGISTER` in `desk_playbook.py:178` widened to name all eight families; since playbook records are append-only, this text is baked into a record at compute time | Run Playbook for a NEW session (or re-run an existing one, which mints a new record because `PLAYBOOK_SETUPS` growing moved `playbook_input_signature`); verify the register footer text lists all eight family names ending "double-bottom." Separately, load a session whose record was recorded BEFORE this iteration (if one is still on file) and verify its register footer still shows the OLD five-family wording — confirming the append-only, non-rewritten contract |
| `/desk` | `DeskPlaybookGeometry` type (`apps/frontend/lib/types.ts:1519-1530`) — no visual element of its own | Config/type change (10 new optional fields added: `range_width_mbr`, `low_zone_touches`, `high_zone_touches`, `crossed_midrange`, `absorption_bar_present`, `tops_gap_mbr`, `tops_separation_bars`, `valley_depth_mbr`, `nominal_risk_mbr`, `second_top_rvol_vs_first`) | Backing shape for the two geometry-line rows above; the served `signal.geometry` object now varies its fields by `setup_id`, same pattern as J-04/J-05's own additions | No standalone visual test — covered indirectly by the two render-branch tests above. Confirm `cd apps/frontend && npx tsc --noEmit` exits clean (already verified by the developer; re-verify only if the type file is touched again) |
| `/desk` | Every other shipped Desk section (screen history calendar, forward returns, refresh chain, ranked briefing, skipped members, runs/pins/compare/provenance) plus the five already-shipped setup families within Playbook Signals | No code change — regression risk only | J-06 touches only the Playbook Signals sub-tree (`playbookSetupLabel`, `PlaybookSignalDetail`, the two copy spots, `PLAYBOOK_REGISTER`); TC-11/TC-15/TC-16 require every other shipped section and setup family to render exactly as before | Load `http://localhost:3301/desk` with `apps/frontend/.next` freshly rebuilt (T-9 discipline); scroll through every shipped section heading (Screen History, Forward Returns, Refresh Chain, Briefing, Skipped, Runs, Pins, Compare, Provenance, Playbook Signals) using the sibling-`display:none`-collapse technique for the lower sections; verify each heading text and layout is unchanged, and separately re-verify an `open_high_break`/`jbe`/`dbi`/`cup_handle`/`capitulation` row still shows its own pre-existing geometry line with no new suffix text and no console error |

<!-- Change Type options used above: Changed behavior | New content | Config/type change -->

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/research/desk_playbook_detect.py` — `detect_range_trade`, `_range_trade_side`,
  `detect_double_top`, `detect_double_bottom`, `_find_double_extreme` — the detection math itself.
  No UI impact directly; its OUTPUT reaches the UI only through the already-registered
  `GET /research/desk/playbook` endpoint, captured in the two geometry-line surface-map rows above.
- `apps/backend/app/research/desk_playbook.py` — `PLAYBOOK_SETUPS` extended to 9 entries,
  `PLAYBOOK_REGISTER` widened (its UI manifestation is covered in the surface-map row above), the
  compute-walk loop wiring the three new detectors beside the existing five. Reaches the UI only
  through the existing endpoint's payload, already covered.
- `apps/backend/tests/test_desk_playbook_detect.py`, `test_desk_playbook.py`,
  `test_desk_playbook_guards.py` (extended with the new zero-`compute_tradability`/
  zero-`compute_levels` call-counting guard and the decline-disclosure source-hash guard),
  `test_desk_ui_guards.py` (extended `_PRICE_ARITHMETIC_FIELDS`) — test files. No UI surface.
- `docs/playbook-detector-spec.md` — §3.5 doc-only prose addition (`decline_bars`/`decline_mbr` +
  re-anchoring reading). Documentation only; not served by any app route; zero diff to any
  `PLAYBOOK_*` constant or to the code lines it describes (source-hash-guard-verified).
- `runs/goal-session-playbook/journey-scripts/J-05.json` — a new stored golden replay script for the
  capitulation family (a QA/regression-automation artifact, not a product surface). It replays an
  ALREADY-SHIPPED (J-05, prior iteration) browser flow; it does not add or change anything a user
  sees.
- The two investigated orphaned `.data/playbook_runs/playbookrun-2026-08-11-*.json` run-ledger
  rows — a data-hygiene investigation (see the dev handoff's "Known Issues"). No code change, no UI
  surface; the rows are not rendered anywhere in the app.

---

## Summary

- **Frontend surfaces changed:** 2 files (`apps/frontend/lib/types.ts`, `apps/frontend/app/desk/page.tsx`), all within the single already-shipped Playbook Signals sub-tree on `/desk`.
- **New pages/routes:** 0
- **Modified components:** 2 (`playbookSetupLabel`, `PlaybookSignalDetail`) — plus the `DeskPlaybookGeometry` type they depend on and the two static copy spots (`page.tsx:5020-5022`, `page.tsx:5117-5123`).
- **Navigation changes:** no
- **Backend-only changes:** 6 (2 detection/compute modules feeding the existing endpoint, 4 test files, 1 doc file, 1 new golden-replay QA script, plus a non-code data-hygiene investigation) — see list above.
