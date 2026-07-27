# Iteration 9 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** lean

## Summary

The new "basis" column on the Desk page is built, and it is honest. Every ranked row of a new
screen now names the exact daily price bar its distance was measured from and how many days old
that bar is; rows saved before this change say plainly "basis not recorded in this snapshot"
instead of guessing. I checked the numbers myself against the one place that owns them and they
match exactly. One thing is missing: the goal text asks for a single picture showing a row that is
**2 days old or fresher** next to a row that is **10 days old or older**. The picture that was
taken shows 3 days next to 14 days. That is not a fault in the software — the newest price data on
the machine is three days old — and the same picture can be taken correctly today with no code
change at all. So the work continues for one short run to take that picture properly.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 Universe ingestion — fetched, registered, honest | passing | passing | Row UT-J-01 (golden replay PASS) + `reports/qa/goal-desk-iter-9-evidence/J-01-verify.png`; evaluator re-listed `apps/backend/.data/universe` — one snapshot file, mtime 2026-07-25, untouched |
| J-02 Coverage + explicit bar top-up over the universe | passing | passing | Row UT-J-02 + `J-02-verify.png`; coverage/tick-evidence badges legible in `UT-03-fresh-vs-stale.png` and `UT-05-legacy-fallback.png` (opened by the evaluator) |
| J-03 The screen — pinned inputs, append-only snapshot, deterministic rank | passing | passing | Row UT-J-03 + `J-03-verify.png`; evaluator's own sha256 + mtime check on all three files in `apps/backend/.data/screen/` |
| J-04 The /desk briefing page | passing | passing | Row UT-J-04 (9-expect golden) + `J-04-verify.png`; UT-08 confirms the seven pre-existing ranked columns + 4-column skip table unchanged; `UT-02-screen-history-table-order.png` opened by the evaluator |
| J-05 Ledger history + drill-in to /structure | passing | passing | Row UT-J-05 + `J-05-verify.png` (opened: /structure prefilled AAPL @ 2026-06-22T23:59:59Z, pinned wall drawn); UT-06 "Latest" round-trip; UT-07 hit-test at the new cell resolves to the drill-in anchor |
| J-06 MCP contract v3 — 17 read-only tools | passing | passing | Row UT-J-06 (34 MCP tests live, 0 failed); evaluator's own check: `EXPECTED_TOOLS` length is exactly 17 and includes `desk_universe`/`desk_screen`; `app/mcp/__init__.py` zero diff |
| J-07 The kept product stands — regression sentinel | passing | passing | Row UT-J-07 + `J-07-verify.png` (opened); evaluator's own suite 1346 passed / 8 skipped / 0 failed, pin `08e471b10130e1e2`, zero diff on every frozen file vs both the iteration snapshot and era-open `047c38e` |
| J-08 Every ranked briefing row names the bar its distance was measured from | (new this iteration) | **partial** | `UT-03-fresh-vs-stale.png` (opened — AAPL 3 d, NFLX/META/NVDA 14 d), `UT-05-legacy-fallback.png` (opened — 10/10 legacy rows read "basis not recorded in this snapshot"), `J-08-verify.png`, plus the evaluator's own read of `screen-2026-07-27-936543601e75.json` (63/63 rows carry both fields) and its own `compute_tradability()` cross-check on six symbols. One acceptance clause unmet — see below. |

### Why J-08 is `partial`, clause by clause

Met, each re-checked by me and not taken from any report:

- **New rows carry both fields.** I read `apps/backend/.data/screen/screen-2026-07-27-936543601e75.json`
  off disk: 63 of 63 ranked rows carry `basis_as_of` and `basis_age_days`; age spread exactly
  `{3, 4, 6, 14}`.
- **Single source of truth.** I called the canonical owner `compute_tradability()` myself against a
  throw-away copy of the bar store at `as_of 2026-07-27T23:59:59Z`: BRK-B `2026-07-23T04:00:00.000000Z`/4 d,
  AAPL `2026-07-24…`/3 d, NFLX `2026-07-13…`/14 d, MSFT `2026-07-21…`/6 d, META `2026-07-13…`/14 d,
  NVDA `2026-07-13…`/14 d — byte-identical to the persisted rows, and every `basis_age_days` is the exact
  calendar-date difference. The desk copies; it never re-derives.
- **Nothing old was rewritten.** Both pre-existing snapshots still hash to `530bb4f6b4a5a3fc…` and
  `9c2fddf6c4821a89…` with mtime 2026-07-25 (before this iteration started at 20:21), and 0 of 10 rows in
  each carries either new key — absent, not `null`, not backfilled.
- **Honest legacy state on screen.** `UT-05-legacy-fallback.png`: all ten rows of the 2026-07-25 screen read
  exactly "basis not recorded in this snapshot", with the "not the latest" banner and Latest button.
- **`[NEW]`-flagged walkthrough exists** — `reports/phase-goal-desk-iter-9-demo-script.md` steps 01/02/03.
- **Suite / pin / frozen files** — my own junit run: 1354 tests, 1346 passed, 8 skipped, 0 failures, 0 errors,
  exit 0 (floor 1341/8); `Config().config_fingerprint()` = `08e471b10130e1e2`; zero diff on `config.py`
  (so zero new Config field), `tradability.py`, `levels.py`, `bars.py`, `StructureChart.tsx`; the
  copy-discipline lint is byte-unmodified vs era open and green.

Unmet — one clause, verbatim from `docs/goal.md`: *"in a real browser after the T-9 clean rebuild, `/desk`
shows the `basis` column with at least one fresh row (age ≤ 2 d) and one stale row (age ≥ 10 d) legible in
the same screenshot"*. `UT-03-fresh-vs-stale.png` legibly shows **3 d** (AAPL) and **14 d**
(NFLX/META/NVDA). The `≥ 10 d` half is met; the `≤ 2 d` half is not. The test plan
(`reports/phase-goal-desk-iter-9-ui-test-plan.md:112-115`) wrote itself an allowance for exactly this case
and the browser-QA lane applied and disclosed it — but a test plan cannot amend the goal file's own
acceptance text, and the allowance was not needed: I measured the canonical owner at
`as_of 2026-07-25T23:59:59Z` on the same throw-away copy and got **AAPL = 1 d** and
**NFLX/META/NVDA = 12 d**, so both thresholds are reachable today with no code change and no write to the
real data folder.

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| Secrets / credentials | OK | `iter-9/scan-report.md` CLEAN on added lines (tracked + 1 untracked file); the product diff is 5 files, none of them config/env |
| Paid or external SaaS dependency | OK | No manifest in the diff — `package.json`, `requirements*.txt`, `pyproject.toml` all untouched; scan-report reports no dependency findings |
| License changes | OK | No LICENSE or license-field file in the diff; scan-report CLEAN |
| Fabricated / substituted data | OK | `basis_as_of` is copied verbatim from the canonical owner — I cross-checked 6 symbols myself; legacy rows show absence honestly (0/10 keys on disk, "basis not recorded in this snapshot" on screen) rather than a read-time computation |
| 1. No execution path, ever | OK | Diff adds a date-subtraction helper, two dict keys, one table cell; `test_no_execution_path.py` byte-unmodified vs era open and green in my own suite run |
| 2. No profit claims and no advice | OK | New copy is `basis <date> · N d before as-of` and `basis not recorded in this snapshot`; copy-discipline lint green unmodified; UT-09 confirmed a 3 d row and a 14 d row render with identical style — no staleness highlight |
| 3. Frozen foundations | OK | My own zero-diff check vs the iteration snapshot on `tradability.py`, `levels.py`, `bars.py`, `StructureChart.tsx`, `PriceChart.tsx`, `app/engine/`, `desk_routes.py`, `mcp/__init__.py`, `meta.py`, `config.py`; and vs era-open `047c38e` on the engine plus every frozen research module |
| 4. Hold-out-only promotion | OK | No strategy, profile, gate, champion, or PnL-ledger code in the diff |
| 5. No lookahead | OK | `basis_age_days` is a pure function of two already-persisted strings; `_resolve_basis` only returns a session closed at or before `as_of` — all six of my probes returned `basis_as_of <= as_of` |
| 6. Single source of truth | OK | `coherence.md` = COHERENCE-PASS; plus my own 6-symbol byte-identity cross-check against `compute_tradability` |
| 7. Deterministic and seeded | OK | No wall clock in the derivation; the same-pins re-run test proves byte-identical rows and no second file |
| 8. Read-only MCP | OK | `app/mcp/__init__.py` zero diff; 17 tools confirmed by my own `EXPECTED_TOOLS` read; `desk_screen` is still a bare GET proxy |
| 9. Immutable data | OK | No bar or dataset written; both pre-existing screen snapshots byte-identical by sha256 and mtime |
| 10. Persistence stays scoped | OK (with a noted deviation) | The browser-QA lane clicked "Run Screen" against the **real** `apps/backend/.data/` instead of the throw-away copy the spec's NOTES directed (audit T3). Not a rail breach — an explicit button click, not a scheduler/daemon/auto-refresh/page-load GET, and it appended a new correctly-pinned file rather than rewriting anything. Carried as hygiene, not scored as a violation |
| Membership is never a signal | OK | Rank rule untouched; the two new fields are descriptive row content, and UT-08 confirms the seven pre-existing ranked columns are unchanged |
| Snapshots are append-only and pinned | OK | The 5-pin key is unchanged; only new snapshots' row content grew; legacy files provably untouched |
| Every run is an explicit operator act | OK | No scheduler added; coherence confirms no new fetch call was added to the page; the one new screen came from a button click |
| The briefing describes, never advises | OK | See anti-goal 2 |
| No new statistics, gates, or strategies | OK | None in the diff |
| The demolition stays demolished | OK | No journal-era machinery; no manual-input write path added to desk records |
| The ledger never holds orders | OK | No size, ticket, entry/exit, or account concept added |
| The suite stays keyless and hermetic | OK | New tests are fixture-scoped; the developer deliberately kept the real-file check out of pytest and documented why; my own suite run needed no network |
| The fingerprint pin does not move | OK | `08e471b10130e1e2` printed live by me; `config.py` zero diff means zero new Config fields |
| The enhancement loop stays inside its box | OK | `docs/goal.md` diff vs HEAD is 50 added lines and **0 removed lines**, all inside the `AUTO:journeys` block; the journey carries a single-source-of-truth acceptance criterion and a `[NEW]` walkthrough; zero goal.md diff vs the iteration snapshot, so no lane touched it during the run |

**Coherence:** `runs/goal-session-desk/iter-9/coherence.md` = **COHERENCE-PASS** — no structural veto.

**Pipeline health:** review PASS, QA PASS, audit PASS_WITH_GAPS, closure CLOSURE-PASS,
ux-regression UX-REGRESSION-PASS. No fail-open signal (no failing review with browser results
past it).

## Next-Step Recommendation

Run one more short pass (**lean**). It needs no change to the program at all — it is a
photography and tidy-up run:

1. **Take the missing picture properly.** Copy the real data folder to a throw-away place with the
   existing script `apps/backend/scripts/goal-desk-iter9-scoped-backend.sh`, run one screen there
   for the date **2026-07-25** (never against the real folder), then photograph the Desk page. I
   measured this myself: Apple will read **1 day**, and Netflix, Meta and Nvidia will read
   **12 days** — both numbers the goal asks for, in one image. Clear the page build first
   (`rm -rf apps/frontend/.next`) as the rules require.
2. **Say plainly in the picture report which data folder was used.** This run photographed the real
   one, which is against its own written plan.
3. **Do not let a test plan lower a bar the goal file sets.** The plan for this run gave itself
   permission to miss the "2 days or fresher" number. Future plans must ask the owner instead.
4. **Two small tidy-ups, only if they cost nothing:** the developer's note pointing at the replay
   evidence file for the new script points at a file that was later overwritten — fix the pointer;
   and the new script's steps 3 and 6 assume the newest saved screen has the new column, so a note
   should say so.
5. **Do not rebuild anything already proven.** Everything else in this run — the column itself, the
   honest "not recorded" text, the untouched old records, the tests, the walkthrough — is verified
   done and must not be redone.

One sentence for the owner: the new "measured from" column on the Desk page works and is honest;
the next short run only needs to take one picture that shows a one-day-old row beside a twelve-day-old
row, which today's data can already produce.

## Halt Justification (if halting)

Not halting. Nothing that used to work stopped working, no rail was broken, and the one remaining
gap is a picture the automation can take by itself — it needs no decision or action from a person.
