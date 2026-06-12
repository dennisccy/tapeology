**Verdict:** COHERENCE-PASS

## Iteration 17 — Capability-34 engine performance gate

**Session:** i_will_be_super_rich_with_my_loved_ones
**Iteration index:** 17
**Audited diff:** `git diff b2dbf7330aae24f0ecae2eb18430c2468824c4ce`

---

## Step 1 — Data Contract check

### Blueprint rows 1 and 2 (the two rows this iteration touches)

**Row 1 — Tape state + confidence** (`TapeStateClassifier`, served by `GET /tape/{t}/state`)

The diff touches only `apps/backend/app/engine/features.py`. No new function in `features.py` or elsewhere computes tape state or confidence. `classifier.py` is not in the diff at all. No new endpoint or service path was introduced for row-1 values. The `_RefreshSide` class and the surrounding refactor are internal to `_Window` — the `FeatureEngine.compute()` public interface is unchanged (same return shape, same module, same single owner). Row-1 value ownership and serving path: unchanged.

**Row 2 — 14 core features × 5 windows** (`FeatureEngine`, served by `GET /tape/{t}/features`)

`FeatureEngine` remains the sole owner in `features.py`. The change removes the post-eviction quadratic fallback (`self._refresh_incremental = False` that permanently degraded to `_refresh_fractions()`) and replaces it with the `_RefreshSide` incremental structure. The public `compute()` shape and the `_refresh_fractions()` authoritative path for the standalone `FeatureEngine` API are both retained. `_refresh_fractions` is explicitly documented as the oracle and the standalone-API authoritative path; the new engine path calls it only when the standalone API is used (no `eff_*` threaded), so the serving endpoint and the single-owner module are unchanged. No second `FeatureEngine` or second computation of any feature was introduced anywhere in the diff.

The new `_RefreshSide` class is a private helper inside `features.py` — it is not a separately exposed computation path; it is the internal implementation of the existing single owner. The diff shows no new file under `app/engine/` or `app/research/` or the API layer that computes `bid_refresh_score` / `ask_refresh_score` independently.

**New config key: `dense_replay_time_budget_seconds`**

This key is a CI gate budget. It is correctly added to the `excluded` set inside `config_fingerprint()` at `apps/backend/app/config.py:654` with documented rationale, a stability test, and a counter-test (as required by the iter-12/iter-16 discipline and the iter-17 spec). It does not appear as a displayed value, does not enter any persisted computation (no verdict, feature, excursion, grade, or stamp reads it), and is not a new contract value. No violation.

**New test/fixture assets**

The untracked files (`test_dense_replay_gate.py`, `test_refresh_increment.py`, fixture `PG_20260609_170000_171000_sip.json`) are test-only assets. They consume the canonical `FeatureEngine` / `TapeEngine` paths — they do not introduce independent computation of any contract value. Not a contract violation.

**No new displayed value** — the iter spec and surface map both confirm zero new information displayed and zero UI surface changes.

**Part A verdict: no violations.**

---

## Step 2 — Information Architecture check

The UI surface map confirms:
- 0 new pages or routes
- 0 modified components
- No navigation changes
- The Studies nav entry remains disabled (the `/studies` page still lands with J-60)

The diff file list (`apps/backend/app/config.py`, `apps/backend/app/engine/features.py`, `runs/.../state/blueprint.md`, `runs/.../telemetry.jsonl`) contains no frontend files, no router changes, no nav changes.

The blueprint's iter-17 build-out note (appended to `blueprint.md` in the diff) explicitly states "no skeleton change, no UI change." The IA skeleton — `Cockpit / Journal / Studies` top bar — is untouched.

**Part B verdict: no violations.**

---

## Step 3 — Advisory observations

None. This is a pure internal backend optimization with byte-identical outputs, no new surfaces, and no formatting or label changes.

---

## Summary

All three objective checks from the invocation context pass:

(a) **Contract values byte-identical, single owner unchanged.** `bid_refresh_score` and `ask_refresh_score` (row 2) remain computed exclusively by `FeatureEngine` in `features.py`; the new `_RefreshSide` structure is an internal implementation detail of the same single owner, not a separate computation path. `_refresh_fractions()` is retained as the standalone-API authoritative path. No second owner, no second endpoint, no non-canonical source.

(b) **`dense_replay_time_budget_seconds` correctly excluded from `config_fingerprint`.** The key appears in the `excluded` set at `apps/backend/app/config.py:654` with documented rationale, and the spec requires a stability test + counter-test to be present in the new test file.

(c) **No new IA surface.** Zero new routes, zero nav changes, Studies entry stays disabled.
