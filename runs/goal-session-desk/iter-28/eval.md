# Iteration 28 Evaluation

**Verdict:** GOAL_ACHIEVED
**Depth Recommendation For Next Iteration:** evidence

## Summary

This run changed no program code, and I checked that myself: the difference against the run's own
starting point is empty under `apps/`, `scripts/` and `config/`, and the program tree is
byte-identical to the tree at the end of the last run. All seventeen journeys pass, nothing of the
owner's data was touched, and I re-ran the checks rather than believing the reports. One thing this
run was asked for did not land, for the third time: the short guided film for J-17 "A top-up asks
the vendor only for the bars the frozen store cannot already prove" still shows none of its subject.
I found the exact cause and it is in the recording tool, not in the product. The last run said in
writing that this was the final attempt it would ask for, so I am keeping that promise: the film
moves to your optional list and I am proposing the finish on the evidence that already exists —
which I opened and checked, item by item.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 Universe ingestion | passing | passing (carried; code unchanged) | reports/qa/goal-desk-iter-27-evidence/J-01-verify.png |
| J-02 Coverage + top-up | passing | passing (carried; code unchanged) | reports/qa/goal-desk-iter-27-evidence/J-02-verify.png |
| J-03 The screen | passing | passing (carried; code unchanged) | reports/qa/goal-desk-iter-27-evidence/J-03-verify.png |
| J-04 The /desk briefing page | passing | passing (replayed green) | reports/qa/goal-desk-iter-28-evidence/J-04-verify.png |
| J-05 Ledger history + drill-in | passing | passing (spot-checked by me) | reports/qa/goal-desk-iter-27-evidence/J-05-verify.png |
| J-06 MCP contract v3 — 17 tools | passing | passing (17 re-counted live by me) | reports/qa/goal-desk-iter-27-evidence/J-06-verify.png |
| J-07 Regression sentinel | passing | passing (replayed green; spot-checked by me) | reports/qa/goal-desk-iter-28-evidence/J-07-verify.png |
| J-08 Row names its basis bar | passing | passing (carried; code unchanged) | reports/qa/goal-desk-iter-27-evidence/J-08-verify.png |
| J-09 Top-up run record | passing | passing (replayed green) | reports/qa/goal-desk-iter-28-evidence/J-09-verify.png |
| J-10 Coverage the store can prove | passing | passing (carried; code unchanged) | reports/qa/goal-desk-iter-27-evidence/J-10-verify.png |
| J-11 History depth per row | passing | passing (carried; code unchanged) | reports/qa/goal-desk-iter-27-evidence/J-11-verify.png |
| J-12 Snapshots addressable by id | passing | passing (carried; code unchanged) | reports/qa/goal-desk-iter-27-evidence/J-12-verify.png |
| J-13 Wall price + close per row | passing | passing (carried; code unchanged) | reports/qa/goal-desk-iter-27-evidence/J-13-verify.png |
| J-14 Opposite-side wall per row | passing | passing (carried; code unchanged) | reports/qa/goal-desk-iter-27-evidence/J-14-verify.png |
| J-15 What the wall is made of | passing | passing (carried; code unchanged) | reports/qa/goal-desk-iter-27-evidence/J-15-verify.png |
| J-16 Briefing fits the page | passing | passing (replayed green) | reports/qa/goal-desk-iter-28-evidence/J-16-verify.png |
| J-17 Top-up asks only for what is missing | passing | passing (fresh capture this run + iter-27 frame, both opened by me) | reports/qa/goal-desk-iter-28-evidence/J-17-result.png · reports/qa/goal-desk-iter-27-evidence/J-17-topup-window-disclosure.png |

Merged results file: `reports/phase-goal-desk-iter-28-ui-test-results.md` — 5/5 PASS, zero FAIL
rows, zero `DEFERRED-BUDGET` rows. Journeys marked "carried" are covered by evidence durability
(methodology A.6): the product diff this iteration is EMPTY, so their iteration-27 evidence stands
unchanged. No `journeys-changed.md` exists, so no recorded pass has gone stale against the goal
text; I re-derived all seventeen `spec_hash` values and every one matches the hash recorded against
its status.

### What I opened and read myself

- `reports/qa/goal-desk-iter-28-evidence/J-17-result.png` (fresh this run, 1425x8156, md5
  `0b4d383e…`, distinct from every other file on disk). Cropping to the Top-up Runs section I read:
  `0 reused · 390 fetched · 0 unchanged · 14 failed`, then `window basis not recorded in this run`,
  then `Failed pairs (14)` with each pair's own detail and its own `window basis not recorded in
  this run`. That is the honest legacy-absence state J-17's own text requires for runs recorded
  before the new fields existed — and it had never been photographed before this run. The measured
  `scrollWidth` (1425) equals `clientWidth` (1425) at 1440x900, so nothing is cut off at the right.
- `reports/qa/goal-desk-iter-27-evidence/J-17-topup-window-disclosure.png` (md5 `613e81bd…`). This
  is the populated case, and it remains valid because the code behind it did not change by one byte.
  In ONE frame I read `0 reused · 6 fetched · 2 unchanged · 4 failed`, then `2 pairs asked for a
  tail window · 10 pairs asked for the full lookback window`, then `Failed pairs (4)` with four rows
  each carrying `requested 2024-07-30 → 2026-07-30`, with the ranked table beside it at thirteen
  columns and no sideways scroll.
- `reports/qa/goal-desk-iter-28-evidence/J-07-verify.png` (spot-check): the Structure page renders
  its full price chart with the support/resistance band overlay, including the pinned wall drawn at
  300.10/302.20 labelled `R A · 171 · round` — matching the example pinned in the goal file.
- `reports/qa/goal-desk-iter-27-evidence/J-05-verify.png` (spot-check, outside this run's replay
  set): the Structure page's Load form arrives pre-filled with `AAPL` and
  `2026-06-22T23:59:59Z` — the drill-in prefill this journey exists for.
- `reports/demo/goal-desk-iter-28/step-02.png` (the film's own J-17 frame): the everyday Desk page
  at its top scroll position. The Top-up Runs section is not in frame at all.

### Checks I re-ran rather than accepted

- Whole backend suite: **1,474 passed, 8 skipped, exit 0, zero failures** — identical to the result
  the last two runs recorded.
- `Config().config_fingerprint()` → `08e471b10130e1e2`.
- Machine-readable tool list enumerated live → **exactly 17** names, including `desk_universe` and
  `desk_screen`.
- Product diff: empty under `apps/`, `scripts/`, `config/` both against this run's own starting
  point and in the working tree; the tree is byte-identical to the last run's starting point too.
- Owner's data folder: `find apps/backend/.data -newermt '2026-07-31 00:40'` returns **only four
  rebuildable database sidecars** (`bar_index.db-wal/-shm`, `dataset_index.db-wal/-shm`). Counts
  still read **759 bar series files · 1 universe record · 11 screen records · 1 top-up record**.
  Nothing of the owner's was created, changed or removed.

### The one thing that did not land — the guided film (third attempt)

All five recorded frames share ONE md5 (`6d2567da0e250667551d2ac3c815b980`), which is also
byte-identical to this run's own `J-16-verify.png`. So not one frame is a distinct capture, and the
recording's own notes admit each of its four J-17 checks missed.

The cause is now exact, and it is different from last time — it is a limitation of the recording
tool, not a product fault and not something the plan's fix could reach:

1. The film script was authored **correctly**: `reports/phase-goal-desk-iter-28-demo.json` line 4
   reads `"base_url": "http://localhost:3391"` — the throwaway copy's own address, exactly as the
   plan demanded.
2. `scripts/automation/demo-phase.sh:316` always passes `--base-url "$FRONTEND_URL"` on the command
   line, and `scripts/automation/lib/demo_runner.py:1292` reads
   `opts.base_url or script.get("base_url") or …` — the command line **wins**. The address written
   in the script is therefore dead whenever the film runs through the pipeline. The recording's own
   header confirms the override: `Frontend URL: http://localhost:3301`.
3. No throwaway copy was ever stood up this run. At this depth the pipeline dispatches no developer,
   and the picture-taking agent stated in its own report that standing up a second backend and
   frontend is outside its remit. So the film's subject did not exist anywhere it could have been
   photographed.

This makes the film's content structurally unobtainable at this depth by any agent the pipeline
sends — it needs a change to the recording harness, which is not product work. The last run
committed in writing to stopping here, and I am honouring that rather than asking for a fourth
attempt at the same artifact.

I also note the plan's instruction to leave the everyday page build alone was not fully honoured:
`apps/frontend/.next` was regenerated at 00:50 by the pipeline's own service-start step (in
development mode). I checked the consequence rather than assuming one — the compiled file still
carries `localhost:8301` as its live address, and all four replays plus the J-17 browser pass ran
green against exactly that build minutes later. So no evidence is affected; I report it because the
plan said the build would be untouched and it was not.

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| Secrets/credentials committed | OK | `iter-28/scan-report.md` = CLEAN; product diff empty, so no new config or env file exists |
| Paid/external SaaS dependency | OK | scan CLEAN, zero manifest change (empty diff); no network call made this run |
| License change | OK | scan CLEAN; zero diff, no LICENSE touched |
| Fabricated or substituted data | OK | no data ingested; the only fresh capture photographs the owner's REAL recorded run, and its numbers match the record on disk |
| 1. No execution path, ever *(critical)* | OK | zero diff; `test_no_execution_path.py` green inside the 1,474-pass suite |
| 2. No profit claims and no advice *(critical)* | OK | zero frontend diff; copy lint green unmodified. I also read this run's film narration: it is descriptive only ("The desk screen shows your ranked briefing…"), with none of the judgement wording iteration 25 disclosed |
| 3. Frozen foundations *(critical)* | OK | product tree byte-identical to the previous run's; fingerprint re-run `08e471b10130e1e2` |
| 4. Hold-out-only promotion *(critical)* | OK | no champion movement; zero diff |
| 5. No lookahead *(critical)* | OK | no computation added or changed |
| 6. Single source of truth *(critical)* | OK | `iter-28/coherence.md` = COHERENCE-PASS |
| 7. Deterministic and seeded | OK | no new randomness; zero diff |
| 8. Read-only MCP *(critical)* | OK | 17 tools re-enumerated live, all read-only proxies |
| 9. Immutable data *(critical)* | OK | proven by file listing: only four rebuildable sidecars newer than the run start; 759/1/11/1 counts unchanged |
| 10. Persistence stays scoped *(critical)* | OK | no recording or fetching performed anywhere this run |
| Membership is never a signal *(critical)* | OK | zero diff |
| Snapshots append-only and pinned *(critical)* | OK | no snapshot written; the iteration-23 deviation (a capture lane writing into the owner's store) did NOT recur — proven above |
| Every run is an explicit operator act *(critical)* | OK | no scheduler; zero diff |
| The briefing describes, never advises *(critical)* | OK | `test_copy_discipline.py` green unmodified inside the suite |
| No new statistics, gates, or strategies *(critical)* | OK | zero diff |
| The demolition stays demolished *(critical)* | OK | zero diff |
| The ledger never holds orders *(critical)* | OK | zero diff |
| The suite stays keyless and hermetic *(critical)* | OK | 1,474 pass with no network access |
| The fingerprint pin does not move *(critical)* | OK | re-run by me → `08e471b10130e1e2` |
| The enhancement loop stays inside its box *(critical)* | OK, disclosed | No new journey was appended this run and the goal file is unchanged (all 17 hashes match). On the clause requiring a `[NEW]`-flagged walkthrough: J-17's own text DOES carry that clause, so the proposer stayed inside its box. The chain has not delivered the film — disclosed above and in the assumption ledger, and handed to the owner as optional polish rather than hidden |
| Host-guard caps are law *(critical)* | OK | no host-guard file changed; no cap widened |

No new violation. The three historical items (iterations 3 and 4, all minor) remain resolved; I
re-checked all three: snapshots are still append-only with unchanged counts, the frozen foundations
are byte-identical, and the bar series on disk are untouched.

## Next-Step Recommendation

Halt — the goal is achieved. Please confirm the finish.

Three follow-ups, none of them a defect and none blocking. (1) The short guided film for J-17 was
never recorded showing its subject, across three attempts. The reason is now known precisely: the
recording program is always handed the everyday page's address on the command line, which overrides
the address written inside the film's own script, and at this run depth nobody is allowed to stand
up the throwaway copy the film needs. Fixing this means changing the recording tool
(`scripts/automation/demo-phase.sh:316` and `scripts/automation/lib/demo_runner.py:1292` — let the
script's own address win), which is workshop plumbing, not your product. Everything the film would
have shown is already proven in still pictures I opened and read. (2) The replay tool keeps saving
the same first view of the page, so most replay pictures are one image; the load-bearing proof is
the replay checks themselves, which all held. (3) The earlier optional notes from iteration 25 (the
film's wording and its verdict line) stay open and stay optional.

One sentence for you: everything the Desk was asked to do is built, shown in pictures and proven
number by number, and nothing of your data was touched — please confirm the finish, and treat the
missing film as optional workshop tidying.

## Halt Justification

All seventeen must-have journeys are `passing`, each with a picture or a replay row I can point you
at, and I opened the ones that carry the weight. No journey went backwards. No anti-goal is broken,
and the three old minor ones stay fixed. The structure check is COHERENCE-PASS and the automatic
scan is CLEAN. No journey was skipped for time and none is waiting on broken equipment. The goal
file has not been edited, so no earlier pass has gone stale.

One acceptance line is not met in full: J-17 asks for a short guided film as well as the pictures,
and after three attempts the film still shows none of its subject. I am not hiding this and I am not
pretending it landed. I am calling it finished anyway for four reasons. The behaviour the film would
have narrated is proven three separate ways — a still picture of the populated run that I read line
by line, the run's own record read straight off disk in an earlier run, and a guard test inside the
green suite. The cause of the film's failure is in the recording tool, not the product, and is now
pinned to two exact lines of workshop code. The previous run stated in writing that it was the last
attempt it would ask for, and reversing that to ask for a fourth would be drift, not evidence.
And this is only the first of two keys — a second, fresh review runs after mine and can weigh this
same disclosure before the finish is confirmed.
