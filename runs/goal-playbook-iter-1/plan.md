# goal-playbook-iter-1 Execution Plan

Era B2 "The Playbook", target journey **J-01** ("The signal contract — opening-range breaks,
lookahead-clean and pre-registered"), required-still-passing **J-10**. Depth: **full** (per the
phase spec's Full-trigger-1 and the iter-0 evaluator's binding recommendation — J-01 stands up the
whole signal-contract architecture every later playbook journey depends on).

Verified against the current tree (HEAD `43eb6c8`, clean, `apps/` diff empty) before writing this
plan: no `desk_playbook*` file exists anywhere under `apps/backend/app/research/` (grep + find both
zero matches), and every anchor the phase spec cites resolves at the exact line it claims —
`desk_forward.py` `DESK_FORWARD_BASELINE_SEED` :138, `forward_parameters()` :225, `_session_slice`
:295, `compute_forward_input_signature` :362, `_draw_anchor_indices` :428, `_measure_from` :451,
`ForwardStore` :802; `desk_sessions.py` `recorded_session_dates` :129, `refuse_if_not_a_session`
:180; `levels.py` `_swing_pivots` :325; `desk_routes.py` `get_forward_store` :412; `bars.py`
`merged_bars` :883; `config.py` `config_fingerprint` :1351. No drift between `docs/goal.md`'s J-01
text, `docs/playbook-detector-spec.md`, and the phase spec's IN SCOPE list — all three agree.

## What to Build

- **`desk_playbook_features.py`** — the spec §2 eight primitives, each attributed in a comment to
  its precedent: `rth_session_slice` (→ `desk_forward._session_slice`), `opening_range` (1m→15min
  window, honest 1m→5m degrade when fewer than 10 of the first 15 one-minute bars are on file, null
  when neither basis exists), `baselines` (MBR + per-slot RVOL-denominator medians over the prior 20
  sessions — the only baseline builder), `swing_pivots` (→ `levels._swing_pivots` strict-extreme /
  ties-are-not-pivots / confirmation-delay rule), `consolidation_range`, `vertical_move`,
  `zone_touches` (→ `desk_forward._touch_scan`), `market_context` (SPY-based, null+reason when no
  SPY bars). Nothing else in this module.
- **`desk_playbook_detect.py`** — `open_high_break` / `open_low_break` (spec §3.1–3.2) emitting the
  spec §0 signal shape. Module docstring carries the T-2 third-setup-vocabulary disclaimer. Must
  never import `setups.py` or `backtests.py`.
- **`desk_playbook.py`** — spec §1 constants verbatim (BOOK/ADAPTATION tags on each), the
  `PLAYBOOK_REGISTER` descriptive-copy sentence, `playbook_parameters()` (call-time reads, mirrors
  `forward_parameters()`), `compute_playbook_input_signature()` (sorted `(symbol, timeframe,
  series_id, checksum)` tuples for members ∪ `{SPY}` × `("1m","5m")` + `config_fingerprint` +
  parameters-blob `sha256[:16]`, metadata-only), `PlaybookStore` (2-pin append-only keyed
  `(session_date, playbook_input_signature)`; id = pure function of the key; checksum-verified load;
  duplicate-key raises; corrupt file surfaced loudly, never overwritten; **no update or delete
  method exists on the class**; versions counted), `compute_playbook(session_date)` (detection-only
  this iteration — walks members, calls `refuse_if_not_a_session` first, records per-symbol absences
  as disclosed rows never crashes), `resolve_desk_playbook_dir` (env-var-or-sibling default
  `TAPEOLOGY_DESK_PLAYBOOK_DIR`, mirrors `resolve_desk_forward_dir`, zero new `Config` field).
- **`desk_routes.py`**: `GET /research/desk/playbook` (`?date=`, `?id=` verbatim reads; honest-empty
  200 payload `{"playbooks": [], "latest": null}` when nothing recorded — never a 404, the
  `desk_forward`/`desk_screen` convention) + a `get_playbook_store` dependency mirroring
  `get_forward_store` (:412). This is the ONLY change to this shared file.
- **Generic lookahead property test** — parametrized over (detector × fixture × signal):
  `detect(bars[:trigger_index+1])` reproduces the identical signal; mutating any bar strictly after
  the trigger index changes nothing. Write it so J-04/J-05/J-06 extend it later by adding fixtures
  only, not by touching its body.
- **Fixtures** (built inline in test code via the `test_desk_forward.py` `_bar`/`_plant` convention —
  no new fixture-file infrastructure under `tests/fixtures/`): one canonical `open_high_break` firing
  session (hand-computed trigger/invalidation/geometry), one near-miss (OR wider than
  `PLAYBOOK_NARROW_OR_MAX_MBR·MBR` — must NOT fire), one 5m-basis opening-range degradation session,
  one ambiguous-outside-bar session (bar strictly breaks both OR sides, neither side previously
  broken).
- **Monkeypatch counter-test** — patching a spec constant moves both `playbook_parameters()`'s blob
  and `compute_playbook_input_signature()`'s output, and the next compute records a NEW version
  rather than raising a duplicate-key error (the `forward_parameters` liveness-test precedent).

## Agents Required

- developer: yes -- backend-only implementation of the four items above (new modules
  `desk_playbook_features.py` / `desk_playbook_detect.py` / `desk_playbook.py`, the one route +
  dependency in `desk_routes.py`, TDD: write TC-1..TC-16 first) plus the dev handoff. No
  frontend-ux work this iteration — `apps/frontend/` is untouched (Frontend Present: no; the `/desk`
  Playbook Signals section is J-03).

## Frontend Present
no

## Files to Create/Modify

New:
- `apps/backend/app/research/desk_playbook_features.py`
- `apps/backend/app/research/desk_playbook_detect.py`
- `apps/backend/app/research/desk_playbook.py`
- `apps/backend/tests/test_desk_playbook_features.py` (primitives, incl. `opening_range`'s 1m→5m
  degrade + null case, `baselines`' `MBR=0`/thin-baseline case, `swing_pivots`' parity with
  `levels._swing_pivots`, `market_context`'s no-SPY-bars null case)
- `apps/backend/tests/test_desk_playbook_detect.py` (fixture goldens for both detectors: canonical,
  near-miss, degraded basis, ambiguous outside bar; the generic lookahead property test lives here
  or in its own `test_desk_playbook_lookahead.py` — developer's call, but keep it structurally
  separable so J-04/J-05/J-06 extend it by fixtures only)
- `apps/backend/tests/test_desk_playbook.py` (`playbook_parameters()` liveness/monkeypatch,
  `compute_playbook_input_signature` hashing, `PlaybookStore` discipline, `compute_playbook`
  session-refusal + absence rows, the `GET /research/desk/playbook` route incl. `?date=`/`?id=` —
  mirrors how `test_desk_forward.py` colocates route tests with its module's tests)

Modify:
- `apps/backend/app/research/desk_routes.py` (add the one route + `get_playbook_store` dependency
  only — no other change)

Deliverable (not source):
- `docs/handoffs/goal-playbook-iter-1-dev.md` (dev handoff, required by DoD)

Do NOT touch: `desk_forward.py`, `desk_screen*.py`, `setups.py`, `bars.py`, `levels.py` (read/import
only — TC-13 asserts zero `git diff` against these); `apps/frontend/**` (no UI this iteration);
`runs/goal-session-playbook/state/blueprint.md` (already registers the "Playbook records" row with
the correct owner/endpoint — no edit needed, per the spec's own NOTES); no new `Config` field.

## Key Test Scenarios

(Full test-first contract is TC-1..TC-16 in the phase spec — this is the load-bearing subset.)

- Honest-empty: no record anywhere → `GET /research/desk/playbook` is HTTP 200 with `playbooks: []`,
  `latest: null` — never 404 (TC-1).
- Canonical fixture fires exactly one `open_high_break` with hand-computed `trigger_price ==
  or_high`, `invalidation_price == or_low - 0.30*(or_high - or_low)`, `side == "long"` (TC-2); the
  wide-OR near-miss fires zero signals (TC-3); the thin-1m fixture builds the OR from the first three
  5m bars and tags `opening_range_basis == "5m"` (TC-4); the both-sides-break fixture records no
  signal plus an `ambiguous_outside_bar` diagnostic (TC-5).
- Lookahead property test: `detect(bars[:trigger_index+1])` reproduces the identical signal;
  mutating any post-trigger bar changes nothing (TC-6).
- Non-session date → `desk_sessions.non_session_refusal`'s sentence, no record written (TC-7).
  Thin-baseline / `MBR=0` symbol-session → a disclosed `absences` row, zero signals for that symbol
  (TC-8).
- Duplicate `(session_date, playbook_input_signature)` write → `PlaybookStore.record()` raises, and
  the original file's SHA-256 is unchanged before/after the failed call (TC-9). Monkeypatched
  constant → both `playbook_parameters()` and `compute_playbook_input_signature()` change, and the
  re-run records a NEW file/id rather than raising (TC-10). Corrupt `file_checksum` → an integrity
  error naming the file, disk untouched (TC-11).
- `?date=D` and `?id=<id>` both verbatim-match the stored record field-for-field (TC-12).
- Full suite ≥ 1926 pass / 8 skip, `Config().config_fingerprint()` == `08e471b10130e1e2`, `git diff`
  empty against `desk_forward.py`/`desk_screen*.py`/`setups.py`/`bars.py` (TC-13).
- J-10 regression: replay the stored golden script
  `runs/goal-session-playbook/journey-scripts/J-10.json` (do not extend or rewrite it — no UI
  changed this iteration) — every step's assertion still matches (TC-14). This is an automated
  replay, not a new interactive browser-QA pass; Frontend Present: no means no NEW browser checks are
  required for J-01 itself, but the existing J-10 script must still be replayed to prove zero
  regression.
- Structural: neither `desk_playbook.py` nor `desk_playbook_detect.py` imports `setups.py`/
  `backtests.py`; no served signal field is named `stop_loss` (the field is `invalidation_price`)
  (TC-15). `PLAYBOOK_REGISTER` passes `test_copy_discipline.find_violations` with zero violations —
  import it the same way `test_desk_forward.py:59` does (TC-16).

## Notes for reviewer / QA / auditor

- Out of scope this iteration (do not let it creep in): measurement/forward returns/
  `invalidation_breached`/seeded baselines (J-02); the compute manager, CLI, run ledger, any POST
  trigger route (J-02); the `/desk` Playbook Signals UI (J-03); JBE/DBI/cup-and-handle/capitulation/
  euphoria/range-trade/double-top-bottom detectors (J-04/J-05/J-06); the back-scan (J-07); the
  evidence view (J-08); the two new MCP tools — MCP stays at 18 (J-09); any `Config` field or
  fingerprint-epoch change.
- If `open_high_break`/`open_low_break` turn out unimplementable as written from
  `docs/playbook-detector-spec.md` §3.1–3.2, the developer drops the detector and records the drop
  for an owner ruling — never improvises a threshold (T-1).
- Environment: this pipeline run isolates temp files — before running pytest or anything that writes
  temp files, `export TMPDIR="/home/dennis-chan/.cache/iad/iad.goal-playbook-iter-1.1205778"
  TMP="/home/dennis-chan/.cache/iad/iad.goal-playbook-iter-1.1205778"
  TEMP="/home/dennis-chan/.cache/iad/iad.goal-playbook-iter-1.1205778"`.
