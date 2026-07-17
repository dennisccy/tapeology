# goal-fast_wall-iter-2 Audit Report

**Date:** 2026-07-17
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS

J-02 ("the stores stop re-reading") is genuinely achieved. The in-process stat-keyed caches
(`bars._VERIFIED_CACHE`, `datasets._VERIFIED_META_CACHE`) and the durable `dataset_index.db`
faithfully implement the spec, and the two CRITICAL anti-goals this iteration touches — "the
verification trust boundary never weakens" and "no divergent accelerator output" — are upheld
*mechanically*, not just by assertion: I confirmed by reading the diff that `load_events`/`replay`
bodies are byte-unchanged (only docstrings moved), and I re-ran the trust-boundary, byte-identity,
tamper, racy-write, and durable-index tests myself. The implementation is surgical (read-path
caching added; no mutation or verification logic altered), scope is exact (5 backend files + tests,
zero frontend, zero out-of-scope files), and `config_fingerprint()` is frozen at `4d665603569b9dbf`.
No CRITICAL or IMPORTANT issue found; the three findings below are all OBSERVATION-level and warrant
no fix.

---

## 2. Findings

### Backend Findings

**B1 — OBSERVATION (gap): `BarStore.root` returns an UNRESOLVED path despite "resolved" wording**
`bars.py:174-184` — `__init__` sets `self._root = Path(root)` (no `.resolve()`) and the new `root`
property returns it verbatim. But the property docstring says "The resolved root directory", the
phase-spec TC-11 says "returns R's resolved path", and the test-plan pass criterion says "equal to
`Path(R).resolve()`". The test (`test_bar_store_root_is_a_public_read_only_property`,
`test_bars.py:333`) only asserts `store.root == root` against an already-absolute `tmp_path`, so it
never exercises the "resolved" claim (no relative path, symlink, or `..` input). No functional
impact **this** iteration: `BarStore` is always constructed with `CONFIG.bar_dir_resolved()` or a
`tmp_path` (both already absolute), and the property has no consumer yet (its stated purpose — a
future J-06 sibling-path derivation — is out of scope). The substantive TC-11 clauses (public,
read-only) both pass. I was unsure between GAP and OBSERVATION and settled on OBSERVATION because
there is no consumer and no realistic wrong behavior in scope. **Not fixed** — changing `self._root`
to resolved would ripple through every file-I/O path in the store (a frozen-foundation surface) for
a cosmetic wording match, i.e. scope creep against the "frozen foundations" anti-goal; the honest
fix is a one-word docstring correction, which I am flagging rather than making.

**B2 — OBSERVATION (observation): durable index serves metadata verified in a PRIOR process**
`datasets.py:316-322` + `dataset_index.py` — a durable-index hit returns metadata that was
checksum-verified in an *earlier* process's lifetime, which is in literal tension with the CRITICAL
anti-goal's phrase "stat-keyed serving applies only to content already fully verified *in this
process's lifetime*". This is **not a violation**: it is exactly what Must-have journey J-02's GOAL
statement and TC-9 mandate (a fresh `DatasetStore` on restart must serve `list()` with zero file
reads). The threat model is identical to the in-process cache — both key on `(path, size,
mtime_ns)`, any stat change forces a full re-verify, integrity failures are never cached, and the
durable row is only ever written from a value `_load` already verified (`datasets.py:328-329`). The
research-value paths (`load_events`/`replay`) always re-verify regardless (proven below), so no
research value is ever read from either cache. The durable index is a pre-registered rebuildable
accelerator that owns nothing — deleting it loses nothing and repopulates byte-identically (TC-10,
which I ran). Flagged for honesty; the coherence-auditor lane is the formal blessing for this
accelerator.

**B3 — OBSERVATION (observation): `DatasetIndex` holds a long-lived sqlite connection, no close()**
`dataset_index.py:71` — one `sqlite3.connect(...)` per `DatasetIndex`, with no `close()` or
context-manager. Because `get_dataset_store()` builds a fresh `DatasetStore` per request, a cold
in-process-cache request opens a new connection. In practice this is not a leak: there is no
reference cycle (`Connection` does not point back to `DatasetIndex`), so CPython refcounting frees
it at request end and `Connection.__del__` closes it promptly; and connections open only on
in-process misses (cold start / stat change), which are rare after warm-up. It mirrors the accepted
`bar_index.py` / `get_bar_index()` precedent exactly. No action needed.

### Frontend Findings

None — this iteration ships zero frontend files (confirmed: `git diff` touches nothing under
`apps/frontend/`). `Frontend Present: no` is correct.

### Test Findings

**T1 — OBSERVATION (observation): the durable/trust-boundary tests spy on `_load`, not raw syscalls**
`test_dataset_index.py:119-125`, `test_datasets.py` `_spy_on_load`, `test_bars.py:265` — "zero
reads" is proven by counting calls to `BarStore._load`/`DatasetStore._load` rather than counting OS
`read()` syscalls. This is a sound proxy: `_load` is the ONLY method that calls `path.read_text()`,
so 0 `_load` calls ⇒ 0 content reads. The tests are otherwise tight and honest — they reset the
in-process cache to genuinely force the durable-index path (TC-9/TC-10), install the spy *after*
warming to isolate `load_events`/`replay` (TC-7), and assert byte-identity via `sort_keys=True` and
raw `response.content` equality (TC-8/TC-9). No weakness; noted only for completeness.

---

## 3. Domain Assessment

The core discipline of this interlude is "make the read path fast without ever weakening what
verification guarantees." The implementation gets the hard part right:

- **The trust boundary is preserved structurally, not just behaviorally.** `get`/`list` route through
  `_cached_meta`/`_cached_load`; `load_events`/`replay` route through the untouched
  `_load_by_id → _load` path. I verified via `git diff` that the only changes to the `load_events`
  and `replay` methods are in docstrings/comments — their executable bodies are byte-identical to
  `HEAD`. TC-7 mechanically proves both re-verify (spy = 1 full `_load` each) even with a warm
  metadata cache. This is the exact shape the CRITICAL anti-goal demands.

- **Integrity failures can never be served stale.** `_load` raises before any cache publish, so only
  successful verifies are ever cached. A tamper changes the file's mtime → stat mismatch → forced
  re-verify → `*IntegrityError` (TC-3 bars, TC-4 datasets, TC-14 edge-report-500-still-bubbles — all
  re-run green by me). The metadata cache never masks the edge-report integrity path.

- **The racy-write guard is sound.** Publishing only when `now - mtime ≥ 2s` (on both the in-process
  and durable-insert paths) is correct for any filesystem mtime resolution ≤ 2s: by the time a file
  is eligible to cache, any second write sharing its mtime tick has already landed and been verified.
  TC-5 proves a freshly-written file re-reads on the second call.

- **Byte-identity holds across all three serving paths.** `meta_json` is stored without `sort_keys`
  and the reconstruction `{**meta, "event_counts": dict(...)}` preserves original key order, so a
  durable-index-served response is byte-identical to a fresh disk verify. TC-8 (REST + MCP, standalone
  AND in-module per the applied iter-1 lesson) and TC-9 confirm this; I re-ran all three.

- **Mutation isolation is placed correctly** — at the get/list return boundary, copying the one
  nested mutable field in each store (`bars` rows; `event_counts`). All other meta fields are scalars,
  so the shallow `{**meta}` copy is sufficient. TC-6 and the `event_counts` test prove it.

No lookahead, no gate/register/vocabulary drift, no new `Config` field, no new runtime dependency
(stdlib `sqlite3`), no source-guard weakened (the MCP test was *extended* with file-aging, its
byte-equality assertion untouched). The accelerators are honest derived values that own nothing.

---

## 4. Fixes Applied During This Audit

None. No CRITICAL or IMPORTANT finding was identified; all three findings are OBSERVATION-level, for
which a fix would be scope creep (and, for B1, would risk the "frozen foundations" anti-goal).

---

## 5. Recommended Next Step

**Proceed to the next iteration (J-03).** J-02 is complete and its dependency consumers are unblocked:
`GET /research/edge-report`'s `_verified_records`/`_cache_key` now ride the cached `dataset_store.list()`
(dev's real-corpus check: cold 29.37s → warm 0.00s, byte-identical, surviving a genuine backend
restart), and `BarStore.root` exists for J-06. Non-regression of the required-still-passing journeys is
well-supported mechanically: zero frontend change, byte-identical dataset responses (TC-8), and the
edge-report integrity path proven unaffected (TC-14) mean J-01 and J-07 cannot have regressed from this
iteration's changes. Two optional, non-blocking clean-ups a future maintainer may batch: correct the
`BarStore.root` docstring wording (B1) and fill in the project's real `.claude/project-template.md`
(the dev's flagged Known Issue — the symlinked template is still the unfilled framework generic).

---

### Verification evidence captured during this audit

| Check | Command | Result |
|-------|---------|--------|
| Targeted store/API tests (TC-1..7, 9..12, 14) | `pytest test_bars test_datasets test_dataset_index test_datasets_api test_edge_report_api` | **78 passed** |
| MCP byte-identity standalone (TC-8) | `pytest ...::test_datasets_tool_byte_identical_on_a_non_empty_live_list` | **1 passed** |
| MCP full module (applied order-coupling lesson) | `pytest test_mcp_server.py` | **28 passed** |
| Full backend suite (TC-13) | `pytest tests/ -q` | **exit code 0 — zero failures** (dev+QA report 1427 passed / 7 skipped; consistent with additive-only test diff) |
| Config fingerprint (TC-13) | `CONFIG.config_fingerprint()` | **`4d665603569b9dbf`** (unchanged) |
| No tests deleted (TC-13) | `git diff -- tests/*.py \| grep '^-.*def test_'` | **none** |
| Scope | `git diff --stat` | 5 backend src/test files + tests; `edge_report.py`, `levels.py`, `setups.py`, `bar_index.py`, `config.py`, `apps/frontend/**` all untouched |
| Trust boundary | `git diff` on `load_events`/`replay` bodies | **only docstrings changed — executable bodies byte-identical** |
