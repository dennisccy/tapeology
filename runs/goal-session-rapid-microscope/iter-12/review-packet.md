# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 7. Shown in full: 5.

**Truncated** (over the line caps; tail omitted, noted inline or fully skipped):
- `apps/backend/app/research/vault.py` (510 lines not shown)
- `apps/backend/tests/test_vault.py` (238 lines not shown)

```diff
diff --git a/apps/backend/app/main.py b/apps/backend/app/main.py
index 47a6983..68f2650 100644
--- a/apps/backend/app/main.py
+++ b/apps/backend/app/main.py
@@ -49,6 +49,7 @@ from .research.routes import (
     set_registry,
 )
 from .research.store import JournalStore
+from .research.vault import VaultLedgerCorruptionError
 from .serializers import (
     serialize_events,
     serialize_features,
@@ -232,6 +233,23 @@ async def _real_data_error_handler(_, exc: RealDataError) -> JSONResponse:
     return JSONResponse(status_code=exc.status_code, content=content)
 
 
+@app.exception_handler(VaultLedgerCorruptionError)
+async def _vault_ledger_corruption_handler(_, exc: VaultLedgerCorruptionError) -> JSONResponse:
+    # TR-25/spec section 7.8: a GLOBAL handler (the RealDataError precedent above), so every
+    # route this exception can reach -- not merely vault.py's own GET /vault -- gets a single,
+    # clear, non-500 refusal, without a route-by-route try/except audit. 503: a data-integrity
+    # incident the operator must resolve through lawful recovery (vault.recover_shard_ledger),
+    # never a client request error and never a silent 200. The body states which ledger and why,
+    # never a stack trace -- the same "typed refusal, no internals leaked" discipline every other
+    # vault refusal in this codebase already follows (SealedShardWithheldError's own precedent).
+    content = {
+        "detail": str(exc),
+        "ledger_kind": exc.ledger_kind,
+        "verify_chain": exc.verify_result,
+    }
+    return JSONResponse(status_code=503, content=content)
+
+
 def _engine_or_404(ticker: str):
     engine = manager.get(ticker)
     if engine is None:
diff --git a/apps/backend/app/research/micro_chain_ledger.py b/apps/backend/app/research/micro_chain_ledger.py
index d214e31..1c61bf5 100644
--- a/apps/backend/app/research/micro_chain_ledger.py
+++ b/apps/backend/app/research/micro_chain_ledger.py
@@ -70,6 +70,49 @@ class HashChainedLedger:
     def path(self) -> Path:
         return self._path
 
+    @property
+    def head_anchor_path(self) -> Path:
+        """PUBLIC accessor for the durable tail-anchor sidecar's own path -- additive (era
+        iteration 12) for lawful-recovery tooling (``vault.py``'s TR-25/spec section 7.8
+        primitive), which must preserve the anchor file byte-for-byte alongside the main chain
+        file BEFORE any repair. Never used by this class's own methods, which already resolve
+        ``self._head_path`` directly."""
+        return self._head_path
+
+    def read_tail_anchor(self) -> dict | None:
+        """PUBLIC accessor for the tail anchor's own parsed content -- additive (era iteration
+        12), for lawful-recovery tooling that must read the anchor INDEPENDENTLY of a broken
+        main-chain walk (``verify_chain()`` itself only ever reports pass/fail, never the
+        anchor's own raw content). Returns ``None`` when no anchor has ever been written (a
+        pristine, never-appended ledger) -- the exact same case ``verify_chain()``'s own
+        ``_verify_tail`` already treats as trivially OK."""
+        return self._read_head_anchor()
+
+    def rewrite_from_recovery(self, rows: list[dict]) -> None:
+        """The ONE lawful whole-file rewrite this primitive ever performs -- exclusively for a
+        caller's own audited, evidenced lawful-recovery flow (this class's callers -- ``vault.
+        py``'s TR-25 primitive today -- are responsible for preserving the corrupt original
+        BYTE-FOR-BYTE and recording the recovery event on a SEPARATE ledger BEFORE ever calling
+        this; see that module's own ``recover_shard_ledger``). Writes ``rows`` (already
+        hash-chained content -- e.g. a caller-side re-derivation of THIS class's own
+        ``append_row`` algorithm, so a faithful reconstruction reproduces byte-identical hashes
+        to whatever was lost) as the ledger's entire new content, then regenerates the tail
+        anchor to match, so a subsequent ``verify_chain()`` call sees a clean, complete chain.
+        Additive: no existing caller of this class (``ExposureRegistry``, ``WalkForwardLedger``)
+        calls this method, so their own behaviour is untouched."""
+        self._root.mkdir(parents=True, exist_ok=True)
+        with self._path.open("w", encoding="utf-8") as fh:
+            for row in rows:
+                fh.write(json.dumps(row, sort_keys=True))
+                fh.write("\n")
+        self._head_path.write_text(
+            json.dumps(
+                {"row_count": len(rows), "head_hash": rows[-1]["row_hash"] if rows else None},
+                sort_keys=True,
+            ),
+            encoding="utf-8",
+        )
+
     def _read_raw(self) -> list[dict]:
         """Every row, append order, parsed but NOT chain-verified -- ``verify_chain()`` is the
         explicit tamper check; a caller just wanting the data reads this (or ``all_rows``)
diff --git a/apps/backend/app/research/micro_routes.py b/apps/backend/app/research/micro_routes.py
index 459d527..07c9f8b 100644
--- a/apps/backend/app/research/micro_routes.py
+++ b/apps/backend/app/research/micro_routes.py
@@ -540,11 +540,13 @@ def get_vault(vault_dir: str = Depends(get_vault_dir)) -> dict:
     """Serves ``vault.py``'s own state verbatim (``vault.build_vault_state`` -- no second
     computation in this handler): every shard's CURRENT lifecycle state (opaque-only while
     ``sealed``, full symbol/date/family provenance from ``assigned`` onward -- section 7.5, TR-2),
-    every registered universe (never the raw secret, only its commitment -- and, while any of that
-    universe's shards is still withheld, only its ``rule_hash``/sizes rather than the
-    ``symbol_rule``/``date_rule`` LISTS, since those minus the public dataset listing would spell
-    out the sealed tranche by subtraction: iter-9 audit third pass, ``vault._serialize_universe``),
-    and both ledgers' own chain-verification verdicts. Never 404/500 on an empty vault -- the desk
+    every registered universe (never the raw secret, only its commitment -- and, while any member
+    of that universe's ORIGINAL registered pool is still unresolved, only the NONCED
+    ``rule_commitment``/sizes rather than the ``symbol_rule``/``date_rule`` LISTS or the nonce
+    itself, since those minus the public dataset listing would spell out the sealed tranche by
+    subtraction: iter-9 audit third pass, widened iteration 12/r7 TR-27,
+    ``vault._serialize_universe``), and both ledgers' own chain-verification verdicts. Never
+    404/500 on an empty vault -- the desk
     router's established never-404-on-absence convention: an honest empty ``shards``/``universes``
     before any universe is ever registered (registration is a step-4, operator-attended act, out of THIS iteration's
     scope)."""
@@ -573,7 +575,20 @@ def get_graduation(graduation_dir: str = Depends(get_micro_graduation_dir)) -> d
     Design Direction example) accompanies the empty ``families`` list at HTTP 200, never a
     fabricated row. Page-load GETs never compute (T-8): J-07 is keyless/automated -- a candidate's
     state is recorded by calling ``micro_graduation.py``'s evaluation functions directly (a test
-    today; a future J-08/J-09 wiring act later), never by this route."""
+    today; a future J-08/J-09 wiring act later), never by this route.
+
+    **Why this route has no golden REPLAY script (iteration 12, TC-15).** J-07 has no frontend
+    page this iteration (J-08's unbuilt scope), so its only browser-verifiable surface is this
+    RAW backend JSON URL, visited directly (``http://<backend-host>:<port>/research/desk/micro/
+    graduation``). The deterministic replay runner's own ``normalize_url`` (``incredible_auto_
+    dev/scripts/automation/lib/demo_runner.py``) FORCIBLY rewrites any localhost absolute URL onto
+    the run's single frontend ``base_url`` host:port -- there is no per-step override in the
+    replay schema -- so a golden script cannot express "navigate to the backend origin" at all; it
+    would silently 404 against the frontend instead. This is therefore genuinely infeasible, not
+    merely unbuilt: the gap is disclosed at ``runs/goal-session-rapid-microscope/state/golden-
+    gaps`` (``J-07``) rather than left to silently disappear, and this surface is re-verified each
+    iteration through the LLM browser-qa lane instead (iteration-10's own ``UT-J-07`` precedent:
+    navigate the browser directly to the backend URL, read the extracted body text)."""
     ledger = GraduationLedger(graduation_dir)
     families = list_graduation_families(ledger)
     return {
diff --git a/apps/backend/app/research/tick_recorder.py b/apps/backend/app/research/tick_recorder.py
index d960f5f..f017867 100644
--- a/apps/backend/app/research/tick_recorder.py
+++ b/apps/backend/app/research/tick_recorder.py
@@ -628,11 +628,55 @@ def _iso_utc_now() -> str:
 # whitelist (the `vault._serialize_shard` discipline, mirrored) that never spreads `progress`
 # itself into a response, so this internal field can never leak by accident. `trades_total`/
 # `quotes_total` are genuine RUNNING TOTALS (era iteration 11, spec section 7.1) accumulated
-# incrementally by `_publish` below -- never derived from a per-chunk count stored anywhere.
+# incrementally by `_publish` below -- never derived from a per-chunk count stored anywhere. They
+# stay EXACT here, internally: only `_progress_view`'s own SERVED projection buckets them
+# (iteration 12, TR-28/r7) -- so a future surface that legitimately needs the exact running total
+# (e.g. the terminal run-log row, untouched this iteration) never has to re-derive it.
 _IDLE_PROGRESS: dict = {
     "chunks_total": 0, "chunks_done": 0, "outcomes": [], "trades_total": 0, "quotes_total": 0,
 }
 
+# TR-28/spec section 7.1 (r7, iteration 12): the frozen, predeclared coarse bucket scheme
+# `_progress_view` serves in place of an exact `trades_total`/`quotes_total`. Broad powers-of-ten
+# ranges, carrying the LABEL rather than a rounded number (`"1M-10M"`, never `3842117` and never
+# `~3800000`) -- deliberately WIDE (each band spans a full order of magnitude or more) so a
+# one-symbol-day run's true count is never pinned down to something a reader could treat as
+# "close enough to exact". A module constant per this era's own parameters discipline (never a
+# `Config` field) -- frozen at authoring, never tuned from any observed run's actual volumes.
+_VOLUME_BUCKETS: tuple[tuple[int, int | None, str], ...] = (
+    (0, 0, "0"),
+    (1, 999, "1-999"),
+    (1_000, 9_999, "1K-10K"),
+    (10_000, 99_999, "10K-100K"),
+    (100_000, 999_999, "100K-1M"),
+    (1_000_000, 9_999_999, "1M-10M"),
+    (10_000_000, 99_999_999, "10M-100M"),
+    (100_000_000, 999_999_999, "100M-1B"),
+    (1_000_000_000, None, "1B+"),
+)
+
+
+def _volume_bucket(count: int) -> str:
+    """The deterministic, order-preserving map from an exact running total to its frozen coarse
+    label (`_VOLUME_BUCKETS` above) -- TR-28's differencing-resistance by construction:
+
+    * never a per-shard count while withheld -- the bucket is the ONLY thing this function can
+      ever return, for any input, so there is no code path that serves the raw `count` at all;
+    * never an exact delta between successive snapshots -- two calls a moment apart yield either
+      the SAME label or the next one up, never a number a reader could subtract;
+    * buckets never narrow as a pool shrinks -- the scheme is a FIXED partition of all possible
+      counts, not something parameterized by pool size, so it cannot narrow under any input; and
+    * monotonic -- a strictly larger `count` never maps to a strictly smaller bucket, so the
+      SEQUENCE of labels served over a run's own lifetime is itself never informative beyond "the
+      true count crossed into a wider band", never how far past the boundary it sits."""
+    if count <= 0:
+        return _VOLUME_BUCKETS[0][2]
+    for low, high, label in _VOLUME_BUCKETS[1:]:
+        if high is None or count <= high:
+            return label
+    return _VOLUME_BUCKETS[-1][2]  # unreachable (the last band's high is None) -- belt and braces
+
+
 _IDLE_RECORDER_SNAPSHOT: dict = {
     "run_id": None,
     "state": "idle",
@@ -671,7 +715,22 @@ def _progress_view(progress: dict, *, started_utc: str | None, finished_utc: str
     ``vault._serialize_shard`` discipline, mirrored) -- ``progress`` still carries an internal
     ``outcomes`` list (see ``_IDLE_PROGRESS``'s own docstring), so a blind spread would re-leak it.
     ``percent_complete``/``elapsed_seconds`` are DERIVED here, never stored on ``progress`` itself,
-    since ``elapsed_seconds`` must reflect "now" for a still-running job."""
+    since ``elapsed_seconds`` must reflect "now" for a still-running job.
+
+    **TR-28/spec section 7.1 (r7, iteration 12): ``trades_total``/``quotes_total`` are GONE from
+    this projection, replaced by ``trades_total_bucket``/``quotes_total_bucket`` (``_volume_
+    bucket`` above).** The iteration-11 audit proved the contradiction this closes: on a
+    one-symbol-day run, the "aggregate" exact total WAS that withheld shard's exact count. This
+    surface ALWAYS buckets -- never conditionally, never threading per-universe vault-exposure
+    state through the recorder -- because recording strictly PRECEDES any possible exposure in
+    the one-way ``sealed -> assigned -> exposed`` lifecycle (``vault.py``'s own module docstring:
+    zero production call sites of ``seal_shard``/``assign_shard``/``expose_shard`` today), so by
+    the time a pool could ever be "whole-pool released" (TR-27's own gate), the recording run this
+    progress surface describes is already historical. This is the phase spec's own explicitly
+    sanctioned scope-reducing option (NOTES: "provably spec-compliant... TC-9/TC-10/TC-11 are
+    outcome-based and pass either way"), deliberately chosen to avoid new coupling between this
+    module and ``vault.py`` -- the OUT-OF-SCOPE item this iteration already names ("wiring
+    tick_recorder to call vault.seal_shard/assign_shard/expose_shard directly")."""
     chunks_total = progress["chunks_total"]
     chunks_done = progress["chunks_done"]
     percent_complete = (chunks_done / chunks_total * 100.0) if chunks_total > 0 else 0.0
@@ -683,8 +742,8 @@ def _progress_view(progress: dict, *, started_utc: str | None, finished_utc: str
         "chunks_total": chunks_total,
         "chunks_done": chunks_done,
         **_outcome_type_counts(progress["outcomes"]),
-        "trades_total": progress["trades_total"],
-        "quotes_total": progress["quotes_total"],
+        "trades_total_bucket": _volume_bucket(progress["trades_total"]),
+        "quotes_total_bucket": _volume_bucket(progress["quotes_total"]),
         "percent_complete": percent_complete,
         "elapsed_seconds": elapsed_seconds,
     }
diff --git a/apps/backend/app/research/vault.py b/apps/backend/app/research/vault.py
index 2b8a95b..84502ab 100644
--- a/apps/backend/app/research/vault.py
+++ b/apps/backend/app/research/vault.py
@@ -9,7 +9,9 @@ exactly one identity function).
 
 **Two distinct ledgers, per the phase spec's own naming (T-2 vocabulary trap).** ``VaultUniverseLedger``
 (recording-universe registrations: ``{universe_id, symbol_rule, date_rule, registered_at,
-rule_hash, vault_secret_commitment}``) and ``VaultShardLedger`` (the shard-lifecycle
+rule_hash, commitment_nonce, rule_commitment, vault_secret_commitment}`` -- the last three fields'
+own two-stage SERVING discipline is the "Iteration 12" paragraph below) and ``VaultShardLedger`` (the
+shard-lifecycle
 ``sealed -> assigned -> exposed`` transitions) are TWO separate ``micro_chain_ledger.
 HashChainedLedger`` instances -- the ``walkforward_ledger.WalkForwardLedger`` "thin domain wrapper
 over ONE HashChainedLedger" shape, built here TWICE (module docstring precedent: "once per
@@ -57,11 +59,16 @@ not enough; JOIN RESISTANCE is the actual requirement (r3), and it is met here i
    rows lets any reader compute ``sealed = expected - served`` and de-anonymise the whole sealed
    tranche by set subtraction -- defeating section 7.3's stated guarantee that "sealed membership
    cannot be inferred from public information before exposure". So the rule lists follow the SAME
-   commit-then-reveal discipline part 2 applies to ``content_checksum``: ``rule_hash`` (already
-   computed at registration) is served throughout, the raw lists only once every shard of that
-   universe has reached ``exposed``. Section 7.2's requirement is that the rule be RECORDED in the
-   vault ledger before any fetch -- unchanged here, and ``find_universe``/the TR-4 verifier still
-   read it verbatim from that ledger, so nothing about the batch check or its auditability moves.
+   commit-then-reveal discipline part 2 applies to ``content_checksum``: a commitment is served
+   throughout, the raw lists only once every shard of that universe has reached ``exposed``.
+   [**Iteration 12 update, r7/TR-27:** that served commitment is NOT ``rule_hash`` -- a bare
+   deterministic hash of a low-entropy, dictionary-enumerable rule is not a hiding commitment.
+   ``rule_hash`` stays purely internal (``register_universe``'s own freeze/idempotency check,
+   never served); ``_serialize_universe`` serves the NONCED ``rule_commitment`` instead. See the
+   "Iteration 12" paragraph below for the full reasoning.] Section 7.2's requirement is that the
+   rule be RECORDED in the vault ledger before any fetch -- unchanged here, and ``find_universe``/
+   the TR-4 verifier still read it verbatim from that ledger, so nothing about the batch check or
+   its auditability moves.
 
 TR-2 proves this by construction rather than by whitelist review (``tests/test_vault.py``'s
 adversarial join-resistance sweep over every registered GET route).
@@ -126,7 +133,86 @@ guard that keeps a later-registered universe from retroactively withholding a pr
 dataset). It is the ONE new choke point ``micro_snapshots.exclude_withheld``/
 ``withheld_dataset_ids_for_store`` (hence its 8 existing corpus-wide enumerator consumers) and
 ``micro_readiness.build_readiness`` both read -- never a second, divergent implementation of "is
-this dataset withheld"."""
+this dataset withheld".
+
+**Iteration 12 -- three closures, per ``docs/rapid-validation-spec.md`` r6/r7 (owner rulings
+2026-08-18/19).**
+
+1. **TR-25, vault-ledger integrity (spec section 7.8).** Every normal reader of either ledger now
+   goes through a GATED read -- ``VaultShardLedger.verified_rows()``/``VaultUniverseLedger.
+   verified_rows()`` -- which calls ``verify_chain()`` FIRST and raises ``VaultLedgerCorruptionError``
+   on any failure, never returning a result computed over a tampered or truncated chain. This is
+   wired in at the LOWEST shared choke points (``_latest_rows_by_dataset_id``, ``_latest_universes``,
+   ``find_universe``), so every one of this module's own public predicates and mutators
+   (``unresolved_pool_universe_by_dataset_id``, ``build_vault_state``, ``currently_sealed_dataset_ids``,
+   ``withheld_dataset_ids``, ``register_universe``, ``verify_universe_recording_batch``,
+   ``seal_shard``/``assign_shard``/``expose_shard`` via their own ``_latest_shard_row`` read)
+   inherits the gate automatically -- and so does every OTHER module that calls into this one
+   (``walkforward.py``'s direct ``currently_sealed_dataset_ids`` call, ``routes.py``'s
+   ``get_withheld_dataset_ids`` dependency) with ZERO changes to those files, exactly the
+   "single choke point, never a second divergent implementation" discipline this module already
+   follows for the withhold predicate itself. ``main.py`` registers ONE global FastAPI exception
+   handler for ``VaultLedgerCorruptionError`` (the ``RealDataError`` precedent), so every route
+   this exception can reach -- not merely this module's own ``GET /vault``/``GET /readiness`` --
+   gets a non-500 refusal, without needing a route-by-route try/except audit. Lawful recovery
+   (``recover_shard_ledger`` below) is the ONLY way back; there is no warn-and-continue path
+   anywhere in this module.
+
+   *Disclosed interpretation call (T-1), matching this module's own established convention of
+   logging rather than silently assuming a scope boundary.* The phase spec's own text asks the
+   shard mutators to check "both ledgers". This module implements that literally for the two
+   functions that already take both ledgers as parameters end to end
+   (``unresolved_pool_universe_by_dataset_id``, ``build_vault_state``) and transitively for
+   ``register_universe``/``find_universe``/``verify_universe_recording_batch`` (all of which read
+   the universe ledger through the same gated ``verified_rows()``). ``seal_shard``/``assign_shard``/
+   ``expose_shard`` are gated on their OWN (shard) ledger only, NOT additionally threaded with a
+   required ``universe_ledger`` parameter. Grounds: a repo-wide grep at authoring (unchanged from
+   iteration 11) still finds ZERO production call sites of these three functions -- everything that
+   calls them today is a test -- so widening their signature buys no real-world safety today, while
+   it would force a mechanical, high-blast-radius migration of roughly 90 call sites across TEN test
+   files (``test_vault.py`` alone has 42) that have nothing to do with ledger integrity, for a
+   currently-unreachable production risk. TC-2's own literal text ("no sealing, no assignment") is
+   satisfied by gating the SHARD ledger, the one these transitions actually read and write; a test
+   pins exactly that. When J-06 step 4 eventually wires real ``seal_shard``/``assign_shard``/
+   ``expose_shard`` calls into production, that wiring is the natural point to revisit whether the
+   universe ledger should also gate these specific transitions -- logged here so the boundary is
+   never silently assumed, exactly this module's own T-1 discipline elsewhere (see the single-shot
+   discipline paragraph above).
+
+2. **TR-27, nonced rule commitment (spec section 7.2/7.5, r7).** ``register_universe`` now mints a
+   high-entropy ``commitment_nonce`` (``secrets.token_hex(32)``) at registration and computes
+   ``rule_commitment = sha256(nonce + canonical_rule)`` (``compute_rule_commitment``) -- served in
+   place of the plain ``rule_hash`` at every disclosure stage. ``rule_hash``/``compute_rule_hash``
+   themselves are UNCHANGED and stay exactly what they were: the ledger's own internal,
+   never-served freeze/idempotency identity function for ``register_universe``'s re-registration
+   check (spec r7's own text: "rule_hash/compute_rule_hash stays as the ledger's own internal
+   identity function"). The reveal gate widens in the SAME diff, per the session's own hard-won
+   lesson ("never widen one side of a paired mechanism and leave its twin narrow"):
+   ``_fully_exposed_universe_ids`` (ledger-tracked-only, the iteration-11 audit's own two-GET
+   subtraction target, ``vault.py:926-938`` pre-iteration-12) is REPLACED by
+   ``_whole_pool_released_universe_ids``, which reuses ``expected_recording_pairs`` -- the SAME
+   expected-pairs computation ``unresolved_pool_universe_by_dataset_id`` already uses -- as the ONE
+   "whole ORIGINAL pool released" predicate. ``symbol_rule``/``date_rule``/``commitment_nonce`` serve
+   ONLY once (a) no ledger-tracked shard of that universe is short of ``exposed`` AND (b) every
+   expected pair has an ``exposed`` shard -- a universe with any ledger-tracked OR
+   untracked-but-rule-matching pair still short of ``exposed`` stays at the committed
+   (``rule_commitment``-only) stage. **Part (a) is not redundant with (b):** an adversarial
+   pre-ship review found that (b) ALONE is keyed on the ``(symbol, session_date)`` pair, not on
+   shard identity, so a SECOND, different ``dataset_id`` sealed+assigned under the SAME pair as an
+   already-exposed first shard (a re-recorded/retry day, spec section 7.7) would satisfy (b) while
+   genuinely still withheld -- reopening the exact two-GET subtraction class this widening exists
+   to close. See that function's own docstring and
+   ``test_two_shards_sharing_one_pair_keep_the_universe_hidden_even_after_one_is_exposed``.
+
+3. **The symbol/date withhold-match normalization (the third cheap companion item).** The
+   universe-rule membership test inside ``unresolved_pool_universe_by_dataset_id`` (test (b) in that
+   function's own docstring) now compares symbols case-insensitively (``_normalize_symbol``) on
+   BOTH the registered rule's own ``symbol_rule`` entries and the incoming record's symbol, so a
+   universe registered as ``aapl`` still withholds a recording produced as ``AAPL`` and vice versa.
+   Deliberately scoped to THIS predicate alone -- ``expected_recording_pairs``/
+   ``verify_recording_batch`` (TR-4's cherry-pick check) keep their own byte-exact matching
+   unchanged, since the phase spec names only "the universe-rule test" inside this one function, not
+   a broader normalization of the recording-batch verifier."""
 
 from __future__ import annotations
 
@@ -135,6 +221,7 @@ import hmac
 import json
 import math
 import os
+import secrets
 from datetime import datetime, timezone
 from pathlib import Path
 
@@ -147,18 +234,23 @@ __all__ = [
     "STATE_SEALED",
     "STATE_ASSIGNED",
     "STATE_EXPOSED",
+    "STATE_EXPOSURE_UNKNOWN",
     "VaultUniverseNotRegisteredError",
     "VaultUniverseAlreadyRegisteredError",
     "CherryPickedBatchError",
     "VaultSecretUnavailable",
     "ShardLifecycleOrderError",
     "SealedShardWithheldError",
+    "VaultLedgerCorruptionError",
     "resolve_vault_dir",
     "shard_ledger_for_dataset_dir",
     "universe_ledger_for_dataset_dir",
+    "recovery_ledger_for_dataset_dir",
     "VaultUniverseLedger",
     "VaultShardLedger",
+    "VaultRecoveryLedger",
     "compute_rule_hash",
+    "compute_rule_commitment",
     "register_universe",
     "find_universe",
     "expected_recording_pairs",
@@ -181,6 +273,8 @@ __all__ = [
     "compute_family_root_id",
     "RULE_DISCLOSURE_COMMITTED",
     "RULE_DISCLOSURE_REVEALED",
+    "preserve_corrupt_ledger",
+    "recover_shard_ledger",
 ]
 
 # docs/rapid-validation-spec.md section 1, transcribed verbatim -- NEVER a Config field (every
@@ -208,6 +302,15 @@ STATE_SEALED = "sealed"
 STATE_ASSIGNED = "assigned"
 STATE_EXPOSED = "exposed"
 
+# Iteration 12 (spec section 7.8, TR-25): the FOURTH, terminal lifecycle value -- never reachable
+# through seal_shard/assign_shard/expose_shard, written ONLY by recover_shard_ledger below when a
+# corrupted ledger's missing suffix cannot be proven complete. Matches neither STATE_SEALED nor
+# STATE_ASSIGNED, so the existing lifecycle guards in assign_shard/expose_shard already refuse any
+# further transition for a shard in this state with no new guard code (their own `actual_state !=
+# expected_state` checks do the job) -- "permanently ineligible for sealed-OOS use" falls out of
+# the existing single-shot machinery for free.
+STATE_EXPOSURE_UNKNOWN = "exposure_unknown"
+
 # The universe rule's two serving stages (module docstring's join-resistance part 4). A DIFFERENT
 # vocabulary from the shard lifecycle above on purpose: a universe has no lifecycle of its own --
 # its rule's disclosure is a pure function of whether every shard it owns has reached `exposed`.
@@ -219,6 +322,10 @@ _VAULT_SECRET_FILE_ENV = "TAPEOLOGY_VAULT_SECRET_FILE"
 
 _UNIVERSE_LEDGER_FILENAME = "vault_universe_ledger.jsonl"
 _SHARD_LEDGER_FILENAME = "vault_shard_ledger.jsonl"
+# Iteration 12 (spec section 7.8): the THIRD, SEPARATE ledger lawful recovery writes to -- "record
+# the corruption event separately and immutably" (never in the corrupted ledger itself, which
+# cannot be trusted to record its own corruption).
+_RECOVERY_LEDGER_FILENAME = "vault_recovery_ledger.jsonl"
 
 # Ledger-machinery keys ``HashChainedLedger.append_row`` itself manages -- stripped before a row's
 # OWN content is carried forward into a later row (``assign_shard``/``expose_shard`` below), so a
@@ -311,6 +418,31 @@ class SealedShardWithheldError(Exception):
         )
 
 
+class VaultLedgerCorruptionError(Exception):
+    """TR-25/spec section 7.8: raised by every GATED vault-ledger read (``VaultShardLedger.
+    verified_rows``/``VaultUniverseLedger.verified_rows``) the instant ``verify_chain()`` reports a
+    broken chain -- content-hash mismatch, prev-hash mismatch, tail truncation, or a head-hash
+    mismatch against the durable tail anchor. Fail-closed: no caller of a gated reader EVER
+    receives a result computed over a ledger that failed this check, and there is no
+    warn-and-continue path anywhere in this module (module docstring's own iteration-12 paragraph
+    lists every choke point this reaches transitively). The ONLY way back is
+    ``recover_shard_ledger`` below (lawful recovery, spec section 7.8) -- never a silent retry,
+    never treating a truncated chain as merely "empty" (TC-1's own requirement: "no shard is
+    reported as 'never exposed'"). ``main.py`` maps this to a single non-500 HTTP refusal for every
+    route it can reach (module docstring)."""
+
+    def __init__(self, ledger_kind: str, verify_result: dict) -> None:
+        self.ledger_kind = ledger_kind
+        self.verify_result = verify_result
+        super().__init__(
+            f"the {ledger_kind} vault ledger failed chain verification "
+            f"(reason={verify_result.get('reason')!r}, failed_at_row={verify_result.get('failed_at_row')!r}) "
+            "-- ALL vault/exposure work is refused (no sealing, no assignment, no exposure check, "
+            "no sealed evaluation) until a lawful, evidence-backed recovery completes (spec "
+            "section 7.8); unknown exposure history may NEVER be read as 'never exposed'"
+        )
+
+
 def _canonical(obj: object) -> bytes:
     """The one canonical JSON encoding this module hashes -- the identical sorted-keys,
     no-whitespace shape every sibling ledger in this codebase hashes (``scout_ledger.py``,
@@ -353,6 +485,15 @@ def universe_ledger_for_dataset_dir(dataset_dir_resolved: str) -> "VaultUniverse
     return VaultUniverseLedger(resolve_vault_dir(dataset_dir_resolved))
 
 
+def recovery_ledger_for_dataset_dir(dataset_dir_resolved: str) -> "VaultRecoveryLedger":
+    """The SEPARATE, immutable incident ledger lawful recovery writes to (spec section 7.8 step 2:
+    "record the corruption event separately and immutably" -- never in the corrupted ledger
+    itself, which cannot be trusted to record its own corruption). The SAME sibling-of-the-
+    dataset-dir resolution every other vault store shares (``resolve_vault_dir``), so there is
+    exactly one vault location, holding all three ledgers side by side."""
+    return VaultRecoveryLedger(resolve_vault_dir(dataset_dir_resolved))
+
+
 # === the two ledgers (module docstring: "once per ledger") =========================================
 
 
@@ -365,12 +506,40 @@ class VaultUniverseLedger:
     def __init__(self, root_dir: str) -> None:
         self._chain = HashChainedLedger(root_dir, _UNIVERSE_LEDGER_FILENAME)
 
+    @property
+    def path(self) -> Path:
+        return self._chain.path
+
+    @property
+    def head_anchor_path(self) -> Path:
+        return self._chain.head_anchor_path
+
     def verify_chain(self) -> dict:
         return self._chain.verify_chain()
 
     def all_rows(self) -> list[dict]:
+        """The RAW, UNGATED reader (``HashChainedLedger.all_rows()``'s own documented contract,
+        unchanged) -- used only by this module's own recovery tooling, which must be able to
+        inspect a corrupted ledger's content directly in order to repair it. Every NORMAL
+        predicate uses ``verified_rows()`` below instead."""
+        return self._chain.all_rows()
+
+    def verified_rows(self) -> list[dict]:
+        """TR-25/spec section 7.8: the GATED reader every normal predicate uses. Calls
+        ``verify_chain()`` FIRST and raises ``VaultLedgerCorruptionError`` on any failure --
+        never returns a result computed over a tampered or truncated chain (module docstring's
+        iteration-12 paragraph)."""
+        result = self._chain.verify_chain()
+        if not result["ok"]:
+            raise VaultLedgerCorruptionError("universe", result)
         return self._chain.all_rows()
 
+    def read_tail_anchor(self) -> dict | None:
+        return self._chain.read_tail_anchor()
+
+    def rewrite_from_recovery(self, rows: list[dict]) -> None:
+        self._chain.rewrite_from_recovery(rows)
+
     def append_row(self, fields: dict) -> dict:
         return self._chain.append_row(fields)
 
@@ -385,6 +554,53 @@ class VaultShardLedger:
     def __init__(self, root_dir: str) -> None:
         self._chain = HashChainedLedger(root_dir, _SHARD_LEDGER_FILENAME)
 
+    @property
+    def path(self) -> Path:
+        return self._chain.path
+
+    @property
+    def head_anchor_path(self) -> Path:
+        return self._chain.head_anchor_path
+
+    def verify_chain(self) -> dict:
+        return self._chain.verify_chain()
+
+    def all_rows(self) -> list[dict]:
+        """The RAW, UNGATED reader -- see ``VaultUniverseLedger.all_rows``'s own docstring; the
+        identical split, mirrored for the shard ledger."""
+        return self._chain.all_rows()
+
+    def verified_rows(self) -> list[dict]:
+        """TR-25/spec section 7.8: the GATED reader every normal predicate uses -- see
+        ``VaultUniverseLedger.verified_rows``'s own docstring, mirrored for the shard ledger."""
+        result = self._chain.verify_chain()
+        if not result["ok"]:
+            raise VaultLedgerCorruptionError("shard", result)
+        return self._chain.all_rows()
+
+    def read_tail_anchor(self) -> dict | None:
+        return self._chain.read_tail_anchor()
+
+    def rewrite_from_recovery(self, rows: list[dict]) -> None:
+        self._chain.rewrite_from_recovery(rows)
+
+    def append_row(self, fields: dict) -> dict:
+        return self._chain.append_row(fields)
+
+
+class VaultRecoveryLedger:
+    """A thin domain wrapper over a THIRD ``HashChainedLedger`` (module docstring: "once per
+    ledger") -- every corruption/recovery event lawful recovery records, in append order (spec
+    section 7.8: "record the corruption event separately and immutably"). Deliberately NOT
+    gated by its own ``verified_rows()`` -- this ledger is a pure audit trail no security
+    predicate reads to make a decision, so keeping it simple (raw ``all_rows()``/``verify_chain()``,
+    the pre-iteration-12 shape of the other two) avoids an unbounded regress of "who verifies the
+    verifier". ``record_recovery_event``'s own append is unaffected either way, since
+    ``HashChainedLedger.append_row`` never gates itself."""
+
+    def __init__(self, root_dir: str) -> None:
+        self._chain = HashChainedLedger(root_dir, _RECOVERY_LEDGER_FILENAME)
+
     def verify_chain(self) -> dict:
         return self._chain.verify_chain()
 
@@ -402,10 +618,37 @@ def compute_rule_hash(symbol_rule: list[str], date_rule: list[str]) -> str:
     """A pure content hash over the resolved, explicit ``symbol_rule``/``date_rule`` lists --
     excludes any wall-clock-derived value (``registered_at`` is never part of this), so two
     genuinely separate registration acts of the IDENTICAL rule compute the identical hash (the
-    ``scout_ledger.compute_spec_hash`` precedent, TC-2)."""
+    ``scout_ledger.compute_spec_hash`` precedent, TC-2).
+
+    **Never served publicly (spec r7/TR-27).** This stays exactly what it always was: the
+    ledger's own INTERNAL freeze/idempotency identity function, read only by
+    ``register_universe``'s own re-registration check. A bare deterministic hash of a low-entropy,
+    dictionary-enumerable rule is not a hiding commitment -- ``compute_rule_commitment`` below is
+    what ``_serialize_universe`` actually serves."""
     return _sha256_hex(_canonical({"symbol_rule": list(symbol_rule), "date_rule": list(date_rule)}))
 
 
+def compute_rule_commitment(nonce: str, symbol_rule: list[str], date_rule: list[str]) -> str:
+    """spec section 7.2/7.5 (r7, TR-27): ``rule_commitment = sha256(nonce ++ canonical_rule)``.
+
+    Unlike ``compute_rule_hash`` above, this is the value ``_serialize_universe`` actually SERVES
+    pre-reveal. The owner's ruling was explicit about why a bare hash will not do:
+    ``symbol_rule``/``date_rule`` are low-entropy and dictionary-enumerable (a real panel of
+    tickers and a real date range), so a third party holding only the served digest could simply
+    hash every plausible guess and check for a match. Prefixing a high-entropy nonce the ledger
+    holds PRIVATELY (never served until whole-pool release) makes this a genuine hiding
+    commitment: recomputing it without the nonce is infeasible, while an operator who legitimately
+    learns the nonce at reveal can recompute it exactly (TC-7) and prove the rule never changed
+    after registration.
+
+    ``nonce`` is encoded as UTF-8 bytes and concatenated directly in front of the SAME canonical
+    JSON encoding ``compute_rule_hash`` hashes -- a fixed-length hex string (``secrets.
+    token_hex(32)`` == 64 hex chars, always), so the boundary between the two halves is never
+    ambiguous."""
+    canonical_rule = _canonical({"symbol_rule": list(symbol_rule), "date_rule": list(date_rule)})
+    return _sha256_hex(nonce.encode("utf-8") + canonical_rule)
+
+
 def register_universe(
     ledger: VaultUniverseLedger,
     *,
@@ -430,7 +673,11 @@ def register_universe(
       except one path" lesson); and
     * ``VaultUniverseAlreadyRegisteredError`` otherwise -- because ``find_universe`` resolves to the
       LATEST row, an unrefused re-registration under a narrowed ``symbol_rule`` would silently
-      redefine ``expected_recording_pairs`` and neutralize TR-4's cherry-pick refusal entirely."""
+      redefine ``expected_recording_pairs`` and neutralize TR-4's cherry-pick refusal entirely.
+
+    **TR-27 (r7): a fresh, high-entropy ``commitment_nonce`` is minted ONLY on a genuinely NEW
+    row.** An idempotent replay returns the EXISTING row -- including its ORIGINAL nonce -- never
+    generating a second one for what is, by definition, the same registration act."""
     rule_hash = compute_rule_hash(symbol_rule, date_rule)
     existing = find_universe(ledger, universe_id)
     if existing is not None:
@@ -440,12 +687,15 @@ def register_universe(
         ):
             return existing
         raise VaultUniverseAlreadyRegisteredError(universe_id, existing["rule_hash"], rule_hash)
+    nonce = secrets.token_hex(32)
     fields = {
         "universe_id": universe_id,
         "symbol_rule": list(symbol_rule),
         "date_rule": list(date_rule),
         "registered_at": registered_at if registered_at is not None else _iso_utc_now(),
         "rule_hash": rule_hash,
+        "commitment_nonce": nonce,
... [diff_bound] apps/backend/app/research/vault.py: 510 more diff lines omitted — Read the file for full detail
diff --git a/apps/backend/tests/test_tick_recorder.py b/apps/backend/tests/test_tick_recorder.py
index 6ba35db..cf0b216 100644
--- a/apps/backend/tests/test_tick_recorder.py
+++ b/apps/backend/tests/test_tick_recorder.py
@@ -859,13 +859,18 @@ def test_cancel_while_running_stops_the_walk_cooperatively_through_the_route(rou
 
 _PROGRESS_AGGREGATE_KEYS = {
     "chunks_total", "chunks_done", "chunks_fetched", "chunks_reused", "chunks_unchanged",
-    "chunks_failed", "trades_total", "quotes_total", "percent_complete", "elapsed_seconds",
+    "chunks_failed", "trades_total_bucket", "quotes_total_bucket", "percent_complete",
+    "elapsed_seconds",
 }
 
 
 def _assert_progress_is_aggregate_only(progress: dict) -> None:
     """TC-6's own field-shape assertion: EXACTLY the ten aggregate fields spec section 7.1 (r5)
-    names -- no ``outcomes``, no ``symbol``, no ``date``, no ``dataset_id``, nothing else."""
+    names -- no ``outcomes``, no ``symbol``, no ``date``, no ``dataset_id``, nothing else.
+
+    Iteration 12 (TR-28/r7): ``trades_total``/``quotes_total`` (exact) are GONE, replaced by
+    ``trades_total_bucket``/``quotes_total_bucket`` (coarse labels) -- the iteration-11 audit
+    proved a one-symbol-day run's "aggregate" exact total WAS that withheld shard's exact count."""
     assert set(progress.keys()) == _PROGRESS_AGGREGATE_KEYS, sorted(progress.keys())
 
 
@@ -937,8 +942,10 @@ def test_tc6_recorder_progress_never_leaks_a_planned_chunks_symbol_date_or_datas
         assert terminal["progress"]["chunks_reused"] == 0
         assert terminal["progress"]["chunks_unchanged"] == 0
         assert terminal["progress"]["chunks_failed"] == 0
-        assert terminal["progress"]["trades_total"] == 3  # 1 trade/chunk -- the fake adapter's shape
-        assert terminal["progress"]["quotes_total"] == 3  # 1 quote/chunk
+        # 3 trades/3 quotes total (1 trade/chunk, 1 quote/chunk -- the fake adapter's shape) both
+        # land in the SAME coarse bucket (iteration 12, TR-28/r7) -- never the exact number 3.
+        assert terminal["progress"]["trades_total_bucket"] == tr._volume_bucket(3) == "1-999"
+        assert terminal["progress"]["quotes_total_bucket"] == tr._volume_bucket(3) == "1-999"
         assert terminal["progress"]["percent_complete"] == 100.0
         assert terminal["progress"]["elapsed_seconds"] >= 0.0
 
@@ -986,4 +993,131 @@ def test_tc7_the_recorder_progress_route_accepts_no_bypass_parameter_header_or_r
     assert probed == plain  # every extra input is silently ignored -- no bypass exists anywhere
 
 
+# ==================================================================================================
+# 13. Era iteration 12 (spec section 7.1, r7): TR-28 -- event/byte VOLUMES are coarse BUCKETS
+#     pre-release, never exact totals. TC-9/TC-10/TC-11 (phase spec's own test-first contract).
+# ==================================================================================================
+
+
+def _run_a_one_symbol_day_recording_to_done(client) -> dict:
+    r = client.post(
+        "/research/desk/micro/recorder/compute", json={"symbols": ["AAPL"], "dates": ["2026-06-01"]},
+    )
+    assert r.status_code == 200
+    deadline = time.time() + 15
+    terminal = None
+    while time.time() < deadline:
+        terminal = client.get("/research/desk/micro/recorder/compute").json()
+        if terminal["state"] != "running":
+            break
+        time.sleep(0.02)
+    assert terminal is not None and terminal["state"] == "done"
+    return terminal
+
+
+def test_tc9_a_one_symbol_day_run_never_serves_an_exact_trade_or_quote_count(route_ctx):
+    """TC-9 (phase spec, literal scenario): a one-symbol-day recorder run whose pool is unexposed
+    -- ``GET /research/desk/micro/recorder/compute`` polled during and after the run never carries
+    an exact trade count, quote count, or byte count anywhere -- only a predeclared coarse bucket
+    label. The iteration-11 audit's own reproduction: on exactly this shape, the "aggregate"
+    ``trades_total``/``quotes_total`` WAS that one shard's exact count."""
+    client, _mgr, _adapter, _tmp_path = route_ctx
+    terminal = _run_a_one_symbol_day_recording_to_done(client)
+    progress = terminal["progress"]
+    _assert_progress_is_aggregate_only(progress)  # exactly the bucket-shaped field set, nothing else
+    assert isinstance(progress["trades_total_bucket"], str) and progress["trades_total_bucket"]
+    assert isinstance(progress["quotes_total_bucket"], str) and progress["quotes_total_bucket"]
+    body_text = json.dumps(terminal)
+    assert "trades_total\"" not in body_text and "quotes_total\"" not in body_text
+
+
+def test_tc10_before_after_a_run_grows_the_bucket_never_narrows_and_resists_differencing(
+    route_ctx, monkeypatch
+):
+    """TC-10: poll a run's progress before and after its own running totals GROW -- the served
+    bucket is monotonic non-decreasing (never narrows), and because it is ALWAYS a coarse label
+    (never conditionally exact -- ``_progress_view``'s own iteration-12 docstring), no pair of
+    snapshots can be combined to solve any count exactly: neither response carries an exact number
+    to difference in the first place."""
+    client, mgr, _adapter, _tmp_path = route_ctx
+    from app.main import app, get_market_adapter
+
+    fake_plan = [
+        {"symbol": "AAPL", "date": "2026-06-01", "start": "2026-06-01T13:30:00Z", "end": "2026-06-01T15:00:00Z"},
+        {"symbol": "AAPL", "date": "2026-06-01", "start": "2026-06-01T15:00:00Z", "end": "2026-06-01T20:00:00Z"},
+    ]
+    monkeypatch.setattr(tr, "plan_recorder_chunks", lambda symbols, dates: list(fake_plan))
+    blocking_adapter = _BlockingTickAdapter()
+    app.dependency_overrides[get_market_adapter] = lambda: blocking_adapter
+    try:
+        r = client.post(
+            "/research/desk/micro/recorder/compute", json={"symbols": ["AAPL"], "dates": ["2026-06-01"]},
+        )
+        assert r.status_code == 200
+        assert blocking_adapter.started.wait(timeout=5.0)
+        before = client.get("/research/desk/micro/recorder/compute").json()["progress"]
+
+        blocking_adapter.proceed.set()
+        deadline = time.time() + 15
+        terminal = None
+        while time.time() < deadline:
+            terminal = client.get("/research/desk/micro/recorder/compute").json()
+            if terminal["state"] != "running":
+                break
+            time.sleep(0.02)
+        assert terminal is not None and terminal["state"] == "done"
+        after = terminal["progress"]
+
+        for snapshot in (before, after):
+            assert "trades_total" not in snapshot and "quotes_total" not in snapshot
+
+        bucket_order = [label for _, _, label in tr._VOLUME_BUCKETS]
+        assert bucket_order.index(before["trades_total_bucket"]) <= bucket_order.index(
+            after["trades_total_bucket"]
+        )
+        assert bucket_order.index(before["quotes_total_bucket"]) <= bucket_order.index(
+            after["quotes_total_bucket"]
+        )
+    finally:
+        blocking_adapter.proceed.set()
+        mgr.join_all(timeout=10.0)
+
+
+def test_tc11_this_surface_deliberately_never_re_enables_exact_totals(route_ctx):
+    """TC-11 is PERMISSIVE ("exact totals MAY be served again"), never mandatory -- and the phase
+    spec's own NOTES sanction never threading per-universe vault-exposure state into this module at
+    all (recording strictly PRECEDES any possible exposure, so a completed run's own progress here
+    always describes pre-release history). This module's own choice: ``_progress_view`` ALWAYS
+    buckets, with no code path that could ever flip to exact -- pinned here so a future change
+    cannot silently re-open TR-28 by conditionally reinstating ``trades_total``."""
+    client, _mgr, _adapter, _tmp_path = route_ctx
+    terminal = _run_a_one_symbol_day_recording_to_done(client)
+    for _ in range(3):  # "long after" completion, simulated by simply re-polling with no new work
+        again = client.get("/research/desk/micro/recorder/compute").json()["progress"]
+        assert "trades_total" not in again and "quotes_total" not in again
+        assert again["trades_total_bucket"] == terminal["progress"]["trades_total_bucket"]
+        assert again["quotes_total_bucket"] == terminal["progress"]["quotes_total_bucket"]
+
+
+def test_volume_bucket_scheme_is_frozen_predeclared_and_never_a_rounded_number(monkeypatch):
+    """The scheme itself, pinned: a module constant (never a ``Config`` field, never tuned from an
+    observed run), monotonic, and never produces a label that LOOKS like a rounded exact count."""
+    assert tr._volume_bucket(0) == "0"
+    assert tr._volume_bucket(1) == tr._volume_bucket(999) == "1-999"
+    assert tr._volume_bucket(1000) == "1K-10K"
+    assert tr._volume_bucket(3_842_117) == "1M-10M"
+    labels = [label for _, _, label in tr._VOLUME_BUCKETS]
+    assert len(labels) == len(set(labels))  # no duplicate label across bands
+    # "0" is the one legitimate bare-digit label -- a genuinely, unambiguously empty count is not
+    # an approximation of anything hidden, so it carries no rounding risk. Every OTHER band must
+    # never look like a rounded exact number.
+    assert labels[0] == "0"
+    for label in labels[1:]:
+        assert not label.isdigit()
+    # monotonic across a wide, increasing sample -- never a larger count mapping to an earlier band.
+    sample = [0, 1, 500, 999, 1_000, 50_000, 999_999, 1_000_000, 5_000_000_000]
+    indices = [labels.index(tr._volume_bucket(n)) for n in sample]
+    assert indices == sorted(indices)
+
+
 from app.config import CONFIG  # noqa: E402 -- imported at bottom to keep the fixture section terse
diff --git a/apps/backend/tests/test_vault.py b/apps/backend/tests/test_vault.py
index 1c9ce12..5e9e907 100644
--- a/apps/backend/tests/test_vault.py
+++ b/apps/backend/tests/test_vault.py
@@ -1151,9 +1151,13 @@ def test_audit_b1_the_universe_rule_cannot_de_anonymise_the_sealed_tranche_by_su
         assert len(datasets["datasets"]) == 3
 
         universe = body["universes"][0]
-        # the commitment stage: the rule's HASH and SHAPE, never its membership.
+        # the commitment stage: the rule's NONCED COMMITMENT and SHAPE, never its membership, and
+        # never the plain rule_hash (r7/TR-27 -- a bare deterministic hash of a low-entropy,
+        # dictionary-enumerable rule is not a hiding commitment).
         assert universe["rule_disclosure"] == vault.RULE_DISCLOSURE_COMMITTED
-        assert universe["rule_hash"] == vault.compute_rule_hash(symbols, dates)
+        assert "rule_hash" not in universe
+        assert "commitment_nonce" not in universe
+        assert universe["rule_commitment"] != vault.compute_rule_hash(symbols, dates)
         assert (universe["symbol_rule_size"], universe["date_rule_size"]) == (2, 2)
         assert "symbol_rule" not in universe and "date_rule" not in universe
         for token in symbols + dates:
@@ -1175,8 +1179,13 @@ def test_audit_b1_the_universe_rule_cannot_de_anonymise_the_sealed_tranche_by_su
             key in universe for key in ("symbol_rule", "date_rule", "expected_pairs")
         )
 
-    # the reveal half: once EVERY shard of the universe is exposed, section 7.2's audit trail is
-    # served in full again -- the commitment is a delay, never a permanent withholding.
+    # TC-6/TR-27 (r7): assigning, then EXPOSING, this ONE tracked shard does NOT reveal the
+    # universe -- three of its four ORIGINAL pool members (both ZQXAAA pairs, and ZQXBBB's other
+    # date) were never even ledger-tracked, let alone exposed. The pre-iteration-12 gate
+    # (`_fully_exposed_universe_ids`, "every LEDGER-TRACKED shard exposed") would have wrongly
+    # revealed the rule here -- the exact two-GET subtraction door the iteration-11 audit proved
+    # open (module docstring). The widened `_whole_pool_released_universe_ids` requires every
+    # ORIGINAL pool member, not merely every member this ledger happens to know about.
     family_root = vault.compute_family_root_id("impact_efficiency_trend", "band_wall_touch", "trades_20")
     vault.assign_shard(
         shard_ledger, dataset_id=sealed_meta["id"], family_root_id=family_root,
@@ -1186,18 +1195,48 @@ def test_audit_b1_the_universe_rule_cannot_de_anonymise_the_sealed_tranche_by_su
     assert still_withheld["rule_disclosure"] == vault.RULE_DISCLOSURE_COMMITTED  # assigned != exposed
 
     vault.expose_shard(shard_ledger, dataset_id=sealed_meta["id"], family_root_id=family_root)
+    one_of_four_exposed = vault.build_vault_state(shard_ledger, universe_ledger)["universes"][0]
+    assert one_of_four_exposed["rule_disclosure"] == vault.RULE_DISCLOSURE_COMMITTED  # STILL hidden
+    assert "symbol_rule" not in one_of_four_exposed
+
+    # the actual reveal half (TC-7): seal, assign and expose the THREE remaining pool members too
+    # -- only once literally every one of the universe's four ORIGINAL pairs is exposed does the
+    # rule (plus the nonce) serve, and it recomputes EXACTLY to the commitment registration
+    # produced up front.
+    for pair in metas:  # metas' own keys ARE the universe's full 2x2 expected set (module setup)
+        if pair == secret_member:
+            continue
+        meta = metas[pair]
+        vault.seal_shard(
+            shard_ledger, dataset_id=meta["id"], universe_id="starter-tranche-v1",
+            content_checksum=meta["checksum"], event_count=meta["event_counts"]["total"],
+            vault_secret=_FIXTURE_SECRET,
+        )
+        vault.assign_shard(
+            shard_ledger, dataset_id=meta["id"], family_root_id=family_root,
+            symbol=pair[0], session_date=pair[1],
+        )
+        vault.expose_shard(shard_ledger, dataset_id=meta["id"], family_root_id=family_root)
+
     revealed = vault.build_vault_state(shard_ledger, universe_ledger)["universes"][0]
     assert revealed["rule_disclosure"] == vault.RULE_DISCLOSURE_REVEALED
     assert revealed["symbol_rule"] == symbols and revealed["date_rule"] == dates
-    assert revealed["rule_hash"] == vault.compute_rule_hash(symbols, dates)
+    assert revealed["rule_commitment"] == universe["rule_commitment"]  # unchanged since registration
+    assert (
+        vault.compute_rule_commitment(revealed["commitment_nonce"], symbols, dates)
+        == revealed["rule_commitment"]
+    )
 
 
 def test_audit_b1_a_universe_with_no_shards_yet_keeps_its_rule_committed(tmp_path):
     """The fail-closed half of the fix. Spec section 7.2's mandated order registers the universe
     (step 5) BEFORE any vendor fetch (step 7), so there is a real window in which the universe owns
     zero shards -- and a reader who harvests the rule during that window keeps it for the whole
-    tranche's life. `_fully_exposed_universe_ids` therefore reveals only a universe that owns at
-    least one shard AND has none left withheld; "no shards" reveals nothing."""
+    tranche's life. `_whole_pool_released_universe_ids` (iteration 12's widened successor to the
+    pre-iteration-12 `_fully_exposed_universe_ids`) therefore reveals only a universe whose full
+    EXPECTED pair set (`expected_recording_pairs`) is a subset of its own EXPOSED pairs; "no shards
+    at all" trivially fails that subset test (an empty exposed-pairs set can never contain the
+    universe's own non-empty expected set), so "no shards" reveals nothing."""
     vault_dir = str(tmp_path / "vault")
     universe_ledger = vault.VaultUniverseLedger(vault_dir)
     vault.register_universe(
@@ -1442,3 +1481,549 @@ def test_tc8_tc9_r5_inference_trap_a_registered_pool_with_mixed_provenance_leave
             "unexposed dataset's (symbol, date) uniquely -- proving TC-8's fixed-code assertion "
             "above is not vacuous"
         )
+
+
+# =====================================================================================================
+# Iteration 12 (docs/phases/goal-rapid-microscope-iter-12.md): TR-25 vault-ledger integrity (spec
+# section 7.8), TR-27 nonced rule commitment (spec section 7.2/7.5, r7), and the symbol-case
+# normalization companion item. TC-1 through TC-14, per the phase spec's own test-first contract.
+# =====================================================================================================
+
+
+def _seal_two_shards(shard_ledger: vault.VaultShardLedger) -> list[dict]:
+    """Two sealed shards (``d-1`` then ``d-2``), so a truncated-tail scenario has something real
+    to lose -- the shared fixture every TR-25 test below builds on."""
+    rows = []
+    for i, (dataset_id, checksum) in enumerate((("d-1", "a" * 64), ("d-2", "b" * 64))):
+        rows.append(
+            vault.seal_shard(
+                shard_ledger, dataset_id=dataset_id, universe_id="u1",
+                content_checksum=checksum, event_count=100 + i, vault_secret=_FIXTURE_SECRET,
+            )
+        )
+    return rows
+
+
+def _truncate_ledger_tail(ledger) -> None:
+    """Drops the LAST line of ``ledger``'s own ``.jsonl`` file, leaving its tail anchor
+    (``chain_head.json``, UNTOUCHED) still claiming the ORIGINAL row count -- TC-1/TC-3's own
+    scenario: a genuine, self-consistent prefix of true history, short by one row the anchor
+    proves should exist. Works for either ``VaultShardLedger`` or ``VaultUniverseLedger``."""
+    lines = ledger.path.read_text(encoding="utf-8").splitlines()
+    ledger.path.write_text("\n".join(lines[:-1]) + ("\n" if lines[:-1] else ""), encoding="utf-8")
+
+
+def _mutate_interior_row(ledger_path: Path, row_index: int, key: str, value: object) -> None:
+    """Rewrites ONE key of an already-appended, interior row -- TC-2's own scenario: the row's own
+    content hash no longer matches what it committed to."""
+    lines = ledger_path.read_text(encoding="utf-8").splitlines()
+    row = json.loads(lines[row_index])
+    row[key] = value
+    lines[row_index] = json.dumps(row, sort_keys=True)
+    ledger_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
+
+
+# --- TC-1/TC-2/TC-3: fail closed on a corrupted ledger, never treat it as empty or complete -------
+
+
+def test_tc1_a_truncated_shard_ledger_tail_fails_closed_on_every_predicate(tmp_path):
+    shard_ledger = vault.VaultShardLedger(str(tmp_path / "vault"))
+    universe_ledger = vault.VaultUniverseLedger(str(tmp_path / "vault"))
+    _seal_two_shards(shard_ledger)
+    _truncate_ledger_tail(shard_ledger)
+
+    assert shard_ledger.verify_chain()["reason"] == "tail_truncated"
+    with pytest.raises(vault.VaultLedgerCorruptionError) as exc_info:
+        vault.currently_sealed_dataset_ids(shard_ledger)
+    assert exc_info.value.ledger_kind == "shard"
+    with pytest.raises(vault.VaultLedgerCorruptionError):
+        vault.withheld_dataset_ids(shard_ledger)  # never silently omits the lost row's shard
+    with pytest.raises(vault.VaultLedgerCorruptionError):
+        vault.unresolved_pool_universe_by_dataset_id(shard_ledger, universe_ledger, [])
+    with pytest.raises(vault.VaultLedgerCorruptionError):
+        vault.build_vault_state(shard_ledger, universe_ledger)
+
+
+def test_tc1_a_truncated_universe_ledger_tail_fails_closed(tmp_path):
+    universe_ledger = vault.VaultUniverseLedger(str(tmp_path / "vault"))
+    vault.register_universe(
+        universe_ledger, universe_id="u1", symbol_rule=["PG"], date_rule=["2026-06-09"],
+        vault_secret_commitment=vault.commit_vault_secret(_FIXTURE_SECRET),
+    )
+    vault.register_universe(
+        universe_ledger, universe_id="u2", symbol_rule=["AAPL"], date_rule=["2026-06-10"],
+        vault_secret_commitment=vault.commit_vault_secret(_FIXTURE_SECRET),
+    )
+    _truncate_ledger_tail(universe_ledger)
+    assert universe_ledger.verify_chain()["reason"] == "tail_truncated"
+
+    with pytest.raises(vault.VaultLedgerCorruptionError) as exc_info:
+        vault.find_universe(universe_ledger, "u2")
+    assert exc_info.value.ledger_kind == "universe"
+    shard_ledger = vault.VaultShardLedger(str(tmp_path / "vault"))
+    with pytest.raises(vault.VaultLedgerCorruptionError):
+        vault.unresolved_pool_universe_by_dataset_id(shard_ledger, universe_ledger, [])
+    with pytest.raises(vault.VaultLedgerCorruptionError):
+        vault.build_vault_state(shard_ledger, universe_ledger)
+    # register_universe's own freeze/idempotency check reads the universe ledger too -- refused
+    # rather than silently re-registering (or silently refusing) against unverifiable history.
+    with pytest.raises(vault.VaultLedgerCorruptionError):
+        vault.register_universe(
+            universe_ledger, universe_id="u3", symbol_rule=["MSFT"], date_rule=["2026-06-11"],
+            vault_secret_commitment=vault.commit_vault_secret(_FIXTURE_SECRET),
+        )
+
+
+def test_tc2_an_interior_row_mutation_fails_closed_and_halts_sealing_and_assignment(tmp_path):
+    shard_ledger = vault.VaultShardLedger(str(tmp_path / "vault"))
+    universe_ledger = vault.VaultUniverseLedger(str(tmp_path / "vault"))
+    _seal_two_shards(shard_ledger)
+    _mutate_interior_row(shard_ledger.path, 0, "universe_id", "a-different-universe")
+
+    assert shard_ledger.verify_chain()["reason"] == "content_hash_mismatch"
+    with pytest.raises(vault.VaultLedgerCorruptionError):
+        vault.build_vault_state(shard_ledger, universe_ledger)
+    # spec section 7.8's own literal words: "no sealing, no assignment, no exposure check".
+    with pytest.raises(vault.VaultLedgerCorruptionError):
+        vault.seal_shard(
+            shard_ledger, dataset_id="d-3", universe_id="u1", content_checksum="c" * 64,
+            event_count=10, vault_secret=_FIXTURE_SECRET,
+        )
+    with pytest.raises(vault.VaultLedgerCorruptionError):
+        vault.assign_shard(
+            shard_ledger, dataset_id="d-1", family_root_id="root", symbol="PG",
+            session_date="2026-06-09",
+        )
+    with pytest.raises(vault.VaultLedgerCorruptionError):
+        vault.expose_shard(shard_ledger, dataset_id="d-1", family_root_id="root")
+
+
+def test_tc3_a_last_known_good_prefix_still_fails_closed_when_the_anchor_proves_more_existed(tmp_path):
+    """The raw prefix, taken in isolation, IS internally hash-chain-consistent -- proving this
+    isn't a trivially-broken file a naive "does row 0 verify" check would already catch. The GATED
+    reader refuses anyway, because the durable tail anchor proves a row is missing."""
+    shard_ledger = vault.VaultShardLedger(str(tmp_path / "vault"))
+    _seal_two_shards(shard_ledger)
+    _truncate_ledger_tail(shard_ledger)
+
+    raw_rows = shard_ledger.all_rows()  # the UNGATED reader -- still works, on purpose
+    assert len(raw_rows) == 1 and raw_rows[0]["dataset_id"] == "d-1"
+
+    with pytest.raises(vault.VaultLedgerCorruptionError) as exc_info:
+        shard_ledger.verified_rows()
+    assert exc_info.value.verify_result["reason"] == "tail_truncated"
+    with pytest.raises(vault.VaultLedgerCorruptionError):
+        vault.currently_sealed_dataset_ids(shard_ledger)
+
+
+# --- TC-4/TC-5: lawful recovery -- proven resumes exactly; unprovable marks exposure_unknown ------
+
+
+def test_tc4_a_hash_attested_reconstruction_resumes_service_and_reports_exact_prior_state(tmp_path):
+    vault_dir = str(tmp_path / "vault")
+    shard_ledger = vault.VaultShardLedger(vault_dir)
+    original_rows = _seal_two_shards(shard_ledger)
+    assert shard_ledger.verify_chain()["ok"] is True
+
+    _truncate_ledger_tail(shard_ledger)  # loses d-2's own seal row
+    verify_result = shard_ledger.verify_chain()
+    assert verify_result["ok"] is False
+
+    lost_row_fields = vault._row_content(original_rows[1])  # the caller's own trusted source
+    recovery_ledger = vault.VaultRecoveryLedger(vault_dir)
+    outcome = vault.recover_shard_ledger(
+        shard_ledger, verify_result=verify_result, reconstructed_suffix=[lost_row_fields],
+        sources=[{"source": "test-fixture-recall", "sha256": "irrelevant-for-this-test"}],
+        operator_identity="test-operator", reason="unit test TC-4",
+        recovery_ledger=recovery_ledger, incident_id="incident-tc4",
+        quarantine_dir=str(tmp_path / "quarantine"),
+    )
+    assert outcome == {"ok": True, "resumed": True, "exposure_unknown_dataset_ids": []}
+
+    # service resumes, reporting the EXACT prior state.
+    assert shard_ledger.verify_chain()["ok"] is True
+    assert vault.currently_sealed_dataset_ids(shard_ledger) == frozenset({"d-1", "d-2"})
+    state = vault.build_vault_state(shard_ledger, vault.VaultUniverseLedger(vault_dir))
+    assert {s["shard_id"] for s in state["shards"]} == {r["shard_id"] for r in original_rows}
+
+    # the recovery event is on permanent record, in the SEPARATE ledger -- never the shard ledger.
+    recovery_rows = recovery_ledger.all_rows()
+    assert len(recovery_rows) == 1
+    assert recovery_rows[0]["outcome"] == "complete"
+    assert recovery_rows[0]["operator_identity"] == "test-operator"
+    assert recovery_rows[0]["last_verified_row_index"] == 0
+    assert recovery_rows[0]["last_verified_row_hash"] == original_rows[0]["row_hash"]
+
+    # the corrupt original was preserved byte-for-byte, never overwritten in place.
+    quarantined = list((tmp_path / "quarantine").glob("incident-tc4.*"))
+    assert quarantined, "no forensic copy of the corrupt ledger was preserved"
+
+
+def test_tc5_an_unprovable_reconstruction_marks_affected_shards_exposure_unknown_permanently(tmp_path):
+    vault_dir = str(tmp_path / "vault")
+    shard_ledger = vault.VaultShardLedger(vault_dir)
+    _seal_two_shards(shard_ledger)
+    _truncate_ledger_tail(shard_ledger)
+    verify_result = shard_ledger.verify_chain()
+
+    recovery_ledger = vault.VaultRecoveryLedger(vault_dir)
+    # no trusted source at all -- the honest "we cannot prove what was lost" case.
+    outcome = vault.recover_shard_ledger(
+        shard_ledger, verify_result=verify_result, reconstructed_suffix=[],
+        sources=[], operator_identity="test-operator", reason="unit test TC-5",
+        recovery_ledger=recovery_ledger, incident_id="incident-tc5",
+        quarantine_dir=str(tmp_path / "quarantine"),
+    )
+    assert outcome["ok"] is False
+    assert outcome["resumed"] is True
+    assert outcome["exposure_unknown_dataset_ids"] == ["d-1"]  # the ONLY shard the trusted prefix names
+
+    # service resumes -- but d-1 (the only shard this ledger could still vouch for) is now
+    # exposure_unknown, never simply "still sealed".
+    assert shard_ledger.verify_chain()["ok"] is True
+    state = vault.build_vault_state(shard_ledger, vault.VaultUniverseLedger(vault_dir))
+    (entry,) = state["shards"]
+    assert entry["exposure_state"] == vault.STATE_EXPOSURE_UNKNOWN
+    assert vault.currently_sealed_dataset_ids(shard_ledger) == frozenset()  # no longer "sealed"
+    assert vault.withheld_dataset_ids(shard_ledger) == frozenset({"d-1"})  # still withheld, though
+
+    # permanence: no further lifecycle transition can ever claim it again -- the EXISTING
+    # single-shot guards refuse it automatically (module docstring next to STATE_EXPOSURE_UNKNOWN).
+    with pytest.raises(vault.ShardLifecycleOrderError):
+        vault.assign_shard(
+            shard_ledger, dataset_id="d-1", family_root_id="root", symbol="PG",
+            session_date="2026-06-09",
+        )
+    with pytest.raises(vault.ShardLifecycleOrderError):
+        vault.seal_shard(
+            shard_ledger, dataset_id="d-1", universe_id="u1", content_checksum="c" * 64,
+            event_count=1, vault_secret=_FIXTURE_SECRET,
+        )
+
+
+def test_tc5_a_wrong_nonempty_reconstruction_is_also_refused_never_treated_as_proven(tmp_path):
+    """TC-5's other failure shape: a SUPPLIED but WRONG suffix (not merely an empty one) must
+    ALSO fail the hash-attested completeness check and fall to the same conservative
+    exposure_unknown path -- proving `recover_shard_ledger` actually verifies the reconstruction
+    byte-for-byte rather than trusting that the caller supplied SOMETHING."""
+    vault_dir = str(tmp_path / "vault")
+    shard_ledger = vault.VaultShardLedger(vault_dir)
+    _seal_two_shards(shard_ledger)
+    _truncate_ledger_tail(shard_ledger)  # loses d-2's own seal row
+    verify_result = shard_ledger.verify_chain()
+
+    recovery_ledger = vault.VaultRecoveryLedger(vault_dir)
+    # a PLAUSIBLE-LOOKING but WRONG guess -- right shape, wrong content (a different checksum than
+    # d-2 actually had) -- never a byte-for-byte match of what was truly lost.
+    wrong_guess = {
+        "dataset_id": "d-2", "content_checksum": "f" * 64, "shard_id": "vshard-wrong-guess",
+        "universe_id": "u1", "checksum_commitment": "wrong-commitment", "size_bucket": "~10^2",
+        "sealed_at": "2026-06-09T00:00:00.000000Z", "exposure_state": vault.STATE_SEALED,
+        "family_root_id": None, "symbol": None, "session_date": None,
+        "assigned_at": None, "exposed_at": None,
+    }
+    outcome = vault.recover_shard_ledger(
+        shard_ledger, verify_result=verify_result, reconstructed_suffix=[wrong_guess],
+        sources=[{"source": "a-wrong-guess", "sha256": "irrelevant"}],
+        operator_identity="test-operator", reason="unit test TC-5 (wrong guess)",
+        recovery_ledger=recovery_ledger, incident_id="incident-tc5-wrong",
+        quarantine_dir=str(tmp_path / "quarantine"),
+    )
+    # refused exactly like the empty-suffix case -- a wrong guess is not "proven complete".
+    assert outcome["ok"] is False
+    assert outcome["exposure_unknown_dataset_ids"] == ["d-1"]  # d-2 still could not be NAMED
+
+    state = vault.build_vault_state(shard_ledger, vault.VaultUniverseLedger(vault_dir))
+    (entry,) = state["shards"]  # the WRONG guess's row was never written -- only d-1 exists
+    assert entry["exposure_state"] == vault.STATE_EXPOSURE_UNKNOWN
+    assert "vshard-wrong-guess" not in json.dumps(state)  # the rejected guess never entered the ledger
+
+    recovery_rows = recovery_ledger.all_rows()
+    assert recovery_rows[-1]["outcome"] == "incomplete"
+
+    # the incomplete recovery is on permanent record too.
+    recovery_rows = recovery_ledger.all_rows()
+    assert len(recovery_rows) == 1
+    assert recovery_rows[0]["outcome"] == "incomplete"
+    assert recovery_rows[0]["exposure_unknown_dataset_ids"] == ["d-1"]
+
+
+def test_tc5_a_shard_recovery_could_not_name_stays_protected_by_the_universe_rule_predicate(tmp_path):
+    """The other half of TC-5's safety net. ``recover_shard_ledger`` cannot even NAME ``d-2`` --
+    its own seal row was inside the unrecoverable gap -- so it is not among the ``exposure_unknown``
+    ids returned. That does NOT mean ``d-2`` is forgotten: after recovery it carries NO row at all
+    in the shard ledger, which is exactly the "untracked pool member" case
+    ``unresolved_pool_universe_by_dataset_id``'s test (b) already exists for -- if ``d-2`` was
+    recorded under a REGISTERED universe's rule, that predicate independently re-catches it, with
+    no reliance on the shard ledger's own (now-incomplete) memory of it."""
+    vault_dir = str(tmp_path / "vault")
+    shard_ledger = vault.VaultShardLedger(vault_dir)
+    universe_ledger = vault.VaultUniverseLedger(vault_dir)
+    vault.register_universe(
+        universe_ledger, universe_id="u1", symbol_rule=["PG", "AAPL"],
+        date_rule=["2026-06-08", "2026-06-09"],
+        vault_secret_commitment=vault.commit_vault_secret(_FIXTURE_SECRET),
+    )
+    _seal_two_shards(shard_ledger)  # d-1, then d-2 -- d-2's own row will be the one lost
+    _truncate_ledger_tail(shard_ledger)
+    verify_result = shard_ledger.verify_chain()
+
+    recovery_ledger = vault.VaultRecoveryLedger(vault_dir)
+    outcome = vault.recover_shard_ledger(
+        shard_ledger, verify_result=verify_result, reconstructed_suffix=[],
+        sources=[], operator_identity="test-operator", reason="unit test TC-5 (b)",
+        recovery_ledger=recovery_ledger, incident_id="incident-tc5b",
+        quarantine_dir=str(tmp_path / "quarantine"),
+    )
+    assert outcome["exposure_unknown_dataset_ids"] == ["d-1"]  # d-2 could not even be NAMED
+
+    # d-2 (recorded AFTER u1's registration, matching its rule) is still caught -- test (b).
+    withheld = vault.unresolved_pool_universe_by_dataset_id(
+        shard_ledger, universe_ledger,
+        [("d-2", "AAPL", "2026-06-09", "2027-01-01T00:00:00.000000Z")],
+    )
+    assert withheld.get("d-2") == "u1"
+
+
+# --- TR-27/TC-6/TC-8: the nonced commitment -- dictionary-attack resistance ------------------------
+
+
+def test_tc8_a_dictionary_attack_cannot_verify_the_commitment_without_the_nonce(tmp_path):
... [diff_bound] apps/backend/tests/test_vault.py: 238 more diff lines omitted — Read the file for full detail
```

## Excluded-path stat (dependency/lockfile visibility)

 runs/goal-session-rapid-microscope/telemetry.jsonl   | 6 ++++++
 runs/goal-session-rapid-microscope/trace/trace.jsonl | 1 +
 2 files changed, 7 insertions(+)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
