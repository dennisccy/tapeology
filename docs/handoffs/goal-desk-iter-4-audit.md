# goal-desk-iter-4 Audit Report

**Date:** 2026-07-26
**Auditor:** Hard audit pass — skeptical, evidence-based (re-audit after the fix pass that answered this file's prior FAIL)

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

J-04's goal is genuinely achieved: `/desk` ships as a real third page, the nav is
Cockpit · Structure · Desk (verified three ways), every rendered value is a verbatim re-format of
its owning endpoint, and the prior audit's CRITICAL (priceless `NaN` bars poisoning the append-only
`BarStore` and unmounting `/structure`) is closed structurally at the write seam, the write path and
the shared merged read — which I re-verified against the REAL store, not the handoff's summary. What
remains is not product defect but **evidence-lane defect**: the browser-QA lane named in DEFINITION
OF DONE #1 never ran this iteration, and the QA report on disk certifies several states that
contradict the shipped code and itself. I closed the worst of it myself by re-running the
deterministic replay lane against the fixed tree (the only replay result on file was a pre-fix
false-negative) and by repairing the self-contradictory acceptance case that misled QA; the rest is
documented below and must not be read as verified.

---

## 2. Findings

### Backend Findings

**B1 — GAP (gap): the no-universe refusal guards the route, not the write path.**
`desk_routes.py:310-325` refuses `POST /research/desk/screen/compute` with 422 when
`universe_store.list()` yields no readable records — exactly what the spec asked for, and its test
(`test_desk_screen_compute.py::test_post_trigger_with_no_universe_registered_refuses_and_persists_nothing`)
asserts zero records before AND after plus `manager.snapshot() is None`. But the refusal sits one
layer above the single writer: `compute_screen` still documents and performs "no universe snapshot
registered -> an honest empty walk" (`desk_screen.py:273-274`), and `run_screen_and_record`
(`desk_screen_compute.py:97-120`) will still persist that empty snapshot — so
`python -m app.research.desk_screen_compute --date <d>` on a machine with no universe registered
writes the same permanent, useless append-only record the audit finding was about. The spec scoped
the refusal to the POST, so this is a GAP, not a spec breach; it is worth writing down because the
same fix pass argued the opposite discipline for B1's own rail ("checked here rather than in each
caller so it holds for every write path", `bars.py:614-628`). A one-line guard in
`run_screen_and_record` would make the refusal structural for the CLI too.

**B2 — GAP (gap): the priceless-bar rail covers the merged read, not the per-series read.**
`BarStore._merged_rows` excludes non-finite rows and reports them (`bars.py:516-547`), and
`GET /research/candles` — the endpoint both chart pages actually use — is therefore clean (verified
live: 500 bars, 0 null-priced). The per-series route `GET /research/bars/{bar_series_id}/candles`
(`routes.py:791-834`) reads `store.candles(...)`, i.e. the stored truth, so it still serves
`"open": null` for the 60 series on disk, and that route has no `integrity_errors` channel at all to
say so. This is deliberate (`test_bars.py::test_a_planted_priceless_series_still_passes_both_checksums`
asserts the per-series read serves the stored rows verbatim) and harmless today — `fetchBarCandles`
(`lib/api.ts:583`) has no UI caller, so no page can be handed a null candle — but a future
per-series chart would inherit the original crash, and the MCP/REST consumer of that route gets a
`null` price with no honest marker.

**B3 — OBSERVATION (gap): the derived `bar_index` still counts the excluded row.**
The exclusion lives on the merged read only, so for an affected pair the index's `bar_count` /
`latest_window_end_utc` (and therefore `/desk`'s coverage badges and `bar_store_signature`) describe
one row the merged read no longer serves. The page's new `desk-coverage-divergence-note`
(`app/desk/page.tsx:216-224`) explains the general "two independent reads" divergence, which covers
this honestly enough for a briefing; recording it so a future iteration does not read the two
counts as one number.

### Frontend Findings

**F1 — GAP (gap): a failed mount-time compute GET leaves an in-flight job unpolled.**
`app/desk/page.tsx:656-658` sets `screenCompute` only `if (result.ok)`, and the poll effect starts
only when `screenCompute?.state === "running"` (line 672). If the mount GET fails transiently while
a job IS running, the page shows no progress and leaves "Run Screen" enabled. It self-heals — a
click returns `started: false` with the same job snapshot (verified live, §3) and polling then
begins — so no fabricated state is ever shown, which is the anti-goal that matters. Flagged by the
reviewer as a NOTE; I agree with GAP.

**F2 — OBSERVATION (gap): two-decimal formatting can render distinct distances identically.**
`fmt(row.distance_bps)` (`app/desk/page.tsx:196-198`) renders anything below 0.005 bps as
`0.00 bps`; the ranking is by the served value, so two adjacent rows can read the same number while
being ordered by a difference the operator cannot see. The served value is on the cell's `title`,
which is the right mitigation for the scanability problem F3 fixed; a future iteration may prefer
significant digits over fixed decimals for this one column.

**F3 — OBSERVATION (gap): the "nearest same-class band" caption is unconditional.**
It renders for every row with a non-null `band_class` (`app/desk/page.tsx:186-195`) rather than only
where the headline band differs from the symbol's highest-scoring same-class band ("where
applicable", spec TC-14). The frontend handoff documents the reading, and the copy is true of
`_select_best_band`'s tuple in every case, so the caption is never false — only sometimes
uninformative.

### Test Findings

**T1 — IMPORTANT (gap, NOT auditor-fixable): the QA report certifies states that contradict the
shipped code and itself.**
`reports/qa/goal-desk-iter-4-qa.md` was written at 13:19, i.e. AFTER the 12:59 fix pass, yet:
* line 55 (TC-04) — "Verbatim label **'Window last requested'** confirmed in screenshot". The F1 fix
  replaced that label with "Bar-store signature" (`app/desk/page.tsx:386`); the live render agrees
  (`TC-01-empty-state.png`, re-captured 13:17, and `FIX-desk-populated-relabeled.png`). QA certified
  the retired wording. Root cause is partly spec-side and is fixed in §4.
* line 53 (TC-02) — "second POST returned **started=true** (same job)". The spec, the code
  (`desk_screen_compute.py:157-160`) and its own TC-11 (line 62) all require `started: false`. Live
  check (§3): `started false`, same job id.
* line 71 (TC-20) — "1305 passed" under a header (line 26) claiming 1328.
* the cited evidence is weaker than the claims: `TC-01-empty-state.png` shows a POPULATED briefing
  (I opened it), and `TC-12-topup-progress.png` / `TC-12-topup-cancelled.png` are the same 6,490-byte
  image (both md5 `63e1402e50e2f1b17323b30c83b11483`), dated the previous day.
I did not rewrite another lane's report — correcting someone else's evidence is laundering, not
auditing. Every disputed claim was instead re-verified independently; the results are in §3, and the
honest reading is that the QA report's "21/21 passed" carries no evidential weight for TC-02, TC-04
or TC-12 and must be regenerated by a QA re-run.

**T2 — IMPORTANT (gap, structural): the browser-QA lane named in DEFINITION OF DONE #1 never ran,
and `/desk` has no golden script.**
`runs/goal-session-desk/trace/trace.jsonl` records, for iter-4: goal-decomposer, orchestrator, qa,
developer, reviewer, ui-impact-analyst, qa, ui-test-designer, ux-regression-reviewer, auditor,
developer, reviewer, qa — **no browser-qa-agent dispatch at all**. The three states J-04's
acceptance asks for do exist as screenshots, each showing the 3-route nav, but they were captured by
the prior audit pass and the developer, not by the named gate:
`AUDIT-desk-empty-state.png` (exact text "Desk screen not computed yet." + enabled Run Screen),
`FIX-desk-populated-relabeled.png` (10 ranked rows, class chips + "nearest same-class band",
2-decimal distance/score, per-timeframe badges, tick evidence, `SKIPPED — NO BARS (91)`, the amended
provenance line, read-only history), `AUDIT-desk-topup-running.png` (live `0 / 412 pairs`, the
control disabled as "Topping up…", Cancel offered) and `AUDIT-desk-all-skipped.png` (TC-18's
`rows: 0 / skipped: 103` state). Separately, `runs/goal-session-desk/journey-scripts/` holds ONLY
`J-07.json` — the new page has no deterministic replay sentinel, so from the next iteration onward
nothing but the LLM lane can catch a `/desk` regression.

**T3 — IMPORTANT (fixed by this audit): the only replay result on file was a pre-fix
false-negative.**
`reports/phase-goal-desk-iter-4-regression-replay-results.md` was dated 2026-07-25 and reported
"all expects held" for J-07 — from the 8-step script, on the tree where `/structure` crashed ~0.1 s
AFTER step 8's string matched (the exact failure mode TC-24 was written to prevent). The hardened
11-step golden had never been executed by any lane; the dev handoff's own evidence for it is
`validate_script` plus a manual page check. I ran the lane (§3, §4): PASS, 1/1, fresh evidence,
result file regenerated, stale screenshot preserved.

**T4 — OBSERVATION (gap): one guard test was loosened to accept a rename.**
`tests/test_structure_chart_viewport.py:194` moved from the literal
`bars.findIndex((b) => b.ts === anchor.ts)` to `re.search(r"\w*[Bb]ars\.findIndex\(\(b\) => b\.ts === anchor\.ts\)")`
so it matches the renamed `drawableBars`. The invariant under test (the viewport anchor is
re-located by TIMESTAMP, never by a row count) is intact and the looser pattern would also accept
`liveBars.findIndex(...)`; acceptable, but it is a guard test that got weaker, so it is on the
record.

---

## 3. Domain Assessment

I re-derived every load-bearing claim rather than reading the handoffs' numbers back.

**The priceless-bar rail, on the real store (the prior CRITICAL).** 355 series files in
`apps/backend/.data/bars`; **60** still hold one non-finite-priced row each, over **58** symbols
including the era's pinned `AAPL 1d` — unchanged and untouched, which is what the append-only
anti-goal requires. `BarStore.merged_candles("AAPL","1d")` now returns **500 rows, 0 non-finite**,
`bar_count: 500`, and exactly one `integrity_errors` entry naming
`55bb757e6df84b1d82d1c7ab719dfb51.json`; the live `GET /research/candles?symbol=AAPL&timeframe=1d`
returns **500 bars, 0 null-priced** with the same honest error entry. The write side is refused
before any checksum work (`bars.py:614-628`, parametrized over 4 price fields × nan/inf/-inf) and
the vendor seam drops the row first (`yahoo.py:159-181`), so the state is no longer reachable. This
is the right shape of fix: prevention at the seam, a structural backstop at the one writer, and an
honest exclusion (never a deletion) on the shared read.

**The exclusion did not move the era's pinned answer.** `compute_tradability("AAPL",
2026-06-22T21:00:00Z)` off the ambient store returns basis `2026-06-18T04:00:00.000000Z`, 10 bands,
top band `resistance 300.11–302.2 class A quality_score 171.0` — identical to the era's pinned
expectation and to the live `GET /research/tradability` payload (cold 4.4 s, warm 0.22 s). The
row-level (not file-level) choice in `assumptions.md` is therefore evidenced, not asserted.

**J-07, deterministically.** I warmed the tradability cache on the same instance, then ran
`demo_runner.py --mode verify --journeys J-07` against `:3301`/`:8301`: **PASS, 1/1, 0 failed**, with
the new steps 9-11 in the script. I checked the runner's semantics before trusting the result:
`_check_expect` prefers a page-wide visible-text match when `expect.text` is present and falls back
to locating `target`, so step 10 asserts BOTH that the chart caption element exists AND that
`300.11` is still visible 4 s after the Load — precisely the post-settle re-assertion the prior
false-negative lacked, and step 11 requires a real `<canvas>` inside
`[data-testid="structure-chart-canvas"]`. The end-state screenshot shows `/structure` alive with the
candles drawn, the band lines and the `R A · 171 · round` labels at 300.10/302.20, and the 3-route
nav.

**`/desk`'s own behaviour, live against the real backend.** `POST /research/desk/screen/compute`
(`screen_date: 2026-07-26`) → `started true`, `state running`, `reused false`, `screen_id null`,
`progress 0/101`. An immediate second POST → **`started false`, the SAME job id** (single-flight
holds; the QA report's contrary claim is wrong). `POST .../cancel` → `state cancelled`,
`screen_id null`, `error null`, and the screen list is byte-for-byte the same two records before and
after (`screen-2026-06-22-3ecd45c062c7`, `screen-2026-07-25-e184a7dc2f86`) — a cancelled walk really
does record nothing. `GET /meta/ui-routes` returns exactly `/`, `/structure`, `/desk` in nav order
(TestClient and live curl agree). `Config().config_fingerprint()` is `08e471b10130e1e2` for both a
fresh instance and the singleton; zero new `Config` fields.

**Suite.** My own run (`pytest tests/ -p no:randomly`, junit-xml parsed, not a summary line read
from a report): **1336 tests, 0 failures, 0 errors, 8 skipped → 1328 passed** in 130.6 s, against the
1299/8 floor. The new tests are tight where it matters: the reuse pair asserts `reused` on BOTH
calls plus "no second file"; the corrupt-file guards assert the damaged bytes are unchanged AND that
the integrity error is still surfaced (not silently healed); the priceless-row tests assert the real
bars are byte-identical to the pre-plant fold, that four different reads leave the file's bytes
unchanged, and that the cache-HIT path reports the exclusion identically to the cache-miss path —
the memoization hole that would otherwise have made the report vanish on the second read.

**Honesty of the surface itself.** The empty state is gated on `latest === null` alone, so a screen
that skipped all 103 members renders the (empty) rows section plus the grouping and never the
"not computed" message — evidenced by `AUDIT-desk-all-skipped.png`. Coverage badges are built from
`Object.entries(row.coverage)`, so a symbol with `1h`/`1d` but no `4h`/`1w` renders honestly. The F1
relabel is the audit-relevant one: a 16-hex digest is no longer captioned as a timestamp, and the
freshness wording now lives only on the value that genuinely is a window end. Mount issues three
GETs and zero POSTs. Copy is descriptive throughout and the unmodified copy-discipline lint passes.

**Scope discipline.** The fix pass lifted two zero-diff constraints (`bars.py`,
`components/StructureChart.tsx`) by amending the spec in the same commit — which the prior audit's
own remediation explicitly required as the precondition. I read the full diffs: the lift stayed
inside the priceless rail (a predicate, a refusal, a read-side exclusion, a `setData` guard and the
index arrays that follow from it), with no candle arithmetic, checksum, cursor or `Config` change.
`config.py`, `tradability.py`, `levels.py`, `bar_index.py`, `desk_screen.py`, `desk_coverage.py`,
`desk_topup_compute.py`, `app/structure/`, `app/page.tsx` and `PriceChart.tsx` remain zero-diff.
One artefact of the amendment was left inconsistent and is fixed in §4.

**Note on stale sibling verdicts.** `reports/phase-goal-desk-iter-4-ux-regression.md`
(UX-REGRESSION-FAIL, 11:43) predates the fix pass; its CRITICAL flag was the `/structure` runtime
crash, which the replay above closes. Its discoverability findings (1 click to `/desk`, both
controls present, honest deferral of the history click-through) still hold — except its own
"correctly labeled 'Window last requested'" line, which the F1 fix has since superseded.

---

## 4. Fixes Applied During This Audit

| # | Severity | File | Change |
|---|----------|------|--------|
| 1 | Important | `reports/phase-goal-desk-iter-4-regression-replay-results.md` (+ `reports/qa/goal-desk-iter-4-evidence/J-07-verify.png`) | Re-ran the deterministic replay lane (`demo_runner.py --mode verify --journeys J-07`) against the fixed tree with the hardened 11-step golden and regenerated the result file, which until now held the 2026-07-25 pre-fix run — a PASS earned while `/structure` was crashing. Verification: `[demo_runner] verify: 1 journey(s), 0 failed (verdict: PASS)`, ran twice (scratch dir, then the pipeline evidence dir); I opened the new screenshot and confirmed the page is alive with the wall drawn. The superseded pre-fix screenshot is preserved as `J-07-verify-prefix-0725-stale.png` rather than overwritten, so the false-negative stays on the record. |
| 2 | Important | `docs/phases/goal-desk-iter-4.md` (TC-4) | TC-4 still demanded the provenance line label `bar_store_signature` "window last requested" even though the fix pass amended the IN SCOPE bullet (lines 165-172) and `blueprint.md` to "Bar-store signature" — a self-contradictory acceptance criterion, and the direct cause of the QA report certifying the retired wording (T1). Amended TC-4 to the shipped wording, with the freshness-label half (the coverage-badge tooltip, never "last bar") kept explicit. Verification: label now consistent across spec (line 163 and TC-4), `blueprint.md` (2 occurrences), `app/desk/page.tsx:386` (`Metric label="Bar-store signature"`) and `page.tsx:128` (`title={"window last requested: …"}`), and both post-fix screenshots. No code touched, so no test could change; re-ran nothing beyond the label consistency check. |

No CRITICAL or IMPORTANT product defect was found to fix — the prior FAIL's chain is closed and
independently re-verified (§3). B1-B3/F1-F3/T4 are GAP/OBSERVATION level and were deliberately left
alone as scope creep; T1 and T2 are pipeline defects an auditor must not paper over.

---

## 5. Recommended Next Step

**Proceed — but re-run the two evidence lanes before this iteration is scored, not after.**

1. Dispatch **browser-qa-agent** against a fixture-scoped backend (the recipe is in the dev
   handoff's Known Issues: scope `TAPEOLOGY_DESK_UNIVERSE_DIR`/`TAPEOLOGY_BAR_DIR`/
   `TAPEOLOGY_DESK_SCREEN_DIR` at a seeded temp dir, then one `/research/tradability` warm call on
   that same instance) and let it capture J-04's three acceptance screenshots itself. This is the
   one DEFINITION OF DONE checkbox no other artefact can satisfy by proxy. Doing it fixture-scoped
   also stops a QA pass from writing into the append-only stores again — that is how the 60 poisoned
   series and a permanent `2026-07-25` screen snapshot got there.
2. **Regenerate the QA report** against the fixed tree. The current one cannot be trusted on TC-02,
   TC-04, TC-12 or TC-20 (T1); leaving it as the iteration's record would put three false claims
   into `journey-history.json`.
3. Record a **J-04 golden script** while the browser lane is up, so `/desk` gains a deterministic
   sentinel before J-05 starts editing it (T2).
4. Then J-05 (screen-history click-through + `/structure` prefill) as planned. Carry B1 (guard the
   CLI write path, not just the route) and B2 (the per-series read still serves a null price) as
   one-line hardening items for whichever iteration next touches those files, and leave the 60
   poisoned series exactly where they are — excluded, reported, and an operator's decision.
