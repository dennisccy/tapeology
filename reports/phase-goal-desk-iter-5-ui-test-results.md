# UI Test Results (merged)

**Date:** 2026-07-26
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** PASS

**Overall:** 5/5 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-07 | The kept product stands — regression sentinel | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-5-evidence/J-07-verify.png |
| UT-J-01 | Universe ingestion — fetched, registered, honest | happy-path (keyless acceptance, browser-executed) | P1 | Fixture snapshot registered and served with checksum + member count in 90–110 and normalized symbols | `GET /research/desk/universe` via browser: 1 snapshot, id `universe-2026-07-25-817cc184bbb3`, checksum `817cc184bbb3`, `member_count: 103`, includes normalized `BRK-B` | PASS | `reports/qa/goal-desk-iter-5-evidence/UT-J-01-universe-endpoint.png` |
| UT-J-02 | Coverage + explicit bar top-up over the universe | happy-path (keyless acceptance, browser-executed) | P1 | Coverage reports bars-present only for the fixture's stocked member(s), bars-missing for every other member, read from `bar_index` (index-fast, no store re-hash) | `GET /research/desk/coverage` via browser: PG shows `has_bars:true` for `1h`/`1d`; every other of the 103 members shows `has_bars:false` on all 4 timeframes; response returned promptly after warm-up | PASS | `reports/qa/goal-desk-iter-5-evidence/UT-J-02-coverage-endpoint.png` |
| UT-J-03 | The screen — pinned inputs, append-only snapshot, deterministic rank | happy-path (keyless acceptance, browser-executed) | P1 | Screen run produces the expected ranked + skipped rows; re-run with identical pins is byte-identical (no rewrite); rows' band values match `GET /research/tradability` byte-for-byte | Screen `screen-2026-07-26-f8c65c9ac382`: 1 ranked row (PG, side `support`, class `C`, distance `322.10 bps`, score `35.0`, price band `141.115–141.82`) + 102 `skipped: no_bars` rows; re-triggering the same `screen_date` returned `reused:true` with the SAME `screen_id` and screen count stayed at 1 (no duplicate); PG's band values (`class C`, `price_low 141.115`, `price_high 141.82`, `quality_score 35.0`) matched a live `GET /research/tradability?symbol=PG&as_of=2026-07-26T23:59:59Z` call exactly, byte-for-byte | PASS | `reports/qa/goal-desk-iter-5-evidence/UT-J-03-screen-endpoint.png` |
| UT-J-04 | The `/desk` briefing page (TC-1..TC-5) | happy-path / validation (browser-verified) | P1 | Empty state before any run; Run Screen shows a disabled "Computing…" state with member progress; a second click during compute is refused (no second POST); populated briefing renders chips/provenance/skip grouping after the run; nav lists exactly 3 routes | All five sub-conditions verified live in-browser — see breakdown below | PASS | `UT-J-04-01-empty-state.png`, `UT-J-04-02-run-screen-computing.png`, `UT-J-04-03-second-click-refused.png`, `UT-J-04-04-populated-briefing.png` |

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-07-26

