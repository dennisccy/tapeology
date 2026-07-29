# Iteration 20 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** evidence

## Summary

This run changed no program code at all. Its whole job was to take two pictures that earlier runs
owed. One of the two was taken and is good: the Desk page, showing the earlier of the two recordings
made on 2026-07-27, now has a full-length picture where the sentence "3 ranked row(s) below show
every timeframe badge dark" and the NFLX row with all four of its time-frame marks unlit sit in the
same image. The other one failed: the guided walkthrough film over a full Desk page was never
recorded, because the film's own instruction file was written with a broken line and the film step
gave up and wrote "SKIPPED", leaving its picture folder empty. Every one of the fourteen journeys
still works and nothing was written into the owner's own data folder this time. Because the film the
goal file asks for twice is still missing, and because one more picture can only be settled by the
owner, I am not calling the goal finished.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 Universe ingestion | passing | passing (carried, code unchanged) | reports/qa/goal-desk-iter-18-evidence/J-01-verify.png (spot-checked by me) |
| J-02 Coverage + top-up | passing | passing (carried, code unchanged) | reports/qa/goal-desk-iter-18-evidence/J-02-verify.png (spot-checked by me) |
| J-03 The screen | passing | passing (carried, code unchanged) | reports/qa/goal-desk-iter-19-evidence/J-03-verify.png |
| J-04 The /desk briefing page | passing | passing (re-verified by replay) | reports/phase-goal-desk-iter-20-ui-test-results.md row UT-J-04 + reports/qa/goal-desk-iter-20-evidence/J-04-verify.png |
| J-05 Ledger history + drill-in | passing | passing (re-verified by replay) | row UT-J-05 + reports/qa/goal-desk-iter-20-evidence/J-05-verify.png (opened: /structure prefilled AAPL, as-of 2026-06-22T23:59:59Z) |
| J-06 MCP contract v3 | passing | passing (re-counted by me: 17 tools) | apps/backend/tests/test_mcp_server.py + my own `len(app.mcp.TOOLS) == 17` |
| J-07 Regression sentinel | passing | passing (re-verified by replay) | row UT-J-07 + reports/qa/goal-desk-iter-20-evidence/J-07-verify.png; my own fingerprint check `08e471b10130e1e2`; `git diff e9a2aaec..HEAD -- apps/` empty |
| J-08 Basis bar named | passing | passing (carried, code unchanged) | reports/qa/goal-desk-iter-19-evidence/J-08-verify.png |
| J-09 Top-up run record | passing | passing (carried, code unchanged) | reports/qa/goal-desk-iter-18-evidence/J-09-verify.png |
| J-10 Coverage provable | passing | passing (carried, code unchanged) | reports/qa/goal-desk-iter-18-evidence/J-10-verify.png |
| J-11 History length | passing | passing (carried, code unchanged) | reports/qa/goal-desk-iter-19-evidence/J-11-verify.png |
| J-12 Snapshots addressable by id | passing (picture owed) | passing — picture debt CLOSED | row UT-J-12 + reports/qa/goal-desk-iter-20-evidence/UT-J-12-result.png (full page 1785x11044, opened by me) |
| J-13 Wall price + close | passing (film owed) | passing (film still owed) | row UT-J-13 + reports/qa/goal-desk-iter-20-evidence/UT-J-13-result.png (opened by me) |
| J-14 Opposite wall | passing (film + hint picture owed) | passing (film + hint picture still owed) | row UT-J-14 + reports/qa/goal-desk-iter-20-evidence/UT-J-14-result.png (opened by me; same image as UT-J-13) |

No journey changed status. Two evidence flags moved: `evidence_makeup` is CLEARED on J-12 (its
full-length picture landed) and stays set on J-13 and J-14 (the walkthrough film is still missing;
for J-14 the hover-hint photograph is also still missing and cannot be taken in this rig).

### What I opened and re-derived myself (not taken from any report)

- `UT-J-12-result.png`: one frame carries the provenance panel (Snapshot id
  `screen-2026-07-27-936543601e75`, Recorded at `2026-07-27T21:42:14.636275Z`, screen date
  2026-07-27, bar-store signature `7eab5f03cf23e8c7`, fingerprint `08e471b10130e1e2`), the
  "Viewing the recorded screen for 2026-07-27 — not the latest." banner, the sentence "3 ranked
  row(s) below show every timeframe badge dark", and the NFLX row with all four marks (1h/4h/1d/1w)
  unlit next to BRK-B/DHR/IBM rows whose marks are lit.
- From disk, not from the page: in `screen-2026-07-27-936543601e75.json` NFLX coverage is
  `{1h:false, 4h:false, 1d:false, 1w:false}` and exactly 3 of 63 rows are all-dark — the same count
  the page prints; in `screen-2026-07-27-3ad3c57aa6ba.json` NFLX is
  `{1h:true, 4h:false, 1d:true, 1w:false}` and 0 of 63 are all-dark. I then opened the later
  recording's own older frame (`reports/qa/goal-desk-iter-16-evidence/UT-03-result.png`) and read
  NFLX's `1h` and `1d` marks LIT there. So the goal file's own named example — NFLX's `1d` mark dark
  in one recording and lit in the other — is now readable across the pair.
- `UT-J-13-result.png` / `UT-J-14-result.png` (one image): a row reading
  `band 488.50–490.91 · close 490.91` (close inside its own range) and, lower in the SAME image,
  `band 508.79–512.31 · close 508.77` (close below its range); and `opposite … · 1.22 bps`,
  `· 1.38 bps`, `· 2.40 bps` in the same frame as `· 1128.29 bps`, `· 2696.60 bps` and
  `· 10788.88 bps`. Two honest caveats about this one image: because the table had to be scrolled
  sideways to bring the two right-hand columns into view, the symbol names and the provenance block
  are pushed out of the frame, so the picture alone does not say WHICH rows or WHICH recording these
  are — I closed that gap myself by matching five rows' values against the recording on disk (below),
  and iteration 19's own picture `J-14-opposite-near-far.png` does carry the provenance block.
- I re-read those numbers straight out of `apps/backend/.data/screen/screen-2026-07-20-ca185294a384.json`:
  BRK-B `price_low 488.5`, `price_high 490.9100036621094`, `reference_close 490.9100036621094`,
  opposite `resistance A 490.9700012207031–494.3949890136719 · 1.22 bps`; LMT `508.789…–512.3115…`,
  close `508.7699890136719`. All five sampled rows match the picture exactly. All 100 ranked rows
  carry `reference_close`, `opposite_band` and `bands_by_class`; 16 closes sit inside their band and
  84 outside; 7 opposite walls are within 25 bps and 48 beyond 1,000 bps.
- The film that failed: `reports/phase-goal-desk-iter-20-demo-results.md` reads
  `Demo Verdict: SKIPPED` with the soft note "demo JSON parse error". I opened
  `reports/phase-goal-desk-iter-20-demo.json`: lines 28, 64 and 76 contain JavaScript regular
  expressions (`/screen.history/i`, `/scroll.*band/i`, `/scroll.*opposite/i`) where a plain quoted
  string is required, so the whole file is unreadable and all 8 steps were dropped.
  `reports/demo/goal-desk-iter-20/` is empty. Its 8 steps were aimed correctly (three at J-13, one
  at J-14), so the plan was right and only the file was malformed. Two of those steps also model the
  sideways reveal of the `band`/`opposite` columns as a click on a button named "scroll…", which no
  such button is — that needs fixing too, not just the quoting.
- Sentinel checks I ran: `Config().config_fingerprint()` prints `08e471b10130e1e2`; the tool list in
  the running code has exactly 17 entries including `desk_screen` and `desk_universe`;
  `git diff e9a2aaec..HEAD -- apps/` is empty and the working tree touches no file under `apps/`, so
  the full test suite result verified at iteration 19 still holds (methodology A.6).
- Stable spot-checks (J-01, J-02, both outside this run's required list): their pictures open as a
  real Desk page with provenance and ranked rows, and nothing contradicts their recorded state.
  Caveat recorded honestly: the iteration-18 replay frames for J-01..J-04 and J-08..J-13 are one and
  the same 115,208-byte image, so they prove the replay ran, not what each individual step saw.

## Anti-goal Check

Basis: `runs/goal-session-desk/iter-20/scan-report.md` (CLEAN), `iter-diff.md` ("no changes"), my own
`git diff e9a2aaec..HEAD` (nothing under `apps/`), and my own `find apps/backend/.data -newermt
"2026-07-29 23:03"`, which returns only the directory's own timestamp — zero files created, modified
or removed in the owner's store.

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| Secrets / credentials | OK | scan-report CLEAN; there are no added lines anywhere — the product diff is empty |
| Paid / external SaaS | OK | no manifest touched (`package.json`, `requirements*.txt`, `pyproject.toml` all unchanged); no dependency added |
| License changes | OK | no LICENSE or license-field change in the (empty) diff |
| Fabricated / substituted data | OK | every rendered number I checked came from the recorded snapshots on disk and matched byte-for-byte; no fixture is presented as live data |
| No execution path, ever | OK | no code change; nothing added under `apps/` |
| No profit claims / no advice | OK | page copy unchanged; the captures read as measurements (bands, closes, bps distances) |
| Frozen foundations | OK | zero diff to `engine/`, `config.py`, `tradability.py`, `levels.py`, `bars.py`, `bar_index.py`, both charts; fingerprint `08e471b10130e1e2` re-printed by me |
| Hold-out-only promotion | OK | no strategy, gate, or champion touched (empty diff) |
| No lookahead | OK | nothing computed this iteration; recordings were read, not recomputed |
| Single source of truth | OK | `coherence.md` = COHERENCE-PASS; the page's values matched their one owner's recorded rows exactly |
| Deterministic and seeded | OK | no new code path; the same recording re-read twice served the same values |
| Read-only MCP | OK | tool list unchanged at 17, all GET proxies (my own count) |
| Immutable data | OK | zero new/modified/removed files under `apps/backend/.data`; all 10 screen records, the universe record, the run ledgers and every bar series predate this iteration |
| Persistence stays scoped | OK, with a disclosed plan deviation | the browser lane again served from the owner's real store instead of the throwaway copy its own spec (TC-1) demanded — but this time it only READ: I verified zero footprint. Not scored as a goal-file violation; recorded as a process deviation, the 5th run in a row the scoped-copy instruction was ignored |
| Membership is never a signal | OK | no code change |
| Snapshots append-only and pinned | OK | nothing written; nothing backfilled; every record still carries its own pins |
| Every run is an explicit operator act | OK | the lane only clicked history rows (plain reads); no new top-up record, no new screen, and the derived caches' timestamps are older than the iteration, so no page load triggered a compute |
| The briefing describes, never advises | OK | copy unchanged; copy-discipline test untouched |
| No new statistics, gates, or strategies | OK | empty diff |
| The demolition stays demolished | OK | empty diff |
| The ledger never holds orders | OK | empty diff |
| Suite stays keyless and hermetic | OK | no test changed; no network test added; the suite was not re-run this iteration, which is sound because the product code is byte-identical to the iteration-19 state where it ran green |
| Fingerprint pin does not move | OK | I printed it myself: `08e471b10130e1e2`; zero new Config fields |
| Enhancement loop stays inside its box | OK | `docs/goal.md` unchanged this iteration (no drift note, and all 14 journey hashes recompute identical) |
| Host-guard caps are law | OK | no cap file touched; the run stayed inside the engine's confinement |

No new violation. The three older items in `journey-history.json` all remain resolved.

## Next-Step Recommendation

One more short capture-only run, and one decision that only the owner can make.

1. For the chain (no program change): record the guided walkthrough film over a full Desk page — the
   populated recording `screen-2026-07-20-ca185294a384` — covering the wall price and close (J-13
   "the wall's price range and the close it was measured from") and the opposite wall (J-14 "where
   the nearest wall on the other side sits"). Two things must be fixed first, both in the film's own
   instruction file: write the click targets as ordinary quoted text instead of the
   slash-delimited pattern that made the file unreadable, and express the sideways reveal of the
   `band`/`opposite` columns as a sideways scroll of the table, not as a click on a button that does
   not exist. Check the file parses before the film runs, and treat "SKIPPED" as a failure of that
   step rather than a note. Take it on a throwaway copy of the data folder, and prove the serving
   program is really pointed at the copy — five runs in a row have quietly used the owner's own
   folder instead.
2. For the owner (this is the item that will otherwise block the finish forever): the goal file asks
   for a photograph of the small hint that appears when the mouse rests on a briefing row. This
   set-up cannot photograph that kind of hint at all — the browser paints it outside the picture it
   saves — and three runs have now tried. The independent second check refused to confirm the finish
   because of exactly that line. Please choose one: (a) change that line to ask for the hint's text
   to be read out of the live page, which is already proven correct, or (b) ask for the hint to be
   shown as an ordinary panel on the page, which a picture can capture — that is a small program
   change nobody has asked for yet. Nothing else is waiting on you.

Also still open by choice, none of them defects: the Desk page is now eight stacked sections and
long, the run tables have no length limit, and the history rows cannot be reached by keyboard.

One sentence for the owner: everything on the Desk works and was checked number-by-number against
your stored files again, but one film still has to be recorded and one line of the goal file needs
your decision before the finish can be confirmed.

## Halt Justification (if halting)

Not halting. All fourteen journeys are passing and there is real, machine-doable work left (record
the film), so this is a CONTINUE at `evidence` depth rather than a stall. I did not return
GOAL_ACHIEVED because the walkthrough film that the goal file requires for both J-13 and J-14 does
not exist — this run tried and produced an empty folder — and because iteration 19's independent
second check already refused the finish for that same missing film plus the hint photograph
(`runs/goal-session-desk/iter-19/eval-confirm.md`). Declaring success now would repeat that refusal
instead of closing it.
