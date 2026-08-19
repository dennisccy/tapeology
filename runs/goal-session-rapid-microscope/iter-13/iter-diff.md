# Iteration diff (bounded)

Files changed: 6. Shown in full: 4.

**Truncated** (over the line caps; tail omitted, noted inline or fully skipped):
- `apps/backend/app/research/vault.py` (8 lines not shown)
- `apps/backend/tests/test_vault.py` (520 lines not shown)

```diff
diff --git a/apps/backend/app/research/micro_routes.py b/apps/backend/app/research/micro_routes.py
index 07c9f8b..9fa438c 100644
--- a/apps/backend/app/research/micro_routes.py
+++ b/apps/backend/app/research/micro_routes.py
@@ -488,8 +488,14 @@ def get_tick_recorder_compute(
     Aggregate-only, at every point during a run (spec section 7.1, r5, era iteration 11):
     ``progress`` never carries a symbol, a date, a dataset id, or any other per-chunk field --
     ``chunks_total``/``chunks_done``/``chunks_fetched``/``chunks_reused``/``chunks_unchanged``/
-    ``chunks_failed``/``trades_total``/``quotes_total``/``percent_complete``/``elapsed_seconds``
-    only. ``manager.snapshot()`` already projects it that way
+    ``chunks_failed``/``trades_total_bucket``/``quotes_total_bucket``/``percent_complete``/
+    ``elapsed_seconds`` only -- never the exact ``trades_total``/``quotes_total`` counts
+    (TR-28/spec section 7.1, r7, iteration 12: bucketed UNCONDITIONALLY, since a one-symbol-day
+    run's "aggregate" exact total would itself be that withheld shard's exact count; see
+    ``tick_recorder._progress_view``'s own docstring for why this never varies with vault-release
+    state -- recording strictly PRECEDES any possible exposure, so a run this progress surface
+    describes is already historical by the time any pool it fed could ever be released).
+    ``manager.snapshot()`` already projects it that way
     (``tick_recorder._copy_recorder_snapshot``/``_progress_view``, an explicit whitelist), so this
     route forwards it VERBATIM -- no second computation, and deliberately no operator-only bypass
     parameter, header, or role claim on this route (r5: using one would itself be a human exposure
diff --git a/apps/backend/app/research/vault.py b/apps/backend/app/research/vault.py
index 84502ab..b665532 100644
--- a/apps/backend/app/research/vault.py
+++ b/apps/backend/app/research/vault.py
@@ -212,7 +212,40 @@ this dataset withheld".
    Deliberately scoped to THIS predicate alone -- ``expected_recording_pairs``/
    ``verify_recording_batch`` (TR-4's cherry-pick check) keep their own byte-exact matching
    unchanged, since the phase spec names only "the universe-rule test" inside this one function, not
-   a broader normalization of the recording-batch verifier."""
+   a broader normalization of the recording-batch verifier.
+
+**Iteration 13 -- spec revision r8: recovery is HALT-ONLY this era.** (Owner ruling of
+2026-08-19, recorded in ``docs/rapid-validation-spec.md``'s r8 revision header, its rewritten
+section 7.8, and trap TR-29; and in ``state/assumptions.md``'s ``2026-08-19 -- OWNER RULING``
+entry.) Iteration 12 shipped a GRADED recovery: a reconstruction that could not be PROVEN
+complete still resumed service, marking the dataset ids it could name ``exposure_unknown``.
+Iteration 13's first pass NARROWED that branch -- resume only when the attempt named at least as
+many rows as the anchor attested -- rather than removing it, and the iteration-13 review then
+disproved the whole design by execution. The tail anchor commits to a row
+COUNT plus the final row's hash and to NO per-row identity, so a SAME-LENGTH suffix naming an
+unrelated dataset satisfied every check the graded branch was able to make: the genuinely
+destroyed shard then existed in no ledger at all, ``verify_chain()`` reported clean, and
+``seal_shard`` would re-seal it FRESH under another universe -- the exact "unknown exposure
+history read as never exposed" outcome section 7.8 forbids. **Row-count equality is not evidence
+of identity and must NEVER authorize recovery.**
+
+r8 therefore DELETES the graded branch outright. ``recover_shard_ledger`` below resumes ONLY on a
+hash-attested proof of completeness; in EVERY other case it refuses -- leaving the corrupt file
+byte-untouched and every vault predicate fail-closed -- no matter how much the operator attests.
+The ``exposure_unknown`` lifecycle value is deleted with it: its only writer was that branch, and
+its only purpose was to make a partially-known ledger servable, which is precisely what r8
+forbids. No affected shard becomes fresh, sealable, assignable or ``historical_oos`` merely
+because some reconstructed ledger would verify internally; if completeness cannot be proven, the
+affected vault/tranche stays BLOCKED. Graded recovery returns only under a FUTURE named revision
+built on a real identity commitment -- at minimum ordered row/event identities, preferably a
+canonical checkpoint/manifest or Merkle-style commitment tied to the chain -- and that migration
+is explicitly NOT designed here. The owner's governing sentence, which every branch below
+implements literally: **for this era, safety wins over degraded availability -- unknown or
+unprovable exposure history means the vault is unavailable, never "fresh".**
+
+The SAME diff also pins, as a documented and tested decision rather than an open reviewer
+question, that ``seal_shard``/``assign_shard``/``expose_shard`` gate on their own shard ledger
+only (see each function's own docstring, and ``state/assumptions.md``'s iter-13 second entry)."""
 
 from __future__ import annotations
 
@@ -234,7 +267,6 @@ __all__ = [
     "STATE_SEALED",
     "STATE_ASSIGNED",
     "STATE_EXPOSED",
-    "STATE_EXPOSURE_UNKNOWN",
     "VaultUniverseNotRegisteredError",
     "VaultUniverseAlreadyRegisteredError",
     "CherryPickedBatchError",
@@ -296,21 +328,19 @@ SURROGATE_SHARD_ID_PREFIX = "vshard-"
 _SURROGATE_LABEL = "vault-shard-surrogate-v1:"
 _CHECKSUM_COMMITMENT_LABEL = "vault-checksum-commitment-v1:"
 
-# The one-way lifecycle's three states (module docstring T-2: this module's OWN vocabulary,
-# distinct from micro_readiness.py's EXPOSURE_STATE_EXPLORATORY/SPLIT_PROVENANCE_HAND_ASSIGNED).
+# The one-way lifecycle's three states -- the WHOLE vocabulary, there is no fourth (module
+# docstring T-2: this module's OWN vocabulary, distinct from micro_readiness.py's
+# EXPOSURE_STATE_EXPLORATORY/SPLIT_PROVENANCE_HAND_ASSIGNED).
+#
+# Iteration 12 added a fourth, `exposure_unknown`, as the graded-recovery downgrade target;
+# spec revision r8 (2026-08-19, module docstring's own "Iteration 13" paragraph) DELETED both the
+# branch that wrote it and the value itself. A vault whose exposure history cannot be PROVEN is
+# unavailable -- never partially servable under a "we are not sure about this shard" state, which
+# is exactly the degraded availability the owner traded away for safety.
 STATE_SEALED = "sealed"
 STATE_ASSIGNED = "assigned"
 STATE_EXPOSED = "exposed"
 
-# Iteration 12 (spec section 7.8, TR-25): the FOURTH, terminal lifecycle value -- never reachable
-# through seal_shard/assign_shard/expose_shard, written ONLY by recover_shard_ledger below when a
-# corrupted ledger's missing suffix cannot be proven complete. Matches neither STATE_SEALED nor
-# STATE_ASSIGNED, so the existing lifecycle guards in assign_shard/expose_shard already refuse any
-# further transition for a shard in this state with no new guard code (their own `actual_state !=
-# expected_state` checks do the job) -- "permanently ineligible for sealed-OOS use" falls out of
-# the existing single-shot machinery for free.
-STATE_EXPOSURE_UNKNOWN = "exposure_unknown"
-
 # The universe rule's two serving stages (module docstring's join-resistance part 4). A DIFFERENT
 # vocabulary from the shard lifecycle above on purpose: a universe has no lifecycle of its own --
 # its rule's disclosure is a pure function of whether every shard it owns has reached `exposed`.
@@ -906,7 +936,21 @@ def seal_shard(
     id, silently voiding r3's entire join-resistance guarantee at the one moment it is supposed to
     take effect. Checked at the door rather than trusted from the caller, because ``seal_shard``
     takes raw bytes and a future operator act could hand it something other than
-    ``load_vault_secret``'s already-validated return."""
+    ``load_vault_secret``'s already-validated return.
+
+    **Corruption gating covers this function's own shard ledger only (iteration 13) -- a
+    deliberate scope, not an oversight (TC-7 pins this).** ``seal_shard``/``assign_shard``/
+    ``expose_shard`` read and write ONLY ``VaultShardLedger`` (via ``_latest_shard_row``'s own
+    gated ``verified_rows()``); none of the three ever reads the universe ledger, even though a
+    ``universe_id`` is stored on every row -- it is recorded verbatim, never looked up, so a
+    corrupted UNIVERSE ledger cannot corrupt what these three write. Widening the gate to also
+    require a sound universe ledger stays deferred until a matching universe-ledger recovery
+    primitive exists to pair with it (module docstring's own "Iteration 12" paragraph, point 1's
+    disclosed interpretation call, and ``state/assumptions.md``'s iter-13 second entry have the
+    full reasoning): these three functions have zero production call sites today, so widening buys
+    no real-world safety yet, while it would force updating roughly 81 unrelated test call sites
+    across ten files and introduce a new halt-with-no-recovery-path failure mode the moment the
+    universe ledger alone became corrupted."""
     if not vault_secret.strip():
         raise VaultSecretUnavailable(
             "seal_shard was handed an empty vault secret -- refused (spec section 7.5 r3): an "
@@ -951,7 +995,10 @@ def assign_shard(
     ``symbol``/``session_date`` -- and, per r3, the surrogate -> ``dataset_id`` mapping -- for the
     first time (TC-7). Refused (``ShardLifecycleOrderError``, TR-12) unless the shard's own latest
     row is currently ``sealed`` -- covers BOTH "never sealed" and "already assigned/exposed"
-    (module docstring's shard-global single-shot reading, TC-8)."""
+    (module docstring's shard-global single-shot reading, TC-8).
+
+    **Corruption gating covers this function's own shard ledger only (iteration 13) -- see
+    ``seal_shard``'s own docstring for the full reasoning.**"""
     latest = _latest_shard_row(ledger, dataset_id)
     actual_state = latest["exposure_state"] if latest is not None else None
     if actual_state != STATE_SEALED:
@@ -977,7 +1024,10 @@ def expose_shard(
     ``checksum_commitment`` can be re-derived from it and verified (r3 point 2). Refused
     (``ShardLifecycleOrderError``, TR-12) unless the shard's own latest row is currently
     ``assigned`` for THIS ``family_root_id`` -- covers "never assigned", "already exposed", and
-    "assigned to a different family" alike."""
+    "assigned to a different family" alike.
+
+    **Corruption gating covers this function's own shard ledger only (iteration 13) -- see
+    ``seal_shard``'s own docstring for the full reasoning.**"""
     latest = _latest_shard_row(ledger, dataset_id)
     actual_state = latest["exposure_state"] if latest is not None else None
     if actual_state != STATE_ASSIGNED or latest.get("family_root_id") != family_root_id:
@@ -1181,19 +1231,18 @@ def _serialize_shard(row: dict) -> dict:
       the surrogate -> ``dataset_id`` mapping (r3 point 1: revealed at assignment). TC-7.
     * ``exposed``  -- the above PLUS the raw ``content_checksum``, against which the salted
       commitment can now be re-derived and verified (r3 point 2).
-    * ``exposure_unknown`` (iteration 12, TR-25/TC-5) -- a lawful-recovery downgrade, never a
-      lifecycle transition of its own. Serves whatever the shard's LAST KNOWN row already
-      disclosed and nothing more: still-opaque if recovery marked it unknown while it was only
-      ever ``sealed`` (``row["symbol"]`` is ``None``), else the ``assigned``-shape fields -- but
-      NEVER ``content_checksum``, since ``exposure_unknown`` never equals ``STATE_EXPOSED`` and
-      so the same ``if state == STATE_EXPOSED`` guard below already excludes it. This is the ONE
-      place ``exposure_unknown``'s "permanently ineligible for sealed-OOS use" requirement is
-      enforced at the SERVING layer; the lifecycle layer enforces it for free (module docstring
-      next to ``STATE_EXPOSURE_UNKNOWN``'s own definition: no further transition can ever match
-      a state that is neither ``sealed`` nor ``assigned``)."""
+
+    The reveal test is a POSITIVE whitelist of the two states that provably earned disclosure
+    (``assigned``, ``exposed``), not a blacklist of ``sealed`` -- so ``sealed`` and ANY value
+    outside this module's three-state vocabulary alike serve only the opaque projection.
+    Iteration 12 wrote the test the other way round (reveal unless ``sealed`` or the since-deleted
+    ``exposure_unknown``), which would have disclosed symbol/date for any unrecognised state; r8
+    (module docstring) removed the fourth state, and the whitelist form makes the serving layer
+    fail CLOSED on an unrecognised one rather than depending on the exhaustiveness of a
+    blacklist."""
     opaque = {key: row[key] for key in _OPAQUE_SHARD_KEYS}
     state = row["exposure_state"]
-    if state == STATE_SEALED or (state == STATE_EXPOSURE_UNKNOWN and row.get("symbol") is None):
+    if state not in (STATE_ASSIGNED, STATE_EXPOSED):
         return opaque
     revealed = {
         **opaque,
@@ -1349,17 +1398,16 @@ def build_vault_state(shard_ledger: VaultShardLedger, universe_ledger: VaultUniv
     }
 
 
-# === iteration 12: lawful recovery -- fail closed, recover only on evidence (spec section 7.8) =====
+# === lawful recovery -- fail closed, recover only on PROOF (spec section 7.8, r8) ==================
 #
-# The ONLY way back from a `VaultLedgerCorruptionError` (module docstring's own iteration-12
-# paragraph). Scoped to the SHARD ledger, where the concrete `exposure_unknown` terminal state
-# lives (a disclosed scope choice, T-1): TC-4/TC-5's own language and the Data Contract's
-# `exposure_unknown` value are both shard-specific, and the universe ledger has no analogous
-# partial-recovery state to downgrade into. The shared low-level pieces below
-# (`preserve_corrupt_ledger`, `_verified_prefix_rows`, `_rehash_suffix`) are generic over EITHER
-# wrapper class, so a hypothetical `reconstruct`-only (TC-4-shape, no TC-5-shape partial mark) path
-# for the universe ledger could reuse them unchanged if a future iteration needs it -- not built
-# here because nothing in this iteration's own test-first contract exercises it.
+# The ONLY way back from a `VaultLedgerCorruptionError`, and since r8 (module docstring's own
+# "Iteration 13" paragraph) it is a single, all-or-nothing door: a hash-attested proof of
+# completeness resumes exact prior service, and everything else halts. Scoped to the SHARD ledger
+# (a disclosed scope choice, T-1) because that is the ledger whose corruption can make a shard look
+# fresh; the shared low-level pieces below (`preserve_corrupt_ledger`, `_verified_prefix_rows`,
+# `_rehash_suffix`) are generic over EITHER wrapper class, so an equivalent universe-ledger door
+# could reuse them unchanged if a future iteration needs one -- not built here because nothing in
+# this iteration's own test-first contract exercises it.
 
 
 def preserve_corrupt_ledger(ledger, quarantine_dir: str, *, incident_id: str) -> dict:
@@ -1457,53 +1505,128 @@ def recover_shard_ledger(
     quarantine_dir: str,
     recovered_at: str | None = None,
 ) -> dict:
-    """spec section 7.8's full lawful-recovery sequence for the SHARD ledger (the one ledger with
-    a defined ``exposure_unknown`` terminal state -- module section note above). Steps, in order:
+    """spec section 7.8's full lawful-recovery sequence for the SHARD ledger. **Halt-only since
+    spec revision r8** (2026-08-19 owner ruling; module docstring's own "Iteration 13" paragraph):
+    exactly TWO outcomes, divided by a byte-for-byte PROOF -- never a row count, never a shape,
+    never the operator's word.
+
+    Steps, in order:
 
     1. Preserve the corrupt ledger byte-for-byte (``preserve_corrupt_ledger``) -- forensic
        evidence, independent of whatever happens next. Also reads the ledger's OWN currently
-       committed tail anchor (``read_tail_anchor``) -- untouched by a content-only corruption in
-       the TC-1/TC-2/TC-3 scenarios -- as the hash-attested target step 3 below tests against.
+       committed tail anchor (``read_tail_anchor``) -- untouched by a content-only corruption --
+       as the hash-attested target step 3 below tests against.
     2. Identify the last verified row (``_verified_prefix_rows``).
     3. Re-chain the caller's ``reconstructed_suffix`` onto that prefix EXACTLY the way
        ``HashChainedLedger.append_row`` would (``_rehash_suffix``) and test whether the result is
-       HASH-ATTESTED COMPLETE: its final row's hash equals the anchor's own ``head_hash`` and the
-       total row count equals the anchor's own ``row_count`` -- a byte-for-byte proof, never the
-       operator's word (module docstring: "operator attestation is audit metadata, never proof of
-       missing history").
-    4a. PROVEN COMPLETE (TC-4): the reconstructed prefix+suffix becomes the ledger's new content
-        (``VaultShardLedger.rewrite_from_recovery`` -- the ONE lawful whole-file rewrite this
-        module ever performs, and only here, only after the corrupt original is already
-        preserved); a ``recovery_completed`` row (citing every hash, source, operator identity and
-        reason) is appended to ``recovery_ledger``; returns ``{"ok": True, "resumed": True,
-        "exposure_unknown_dataset_ids": []}``. Predicates read this ledger normally again from
-        this point on, reporting the EXACT prior exposure state (TC-4).
-    4b. NOT proven -- missing or wrong suffix, a hash/row-count mismatch, or none supplied at all
-        (TC-5): refuses to truncate-and-continue. The ledger's new content is the verified prefix
-        PLUS one ``exposure_unknown`` row per DISTINCT ``dataset_id`` the prefix ever named --
-        conservative, since the lost suffix could have advanced ANY of them past what the prefix
-        last saw, and TR-25's own invariant forbids ever resolving that uncertainty in a shard's
-        favour. A ``recovery_incomplete`` row (naming the gap) is still appended to
-        ``recovery_ledger``; returns ``{"ok": False, "resumed": True,
-        "exposure_unknown_dataset_ids": [...]}``. Every affected shard is now permanently
-        ineligible for sealed-OOS use -- TR-12's own single-shot guards already refuse any further
-        ``assign_shard``/``expose_shard`` call for a shard whose state is not EXACTLY what those
-        transitions expect, so ``exposure_unknown`` (matching neither ``sealed`` nor ``assigned``)
-        is refused there automatically; no new lifecycle guard code is needed (``STATE_EXPOSURE_
-        UNKNOWN``'s own definition above).
-
-    Either branch RESUMES service (``resumed: True``): a corrupted ledger does not stay refused
-    forever once a lawful recovery -- proven or conservatively incomplete -- has run; only an
-    UNATTEMPTED recovery leaves ``VaultLedgerCorruptionError`` firing on every read."""
+       HASH-ATTESTED COMPLETE -- FIVE conjuncts, every one required and none sufficient alone:
+       the candidate is non-empty, its row count equals the anchor's own ``row_count``, its final
+       row's hash equals the anchor's own ``head_hash``, the whole candidate chain is internally
+       consistent when re-derived from its own row contents, and it accounts for at least as many
+       rows as the preserved corrupt file itself still carries (a recovery may never DELETE
+       preserved evidence). The three guards beyond the original count+hash pair each close a
+       laundering path found by attacking this function directly; the inline comments at the check
+       itself carry all three reproductions. See also the r8 note below on why the count conjunct
+       can never be promoted into a dividing line of its own.
+    4. Two outcomes, and only two:
+
+       a. **PROVEN COMPLETE -> resume exactly.** The reconstructed prefix+suffix becomes the
+          ledger's new content (``VaultShardLedger.rewrite_from_recovery`` -- the ONE lawful
+          whole-file rewrite this module ever performs, and only here, only after the corrupt
+          original is already preserved); a ``recovery_completed`` row (citing every hash, source,
+          operator identity and reason) is appended to ``recovery_ledger``; returns ``{"ok": True,
+          "resumed": True}``. Predicates read this ledger normally again from this point on,
+          reporting the EXACT prior exposure state -- no shard's history is guessed at, because
+          the reconstruction reproduced the committed head hash bit for bit.
+       b. **ANYTHING ELSE -> HALT.** A missing, truncated, tampered, wrong, reordered, padded or
+          merely unproven suffix -- and equally a missing or unreadable anchor
+          (``read_tail_anchor()`` returned ``None``, so no independent proof of the true history
+          exists to test against AT ALL) -- all land here. ``rewrite_from_recovery`` is NEVER
+          called: the corrupted file on disk stays byte-untouched, ``verify_chain()`` keeps
+          reporting exactly the same failure immediately afterward, and every dependent predicate
+          (``currently_sealed_dataset_ids``, ``withheld_dataset_ids``,
+          ``unresolved_pool_universe_by_dataset_id``, ``build_vault_state``, and the
+          ``seal_shard``/``assign_shard``/``expose_shard`` transitions, all gated through
+          ``verified_rows()``) keeps raising ``VaultLedgerCorruptionError``. The affected vault
+          stays BLOCKED -- no shard of it becomes fresh, sealable, assignable or ``historical_oos``
+          on the strength of an unproven story about its own history. An immutable incident row
+          (``outcome: "halted"``, citing the anchor's own ``row_count``/``head_hash`` beside what
+          the attempt actually produced) is still appended to ``recovery_ledger``, so the attempt
+          is on permanent record even though nothing about the shard ledger changed. Returns
+          ``{"ok": False, "resumed": False}``. A LATER call against the SAME still-corrupted file,
+          given a genuinely provable reconstruction, still succeeds normally -- a halt never
+          consumes or alters the original corrupted ledger.
+
+    **Why there is no third, "graded" branch (r8, and TR-29 keeps it deleted).** Iteration 12 had
+    one, and iteration 13's first pass narrowed it instead of removing it: if the attempt merely
+    NAMED as many rows as the anchor attested, it resumed with the named dataset ids marked
+    ``exposure_unknown``. The iteration-13 review broke that by execution --
+    seal ``d-1``/``d-2``/``d-3``, destroy ``d-3``'s row, hand this function a SAME-LENGTH suffix
+    naming an unrelated ``d-fake``, and ``d-3`` vanished from every ledger while ``verify_chain()``
+    reported clean and ``seal_shard`` would re-seal it fresh under another universe. The defect is
+    not fixable by tightening that comparison, because the tail anchor commits to a row COUNT plus
+    the final row's hash and to NO per-row identity: **counting can never prove identity.** A
+    future named revision may reintroduce graded recovery once the ledger carries a real identity
+    commitment (at minimum ordered row/event identities, preferably a canonical checkpoint or
+    Merkle-style manifest tied to the chain) -- deliberately NOT designed here, and no on-disk
+    format changes in this fix.
+
+    ``sources``/``operator_identity``/``reason`` are recorded as audit metadata on every outcome
+    and are read by NO decision this function makes: operator attestation can never substitute for
+    missing identity evidence (spec section 7.8), so no value of any of them can turn a halt into a
+    resume. Only the hashes decide."""
     preserved = preserve_corrupt_ledger(shard_ledger, quarantine_dir, incident_id=incident_id)
     anchor = shard_ledger.read_tail_anchor() or {}
+    anchor_row_count = anchor.get("row_count")
     good_prefix = _verified_prefix_rows(shard_ledger, verify_result)
+    preserved_row_count = len(shard_ledger.all_rows())
     candidate_suffix = _rehash_suffix(good_prefix, reconstructed_suffix)
     candidate_rows = good_prefix + candidate_suffix
     recovered_at = recovered_at if recovered_at is not None else _iso_utc_now()
     final_hash = candidate_rows[-1]["row_hash"] if candidate_rows else None
+
+    # Spec section 7.8's own "verify the reconstruction is internally consistent" step, applied to
+    # the WHOLE candidate ledger rather than the suffix half alone. `_rehash_suffix` already IS the
+    # definition of a valid chain (`HashChainedLedger.append_row`'s algorithm), so re-deriving every
+    # row from its content and demanding byte-equality re-checks each row's own content hash, its
+    # prev_hash link and its row_index in one comparison -- with no second implementation of the
+    # chain walk. It matters because `good_prefix` comes from `_verified_prefix_rows`, which trusts
+    # the CALLER-SUPPLIED `verify_result` to decide how much of the on-disk file is genuine: hand
+    # this function a `verify_result` that understates the damage (say "tail_truncated" over a file
+    # whose interior row was edited in place) and the stored final row hash can still match the
+    # anchor, so the two hash/count conjuncts alone would attest "proven complete" over rows the
+    # file itself no longer authenticates. Verified by execution before this line existed.
+    rederived = _rehash_suffix([], [_row_content(row) for row in candidate_rows])
+    internally_consistent = rederived == candidate_rows
+
+    # `bool(candidate_rows)`: an EMPTY reconstruction can never be a proof. Without it, an anchor
+    # reading `{"row_count": 0, "head_hash": null}` -- which `append_row` never writes, so it means
+    # tampering or an earlier bad rewrite -- is "matched" by supplying nothing at all (0 == 0, None
+    # == None), and the recovery would WIPE the ledger and report success: every sealed shard gone,
+    # re-sealable fresh under any universe. Verified by execution before this guard existed. A
+    # genuinely empty ledger has no lost history to recover and never reaches this function.
+    #
+    # `len(candidate_rows) >= preserved_row_count` (iteration-13 AUDIT): a recovery may never DELETE
+    # rows the corrupt file itself still carries. The anchor is written AFTER the row it commits to
+    # (`micro_chain_ledger.append_row`'s own comment calls the window "benign -- never falsely
+    # short"), so a crash between the two leaves the ledger LONGER than the anchor. In that state a
+    # byte-GENUINE reconstruction of the anchor-length history satisfies the four conjuncts above
+    # while `rewrite_from_recovery` truncates the surplus rows away -- observed end to end: seal
+    # d-1..d-4 with the anchor lagging at 3, corrupt an interior row, recover with the true first
+    # three rows, and d-4's seal row is gone, `verify_chain()` reports clean, `seal_shard` re-seals
+    # d-4 FRESH, and a `recovery_completed` attestation certifies the loss. That is r8 section 7.8's
+    # forbidden outcome ("no affected shard becomes fresh, sealable, assignable ... merely because
+    # the reconstructed ledger now verifies internally") reached through the PROVEN side of the
+    # door. This conjunct is a pure additional REFUSAL -- it can only turn a proof into a halt,
+    # never the reverse -- so it does not resurrect count equality as evidence of anything: it is a
+    # floor against destroying preserved evidence, never an authorization. When it fires the vault
+    # stays BLOCKED, which is r8's own trade (safety over degraded availability).
     proven_complete = (
-        len(candidate_rows) == anchor.get("row_count") and final_hash == anchor.get("head_hash")
+        bool(candidate_rows)
+        and anchor_row_count == len(candidate_rows)
+        and final_hash == anchor.get("head_hash")
+        and internally_consistent
+        and len(candidate_rows) >= preserved_row_count
     )
 
     last_verified_row_index = (len(good_prefix) - 1) if good_prefix else None
@@ -1527,32 +1650,40 @@ def recover_shard_ledger(
                 "outcome": "complete",
             }
         )
-        return {"ok": True, "resumed": True, "exposure_unknown_dataset_ids": []}
-
-    affected_dataset_ids = sorted({row["dataset_id"] for row in good_prefix})
-    latest_by_id: dict[str, dict] = {}
-    for row in good_prefix:
-        latest_by_id[row["dataset_id"]] = row
-    unknown_fields = [
-        {**_row_content(latest_by_id[dataset_id]), "exposure_state": STATE_EXPOSURE_UNKNOWN}
-        for dataset_id in affected_dataset_ids
-    ]
-    unknown_rows = _rehash_suffix(good_prefix, unknown_fields)
-    shard_ledger.rewrite_from_recovery(good_prefix + unknown_rows)
+        return {"ok": True, "resumed": True}
+
+    # NOT PROVEN COMPLETE -> HALT, unconditionally (spec section 7.8 r8; docstring branch 4b). No
+    # secondary test runs here and none may ever be added on the CURRENT anchor schema: the anchor
+    # commits to a row count and the final row's hash only, so nothing available at this point can
+    # distinguish "every truly lost row is accounted for" from "the count was padded with rows that
+    # were never there" -- the exact laundering TR-29 pins. The corrupted file is left alone; the
+    # vault stays blocked; the attempt goes on permanent record and changes nothing else.
     recovery_ledger.append_row(
         {
-            "kind": "recovery_incomplete",
+            "kind": "recovery_halted",
             "ledger_kind": "shard",
             "incident_id": incident_id,
             "corrupt_ledger_sha256": preserved["corrupt_ledger_sha256"],
             "last_verified_row_index": last_verified_row_index,
             "last_verified_row_hash": last_verified_row_hash,
+            # Audit metadata only -- recorded because a halt must say what was attempted, never
+            # read back by any decision above (docstring's closing paragraph).
             "attempted_sources": list(sources),
             "operator_identity": operator_identity,
             "reason": reason,
             "recovered_at": recovered_at,
-            "exposure_unknown_dataset_ids": affected_dataset_ids,
-            "outcome": "incomplete",
+            # Why the proof failed: the two dimensions the anchor actually commits to, plus
+            # whether the candidate chain even hangs together on its own terms.
+            "anchor_row_count": anchor_row_count,
+            "attempted_row_count": len(candidate_rows),
+            # How many rows the preserved corrupt file itself still carried -- an attempt that
+            # accounts for FEWER than this would have destroyed preserved evidence (see the
+            # `preserved_row_count` conjunct above).
+            "preserved_row_count": preserved_row_count,
... [diff_bound] apps/backend/app/research/vault.py: 8 more diff lines omitted — Read the file for full detail
diff --git a/apps/backend/tests/test_tick_recorder.py b/apps/backend/tests/test_tick_recorder.py
index cf0b216..85e2ac2 100644
--- a/apps/backend/tests/test_tick_recorder.py
+++ b/apps/backend/tests/test_tick_recorder.py
@@ -874,6 +874,25 @@ def _assert_progress_is_aggregate_only(progress: dict) -> None:
     assert set(progress.keys()) == _PROGRESS_AGGREGATE_KEYS, sorted(progress.keys())
 
 
+def test_tc8_the_recorder_progress_route_docstring_names_the_bucketed_fields_it_actually_serves():
+    """TC-8 (iteration 13, docstring-only fix -- goal-rapid-microscope-iter-13): the route
+    function's own docstring must name the fields ``_progress_view`` actually serves today
+    (``trades_total_bucket``/``quotes_total_bucket``, TR-28/r7 -- pinned above by
+    ``_assert_progress_is_aggregate_only``) -- never the stale, pre-iteration-12 unconditional
+    ``trades_total``/``quotes_total`` pair as though it were still served plain."""
+    from app.research.micro_routes import get_tick_recorder_compute
+
+    doc = get_tick_recorder_compute.__doc__ or ""
+    assert "trades_total_bucket" in doc
+    assert "quotes_total_bucket" in doc
+    # the OLD, stale field-LIST form -- `chunks_failed` through `percent_complete` listed
+    # back-to-back with the bare (un-bucketed) names in the middle, as though served plain -- must
+    # not appear anywhere in the corrected docstring. (The corrected prose still legitimately
+    # names the bare pair once, elsewhere, to explain that they are NEVER served -- this checks
+    # the specific stale listing shape, not bare mentions of the field names.)
+    assert "``chunks_failed``/``trades_total``/``quotes_total``/``percent_complete``" not in doc
+
+
 def test_tc6_recorder_progress_never_leaks_a_planned_chunks_symbol_date_or_dataset_id(
     route_ctx, monkeypatch
 ):
diff --git a/apps/backend/tests/test_vault.py b/apps/backend/tests/test_vault.py
index 5e9e907..694b7d0 100644
--- a/apps/backend/tests/test_vault.py
+++ b/apps/backend/tests/test_vault.py
@@ -1504,6 +1504,24 @@ def _seal_two_shards(shard_ledger: vault.VaultShardLedger) -> list[dict]:
     return rows
 
 
+def _seal_three_shards(shard_ledger: vault.VaultShardLedger) -> list[dict]:
+    """Three sealed shards (``d-1``, ``d-2``, ``d-3``) -- iteration 13's own fixture, the exact
+    shape of the iteration-12 evaluator's own reproduction (goal-rapid-microscope-iter-13's
+    BACKGROUND): a genuine two-row verified prefix (``d-1``, ``d-2``) in front of a THIRD shard
+    whose own row can be destroyed on its own, entirely unnamed by anything before it."""
+    rows = []
+    for i, (dataset_id, checksum) in enumerate(
+        (("d-1", "a" * 64), ("d-2", "b" * 64), ("d-3", "c" * 64))
+    ):
+        rows.append(
+            vault.seal_shard(
+                shard_ledger, dataset_id=dataset_id, universe_id="u1",
+                content_checksum=checksum, event_count=100 + i, vault_secret=_FIXTURE_SECRET,
+            )
+        )
+    return rows
+
+
 def _truncate_ledger_tail(ledger) -> None:
     """Drops the LAST line of ``ledger``'s own ``.jsonl`` file, leaving its tail anchor
     (``chain_head.json``, UNTOUCHED) still claiming the ORIGINAL row count -- TC-1/TC-3's own
@@ -1616,7 +1634,14 @@ def test_tc3_a_last_known_good_prefix_still_fails_closed_when_the_anchor_proves_
         vault.currently_sealed_dataset_ids(shard_ledger)
 
 
-# --- TC-4/TC-5: lawful recovery -- proven resumes exactly; unprovable marks exposure_unknown ------
+# --- TC-4/TC-5 (iteration 12) -- lawful recovery, HALT-ONLY since spec revision r8 (2026-08-19
+# owner ruling; vault.py's own module docstring, spec section 7.8, TR-29). Exactly two outcomes: a
+# hash-attested proof of completeness resumes the EXACT prior state, and every other input -- empty,
+# short, wrong, reordered, padded to the right length, or unanchored -- refuses to resume at all,
+# leaving the corrupt file untouched and the whole vault blocked. Iteration 12's graded middle
+# branch (resume while marking the named dataset ids `exposure_unknown`) was DELETED by r8 after the
+# iteration-13 review proved it launders identity: row-count equality is not evidence of identity.
+# The tests below assert the refusals; TR-29's own block further down attacks them. -------------
 
 
 def test_tc4_a_hash_attested_reconstruction_resumes_service_and_reports_exact_prior_state(tmp_path):
@@ -1638,7 +1663,7 @@ def test_tc4_a_hash_attested_reconstruction_resumes_service_and_reports_exact_pr
         recovery_ledger=recovery_ledger, incident_id="incident-tc4",
         quarantine_dir=str(tmp_path / "quarantine"),
     )
-    assert outcome == {"ok": True, "resumed": True, "exposure_unknown_dataset_ids": []}
+    assert outcome == {"ok": True, "resumed": True}
 
     # service resumes, reporting the EXACT prior state.
     assert shard_ledger.verify_chain()["ok"] is True
@@ -1659,7 +1684,180 @@ def test_tc4_a_hash_attested_reconstruction_resumes_service_and_reports_exact_pr
     assert quarantined, "no forensic copy of the corrupt ledger was preserved"
 
 
-def test_tc5_an_unprovable_reconstruction_marks_affected_shards_exposure_unknown_permanently(tmp_path):
+# --- iteration 13's own TC-1/TC-2/TC-3/TC-4 (docs/phases/goal-rapid-microscope-iter-13.md): the
+# hole the iteration-12 evaluator found -- a shard entirely unnamed by any recovery attempt must
+# never silently escape marking; it must halt the whole ledger instead. --------------------------
+
+
+def test_tc1_the_iteration_12_reproduction_an_entirely_unnamed_lost_row_refuses_to_resume(tmp_path):
+    """The exact end-to-end reproduction the iteration-12 evaluator ran (goal.md's BACKGROUND):
+    seal d-1/d-2/d-3, destroy d-3's own row (only), attempt recovery with NOTHING to reconstruct
+    it. Before this iteration's fix, this silently resumed -- marking only d-1/d-2 (the surviving
+    verified prefix) exposure_unknown -- letting d-3 escape into looking like an ordinary,
+    never-sealed dataset even though verify_chain() reported clean again afterward. The corrected
+    behavior (r8): nothing here is PROVEN, so recovery refuses to resume at all."""
+    vault_dir = str(tmp_path / "vault")
+    shard_ledger = vault.VaultShardLedger(vault_dir)
+    _seal_three_shards(shard_ledger)
+    assert shard_ledger.read_tail_anchor()["row_count"] == 3
+
+    _truncate_ledger_tail(shard_ledger)  # loses d-3's own seal row; d-1/d-2 remain a genuine prefix
+    verify_result = shard_ledger.verify_chain()
+    assert verify_result["ok"] is False and verify_result["reason"] == "tail_truncated"
+
+    recovery_ledger = vault.VaultRecoveryLedger(vault_dir)
+    outcome = vault.recover_shard_ledger(
+        shard_ledger, verify_result=verify_result, reconstructed_suffix=[],
+        sources=[], operator_identity="test-operator", reason="unit test iter-13 TC-1",
+        recovery_ledger=recovery_ledger, incident_id="incident-iter13-tc1",
+        quarantine_dir=str(tmp_path / "quarantine"),
+    )
+    assert outcome == {"ok": False, "resumed": False}
+
+    # never rewritten -- the corrupted file on disk is exactly as it was before the attempt.
+    assert shard_ledger.verify_chain() == verify_result
+    raw_dataset_ids = [row["dataset_id"] for row in shard_ledger.all_rows()]
+    assert raw_dataset_ids == ["d-1", "d-2"]
+
+    # d-3 appears in NO row anywhere -- not sealed, not "unknown", not anything.
+    recovery_rows = recovery_ledger.all_rows()
+    assert len(recovery_rows) == 1
+    assert recovery_rows[0]["outcome"] == "halted"
+    assert recovery_rows[0]["anchor_row_count"] == 3
+    assert recovery_rows[0]["attempted_row_count"] == 2
+    assert "d-3" not in json.dumps(recovery_rows)
+
+
+def test_tc2_a_missing_tail_anchor_refuses_to_resume_even_with_a_perfect_reconstruction(tmp_path):
+    """iteration-13 TC-2: the ledger's own durable tail-anchor SIDECAR file (not its content rows)
+    is the one thing missing here -- all three rows are still fully present and internally
+    self-consistent on disk. Even so, `recover_shard_ledger` must never call this "proven
+    complete": with no anchor, there is no independent proof of the true history to test the
+    reconstruction against AT ALL, so a HALT is the only lawful outcome -- regardless of how
+    faithful the caller's own reconstructed_suffix happens to be."""
+    vault_dir = str(tmp_path / "vault")
+    shard_ledger = vault.VaultShardLedger(vault_dir)
+    original_rows = _seal_three_shards(shard_ledger)
+    assert shard_ledger.verify_chain()["ok"] is True
+
+    shard_ledger.head_anchor_path.unlink()
+    verify_result = shard_ledger.verify_chain()
+    assert verify_result == {"ok": False, "failed_at_row": None, "reason": "head_anchor_missing"}
+
+    recovery_ledger = vault.VaultRecoveryLedger(vault_dir)
+    # a BYTE-PERFECT full reconstruction, offered as the caller's own reconstructed_suffix -- and
+    # it still cannot save the attempt, because nothing independent of the missing anchor can
+    # prove three rows (not two, not four) is the true count.
+    perfect_suffix = [vault._row_content(row) for row in original_rows]
+    outcome = vault.recover_shard_ledger(
+        shard_ledger, verify_result=verify_result, reconstructed_suffix=perfect_suffix,
+        sources=[{"source": "operator-recall", "sha256": "irrelevant-for-this-test"}],
+        operator_identity="test-operator", reason="unit test iter-13 TC-2",
+        recovery_ledger=recovery_ledger, incident_id="incident-iter13-tc2",
+        quarantine_dir=str(tmp_path / "quarantine"),
+    )
+    assert outcome == {"ok": False, "resumed": False}
+
+    # never rewritten -- still failing the identical way immediately after the attempt.
+    assert shard_ledger.verify_chain() == verify_result
+    recovery_rows = recovery_ledger.all_rows()
+    assert len(recovery_rows) == 1
+    assert recovery_rows[0]["outcome"] == "halted"
+    assert recovery_rows[0]["anchor_row_count"] is None
+    assert recovery_rows[0]["anchor_head_hash"] is None
+
+
+def test_tc3_predicates_keep_raising_after_a_halt_rather_than_omitting_the_unnamed_shard(tmp_path):
+    """TC-3: after TC-1's halt, currently_sealed_dataset_ids/withheld_dataset_ids/
+    unresolved_pool_universe_by_dataset_id/build_vault_state must each raise
+    VaultLedgerCorruptionError -- never silently return a result that simply omits d-3, which is
+    exactly the shape of the iteration-12 hole (a corrupted-but-"clean-looking" ledger)."""
+    vault_dir = str(tmp_path / "vault")
+    shard_ledger = vault.VaultShardLedger(vault_dir)
+    universe_ledger = vault.VaultUniverseLedger(vault_dir)
+    _seal_three_shards(shard_ledger)
+    _truncate_ledger_tail(shard_ledger)
+    verify_result = shard_ledger.verify_chain()
+
+    recovery_ledger = vault.VaultRecoveryLedger(vault_dir)
+    outcome = vault.recover_shard_ledger(
+        shard_ledger, verify_result=verify_result, reconstructed_suffix=[],
+        sources=[], operator_identity="test-operator", reason="unit test iter-13 TC-3",
+        recovery_ledger=recovery_ledger, incident_id="incident-iter13-tc3",
+        quarantine_dir=str(tmp_path / "quarantine"),
+    )
+    assert outcome["resumed"] is False
+
+    with pytest.raises(vault.VaultLedgerCorruptionError):
+        vault.currently_sealed_dataset_ids(shard_ledger)
+    with pytest.raises(vault.VaultLedgerCorruptionError):
+        vault.withheld_dataset_ids(shard_ledger)
+    with pytest.raises(vault.VaultLedgerCorruptionError):
+        vault.unresolved_pool_universe_by_dataset_id(shard_ledger, universe_ledger, [])
+    with pytest.raises(vault.VaultLedgerCorruptionError):
+        vault.build_vault_state(shard_ledger, universe_ledger)
+
+
+def test_tc4_a_later_fuller_reconstruction_still_succeeds_against_the_same_untouched_file(tmp_path):
+    """TC-4: a halt never consumes or destroys the corrupted original -- a SECOND
+    recover_shard_ledger call, this time with a byte-correct reconstruction of the truly lost row,
+    proves complete exactly as the unchanged proven-complete path (TC-6) always has, and the
+    recovery_ledger shows BOTH the earlier halted attempt and the later completed one, on
+    permanent record."""
+    vault_dir = str(tmp_path / "vault")
+    shard_ledger = vault.VaultShardLedger(vault_dir)
+    original_rows = _seal_three_shards(shard_ledger)
+    _truncate_ledger_tail(shard_ledger)
+    verify_result = shard_ledger.verify_chain()
+
+    recovery_ledger = vault.VaultRecoveryLedger(vault_dir)
+    halted = vault.recover_shard_ledger(
+        shard_ledger, verify_result=verify_result, reconstructed_suffix=[],
+        sources=[], operator_identity="test-operator", reason="unit test iter-13 TC-4 (halt)",
+        recovery_ledger=recovery_ledger, incident_id="incident-iter13-tc4-halt",
+        quarantine_dir=str(tmp_path / "quarantine"),
+    )
+    assert halted == {"ok": False, "resumed": False}
+
+    # the SAME still-corrupted ledger, re-verified fresh -- untouched by the halted attempt --
+    # this time with d-3's true lost row supplied faithfully.
+    verify_result_again = shard_ledger.verify_chain()
+    assert verify_result_again == verify_result
+    lost_row_fields = vault._row_content(original_rows[2])
+    completed = vault.recover_shard_ledger(
+        shard_ledger, verify_result=verify_result_again, reconstructed_suffix=[lost_row_fields],
+        sources=[{"source": "test-fixture-recall", "sha256": "irrelevant-for-this-test"}],
+        operator_identity="test-operator", reason="unit test iter-13 TC-4 (complete)",
+        recovery_ledger=recovery_ledger, incident_id="incident-iter13-tc4-complete",
+        quarantine_dir=str(tmp_path / "quarantine"),
+    )
+    assert completed == {"ok": True, "resumed": True}
+
+    assert shard_ledger.verify_chain()["ok"] is True
+    assert vault.currently_sealed_dataset_ids(shard_ledger) == frozenset({"d-1", "d-2", "d-3"})
+    state = vault.build_vault_state(shard_ledger, vault.VaultUniverseLedger(vault_dir))
+    assert {s["shard_id"] for s in state["shards"]} == {r["shard_id"] for r in original_rows}
+
+    recovery_rows = recovery_ledger.all_rows()
+    assert len(recovery_rows) == 2
+    assert recovery_rows[0]["outcome"] == "halted"
+    assert recovery_rows[1]["outcome"] == "complete"
+
+
+# --- iteration 12's own TC-5, revised twice (iteration 13 + spec revision r8): the smaller-scale,
+# two-shard reproductions. An empty suffix halts (below); a wrong suffix that pads the row count to
+# the anchor's own count ALSO halts (further below -- iteration 13 first shipped that case as a
+# graded resume, which is exactly what r8 deleted). -----------------------------------------------
+
+
+def test_tc5_an_entirely_unnamed_shortfall_refuses_to_resume_rather_than_marking_a_subset(tmp_path):
+    """The smaller-scale (two-shard) companion to iteration 13's own TC-1: before this iteration's
+    fix, an entirely-unnamed lost row (nothing in the verified prefix, nothing in an empty
+    reconstructed_suffix) still let the recovery "succeed" by marking ONLY the surviving prefix
+    (d-1) exposure_unknown -- silently dropping d-2 out of every predicate with no trace, while
+    `rewrite_from_recovery` re-healed the tail anchor so `verify_chain()` reported clean again.
+    The corrected behavior: nothing about the lost row is PROVEN, so recovery refuses to resume at
+    all and d-2 can never silently read as "never sealed" (spec section 7.8's own invariant)."""
     vault_dir = str(tmp_path / "vault")
     shard_ledger = vault.VaultShardLedger(vault_dir)
     _seal_two_shards(shard_ledger)
@@ -1674,27 +1872,27 @@ def test_tc5_an_unprovable_reconstruction_marks_affected_shards_exposure_unknown
         recovery_ledger=recovery_ledger, incident_id="incident-tc5",
         quarantine_dir=str(tmp_path / "quarantine"),
     )
-    assert outcome["ok"] is False
-    assert outcome["resumed"] is True
-    assert outcome["exposure_unknown_dataset_ids"] == ["d-1"]  # the ONLY shard the trusted prefix names
+    assert outcome == {"ok": False, "resumed": False}
 
-    # service resumes -- but d-1 (the only shard this ledger could still vouch for) is now
-    # exposure_unknown, never simply "still sealed".
-    assert shard_ledger.verify_chain()["ok"] is True
-    state = vault.build_vault_state(shard_ledger, vault.VaultUniverseLedger(vault_dir))
-    (entry,) = state["shards"]
-    assert entry["exposure_state"] == vault.STATE_EXPOSURE_UNKNOWN
-    assert vault.currently_sealed_dataset_ids(shard_ledger) == frozenset()  # no longer "sealed"
-    assert vault.withheld_dataset_ids(shard_ledger) == frozenset({"d-1"})  # still withheld, though
+    # the ledger is refused, not "recovered incompletely" -- still failing, byte-untouched.
+    assert shard_ledger.verify_chain() == verify_result
+    assert [row["dataset_id"] for row in shard_ledger.all_rows()] == ["d-1"]  # untouched, 1 raw row
 
-    # permanence: no further lifecycle transition can ever claim it again -- the EXISTING
-    # single-shot guards refuse it automatically (module docstring next to STATE_EXPOSURE_UNKNOWN).
-    with pytest.raises(vault.ShardLifecycleOrderError):
+    # every dependent predicate keeps raising -- d-1 is NOT quietly served as "currently sealed"
+    # either, since that would itself misstate a shard whose true post-corruption state is unknown.
+    with pytest.raises(vault.VaultLedgerCorruptionError):
+        vault.currently_sealed_dataset_ids(shard_ledger)
+    with pytest.raises(vault.VaultLedgerCorruptionError):
+        vault.build_vault_state(shard_ledger, vault.VaultUniverseLedger(vault_dir))
+
+    # permanence of the REFUSAL: no lifecycle transition can sneak past it either -- the gated
+    # reader every one of them shares raises before any lifecycle-state check even runs.
+    with pytest.raises(vault.VaultLedgerCorruptionError):
         vault.assign_shard(
             shard_ledger, dataset_id="d-1", family_root_id="root", symbol="PG",
             session_date="2026-06-09",
         )
-    with pytest.raises(vault.ShardLifecycleOrderError):
+    with pytest.raises(vault.VaultLedgerCorruptionError):
         vault.seal_shard(
             shard_ledger, dataset_id="d-1", universe_id="u1", content_checksum="c" * 64,
             event_count=1, vault_secret=_FIXTURE_SECRET,
@@ -1702,19 +1900,29 @@ def test_tc5_an_unprovable_reconstruction_marks_affected_shards_exposure_unknown
 
 
 def test_tc5_a_wrong_nonempty_reconstruction_is_also_refused_never_treated_as_proven(tmp_path):
-    """TC-5's other failure shape: a SUPPLIED but WRONG suffix (not merely an empty one) must
-    ALSO fail the hash-attested completeness check and fall to the same conservative
-    exposure_unknown path -- proving `recover_shard_ledger` actually verifies the reconstruction
-    byte-for-byte rather than trusting that the caller supplied SOMETHING."""
+    """TC-5's other failure shape: a SUPPLIED but WRONG suffix (not merely an empty one), whose row
+    count exactly matches the anchor's own row_count=2.
+
+    **Revised by spec revision r8** (2026-08-19 owner ruling). Iteration 13 first shipped this case
+    as a graded RESUME: because both d-1 and d-2 were named, it rewrote the ledger with the named
+    ids marked `exposure_unknown` and returned `resumed: True`. The owner deleted that branch after
+    the iteration-13 review proved a same-length suffix can name anything at all (TR-29 below), so
+    the assertions here now demand a REFUSAL -- a strictly stronger guarantee than the graded
+    outcome this test used to assert, not a loosened one: the ledger is not rewritten, the vault
+    stays blocked, and no shard is left in a state that says "we are not sure about this one".
+    Also proves `recover_shard_ledger` verifies the reconstruction byte-for-byte rather than
+    trusting that the caller supplied SOMETHING of the right length."""
     vault_dir = str(tmp_path / "vault")
     shard_ledger = vault.VaultShardLedger(vault_dir)
     _seal_two_shards(shard_ledger)
     _truncate_ledger_tail(shard_ledger)  # loses d-2's own seal row
     verify_result = shard_ledger.verify_chain()
+    assert shard_ledger.read_tail_anchor()["row_count"] == 2
 
     recovery_ledger = vault.VaultRecoveryLedger(vault_dir)
-    # a PLAUSIBLE-LOOKING but WRONG guess -- right shape, wrong content (a different checksum than
-    # d-2 actually had) -- never a byte-for-byte match of what was truly lost.
+    # a PLAUSIBLE-LOOKING but WRONG guess -- right shape, right dataset_id, right COUNT, wrong
+    # content (a different checksum than d-2 actually had): never a byte-for-byte match of what
+    # was truly lost.
     wrong_guess = {
         "dataset_id": "d-2", "content_checksum": "f" * 64, "shard_id": "vshard-wrong-guess",
         "universe_id": "u1", "checksum_commitment": "wrong-commitment", "size_bucket": "~10^2",
@@ -1729,33 +1937,33 @@ def test_tc5_a_wrong_nonempty_reconstruction_is_also_refused_never_treated_as_pr
         recovery_ledger=recovery_ledger, incident_id="incident-tc5-wrong",
         quarantine_dir=str(tmp_path / "quarantine"),
     )
-    # refused exactly like the empty-suffix case -- a wrong guess is not "proven complete".
-    assert outcome["ok"] is False
-    assert outcome["exposure_unknown_dataset_ids"] == ["d-1"]  # d-2 still could not be NAMED
-
-    state = vault.build_vault_state(shard_ledger, vault.VaultUniverseLedger(vault_dir))
-    (entry,) = state["shards"]  # the WRONG guess's row was never written -- only d-1 exists
-    assert entry["exposure_state"] == vault.STATE_EXPOSURE_UNKNOWN
-    assert "vshard-wrong-guess" not in json.dumps(state)  # the rejected guess never entered the ledger
+    # the count matched the anchor exactly -- and it bought the attempt nothing (r8).
+    assert outcome == {"ok": False, "resumed": False}
 
-    recovery_rows = recovery_ledger.all_rows()
-    assert recovery_rows[-1]["outcome"] == "incomplete"
+    # the corrupted file is byte-untouched: still one raw row, still failing identically.
+    assert shard_ledger.verify_chain() == verify_result
+    assert [row["dataset_id"] for row in shard_ledger.all_rows()] == ["d-1"]
+    with pytest.raises(vault.VaultLedgerCorruptionError):
+        vault.build_vault_state(shard_ledger, vault.VaultUniverseLedger(vault_dir))
 
-    # the incomplete recovery is on permanent record too.
+    # the halted attempt is on permanent record, saying WHY the proof failed: the count matched,
+    # the hash did not.
     recovery_rows = recovery_ledger.all_rows()
     assert len(recovery_rows) == 1
-    assert recovery_rows[0]["outcome"] == "incomplete"
-    assert recovery_rows[0]["exposure_unknown_dataset_ids"] == ["d-1"]
-
-
-def test_tc5_a_shard_recovery_could_not_name_stays_protected_by_the_universe_rule_predicate(tmp_path):
-    """The other half of TC-5's safety net. ``recover_shard_ledger`` cannot even NAME ``d-2`` --
-    its own seal row was inside the unrecoverable gap -- so it is not among the ``exposure_unknown``
-    ids returned. That does NOT mean ``d-2`` is forgotten: after recovery it carries NO row at all
-    in the shard ledger, which is exactly the "untracked pool member" case
-    ``unresolved_pool_universe_by_dataset_id``'s test (b) already exists for -- if ``d-2`` was
-    recorded under a REGISTERED universe's rule, that predicate independently re-catches it, with
-    no reliance on the shard ledger's own (now-incomplete) memory of it."""
+    assert recovery_rows[0]["outcome"] == "halted"
+    assert recovery_rows[0]["anchor_row_count"] == recovery_rows[0]["attempted_row_count"] == 2
+    assert recovery_rows[0]["attempted_final_row_hash"] != recovery_rows[0]["anchor_head_hash"]
+
+
+def test_tc5_a_registered_universe_rule_does_not_bypass_the_post_halt_corruption_refusal(tmp_path):
+    """The `unresolved_pool_universe_by_dataset_id` predicate reads BOTH ledgers (module
+    docstring) -- this proves its fail-closed check truly runs FIRST, before any universe-rule
+    reasoning, even when a real registered universe's rule would otherwise match the very shard a
+    halted recovery could not name. Before this iteration's fix, a shard the shard ledger's own
+    recovery could not name still fell back on this predicate's universe-rule test as a safety
+    net (`recover_shard_ledger` used to resume, marking only d-1); after the fix, no fallback is
+    ever reached at all, because the corrupted shard ledger refuses to resume in the first place
+    -- a strictly stronger guarantee that makes the old safety net unnecessary."""
     vault_dir = str(tmp_path / "vault")
     shard_ledger = vault.VaultShardLedger(vault_dir)
     universe_ledger = vault.VaultUniverseLedger(vault_dir)
@@ -1775,14 +1983,541 @@ def test_tc5_a_shard_recovery_could_not_name_stays_protected_by_the_universe_rul
         recovery_ledger=recovery_ledger, incident_id="incident-tc5b",
         quarantine_dir=str(tmp_path / "quarantine"),
     )
-    assert outcome["exposure_unknown_dataset_ids"] == ["d-1"]  # d-2 could not even be NAMED
+    assert outcome == {"ok": False, "resumed": False}
 
-    # d-2 (recorded AFTER u1's registration, matching its rule) is still caught -- test (b).
-    withheld = vault.unresolved_pool_universe_by_dataset_id(
-        shard_ledger, universe_ledger,
-        [("d-2", "AAPL", "2026-06-09", "2027-01-01T00:00:00.000000Z")],
+    # d-2 (recorded AFTER u1's registration, matching its rule) would have matched test (b)'s
+    # universe-rule membership check -- but the function never reaches it: the shard ledger's own
+    # corruption check fires first and refuses the whole call.
+    with pytest.raises(vault.VaultLedgerCorruptionError):
+        vault.unresolved_pool_universe_by_dataset_id(
+            shard_ledger, universe_ledger,
+            [("d-2", "AAPL", "2026-06-09", "2027-01-01T00:00:00.000000Z")],
+        )
+
+
+# =====================================================================================================
+# TR-29 (spec revision r8, 2026-08-19 owner ruling -- docs/rapid-validation-spec.md section 9 and
+# the rewritten section 7.8): RECOVERY IS HALT-ONLY. The iteration-13 review proved by execution
+# that the graded branch iteration 13 itself shipped launders identity, because the tail anchor
+# commits to a row COUNT plus the final row's hash and to NO per-row identity. Every trap below
+# hands `recover_shard_ledger` a reconstruction that SATISFIES the deleted branch's own row-count
+# test exactly, and demands a refusal -- so a future edit that reintroduces any count-based
... [diff_bound] apps/backend/tests/test_vault.py: 520 more diff lines omitted — Read the file for full detail
diff --git a/docs/goal.md b/docs/goal.md
index 8faa684..1ac3843 100644
--- a/docs/goal.md
+++ b/docs/goal.md
@@ -154,7 +154,7 @@ items, in that order.**
    `08e471b10130e1e2` every iteration; every `referee_*` module byte-identical to `main` at
    era open (SHA-256 listing recorded at iteration 0 and re-checked); every kept `/`,
    `/structure`, `/desk` behavior browser-verified as shipped.
-2. **No leakage trap fails, ever.** The TR-1…TR-28 suite of
+2. **No leakage trap fails, ever.** The TR-1…TR-29 suite of
    [`docs/rapid-validation-spec.md`](rapid-validation-spec.md) §9 is implemented and green:
    prefix discipline, origin fencing, sealed-shard sweeps, cherry-pick refusal, class-mixing
    refusal, purge exactness, screening calibration, pool invariance, ledger chain integrity,
@@ -164,7 +164,8 @@ items, in that order.**
    TR-20 root-family lineage, TR-21 process-label discipline, TR-22 exposure registry — and
    the r6 traps: TR-23 sealed-verdict ownership, TR-24 lineage confirmation boundary,
    TR-25 vault-ledger integrity, TR-26 depletion revealing-quote availability — and the r7
-   traps: TR-27 nonced rule commitment, TR-28 coarse pre-release volumes.
+   traps: TR-27 nonced rule commitment, TR-28 coarse pre-release volumes, and the r8
+   trap TR-29 halt-only vault recovery.
 3. **Every trial is on the record.** The scout ledger is hash-chained append-only; every
    evaluated variant — every kill, with its closed-vocabulary reason — is a permanent row; the
    union-N denominator is served beside every family; "statistically above null" and
@@ -661,12 +662,13 @@ operator-attended act inside the era.
 
 - **J-10: The kept product stands — traps armed, sentinel green**
   - Steps:
-    1. Land the full TR-1…TR-28 suite (whichever traps did not ship inside J-02…J-07 land
+    1. Land the full TR-1…TR-29 suite (whichever traps did not ship inside J-02…J-07 land
        here — the r2 traps TR-17 availability, TR-18 units, TR-19 preservation, TR-20 root
        lineage, TR-21 process labels, TR-22 exposure registry, and the r6 traps TR-23
        sealed-verdict ownership, TR-24 lineage boundary, TR-25 vault-ledger integrity,
        TR-26 depletion revealing quote, and the r7 traps TR-27 nonced rule commitment,
-       TR-28 coarse pre-release volumes, included) plus the extended
+       TR-28 coarse pre-release volumes, and the r8 trap TR-29 halt-only vault
+       recovery, included) plus the extended
        guard tests (accessor import-ban, micro threshold-sweep ban, copy discipline for micro
        copy, `_PRICE_ARITHMETIC_FIELDS` additions).
     2. Run the deterministic-rerun check (byte-identical snapshot/screen/fold outputs on a
diff --git a/docs/rapid-validation-spec.md b/docs/rapid-validation-spec.md
index 97e6c51..6d427aa 100644
--- a/docs/rapid-validation-spec.md
+++ b/docs/rapid-validation-spec.md
@@ -109,6 +109,22 @@
 > scheme must be differencing-resistant. Rejected in both cases: accepting the residual leak.
 > A third audit finding (B3, the missing `verify_chain()` call) needed no ruling — r6 §7.8 already
 > settled it; the iteration-11 phase spec's claim that it is "an open owner question" is STALE.
+>
+> **Revision r8 (2026-08-19, owner ruling — recovery is halt-only this era).** The iteration-13
+> review PROVED by execution that r6 §7.8's graded resume branch cannot be made safe on the current
+> ledger: the tail anchor stores a row COUNT plus the final row's hash and no per-row identity, so a
+> same-length reconstructed suffix naming an unrelated dataset passes the completeness check —
+> the genuinely destroyed shard then exists in no ledger at all, `verify_chain()` reports clean, and
+> `seal_shard` will re-seal it fresh under another universe as if it had never existed. **Row-count
+> equality is not evidence of identity and must never authorize recovery.** r8 therefore DELETES the
+> union-marking / degraded-resume branch for this era: §7.8 becomes halt-only. Graded recovery
+> returns only under a FUTURE named revision built on a real identity commitment — and that
+> commitment must not be a mere SET of dataset ids: it must preserve enough to prove the exact
+> historical suffix (at minimum ordered row/event identities, preferably a canonical
+> checkpoint/manifest or Merkle-style commitment tied to the ledger chain). That migration is not to
+> be designed ad hoc inside this fix. Owner's governing sentence: **for this era, safety wins over
+> degraded availability — unknown or unprovable exposure history means the vault is unavailable,
+> never "fresh".** Traps → TR-29.
 
 ---
 
@@ -722,9 +738,28 @@ evaluation event is accounted for · write a NEW ledger epoch/recovery record ci
 ledger hash, last verified row + hash, reconstruction sources + hashes, recovered suffix hash,
 operator identity and time, and an explicit recovery reason. Only then may predicates resume.
 
-**If the missing suffix cannot be PROVEN complete, recovery must not truncate to the last verified
-row.** Every shard whose freshness could be affected is conservatively marked `exposure_unknown`
-and is permanently ineligible for sealed-OOS use — or the whole tranche halts.
+**If the missing suffix cannot be PROVEN complete, recovery HALTS — full stop (r8).** The owner
+deleted the graded resume branch after the iteration-13 review proved it unsafe: the tail anchor
+carries a row COUNT and the final row's hash but no per-row identity, so a same-length suffix
+naming an unrelated dataset satisfied the check while the genuinely destroyed shard vanished from
+every ledger, `verify_chain()` reported clean, and `seal_shard` would re-seal it fresh under
+another universe. **Row-count equality is not evidence of identity and must NEVER authorize
+recovery.** Therefore, for this era:
+
+- any missing, truncated, or tampered suffix keeps EVERY vault predicate fail-closed;
+- a reconstructed suffix is accepted ONLY if it can be proven against pre-existing trusted
+  commitments; matching row count alone is never sufficient;
+- operator attestation cannot substitute for missing identity evidence;
+- no affected shard becomes fresh, sealable, assignable, or `historical_oos` merely because the
+  reconstructed ledger now verifies internally;
+- if completeness cannot be proven, the affected vault/tranche stays BLOCKED.
+
+Graded recovery returns only under a FUTURE named revision built on a real identity commitment —
+and that commitment must NOT be a mere SET of dataset ids: it must preserve enough to prove the
+exact historical suffix (at minimum ordered row/event identities, preferably a canonical
+checkpoint/manifest or Merkle-style commitment tied to the ledger chain). That migration is not
+designed ad hoc inside a fix. **Safety wins over degraded availability: unknown or unprovable
+exposure history means the vault is unavailable, never "fresh".**
 
 **Traps.** Truncating the tail ⇒ all exposure predicates fail closed · mutating an interior row ⇒
 fail closed · replacing the ledger with a last-known-good prefix ⇒ still fail closed when a later
@@ -863,7 +898,8 @@ boundary by its `observed_through`.
 | TR-22 exposure registry | A spec registered after a logged serving of its validation window is auto-classed `historical_exposed_diagnostic`; the registry's r2 initialization marks every playbook-corpus and legacy-tick window exposed |
 | TR-23 sealed-verdict ownership (r6 §8.1) | A caller-asserted `passed` boolean is impossible/refused · mutating any evaluation input changes the artifact hash and invalidates the transition · a rule unregistered, or changed after assignment, fails closed · re-running the evaluator on identical inputs yields a byte-identical artifact and verdict · a second sealed evaluation for the same (`family_root_id`, shard) is refused · a failed verdict travels in every later export bundle |
 | TR-24 lineage boundary (r6 §8.2) | A KILLED sibling of the same `family_root_id` with a later `observed_through` than the survivor pushes `proposed_confirmation_boundary` past it (lineage knowledge cannot be laundered through candidate selection) · a deferred feature with `anchor_at < observed_through` moves the boundary by its `observed_through` · the final Referee boundary is never earlier than either the proposed or the registration boundary |
-| TR-25 vault-ledger integrity (r6 §7.8) | Tail truncation ⇒ every exposure predicate fails closed · interior-row mutation ⇒ fails closed · a last-known-good prefix still fails closed when a committed checkpoint proves later history existed · a hash-pinned reconstruction restores the exact prior exposure state · an unverifiable recovery never makes an affected shard fresh again (`exposure_unknown`, permanently sealed-OOS-ineligible) |
+| TR-25 vault-ledger integrity (r6 §7.8) | Tail truncation ⇒ every exposure predicate fails closed · interior-row mutation ⇒ fails closed · a last-known-good prefix still fails closed when a committed checkpoint proves later history existed · a hash-pinned reconstruction restores the exact prior exposure state · an unverifiable recovery never makes an affected shard fresh again — **under r8 that means the recovery is REFUSED and the tranche stays blocked** (the `exposure_unknown` state this row originally named was deleted with r8's graded-resume branch; see TR-29) |
+| TR-29 recovery is halt-only (r8 §7.8) | The demonstrated attack: seal `d-1`/`d-2`/`d-3`, destroy the row containing `d-3`, present a SAME-LENGTH reconstructed suffix containing an unrelated `d-fake` ⇒ recovery REFUSES, and `d-3` never becomes sealable again under another universe · same row count with REORDERED identities ⇒ refuse · same row count with a SUBSTITUTED identity ⇒ refuse · same final-row count but a missing earlier exposure ⇒ refuse · a cleanly internally re-chained forged suffix is NOT proof of historical completeness · operator attestation never substitutes for missing identity evidence |
 | TR-27 nonced rule commitment (r7 §7.2) | One ledger-tracked shard exposed while untracked pool members remain withheld ⇒ rule contents hidden · ALL tracked shards exposed but one untracked ORIGINAL-pool member still withheld ⇒ still hidden · after the final pool member is released ⇒ `symbol_rule` + `date_rule` + nonce reveal and recompute EXACTLY to the registered `rule_commitment` · a plausible-rule dictionary attack against the served commitment cannot verify guesses without the nonce · no other API/UI/MCP surface serves the symbol or date axes pre-release |
 | TR-28 coarse pre-release volumes (r7 §7.1) | A one-symbol-day run while withheld ⇒ no exact trade/quote/byte count appears on ANY surface · a multi-shard pool ⇒ coarse bucket labels only, never rounded numbers · expose one shard and re-query ⇒ the remaining withheld counts cannot be solved exactly from the before/after response pair (differencing resistance) · buckets never narrow as the pool shrinks · the final ORIGINAL-pool member released ⇒ exact totals may be served |
 | TR-26 depletion revealing quote (r6 §3) | Price-change termination: `available_at` equals the first CHANGED-price quote, not the last same-price one · bound termination: `available_at` equals the bound-hitting quote · truncating immediately BEFORE the revealing quote makes the depletion value non-existent/unavailable, and including it makes the value appear deterministically |
```
