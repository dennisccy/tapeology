# Phase goal-rapid-microscope-iter-24 — User-Visible Changes

**Phase:** goal-rapid-microscope-iter-24
**Date:** 2026-08-23
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- Nothing new. This iteration adds no new page, button, control, or navigation path — confirmed
  by `git diff`: **zero frontend files changed** (only backend Python, test files, QA scripts, and
  stored replay-script JSON were touched). The spec itself states "New user-facing capability:
  none."
- The only thing an operator using the scoped QA rig (not the ordinary/real backend) can newly
  see is one seeded pilot-study row in the Scout Ledger section on `/desk` — but this is QA
  evidence infrastructure, not a shipped product capability (see "Not Visible Yet" below).

---

## What Changed in the Visible UI

- **`/desk` → Validation Vault section → "Sealed at" column**: the value shown for every shard
  row (sealed, assigned, and exposed alike) is sourced from a backend field that now carries only
  a calendar date (`YYYY-MM-DD`) instead of a full microsecond-precision timestamp. This is a
  deliberate privacy-hardening change: the previous full-precision value could be cross-referenced
  against already-published per-run seal counts to narrow down which secret shard a given tape
  is, and this iteration closes that channel. **However, see the regression noted below — the
  actual rendered text is not simply "a coarser date."**

No other visible surface changed. The Scout Ledger and Walk-Forward sections' headings, layout,
and controls are all unchanged; only two stored QA-replay scripts (not application code) had their
target assertion string swapped, described below.

---

## What Old Behavior Changed

- **Validation Vault "Sealed at" column now displays an incorrect value — a verified display
  regression, not yet caught anywhere in this iteration's dev/review artifacts.**
  Previously the column showed the true sealing instant, e.g. `2026-06-09 16:43 ET`. The backend
  now serves a bare date string for this field (verified directly against the new
  `test_vault.py` assertions: the served value is exactly `"2026-06-09"`, 10 characters, no
  time-of-day). The frontend cell still calls the same formatter it always did —
  `formatDateTimeET(shard.sealed_at, { seconds: false })` (`apps/frontend/app/desk/page.tsx:6801`)
  — which assumes every value it receives is a full ISO instant and converts it through the
  `America/New_York` timezone. Fed a bare date string, JavaScript parses it as UTC midnight, and
  converting UTC midnight into US-Eastern time always lands on the **previous calendar day** with
  a **spurious evening time-of-day**. Reproduced directly with the app's own formatter logic:
  `"2026-06-09"` → renders as **`2026-06-08 20:00 ET`** (EDT, summer) or `"2026-01-15"` →
  **`2026-01-14 19:00 ET`** (EST, winter) — confirmed with a standalone Node.js run of the exact
  `etParts`/`formatDateTimeET` code from `apps/frontend/lib/datetime.ts`.

  This has two consequences, both user-visible on the shipped page:
  1. **The displayed date is simply wrong** — one calendar day earlier than the shard actually
     sealed.
  2. **The fix's own intent is partly undone** — the column still shows a time-of-day component
     (an incorrect, generic one, always in the 19:00–20:00 band), rather than reading as a clean
     date the way the backend change and the phase's own "no time-of-day component" goal intended.

  Note this affects **only** the "Sealed at" column. The neighboring "Assigned at" and "Exposed
  at" columns (`shard.assigned_at` / `shard.exposed_at`, page.tsx:6827/6831) were **not** touched
  by this iteration's backend change and still render correctly, since those backend fields still
  carry full-precision timestamps.

  This was not caught by the dev handoff (which lists "Backend-Only Items: None... nothing new was
  added that lacks a UI path" and does not mention this) or by the code reviewer (whose review
  covers only backend files — no frontend file changed, so none was examined). No browser
  screenshot exists yet for this iteration to have caught it visually either.

- **Two stored QA-replay scripts' assertion text changed (`J-08.json` step 3, `J-10.json` step
  12)** — no product behavior changed here. These are golden-replay JSON files, not application
  code: they used to assert the Scout Ledger section shows the literal empty-state text "No
  candidates ledgered." Because this iteration's QA fixture now seeds a real pilot-study row into
  that same rig (for the new J-09 golden), that empty-state text is no longer always true on this
  specific rig, so both scripts were updated to assert the always-present heading "Ledger chain
  verification:" instead. **A real operator running the ordinary backend against the real
  `.data` store, with no candidates ledgered, still sees "No candidates ledgered." exactly as
  before** — nothing in production code changed here.

---

## Not Visible Yet

- **The new pilot-study Scout Ledger row** (seeded via the new
  `apps/backend/scripts/seed_micro_scout_iter24_j09_fixture.py`, a `capitulation_exhaustion_pilot`
  family with `family_id = failed_aggression_score__playbook_signal__trades_20`) exists **only**
  inside the throwaway, scoped QA-rig backend store started by
  `apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh`. An operator running the
  ordinary backend against the real `.data/` store will not see this row — it is QA evidence
  infrastructure for the automated replay/browser-QA pass, not a shipped product capability.
- **The widened `stage_tr2()` run-aware anti-goal check** (`j06_operator.py`) is an operator-run
  CLI verification tool (`j06_operator.py verify` / `tr2`), never surfaced in the web UI. It
  exists purely to catch a future silent violation of the sealed-pool identifiability floor; there
  is nothing for a UI user to see or interact with.
- **The independent code-read findings for `j06_operator.py`/`tick_recorder.py`** (no new defect
  found beyond the sealing-time leak, per the dev handoff) have no UI surface at all — these are
  internal-code-quality confirmations, not features.
