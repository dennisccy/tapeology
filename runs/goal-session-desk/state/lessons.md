# Goal Session desk — Lessons Learned

Append-only ledger of takeaways from prior iterations. The goal-evaluator
appends one entry per iteration; the goal-decomposer reads this file before
planning each iteration to avoid repeating known pitfalls.

Each entry should be 1-3 sentences capturing a non-obvious lesson — surprising
failures, regression triggers, or decisions that worked well. Avoid
restating the verdict (the evaluator-log.md already does that).

## iter-0 — 2026-07-25T03:25:01+01:00

**Verdict:** CONTINUE
**Lesson:** The new J-07 golden (`runs/goal-session-desk/journey-scripts/J-07.json`) step 8 asserts
the text `300.11` — a post-Load, cache-warmth-dependent async value — on the 15 s default timeout,
which is the exact shape of assertion that cost a full iteration in the `yahoo_fetch` era (headless
matcher misses async-rendered list text). Re-point it at a statically-rendered `/structure` shell
string (or widen its timeout) BEFORE the replay lane guards J-07; if replay FAILs step 8 while the
LLM lane passes, the merged results file wins and it is a golden false negative, not a regression.
**Applies to:** any iteration where J-07 rides the deterministic replay lane, and every new golden
script written this era.

## iter-0 — 2026-07-25T03:25:01+01:00

**Verdict:** CONTINUE
**Lesson:** On a freshly-started scoped browser-QA backend, the first
`GET /research/setups?symbol=AAPL` took ~9–11 min at ~96% CPU (warm re-call: 0.84 s) — the
`/structure` Case Studies skeleton is honest, not hung, but any browser pass that clicks a Case
Study needs the cache warmed first or a wait budget far past the usual per-command timeout.
**Applies to:** every browser-QA dispatch against `.data/scoped_browser_qa`; and read it as live
precedent when building J-02's "coverage GET is index-read fast, never re-hashes the store"
requirement (T-4).

## iter-1 — 2026-07-25T06:05:00+01:00

**Verdict:** CONTINUE
**Lesson:** The era's Path-A protocol only protects `config_fingerprint()` — there is a SECOND,
unnamed whole-config hash, `edge_report_cache._config_content_hash` (`apps/backend/app/research/edge_report_cache.py:165-169`),
which hashes `dataclasses.asdict(config)` with NO exclusion set and keys four durable caches
(`setups_scan_cache`, `tradability_cache`, `edge_report_cache`, `edge_report_backtest_cache`). Adding
the four `desk_universe_*` fields moved it to `dc0271c15a26…` (I confirmed the change myself), so
every pre-diff cache row is unreachable: the real-data `GET /research/setups` is cold again (~9–11 min
first call) and `/structure` Load is back to ~21.6 s. Served values are unaffected (no desk field is
read outside `config.py` + the two desk modules), so this is pure latency — but it re-arms exactly the
false-negative trap that has burned prior browser passes.
**Applies to:** every era-B iteration that adds ANY `Config` field (i.e. most of them), and
unconditionally to whichever iteration next dispatches browser QA (expected J-04): warm
`/research/setups` and `/structure` Load on the real data dir first, and budget for the cold call.
