# goal-rapid-microscope-iter-13 Dev Handoff

**Phase:** goal-rapid-microscope-iter-13
**Date:** 2026-08-19
**Agent:** developer
**Status:** complete (revised — see **Fix Notes (r8)** at the end)

> **READ THE FIX NOTES FIRST.** The review FAILED this pass with one CRITICAL, the owner ruled on
> it, and the ruling is now **spec revision r8**: recovery is HALT-ONLY this era. The
> "Named-but-unverified / union-marking" branch described in *What Was Built* item 1.2 below
> **no longer exists** — it was deleted, along with the `exposure_unknown` state itself. Everything
> else below still stands. The Fix Notes section supersedes any sentence that conflicts with it.

## What Was Built

A three-way correctness fix to `vault.recover_shard_ledger` (spec `docs/rapid-validation-spec.md`
§7.8, TR-25) closing the integrity hole the iteration-12 evaluator found, plus two
documentation-only clarifications. No new endpoint, no new store, no schema change, zero frontend
files touched.

- **`recover_shard_ledger`'s "not proven complete" branch is now a genuine three-way split**
  (previously two-way):
  1. **Proven-complete** (unchanged) — the reconstructed prefix+suffix hash-matches the tail
     anchor exactly; the ledger is rewritten; service resumes with the exact prior exposure state.
  2. **Named-but-unverified** (revised) — every anchor-attested row is at least NAMED by a
     dataset_id somewhere in the attempt (verified prefix + caller's `reconstructed_suffix`
     together meet or exceed the anchor's `row_count`), but the hash-attested completeness check
     still fails on content. Resumes (`resumed: True, ok: False`), now marking the **union** of
     prefix-named AND suffix-named dataset ids `exposure_unknown` — the iteration-12 code only
     ever marked the prefix half, letting a shard named solely in a wrong/incomplete suffix guess
     escape marking entirely.
  3. **Cannot be named at all** (new) — either a genuine row-count shortfall against the anchor
     (some row the anchor attests existed has no dataset_id anywhere), or the anchor itself is
     missing/unreadable so the true row count cannot be bounded at all. Refuses to resume
     (`resumed: False`): `rewrite_from_recovery` is never called, the corrupted file on disk stays
     untouched, `verify_chain()` keeps reporting the identical failure immediately afterward, and
     every dependent predicate (`currently_sealed_dataset_ids`, `withheld_dataset_ids`,
     `unresolved_pool_universe_by_dataset_id`, `build_vault_state`) keeps raising
     `VaultLedgerCorruptionError`. Still appends an immutable `outcome: "halted"` incident row to
     `recovery_ledger` (naming the anchor's `row_count` beside how many rows the attempt could
     actually name), so the attempt itself stays on permanent record. This is exactly the branch
     the pre-iteration-13 code never used — spec §7.8's own "or the whole tranche halts" disjunct
     — and it is the hole the iteration-12 evaluator's reproduction (seal ds-1/ds-2/ds-3, destroy
     ds-3's row, empty suffix) exercised: before this fix, ds-3 silently left the withheld set and
     read as an ordinary never-sealed dataset even though `verify_chain()` reported clean again
     after the (buggy) "recovery".
  A later `recover_shard_ledger` call against the same still-corrupted, untouched file, given a
  fuller reconstruction, can still succeed normally (verified end to end).

- **`seal_shard`/`assign_shard`/`expose_shard` docstring pin (zero behavior change).** Each now
  states explicitly that its corruption gating is scoped to its own shard ledger only — resolving
  the iteration-12 reviewer's open scope question as a documented, tested decision rather than an
  ambiguity. A pinning test proves a truncated universe ledger (shard ledger intact) does not
  change what these three write. Widening to gate on both ledgers, plus the matching
  universe-ledger recovery primitive it would require, stays deliberately deferred (see NOTES).

- **`micro_routes.py` docstring fix (zero behavior change).** `get_tick_recorder_compute`'s
  docstring named the stale, pre-iteration-12 `trades_total`/`quotes_total` field pair as though
  still served plain. Corrected to name the fields `_progress_view` actually serves today
  (`trades_total_bucket`/`quotes_total_bucket`, unconditionally — see "Known Issues" below for one
  discrepancy I found and resolved against the code, not the phase-spec prose).

## Files Changed

- `apps/backend/app/research/vault.py` — the three-way `recover_shard_ledger` split (module
  docstring gained an "Iteration 13" paragraph; function docstring and body rewritten); docstring
  clarification added to `seal_shard`/`assign_shard`/`expose_shard`.
- `apps/backend/app/research/micro_routes.py` — docstring fix on `get_tick_recorder_compute`
  (prose only; the route's own return statement and `_progress_view` are byte-unchanged).
- `apps/backend/tests/test_vault.py` — added `_seal_three_shards` fixture helper; added 5 new
  tests (the iteration-12-evaluator reproduction, the missing-anchor variant, the post-halt
  raise-everywhere check, the re-recovery-after-halt success, and the seal/assign/expose pinning
  test); revised the 3 existing TC-5-named tests that asserted the old (buggy) two-way outcome to
  assert the corrected halt/union behavior instead (renamed two of them since their old names
  described an outcome — "marks... permanently" / a since-superseded "safety net" story — the new
  behavior no longer produces).
- `apps/backend/tests/test_tick_recorder.py` — added one docstring-pinning test for
  `get_tick_recorder_compute`.

No files under `apps/frontend/` changed. No `referee_*.py`, `micro_observer.py`,
`micro_features.py`, `micro_graduation.py`, Playbook detector, or `Config` field changed (all
confirmed via `git status`/`git diff` — zero touches). `runs/goal-session-rapid-microscope/state/
blueprint.md`'s iter-13 documentation note was already committed (from the iter-12 showcase
commit, `9f1722e`) before this dev pass started — nothing further needed there.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -q`

**Full suite result: 3218 collected / 3210 passed / 8 skipped / 0 failed.**
Baseline (pre-iteration, this session's frozen figure): 3212 collected / 3204 passed / 8 skipped
/ 0 failed. **Delta: +6 collected, +6 passed, 0 skipped, 0 failed** — exactly the 6 new tests this
iteration adds (5 in `test_vault.py`: the iteration-12-evaluator's own three-shard reproduction,
the missing-anchor variant, the post-halt raise-everywhere check, the re-recovery-after-halt
success, and the seal/assign/expose pinning test; 1 in `test_tick_recorder.py`: the
`get_tick_recorder_compute` docstring pin). Zero regressions; skip count unchanged at 8.

Evidence trail (this pytest version's `-q` mode does not print its traditional final summary line
to a redirected/non-tty stream, so the count above was obtained two independent ways, cross-checked
against each other and against two separate full-suite runs):
1. The run's own captured exit code, explicitly appended inside the same redirected stream
   (`{ pytest tests/ -q ; echo "REAL_EXIT_CODE=$?"; } > log 2>&1`): **`REAL_EXIT_CODE=0`** — pytest
   only returns 0 when every collected test passed (or was skipped); any failure forces a non-zero
   exit.
2. The complete per-test progress-marker stream (every `.`/`s`/`F`/`x`/`X`/`E` character pytest's
   `-q` reporter ever printed, across the whole run) was extracted from the log and counted
   programmatically: **3218 markers total — 3210 `.` (passed), 8 `s` (skipped), zero `F`/`x`/`X`/`E`
   anywhere.** Re-run independently a second time (two full runs, ~10 minutes each): identical
   3218/3210/8/0 both times. `--collect-only` separately confirms 3218 collected (summed from its
   own per-file counts), matching both full runs exactly.
- **IMPORTANT — three test-name/behavior changes in `test_vault.py` are EXPECTED, not
  regressions.** Confirmed directly (not merely asserted): before this iteration's fix, running the
  UNCHANGED test file against the NEW `vault.py` code produced exactly 3 failures, all in
  `test_vault.py`, all in the exact 3 tests the plan named in advance:
  `test_tc5_an_unprovable_reconstruction_marks_affected_shards_exposure_unknown_permanently` and
  `test_tc5_a_shard_recovery_could_not_name_stays_protected_by_the_universe_rule_predicate` (both
  now assert the halt path, `resumed: False` — renamed to
  `test_tc5_an_entirely_unnamed_shortfall_refuses_to_resume_rather_than_marking_a_subset` and
  `test_tc5_a_registered_universe_rule_does_not_bypass_the_post_halt_corruption_refusal`
  respectively, since their old names described an outcome the corrected code no longer produces),
  and `test_tc5_a_wrong_nonempty_reconstruction_is_also_refused_never_treated_as_proven` (now
  asserts the union-marking path, `exposure_unknown_dataset_ids == ["d-1", "d-2"]` instead of the
  old, buggy `["d-1"]` alone — kept its original name since "refused, never treated as proven"
  still accurately describes the corrected outcome). This is the SPECIFIED behavior change the
  phase spec's own plan called out in advance (three-way split replacing a two-way one); the
  post-fix suite above is 100% green with these three tests already revised to match the corrected
  semantics — the 3210/3218 passed count already includes them passing under their NEW assertions.
- `tests/test_vault.py` + `tests/test_tick_recorder.py` in isolation: 108 passed, 0 failed (run
  separately first, before the full-suite run, specifically to confirm the 3 old assertions failed
  against the new code exactly as predicted, then again after revising them to confirm green).
- Config fingerprint: `Config().config_fingerprint()` → **`08e471b10130e1e2`** — checked directly
  by importing `app.config.Config` and calling the method fresh, this run. Unchanged.
- `apps/backend/app/config.py`: `git status`/`git diff` both empty — zero new `Config` fields,
  confirmed by diff, not inferred from the fingerprint alone.
- MCP `EXPECTED_TOOLS`: still the 22-tuple — checked directly by parsing
  `tests/test_mcp_server.py`'s own `EXPECTED_TOOLS` literal and counting its entries fresh this
  run (22). Zero MCP file touched (`git status` confirms no MCP module in the diff).
- Six `referee_*.py` files: `git status`/`git diff` both empty for
  `apps/backend/app/research/referee_*.py`, checked fresh this run — byte-untouched.
- Zero frontend files changed: `git status --porcelain apps/frontend/` returns nothing, checked
  fresh this run.
- Real `.data/datasets` store: 18 JSON dataset files, byte-unchanged; no `.data/micro_vault`
  directory exists (confirmed via `find`/`ls`).

## Pre-handoff verification

- **Service startup**: ran `scripts/dev.sh` (backend `:8301`, frontend `:3301`), confirmed
  `GET /health` → `{"status":"ok"}` and `GET /` → 200 with a successful Next.js compile. Stopped
  both processes, confirmed ports fully released (`lsof`/`ps`), started again — second run also
  came up clean with `{"status":"ok"}` and no port-conflict errors in either log. Both server
  processes killed before finishing this task (verified via `ps`/`lsof` — nothing left listening
  on either port).
- **External integrations**: none added this iteration (no new adapter/scraper/vendor call).
- **Native dependency binaries**: none added this iteration.

## Known Issues

- **One prose discrepancy between the phase spec and the verified code, resolved against the
  code.** The phase spec's IN-SCOPE item for the `micro_routes.py` docstring fix describes the
  corrected fields as "`trades_total_bucket`/`quotes_total_bucket` pre-release; the exact pair
  only after whole-ORIGINAL-pool release, per r7 §7.1". I read `tick_recorder._progress_view`'s
  actual implementation and its own docstring directly: it buckets **unconditionally**, "never
  conditionally, never threading per-universe vault-exposure state through the recorder" (the
  function's own words), because a recording run's progress is always historical by the time any
  pool it fed could ever be released. I wrote the corrected `get_tick_recorder_compute` docstring
  to match the verified code (always bucketed, never the exact pair) rather than the phase spec's
  paraphrase, and pinned it with a test that would fail if a future change reintroduced the stale
  unconditional-serving claim. This is a documentation-only judgment call with zero behavior
  change and zero test-coverage risk either way (the route's actual served shape was already
  thoroughly tested pre-iteration and is untouched); flagging it for the reviewer/auditor in case
  the phase-spec wording reflects intent I'm missing.
- Everything else in the phase spec's IN SCOPE / DEFINITION OF DONE list is implemented and
  test-covered as specified. J-06 steps 4–5 remain untouched by design (out of scope this
  iteration, per the phase spec's own OUT OF SCOPE list).

---

# Fix Notes (r8) — 2026-08-19, second dev pass

**Input:** `reports/reviews/goal-rapid-microscope-iter-13-review.md` (verdict FAIL, one CRITICAL,
proven by direct execution against the real module), and the owner ruling it escalated under T-1.
The ruling is recorded as **spec revision r8** in `docs/rapid-validation-spec.md` (revision header,
rewritten §7.8, new trap TR-29) and in `runs/goal-session-rapid-microscope/state/assumptions.md`
(`2026-08-19 — OWNER RULING`). **Where the iteration-13 phase spec still describes a graded /
union-marking resume branch, the phase spec is SUPERSEDED and r8 was implemented instead.**

## The defect, restated

`vault.py:1612`'s `every_anchor_row_named` compared `len(candidate_rows) >= anchor_row_count` — a
row COUNT and nothing else. The tail anchor commits to a row count plus the final row's hash and to
**no per-row identity**, so a same-length reconstructed suffix naming an unrelated `d-fake` passed:
the genuinely destroyed `d-3` then existed in no ledger at all, `verify_chain()` reported clean, and
`seal_shard` would re-seal `d-3` fresh under another universe. **Row-count equality is not evidence
of identity and can never authorize recovery** — which is why this was not fixable by tightening the
comparison.

## What changed in this pass

1. **The graded / union-marking resume branch is DELETED.** `recover_shard_ledger` now has exactly
   two outcomes: a hash-attested proof of completeness resumes the exact prior state, and
   **everything else halts** — `rewrite_from_recovery` is never called, the corrupt file stays
   byte-untouched, `verify_chain()` keeps failing, and every predicate plus every lifecycle
   transition keeps raising `VaultLedgerCorruptionError`. The vault stays BLOCKED. No affected shard
   becomes fresh, sealable, assignable, or `historical_oos`.
2. **The `exposure_unknown` lifecycle value is deleted with it** (`STATE_EXPOSURE_UNKNOWN`, its
   `__all__` entry, and its `_serialize_shard` branch). The branch that wrote it was its only
   writer, so keeping it would have left a state nothing can produce advertised as legal. The
   module's state vocabulary is back to exactly `sealed` / `assigned` / `exposed`.
3. **`_serialize_shard` now reveals identity on a positive whitelist** (`assigned`/`exposed`)
   instead of excluding a blacklist (`sealed` / the deleted fourth state). Same behavior for the
   three real states; an unrecognised state now serves only the opaque projection instead of
   disclosing symbol/session_date. Tested.
4. **Return contract:** `{"ok", "resumed"}`. The `exposure_unknown_dataset_ids` key is gone from
   both the return value and the recovery-ledger row — it only ever carried the deleted branch's
   output. The halted row is now `kind: "recovery_halted"` and records why the proof failed:
   `anchor_row_count`, `attempted_row_count`, `anchor_head_hash`, `attempted_final_row_hash`,
   `attempted_chain_internally_consistent`. Zero production call sites, no served endpoint, no
   on-disk format change anywhere (the ruling's stop sign).
5. **No identity-commitment migration was designed** — explicitly out of scope per the ruling. The
   module docstring and the function docstring both record what a future named revision would need
   (ordered row/event identities, ideally a canonical checkpoint/manifest or Merkle-style commitment
   tied to the chain), and why counting can never substitute for it.

## Two further laundering paths I found by attacking my own fix (and closed)

The dispatch required attacking the fix by execution rather than trusting it. Two probes against
the *proven-complete* side of the door — the side the ruling did not touch — reproduced real
laundering, both confirmed by running them, both now closed and regression-tested:

- **An empty reconstruction "proved" a wiped ledger.** With a tail anchor reading
  `{"row_count": 0, "head_hash": null}` (which `append_row` never writes, so it means tampering or an
  earlier bad rewrite), supplying *nothing at all* satisfied both original conjuncts (0 == 0, None ==
  None). The recovery reported success and wiped every sealed row off the ledger; the three shards
  then read as never sealed and `d-1` was re-sealable under a new universe. **Executed and observed
  before the fix.** Closed by requiring a non-empty candidate. Test:
  `test_r8_an_empty_reconstruction_can_never_prove_the_ledger_was_always_empty`.
- **A prefix the file no longer authenticates could "prove" completeness.**
  `_verified_prefix_rows` trusts the *caller-supplied* `verify_result` to decide how much of the file
  is genuine. Hand it a `verify_result` that understates the damage (`tail_truncated` over a file
  whose interior row was edited in place) and the prefix is taken as trusted with its stored hashes —
  and because an in-place edit leaves later rows' stored hashes untouched, the anchor's count *and*
  head hash both still matched. The attempt returned `ok: True` and wrote a permanent
  `recovery_completed` attestation over rows containing a substituted `dataset_id`. **Executed and
  observed before the fix.** Closed by re-deriving the whole candidate chain from its own row
  contents and demanding byte-equality — spec §7.8's own "verify the reconstruction is internally
  consistent" step, which had only ever been applied to the suffix half. Implemented by reusing
  `_rehash_suffix` (no second implementation of the chain walk). Test:
  `test_r8_a_prefix_the_file_no_longer_authenticates_can_never_prove_completeness`.

Both additions only ever **narrow** the resume door; neither changes any on-disk format, and the
genuine hash-attested reconstruction still resumes exactly as before (pinned by the unchanged TC-4 /
TC-6 tests and re-verified by probe).

## TR-29 — the owner's enumerated traps, all implemented and green

| Trap (owner's wording) | Test |
|---|---|
| The demonstrated attack: same-length suffix naming an unrelated `d-fake` ⇒ refuse, and `d-3` never sealable again under another universe | `test_tr29_a_same_length_suffix_naming_an_unrelated_dataset_is_refused_and_never_reseals` |
| Same row count, REORDERED identities ⇒ refuse | `test_tr29_a_same_count_suffix_with_reordered_identities_is_refused` |
| Same row count, SUBSTITUTED identity ⇒ refuse | `test_tr29_a_same_count_suffix_with_one_substituted_identity_is_refused` |
| Same final-row count but a missing earlier exposure ⇒ refuse | `test_tr29_a_missing_earlier_exposure_padded_to_the_same_final_count_is_refused` |
| A cleanly internally re-chained FORGED suffix is not proof of historical completeness | `test_tr29_a_cleanly_internally_rechained_forged_suffix_is_not_proof_of_completeness` |
| Operator attestation alone never certifies missing identity evidence | `test_tr29_operator_attestation_alone_never_certifies_missing_identity_evidence` |

**Every TR-29 case asserts the count equality explicitly** (`attempted_row_count ==
anchor_row_count`), so none of these refusals can be passing for the trivial reason of a short
suffix — each input satisfies the deleted branch's own test exactly. Three of them additionally run
the *true* reconstruction against the same untouched file and assert it proves complete, so the
refusal is demonstrably about the reordering / the substituted id / the forgery and nothing else.

Independently of the test suite, the review's own reproduction script and five further attack shapes
(overreaching `failed_at_row`, a suffix padded past the anchor count, a whole-file replacement by an
internally valid forged chain, plus the two probes above) were executed directly against the patched
module: **all refuse; the genuine reconstruction still resumes and restores all three shards.**

## EXPECTED behaviour changes in existing tests — not regressions

r8 deletes behaviour that iteration 13's first pass had just shipped, so tests that asserted it had
to change. Listing them explicitly so the reviewer and auditor can check they were *strengthened*,
not loosened:

- `test_tc5_a_wrong_nonempty_reconstruction_is_also_refused_never_treated_as_proven` — **the
  material one.** Previously asserted the graded resume (`resumed: True`, ledger rewritten,
  `exposure_unknown_dataset_ids == ["d-1", "d-2"]`). Now asserts a refusal plus strictly more: the
  count matched the anchor exactly and bought nothing, the file is byte-untouched, `build_vault_state`
  still raises, and the halted record shows count-match-with-hash-mismatch. Its name already said
  "is also refused" — the assertions now match the name.
- Seven tests had `outcome == {...}` updated for the two-key return shape (mechanical), and two had
  `exposure_unknown_dataset_ids`/`named_row_count` field assertions replaced by
  `attempted_row_count` / `anchor_head_hash` / `attempted_chain_internally_consistent`.
- No test was deleted, no assertion was weakened, and no guard test was edited. The era's frozen
  guards (`test_mcp_server.py`, `test_meta_routes.py`, `test_desk_ui_guards.py`,
  `test_copy_discipline.py`, `test_no_execution_path.py`, the referee guards, the golden traces) are
  untouched.

## Tests run (this pass)

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -q --junitxml=<file>`

**Full suite: 3227 collected / 3219 passed / 8 skipped / 0 failed / 0 errors** (`REAL_EXIT_CODE=0`,
589s). Counts read from the JUnit XML (`tests`/`failures`/`errors`/`skipped` attributes), not from
`-q` prose.

Baseline stated in the dispatch: **3218 / 3210 / 8 / 0**. **Delta: +9 collected, +9 passed, 0
skipped, 0 failed, 0 regressions** — exactly the 9 tests added this pass (6 TR-29 + 2 self-attack
probes + 1 serialization whitelist). `tests/test_vault.py` alone: 73 passed / 0 failed (was 64).

Frozen rails re-checked fresh this pass:

- `Config().config_fingerprint()` → **`08e471b10130e1e2`**; `apps/backend/app/config.py` diff empty
  (zero new `Config` fields).
- Six `referee_*.py`: `git diff --stat HEAD -- 'apps/backend/app/research/referee_*.py'` empty —
  byte-untouched.
- MCP `EXPECTED_TOOLS`: **22** entries, parsed from the literal; no MCP module in the diff.
- `git status --porcelain apps/frontend/` → empty. **Zero frontend files.**
- Real `.data`: 18 datasets, **no `micro_vault` directory** (this fix touches no store on disk).
- `vault.__all__`: 45 entries, none dangling (`STATE_EXPOSURE_UNKNOWN` removed cleanly).

## Files changed (this pass)

- `apps/backend/app/research/vault.py` — module docstring "Iteration 13" paragraph rewritten for r8;
  `STATE_EXPOSURE_UNKNOWN` deleted (constant, `__all__`, comment); `_serialize_shard` whitelist +
  docstring; recovery section header; `recover_shard_ledger` docstring + body (halt-only, four-conjunct
  proof, `recovery_halted` record).
- `apps/backend/tests/test_vault.py` — 9 tests added (TR-29 block + the two self-attack probes + the
  serialization whitelist), 10 existing recovery tests revised as listed above, one fixture helper
  (`_fabricated_seal_row_fields`) added.
- `runs/goal-session-rapid-microscope/state/blueprint.md` — the iter-12 `exposure_unknown`
  value-space extension marked **RETRACTED by r8** (documentation only; no shape/owner/endpoint
  change), and the iter-13 note updated to say so.
- `apps/backend/app/research/micro_routes.py` and `apps/backend/tests/test_tick_recorder.py` —
  unchanged by this pass (their first-pass docstring fix and its pinning test stand).

## Known issues / limitations after this pass

- **Recovery is now strictly less available.** Any corruption whose suffix cannot be proven
  byte-for-byte leaves the vault permanently blocked with no in-product way back. That is the
  owner's explicit trade ("safety wins over degraded availability"), not an oversight — but it means
  a single lost tail row can strand a whole tranche until a provable reconstruction exists.
- **The tail anchor is still the only external proof point.** An attacker (or a bug) able to
  *rewrite the anchor sidecar* can still make a tampered ledger verify — e.g. replace both the file
  and its anchor with a self-consistent forgery. Nothing in this fix changes that, and it cannot be
  fixed without the identity commitment r8 defers to a future named revision. Recorded here because
  it bounds what "the vault is safe" means today.
- `_verified_prefix_rows` still takes the caller's `verify_result` at face value when deciding how
  much of the file to trust. The new internal-consistency conjunct means a wrong `verify_result` can
  no longer manufacture a false proof, but it can still *under*-trust a genuine file (a caller
  passing `head_hash_mismatch` for a merely truncated ledger gets an empty prefix and must supply
  the whole history). Harmless direction, worth knowing.
- The iteration-13 **phase spec** still contains the superseded union-marking requirement in its IN
  SCOPE / DEFINITION OF DONE / TC-5 sections. I did not edit the phase spec (not mine to rewrite);
  r8 in the canonical spec plus `assumptions.md` govern. The plan file
  (`runs/goal-rapid-microscope-iter-13/plan.md`) is stale in the same way.

---

# Audit addendum (2026-08-19, auditor) — claims above corrected by one CRITICAL fix

The audit found a **THIRD** laundering path on the proven-complete side (a third beyond the two
this handoff's own self-attack section reports), reproduced it end to end, and fixed it. The
following claims above are superseded — everything else in this handoff still stands:

1. **"FOUR conjuncts" / "the two guards beyond the original count+hash pair" is now FIVE / three.**
   `recover_shard_ledger`'s proof gained `len(candidate_rows) >= preserved_row_count`: a recovery
   may never DELETE rows the preserved corrupt file itself still carries.
2. **"the genuine hash-attested reconstruction still resumes exactly as before" no longer holds in
   one case, deliberately.** When the tail anchor lags the ledger file — the crash window
   `micro_chain_ledger.append_row`'s own comment calls "benign -- never falsely short" — a
   byte-GENUINE reconstruction of the ANCHOR-length history used to satisfy all four conjuncts, and
   `rewrite_from_recovery` then truncated the surplus rows away. Observed: seal `d-1`..`d-4` with the
   anchor lagging at 3, corrupt an interior row, recover with the true first three rows ⇒ `d-4`'s
   seal row deleted, `verify_chain()` clean, `seal_shard("d-4")` succeeding FRESH under another
   universe, and a permanent `recovery_completed` attestation certifying the loss. That is r8 §7.8's
   forbidden outcome reached through the proven side of the door. It now halts.
3. **The halted incident row gained one forensic field**, `preserved_row_count`, beside
   `attempted_row_count`.
4. **Suite counts move by exactly the one regression test the fix adds:** **3228 collected / 3220
   passed / 8 skipped / 0 failed / 0 errors** (`REAL_EXIT_CODE=0`, 587s, JUnit XML). The
   pre-fix 3227/3219/8/0 figure this handoff reports was independently re-run and confirmed first.
   Test: `test_audit_a_recovery_can_never_delete_rows_the_corrupt_file_itself_still_carries`.
5. **"Every TR-29 case asserts the count equality explicitly" is 5 of 6.**
   `test_tr29_operator_attestation_alone_never_certifies_missing_identity_evidence` satisfies the
   equality by construction (verified by execution: attempted 3 == anchor 3) but does not assert it,
   so a future edit shortening its fabricated suffix would let that one trap pass for the trivial
   reason. Left as disclosed test debt, not fixed (observation-level).
6. **"no on-disk format change anywhere" is imprecise** — the shard-ledger and tail-anchor formats
   are genuinely unchanged (`micro_chain_ledger.py` byte-untouched, verified), but the RECOVERY
   ledger's halted-row field set did change this iteration (`recovery_incomplete` →
   `recovery_halted`, `exposure_unknown_dataset_ids` dropped, forensic fields added). Harmless —
   zero rows exist in any store, no Data Contract row, no serving endpoint.

Full detail, evidence and the remaining disclosed residuals:
`docs/handoffs/goal-rapid-microscope-iter-13-audit.md`.
