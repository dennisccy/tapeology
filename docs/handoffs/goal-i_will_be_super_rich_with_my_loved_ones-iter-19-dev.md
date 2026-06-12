# goal-i_will_be_super_rich_with_my_loved_ones-iter-19 Dev Handoff

**Phase:** goal-i_will_be_super_rich_with_my_loved_ones-iter-19
**Date:** 2026-06-12
**Agent:** developer
**Status:** complete

## Iteration intent (read this first)

This is an **evidence-completion iteration: pixels, not code.** Per the iter spec there is
**no planned backend or frontend code change** — the code under test is the committed iter-18
replay-study layer (capability 32). The developer's job is operational: (1) repair the corrupted
frontend build substrate, (2) prove the running code IS the iter-18 code via canary probes, (3)
ensure the persistent dev journal DB holds the cancelled / hindsight / re-run / failed study
records the J-60/J-61 **pixel** legs need, (4) re-run the backend regression suite, and (5) leave a
clean, healthy, server-free substrate for the browser-qa-agent to capture against.

The actual rendered-pixel captures (J-60/J-61 legs, J-68 sentinel) are the **browser-qa-agent's**
job downstream — this handoff hands it a verified, seeded, healthy substrate.

> **Re-run note.** An infrastructure pause re-ran iteration-19's planning step (spec NOTES,
> line 127), so the developer step ran again. A prior dev pass + reviewer PASS + a browser-qa run
> already exist as untracked artifacts for this iteration; this pass **re-verified** the substrate
> from scratch (fresh servers, fresh canary, full regression) rather than redoing seeding, and
> found the substrate strictly **better** than the prior handoff described — the one J-61 leg the
> prior handoff flagged as record-absent (the `failed` study) now has a persisted record.

## What Was Done (this pass)

### Environment repair (operational, not app code)
- **Removed the corrupted `apps/frontend/.next`.** On disk it carried **production-build
  artifacts** (`prerender-manifest.json`, `build-manifest.json`) — confirming the iter-2/iter-18
  hazard (a production `npm run build` into the live dev server's shared `.next`) had recurred.
  Cleared it; `.next` is gitignored (no tracked deletion). A fresh `next dev` recompiled the routes
  cleanly during canary, after which `.next` was **cleared one final time** so the browser-qa step
  starts from a clean build substrate it owns.

### Canary verification (code identity — iter-6 lesson) — re-proven this pass on fresh servers
Backend started fresh on `:8650` with the persistent dev DB
(`TAPEOLOGY_JOURNAL_DB=apps/backend/tapeology_journal.db`); frontend started fresh on `:3650`
(`NEXT_PUBLIC_API_URL=http://localhost:8650`). All canary preconditions PASS:
- `GET /health` → **200** `{"status":"ok"}`.
- `GET /research/taxonomy → studies` carries the iter-18 copy verbatim:
  - **5 status labels**: Queued / Running / Done / Cancelled / Failed.
  - **4 per-status honest-absence sentences**, each DISTINCT (verified), the `cancelled` one
    flagging "PARTIAL … not a complete measurement", the `failed` one stating "never an empty or
    fabricated success".
  - **`hindsight_level_label`** = "Level chosen with hindsight" + caption ("excluded from any
    cross-study comparison").
  - **`measurement_framing`** = "These are journaled MEASUREMENTS … not a profitability claim, an
    edge, a win rate, or a forecast …" (anti-goal-clean — no edge/P&L/win-rate claim).
  - **`null_baseline_caption`** + **`truncated_caption`** present; `level_setups` /
    `state_native_setups` scoped correctly; disclaimer "Descriptive only — not trading advice."
- Frontend SSR for `/studies`, `/`, `/journal` → all **HTTP 200**; `/studies` SSR carries the real
  taxonomy copy ("Replay studies" title, `studies-title` testid, "Descriptive only" framing) and
  **zero** "Internal Server Error" text — not a disguised error page. `/` carries the enabled
  **Studies** nav entry.
- **Server start newer than newest committed file:** backend start epoch `1781256494` and frontend
  start epoch `1781256584` both **>** newest app-file mtime `1781226403`
  (`apps/frontend/components/StudyResultsView.tsx`, 2026-06-12 02:06). Code identity is fresh.
- **`config_fingerprint` of served studies: `69f5231b0c7f6006`** (matches the iter-18 reference).

### J-60/J-61 pixel substrate — verified present in the persistent dev DB
The persistent dev DB (`apps/backend/tapeology_journal.db`, gitignored, 2.6 MB) holds the complete
record set the **pixel** legs need (it accumulated the prior dev pass's seeds plus the prior
browser-qa run's API-created records — 20 studies total: 18 done / 1 cancelled / 1 failed). The
records are stored as JSON payload blobs and served verbatim. Each critical record was decoded and
checked this pass:

| id (prefix) | status      | setup × dir              | feed | partial | hindsight | setup n / null n | covers |
|-------------|-------------|--------------------------|------|---------|-----------|------------------|--------|
| `3177434f`  | done        | trend_continuation long  | sip  | false   | false     | 2 / 99           | J-60 **reference** — pinned anchors matched exactly: r_basis [0.3, 0.6], verdicts [invalidated, confirming] |
| `4b1e33c1`  | done        | trend_continuation long  | sip  | false   | false     | 2 / 99           | J-60 **re-run** — result payload **byte-equal** to `3177434f` (occurrences + null + aggregates + fingerprint + seed) |
| `1cbf130a`  | done        | absorption_reversal long | sim  | false   | false     | 1 / 100          | J-60 **seeded-sim** leg (SIM-REVERSAL): r_basis [0.2], verdict [confirming] |
| `6477d260`  | done        | level_break long         | sip  | false   | **true**  | 3 / 99           | J-61 **hindsight_level** label + `excluded_from_cross_study_aggregate=true` |
| `82077d4a`  | **cancelled** | absorption_reversal long | sim | **true** | false    | 1 / 100 (PARTIAL)| J-61 **cancelled + PARTIAL** — `status=cancelled`, `partial=true`, occurrence verdict [pending]; never presented as complete |
| `9c00f133`  | **failed**  | absorption_reversal long | sip  | false   | false     | 0 / 0            | J-61 **failed** — `status=failed`, explicit `error` ("invalid symbol …"), **zero fabricated occurrences** |

All carry `config_fingerprint=69f5231b0c7f6006` and `null_baseline_seed=1729`. The reference vs
re-run **result byte-equality** (the J-60 cross-check) was re-verified True this pass. The browser
agent can also create fresh studies live (create → `queued`/`running`/`done` is the J-60 monitor
leg; the unpaced fixture run completes in ~1 s, so transient frames must be captured promptly).

### REST honesty cross-checks (re-run live this pass)
- Unknown study id → **404** `{"detail":"no study with id 'does-not-exist-xyz'"}`.
- Level setup submitted WITHOUT a level → **422**
  `{"detail":"setup_type 'level_break' requires a level_price (a level is never guessed)"}`.
- `GET /research/studies` → **200**, 20 records served verbatim from the store.
- `GET /research/studies/{id}` (the cancelled record) → **200**, `{"study": {... status:cancelled,
  partial:true ...}}` — served verbatim.

### Backend regression
`cd apps/backend && .venv/bin/python -m pytest tests/` → **671 passed, 1 skipped, exit code 0**
(verified by exit code; full run, no `-q`) — unchanged from iter-18, zero regressions.

## Conditional frontend fix

**NONE.** The browser-run substrate is healthy and the committed `/studies` surface renders
correctly (verified via SSR + live backend request/response). No defect blocking a J-60/J-61
acceptance clause was found at the developer stage, so the spec's "conditional, tightly bounded"
frontend fix was **not** triggered.

## Files Changed

- **No app code changed.** `git diff --stat -- apps/` is empty; `git status --porcelain -- apps/`
  shows no tracked app-code modification or addition. Zero-tracked-code-change is the spec's
  central discipline this iteration.
- Operational only (both gitignored, untracked):
  - cleared `apps/frontend/.next` (corrupted production-build artifacts; dev server rebuilds clean,
    then cleared again for the browser-qa hand-off);
  - persistent dev DB `apps/backend/tapeology_journal.db` holds the J-60/J-61 record set above
    (seeded across the prior dev + browser-qa passes through the live `/research/studies` API).

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/`
Result: **671 passed, 1 skipped, 0 failed** (exit code 0; unchanged from iter-18).

## Substrate handed to browser-qa-agent

- **`.next` cleared** (gitignored; browser-qa starts its own fresh `next dev`).
- **All server processes stopped clean** — verified zero real `uvicorn` / `next dev` /
  `next-server` processes and both ports `:8650` / `:3650` FREE. The browser-qa step starts its own
  offset-port servers.
- Persistent dev DB seeded with the full J-60/J-61 record set above (`TAPEOLOGY_JOURNAL_DB`),
  including the `failed` record the prior handoff had flagged as missing.
- iter-18 designed UI test plan at
  `reports/phase-goal-i_will_be_super_rich_with_my_loved_ones-iter-18-ui-test-plan.md` (33 tests,
  never executed) is the starting point — re-use it, do not redesign from scratch.
- **Do NOT run `npm run build` into the shared `.next` before browser QA completes** (iter-2 /
  iter-18 lesson — that production build is exactly what corrupted the substrate; `prerender-
  manifest.json` artifacts were the smoking gun found on disk this pass).

## Known Issues / Gaps (honest)

- **All J-61 pixel legs now have a persisted record.** The one gap the prior handoff flagged — a
  credential-free `failed` study record — is **closed**: `9c00f133` is a persisted `failed` study
  with an explicit `error` and zero fabricated occurrences. (It carries `source/feed = sip`; in a
  credential-free env the `failed` record was produced via an invalid-symbol path during the prior
  browser-qa run. It renders correctly as an explicit failure, never an empty success.)
- **Live mid-run cancel is timing-sensitive.** The unpaced sim/reference studies finish in ~1 s, so
  a live cancel rarely wins the race (the spec anticipated this). The persisted `cancelled`+`partial`
  record (`82077d4a`) is the spec-blessed evidence; the browser agent should prefer rendering it
  over a flaky live cancel.
- **`.next` must stay dev-built.** It is cleared at hand-off and must be rebuilt only by `next dev`
  (browser-qa's own server), never by a production `npm run build` into the shared dir before
  captures complete.
- **This step produces no pixels.** Per the spec, the rendered-pixel proof (J-60/J-61 legs, J-68
  sentinel) is the browser-qa-agent's deliverable downstream; if the frontend is dead at that step,
  the iteration must conclude as **failed verification** (hard-flag), never a soft PASS on skips.

---

## Fix Notes (FIX MODE — review FAIL → conditional frontend fix)

**Date:** 2026-06-12 · **Agent:** developer (fix pass) · **Trigger:** reviewer FAIL (CRITICAL).

The browser-qa run that followed the prior dev pass exposed a real J-61 acceptance-clause defect,
so the spec's **"Conditional, tightly bounded"** frontend-fix clause (IN SCOPE) is now in effect.
This pass landed exactly one minimal fix inside the permitted studies-frontend boundary — no
backend, engine, provider, classifier, store, schema, config, or endpoint change.

### Triggering pixel evidence
- Review report: `reports/reviews/goal-i_will_be_super_rich_with_my_loved_ones-iter-19-review.md`
  (Verdict FAIL; CRITICAL on `StudyCreateForm.tsx:69`).
- Browser QA finding **UT-J-61-b**: submitting a `level_break` study with NO level *silently
  disabled the Run button* — no inline error, no toast, no API call. That violates J-61's
  "honest inline error from the backend 422 — never a guess, never a silent no-op" requirement.

### Root cause
`canSubmit` (StudyCreateForm.tsx) returned `false` whenever `requiresLevel && levelPrice.trim()===""`.
That courtesy-disable pre-empted the POST, so the backend's 422 — which exists and is correct —
could never reach the already-wired inline error banner. The button just sat disabled with no
explanation: a silent no-op.

### Fix (single file, minimal)
- `apps/frontend/components/StudyCreateForm.tsx` — removed the empty-level branch from `canSubmit`
  (and its now-unused `requiresLevel`/`levelPrice` deps), with a comment explaining the J-61
  rationale. The Run button is now ENABLED for a level setup with a blank level; submitting fires
  the POST, the backend returns 422, and `createStudy` → `onCreate` (page.tsx) → the existing
  `error` banner (lines 273–281) render the backend detail **verbatim**.
  - `handleSubmit` already omits `level_price` when the field is blank (it only sets it when
    `levelPrice.trim() !== ""`), so the blank-level POST goes through and the backend 422 fires —
    no client-side guess is ever inserted. The historical-source required-field disable is
    UNCHANGED (those are not a backend-honesty leg).
  - `requiresLevel` and `levelPrice` remain referenced (handleSubmit + the level input render), so
    no dead code / no unused-var.

### Why this respects the anti-goals & the data contract
- **Backend stays the validation authority** (architecture principle: no frontend business logic).
  The frontend no longer makes a client-side decision that hides the truth — it surfaces the
  backend's verbatim 422 instead of guessing a level or silently swallowing the action.
- No new displayed value, no second computation/serving path (the 422 detail is read verbatim from
  the owning endpoint `POST /research/studies`). Data-contract clean.
- Diff is confined to one studies-frontend component — inside the spec's permitted conditional-fix
  boundary; no backend/engine/schema/config/endpoint touched.

### Verification (this fix pass)
- **Type-check:** `cd apps/frontend && npx tsc --noEmit` → **exit 0** (no `npm run build`, so the
  shared `.next` is NOT corrupted — iter-2/iter-18 lesson honoured; `.next` left absent for
  browser-qa to own).
- **Backend regression:** `cd apps/backend && .venv/bin/python -m pytest tests/` →
  **671 passed, 1 skipped, exit 0** (unchanged — frontend-only fix, no backend impact).
- **Live 422 probe** (fresh uvicorn on :8799, then killed):
  `POST /research/studies {setup_type:"level_break", … no level_price}` →
  **HTTP 422** `{"detail":"setup_type 'level_break' requires a level_price (a level is never guessed)"}`
  — this is the exact string that now renders inline once the button is enabled.
  Taxonomy canary re-confirmed: `level_setups=['level_break','failed_move_fade']`,
  `hindsight_level_caption` present.
- **Servers clean:** the probe uvicorn was killed; zero `uvicorn` / `next dev` processes remain.

### Files Changed (this fix pass)
- `apps/frontend/components/StudyCreateForm.tsx` — removed the empty-level silent-disable from
  `canSubmit` so a level setup with a blank level surfaces the backend's honest 422 inline (J-61).

### Hand-off to browser-qa
Re-run the **UT-J-61-b** leg: select setup `level_break` with the level field BLANK, click **Run
study**, and capture the inline rose error banner showing
"setup_type 'level_break' requires a level_price (a level is never guessed)". The button is now
clickable; the prior silent-disable is gone. All other J-60/J-61/J-68 legs are unaffected by this
single-component change — the rest of the verified substrate above still stands.
