# Goal Iteration 27 — UI Test Results (LLM browser-qa pass)

**Phase:** goal-desk-iter-27
**Date:** 2026-07-30
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

---

**Overall:** 1/1 tests passed (0 skipped)

Scope for this run (goal-mode LEAN): **J-17 only.** J-01..J-16 are covered by deterministic
golden replay this iteration (out of scope for this dispatch per the pump's own instructions).

Precondition check: ambient frontend `http://localhost:3301` → 200, ambient backend
`http://localhost:8301/meta/ui-routes` → 200, Chrome MCP attached to the pinned CDP endpoint
successfully. Rebuilt-frontend precondition independently re-confirmed: both
`apps/frontend/.next/static/chunks/app/{layout,desk/page}.js` contain `localhost:8301` and do
**not** contain `localhost:8000` (grep re-run at dispatch start).

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-17 | A top-up asks the vendor only for the bars the frozen store cannot already prove | full-stack/browser | P1 | On a fixture-scoped rig, `/desk`'s Top-up Runs section shows 4-outcome counts incl. ≥1 `unchanged`, a tail-vs-full-lookback line, and ≥1 failed pair's own `requested_window`, legible in one 1440×900 screenshot with no horizontal scroll; ranked table renders as J-16 shipped it | Fresh fixture-scoped rig (own `.data` copy + own frontend build dir, never the ambient store/`.next`) produced a real top-up: `0 reused · 6 fetched · 2 unchanged · 4 failed`, `2 pairs asked for a tail window · 10 pairs asked for the full lookback window`, 4 failed `ZZZINVALIDXYZ` rows each showing `requested 2024-07-30 → 2026-07-30`; all rendered together in one screenshot at 1440×900 with `scrollWidth === clientWidth` (1425, no horizontal scroll); the same screenshot also shows the J-16 ranked table (13 columns, 2 ranked rows + 1 skipped row) rendering unchanged | PASS | `reports/qa/goal-desk-iter-27-evidence/J-17-topup-window-disclosure.png` |

---

## Passed Tests

### UT-J-17 — A top-up asks the vendor only for the bars the frozen store cannot already prove

**Verdict:** PASS
**Evidence:** `reports/qa/goal-desk-iter-27-evidence/J-17-topup-window-disclosure.png`

**Scoped-rig setup (per the iteration NOTES — never the operator's ambient `apps/backend/.data`,
and never the shared `apps/frontend/.next`, per the iter-26 lesson):**
- A fresh root under `$TMPDIR/desk-iter27-scoped-qa` with `TAPEOLOGY_BAR_DIR`,
  `TAPEOLOGY_DATASET_DIR`, `TAPEOLOGY_DESK_UNIVERSE_DIR`, `TAPEOLOGY_DESK_SCREEN_DIR`,
  `TAPEOLOGY_DESK_TOPUP_LOG_DIR`, `TAPEOLOGY_JOURNAL_DB` all pointed at fresh subdirectories.
- A scoped backend on `:8391` (fresh uvicorn process, scoped env vars) and a scoped frontend on
  `:3391` — a **full rsync copy** of `apps/frontend` (excluding `node_modules`/`.next`, with
  `node_modules` symlinked back to the real install) run with `next dev` from its own directory,
  so it builds its own `.next` and never touches the ambient `apps/frontend/.next` the `:3301` pair
  now correctly uses.

**Data seeded (via the real running scoped backend, real keyless Yahoo network calls — never a
fixture pretending to be live):**
- A 3-symbol universe snapshot (`AAPL`, `MSFT`, `ZZZINVALIDXYZ`) registered directly via
  `UniverseStore.record()` (the canonical writer, same one the real fetch path uses).
- `AAPL` pre-seeded with real bars for all 4 top-up timeframes (`1h/4h/1d/1w`), reaching from
  `2024-05-21` through `2026-07-30` (today) — deep enough to pass the top-up's own 730-day
  lookback start, and current enough that a subsequent tail request finds nothing new for two of
  the four timeframes.
- `MSFT` and `ZZZINVALIDXYZ` left with nothing frozen (`ZZZINVALIDXYZ` is not a real ticker —
  Yahoo genuinely returns no data for it).

**Real top-up run triggered** (`POST /research/desk/topup/compute` on the scoped backend, actual
Yahoo vendor calls, no test doubles) over the 3×4 = 12 pairs; polled to `state: "done"` (~2.4s).
Recorded run (`GET /research/desk/topup/runs` on the scoped backend):

- **`0 reused · 6 fetched · 2 unchanged · 4 failed`** (12 pairs total).
  - `unchanged` (2): `AAPL 1h`, `AAPL 4h` — a real vendor call on the tail window returned only
    bars already registered (`BarSeriesAlreadyRegistered`, 409) → correctly classified
    `"unchanged"`, not `"failed"`.
  - `fetched` (6): `AAPL 1d`/`1w` (tail window, genuinely new content), `MSFT` ×4 (nothing frozen
    → full lookback → real new data).
  - `failed` (4): `ZZZINVALIDXYZ` ×4 — genuinely no vendor data for an unknown symbol, each with
    its own `requested_window` recorded (`2024-07-30 → 2026-07-30`).
- **`window_basis`: 2 `"tail"`** (`AAPL 1d`, `AAPL 1w`) **· 10 `"full_lookback"`** (`AAPL 1h`/`4h`
  — real Yahoo-served content for the tail request coincided with what was already frozen; `MSFT`
  ×4; `ZZZINVALIDXYZ` ×4).
- `config_fingerprint` on the recorded run: **`08e471b10130e1e2`** (unchanged).

**Browser verification** (scoped frontend `:3391`, viewport set to 1440×900 before navigating):
navigated to `/desk`; `document.documentElement.scrollWidth === clientWidth === 1425` (< 1440 —
no horizontal scroll). A bonus real screen compute (`POST /research/desk/screen/compute`,
`screen_date: 2026-07-30`) was also triggered on the same rig so the J-16 ranked-table regression
check could be captured in the SAME screenshot. The rendered page shows, top to bottom: Provenance
(fingerprint `08e471b10130e1e2`), the Briefing ranked table (13 columns: rank/symbol/side/class/
distance/score/coverage/tick evidence/basis/history/band/opposite/levels — 2 ranked rows `AAPL`
class A resistance, `MSFT` class A support — matching J-16's shipped layout unchanged), Skipped
Members (`ZZZINVALIDXYZ`, `reason: no bars`), and the Top-up Runs section reading, verbatim:

> `state: done   12 of 12 pairs attempted   0 reused · 6 fetched · 2 unchanged · 4 failed`
> `2 pairs asked for a tail window · 10 pairs asked for the full lookback window`
> `Failed pairs (4)` — each of the 4 `ZZZINVALIDXYZ` rows shows its own detail plus
> `requested 2024-07-30 → 2026-07-30`.

All three TC-6/acceptance elements (four-outcome counts incl. `unchanged` > 0, the tail-vs-full
descriptive line, a failed pair's own `requested_window`) are visible together in ONE screenshot,
along with the unchanged J-16 ranked table — `J-17-topup-window-disclosure.png`. (Note: a plain
viewport-clipped `screenshot` action returned a blank frame at this scroll depth in this headless
session — a rendering/compositing quirk with the sticky nav bar, not a product defect;
`fullpage: true` captures correctly and was used instead. Confirmed independently: `elementFromPoint`
at the target viewport coordinates resolved to the real "Latest run" DOM node with real text
content while the plain screenshot mode returned blank, isolating the issue to the screenshot
capture path, not the page render.)

**Teardown / append-only proof:** the scoped backend (`:8391`) and frontend (`:3391`) processes
were killed via `fuser -k -9` on both ports at the end of this pass (confirmed free via `ss -tln`).
The ambient `apps/backend/.data` store was never pointed at by any env var used in this rig;
verified afterward: `GET http://localhost:8301/research/desk/topup/runs` still shows exactly 1 run
(`topup-2026-07-29-5de907c83fc4`, unchanged) and `GET http://localhost:8301/research/desk/universe`
still shows exactly 1 snapshot (101 real members, unchanged) — identical to before this QA pass.
`git status --short apps/ scripts/ config/` is empty (zero code change, as the iteration spec
requires); `Config().config_fingerprint()` → `08e471b10130e1e2`. The ambient `:3301`/`:8301` pair
was independently re-curled afterward and still serves correctly (200/200).

**Genuine-new-capture check:** `md5sum` of the new screenshot does not match the iter-26 J-17
screenshot or the iter-26 ranked-table-regression screenshot (all three distinct files).

---

## Golden replay scripts

- **`runs/goal-session-desk/journey-scripts/J-17.json` — written (REQUIRED this run, not
  best-effort).** J-17's full acceptance depends on specific outcome counts (`unchanged`,
  tail-vs-full-lookback, a particular failed pair) produced only by a throwaway fixture-scoped rig
  that no longer exists after teardown — a future replay against the STANDARD ambient
  `:3301`/`:8301` pair cannot reproduce those exact numbers (the ambient store holds only the one
  legacy, pre-iter-26 top-up run, `topup-2026-07-29-5de907c83fc4`, 404 pairs, which structurally
  lacks the `unchanged` outcome and the `window_basis` field entirely — confirmed via direct query:
  `0 reused · 390 fetched · 0 unchanged · 14 failed`, no `window_basis` on any outcome).
  Rather than skip the golden (as iter-26's QA did, for exactly this reason), this run writes an
  honest **partial proxy** — mirroring J-06's precedent — that asserts the part of J-17's shipped
  behavior that IS stable and durable against the ambient pair: the extended four-outcome counts
  line rendering correctly with the ambient run's own real numbers
  (`0 reused · 390 fetched · 0 unchanged · 14 failed`), the honest
  `"window basis not recorded in this run"` legacy-absence fallback (both the summary line and,
  implicitly, that no per-pair `requested_window` exists to render instead), and the
  `"Failed pairs (14)"` count. This exercises the SAME shipped code path (`topupOutcomeCounts`,
  `topupWindowBasisCounts`, `WINDOW_BASIS_NOT_RECORDED`) that the full fixture-scoped acceptance
  exercises — just on the ambient run's legacy data rather than a fresh `unchanged`-bearing one.
  **Verified against the real ambient pair with the actual (non-LLM) replay tool before finishing
  this dispatch:** `python3 scripts/automation/lib/demo_runner.py --mode verify --scripts-dir
  runs/goal-session-desk/journey-scripts --journeys J-17 --base-url http://localhost:3301` →
  `1/1 journeys passed (0 skipped)`, verdict PASS. Lint also clean:
  `python3 scripts/automation/lib/demo_runner.py --mode lint --scripts-dir
  runs/goal-session-desk/journey-scripts --journeys J-17` → `J-17 ok`.
  **Caveat for future maintainers:** this golden will need an update (not just an ambient-data
  refresh) if the ambient store's one legacy run is ever superseded by a new ambient top-up run —
  at that point the specific counts asserted here would need re-deriving from whatever the new
  ambient "latest" run actually shows, OR the assertions would need loosening to structural
  presence checks only. No existing golden script (J-01..J-16) clicks a Top-up/Run Screen button
  against the ambient pair, so this is not expected to happen from ordinary replay traffic.

---

## Environment

- **Frontend URL (dispatch-assigned, used for precondition checks):** http://localhost:3301
- **Frontend URL (used for J-17 fixture-scoped evidence capture):** http://localhost:3391 (fresh
  scoped instance stood up by this QA pass — own directory copy, own `.next`, own port —
  `NEXT_PUBLIC_API_URL=http://localhost:8391`, torn down at the end of this pass)
- **Backend URL (used for J-17 fixture-scoped evidence capture):** http://localhost:8391 (fresh
  scoped instance, fixture-scoped `.data`, torn down at the end of this pass)
- **Ambient pair (unaffected, independently re-verified before and after):**
  http://localhost:3301 / http://localhost:8301
- **Browser:** Chrome via `mcp__plugin_superpowers-chrome_chrome__use_browser` (headless, CDP
  `127.0.0.1:9222`)
- **Test Date:** 2026-07-30
- **Evidence directory:** `reports/qa/goal-desk-iter-27-evidence/`
