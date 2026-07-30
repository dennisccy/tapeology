# Iteration 27 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** evidence

## Summary

This run changed no program code at all, and I checked that myself: the difference against the
run's own starting point is empty under `apps/`, `scripts/` and `config/`, with no new files there,
and the program tree is byte-identical to the tree that was saved at the end of the last run. The
run had three jobs. Two of them landed and I proved both by opening the files rather than reading
about them: the page bundle was rebuilt so the everyday page at port 3301 talks to the running
program again, after which all sixteen saved test scripts replayed green with no script edits; and
the new top-up disclosure was photographed afresh on a throwaway copy of the data, in one picture
that shows the four counts, the tail-versus-full-window line and four failed rows each naming the
window it asked for. The third job failed. The short guided film was recorded against the everyday
page instead of the throwaway copy where the populated run actually lived, so all five of its
frames are literally one and the same picture of the top of the Desk page, and none of the words
the film is supposed to show appear anywhere in it. I am not calling the goal finished on that.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 Universe ingestion — fetched, registered, honest | passing | passing | `reports/phase-goal-desk-iter-27-ui-test-results.md` row UT-J-01 PASS (golden replay, zero script edits) + `reports/qa/goal-desk-iter-27-evidence/J-01-verify.png` |
| J-02 Coverage + explicit bar top-up over the universe | passing | passing | same file, row UT-J-02 PASS + `.../J-02-verify.png` |
| J-03 The screen — pinned inputs, append-only snapshot, deterministic rank | passing | passing | same file, row UT-J-03 PASS + `.../J-03-verify.png` |
| J-04 The /desk briefing page | passing | passing | same file, row UT-J-04 PASS + `.../J-04-verify.png` |
| J-05 Ledger history + drill-in to /structure | passing | passing | same file, row UT-J-05 PASS + `.../J-05-verify.png` — **spot-check: I opened this image** and read the `/structure` Load form pre-filled with SYMBOL `AAPL` and AS-OF `2026-06-22T23:59:59Z`, which is the drill-in prefill this journey exists for |
| J-06 MCP contract v3 — 17 read-only tools | passing | passing | same file, row UT-J-06 PASS + `.../J-06-verify.png`; **I also re-counted the tools myself** in the running module: `len(app.mcp.TOOL_NAMES) == 17`, names enumerated |
| J-07 The kept product stands — regression sentinel | passing | passing | same file, row UT-J-07 PASS + `.../J-07-verify.png` — **spot-check: I opened this image** and read a fully rendered `/structure` Tradable Map with the pinned AAPL wall drawn at 300.10/302.20 labelled `R A · 171 · round`, matching `docs/goal.md`'s own pinned example |
| J-08 Every ranked briefing row names the bar its distance was measured from | passing | passing | same file, row UT-J-08 PASS + `.../J-08-verify.png` |
| J-09 Every top-up run leaves an append-only record of what it attempted | passing | passing | same file, row UT-J-09 PASS + `.../J-09-verify.png` |
| J-10 The coverage the briefing shows is the coverage the frozen store can prove | passing | passing | same file, row UT-J-10 PASS + `.../J-10-verify.png` |
| J-11 Every ranked briefing row states how much completed history its wall was measured over | passing | passing | same file, row UT-J-11 PASS + `.../J-11-verify.png` |
| J-12 Every recorded screen the ledger lists can be read back | passing | passing | same file, row UT-J-12 PASS + `.../J-12-verify.png` |
| J-13 Every ranked briefing row states the price its wall sits at and the close it was measured from | passing | passing | same file, row UT-J-13 PASS + `.../J-13-verify.png` |
| J-14 Every ranked briefing row states where the nearest wall on the OTHER side of price sits | passing | passing | same file, row UT-J-14 PASS + `.../J-14-verify.png` |
| J-15 Every ranked briefing row states what its wall is actually made of | passing | passing | same file, row UT-J-15 PASS + `.../J-15-verify.png` |
| J-16 The briefing fits the page it is read on | passing | passing | same file, row UT-J-16 PASS + `.../J-16-verify.png` |
| J-17 A top-up asks the vendor only for the bars the frozen store cannot already prove | passing (`evidence_makeup`) | passing (`evidence_makeup` STAYS set — film still owed) | same file, row UT-J-17 PASS + `reports/qa/goal-desk-iter-27-evidence/J-17-topup-window-disclosure.png` — **I opened this image**: one 1440×900 frame, no sideways scroll, showing `0 reused · 6 fetched · 2 unchanged · 4 failed`, then `2 pairs asked for a tail window · 10 pairs asked for the full lookback window`, then `Failed pairs (4)` with four ZZZINVALIDXYZ rows each carrying `requested 2024-07-30 → 2026-07-30`, with the J-16 ranked table unchanged at 13 columns in the same frame |

Honest note on the replay pictures (carried, unchanged since iteration 22b — a defect in the
replay tool, not in the product): the sixteen `J-*-verify.png` files collapse to **three distinct
images** by checksum, because the replay tool re-saves the first view of whatever page it lands on.
The load-bearing proof for those sixteen is the replay assertions themselves, every one of which
held; the two I spot-checked (J-05, J-07) are among the distinct images and both matched their
recorded status.

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| Secrets / credentials committed | OK | `iter-27/scan-report.md` CLEAN; and the product diff against snapshot `a9fd2e7` is empty under `apps/`, `scripts/`, `config/` with zero untracked files there — there are no added lines to carry a secret |
| Paid / external SaaS dependency | OK | zero diff means zero manifest change. The only outside call this run made was the existing keyless Yahoo bar seam, on a throwaway data copy, which this era already sanctions |
| License changes | OK | `scan-report.md` CLEAN; no `LICENSE` or license-field file appears in the (empty) diff |
| Fabricated or substituted data | OK | the throwaway rig made **genuine** vendor calls (the failing rows are a deliberately invalid ticker, so the vendor really did return nothing); every number I read on screen I matched to the record the run wrote. The new `J-17.json` replay script asserts the everyday store's own real legacy numbers and is openly labelled a partial proxy in the QA report |
| No execution path, ever *(critical)* | OK | zero code diff; `test_no_execution_path.py` unmodified |
| No profit claims and no advice *(critical)* | OK | zero copy diff; `test_copy_discipline.py` re-run by me, green unmodified. I also read the film's spoken words: descriptive only this time ("the system records exactly what window it asked for"), with none of the judgement language iteration 25 disclosed |
| Frozen foundations *(critical)* | OK | product tree byte-identical to iteration 26's commit `f6968e0`; `Config().config_fingerprint()` re-run by me prints `08e471b10130e1e2` |
| No lookahead *(critical)* | OK | zero diff to any as-of path |
| Single source of truth *(critical)* | OK | zero diff; `iter-27/coherence.md` reads COHERENCE-PASS |
| Deterministic and seeded | OK | zero diff |
| Read-only MCP *(critical)* | OK | I re-counted in the running code: exactly 17 tools, all GET proxies |
| Immutable data *(critical)* | OK | I proved this rather than accepting it: `find apps/backend/.data -newermt '2026-07-31 00:00'` returns ONLY `bar_index.db-wal` and `bar_index.db-shm` (rebuildable sidecars), and the counts still read 759 bar series / 1 universe / 11 screens / 1 top-up run |
| Persistence stays scoped *(critical)* | OK | the populated run for the picture was written to a throwaway copy under the run's own temp root, never the operator's store (proved by the file listing above) |
| Membership is never a signal *(critical)* | OK | zero diff |
| Snapshots are append-only and pinned *(critical)* | OK | same file listing; nothing of the operator's was created, changed or removed |
| Every run is an explicit operator act *(critical)* | OK | zero diff; the top-up and screen runs on the throwaway rig were explicit POST calls; no scheduler, cron or auto-refresh exists |
| The briefing describes, never advises *(critical)* | OK | copy lint green unmodified (I re-ran it) |
| No new statistics, gates, or strategies *(critical)* | OK | zero diff |
| The demolition stays demolished *(critical)* | OK | zero diff; no manual-input path added |
| The ledger never holds orders *(critical)* | OK | zero diff |
| The suite stays keyless and hermetic *(critical)* | OK | no test changed; the vendor calls happened in an operator-style verification run, reported as such, never inside the test suite |
| The fingerprint pin does not move *(critical)* | OK | re-run by me: `08e471b10130e1e2`; zero new config fields |
| The enhancement loop stays inside its box *(critical)* | **OPEN — the one unmet item** | `docs/goal.md` is unchanged this run (I checked the diff) and no proposer ran. But this rail requires an added journey to **include a `[NEW]`-flagged walkthrough**, and J-17's own acceptance repeats it. A film exists but shows none of the journey — see below. I record this as an unmet condition, not as a violation by act |
| Host-guard caps are law *(critical)* | OK | nothing observed that disables, widens or bypasses the caps |

### The one unmet item, stated plainly

A film was recorded (`reports/demo/goal-desk-iter-27/`, verdict `RECORDED_WITH_NOTES`), and I
proved it is empty rather than reading about it:

- All five frames share one checksum, `dd3486a6bede477c9d9bb5475aa5bd27`, which is also
  byte-identical to eight of this same run's replay pictures. So no frame is a new capture at all
  (the iteration's own TC-6 fails).
- I opened `reports/demo/goal-desk-iter-27/step-02.png` and found the **everyday** Desk page at its
  top scroll position (snapshot `screen-2026-07-30-bad6387963ef`, universe `2026-07-25`, rows
  BRK-B / AMZN / MDLZ / MSFT). The Top-up Runs section is not in frame at all (TC-5 fails).
- Root cause, exactly: `reports/phase-goal-desk-iter-27-demo.json` carries
  `"base_url": "http://localhost:3301"` — the everyday pair — while the populated run the film
  needs existed only on the throwaway rig at `:3391`/`:8391`, which the picture-taking step tore
  down at 00:28, one minute before the film step ran at 00:29. All four of the film's J-17 checks
  therefore missed, and each is disclosed as a soft note in
  `reports/phase-goal-desk-iter-27-demo-results.md`.

## Next-Step Recommendation

One more short capture-only run, no code change, with exactly one job: record J-17's guided film
so its own frames actually show the top-up disclosure. The fix is small and now precisely known —
the film must be pointed at the throwaway copy where the populated run lives, not at the everyday
page. Concretely, the run's plan must say two things: keep the throwaway rig alive until the film
step has finished (this run killed it one minute too early), and set the film's `base_url` to that
rig's own address rather than `http://localhost:3301`. The frames must show the four counts line,
the tail-versus-full-window line and at least one failed row's own requested window, and each step
must name one row rather than all of them; do not script a click inside a briefing row, because an
invisible full-row link makes that impossible by design.

I am bounding this deliberately: **this is the last capture run I will ask for on this film.** If
the next attempt still cannot put that content in frame, the right call is to stop retrying, hand
the film to you as an optional piece of showcase polish, and propose the finish on the evidence
that already exists — because the product itself is done and proven. You can also make that call
now if you prefer: nothing about the Desk's behaviour is unproven, and the only thing missing is a
demonstration video. One sentence for you: everything the Desk was asked to do works and is
photographed, but the short film meant to walk through the newest piece was aimed at the wrong copy
of the page and shows nothing — one more brief run should fix that, and if it does not, we should
close anyway.

Two further things for your own track, neither blocking and both carried from earlier runs: the
replay tool keeps saving the same first view, so sixteen replay pictures are only three distinct
images; and the backend test suite reads two files out of the run bookkeeping folder
(`runs/goal-session-desk/journey-scripts/`), so archiving that folder would break the suite.

## Halt Justification (if halting)

Not halting.
