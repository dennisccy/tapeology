# Iteration State — desk

**After iteration:** 5 · **Date:** 2026-07-26 · **Verdict:** CONTINUE

## Journeys

4 passing (J-01 J-02 J-03 J-04) · 2 failing (J-05 J-06) · 1 partial (J-07 — only its "MCP = 17 tools" clause unmet, at 15) — 7 total

## Active blockers

- **Dev, do FIRST next iteration:** `runs/goal-session-desk/journey-scripts/J-04.json` step 5 clicks "Run Screen" — replaying that golden against the AMBIENT backend records a real screen snapshot into `apps/backend/.data/screen`. Scope the replay lane's data dirs or drop the click / assert read-only content only.
- **HUMAN (owner) call, now 2 iterations old:** `docs/goal.md` still lists `apps/backend/app/research/bars.py` + `apps/frontend/components/StructureChart.tsx` as untouched this era; both changed in iter-4 under a developer-written spec amendment. Owner ratifies in `docs/goal.md` or the two files revert (minor/unresolved in `journey-history.json`). Does NOT block J-05 or J-06.
- Nothing else blocked — J-05 and J-06 are both keyless, unblocked and tractable.

## Last 2 verdicts

- iter 5: CONTINUE — J-04 `partial → passing`: the never-existing "Run Screen running + second click refused" screenshot was finally captured on a fixture-scoped backend (evaluator opened all 4 shots and pixel-diffed the two running ones); suite 1328p/8s/0f, pin `08e471b10130e1e2`, ambient `.data/` byte-identical, COHERENCE-PASS, product diff = README prose + 1 QA script only.
- iter 4: CONTINUE — `/desk` shipped and worked, but `browser-qa-agent` never dispatched, so one required screenshot did not exist anywhere ⇒ J-04 held at `partial`. COHERENCE-WARN.

## Do not redo

- **J-04 is DONE and fully evidenced** — page, controls, provenance, chips, skip grouping, single-flight; 4 current screenshots in `reports/qa/goal-desk-iter-5-evidence/` + a linted golden at `journey-scripts/J-04.json`. Do not rebuild or re-photograph it; only fix the golden's write-click.
- **J-01 + J-02 + J-03 DONE, clause-verified** (`state/journey-history.json`), re-verified passing in iter-5 with browser-rendered payloads. Re-check only suite + pin + zero-diff on their owners.
- **The fixture-scoped QA recipe exists and works:** `apps/backend/scripts/qa_desk_iter5_fixture_scoped_backend.sh <fresh-root> <port>` (6+1 `TAPEOLOGY_*` vars; PG-only bars ⇒ 1 ranked row + 102 honest `no_bars`). Reuse it — never run a browser pass against the ambient store.
- **`reports/qa/goal-desk-iter-4-qa.md` stays discredited and untouched**; iter-5's `ui-test-results.md` is the authoritative record. Do not cite or "fix" the iter-4 file.
- **Settled:** zero new `Config` field all era; chip copy "nearest same-class band" (`_select_best_band` byte-unchanged); `bar_store_signature` labelled "Bar-store signature", "window last requested" only on coverage tooltips; Run Screen submits the client's today; price-less rows excluded-and-reported on the merged read, never deleted.
- **Hygiene only when those files are open:** guard `run_screen_and_record` like the POST route (B1); apply `_has_finite_prices` to the per-series read (B2); re-tighten `test_structure_chart_viewport.py:194`. Suite floor **1328p / 8s**; J-07 stays `partial` until MCP = 17 tools.
