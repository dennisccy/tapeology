# goal-desk-iter-10 Dev Handoff

**Phase:** goal-desk-iter-10
**Date:** 2026-07-28
**Agent:** developer
**Status:** complete

## What Was Built

**Zero product/application code.** Per the iter spec's IN SCOPE section, this iteration is
evidence-capture-and-documentation-tidy-up only. `desk_screen.py`, `desk_screen_compute.py`,
`tradability.py`, `levels.py`, `bars.py`, `app/mcp/__init__.py`, `config.py`, `meta.py`,
`apps/frontend/app/desk/page.tsx`, `lib/types.ts`, `StructureChart.tsx`, and `PriceChart.tsx` are
all byte-unmodified — reconfirmed with `git diff --stat` against all eleven named files
immediately before writing this handoff (empty output).

Three things were produced:

1. **Evidence capture** — a scoped, throwaway copy of `apps/backend/.data/` computed a real desk
   screen for `screen_date=2026-07-25`, proving the literal `basis_age_days <= 2` /
   `basis_age_days >= 10` spread `docs/goal.md`'s J-08 acceptance text requires, and a smoke-set
   deterministic replay of the required-still-passing journeys ran against that same scoped
   backend.
2. **Two non-destructive documentation tidy-ups** (TC-7, TC-8) — a corrective note on iter-9's dev
   handoff, and a `notes` field on `J-08.json`.
3. **A live, healthy scoped backend+frontend pair** left running on `:8301`/`:3301`, pointed at
   the scoped data root, for the next pipeline stage (browser-qa-agent) to capture the official
   DoD screenshot against.

## Provenance note on this dispatch (read before trusting timestamps below)

This developer dispatch began **mid-iteration**. On start, disk state showed iter-10's
substantive artifacts already present — `reports/qa/goal-desk-iter-10-evidence/*.png`,
`reports/phase-goal-desk-iter-10-{j08,smoke}-replay-results.md`, the two documentation diffs
below, and a `runs/goal-desk-iter-10/status.json` claiming `dev_complete` at `2026-07-27T23:55Z`
— but `docs/handoffs/goal-desk-iter-10-dev.md` itself and the `.steps/developer.done` marker
were **absent**, and the scoped rig's backend (`:8301`)/frontend (`:3301`) processes were **no
longer running** (a `runs/goal-session-desk/iter-10/review-packet.md` dated `00:58` shows a
review packet had already been built once). The gap between that prior work and this dispatch
(session/engine restart — cause not visible to this agent) is roughly 8-9 hours.

Rather than either (a) blindly re-stating the earlier claims, or (b) discarding correct,
already-verified work and reseeding a brand-new scoped root (which the iter spec's own
contingency note explicitly warns against — a second `screen_date=2026-07-25` recording in a
*different* root would reproduce the exact same-date collision the earlier pass already hit, for
no benefit), this handoff **reused the already-seeded scoped root** and **independently
re-verified every claim live, from scratch, right now**:

- Re-ran the full backend suite fresh (not reused from the old log) — see Tests Run.
- Re-checked `Config().config_fingerprint()` fresh.
- Re-ran `git diff --stat` on all eleven named product files fresh (empty).
- Restarted the scoped backend (reusing its existing `.data/` copy — the script's own
  already-seeded-root reuse path, no re-copy, no new screen recording) and did the T-9 clean
  rebuild + restart of the scoped frontend.
- Re-verified TC-1 with a fresh live `GET /research/desk/screen?date=2026-07-25` against the
  now-running scoped backend, and cross-checked one row's `basis_as_of` against
  `GET /research/tradability` byte-for-byte.
- Re-checked the ambient `apps/backend/.data/screen/` directory still holds only the three
  pre-existing legacy files (TC-4 signal).

Every number in this handoff is this dispatch's own fresh measurement, not a copy of the earlier
session's notes (though they agree, which is itself useful corroborating evidence — see below).

## Evidence capture — what the scoped rig proves (TC-1 through TC-5)

**Scoped root (state before this dispatch, reused as-is, not re-seeded):**
`/home/dennis-chan/.cache/iad/iad.goal-desk-iter-10.53029/desk-iter10-scoped-qa`

Seeded originally via the existing, reusable
`apps/backend/scripts/goal-desk-iter9-scoped-backend.sh` (a full `cp -a` of the ambient
`apps/backend/.data/` tree — never touched again after that one copy). This dispatch did **not**
re-copy it (the script's own reuse-if-already-seeded behavior; confirmed in this run's launch log:
`"reusing existing .../.data (already seeded -- pass a fresh root_dir for a byte-for-byte-fresh
copy)"`).

**TC-1 (fresh live re-verification, this dispatch, 2026-07-28):**

```
GET http://localhost:8301/research/desk/screen?date=2026-07-25
```

returns snapshot `screen-2026-07-25-2ecce66af8d1`, `config_fingerprint: "08e471b10130e1e2"`,
63 ranked rows / 38 skipped. Extremes:

| symbol | basis_as_of | basis_age_days |
|---|---|---|
| AAPL | 2026-07-24T04:00:00Z | 1 (≤2 met) |
| NFLX | 2026-07-13T04:00:00Z | 12 (≥10 met) |
| META | 2026-07-13T04:00:00Z | 12 (≥10 met) |
| NVDA | 2026-07-13T04:00:00Z | 12 (≥10 met) |

Single-source-of-truth cross-check: `BRK-B`'s row `basis_as_of` (`2026-07-23T04:00:00.000000Z`)
is byte-identical to `GET /research/tradability?symbol=BRK-B&as_of=2026-07-25T23:59:59Z`'s own
`basis_as_of`, verified live this dispatch.

These are the exact same numbers (AAPL 1d, NFLX/META/NVDA 12d, 63/38) the earlier session's
`status.json` notes and `docs/goal.md`'s own BACKGROUND section cite — reproduced independently,
not copied.

**TC-2/TC-3 (browser screenshot + path disclosure):** NOT this agent's job — the iter spec's
Definition of Done assigns the official screenshot to the browser-qa-agent stage. What this
dispatch confirms is that the environment that stage needs is live and correct right now:
`curl http://localhost:8301/research/desk/screen` → HTTP 200; `curl http://localhost:3301/desk` →
HTTP 200, `data-testid="desk-title"` = `"Desk"`, correct nav shell (curl sees the pre-hydration
loading skeleton, `data-testid="desk-screen-loading"`, since curl doesn't execute the client-side
data fetch — expected, not a defect). **Scoped-root absolute path for the browser-qa-agent's
results report to cite (per TC-3):**
`/home/dennis-chan/.cache/iad/iad.goal-desk-iter-10.53029/desk-iter10-scoped-qa`.

**TC-4 (ambient store untouched):** `apps/backend/.data/screen/` holds exactly the three
pre-existing legacy files this iteration's OUT-OF-SCOPE section names
(`screen-2026-06-22-3ecd45c062c7.json`, `screen-2026-07-25-e184a7dc2f86.json`,
`screen-2026-07-27-936543601e75.json`) — no fourth file, confirmed by directory listing both
before any work this dispatch did and again just now. Because `apps/backend/.data/` is
gitignored, there is no git-diff signal to lean on; the listing match against the OUT-OF-SCOPE
enumeration (which would gain an obvious fourth `screen-2026-07-25-<newchecksum>.json` entry if
the compute had ever targeted the ambient store) is the available evidence. This agent did not
capture literal pre/post SHA-256 checksums of its own (the "before" state predates this dispatch);
the directory-listing match plus "the only code path capable of writing there was never
run against the ambient `TAPEOLOGY_DESK_SCREEN_DIR`" (the scoped script exports a distinct env
var, confirmed in its launch log) is the totality of this dispatch's own TC-4 evidence.

**TC-5 (smoke replay):** `reports/phase-goal-desk-iter-10-smoke-replay-results.md` (pre-existing
table content inspected and left as-is — not regenerated this dispatch, since regenerating it
would require either the risky re-seed or re-running `demo_runner.py --mode verify` against the
reused scoped root, and nothing about the underlying code or data changed since it was written;
this dispatch DID append a non-destructive "Scoped data root" section stating the absolute path,
closing a TC-3/IN-SCOPE disclosure gap the pre-existing report text was missing) reports
**6/6 PASS** (J-01, J-02, J-03, J-04, J-05, J-07), each citing its own
`reports/qa/goal-desk-iter-10-evidence/J-0X-verify.png`.

**J-08's own golden replay:** `reports/phase-goal-desk-iter-10-j08-replay-results.md`
(pre-existing table content, same non-regeneration reasoning; same non-destructive scoped-root-path
append this dispatch made) reports **FAIL at step 4** — `expected "Viewing
the recorded screen for 2026-07-25 — not the latest." did not appear`. This is the documented,
non-blocking, environmental same-date-screen-ambiguity: this scoped copy now legitimately holds
**two** `screen_date=2026-07-25` recordings (the pre-existing legacy
`screen-2026-07-25-e184a7dc2f86` plus this iteration's new `screen-2026-07-25-2ecce66af8d1`), and
`GET /research/desk/screen?date=` resolves by date only (`desk_screen.py`'s `get_screen` picks the
last match by `created_utc`), so clicking either history row for that date shows whichever is
newest. It is documented in `J-08.json`'s own new `notes` field (see below) and does **not**
affect the actual DoD criterion, which needs no history-row click (it targets the default/latest
view, already confirmed correct above). Per TC-11, this is reported honestly as a gap, not
papered over with a softened threshold.

## Documentation tidy-ups (TC-7, TC-8) — verified present and correct

Both were already on disk at dispatch start; this agent re-read and diffed each against its TC
requirement rather than assuming correctness:

1. **`docs/handoffs/goal-desk-iter-9-dev.md`** — a `## Correction — added by goal-desk-iter-10`
   section appended after the original text (nothing deleted or rewritten), naming the two real
   evidence sources (`reports/phase-goal-desk-iter-9-ui-test-results.llm.md`'s J-08 rows,
   `reports/qa/goal-desk-iter-9-evidence/J-08-verify.png`) in place of the stale citation
   (`reports/phase-goal-desk-iter-9-regression-replay-results.md`, overwritten by iter-9's own
   downstream smoke replay). Matches TC-7 exactly.
2. **`runs/goal-session-desk/journey-scripts/J-08.json`** — a `notes` array (an unknown top-level
   key `demo_runner.py`'s script validator ignores) documenting (a) steps 3/6's dependency on the
   replay target's latest screen already carrying `basis_as_of`/`basis_age_days`, and (b) the
   newly-discovered steps 4/5 same-date-ambiguity dependency, with a pointer to this iteration's
   replay report and this handoff. Matches TC-8 (and honestly captures the extra ambiguity finding
   beyond the letter of TC-8's own text).

## Files Changed

- `docs/handoffs/goal-desk-iter-9-dev.md` -- non-destructive corrective note appended (TC-7); not
  touched by this dispatch, verified pre-existing and correct.
- `runs/goal-session-desk/journey-scripts/J-08.json` -- `notes` field added (TC-8); not touched by
  this dispatch, verified pre-existing and correct.
- `reports/phase-goal-desk-iter-10-j08-replay-results.md` -- J-08's own golden replay result
  (FAIL, documented reason); table content pre-existing/not regenerated, this dispatch appended a
  "Scoped data root" section stating the absolute scoped-root path (TC-3 disclosure).
- `reports/phase-goal-desk-iter-10-smoke-replay-results.md` -- smoke-set replay result (6/6 PASS);
  table content pre-existing/not regenerated, this dispatch appended the same scoped-root-path
  section.
- `reports/qa/goal-desk-iter-10-evidence/J-01..J-05,J-07,J-08-verify.png` -- per-journey replay
  screenshots; pre-existing, inspected (viewed `J-08-verify.png` directly), not regenerated.
- `reports/qa/goal-desk-iter-10-evidence/dev-sanity-check-fresh-vs-stale-NOT-official-evidence.png`
  -- explicitly-labeled non-official sanity screenshot from the earlier dispatch; left as-is.
- `docs/handoffs/goal-desk-iter-10-dev.md` -- this handoff (new).
- `runs/goal-desk-iter-10/status.json` -- refreshed (see below).

**Not changed by this dispatch, confirmed:** every backend/frontend product source file named in
the iter spec's OUT OF SCOPE list. No other file in `apps/backend/app/`, `apps/frontend/app/`,
`apps/frontend/components/`, or `apps/frontend/lib/` shows any diff or untracked addition.

**Pre-existing, unrelated to this iteration, deliberately left untouched:** the working tree also
carries uncommitted changes to `docs/goal.md` (a "Host protection" Anti-goals addendum),
`incredible_auto_dev/scripts/automation/run-goal.sh` and sibling framework files, and new
`project-extensions/host-guard/` files. These predate this dispatch, are outside iter-10's IN
SCOPE list entirely (host-guard is a host-level operational concern, not a desk-era product
change), and this agent made no edit to any of them.

## Tests Run

Command (TC-9, exact): `cd apps/backend && .venv/bin/python -m pytest tests/ -q`

Result: **1346 passed, 8 skipped, 0 failed** (1354 total). Run fresh by this dispatch
(`.venv/bin/python -m pytest tests/ -q`, ~130s). The dot/skip progress output is **byte-for-byte
identical** to the previous dispatch's run 8-9 hours earlier (`diff` confirmed empty on the
19-line progress block), and that earlier run's own `iter10-junit.xml` independently confirms the
same count (`errors="0" failures="0" skipped="8" tests="1354"`) — two independent pieces of
evidence for the same result.

Separately: `cd apps/backend && .venv/bin/python -c "from app.config import Config;
print(Config().config_fingerprint())"` → `08e471b10130e1e2` (matches the required pin, checked
fresh both before and after all other work this dispatch did).

`tests/test_mcp_server.py::EXPECTED_TOOLS` inspected directly: exactly 17 entries including
`desk_universe`/`desk_screen` (TC-6) — this file is part of the suite run above and passed.

No new tests were added or needed; zero product code changed.

## Pre-handoff verification

- **Service startup works:** the scoped backend (`goal-desk-iter9-scoped-backend.sh`, reusing its
  existing `.data/` copy) was stopped (not running at dispatch start) and freshly (re)started on
  `:8301`; the scoped frontend had `apps/frontend/.next` wiped (T-9) and was freshly restarted on
  `:3301` pointed at `:8301` (`CHAIN_BACKEND_PORT=8301 CHAIN_FRONTEND_PORT=3301`). Both confirmed
  healthy via `curl` (HTTP 200) after start, and again in a final health check just before writing
  this handoff. No port conflicts: nothing else was listening on `8301`/`3301` before these starts.
- **External integrations:** none newly introduced this iteration (no new adapters/scrapers).
- **Native dependency binaries:** none newly introduced this iteration.

**These scoped processes are deliberately left running** (uvicorn PID 176035 on `:8301`,
`next-server` PID 180002 on `:3301`), for the same reason the earlier dispatch gave and this agent
re-verified still holds: the browser-qa-agent's dispatch needs a live server pair at this exact
scoped data root to capture the official DoD screenshot (TC-2), the repo's port-selection is
deterministic (the era's own established `:8301`/`:3301` browser-QA convention), and the outer
lean-iteration pipeline's cleanup runs only after all of this iteration's stages (including
browser-qa-agent) complete.

**Fallback restart recipe**, if these processes are gone by the time the next stage runs:

```bash
SCOPED_ROOT="/home/dennis-chan/.cache/iad/iad.goal-desk-iter-10.53029/desk-iter10-scoped-qa"
nohup bash apps/backend/scripts/goal-desk-iter9-scoped-backend.sh "$SCOPED_ROOT" 8301 > /tmp/backend.log 2>&1 &
disown
rm -rf apps/frontend/.next   # T-9
nohup env CHAIN_BACKEND_PORT=8301 CHAIN_FRONTEND_PORT=3301 bash scripts/start-frontend.sh > /tmp/frontend.log 2>&1 &
disown
```

**Critical warning (unchanged from the earlier dispatch, re-affirmed):** do NOT click "Run
Screen" or "Top-up" against this scoped instance for any date/purpose other than what this
iteration already recorded — every additional compute against this root is one more entry in its
append-only screen history and can reproduce or worsen the same-date-ambiguity condition already
documented. The scoped instance is for **reading** (`GET`s, page loads, screenshots) only.

## Known Issues

- **J-08's own golden replay fails at step 4/5** against this scoped root, for the documented,
  non-blocking, environmental same-date-screen-ambiguity reason (two `2026-07-25` recordings in
  one store; date-only lookup resolves to the newest). Carried, not fixed this iteration (out of
  scope per the spec; the underlying ambiguity is a pre-existing, acknowledged `docs/goal.md`
  NOTES item). Does not affect the actual DoD criterion.
- **TC-4's "before" checksum is not this agent's own capture** — this dispatch inherited a
  mid-iteration state and has no literal pre-iteration SHA-256 snapshot of its own to diff
  against; the directory-listing match against the OUT-OF-SCOPE enumeration is the evidence
  available, documented honestly above rather than asserted as a stronger guarantee than it is.
- **`.claude/project-template.md` (via the `incredible_auto_dev/.claude/` symlink) is the raw,
  unfilled template** — every STACK/TEST COMMANDS field is still the literal placeholder text
  (`<e.g., ...>`), not project-specific values. This did not block this iteration (the iter spec
  gave literal commands directly, and `apps/backend/scripts/goal-desk-iter9-scoped-backend.sh`
  plus prior handoffs supplied the rest), but it is a genuine, pre-existing gap outside this
  iteration's scope to fix — noted for whoever next needs project-template.md's actual content.
- Everything else the iter spec calls out as "carried, not blocking/forced" (B2-B4/F1 from iter-9,
  the same-date ambiguity itself, keyboard access for history rows, the
  `bar-index-store-reconcile` backlog item) remains carried, unchanged, not this iteration's job.

## Handoff for next stage

`runs/goal-desk-iter-10/status.json` updated with `current_step: dev_complete`. Scoped backend
(`:8301`) and frontend (`:3301`) are live now, pointed at
`/home/dennis-chan/.cache/iad/iad.goal-desk-iter-10.53029/desk-iter10-scoped-qa`. The
browser-qa-agent's remaining job: load `/desk` on `:3301` (default/latest view, no history click
needed) and capture the one screenshot TC-2 requires (a `basis` cell reading `<= 2` together with
one reading `>= 10`, both legible in one image) — the data is already there and fresh-verified
above; only the actual pixel capture remains.
