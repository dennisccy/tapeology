# Phase goal-rapid-microscope-iter-21 — User-Visible Changes

**Phase:** goal-rapid-microscope-iter-21
**Date:** 2026-08-20
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

None — this iteration adds no new user-triggerable control anywhere in the UI. The three new
research capabilities it ships (band-touch enumeration, structure-conditioned Scout anchors, the
walk-forward floor check) are all reachable only through a direct backend API call
(`POST /research/desk/micro/scout/compute` with `{"grid": "delta_divergence_pilot"}`) or the
backend CLI's new `--grid delta_divergence_pilot` flag — never through a button, form, or link on
`/desk`. This is by design (goal.md's own OUT OF SCOPE list: "a UI trigger button for the pilot
grid" is explicitly excluded this iteration, matching the "operator act, not a goal-mode/UI act"
framing).

---

## What Changed in the Visible UI

- The **Microscope Readiness** section on `/desk` (Sealed Tranche table) now shows one new row,
  "Joinable corpus — band touches", directly below the existing "Joinable corpus — withheld
  (excluded)" row. It renders either a real integer (the materialized wall-touch count) or the
  honest literal text "not enumerated" — never a bare, ambiguous number. Before this iteration the
  underlying value was fetched by the frontend but never rendered anywhere.
- The **Scout Ledger** section's per-candidate table (`/desk` → Scout Ledger, inside each
  `family.trials` row) can now show extra text in the existing Feature cell — e.g.
  `divergence_at_level_bearish / threshold (band_touch)` — whenever a ledgered candidate's
  `structure_context.kind` is not `"none"`. This text only appears once an operator has explicitly
  run the new pilot-study Scout grid (see "Not Visible Yet" below); every row the shipped default
  grid has ever produced (`kind="none"`) still renders exactly the text it always has.
- The **Scout Ledger** table can now contain a second row under the same `candidate_id` as a
  screened candidate — the walk-forward floor-check decision. That row shows em-dashes (`—`) in
  the Feature/Horizon columns and `null` in the collapsed `screen_result` JSON detail, because it
  is an eligibility decision, not a statistical screen. It is honest, but visually looks slightly
  incomplete next to a normal screen row (a known, logged UX rough edge — see the dev handoff's
  "Known Issues").

---

## What Old Behavior Changed

- **`GET /research/desk/micro/readiness`** (the data behind the Microscope Readiness section):
  previously `joinable_corpus.band_touch_count` always served the placeholder
  `{"status": "not_enumerated", "count": null}` on every call. Now the route always constructs a
  `BandMapResolver` and serves the real `{"status": "enumerated", "count": <int>}` — same field
  name, same shape, a genuinely different (and now meaningful) value on every request from this
  iteration forward. On the real production data today this is verified to read a real, non-zero
  count (`8247`, confirmed live); on most fixture/QA backends without a pre-computed wall map it
  will honestly read `0`.
- No other previously-shipped behavior changed. The default Scout compute grid (the existing "Run
  Scout" button), the Walk-Forward section's own ledger, the Playbook Evidence section, and every
  other already-shipped `/desk` section render byte-identically to before this iteration when no
  pilot-grid row exists.

---

## Not Visible Yet

- **The three predeclared pilot-study candidate specs** (range-wall failed aggression,
  delta-divergence-at-level-tests, capitulation exhaustion) exist frozen in `scout.py` source, but
  there is still no button or form anywhere on `/desk` to run any of them. The only way to make a
  `band_touch`/`playbook_signal` row appear in the Scout Ledger on screen is a direct
  `POST /research/desk/micro/scout/compute` API call with `{"grid": "delta_divergence_pilot"}` (or
  the backend CLI's new `--grid` flag) — an explicit, intentional gap this iteration.
- **Studies 1 and 3** (range-wall failed aggression, capitulation exhaustion) were never passed
  through the screening pipeline at all this iteration — not even via the API — so no on-screen
  evidence of either can exist yet regardless of how the pilot grid is triggered. Only Study 2
  (delta divergence at level tests) can ever appear as a real Scout Ledger row this iteration.
- **The band-touch enumerator itself** has no dedicated UI of its own — its only visible trace on
  `/desk` is the materialized count in Microscope Readiness described above, and indirectly, any
  Scout Ledger row anchored to a band touch once the pilot grid is run.
- **The walk-forward floor-check decision** for the screened candidate is visible only inside the
  Scout Ledger's existing table (a second row under the same `candidate_id`) — it is NOT shown in
  the separate Walk-Forward section, even though that section's name might suggest it would be.
- **The r5 §10.7 "seal-unaware metric" UI caveat sentence** stays unbuilt this iteration (explicitly
  dropped per goal.md's NOTES) — `strategy_trade_readiness` has no live UI consumer to attach a
  caveat to.
