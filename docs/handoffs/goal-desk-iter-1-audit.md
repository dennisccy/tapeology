# goal-desk-iter-1 Audit Report

**Date:** 2026-07-25
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

J-01's universe subsystem is genuinely built, not stubbed: I independently re-ran the full suite
(**1210 passed / 8 skipped / 0 failed**), re-ran the live Wikipedia integration test for real
(**1 passed in 0.21s**), read the actual snapshot the production route registered from live data
through the real route handler (**101 members, 12-char checksum, `BRK.B → BRK-B` with the raw form
retained, provenance embedded, integrity-verified**), re-verified the pin
(`Config().config_fingerprint() == 08e471b10130e1e2`), re-diffed the TC-11 kept-route capture
(14/14 byte-identical), and proved TC-13 empirically by re-running the three new test files with
`socket.connect`/`create_connection`/`getaddrinfo` hard-blocked (41 passed / 1 skipped, zero
network). No CRITICAL or IMPORTANT finding survived verification, so no fix was applied. Six real
gaps are documented below — the load-bearing one (**B1**) is that the four new `Config` fields
cold-invalidate every durable cache keyed on `edge_report_cache._config_content_hash`, which I
proved on disk: the pre-iteration `/research/setups` scan row (134 MB, created today at
02:04:25Z) is now unreachable, so the next real call re-runs the ~9–11 min full-panel scan.

---

## 2. Findings

### Backend Findings

**B1 — GAP (gap, not fixed — deliberately): the four new `Config` fields cold-invalidate every
`_config_content_hash`-keyed durable cache; `/research/setups` is now cold on the real data dir**

`apps/backend/app/config.py:1118-1134` adds four fields to the `Config` dataclass. The Path-A
protocol the spec mandates (`config_fingerprint()` exclusion set, `config.py:1567-1570`) was
followed exactly and the pin is unchanged — but there is a **second**, independent whole-config
hash that the spec's Path-A protocol never mentions:
`apps/backend/app/research/edge_report_cache.py:165-169` hashes `dataclasses.asdict(config)` with
**no exclusion set at all**, and it is the shared key component for four durable caches —
`setups_scan_cache` (`setups.py:440-455`), `tradability_cache` (`routes.py:966-975`),
`edge_report_cache` (`edge_report_cache.py:179-185`) and `edge_report_backtest_cache`
(`edge_report_backtest_cache.py:102`). Adding fields to `Config` changes that hash, so every row
written before this diff becomes unreachable.

Proved on the real data directory, not inferred:

```
config_content_hash NOW  : dc0271c15a2687884b6b41f1…      (post-diff)
config_content_hash PRE  : 5e6236b5e65a8aaa2bc616d8…      (same asdict minus the 4 desk fields)
CHANGED BY THIS DIFF     : True

.data/setups_scan_cache.db (10 rows)
  CURRENT (post-diff) key present : False
  PRE-ITERATION key present       : True   created 2026-07-25T02:04:25.639015Z
                                           result_json = 134,300,138 bytes
```

`app/config.py` mtime is `04:22:48`; the stranded row was written at `02:04:25Z` — i.e. it was
warm when this iteration started (iter-0's baseline walk warmed it) and is cold now. The concrete
cost is exactly the trap this phase spec itself carries forward in NOTES: *"The scoped QA
backend's first `GET /research/setups` call runs cold at ~9–11 min (0.84s warm) — warm the cache
before any browser pass that touches Case Studies."* That trap is now armed on the **real** data
dir, and J-04 is the next iteration expected to dispatch browser QA. `tradability_cache` (18 rows,
the `/structure` Load 21.6s→1.4s cache) and `edge_report_backtest_cache` (25 rows, the resumable
sweep) key through the same function and are invalidated the same way; `edge_report_cache`'s single
row (2026-07-22) was already unreachable before this diff via the sanctioned 5D epoch bump, so this
diff does not newly strand it.

Why this is a GAP and not IMPORTANT (I weighed both, and this was the closest call in the audit):
1. **No served value changes.** `config_content_hash` is key material only — it is never
   serialized into any response body (verified by grep across `app/`: the only non-cache call site
   is `routes.py:971`, which passes it into `tradability_cache_key`). TC-11's byte-identity claim
   therefore still holds; only latency regresses.
2. **The recomputed value is provably identical.** No desk field is read anywhere in the
   levels/tradability/setups/backtest call graph — `grep -rn "desk_universe_" app/` returns hits
   only in `config.py` and the two new desk modules — so the cold scan reproduces the same bytes.
3. **The busting behaviour is the documented, deliberate contract** of that hash, not a defect
   introduced here: `edge_report_cache.py:60-68` states it hashes every field "with NO exclusion
   set … any config field change, fingerprinted or not, busts this cache … an extra, harmless
   recompute, accepted."
4. **The only available code fix would be worse than the gap.** Adding a hand-picked
   `desk_universe_*` exclusion to `_config_content_hash` would edit a frozen kept mechanism shared
   by four caches, install the second copy of an exclusion policy its own docstring warns against,
   and weaken a deliberately conservative guard — squarely a "frozen foundations" edit and scope
   creep well outside J-01. That is a decomposer/spec decision, not an audit-time edit.

Carry forward (two items, both for the next spec): (a) warm `GET /research/setups` on the real
data dir before J-04's browser pass — it is cold right now; (b) the era's Path-A protocol should
state what happens to `_config_content_hash` when a field is added, because **every** further
era-B `Config` field will re-bust these caches the same way.

**B2 — GAP (gap): the parser silently drops rows, contradicting its own "never a per-row skip"
claim**

`apps/backend/app/research/desk_universe.py:277-281` skips any row too short to reach the symbol
column and any row whose symbol cell is empty after citation-stripping. The module's own contract
(`desk_universe.py:258-259`) states the opposite discipline: *"the WHOLE fetch is refused, never a
per-row skip that would silently shrink the list."* The `[90, 110]` bounds check is the only guard,
so a drift of 1–13 dropped rows registers as a valid, plausible-looking snapshot with no signal
that anything was dropped. Realistic trigger: the live constituents table gains a spanning
notes/footnote row, or a row with an empty Symbol cell. Not a defect against the spec (whose named
error cases — charset, bounds, table shape — are all honestly implemented and tested, and the real
page currently parses to exactly the true index size of 101), and the reviewer already logged the
row-skip half as a NOTE (`reports/reviews/goal-desk-iter-1-review.md:26-28`). Recommendation for
J-02, when exact membership completeness starts driving screening: carry a `skipped_rows` count in
the snapshot payload so the ambiguity is surfaced rather than dropped.

**B3 — GAP (gap): a corrupt snapshot file with the same date+checksum is silently overwritten by a
re-record**

`UniverseStore.record` (`desk_universe.py:395-418`) detects duplicates by scanning
`self.list()`, and `list()` (`desk_universe.py:370-379`) moves any file failing its checksum
verification into the `errors` list rather than `records`. A corrupt file is therefore invisible to
the duplicate check, and because `snapshot_id` is `universe-<today>-<checksum12>`, the subsequent
`write_text` lands on the **same path** and overwrites it. Verified empirically:

```
registered:  universe-2026-07-25-817cc184bbb3
after tamper -> records: 0  errors: 1
RE-RECORD ACCEPTED -> universe-2026-07-25-817cc184bbb3  (same path: True)
corrupt file OVERWRITTEN;  final records: 1  errors: 0
```

Why GAP and not a breach of "snapshots are never rewritten": no **valid** snapshot can ever be
lost this way — a valid duplicate always raises `UniverseAlreadyRegistered` before any write
(TC-5, verified) — so the only reachable case replaces an unreadable file with a valid one, i.e. a
self-heal rather than data loss. It is nonetheless a *silent* one: the operator gets no indication
that a file previously reported in `integrity_errors` was replaced. Related and consistent with
precedent: `write_text` is non-atomic (no temp+rename), exactly as `bars.py:575` and
`datasets.py:443` already do it, so a crash mid-write is the realistic way to create the corrupt
file in the first place.

**B4 — OBSERVATION (observation): the `.` branch of the ticker charset is unreachable**

`_TICKER_RE = ^[A-Z.-]{1,6}$` (`desk_universe.py:49`) is matched only **after**
`raw.replace(".", "-").upper()` (`desk_universe.py:290-291`), so no candidate can ever contain a
`.` at check time. Harmless and deliberately spec-faithful (the spec and `docs/goal.md` both write
the charset as `[A-Z.-]{1,6}`) — noted only so a future reader does not mistake it for a live
guard. Same line: `.upper()` means a lowercase vendor ticker is silently accepted and uppercased
rather than rejected.

**B5 — GAP (gap): `docs/goal.md`'s J-01 step 1 names a "derived index" that was not built**

`docs/goal.md` J-01 step 1 describes the store as "`.data/universe/universe-<date>-<checksum12>.json`,
frozen JSON **+ derived index**". No index ships. This is a documented, reasoned decomposer
decision (`docs/phases/goal-desk-iter-1.md:53` and NOTES:136) and J-01's own *Acceptance* clause
does not mention an index, so J-01 can still be judged passing — recorded here so the evaluator
sees the delta against the journey text rather than only against the iteration spec, and so J-02
(whose acceptance genuinely does have an index-speed requirement) inherits it explicitly.

### Frontend Findings

**F1 — none applicable (verified, not assumed).** `git status` shows zero frontend files touched;
`UI_ROUTES` is still exactly two rows (`apps/backend/app/meta.py:27-30`, `Cockpit` + `/structure`);
no `/desk` route, nav entry or fetch button exists. That matches `Frontend Present: no` and the
spec's "UI surface changes: None". The backend capability being UI-invisible this iteration is
correct scope, not a hidden feature — `/desk` is J-04's job.

### Test Findings

**T1 — OBSERVATION (observation): three QA rows were signed off on the dev handoff rather than
independently executed**

`reports/qa/goal-desk-iter-1-qa.md:55` (TC-04), `:60` (TC-09) and `:64` (TC-13) carry
"Verified by dev handoff" / "Verified by dev handoff; unit test suite includes …" as their
evidence. That is below the evidence floor for a PASS row. All three are in fact sound — I
verified them independently:
- TC-04 / TC-09: covered by `test_post_fetch_with_a_charset_violating_ticker_is_an_explicit_422`,
  `test_post_fetch_with_an_out_of_bounds_count_is_an_explicit_422` and
  `test_route_level_counter_test_raising_min_members_refuses_the_same_valid_fixture`, all green in
  my own suite run, each asserting both the 422 **and** that no snapshot file was created.
- TC-13: proved harder than the handoff's "by construction" claim — I re-ran the three desk test
  files under a plugin that replaces `socket.socket.connect`, `socket.create_connection` and
  `socket.getaddrinfo` with a raising stub: `41 passed, 1 skipped in 1.28s`. Zero network calls,
  demonstrated rather than argued.

**T2 — OBSERVATION (observation): TC-11's capture covers 14 of 24 kept GET route templates, all
against an empty data dir**

The spec's TC-11 (`docs/phases/goal-desk-iter-1.md:126`) says "**every** kept `/research`, `/tape`,
`/meta` GET route". The delivered capture (`runs/goal-desk-iter-1/kept-route-baseline.txt`) probes
14 paths; the app actually exposes 24 kept GET route templates (OpenAPI enumeration) — unprobed:
`/research/levels`, `/research/tradability`, `/research/bars/{id}`, `/research/bars/{id}/candles`,
`/research/datasets/{id}`, `/research/setups/{id}`, and `/tape/{ticker}/{features,events,summary,history}`.
Both captures also ran against a hermetic temp `.data/` dir, so every store-backed route was
recorded in its empty state (`/research/setups` → body_len 13, `{"events":[]}`), which is
structurally unable to observe the cache-warmth change B1 documents. Adequate evidence for *this*
diff — it is provably additive, and the four new fields are read by nothing outside the two new
desk modules — but the protocol's wording overstates its own coverage, and the empty-dir choice is
what let B1 through the gate unnoticed.

**T3 — OBSERVATION (observation): skip count 7 → 8**

TC-12's literal "exactly 7 skipped" is stale by one because TC-14 mandates a new
`TAPEOLOGY_LIVE_INTEGRATION`-gated test that self-skips, matching the three existing integration
files. Confirmed live (`1210 passed, 8 skipped`), honestly flagged by the developer
(`docs/handoffs/goal-desk-iter-1-dev.md:99-113`) and by the reviewer. Accepted; the next spec
should state the skip floor as 8, non-decreasing.

**T4 — GAP (gap): the dev handoff's closing bullet is self-contradictory and now factually stale**

`docs/handoffs/goal-desk-iter-1-dev.md:177-180` says *"The real `.data/universe/` directory now
holds one real, live-fetched snapshot"* and then, in the same bullet, *"(… NOT the repo's real
`apps/backend/.data/`). No production data directory was touched by this work."* The header clause
is the true one: `apps/backend/.data/universe/universe-2026-07-25-49b33fa31680.json` exists
(mtime 04:58, i.e. **after** the handoff was written and after the dev step closed at 04:01 —
almost certainly QA's live backend verification, which reports the same checksum
`49b33fa31680`). I read it through the real route handler: 101 members, `integrity_errors: []`,
provenance intact, no dotted tickers, `raw_members["BRK-B"] == "BRK.B"`. Nothing is committed
(`.gitignore:72` covers `.data/`) and the write came from an explicit operator POST, so no
anti-goal is breached — but the claim as written is wrong, and there is a real consequence for
J-02+: the production universe dir is **pre-populated**, so a fresh live POST of identical
Wikipedia content will now return 409 rather than register.

---

## 3. Domain Assessment

The core domain logic is sound and, unusually, honest in the places where honesty is expensive.

**Parser.** Stdlib-only (`html.parser.HTMLParser`), no dependency drift — grep for
`bs4|BeautifulSoup|lxml|html5lib|read_html|pandas` in the new modules returns only the docstrings
saying they are not used. The symbol column is located by header text
(`_find_symbol_column`, `desk_universe.py:234-246`), never a hardcoded index, and a test proves the
same parser works with Symbol at index 0 and at index 2. Normalization happens **before** the
charset check and before dedup, which is the correct order (a raw `BRK.B` would otherwise fail a
post-normalization charset gate or dedupe into the wrong bucket), and `setdefault` keeps the first
raw form so `raw_members` is stable. Failure modes are distinct and specific — no recognizable
table, zero tickers, a named charset violator, an out-of-bounds count — and all four abort the
whole fetch. The one soft edge is B2.

**Store.** Immutability is structural, not policed: there is no update or delete function in the
module, `record` is the only writer, and duplicate content raises before any write, so TC-5's
"byte-unchanged" property is a consequence of control flow rather than a promise. The content
checksum keys on the normalized membership alone, which is the right identity choice — the same
membership fetched on a different day from a re-rendered page is correctly recognized as the same
content. Integrity is verified on **every** load and a bad file is surfaced as an explicit
`integrity_errors` row rather than hidden or served as data; `list()` hands out fresh copies of the
nested `members`/`raw_members` so a caller cannot poison a later read. The single hole is B3.

**Routes.** The failure taxonomy maps cleanly and server-side: 503 vendor-unreachable, 422
parse/charset/bounds, 409 duplicate, 200 honest-empty before any registration (never 404). The GET
handler reads only — it cannot trigger a fetch or a compute, which is the era's
"every run is an explicit operator act" anti-goal implemented rather than asserted. `latest` is the
stored record verbatim (`desk_routes.py:101-103`), not a recompute, so single-source-of-truth
holds. The fetch seam is a real FastAPI dependency, so hermetic tests inject fixture HTML with no
monkeypatching of module internals.

**Anti-goals I checked against code rather than the QA checklist.** MCP stays read-only — the
proxy issues `client.get(path)` only (`app/mcp/__init__.py:382`) and
`ALLOWED_GET_PREFIXES = ("/tape/", "/research/", "/meta/")` (`:57`) covers the new GET path with no
MCP change, so the spec's claim there is accurate and the new POST is unreachable from MCP. T-3
holds and its guard is well built — it scans only actual import lines, so the module's own docstring
naming `DatasetStore` in prose cannot false-pass it, and a lazy in-function import would still be
caught because it strips indentation first. Membership never enters a computation: nothing outside
the two desk modules reads a `desk_universe_*` field. No statistics, gates, strategies, ledger rows
or order concepts appear anywhere in the diff.

**Test quality.** Assertions are tight and specific rather than accommodating: exact member counts
(`== 103`), exact first three tickers, `len(checksum) == 12` plus a hex parse, `"BRK.B" not in
members` (the negative form, which is the one that actually catches a normalization regression),
byte-comparison of the on-disk file across a refused duplicate, and file-count assertions after
every failure path so a partial registration cannot hide. The counter-test is run twice —
once against the pure parser and once end-to-end through the route — which is the right shape,
since the route version is what proves the field is live-wired rather than merely readable. The
committed "fixture universe" is internally consistent under its own verifier: I recomputed both
checksums independently (`file_checksum` matches the record; the 12-char content checksum
recomputes to `817cc184bbb3`, matching both `meta["checksum"]` and the filename), so J-02–J-05 can
rely on it. Two soft spots: `test_the_committed_fixture_snapshot_is_a_valid_already_registered_universe`
asserts four fields rather than equality against a fresh `record()` of the same fixture (so a
future drift in the record shape would not be caught there), and nothing tests the B3 overwrite
path or a mixed valid+corrupt directory.

---

## 4. Fixes Applied During This Audit

| # | Severity | File | Change |
|---|----------|------|--------|
| — | — | — | **None.** No CRITICAL or IMPORTANT finding survived verification. |

Every finding above is a GAP or an OBSERVATION, which the auditor contract explicitly says to
document rather than fix. The one finding that came close to IMPORTANT (**B1**) is deliberately
left unfixed: its only available code fix would add a hand-picked exclusion set to
`edge_report_cache._config_content_hash` — a frozen, kept mechanism shared by four caches whose own
docstring both refuses an exclusion set on purpose and warns against a second copy of that
policy. Weakening it to make this iteration's diff look clean would trade a documented latency gap
for a real "frozen foundations" violation and out-of-scope scope creep. No dev-handoff claim was
invalidated by an audit fix (T4's stale claim predates the audit and is reported, not edited).

Verification commands run during this audit, with results:

| Check | Command | Result |
|---|---|---|
| Full suite | `cd apps/backend && .venv/bin/python -m pytest tests/ -p no:warnings` | `1210 passed, 8 skipped in 118.90s` |
| Hermetic proof (TC-13) | same, on the 3 desk test files, `-p no_network_plugin` (socket connect/create_connection/getaddrinfo stubbed to raise) | `41 passed, 1 skipped in 1.28s` — zero network |
| Fingerprint pin (TC-8) | `python -c "from app.config import Config; print(Config().config_fingerprint())"` | `08e471b10130e1e2` |
| Live vendor (TC-14) | `TAPEOLOGY_LIVE_INTEGRATION=1 pytest tests/test_desk_universe_live_integration.py` | `1 passed in 0.21s` (independent of the handoff's claim) |
| Kept routes (TC-11) | `diff kept-route-baseline.txt kept-route-after.txt` | 14/14 status+sha256+body_len identical (only the label/port comment lines differ) |
| Real snapshot (TC-2/3/6/10) | `get_universe(get_universe_store())` against the real `.data/universe` | 101 members, checksum 12 chars, sorted+unique, no dotted tickers, `raw_members["BRK-B"]=="BRK.B"`, provenance = URL/90/110, `integrity_errors: []` |
| Fixture snapshot integrity | recomputed `file_checksum` + content checksum12 | both match; filename == `meta["checksum"]` == `817cc184bbb3` |
| Cache invalidation (B1) | recomputed `_config_content_hash` with/without the 4 desk fields vs. `.data/setups_scan_cache.db` | pre-iteration key present (134 MB, 02:04:25Z); post-diff key absent |
| Store overwrite (B3) | tamper a snapshot, re-record identical content | accepted; corrupt file overwritten at the same path |

**Definition of Done — verified item by item:** (1) J-01/TC-1–TC-7 ✔ (all seven traced through
code and re-executed); (2) Path-A fields + exclusion + stability + counter-test + provenance, pin
unchanged ✔ (with B1's caveat about the *other*, non-fingerprint hash the protocol never named);
(3) TC-11 kept-route byte-identity ✔ (coverage caveat T2); (4) no anti-goal violation ✔
(append-only, no `datasets.py` routing, hermetic suite proven with sockets blocked, MCP still
GET-only, pin unmoved); (5) suite ≥1169 passed / 0 failed ✔ (1210/8, skip deviation T3);
(6) live Wikipedia fetch attempted and honestly reported ✔ (re-verified independently);
(7) dev handoff written ✔ (one stale bullet, T4).

---

## 5. Recommended Next Step

**Proceed to J-02.** J-01 delivered the seam, the honest parser, the append-only checksummed store
and both routes, at the scope the spec set and no wider; the era's dependency chain is genuinely
unblocked and "the fixture universe" is real, verified and reusable by name. Nothing here needs
rework before the next iteration.

Four things the next spec must carry forward, in priority order:

1. **Warm `GET /research/setups` on the real data dir before the next browser-QA pass (J-04).** It
   is cold *right now* because of B1, and cold means ~9–11 minutes on the first call. This is the
   exact false-negative shape the current spec's NOTES already warn about; it is now armed on real
   data rather than only on the scoped QA backend.
2. **Extend the era's Path-A protocol to `_config_content_hash`.** Every future era-B `Config`
   field will re-bust the setups/tradability/edge-report/backtest caches the same way. The
   decomposer should decide explicitly — accept and schedule the re-warm, or make a spec'd,
   tested change to that hash — rather than rediscovering it per iteration.
3. **Note that the production universe dir is pre-populated** (T4): a live POST of identical
   Wikipedia content now returns 409, which will surprise J-02–J-05 verification steps that expect
   a fresh registration.
4. **Small hardening, only if J-02 makes exact membership load-bearing:** surface a `skipped_rows`
   count from the parser (B2), and state the suite's skip floor as 8, non-decreasing (T3).
