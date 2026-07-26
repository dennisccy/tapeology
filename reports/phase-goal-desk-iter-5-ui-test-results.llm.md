# Phase goal-desk-iter-5 — UI Test Results

**Phase:** goal-desk-iter-5
**Date:** 2026-07-26
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

**Overall:** 4/4 tested journeys passed (0 skipped). J-07 was explicitly excluded from this run per
dispatch instructions ("a deterministic replay verifies them separately") — not executed, not
scored here.

---

## Fixture-scoped data basis (cited by every claim below)

- **Backend:** fresh fixture-scoped FastAPI instance, port 8301, root
  `/var/tmp/iad.goal-desk-iter-5.822370/desk-iter5-browser-qa-run` (never used for any prior
  verification run — confirmed empty screen history at start). Launched via
  `apps/backend/scripts/qa_desk_iter5_fixture_scoped_backend.sh` (the developer's iter-5 script),
  which exports `TAPEOLOGY_DESK_UNIVERSE_DIR`, `TAPEOLOGY_BAR_DIR`, `TAPEOLOGY_DESK_SCREEN_DIR`,
  `TAPEOLOGY_DATASET_DIR`, `TAPEOLOGY_BAR_INDEX_DB`, `TAPEOLOGY_DATASET_INDEX_DB`,
  `TAPEOLOGY_JOURNAL_DB` all under that root — never the ambient `apps/backend/.data/`.
- **Universe fixture:** verbatim copy of
  `apps/backend/tests/fixtures/universe/universe-2026-07-25-817cc184bbb3.json` — id
  `universe-2026-07-25-817cc184bbb3`, checksum `817cc184bbb3`, 103 members (within the 90–110
  bound), Yahoo-normalized symbols (e.g. `BRK-B`) confirmed present.
- **Bar fixtures:** verbatim copies of the two committed
  `apps/backend/tests/fixtures/bars/{009371c9c02f46338bafef47148f92ad,b08b1a55ef4a45b2a1adad8fa82ccdf1}.json`
  files — both for symbol **PG** (1h + 1d), `bar_index.db` rebuilt from them via `BarIndex.reindex()`
  (log: "bar_index seeded: 2 series, 0 errors"). PG is therefore the ONLY universe member with any
  bar coverage on this fixture set.
- **Frontend:** `apps/frontend/.next` removed and rebuilt (T-9), started on port 3301 with
  `NEXT_PUBLIC_API_URL=http://localhost:8301` pointed at the fixture-scoped backend above.
- **Warm-up:** `curl --max-time 30 http://localhost:8301/research/desk/coverage` issued before any
  browser navigation (avoids the iter-0 cold-first-call trap) — 200 OK.
- Before opening the browser, `GET /research/desk/screen` on this fresh root returned
  `{"screens":[],"latest":null,"integrity_errors":[]}` — confirmed honest-empty baseline.
- The **ambient dev backend/frontend** that were already running on 8301/3301 at dispatch time
  (an unscoped instance holding real accumulated screens, universe snapshot
  `universe-2026-07-25-49b33fa31680`) were stopped BEFORE this pass and restarted AFTER it, so the
  fixture-scoped and ambient stores never overlapped. The restarted ambient instance was confirmed
  to still serve the SAME pre-existing universe id (`...-49b33fa31680`, distinct from the fixture's
  `...-817cc184bbb3`), proving the two never mixed.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | Universe ingestion — fetched, registered, honest | happy-path (keyless acceptance, browser-executed) | P1 | Fixture snapshot registered and served with checksum + member count in 90–110 and normalized symbols | `GET /research/desk/universe` via browser: 1 snapshot, id `universe-2026-07-25-817cc184bbb3`, checksum `817cc184bbb3`, `member_count: 103`, includes normalized `BRK-B` | PASS | `reports/qa/goal-desk-iter-5-evidence/UT-J-01-universe-endpoint.png` |
| UT-J-02 | Coverage + explicit bar top-up over the universe | happy-path (keyless acceptance, browser-executed) | P1 | Coverage reports bars-present only for the fixture's stocked member(s), bars-missing for every other member, read from `bar_index` (index-fast, no store re-hash) | `GET /research/desk/coverage` via browser: PG shows `has_bars:true` for `1h`/`1d`; every other of the 103 members shows `has_bars:false` on all 4 timeframes; response returned promptly after warm-up | PASS | `reports/qa/goal-desk-iter-5-evidence/UT-J-02-coverage-endpoint.png` |
| UT-J-03 | The screen — pinned inputs, append-only snapshot, deterministic rank | happy-path (keyless acceptance, browser-executed) | P1 | Screen run produces the expected ranked + skipped rows; re-run with identical pins is byte-identical (no rewrite); rows' band values match `GET /research/tradability` byte-for-byte | Screen `screen-2026-07-26-f8c65c9ac382`: 1 ranked row (PG, side `support`, class `C`, distance `322.10 bps`, score `35.0`, price band `141.115–141.82`) + 102 `skipped: no_bars` rows; re-triggering the same `screen_date` returned `reused:true` with the SAME `screen_id` and screen count stayed at 1 (no duplicate); PG's band values (`class C`, `price_low 141.115`, `price_high 141.82`, `quality_score 35.0`) matched a live `GET /research/tradability?symbol=PG&as_of=2026-07-26T23:59:59Z` call exactly, byte-for-byte | PASS | `reports/qa/goal-desk-iter-5-evidence/UT-J-03-screen-endpoint.png` |
| UT-J-04 | The `/desk` briefing page (TC-1..TC-5) | happy-path / validation (browser-verified) | P1 | Empty state before any run; Run Screen shows a disabled "Computing…" state with member progress; a second click during compute is refused (no second POST); populated briefing renders chips/provenance/skip grouping after the run; nav lists exactly 3 routes | All five sub-conditions verified live in-browser — see breakdown below | PASS | `UT-J-04-01-empty-state.png`, `UT-J-04-02-run-screen-computing.png`, `UT-J-04-03-second-click-refused.png`, `UT-J-04-04-populated-briefing.png` |

---

## Passed Tests

### UT-J-01 — Universe ingestion — fetched, registered, honest
**Verdict:** PASS
**Evidence:** `reports/qa/goal-desk-iter-5-evidence/UT-J-01-universe-endpoint.png`

- Navigated the browser directly to `http://localhost:8301/research/desk/universe` (fixture-scoped
  backend). Response: one snapshot, `id: universe-2026-07-25-817cc184bbb3`, `checksum: 817cc184bbb3`,
  `member_count: 103` (within the 90–110 bound), `source_url` recorded, `raw_members`/`members`
  present with Yahoo-normalized dashes (`BRK-B` observed in the member list read via curl against
  the same instance immediately before the browser check).
- The pre-registration honest-empty state was independently confirmed on the SAME fresh root before
  the universe directory was ever populated by anything other than the committed fixture copy (see
  "Fixture-scoped data basis" above) — this iteration made no live Wikipedia fetch and no corrupted-
  fixture attempt (out of scope; that path is covered by the backend unit suite, not this browser
  pass).
- This journey's acceptance is fundamentally a keyless/automated backend contract (goal.md marks it
  "(Keyless; automated.)"); the browser-executed portion above is the observable subset a UI check
  can add on top of the suite.

### UT-J-02 — Coverage + explicit bar top-up over the universe
**Verdict:** PASS
**Evidence:** `reports/qa/goal-desk-iter-5-evidence/UT-J-02-coverage-endpoint.png`

- Navigated the browser to `http://localhost:8301/research/desk/coverage`. Response covers all 103
  registered members; PG alone shows `has_bars:true` for `1h` (latest window end
  `2026-06-09T21:00:00Z`) and `1d` (latest window end `2026-06-06T00:00:00Z`), `has_bars:false` for
  `4h`/`1w`; every other of the 103 members shows `has_bars:false` on all four timeframes — exactly
  matching the truth-table implied by the fixture (only PG has any registered bars on this root).
- The GET returned promptly (the warm-up call plus this browser call both completed without any
  visible delay), consistent with T-4 (coverage reads `bar_index`, never re-hashes the store).
- Top-up (POST + CLI operator-run act against ~100 live symbols) is explicitly an operator-run,
  not-CI-gated act per goal.md and was not exercised this pass (correctly out of scope for a keyless
  browser check); the `/desk` page's Top-up button presence/enabled state was visually confirmed in
  the empty-state screenshot (`UT-J-04-01-empty-state.png`) as part of UT-J-04.

### UT-J-03 — The screen — pinned inputs, append-only snapshot, deterministic rank
**Verdict:** PASS
**Evidence:** `reports/qa/goal-desk-iter-5-evidence/UT-J-03-screen-endpoint.png`

- Triggered a real screen compute (via the `/desk` "Run Screen" button, see UT-J-04) for
  `screen_date: 2026-07-26`. Result, read back through the browser at
  `http://localhost:8301/research/desk/screen`: one screen snapshot
  `screen-2026-07-26-f8c65c9ac382` with `universe_snapshot_id: universe-2026-07-25-817cc184bbb3`,
  `config_fingerprint: 08e471b10130e1e2`, `bar_store_signature: 715be94f7ab637c9`; `rows` contains
  exactly one entry (PG, `side: support`, `band_class: C`, `distance_bps: 322.0963559437696`,
  `band_score: 35.0`, `price_low: 141.115`, `price_high: 141.82`, coverage `1h`/`1d` true); `skipped`
  contains all other 102 members each with `reason: no_bars`.
- **Determinism / append-only check:** re-triggered the compute for the SAME `screen_date` via
  `POST /research/desk/screen/compute`. The response reported `reused: true` with the SAME
  `screen_id` (`screen-2026-07-26-f8c65c9ac382`); `GET /research/desk/screen` afterward still listed
  exactly ONE screen (no duplicate snapshot was written) — confirming same-pins re-runs reproduce
  byte-identical content rather than rewriting.
- **Single-source-of-truth check:** called `GET /research/tradability?symbol=PG&as_of=2026-07-26T23:59:59Z`
  directly. Its band list contains a `support`/`class C` entry with `price_low: 141.115`,
  `price_high: 141.82`, `quality_score: 35.0` — matching the screen row's band values byte-for-byte
  (the screen's `band_score` field equals `tradability`'s `quality_score` field for the same band).
  This confirms the desk reads the canonical `compute_tradability` owner verbatim rather than
  recomputing.
- `config_fingerprint` in the screen snapshot is `08e471b10130e1e2` — the era pin, unmoved.

### UT-J-04 — The `/desk` briefing page
**Verdict:** PASS
**Evidence:** `UT-J-04-01-empty-state.png`, `UT-J-04-02-run-screen-computing.png`,
`UT-J-04-03-second-click-refused.png`, `UT-J-04-04-populated-briefing.png`

**TC-1 (empty state):** Navigated to `http://localhost:3301/desk` on the fresh fixture-scoped root
(zero prior screens). DOM confirmed: `[data-testid="app-nav"]` links exactly
`["Cockpit","Structure","Desk"]`; `[data-testid="desk-title"]` = "Desk";
`[data-testid="desk-screen-not-computed"]` text = exactly "Desk screen not computed yet." with "No
screen has been recorded yet for the registered universe." beneath it; both
`[data-testid="desk-run-screen-button"]` ("Run Screen") and `[data-testid="desk-topup-button"]`
("Top-up") enabled (`disabled: false`). Screenshot: `UT-J-04-01-empty-state.png`.

**TC-2 (Run Screen running, disabled):** Clicked the Run Screen button. Live DOM read immediately
after the click confirmed the transition: button text → "Computing…", `disabled: true`,
`[data-testid="desk-screen-compute-running"]` text = "0 / 103 members\n\nCancel". This state is
driven by the compute-manager's poll cadence (the button stays "Computing…" until the NEXT
700ms poll tick corrects it), not by backend compute time — the underlying backend job itself
finished in single-digit milliseconds every time it was measured directly via
`GET /research/desk/screen/compute` (`started_utc`/`finished_utc` ~7ms apart), consistent with the
developer handoff's finding for this tiny fixture set. To reliably capture this fast, genuinely-real
but sub-second UI state in a static screenshot, one poll `fetch()` call inside the PAGE'S OWN JS
context was held open for several seconds via a client-side timing shim before resolving (a QA
capture aid only — it delays when the browser's own next poll response arrives, it does not fake,
skip, or alter any request/response body, and it triggers no additional network call). While frozen
in this state, the browser screenshot was taken: `UT-J-04-02-run-screen-computing.png` shows
"Computing…" (disabled) and "0 / 103 members" + "Cancel" clearly rendered.

**TC-3 (second click refused, single-flight):** `window.fetch` was instrumented (in the same page
context, no server-side change) to count POST calls to `/research/desk/screen/compute` for the
entire click sequence. Result: exactly **one** POST call was recorded for the whole run, even after
TWO additional `.click()` invocations were fired at the disabled button while it was showing
"Computing…". The button remained disabled/"Computing…" after both extra clicks (no reset, no
second cycle), and `document.body` was confirmed still present (post-match liveness) after each
check. Screenshot `UT-J-04-03-second-click-refused.png` shows the still-disabled/"Computing…" state
unchanged after the refused second click.

**TC-4 (populated briefing):** After the compute resolved and the page was freshly reloaded (clean
state, no injected styling), `http://localhost:3301/desk` rendered: `[data-testid="desk-provenance"]`
with all five labeled rows (Universe snapshot `universe-2026-07-25-817cc184bbb3`; Screen date
`2026-07-26`; As of `2026-07-26T23:59:59Z`; Config fingerprint `08e471b10130e1e2`; Bar-store
signature `715be94f7ab637c9`); `[data-testid="desk-screen-rows-table"]` with one row (PG, support,
"Class C" chip with "nearest same-class band" caption, "322.10 bps", score "35.00", four coverage
badges); `[data-testid="desk-skipped-section"]` heading "SKIPPED — NO BARS (102)" with the full
grouped list. Screenshot: `UT-J-04-04-populated-briefing.png`.

**TC-5 (route contract):** `GET /meta/ui-routes` (called both via curl and by navigating the browser
directly to it) returned exactly three entries: `/` (Cockpit), `/structure` (Structure), `/desk`
(Desk) — matching the nav bar observed in every screenshot above.

**TC-7 (ambient store untouched):** `apps/backend/.data/` was listed (path|mtime|size, 391 entries)
immediately before the fixture-scoped backend was launched and again immediately after the entire
pass (including this journey's compute runs) completed and the fixture-scoped processes were torn
down. `diff` between the two listings was **empty** — zero new or modified files anywhere under the
ambient store.

**Golden replay:** `runs/goal-session-desk/journey-scripts/J-04.json` recorded (schema_version 1,
9 steps: goto `/desk` → nav/title/static-copy identity checks → click Run Screen → `wait_for` 2000ms
→ provenance-panel text check → nav liveness recheck → title liveness recheck). Deliberately does
NOT assert the empty state or the transient running text (both are environment-state-dependent for
a future ambient-backend replay, per lesson (a) — a golden must assert stable, non-timing-dependent
content). Linted clean:
`python3 scripts/automation/lib/demo_runner.py --mode lint --scripts-dir runs/goal-session-desk/journey-scripts --journeys J-04` → `J-04 ok`.

---

## Failed Tests

None.

---

## Skipped Tests

None. (J-07 was out of scope for this dispatch by explicit instruction — a deterministic replay
verifies it separately — and is therefore not listed as a test row here, passed, failed, or
skipped.)

---

## Environment

- **Frontend URL:** http://localhost:3301 (fixture-scoped backend on :8301 during the pass; both
  torn down and the prior ambient instance restarted afterward — see "Fixture-scoped data basis")
- **Browser:** Chrome via `mcp__plugin_superpowers-chrome_chrome__use_browser`
- **Test Date:** 2026-07-26
- **Evidence directory:** `reports/qa/goal-desk-iter-5-evidence/`
- **Clean rebuild (T-9):** `apps/frontend/.next` removed and rebuilt before this pass.
- **Ambient-store integrity:** confirmed byte-identical before/after listing of
  `apps/backend/.data/` (391 entries, empty diff) — no new or modified files from this pass.
