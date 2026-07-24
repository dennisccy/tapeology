# goal-clean_slate-iter-1 Audit Report

**Date:** 2026-07-24
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

J-01's backend demolition is genuinely complete and byte-safe: the three "relocations" are byte-identical to their `fa76460` originals (only docstrings referencing now-deleted callers were trimmed), 27/28 kept routes are sha256-identical with `/research/taxonomy` the sole sanctioned diff, the 11 modules / 14 routes / journal-era store methods / 25 test files are gone grep-provably, and `config_fingerprint()` still prints `4d665603569b9dbf` with all 13 pins byte-untouched. The two documented "gaps" — one pre-authorized failing MCP test (owned by J-03) and four `None`-returning `ResearchRegistry` stubs kept alive for J-02's WS-merge removal — are both spec-sanctioned cross-iteration deferrals that were resolved correctly; forcing either "closed" this iteration would have *introduced* a regression (reverting a deletion, editing an out-of-scope file, or breaking the live WS tape stream), so they are acceptable and carried forward, not defects.

---

## 2. Findings

### Backend Findings

**B1 — GAP (documented): DoD "0 failed" vs. the one pre-authorized MCP-proxy failure.**
The suite is `1165 passed, 1 failed, 0 errors, 7 skipped`. The DoD line "Full backend suite passes (0 failed, 0 errors)" is literally unmet, but the single failure is `tests/test_mcp_server.py::test_static_live_tools_json_byte_identical_to_rest` (`test_mcp_server.py:244`), which iterates `LIVE_STATIC` (`test_mcp_server.py:81`) and fails on `journal → GET /research/journal` now returning 404. This is the EXACT scenario the phase spec's OUT OF SCOPE section pre-authorizes ("The three soon-dead MCP tools transiently proxy to now-404 routes via `get_endpoint`'s existing honest-404 contract this iteration — expected, not a defect") and the spec explicitly forbids touching `test_mcp_server.py` this iteration ("Leave `test_mcp_server.py` ... untouched ... belongs to J-03"). I verified the failure is nothing more: it fails fast on the first deleted-route proxy; `taxonomy`/`ui_route_map` still 200. No fix applied — the only ways to force green (revert a route deletion, or edit the J-03-owned test) each violate the phase scope. Owned by J-03.

**B2 — GAP (documented): spec IN-SCOPE says "strip `hint_projection_for`", but it was kept as a `None` stub.**
The phase spec IN SCOPE line 52 says to strip `ResearchRegistry`'s `hint_projection_for`. The dev instead kept `hint_projection_for` (`routes.py:294`), plus `projection_for`/`monitor_for`/`_surviving_projection`, as permanent `None`-returning stubs. I traced the reason and confirm it is correct: the *only* live callers of these in `app/` are `main.py:616` (`projection_for`) and `main.py:628` (`hint_projection_for`) — the WS `thesis`/`hint` frame merge, which the SAME spec explicitly defers to J-02 (OUT OF SCOPE, and IN SCOPE line 53 "the WS `thesis`/`hint` merge is J-02's job, not this iteration's"). Stripping the method while its caller survives would raise `AttributeError` on every WS frame and break the live cockpit tape stream — a far worse "frozen kept surface" anti-goal violation. The stub is honest: `main.py:595/600` merely assign the result into `frame["thesis"]`/`frame["hint"]`; `None` serializes to JSON `null`, which `main.py:592-593` documents as "a normal state, never an error", and `None` was already the return for an unwired registry. Documented as dev Known Issue #4 with an explicit J-02 handoff ("delete `hint_projection_for`/`projection_for`/`_surviving_projection`/`monitor_for` in the SAME commit that removes the WS merge"). This is a sanctioned T-14 inventory correction, not an improvisation. No fix applied (a "fix" here reintroduces the breakage).

**B3 — OBSERVATION: one docstring line of the KEEP method `set_champion_pointer` was edited.**
`store.py`'s `set_champion_pointer` (an I-3 KEEP method the DoD says stays "untouched") had exactly one docstring line changed — dropping "`(e.g. ``expire_stale_actives``)`", a reference to a journal-era method that IS deleted (grep: no definition/call remains). The executable body is byte-identical (verified by full-body diff vs `fa76460`), and the champion-pointer route is among the 27 byte-identical kept routes. Zero behavioral impact; the edit is arguably *required* by the "deletion complete, never cosmetic" anti-goal (don't leave a docstring pointing at a deleted method). Not fixed — reverting would reintroduce a dangling reference.

### Test Findings

**T1 — OBSERVATION: a source-introspection guard's anchor string was updated to track the relocation.**
`test_backtests.py`'s `test_runner_consumes_the_shared_r_helper_and_the_public_dataset_api` changed its assertion from `assert "from .marks import r_basis" in src` to `assert "def r_basis(" in src`. The "No guard weakening" anti-goal says source-introspection guards "stay as written", but the old anchor is now *impossible* (`marks.py` is deleted, so the import string can never appear) — keeping it verbatim would red-fail the guard on a property that MOVED, not one that was violated. The new anchor verifies the relocated single-owner `def r_basis(` is present in `backtests.py` — an equal-strength substring canary preserving the "one R formula, one owner" guarantee. This is a faithful adaptation to the sanctioned relocation, not a weakening; documented in the dev handoff. The 2 fingerprint pins in the same file (`test_backtests.py:416`, `:1485`) are byte-identical (confirmed by `sed` — both still `assert CONFIG.config_fingerprint() == "4d665603569b9dbf"`; the only line-adding hunk sits after 1485).

### Frontend Findings

None — `git diff fa76460 -- apps/frontend/` is empty (verified), as required for this backend-only iteration.

---

## 3. Domain Assessment

The load-bearing risk of a demolition iteration is that a "relocation" silently alters research math while the noise of 18,597 deletions hides it. I verified each relocated symbol against its `fa76460` original rather than trusting the handoff:

- **`r_basis`** (→ `backtests.py`): body byte-identical (`return abs(reference_price - invalidation_price)`); only the docstring's dead-caller references trimmed.
- **State-native arming family** (→ `backtests.py`): `_control_state`, `_absorption_state` (comment included), `_premise_state` (body), `_synthetic_invalidation` (all three body lines), `STATUS_*`, `TERMINAL_STATUSES`, `_PROGRESS_EVERY = 250`, `_PathPoint` (all four fields) — every executable line byte-identical. The dev's own gap-catch (`_absorption_state`, which the plan's gap-note missed) is a real latent-`NameError` avoidance, correctly relocated.
- **Dataset-source vocabulary** (→ `datasets.py`): `SOURCE_REFERENCE`/`SOURCE_HISTORICAL`/`REFERENCE_SOURCE_ID` and the full `_load_reference_window` body (fixture path, trade/quote parsing, `HistoricalWindow` construction) byte-identical.

The behavioral proof is threefold and independent: (1) the sha256 byte-comparison shows 27/28 kept routes unchanged (`kept-route-baseline.txt` vs `kept-route-after.txt` diff — only line 24 `research.taxonomy` 14021→304 bytes); (2) the frozen `config_fingerprint()` still prints `4d665603569b9dbf`; (3) the 1165-test suite (which exercises the relocated helpers via `test_backtests.py`'s pinned trade-arithmetic) is green but for the one pre-authorized MCP failure. The taxonomy slim honestly retains the required `sim`/`iex`/`sip`/`yahoo` source labels (they live inside `feed_basis.feeds[]`, verified in the captured body) — the dev's "slimmed to feed_basis" phrasing and TC-04's requirement are both satisfied. Failure handling stays explicit and ambiguous data stays honest: the demolished-surface stubs return the pre-existing `null` normal state, never a fabricated value, and the deleted routes 404 honestly (the failing MCP test is itself the proof that `/research/journal` → 404). Core domain logic is intact.

---

## 4. Fixes Applied During This Audit

None. Every finding is GAP- or OBSERVATION-level and spec-pre-authorized; per the auditor rubric these are documented, not fixed. Critically, each is a case where applying a "fix" would *introduce* a regression:

| # | Severity | File | Why NOT fixed |
|---|----------|------|---------------|
| B1 | GAP | `tests/test_mcp_server.py:244` | Forcing green needs a route-deletion revert (defeats the phase) or a J-03-owned edit (out of scope). Spec pre-authorizes it. |
| B2 | GAP | `app/research/routes.py:294` | Stripping the stub breaks `main.py:628` WS frames (live tape stream). Its caller-removal is J-02's scope. |
| B3 | OBSERVATION | `app/research/store.py` (`set_champion_pointer`) | Reverting reintroduces a docstring reference to the deleted `expire_stale_actives`. |
| T1 | OBSERVATION | `tests/test_backtests.py` (~L1493) | Reverting the anchor red-fails a guard on a property that legitimately moved. |

---

## 5. Recommended Next Step

**Proceed to J-02 (frontend/WS demolition).** J-01's backend goal is fully and safely achieved. J-02's planner should carry forward two items already flagged in the dev handoff and re-confirmed here:

1. **Delete the four `ResearchRegistry` stubs in the SAME commit that removes the WS `thesis`/`hint` merge from `main.py`** (`projection_for`, `hint_projection_for`, `monitor_for`, `_surviving_projection`, and the inert `_monitors` dict) — they become genuinely dead only once `main.py:616/628` are gone (B2).
2. **The one failing MCP test is J-03's**, not J-02's — do not "fix" it during frontend work; it closes when `test_mcp_server.py`'s 15-tool contract is updated and the `journal`/`analytics`/`studies` MCP tools are removed (B1).

Also still pending for J-05 (unchanged by this iteration): the pre-existing suppressed `SHOW_CASE_STUDIES` flag on `/structure` must be resolved (restore vs. operator rescope) before J-05 can close.
