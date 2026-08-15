# Iteration diff (bounded)

Files changed: 10. Shown in full: 8.

**Truncated** (over the line caps; tail omitted, noted inline or fully skipped):
- `apps/backend/tests/test_pnl_scan.py` (503 lines not shown)
- `apps/backend/tests/test_referee_adjudicate.py` (42 lines not shown)

```diff
diff --git a/apps/backend/app/research/pnl_scan.py b/apps/backend/app/research/pnl_scan.py
index 7b78f4d..df9902c 100644
--- a/apps/backend/app/research/pnl_scan.py
+++ b/apps/backend/app/research/pnl_scan.py
@@ -113,6 +113,25 @@ branch alongside the profile axis above, never a refactor of it.
     reported edge for one measured under a tighter crossing rule. A static, config-independent string
     — present on every report, on every axis — so it never perturbs the byte-identical-rerun
     guarantee.
+
+era-6 "The Referee" J-08 — the promotion interlock (spec Sec8): the ONE deliberate exception the
+goal-6 constitution names to "every KEPT surface stays byte-identical" — ``_promote`` now consults
+``referee_adjudicate.authorize_promotion`` BEFORE ``append_validation_row`` (the ledger-row-first /
+pointer-second write order is UNCHANGED after authorization — authorization gates whether that
+sequence starts at all, never reorders it). Sweep computation, candidate evaluation, and survivor
+labelling are entirely unaffected — a candidate can be ``survivor: true`` and still, honestly,
+``promotion_eligible: false``. ``run_sweep``/``_promote`` gain ONE new required parameter,
+``certificate_store`` (a ``CertificateStore`` handle — REQUIRED, never optional, so the interlock can
+never be silently skipped by omission); ``main()`` resolves the operator's real one the SAME way
+``referee_adjudicate.py``'s own CLI does (``resolve_referee_registry_dir``). ``live_scan_context`` —
+``{champion_identity, train_dataset, holdout_dataset, config_fingerprint, gate_version,
+referee_parameters_hash}`` — is built FRESH from this run's own values every time, never cached, never
+caller-overridable; ``train_dataset``/``holdout_dataset`` are narrowed to exactly ``{id, checksum,
+split}`` (spec Sec8's own certificate shape) via ``_dataset_pin`` so a certificate's pins and a live
+scan's pins are directly, byte-comparably equal. NO bypass flag, environment override, or
+default-allow path exists anywhere in this chain (source-scan guard-tested,
+``test_no_bypass_path_exists_for_authorize_promotion``) — a certificate is either on file and
+matching, or promotion is refused with a distinct, honest ``refusal_class``.
 """
 
 from __future__ import annotations
@@ -128,6 +147,8 @@ from .backtests import BacktestJobManager, REGISTER, STATUS_DONE
 from .bars import BarStore
 from .datasets import DatasetStore, SPLIT_HOLDOUT, SPLIT_TRAIN
 from .pnl_ledger import LedgerCompositionError, append_validation_row
+from .referee_adjudicate import REFEREE_GATE_VERSION, authorize_promotion, referee_parameters_hash
+from .referee_registry import CertificateStore, resolve_referee_registry_dir
 from .store import DuplicateEnhancementError, JournalStore
 
 __all__ = ["ScanError", "run_sweep", "main"]
@@ -263,6 +284,14 @@ def _is_positive(aggregate: dict) -> bool:
     return aggregate["delta_net_r"] > 0 and aggregate["delta_net_usd"] > 0
 
 
+def _dataset_pin(dataset_meta: dict) -> dict:
+    """The exact ``{id, checksum, split}`` shape spec Sec8's certificate pins (and
+    ``live_scan_context`` below) carry for a dataset — narrowed off the full, richer
+    ``DatasetStore`` metadata dict so a certificate's OWN pin and a live scan's own pin are
+    directly, byte-comparably equal (never a superset vs. a subset that "happen" to overlap)."""
+    return {"id": dataset_meta["id"], "checksum": dataset_meta["checksum"], "split": dataset_meta["split"]}
+
+
 def _promote(
     store: JournalStore,
     config: Config,
@@ -275,6 +304,7 @@ def _promote(
     holdout_datasets: list[dict],
     train_rows: list[dict],
     holdout_rows: list[dict],
+    certificate_store: CertificateStore,
 ) -> dict:
     """Promote a genuine hold-out survivor: append ONE PnL-ledger row (the EXISTING single
     writer) THEN move the persisted champion pointer — in that crash-safe order (see the module
@@ -287,7 +317,12 @@ def _promote(
     pair the winning candidate's OWN backtests ran at — the profile axis passes
     ``(champion['strategy_id'], candidate_id)`` (unchanged); the strategy axis passes
     ``(candidate_id, PROFILE_DEFAULT)``. Either way the pointer moves to precisely what was
-    measured — never a third, re-derived pair."""
+    measured — never a third, re-derived pair.
+
+    era-6 J-08: with EXACTLY one train/hold-out dataset registered, ``authorize_promotion`` is
+    consulted BEFORE ``append_validation_row`` — a valid, candidate-specific Referee certificate
+    is REQUIRED or nothing is written and nothing moves (fail closed; no bypass of any kind).
+    ``live_scan_context`` is built FRESH from this run's own values every call, never cached."""
     if len(train_datasets) != 1 or len(holdout_datasets) != 1:
         return {
             "candidate_id": candidate_id,
@@ -297,7 +332,31 @@ def _promote(
                 f"registered — automatic promotion requires exactly one of each (the existing "
                 f"ledger writer's shape); nothing was promoted this run"
             ),
+            "promotion_eligible": None,
+            "refusal_class": None,
+            "reason": None,
+        }
+
+    live_scan_context = {
+        "champion_identity": champion,
+        "train_dataset": _dataset_pin(train_datasets[0]),
+        "holdout_dataset": _dataset_pin(holdout_datasets[0]),
+        "config_fingerprint": config.config_fingerprint(),
+        "gate_version": REFEREE_GATE_VERSION,
+        "referee_parameters_hash": referee_parameters_hash(),
+    }
+    candidate = {"strategy_id": new_strategy_id, "profile": new_profile}
+    authorization = authorize_promotion(candidate, certificate_store, live_scan_context)
+    if not authorization["authorized"]:
+        return {
+            "candidate_id": candidate_id,
+            "promoted": False,
+            "note": None,
+            "promotion_eligible": False,
+            "refusal_class": authorization["refusal_class"],
+            "reason": authorization["reason"],
         }
+
     enhancement_id = f"{candidate_id}-over-{champion['strategy_id']}-{champion['profile']}"
     title = (
         f"candidate '{candidate_id}' over champion "
@@ -324,7 +383,14 @@ def _promote(
     # The ledger row is now durably committed — safe to move the pointer. A crash AFTER this
     # point leaves a correctly-attributed ledger row and a moved pointer: fully consistent.
     store.set_champion_pointer(strategy_id=new_strategy_id, profile=new_profile, wall_ts=time.time())
-    return {"candidate_id": candidate_id, "promoted": True, "enhancement_id": enhancement_id}
+    return {
+        "candidate_id": candidate_id,
+        "promoted": True,
+        "enhancement_id": enhancement_id,
+        "promotion_eligible": True,
+        "refusal_class": None,
+        "reason": None,
+    }
 
 
 # --- the ONE computer of Data Contract row 36 --------------------------------------------------
@@ -337,6 +403,7 @@ def run_sweep(
     *,
     candidate_strategy_id: str | None = None,
     bar_store: BarStore | None = None,
+    certificate_store: CertificateStore,
 ) -> dict:
     """Run the full candidate sweep ONCE. Returns the complete report dict — the SAME shape
     persisted to ``--out`` (the CLI is a thin wrapper). A genuine hold-out survivor is promoted
@@ -355,7 +422,13 @@ def run_sweep(
         champion's CURRENT ``strategy_id`` (never hardcoded), also at ``profile=PROFILE_DEFAULT``.
 
     ``bar_store`` (era-4 J-04's row-39 level source) is threaded through every backtest this run
-    makes, on either axis — ``v1`` ignores it; only a ``structure_tape`` run ever reads it."""
+    makes, on either axis — ``v1`` ignores it; only a ``structure_tape`` run ever reads it.
+
+    ``certificate_store`` (era-6 J-08) is REQUIRED — never optional, never defaulted — so the
+    promotion interlock can never be silently skipped by omission (an accidentally-missing
+    argument is a loud ``TypeError`` at the call site, not a silent bypass). Sweep computation,
+    candidate evaluation, and survivor labelling never touch it; only ``_promote`` does, and only
+    once a genuine hold-out survivor is found."""
     champion = store.get_champion_pointer()
     jobs = BacktestJobManager(store, config)
 
@@ -458,6 +531,7 @@ def run_sweep(
                 holdout_datasets=holdout_datasets,
                 train_rows=train_rows,
                 holdout_rows=holdout_rows,
+                certificate_store=certificate_store,
             )
 
     return {
@@ -514,10 +588,15 @@ def main() -> int:
     try:
         dataset_store = DatasetStore(config.dataset_dir_resolved())
         bar_store = BarStore(config.bar_dir_resolved())
+        # era-6 J-08: the SAME resolved registry directory referee_adjudicate.py's own CLI/routes
+        # read/write (TAPEOLOGY_DESK_REFEREE_REGISTRY_DIR or the sibling-of-universe-dir default)
+        # — never a second, independently-resolved certificate location.
+        certificate_store = CertificateStore(resolve_referee_registry_dir(config.desk_universe_dir_resolved()))
         try:
             report = run_sweep(
                 store, dataset_store, config,
                 candidate_strategy_id=args.strategy, bar_store=bar_store,
+                certificate_store=certificate_store,
             )
         except ScanError as exc:
             print(f"error: {exc}", file=sys.stderr)
diff --git a/apps/backend/app/research/referee_adjudicate.py b/apps/backend/app/research/referee_adjudicate.py
index f93649d..b282a71 100644
--- a/apps/backend/app/research/referee_adjudicate.py
+++ b/apps/backend/app/research/referee_adjudicate.py
@@ -102,9 +102,11 @@ from .bars import BarStore
 from .desk_playbook import PlaybookStore, resolve_desk_playbook_dir
 from .desk_playbook_features import side_sign
 from .referee_evidence import (
+    REFEREE_FORMING_BAR_BASIS_CAVEAT,
     _epoch_from_iso,
     current_playbook_detector_basis,
     playbook_observations,
+    strategy_observations,
 )
 from .referee_null import (
     REFEREE_NULL_CONTEXT_SPEC_ID,
@@ -113,12 +115,21 @@ from .referee_null import (
     _locate_measurement_series,
     _measure_one_anchor,
     _parse_observation_id,
+    null_context_spec_parameters,
     null_context_spec_signature,
+    null_tod_spec_parameters,
     null_tod_spec_signature,
     resolve_occurrence_backing_bucket,
     resolve_referee_null_dir,
+    test_perm_spec_parameters,
+)
+from .referee_registry import (
+    CertificateAlreadyRecorded,
+    CertificateStore,
+    FamilyStore,
+    HypothesisStore,
+    resolve_referee_registry_dir,
 )
-from .referee_registry import FamilyStore, HypothesisStore, resolve_referee_registry_dir
 from .referee_stats import (
     INSUFFICIENT_SAMPLE,
     REFEREE_B,
@@ -130,17 +141,22 @@ from .referee_stats import (
     bootstrap_ci_occurrence,
     equal_weight_t,
     permutation_test,
+    referee_stats_parameters,
     run_oracle_attestation,
     sign_flip_result,
     verify_oracle_attestation,
 )
 from .routes import get_bar_store
+from .store import JournalStore
 
 __all__ = [
     "REFEREE_GATE_VERSION",
     "REFEREE_REGISTER",
+    "REFEREE_STRATEGY_NULL_DESIGN_CAVEAT",
     "resolve_referee_eval_dir",
     "resolve_referee_eval_log_dir",
+    "referee_parameters",
+    "referee_parameters_hash",
     "EvaluationIntegrityError",
     "EvaluationAlreadyRecorded",
     "SnapshotAlreadyRecorded",
@@ -178,6 +194,53 @@ _EVAL_LOG_DIR_ENV = "TAPEOLOGY_DESK_REFEREE_EVAL_LOG_DIR"
 
 _ESTIMANDS_AGAINST_NULL = frozenset({"A", "C"})
 
+# goal-referee-iter-9 (J-08 Step 1, spec Sec3.7/Sec9 item 6): the strategy family's own null-design
+# disclosure -- served once per strategy-family evaluation record (``provenance.basis_caveats``,
+# alongside the Card-6.4 ``REFEREE_FORMING_BAR_BASIS_CAVEAT`` every strategy_trade observation
+# already carries), stated rather than hidden, exactly as the spec's own assumption ledger names
+# it. A static, config-independent string -- never wall-clock or per-run-random.
+REFEREE_STRATEGY_NULL_DESIGN_CAVEAT: str = (
+    "the strategy family's recorded random_null baseline is 100 uniform-random-timed entries per "
+    "backtest report (backtests.py's own seeded null baseline), not count- or time-of-day-matched "
+    "to the candidate strategy's own entries -- a materially weaker null than the Playbook family's "
+    "matched-anchor design (docs/referee-statistical-spec.md Sec3.7, Sec9 item 6). Card 6.6's "
+    "strategy-matched nulls remain future work, gated on the tick library."
+)
+
+
+# === spec Sec1's own aggregator: referee_parameters() ================================================
+#
+# "Every constant [Sec1's table] is read at call time by referee_parameters(), embedded verbatim in
+# every referee record, and hashed into that record's identity. A monkeypatched constant must move
+# the parameters AND the identity (counter-tested)." This module is the natural home: it already
+# defines REFEREE_GATE_VERSION and already imports every OTHER module's own existing `_parameters()`
+# stub (referee_stats_parameters, null_tod_spec_parameters, null_context_spec_parameters,
+# test_perm_spec_parameters) -- combined here ONCE rather than re-derived per caller, closing the
+# goal.md IN SCOPE bullet: "combines every referee module's existing `_parameters()` stub (stats,
+# null specs, test spec) plus REFEREE_GATE_VERSION into one dict, hashed once, read at call time."
+
+
+def referee_parameters() -> dict:
+    """Every referee module's own pre-registered constants, in one dict, read fresh at call time
+    (never cached) -- Parameters discipline: a test that monkeypatches ANY constant reachable from
+    the four stub calls below moves this dict's own return value (and therefore
+    ``referee_parameters_hash()``'s), never silently leaving a stale parameters identity behind."""
+    return {
+        "gate_version": REFEREE_GATE_VERSION,
+        "stats": referee_stats_parameters(),
+        "null_tod": null_tod_spec_parameters(),
+        "null_context": null_context_spec_parameters(),
+        "test_perm": test_perm_spec_parameters(),
+    }
+
+
+def referee_parameters_hash() -> str:
+    """``referee_parameters()``'s own content hash -- the ``referee_parameters_hash`` pin every
+    strategy-family certificate and ``authorize_promotion``'s ``live_scan_context`` carry (spec
+    Sec8; goal.md J-08 Step 2/3). Read at call time, exactly like ``referee_parameters()`` itself,
+    so a monkeypatched constant moves both together (TC-14)."""
+    return _sha256(_canonical(referee_parameters()))[:16]
+
 
 def resolve_referee_eval_dir(desk_universe_dir_resolved: str) -> str:
     """The evaluation + adjudication-snapshot stores' SHARED directory (two record kinds,
@@ -452,6 +515,66 @@ def _pool_for_estimand(
     return _pool_cell_vs_complement(occurrences, hypothesis, context_resolver)
 
 
+# === J-08 Step 1: the strategy-family analog pooling (spec Sec3.7) ====================================
+
+
+def _pool_strategy_trades(journal_store: JournalStore) -> dict:
+    """The strategy-family analog of ``_pool_against_null`` (spec Sec3.7: "Cluster = dataset. Per
+    dataset d with >=1 candidate trade: Delta_d = mean(candidate net_r in d) - mean(recorded
+    random_null net_r in d)") -- reuses ``referee_evidence.strategy_observations()`` verbatim
+    (never a second join of trades to dataset identity) and groups by ``cluster_key`` = dataset id
+    (never ``session_date``, TC-9). Shaped IDENTICALLY to ``_pool_against_null``'s own return dict
+    so ``run_evaluation_and_record`` reuses every downstream step (coverage, permutation test,
+    both bootstrap CIs, BH, snapshot) with zero branching beyond the POOLING call itself.
+
+    ``occurrence_diffs`` is honestly ``None`` (``_pool_cell_vs_complement``'s own "not defined at
+    occurrence level" precedent, not ``_pool_against_null``'s occurrence-diff list): unlike
+    estimand A/C's ToD-matched null (exactly ``K`` anchors per occurrence, a natural per-occurrence
+    pairing), a candidate trade has no single designated partner among a dataset's ``random_null``
+    trades (``backtest_null_entry_count`` uniform-random draws per report, spec Sec9 item 6) --
+    only the DATASET-clustered ``Delta_d`` is spec-defined. Recorded as an explicit design choice
+    (T-1), not a silent gap: it structurally disables ``bootstrap_ci_occurrence``/the entry-basis
+    sensitivity for strategy-family evaluations (both already gated on non-empty
+    ``occurrence_diffs``/``_ESTIMANDS_AGAINST_NULL`` in ``run_evaluation_and_record``), which is
+    correct here -- there is no occurrence-level uncertainty quantity to disclose."""
+    obs = strategy_observations(journal_store)
+    by_cluster_candidate: dict[str, list[float]] = {}
+    by_cluster_null: dict[str, list[float]] = {}
+    observation_ids_by_cluster: dict[str, set[str]] = {}
+    for observation in obs["observations"]:
+        cluster_key = observation["cluster_key"]
+        by_cluster_candidate.setdefault(cluster_key, []).append(observation["value"])
+        observation_ids_by_cluster.setdefault(cluster_key, set()).add(observation["observation_id"])
+    for observation in obs["null_observations"]:
+        by_cluster_null.setdefault(observation["cluster_key"], []).append(observation["value"])
+
+    all_clusters = set(by_cluster_candidate) | set(by_cluster_null)
+    session_groups: dict[str, tuple[list[float], list[float]]] = {}
+    one_group_excluded = 0
+    for cluster_key in all_clusters:
+        candidate_values = by_cluster_candidate.get(cluster_key, [])
+        null_values = by_cluster_null.get(cluster_key, [])
+        if candidate_values and null_values:
+            session_groups[cluster_key] = (candidate_values, null_values)
+        else:
+            one_group_excluded += 1
+
+    observation_ids: set[str] = set()
+    for cluster_key in session_groups:
+        observation_ids |= observation_ids_by_cluster.get(cluster_key, set())
+
+    return {
+        "session_groups": session_groups,
+        "occurrence_diffs": None,
+        "occurrences_pooled": len(observation_ids),
+        "one_group_sessions_excluded": one_group_excluded,
+        "informative_sessions": len(session_groups),
+        "observation_ids": observation_ids,
+        "null_record_ids": set(),
+        "by_session": {},
+    }
+
+
 # === the entry-basis sensitivity (spec Sec4.3; A/C only) ==============================================
 
 
@@ -926,6 +1049,72 @@ def _build_and_record_snapshot(
         return existing
 
 
+# === J-08 Step 2: the certificate's REAL mint call site (spec Sec8) ===================================
+
+
+def _mint_strategy_certificate(
+    *,
+    hypothesis: dict,
+    recorded: dict,
+    snapshot: dict,
+    candidate: dict,
+    champion_identity_at_scan_time: dict,
+    train_dataset: dict,
+    holdout_dataset: dict,
+    certificate_store: CertificateStore,
+) -> dict | None:
+    """Mints ONE certificate record (spec Sec8) for a strategy-family hypothesis's own freshly
+    recorded, gate-passing confirmatory checkpoint -- called ONLY from
+    ``run_evaluation_and_record``'s own fresh-compute path (never a hand-written or fixture path
+    in production code), and only when its caller explicitly supplied ``certificate_mint`` (the
+    live scan identity this certificate is meant to authorize -- a hypothesis record alone names
+    no ``(strategy_id, profile)`` candidate, no champion, and no train/holdout dataset pair, so
+    this function cannot derive them; the caller, which DOES know which live ``pnl_scan`` run this
+    mint is for, supplies them verbatim).
+
+    Refuses (returns ``None``, mints nothing) unless the attestation RE-verifies (T-8, never
+    trusted from the stored ``passed`` flag) -- the exact gate ``_snapshot_fold``/
+    ``_build_and_record_snapshot`` already enforce, read here from the just-built
+    ``recorded``/``snapshot`` rather than re-derived a second way. ``gate_results.bh_pass`` is the
+    family BH pass ``snapshot["bh"]["bh_pass"]`` already computed; ``floors_met`` is
+    ``recorded["confirmatory_eligible"]`` (the SAME floor check that gated this evaluation into
+    ``role == "checkpoint"`` in the first place -- served explicitly on the certificate so
+    ``authorize_promotion`` never has to re-derive it from a foreign evaluation record). A
+    re-mint attempt for an identical ``(hypothesis_id, evaluation_basis, candidate)`` key -- e.g. a
+    caller retrying after a crash between this write and its own follow-up -- returns the
+    ALREADY-recorded certificate rather than raising (append-only idempotence, the
+    ``HypothesisStore``/``NullStore`` precedent elsewhere in this era)."""
+    if not verify_oracle_attestation(recorded.get("attestation")):
+        return None
+    ci_cluster = recorded.get("ci_cluster")
+    ci = ci_cluster if isinstance(ci_cluster, list) else None
+    certificate_id = _sha256(
+        _canonical([hypothesis["hypothesis_id"], recorded["evaluation_basis"], candidate])
+    )[:16]
+    fields = {
+        "certificate_id": certificate_id,
+        "candidate": dict(candidate),
+        "champion_identity_at_scan_time": dict(champion_identity_at_scan_time),
+        "train_dataset": dict(train_dataset),
+        "holdout_dataset": dict(holdout_dataset),
+        "config_fingerprint": recorded["provenance"]["config_fingerprint"],
+        "gate_version": REFEREE_GATE_VERSION,
+        "referee_parameters_hash": referee_parameters_hash(),
+        "family_id": hypothesis["family_id"],
+        "hypothesis_id": hypothesis["hypothesis_id"],
+        "gate_results": {
+            "calibrated_p": recorded["permutation_p"],
+            "bh_pass": snapshot["bh"]["bh_pass"],
+            "ci": ci,
+            "floors_met": recorded["confirmatory_eligible"],
+        },
+    }
+    try:
+        return certificate_store.record(fields)
+    except CertificateAlreadyRecorded:
+        return certificate_store.get(certificate_id)
+
+
 # === the compute walker: ONE evaluation act, start to finish ==========================================
 
 
@@ -943,14 +1132,33 @@ def run_evaluation_and_record(
     progress: Callable[[dict], None] | None = None,
     should_abort: Callable[[], bool] | None = None,
     run_store: RefereeEvaluationRunStore | None = None,
+    journal_store: JournalStore | None = None,
+    certificate_mint: dict | None = None,
 ) -> dict:
     """Runs ONE evaluation act for ``hypothesis_id`` (spec Sec3/Sec5) and records it -- resumable
     (TC-34: an unchanged store reuses the existing record under the exact ``evaluation_basis`` key,
     computing nothing new) and cancel-safe (``should_abort`` is checked before every named phase, so
     a cancel writes NO partial evaluation record, TC-33). Returns
-    ``{"cancelled": bool, "record": dict|None, "snapshot": dict|None, "reused": bool}``. Raises
-    ``ValueError`` for an unknown ``hypothesis_id`` (surfaced by the caller -- the CLI lets it
-    propagate; the route validates first and never reaches this function for one)."""
+    ``{"cancelled": bool, "record": dict|None, "snapshot": dict|None, "reused": bool,
+    "certificate": dict|None}``. Raises ``ValueError`` for an unknown ``hypothesis_id`` (surfaced
+    by the caller -- the CLI lets it propagate; the route validates first and never reaches this
+    function for one).
+
+    ``journal_store`` (goal-referee-iter-9, J-08 Step 1) is consulted ONLY for a
+    ``hypothesis["evidence_family"] == "strategy"`` hypothesis (the playbook path never touches
+    it) -- required for that branch to pool anything; ``None`` (the default -- every EXISTING
+    playbook-only caller is unaffected) makes a strategy-family evaluation pool an honest empty
+    corpus rather than raise.
+
+    ``certificate_mint`` (J-08 Step 2) is the CALLER's own live scan identity -- this function has
+    no way to derive "which pnl_scan run this certificate should authorize" from a hypothesis
+    record alone. ``None`` (the default -- every route/CLI caller today) mints nothing, matching
+    goal.md's own "no strategy certificate can honestly exist this era" (fixture-only, reachable
+    only by a caller that explicitly supplies one). When supplied, shaped
+    ``{"candidate": {"strategy_id": str, "profile": str}, "champion_identity_at_scan_time": dict,
+    "train_dataset": dict, "holdout_dataset": dict, "certificate_store": CertificateStore}`` -- see
+    ``_mint_strategy_certificate``, consulted ONLY at a FRESH strategy-family checkpoint (never on
+    the dedup/reused path)."""
     started_at = _iso_utc_now()
 
     def _log(*, state: str, done: int, total: int, error: str | None) -> None:
@@ -986,15 +1194,31 @@ def run_evaluation_and_record(
     try:
         config_fingerprint = config.config_fingerprint()
         estimand = hypothesis["estimand"]
-        context_resolver = (
-            BandMapResolver(bar_store, config, compute=False) if estimand in ("B", "C") else None
-        )
-        occurrences, _record_cache = _eligible_setup_side_occurrences(
-            hypothesis, playbook_store, config_fingerprint
-        )
-        pool = _pool_for_estimand(
-            hypothesis, occurrences, null_store=null_store, context_resolver=context_resolver
-        )
+        evidence_family = hypothesis["evidence_family"]
+        if evidence_family == "strategy":
+            # J-08 Step 1 (spec Sec3.7): the strategy-family analog -- cluster = dataset, never
+            # session_date (``_pool_strategy_trades``, never ``_pool_for_estimand``'s playbook-only
+            # occurrence gather). ``journal_store=None`` (no production caller reaches this branch
+            # without one this era) pools an honest empty corpus rather than raise.
+            pool = (
+                _pool_strategy_trades(journal_store)
+                if journal_store is not None
+                else {
+                    "session_groups": {}, "occurrence_diffs": None, "occurrences_pooled": 0,
+                    "one_group_sessions_excluded": 0, "informative_sessions": 0,
+                    "observation_ids": set(), "null_record_ids": set(), "by_session": {},
+                }
+            )
+        else:
+            context_resolver = (
+                BandMapResolver(bar_store, config, compute=False) if estimand in ("B", "C") else None
+            )
+            occurrences, _record_cache = _eligible_setup_side_occurrences(
+                hypothesis, playbook_store, config_fingerprint
+            )
+            pool = _pool_for_estimand(
+                hypothesis, occurrences, null_store=null_store, context_resolver=context_resolver
+            )
         _tick()
 
         coverage = {
@@ -1042,7 +1266,13 @@ def run_evaluation_and_record(
             elif existing["role"] == "checkpoint":
                 snapshot = snapshot_store.get_for_hypothesis(hypothesis_id)
             _log(state="completed", done=total_units, total=total_units, error=None)
-            return {"cancelled": False, "record": existing, "snapshot": snapshot, "reused": True}
+            # No mint attempt on the dedup/reused path (goal-referee-iter-9): a certificate mints
+            # only at the hypothesis's ONE fresh checkpoint compute, below -- a re-run over an
+            # unchanged store is by definition not that fresh compute.
+            return {
+                "cancelled": False, "record": existing, "snapshot": snapshot, "reused": True,
+                "certificate": None,
+            }
 
         if _aborted():
             _log(state="cancelled", done=done_units, total=total_units, error=None)
@@ -1081,6 +1311,13 @@ def run_evaluation_and_record(
             "attestation": None,
             "provenance": {"config_fingerprint": config_fingerprint, "computed_at": _iso_utc_now()},
         }
+        if evidence_family == "strategy":
+            # spec Sec3.7/Sec9 item 6 + goal.md J-08 Step 1: the Card-6.4 forming-bar caveat
+            # (already stamped per-observation by `_strategy_observation`) plus the null-design
+            # disclosure, served ONCE per evaluation record rather than re-served per observation.
+            fields["provenance"]["basis_caveats"] = [
+                REFEREE_FORMING_BAR_BASIS_CAVEAT, REFEREE_STRATEGY_NULL_DESIGN_CAVEAT,
+            ]
 
         if _aborted():
             _log(state="cancelled", done=done_units, total=total_units, error=None)
@@ -1168,6 +1405,7 @@ def run_evaluation_and_record(
         raise
 
     snapshot = None
+    certificate = None
     if recorded["role"] == "checkpoint":
         try:
             snapshot = _build_and_record_snapshot(
@@ -1177,9 +1415,24 @@ def run_evaluation_and_record(
         except Exception as exc:  # noqa: BLE001
             _log(state="failed", done=done_units, total=total_units, error=str(exc))
             raise
+        # J-08 Step 2 (spec Sec8): the certificate's REAL mint call site -- reachable ONLY through
+        # this fresh-compute path, and only for a strategy-family hypothesis whose caller supplied
+        # its own live scan identity (TC-11/TC-12: a Playbook checkpoint or an unsupplied
+        # `certificate_mint` mints nothing).
+        if evidence_family == "strategy" and certificate_mint is not None:
+            try:
+                certificate = _mint_strategy_certificate(
+                    hypothesis=hypothesis, recorded=recorded, snapshot=snapshot, **certificate_mint,
+                )
+            except Exception as exc:  # noqa: BLE001
+                _log(state="failed", done=done_units, total=total_units, error=str(exc))
+                raise
 
     _log(state="completed", done=total_units, total=total_units, error=None)
-    return {"cancelled": False, "record": recorded, "snapshot": snapshot, "reused": False}
+    return {
+        "cancelled": False, "record": recorded, "snapshot": snapshot, "reused": False,
+        "certificate": certificate,
+    }
 
 
 # === the single-flight-per-hypothesis compute manager ==================================================
diff --git a/apps/backend/app/research/referee_registry.py b/apps/backend/app/research/referee_registry.py
index b71d115..9c12276 100644
--- a/apps/backend/app/research/referee_registry.py
+++ b/apps/backend/app/research/referee_registry.py
@@ -130,7 +130,9 @@ from .referee_null import (
 __all__ = [
     "REFEREE_MIN_SESSIONS",
     "REFEREE_MIN_OCCURRENCES",
+    "REFEREE_DEFAULT_Q",
     "REFEREE_HYPOTHESIS_ORIGIN",
+    "REFEREE_STARTER_FAMILY_ID",
     "REFEREE_STARTER_FAMILY_SHORTLIST",
     "resolve_referee_registry_dir",
     "RegistryIntegrityError",
@@ -159,6 +161,16 @@ __all__ = [
 REFEREE_MIN_SESSIONS: int = 12
 REFEREE_MIN_OCCURRENCES: int = 12
 
+# goal-referee-iter-9 rider (closes the iter-8 coherence-audit F1 WARN): spec Sec1's own pinned
+# default BH q -- previously only an UNOWNED apps/frontend/app/desk/page.tsx literal
+# (REFEREE_STARTER_FAMILY_Q). Owned here, served by `shortlist_response()` below.
+REFEREE_DEFAULT_Q: float = 0.10
+
+# The starter family's own id (spec Sec7's single shared family) -- previously only an unowned
+# frontend literal (REFEREE_STARTER_FAMILY_ID in apps/frontend/app/desk/page.tsx), moved
+# backend-side this iteration (goal-referee-iter-9 rider) and served by `shortlist_response()`.
+REFEREE_STARTER_FAMILY_ID: str = "referee-starter-family"
+
 # Every hypothesis this era carries this exact origin label (goal.md: "the atlas was inspected
 # before these questions were written down") -- server-stamped, never caller-supplied.
 REFEREE_HYPOTHESIS_ORIGIN: str = "historical-exploration"
@@ -785,21 +797,49 @@ def withdraw_hypothesis(
 # === the read-side fold: GET /research/desk/referee/registry =========================================
 
 
+def _signal_matches_hypothesis_cell(
+    hypothesis: dict, signal: dict, *, context_resolver: BandMapResolver | None,
+) -> bool:
+    """goal-referee-iter-9 rider: ``True`` iff ``signal`` belongs to ``hypothesis``'s own
+    ``(setup_id, side[, context_predicate])`` cell -- the SAME context_predicate/backing-bucket
+    check ``_starter_context_readiness`` already applies for the shortlist's own live readiness,
+    now shared by BOTH ``_hypothesis_accrual`` and ``_hypothesis_discovery`` below (one helper,
+    never two independently-drifting pooling walks) so a B/C hypothesis's registry-row numbers
+    agree with its own shortlist row's live readiness for the identical cell. Estimand A
+    (``context_predicate`` is ``None``) is a plain ``(setup_id, side)`` match, unchanged from
+    before this rider. A B/C hypothesis whose context cannot be resolved at all (no
+    ``context_resolver`` supplied, or the signal's own band map cannot be resolved) is honestly
+    EXCLUDED, never assumed a match (T-5)."""
+    if signal["setup_id"] != hypothesis["setup_id"] or signal["side"] != hypothesis["side"]:
+        return False
+    context_predicate = hypothesis.get("context_predicate")
+    if context_predicate is None:
+        return True
+    if context_resolver is None:
+        return False
+    cell = resolve_occurrence_backing_bucket(
+        signal, signal["symbol"], _epoch_from_iso(signal["trigger_ts"]),
+        signal.get("entry"), hypothesis["side"], context_resolver,
+    )
+    return cell == context_predicate["backing_bucket"]
+
+
 def _hypothesis_accrual(
     hypothesis: dict,
     newest_by_date: dict[str, dict],
     *,
     live_basis: str,
     config_fingerprint: str,
+    context_resolver: BandMapResolver | None = None,
 ) -> dict:
     """The disclosed readiness PROXY (module docstring): distinct post-boundary ``session_date``s
-    carrying >=1 observation in this hypothesis's own ``(setup_id, side)`` cell, walked against an
+    carrying >=1 observation in this hypothesis's own ``(setup_id, side[, context_predicate])``
+    cell (goal-referee-iter-9 rider: a B/C hypothesis's own context predicate now applies here
+    too, via the shared ``_signal_matches_hypothesis_cell`` helper), walked against an
     ALREADY-scanned ``newest_by_date`` map (never a second ``PlaybookStore.list()`` call --
     ``registry_response`` below scans exactly once and folds every hypothesis against that one
     scan) using the SAME shared pooling primitives ``playbook_occurrence_readiness`` itself uses."""
     boundary = hypothesis["confirmation_start_boundary"]
-    setup_id = hypothesis["setup_id"]
-    side = hypothesis["side"]
     informative_dates: set[str] = set()
     for session_date, record in newest_by_date.items():
         if session_date <= boundary:
@@ -813,7 +853,7 @@ def _hypothesis_accrual(
         ):
             continue  # T-6: pool only at the current (detector_basis, config_fingerprint)
         for signal in record["signals"]:
-            if signal["setup_id"] == setup_id and signal["side"] == side:
+            if _signal_matches_hypothesis_cell(hypothesis, signal, context_resolver=context_resolver):
                 informative_dates.add(session_date)
                 break
 
@@ -839,18 +879,20 @@ def _hypothesis_discovery(
     *,
     live_basis: str,
     config_fingerprint: str,
+    context_resolver: BandMapResolver | None = None,
 ) -> dict:
     """The ``discovery (exploratory)`` block (goal.md J-07 Step 4): pre-boundary (``session_date
-    <= confirmation_start_boundary``) observations in the hypothesis's own ``(setup_id, side)``
-    cell -- the exact COMPLEMENT of ``_hypothesis_accrual``'s own post-boundary walk, over the
-    SAME already-scanned ``newest_by_date`` map and the SAME current-basis filter (never a second
-    pooling implementation). ``state/assumptions.md`` (iter-8) rules the stale-basis exclusion
-    applies here too, for consistency with ``accrual``. Never contributes to the ``accrual``
-    block; a deep-backfilled pre-boundary record recorded AFTER registration still lands here,
-    keyed on ``session_date`` alone -- never ``recorded_at`` (TC-10)."""
+    <= confirmation_start_boundary``) observations in the hypothesis's own
+    ``(setup_id, side[, context_predicate])`` cell (goal-referee-iter-9 rider: the SAME
+    context-predicate check ``_hypothesis_accrual`` now applies, via the shared
+    ``_signal_matches_hypothesis_cell`` helper) -- the exact COMPLEMENT of ``_hypothesis_accrual``'s
+    own post-boundary walk, over the SAME already-scanned ``newest_by_date`` map and the SAME
+    current-basis filter (never a second pooling implementation). ``state/assumptions.md``
+    (iter-8) rules the stale-basis exclusion applies here too, for consistency with ``accrual``.
+    Never contributes to the ``accrual`` block; a deep-backfilled pre-boundary record recorded
+    AFTER registration still lands here, keyed on ``session_date`` alone -- never ``recorded_at``
+    (TC-10)."""
     boundary = hypothesis["confirmation_start_boundary"]
-    setup_id = hypothesis["setup_id"]
-    side = hypothesis["side"]
     n = 0
     discovery_dates: set[str] = set()
     for session_date, record in newest_by_date.items():
@@ -864,7 +906,7 @@ def _hypothesis_discovery(
         ):
             continue  # T-6: pool only at the current (detector_basis, config_fingerprint)
         for signal in record["signals"]:
-            if signal["setup_id"] == setup_id and signal["side"] == side:
+            if _signal_matches_hypothesis_cell(hypothesis, signal, context_resolver=context_resolver):
                 n += 1
                 discovery_dates.add(session_date)
     return {"n": n, "n_sessions": len(discovery_dates), "label": "discovery (exploratory)"}
@@ -878,6 +920,8 @@ def registry_response(
     certificate_store: CertificateStore,
     playbook_store: PlaybookStore,
     config_fingerprint: str,
+    bar_store: BarStore | None = None,
+    config: Config | None = None,
 ) -> dict:
     """The whole ``GET /research/desk/referee/registry`` body -- the pinned five-key shape
     (``runs/goal-session-referee/state/blueprint.md`` iter-6/iter-7/iter-8 notes): ``families``,
@@ -888,7 +932,14 @@ def registry_response(
     ``get_referee_nulls``'s own ``{"records": [...], "integrity_errors": [...]}`` disclosure
     pattern, reused here rather than inventing a second shape -- each of the four stores' own
     ``.list()`` errors is tagged with its ``store`` kind and concatenated into ONE flat list, so a
-    corrupted file is surfaced explicitly instead of silently vanishing from the response."""
+    corrupted file is surfaced explicitly instead of silently vanishing from the response.
+
+    ``bar_store``/``config`` (goal-referee-iter-9 rider) are OPTIONAL: supplied by the real route
+    so a B/C hypothesis's ``accrual``/``discovery`` can resolve its own context predicate (the
+    SAME ``compute=False`` ``BandMapResolver`` lookup ``shortlist_response`` already builds, over
+    the ALREADY-RECORDED band map, never a fresh compute, T-8); omitted, every hypothesis in this
+    era's own registered set is Estimand A (``context_predicate is None``), which never touches
+    the resolver at all -- so every EXISTING caller of this function is unaffected either way."""
     families, family_errors = family_store.list()
     hypotheses, hypothesis_errors = hypothesis_store.list()
     withdrawals, withdrawal_errors = withdrawal_store.list()
@@ -908,14 +959,21 @@ def registry_response(
     live_basis = current_playbook_detector_basis()
     records, _integrity_errors = playbook_store.list()
     newest_by_date = _newest_per_session_date(records)
+    context_resolver = (
+        BandMapResolver(bar_store, config, compute=False)
+        if bar_store is not None and config is not None
+        else None
+    )
 
     folded_hypotheses = []
     for hypothesis in hypotheses:
         accrual = _hypothesis_accrual(
-            hypothesis, newest_by_date, live_basis=live_basis, config_fingerprint=config_fingerprint
+            hypothesis, newest_by_date, live_basis=live_basis, config_fingerprint=config_fingerprint,
+            context_resolver=context_resolver,
         )
         discovery = _hypothesis_discovery(
-            hypothesis, newest_by_date, live_basis=live_basis, config_fingerprint=config_fingerprint
+            hypothesis, newest_by_date, live_basis=live_basis, config_fingerprint=config_fingerprint,
+            context_resolver=context_resolver,
         )
         status = "withdrawn" if hypothesis["hypothesis_id"] in withdrawn_ids else "active"
         folded_hypotheses.append(
@@ -1002,6 +1060,25 @@ REFEREE_STARTER_FAMILY_SHORTLIST: tuple[dict, ...] = (
             "and place"
         ),
     },
+    # goal-referee-iter-9 rider: spec Sec7's own S-4 row reads "range_trade (registered PER SIDE)
+    # at_wall vs other same-setup contexts" -- only the long side shipped at iter-8, dropped
+    # without a recorded reason (state/assumptions.md iter-9 entry rules this a plain instruction,
+    # not a human-ruling question). The short-side sibling, otherwise byte-identical to S-4
+    # (estimand B, same measure/horizon/sidedness/rationale shape), reusing
+    # `_starter_context_readiness` verbatim.
+    {
+        "candidate_id": "S-6", "estimand": "B", "evidence_family": "playbook",
+        "setup_id": "range_trade", "side": "short",
+        "context_predicate": {"backing_bucket": AT_WALL},
+        "primary_measure_key": "1h", "primary_horizon": "1h", "sidedness": "greater",
+        "null_spec_id": None, "test_spec_id": REFEREE_TEST_PERM_SPEC_ID,
+        "target_sessions": REFEREE_MIN_SESSIONS, "min_occurrences": REFEREE_MIN_OCCURRENCES,
+        "rationale": (
+            "the short-side sibling of S-4 (spec Sec7's own \"registered per side\" wording): a "
+            "range bounce plays out over the traverse toward the opposite boundary; to_close "
+            "would contaminate with post-breakout regimes"
+        ),
+    },
 )
 
 
@@ -1144,7 +1221,15 @@ def shortlist_response(
                 "projected_days_to_target": projected_days,
             }
         )
-    return {"candidates": candidates}
+    # goal-referee-iter-9 rider (closes iter-8 coherence-audit F1 WARN): `family_id`/`family_q`
+    # served here for the first time -- the starter family's own registration-mechanics fields,
+    # previously only an unowned apps/frontend/app/desk/page.tsx literal. The frontend now reads
+    # both from this response instead of a local constant.
+    return {
+        "candidates": candidates,
+        "family_id": REFEREE_STARTER_FAMILY_ID,
+        "family_q": REFEREE_DEFAULT_Q,
+    }
 
 
 # --- The CLI (register / withdraw) --------------------------------------------------------------------
diff --git a/apps/backend/app/research/referee_routes.py b/apps/backend/app/research/referee_routes.py
index 1749e88..2da68fc 100644
--- a/apps/backend/app/research/referee_routes.py
+++ b/apps/backend/app/research/referee_routes.py
@@ -258,10 +258,16 @@ def get_referee_registry(
     withdrawal_store: WithdrawalStore = Depends(get_referee_withdrawal_store),
     certificate_store: CertificateStore = Depends(get_referee_certificate_store),
     playbook_store: PlaybookStore = Depends(get_playbook_store),
+    bar_store: BarStore = Depends(get_bar_store),
 ) -> dict:
     """The pinned four-key registry fold (``families``/``hypotheses``/``withdrawals``/
     ``certificates``) — every hypothesis served with its read-side ``status``/``accrual``
-    additions, never persisted on the record itself. Never 404/500 on an empty registry."""
+    additions, never persisted on the record itself. Never 404/500 on an empty registry.
+
+    ``bar_store`` (goal-referee-iter-9 rider) lets a B/C hypothesis's own ``accrual``/
+    ``discovery`` resolve its context predicate (a ``compute=False`` lookup over the
+    ALREADY-RECORDED band map, T-8) so its registry-row numbers agree with its own shortlist
+    row's live readiness for the identical cell."""
     return registry_response(
         family_store=family_store,
         hypothesis_store=hypothesis_store,
@@ -269,6 +275,8 @@ def get_referee_registry(
         certificate_store=certificate_store,
         playbook_store=playbook_store,
         config_fingerprint=CONFIG.config_fingerprint(),
+        bar_store=bar_store,
+        config=CONFIG,
     )
 
 
diff --git a/apps/backend/tests/test_desk_ui_guards.py b/apps/backend/tests/test_desk_ui_guards.py
index 63fd056..e747bde 100644
--- a/apps/backend/tests/test_desk_ui_guards.py
+++ b/apps/backend/tests/test_desk_ui_guards.py
@@ -251,6 +251,11 @@ _PRICE_ARITHMETIC_FIELDS = (
     # and a registered hypothesis's discovery count (never combined with its accrual siblings).
     r"|candidate\.(?:n|n_sessions|accrual_rate_sessions_per_day|projected_days_to_target)"
     r"|hyp\.discovery\.(?:n|n_sessions)"
+    # goal-referee-iter-9 (J-08 rider): the Referee Registry section's own accrual numerics --
+    # mirrors the existing `hyp.discovery.*` entry above (a "sessions accrued so far" readout is
+    # the obvious client-side subtraction to reach for and the obvious thing to get wrong; the
+    # backend already served both halves of the ratio as computed numbers).
+    r"|hyp\.accrual\.(?:informative_post_boundary_sessions|target_sessions)"
 )
 _PRICE_ARITHMETIC_PATTERN = re.compile(
     rf"({_PRICE_ARITHMETIC_FIELDS})\s*[-+*/]|[-+*/]\s*({_PRICE_ARITHMETIC_FIELDS})"
@@ -484,6 +489,31 @@ def test_desk_page_price_arithmetic_guard_catches_referee_shortlist_and_discover
     ) is None
 
 
+def test_desk_page_price_arithmetic_guard_catches_hyp_accrual_arithmetic_in_isolation():
+    """goal-referee-iter-9 rider (TC-18): ``hyp.accrual.*`` isolated -- never paired with a
+    ``hyp.discovery.*`` field, so this proves THIS iteration's own extension is what catches it
+    (the pre-existing seeded string above already matched on its own ``hyp.discovery.n`` half,
+    which would have passed even before this rider). A mutated-to-arithmetic "sessions remaining"
+    readout fails; the shipped pass-through rendering (the exact
+    ``{hyp.accrual.informative_post_boundary_sessions} / {hyp.accrual.target_sessions}`` JSX line)
+    passes clean."""
+    seeded_remaining = (
+        "const remaining = hyp.accrual.target_sessions - "
+        "hyp.accrual.informative_post_boundary_sessions;"
+    )
+    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_remaining) is not None
+
+    seeded_ratio = (
+        "const pct = hyp.accrual.informative_post_boundary_sessions / hyp.accrual.target_sessions;"
+    )
+    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_ratio) is not None
+
+    # The shipped pass-through rendering (page.tsx's own "X / Y" JSX line) stays clean.
+    assert _PRICE_ARITHMETIC_PATTERN.search(
+        "{hyp.accrual.informative_post_boundary_sessions} / {hyp.accrual.target_sessions}"
+    ) is None
+
+
 # goal-playbook-iter-4 audit (F1): `base_lows_ascending` is ONE served field name carrying the
 # direction-appropriate triangle check underneath (non-decreasing LOWS for `jbe`, non-increasing
 # HIGHS for `dbi` -- see `desk_playbook_detect._base_lows_ascending`). The continuation geometry
diff --git a/apps/backend/tests/test_pnl_scan.py b/apps/backend/tests/test_pnl_scan.py
index 0491758..814a845 100644
--- a/apps/backend/tests/test_pnl_scan.py
+++ b/apps/backend/tests/test_pnl_scan.py
@@ -39,6 +39,7 @@ import dataclasses
 import json
 import random
 import sys
+import time
 from pathlib import Path
 
 import pytest
@@ -59,7 +60,24 @@ from app.research.datasets import DatasetStore, SPLIT_HOLDOUT, SPLIT_TRAIN, reco
 from app.research.pnl_baseline import seed_founding_row
 from app.research.pnl_scan import ScanError, run_sweep
 from app.research.profiles import profiles_projection
-from app.research.store import JournalStore
+from app.research.desk_playbook import PlaybookStore
+from app.research.referee_adjudicate import (
+    REFEREE_GATE_VERSION,
+    AdjudicationSnapshotStore,
+    RefereeEvaluationStore,
+    referee_parameters_hash,
+    run_evaluation_and_record,
+)
+from app.research.referee_null import REFEREE_TEST_PERM_SPEC_ID, RefereeNullStore
+from app.research.referee_registry import (
+    REFEREE_MIN_OCCURRENCES,
+    REFEREE_MIN_SESSIONS,
+    CertificateStore,
+    FamilyStore,
+    HypothesisStore,
+    register_hypothesis,
+)
+from app.research.store import BacktestRecord, JournalStore
 
 # The SAME synthetic three-timeframe confluence fixture test_backtests.py reuses (its own directive:
 # the committed real PG bar fixture stores only two timeframes and can never produce a class-A
@@ -155,10 +173,175 @@ def store(tmp_path):
     s.close()
 
 
+@pytest.fixture
+def certificate_store(tmp_path):
+    """era-6 J-08: an isolated, per-test ``CertificateStore`` — ``run_sweep``'s new REQUIRED
+    parameter. Empty by default (the honest "no certificate exists" baseline every scenario below
+    that never sets one up naturally reaches)."""
+    return CertificateStore(tmp_path / "referee_registry")
+
+
+# --- era-6 J-08: the promotion interlock -- shared certificate/live-scan-context fixture helpers ---
+
+
+def _live_scan_context(*, champion: dict, train_meta: dict, holdout_meta: dict, config: Config) -> dict:
+    """The exact ``live_scan_context`` shape ``pnl_scan._promote`` builds from a live run's own
+    values — computed independently here (never imported from ``pnl_scan`` internals) so a test
+    genuinely proves the two sides agree, rather than sharing one implementation with itself."""
+    return {
+        "champion_identity": champion,
+        "train_dataset": {
+            "id": train_meta["id"], "checksum": train_meta["checksum"], "split": train_meta["split"],
+        },
+        "holdout_dataset": {
+            "id": holdout_meta["id"], "checksum": holdout_meta["checksum"], "split": holdout_meta["split"],
+        },
+        "config_fingerprint": config.config_fingerprint(),
+        "gate_version": REFEREE_GATE_VERSION,
+        "referee_parameters_hash": referee_parameters_hash(),
+    }
+
+
+def _matching_certificate(*, candidate: dict, live: dict, **overrides: object) -> dict:
+    """A hand-built certificate matching every one of ``live``'s own pins (the
+    ``test_referee_adjudicate.py`` ``_fixture_certificate``/``_live_scan_context_matching``
+    precedent) — every refusal-class test below overrides exactly the ONE field it means to
+    mismatch. Hand-building a certificate directly (never through the real evaluation rail) is
+    fine for THESE tests: they exercise ``authorize_promotion``'s own refusal-class boundaries,
+    not the mint path itself (that is TC-2's own job, below, which mints for real)."""
+    fields = {
+        "certificate_id": f"cert-{candidate['strategy_id']}-{candidate['profile']}",
+        "candidate": dict(candidate),
+        "champion_identity_at_scan_time": live["champion_identity"],
+        "train_dataset": live["train_dataset"],
+        "holdout_dataset": live["holdout_dataset"],
+        "config_fingerprint": live["config_fingerprint"],
+        "gate_version": live["gate_version"],
+        "referee_parameters_hash": live["referee_parameters_hash"],
+        "family_id": "fam-fixture", "hypothesis_id": "hyp-fixture",
+        "gate_results": {"calibrated_p": 0.01, "bh_pass": True, "ci": [0.1, 0.9], "floors_met": True},
+    }
+    fields.update(overrides)
+    return fields
+
+
+# --- era-6 J-08 (TC-2): a REAL strategy-family evaluation, minted through the real rail ------------
+#
+# 12 independent dataset clusters (REFEREE_MIN_SESSIONS/REFEREE_MIN_OCCURRENCES's own floor), each
+# carrying exactly ONE candidate trade at a strongly positive net_r and ONE recorded random_null
+# trade at an equally strongly NEGATIVE net_r -- an IDENTICAL per-cluster Delta_d by construction
+# (the ``_plant_known_corpus`` precedent in test_referee_adjudicate.py), so the exact-enumeration
+# permutation space (2**12 = 4096 <= REFEREE_ENUMERATION_THRESHOLD) has exactly ONE combination
+# (the observed grouping itself) at or above the observed T -- a deterministic, hand-verifiable
+# p = 2/4097, comfortably under the family's own q=0.10 (m=1: bh_pass iff p<=q).
+
+
+def _strategy_trade(*, direction: str = "long", logical_ts: float = 100.0, net_r: float = 1.0) -> dict:
+    """A minimal ``_close_trade``-shaped trade -- only the fields the strategy adapter
+    (``referee_evidence._strategy_observation``) reads (the ``test_referee_evidence.py`` ``_trade``
+    precedent, reused here rather than imported across test files)."""
+    return {
+        "setup_type": "v1", "direction": direction,
+        "entry": {"logical_ts": logical_ts, "price": 100.0, "fill_price": 100.0, "spread": 0.0},
+        "exit": {
+            "logical_ts": logical_ts + 60.0, "price": 101.0, "fill_price": 101.0, "spread": 0.0,
+            "reason": "horizon",
+        },
+        "invalidation_price": 99.0, "r_basis": 1.0, "shares": 1.0,
+        "gross_r": net_r, "net_r": net_r, "gross_usd": 0.0, "net_usd": 0.0,
+        "fees_usd": 0.0, "slippage_usd": 0.0,
+    }
+
+
+def _plant_strategy_backtest(
+    journal_store: JournalStore, *, backtest_id: str, dataset: dict,
+    candidate_net_r: float, null_net_r: float,
+) -> None:
+    """Plants one ``done`` backtest report whose ``result`` block already carries the dataset
+    joined verbatim (``backtests.py``'s own result-block shape), reproduced by hand -- the
+    ``test_referee_evidence.py`` ``_plant_backtest_result`` precedent."""
+    payload = {
+        "id": backtest_id, "status": "done",
+        "result": {
+            "dataset": dataset, "strategy_id": STRATEGY_V1_ID, "profile": PROFILE_DEFAULT,
+            "config_fingerprint": CONFIG.config_fingerprint(),
+            "trades": [_strategy_trade(net_r=candidate_net_r)],
+            "null_baseline": {
+                "seed": 1729, "entry_count": 1, "trades": [_strategy_trade(net_r=null_net_r)],
+            },
+        },
+    }
+    journal_store.insert_backtest(
+        BacktestRecord(id=backtest_id, payload=payload, created_wall_ts=time.time())
+    )
+
+
+def _mint_matching_certificate_through_the_real_rail(
+    store: JournalStore, tmp_path: Path, *, candidate: dict, live: dict,
+) -> CertificateStore:
+    """Plants 12 strongly-separated strategy-family dataset clusters into ``store`` (the SAME
+    journal DB the caller's own ``run_sweep`` will use), registers a strategy-family hypothesis at
+    exactly the floor (``target_sessions=min_occurrences=REFEREE_MIN_SESSIONS``), and runs the REAL
+    evaluation rail (``run_evaluation_and_record``) to its attested, gate-passing confirmatory
+    checkpoint -- minting exactly one certificate pinned to ``candidate``/``live`` (goal.md J-08:
+    "mintable only through the real evaluation rail"). Returns the ``CertificateStore`` the caller's
+    own ``run_sweep`` should then pass ``authorize_promotion``."""
+    for i in range(12):
+        dataset = {
+            "id": f"strategy-ds-{i}", "checksum": f"cksum-{i}", "split": SPLIT_TRAIN,
+            "symbol": "SYN-STRAT", "epoch_anchor": 1_800_000_000.0 + i * 86_400.0,
+        }
+        _plant_strategy_backtest(
+            store, backtest_id=f"strategy-bt-{i}", dataset=dataset,
+            candidate_net_r=1.0, null_net_r=-1.0,
+        )
+
+    registry_dir = tmp_path / "referee_registry"
+    eval_dir = tmp_path / "referee_eval"
+    family_store = FamilyStore(registry_dir)
+    hypothesis_store = HypothesisStore(registry_dir)
+    hypothesis_id = "hyp-strategy-cert"
+    payload = {
+        "hypothesis_id": hypothesis_id, "family_id": "fam-strategy-cert", "family_q": 0.10,
+        "family_candidate_hypothesis_ids": [hypothesis_id],
+        "evidence_family": "strategy", "estimand": "A",
+        "setup_id": "structure_tape", "side": "long", "context_predicate": None,
+        "primary_measure_key": "net_r", "primary_horizon": "trade", "sidedness": "greater",
+        "null_spec_id": None, "test_spec_id": REFEREE_TEST_PERM_SPEC_ID,
+        "target_sessions": REFEREE_MIN_SESSIONS, "min_occurrences": REFEREE_MIN_OCCURRENCES,
+    }
+    register_hypothesis(family_store, hypothesis_store, payload, confirm=True)
+
+    certificate_store = CertificateStore(registry_dir)
+    result = run_evaluation_and_record(
+        hypothesis_id,
+        hypothesis_store=hypothesis_store, family_store=family_store,
+        playbook_store=PlaybookStore(tmp_path / "unused-playbook"),
+        bar_store=BarStore(tmp_path / "unused-bars"), config=CONFIG,
+        null_store=RefereeNullStore(tmp_path / "unused-nulls"),
+        evaluation_store=RefereeEvaluationStore(eval_dir),
+        snapshot_store=AdjudicationSnapshotStore(eval_dir),
+        journal_store=store,
+        certificate_mint={
+            "candidate": candidate,
+            "champion_identity_at_scan_time": live["champion_identity"],
+            "train_dataset": live["train_dataset"],
+            "holdout_dataset": live["holdout_dataset"],
+            "certificate_store": certificate_store,
+        },
+    )
+    assert result["cancelled"] is False
+    assert result["record"]["role"] == "checkpoint"
+    assert result["record"]["permutation_p"] == pytest.approx(2.0 / 4097.0)
+    assert result["snapshot"]["bh"]["bh_pass"] is True
+    assert result["certificate"] is not None
+    return certificate_store
+
+
 # --- Fixture sweep: the non-regression baseline (Key Test Scenario 1) ------------------------------
 
 
-def test_fixture_sweep_is_zero_survivors_and_leaves_everything_untouched(store, tmp_path):
+def test_fixture_sweep_is_zero_survivors_and_leaves_everything_untouched(store, tmp_path, certificate_store):
     """On the committed fixture pair, ``candidate-faster-warmup`` is a non-survivor: identical
     trades on train (delta exactly zero) and a NEGATIVE hold-out delta with n below the
     promotion minimum — both independently sufficient to refuse promotion. Seeds the founding
@@ -169,7 +352,7 @@ def test_fixture_sweep_is_zero_survivors_and_leaves_everything_untouched(store,
     created, _ = seed_founding_row(store, DatasetStore(tmp_path / "founding-datasets"), CONFIG)
     assert created is True
 
-    report = run_sweep(store, dataset_store, CONFIG)
+    report = run_sweep(store, dataset_store, CONFIG, certificate_store=certificate_store)
 
     assert report["champion_before"] == {"strategy_id": STRATEGY_V1_ID, "profile": PROFILE_DEFAULT}
     assert report["champion_after"] == report["champion_before"]
@@ -194,7 +377,7 @@ def test_fixture_sweep_is_zero_survivors_and_leaves_everything_untouched(store,
     assert profiles_projection(store, CONFIG)["champion"] == report["champion_before"]
 
 
-def test_zero_registered_candidates_is_an_honest_empty_sweep(store, monkeypatch):
+def test_zero_registered_candidates_is_an_honest_empty_sweep(store, monkeypatch, certificate_store):
     """Zero registered candidates -> an explicit, honest empty report (never an error) — the
     ``profile_registry`` filter to non-default entries applied to an all-default registry."""
     monkeypatch.setattr(
@@ -203,7 +386,7 @@ def test_zero_registered_candidates_is_an_honest_empty_sweep(store, monkeypatch)
         lambda self: [{"id": PROFILE_DEFAULT, "frozen": True, "is_default": True}],
     )
     dataset_store = DatasetStore(FIXTURE_DATASET_DIR)
-    report = run_sweep(store, dataset_store, CONFIG)
+    report = run_sweep(store, dataset_store, CONFIG, certificate_store=certificate_store)
     assert report["candidates"] == []
     assert report["promotion"] is None
     assert len(store.list_pnl_ledger()) == 0
@@ -212,22 +395,23 @@ def test_zero_registered_candidates_is_an_honest_empty_sweep(store, monkeypatch)
 # --- Controlled survivor: a genuine, isolated hold-out win (Key Test Scenario 2) --------------------
 
 
-def test_controlled_survivor_moves_champion_and_appends_exactly_one_ledger_row(store, tmp_path):
-    """An ISOLATED synthetic train + hold-out pair (never the shipped fixture) on which the
-    candidate legitimately beats the champion on BOTH splits, with a test-LOCAL lowered
-    promotion minimum (``dataclasses.replace`` — the shipped default of 5 is never touched):
-    promotes for real — champion pointer moves, exactly one provenance-stamped ledger row is
-    appended via the existing single writer — while ``default`` and every engine default stay
-    byte-identical."""
+def test_controlled_survivor_is_refused_without_a_certificate(store, tmp_path, certificate_store):
+    """era-6 J-08 (TC-1), inverting this suite's own pre-iter-9 "controlled survivor promotes"
+    assertions per goal.md's own stated consequence: an ISOLATED synthetic train + hold-out pair on
+    which the candidate legitimately beats the champion on BOTH splits is now REFUSED — no ledger
+    row, no pointer move — absent a valid, candidate-specific Referee certificate. ``survivor``
+    still reads ``True`` (the hold-out gate itself still passed; only the NEW certificate interlock
+    blocks the write)."""
     dataset_store = DatasetStore(tmp_path / "datasets")
-    train_meta = _winning_dataset(dataset_store, "SYN-TRAIN-A", seed=7, split=SPLIT_TRAIN)
-    holdout_meta = _winning_dataset(dataset_store, "SYN-HOLDOUT-B", seed=11, split=SPLIT_HOLDOUT)
+    _winning_dataset(dataset_store, "SYN-TRAIN-A", seed=7, split=SPLIT_TRAIN)
+    _winning_dataset(dataset_store, "SYN-HOLDOUT-B", seed=11, split=SPLIT_HOLDOUT)
     test_config = dataclasses.replace(CONFIG, promotion_min_sample_size=1)
 
-    report = run_sweep(store, dataset_store, test_config)
+    report = run_sweep(store, dataset_store, test_config, certificate_store=certificate_store)
 
     (candidate,) = report["candidates"]
-    # The win is asserted, not merely assumed (both R and $ on both splits, empirically robust).
+    # The win is asserted, not merely assumed (both R and $ on both splits, empirically robust) —
+    # the hold-out gate itself still genuinely passes; only the certificate interlock refuses.
     assert candidate["train"]["aggregate"]["delta_net_r"] > 0
     assert candidate["train"]["aggregate"]["delta_net_usd"] > 0
     assert candidate["holdout"]["aggregate"]["delta_net_r"] > 0
@@ -237,6 +421,51 @@ def test_controlled_survivor_moves_champion_and_appends_exactly_one_ledger_row(s
     assert candidate["overfit"] is False
 
     assert report["champion_before"] == {"strategy_id": STRATEGY_V1_ID, "profile": PROFILE_DEFAULT}
+    assert report["champion_after"] == report["champion_before"]  # UNMOVED
+    assert report["promotion"] == {
+        "candidate_id": PROFILE_CANDIDATE_FASTER_WARMUP,
+        "promoted": False,
+        "note": None,
+        "promotion_eligible": False,
+        "refusal_class": "no_certificate",
+        "reason": report["promotion"]["reason"],
+    }
+    assert report["promotion"]["reason"]
+
+    assert len(store.list_pnl_ledger()) == 0  # nothing written
+    assert CONFIG.config_fingerprint() == "08e471b10130e1e2"
+    assert profiles_projection(store, test_config)["champion"] == report["champion_before"]
+
+
+def test_controlled_survivor_promotes_with_a_certificate_minted_through_the_real_evaluation_rail(
+    store, tmp_path,
+):
+    """era-6 J-08 (TC-2): the SAME controlled-survivor scenario as the refusal test above, but with
+    a certificate minted through the REAL evaluation rail (``run_evaluation_and_record``, a genuine
+    strategy-family hypothesis reaching an attested, gate-passing confirmatory checkpoint — never a
+    hand-written fixture path) matching every one of the live scan's own pins: promotes for real —
+    champion pointer moves, exactly one provenance-stamped ledger row is appended — exactly as this
+    suite asserted before this iteration, PLUS the new ``promotion_eligible: True`` field."""
+    dataset_store = DatasetStore(tmp_path / "datasets")
+    train_meta = _winning_dataset(dataset_store, "SYN-TRAIN-A", seed=7, split=SPLIT_TRAIN)
+    holdout_meta = _winning_dataset(dataset_store, "SYN-HOLDOUT-B", seed=11, split=SPLIT_HOLDOUT)
+    test_config = dataclasses.replace(CONFIG, promotion_min_sample_size=1)
+
+    champion_before = store.get_champion_pointer()
+    candidate = {"strategy_id": champion_before["strategy_id"], "profile": PROFILE_CANDIDATE_FASTER_WARMUP}
+    live = _live_scan_context(
+        champion=champion_before, train_meta=train_meta, holdout_meta=holdout_meta, config=test_config,
+    )
+    certificate_store = _mint_matching_certificate_through_the_real_rail(
+        store, tmp_path, candidate=candidate, live=live,
+    )
+
+    report = run_sweep(store, dataset_store, test_config, certificate_store=certificate_store)
+
+    (result_candidate,) = report["candidates"]
+    assert result_candidate["survivor"] is True
+
+    assert report["champion_before"] == champion_before
     assert report["champion_after"] == {
         "strategy_id": STRATEGY_V1_ID,
         "profile": PROFILE_CANDIDATE_FASTER_WARMUP,
@@ -245,6 +474,9 @@ def test_controlled_survivor_moves_champion_and_appends_exactly_one_ledger_row(s
         "candidate_id": PROFILE_CANDIDATE_FASTER_WARMUP,
         "promoted": True,
         "enhancement_id": f"{PROFILE_CANDIDATE_FASTER_WARMUP}-over-{STRATEGY_V1_ID}-{PROFILE_DEFAULT}",
+        "promotion_eligible": True,
+        "refusal_class": None,
+        "reason": None,
     }
 
     rows = store.list_pnl_ledger()
@@ -252,10 +484,10 @@ def test_controlled_survivor_moves_champion_and_appends_exactly_one_ledger_row(s
     row = rows[0].payload
     assert row["founding"] is False
     assert row["baseline"]["train"]["net_r"] == pytest.approx(
-        candidate["train"]["datasets"][0]["champion"]["net_r"]
+        result_candidate["train"]["datasets"][0]["champion"]["net_r"]
     )
     assert row["candidate"]["train"]["net_r"] == pytest.approx(
-        candidate["train"]["datasets"][0]["candidate"]["net_r"]
+        result_candidate["train"]["datasets"][0]["candidate"]["net_r"]
     )
     assert row["provenance"]["strategy_id"] == STRATEGY_V1_ID
     assert row["provenance"]["profile"] == PROFILE_CANDIDATE_FASTER_WARMUP
@@ -272,13 +504,13 @@ def test_controlled_survivor_moves_champion_and_appends_exactly_one_ledger_row(s
 # --- Min-n gate, both ways (Key Test Scenario 3) -----------------------------------------------
 
 
-def test_min_n_gate_rejects_below_minimum_despite_positive_holdout(store, tmp_path):
+def test_min_n_gate_rejects_below_minimum_despite_positive_holdout(store, tmp_path, certificate_store):
     dataset_store = DatasetStore(tmp_path / "datasets")
     _winning_dataset(dataset_store, "SYN-TRAIN-A", seed=7, split=SPLIT_TRAIN)
     _winning_dataset(dataset_store, "SYN-HOLDOUT-B", seed=11, split=SPLIT_HOLDOUT)
     test_config = dataclasses.replace(CONFIG, promotion_min_sample_size=2)  # candidate n=1 < 2
 
-    report = run_sweep(store, dataset_store, test_config)
+    report = run_sweep(store, dataset_store, test_config, certificate_store=certificate_store)
 
     (candidate,) = report["candidates"]
     assert candidate["holdout"]["aggregate"]["delta_net_r"] > 0
@@ -290,18 +522,26 @@ def test_min_n_gate_rejects_below_minimum_despite_positive_holdout(store, tmp_pa
     assert report["champion_after"] == report["champion_before"]
 
 
-def test_min_n_gate_promotes_at_or_above_minimum(store, tmp_path):
+def test_min_n_gate_survivor_at_or_above_minimum_is_still_refused_without_a_certificate(
+    store, tmp_path, certificate_store,
+):
+    """era-6 J-08: inverts this suite's own pre-iter-9 "min-n gate promotes" assertion — the
+    hold-out gate itself still passes at n=1>=1 (``survivor`` reads ``True``), but with no
+    certificate on file the certificate interlock refuses it, same as the controlled-survivor case
+    above (a different fixture path reaching the identical refusal, TC-1's own generality)."""
     dataset_store = DatasetStore(tmp_path / "datasets")
     _winning_dataset(dataset_store, "SYN-TRAIN-A", seed=7, split=SPLIT_TRAIN)
     _winning_dataset(dataset_store, "SYN-HOLDOUT-B", seed=11, split=SPLIT_HOLDOUT)
     test_config = dataclasses.replace(CONFIG, promotion_min_sample_size=1)  # candidate n=1 >= 1
 
-    report = run_sweep(store, dataset_store, test_config)
+    report = run_sweep(store, dataset_store, test_config, certificate_store=certificate_store)
 
     (candidate,) = report["candidates"]
     assert candidate["survivor"] is True
-    assert report["promotion"]["promoted"] is True
-    assert len(store.list_pnl_ledger()) == 1
+    assert report["promotion"]["promoted"] is False
+    assert report["promotion"]["promotion_eligible"] is False
+    assert report["promotion"]["refusal_class"] == "no_certificate"
+    assert len(store.list_pnl_ledger()) == 0
 
 
 # --- Determinism (Key Test Scenario 4) ----------------------------------------------------------
@@ -332,7 +572,7 @@ def test_determinism_two_independent_fresh_state_runs_are_byte_identical(tmp_pat
... [diff_bound] apps/backend/tests/test_pnl_scan.py: 503 more diff lines omitted — Read the file for full detail
diff --git a/apps/backend/tests/test_referee_adjudicate.py b/apps/backend/tests/test_referee_adjudicate.py
index 65a47f2..983b90a 100644
--- a/apps/backend/tests/test_referee_adjudicate.py
+++ b/apps/backend/tests/test_referee_adjudicate.py
@@ -24,7 +24,7 @@ import pytest
 from fastapi.testclient import TestClient
 
 import app.research.referee_adjudicate as referee_adjudicate_module
-from app.config import CONFIG
+from app.config import CONFIG, PROFILE_DEFAULT, STRATEGY_V1_ID
 from app.main import app
 from app.providers.adapters.base import RawBar
 from app.research.bars import BarStore
@@ -34,6 +34,7 @@ from app.research.desk_playbook_features import side_sign
 from app.research.referee_adjudicate import (
     REFEREE_GATE_VERSION,
     REFEREE_REGISTER,
+    REFEREE_STRATEGY_NULL_DESIGN_CAVEAT,
     AdjudicationSnapshotStore,
     RefereeEvaluationComputeManager,
     RefereeEvaluationRunStore,
@@ -41,14 +42,18 @@ from app.research.referee_adjudicate import (
     _build_and_record_snapshot,
     _canonical,
     _family_bh_fold,
+    _mint_strategy_certificate,
     _pool_against_null,
     _pool_cell_vs_complement,
+    _pool_strategy_trades,
     _sha256,
     adjudications_response,
     authorize_promotion,
+    referee_parameters,
+    referee_parameters_hash,
     run_evaluation_and_record,
 )
-from app.research.referee_evidence import playbook_observations
+from app.research.referee_evidence import REFEREE_FORMING_BAR_BASIS_CAVEAT, playbook_observations
 from app.research.referee_null import (
     REFEREE_NULL_CONTEXT_SPEC_ID,
     REFEREE_NULL_TOD_SPEC_ID,
@@ -57,6 +62,8 @@ from app.research.referee_null import (
     build_null_record,
 )
 from app.research.referee_registry import (
+    REFEREE_MIN_OCCURRENCES,
+    REFEREE_MIN_SESSIONS,
     CertificateStore,
     FamilyStore,
     HypothesisStore,
@@ -68,6 +75,7 @@ from app.research.referee_registry import (
 from app.research.referee_routes import get_referee_eval_compute_manager
 import app.research.referee_stats as referee_stats_module
 from app.research.referee_stats import run_oracle_attestation, verify_oracle_attestation
+from app.research.store import BacktestRecord, JournalStore
 
 _ET = ZoneInfo("America/New_York")
 
@@ -1029,6 +1037,383 @@ def test_get_adjudications_route_serves_integrity_errors_key_on_a_healthy_store(
     assert set(body) == {"entries", "register", "integrity_errors"}
 
 
+# === goal-referee-iter-9 (J-08 Step 1): the strategy-family evaluation branch (spec Sec3.7) ===========
+#
+# Fixture builders mirror ``test_referee_evidence.py``'s own ``_trade``/``_plant_backtest_result``
+# precedent (a minimal ``_close_trade``-shaped trade, a hand-built ``result`` block planted directly
+# via ``JournalStore.insert_backtest`` — never a real replay) rather than importing across test
+# files, matching this file's own established local-copy convention.
+
+
+def _strategy_trade(*, direction: str = "long", logical_ts: float = 100.0, net_r: float = 1.0) -> dict:
+    return {
+        "setup_type": "v1", "direction": direction,
+        "entry": {"logical_ts": logical_ts, "price": 100.0, "fill_price": 100.0, "spread": 0.0},
+        "exit": {
+            "logical_ts": logical_ts + 60.0, "price": 101.0, "fill_price": 101.0, "spread": 0.0,
+            "reason": "horizon",
+        },
+        "invalidation_price": 99.0, "r_basis": 1.0, "shares": 1.0,
+        "gross_r": net_r, "net_r": net_r, "gross_usd": 0.0, "net_usd": 0.0,
+        "fees_usd": 0.0, "slippage_usd": 0.0,
+    }
+
+
+def _plant_strategy_backtest(
+    journal_store: JournalStore, *, backtest_id: str, dataset_id: str,
+    candidate_net_rs: list[float], null_net_rs: list[float], symbol: str = "SYN-STRAT",
+) -> None:
+    payload = {
+        "id": backtest_id, "status": "done",
+        "result": {
+            "dataset": {
+                "id": dataset_id, "checksum": f"cksum-{dataset_id}", "split": "train",
+                "symbol": symbol, "epoch_anchor": 1_800_000_000.0,
+            },
+            "strategy_id": STRATEGY_V1_ID, "profile": PROFILE_DEFAULT,
+            "config_fingerprint": CONFIG.config_fingerprint(),
+            "trades": [_strategy_trade(net_r=r) for r in candidate_net_rs],
+            "null_baseline": {
+                "seed": 1729, "entry_count": len(null_net_rs),
+                "trades": [_strategy_trade(net_r=r) for r in null_net_rs],
+            },
+        },
+    }
+    journal_store.insert_backtest(
+        BacktestRecord(id=backtest_id, payload=payload, created_wall_ts=time_module.time())
+    )
+
+
+def _register_strategy_hypothesis(
+    family_store: FamilyStore, hypothesis_store: HypothesisStore, hypothesis_id: str, family_id: str,
+    *, target_sessions: int = REFEREE_MIN_SESSIONS, min_occurrences: int = REFEREE_MIN_OCCURRENCES,
+) -> dict:
+    """A strategy-family hypothesis registration payload -- ``setup_id``/``side`` are schema-required
+    (``_REQUIRED_HYPOTHESIS_FIELDS`` applies uniformly across both evidence families) but carry no
+    functional meaning for THIS branch (spec Sec3.7's own pooling is dataset-clustered, not
+    setup/side-filtered; blueprint.md's iter-9 note: "No new field" -- no per-candidate strategy_id/
+    profile field exists on the hypothesis record this era). Logged as a T-1 interpretation:
+    ``state/assumptions.md`` iter-9 (developer)."""
+    payload = {
+        "hypothesis_id": hypothesis_id, "family_id": family_id, "family_q": 0.10,
+        "family_candidate_hypothesis_ids": [hypothesis_id],
+        "evidence_family": "strategy", "estimand": "A",
+        "setup_id": "structure_tape", "side": "long", "context_predicate": None,
+        "primary_measure_key": "net_r", "primary_horizon": "trade", "sidedness": "greater",
+        "null_spec_id": None, "test_spec_id": REFEREE_TEST_PERM_SPEC_ID,
+        "target_sessions": target_sessions, "min_occurrences": min_occurrences,
+        "registered_at": _REGISTERED_AT,
+    }
+    return register_hypothesis(family_store, hypothesis_store, payload, confirm=True)
+
+
+@pytest.fixture
+def journal_store(tmp_path):
+    js = JournalStore(str(tmp_path / "strategy-journal.db"), CONFIG)
+    yield js
+    js.close()
+
+
+def test_tc9_strategy_pooling_groups_by_dataset_cluster_key_never_session_date(journal_store):
+    """TC-9: ``_pool_strategy_trades`` groups ``referee_evidence.strategy_observations()``'s
+    primary/null trade lists by ``cluster_key`` = dataset id -- TWO backtest reports over the SAME
+    dataset id (planted as if from different runs) pool into ONE cluster; a report over a DIFFERENT
+    dataset id pools into its own. Never grouped by ``session_date`` (every trade below shares the
+    identical fixed ``epoch_anchor``, so a session_date-keyed pool would collapse to ONE cluster --
+    proving the grouping key genuinely is the dataset id, not an accidentally-identical date)."""
+    _plant_strategy_backtest(
+        journal_store, backtest_id="bt-1", dataset_id="ds-1",
+        candidate_net_rs=[1.0], null_net_rs=[-1.0],
+    )
+    _plant_strategy_backtest(
+        journal_store, backtest_id="bt-2", dataset_id="ds-1",
+        candidate_net_rs=[0.5], null_net_rs=[-0.5],
+    )
+    _plant_strategy_backtest(
+        journal_store, backtest_id="bt-3", dataset_id="ds-2",
+        candidate_net_rs=[2.0], null_net_rs=[-2.0],
+    )
+
+    pool = _pool_strategy_trades(journal_store)
+
+    assert set(pool["session_groups"]) == {"ds-1", "ds-2"}
+    ds1_candidates, ds1_nulls = pool["session_groups"]["ds-1"]
+    assert sorted(ds1_candidates) == [0.5, 1.0]  # bt-1 + bt-2's own candidate trades, pooled
+    assert sorted(ds1_nulls) == [-1.0, -0.5]
+    ds2_candidates, ds2_nulls = pool["session_groups"]["ds-2"]
+    assert ds2_candidates == [2.0] and ds2_nulls == [-2.0]
+    assert pool["informative_sessions"] == 2  # 2 dataset clusters, never 1 (session_date collapse)
+    assert pool["occurrence_diffs"] is None  # not defined at occurrence level for strategy family
+    assert pool["occurrences_pooled"] == 3  # 3 candidate trades total, across both clusters
+
+
+def test_tc9_a_dataset_with_only_candidate_or_only_null_trades_is_excluded_and_counted(journal_store):
+    """A dataset cluster carrying candidate trades but NO recorded null (or vice versa) is honestly
+    excluded from ``session_groups`` and counted in ``one_group_sessions_excluded`` -- never
+    silently substituted (T-5), mirroring ``_pool_against_null``'s own one-sided-session handling."""
+    _plant_strategy_backtest(
+        journal_store, backtest_id="bt-both", dataset_id="ds-both",
+        candidate_net_rs=[1.0], null_net_rs=[-1.0],
+    )
+    _plant_strategy_backtest(
+        journal_store, backtest_id="bt-candidate-only", dataset_id="ds-candidate-only",
+        candidate_net_rs=[1.0], null_net_rs=[],
+    )
+
+    pool = _pool_strategy_trades(journal_store)
+
+    assert set(pool["session_groups"]) == {"ds-both"}
+    assert pool["one_group_sessions_excluded"] == 1  # ds-candidate-only
+
+
+def test_tc10_todays_real_corpus_shape_serves_insufficient_sample_with_caveats_and_null_disclosure(
+    journal_store, tmp_path,
+):
+    """TC-10: at today's real corpus shape (champion holdout n=1, far below
+    ``promotion_min_sample_size``=5 -- reproduced here as a SINGLE dataset cluster, far below
+    ``REFEREE_MIN_CLUSTERS_FOR_CI``=8 and ``REFEREE_MIN_SESSIONS``=12), the strategy-family
+    evaluation's own clustered-CI reads the literal ``insufficient_sample`` sentinel (never a
+    fabricated interval), the recorded ``provenance.basis_caveats`` includes the Card-6.4
+    forming-bar caveat, and the served null-design disclosure states the recorded null is
+    uniform-random, not count/ToD-matched -- stated, not hidden."""
+    _plant_strategy_backtest(
+        journal_store, backtest_id="bt-real-shape", dataset_id="ds-real-shape",
+        candidate_net_rs=[1.0], null_net_rs=[-0.2, 0.1, -0.3],
+    )
+    registry_dir = tmp_path / "registry"
+    family_store = FamilyStore(registry_dir)
+    hypothesis_store = HypothesisStore(registry_dir)
+    _register_strategy_hypothesis(family_store, hypothesis_store, "hyp-real-shape", "fam-real-shape")
+
+    result = run_evaluation_and_record(
+        "hyp-real-shape",
+        hypothesis_store=hypothesis_store, family_store=family_store,
+        playbook_store=PlaybookStore(tmp_path / "unused-playbook"),
+        bar_store=BarStore(tmp_path / "unused-bars"), config=CONFIG,
+        null_store=RefereeNullStore(tmp_path / "unused-nulls"),
+        evaluation_store=RefereeEvaluationStore(tmp_path / "eval"),
+        snapshot_store=AdjudicationSnapshotStore(tmp_path / "eval"),
+        journal_store=journal_store,
+    )
+    record = result["record"]
+    assert record["evidence_family"] == "strategy"
+    assert record["confirmatory_eligible"] is False  # 1 cluster << REFEREE_MIN_SESSIONS (12)
+    assert record["role"] == "pending"
+    assert record["T"] is None and record["permutation_p"] is None  # T-4: no confirmatory p pre-floor
+    assert record["ci_cluster"] == "insufficient_sample"  # never a fabricated interval
+    assert record["ci_occurrence"] is None  # not defined at occurrence level (this branch's design)
+
+    basis_caveats = record["provenance"]["basis_caveats"]
+    assert REFEREE_FORMING_BAR_BASIS_CAVEAT in basis_caveats
+    assert REFEREE_STRATEGY_NULL_DESIGN_CAVEAT in basis_caveats
+    assert "100" in REFEREE_STRATEGY_NULL_DESIGN_CAVEAT  # backtest_null_entry_count's real default
+    assert "uniform-random" in REFEREE_STRATEGY_NULL_DESIGN_CAVEAT
+    assert "not count- or time-of-day-matched" in REFEREE_STRATEGY_NULL_DESIGN_CAVEAT
+    assert result["certificate"] is None  # never checkpoint -> never even attempted
+
+
+def _plant_strong_strategy_effect(journal_store: JournalStore, *, n_clusters: int = 12) -> None:
+    """``n_clusters`` independent dataset clusters, each carrying exactly ONE candidate trade at a
+    strongly positive net_r and ONE recorded null trade at an equally strongly NEGATIVE net_r -- an
+    IDENTICAL per-cluster Delta_d by construction (the ``_plant_known_corpus`` precedent above),
+    reaching a deterministic, hand-verifiable p = 2/(2**n_clusters + 1) under exact enumeration
+    (n1=n2=1 per cluster -> 2**n_clusters total combinations, comfortably <=
+    REFEREE_ENUMERATION_THRESHOLD at n_clusters=12), comfortably under any registered q."""
+    for i in range(n_clusters):
+        _plant_strategy_backtest(
+            journal_store, backtest_id=f"strong-bt-{i}", dataset_id=f"strong-ds-{i}",
+            candidate_net_rs=[1.0], null_net_rs=[-1.0],
+        )
+
+
+def test_tc11_a_playbook_checkpoint_never_mints_a_certificate(stores):
+    """TC-11: a Playbook-family hypothesis reaching its confirmatory checkpoint gains no new
+    ``CertificateStore`` record -- the mint path fires only for ``evidence_family == "strategy"``
+    checkpoints, even when a (deliberately mismatched-looking, never actually usable) ``certificate_
+    mint`` happens to be supplied."""
+    _plant_known_corpus(
+        stores, "hyp-tc11-playbook", "fam-tc11-playbook", n_sessions=13,
+        trigger_close=100.0, flat_close=102.0,
+    )
+    certificate_store = CertificateStore(stores["hypothesis_store"].root)
+    result = _run_eval(
+        stores, "hyp-tc11-playbook",
+        certificate_mint={
+            "candidate": {"strategy_id": STRATEGY_V1_ID, "profile": PROFILE_DEFAULT},
+            "champion_identity_at_scan_time": {"strategy_id": STRATEGY_V1_ID, "profile": PROFILE_DEFAULT},
+            "train_dataset": {"id": "ds-train", "checksum": "abc", "split": "train"},
+            "holdout_dataset": {"id": "ds-holdout", "checksum": "def", "split": "holdout"},
+            "certificate_store": certificate_store,
+        },
+    )
+    assert result["record"]["role"] == "checkpoint"
+    assert result["snapshot"]["verdict"] == "corroborated"
+    assert result["certificate"] is None  # the mint path never fires for a playbook checkpoint
+
+    records, errors = certificate_store.list()
+    assert errors == []
+    assert records == []
+
+
+def test_tc12_a_strategy_checkpoint_mints_exactly_one_certificate_through_the_real_rail(
+    journal_store, tmp_path,
+):
+    """TC-12: a strategy-family hypothesis reaching an attested, gate-passing confirmatory
+    checkpoint mints EXACTLY one certificate, pinning every named field, reachable ONLY through
+    ``run_evaluation_and_record`` itself (never a hand-written fixture path in production code)."""
+    _plant_strong_strategy_effect(journal_store, n_clusters=12)
+    registry_dir = tmp_path / "registry"
+    family_store = FamilyStore(registry_dir)
+    hypothesis_store = HypothesisStore(registry_dir)
+    _register_strategy_hypothesis(family_store, hypothesis_store, "hyp-tc12", "fam-tc12")
+    certificate_store = CertificateStore(registry_dir)
+    candidate = {"strategy_id": "structure_tape", "profile": PROFILE_DEFAULT}
+    champion_identity = {"strategy_id": STRATEGY_V1_ID, "profile": PROFILE_DEFAULT}
+    train_dataset = {"id": "ds-train-pin", "checksum": "train-checksum", "split": "train"}
+    holdout_dataset = {"id": "ds-holdout-pin", "checksum": "holdout-checksum", "split": "holdout"}
+
+    result = run_evaluation_and_record(
+        "hyp-tc12",
+        hypothesis_store=hypothesis_store, family_store=family_store,
+        playbook_store=PlaybookStore(tmp_path / "unused-playbook"),
+        bar_store=BarStore(tmp_path / "unused-bars"), config=CONFIG,
+        null_store=RefereeNullStore(tmp_path / "unused-nulls"),
+        evaluation_store=RefereeEvaluationStore(tmp_path / "eval"),
+        snapshot_store=AdjudicationSnapshotStore(tmp_path / "eval"),
+        journal_store=journal_store,
+        certificate_mint={
+            "candidate": candidate, "champion_identity_at_scan_time": champion_identity,
+            "train_dataset": train_dataset, "holdout_dataset": holdout_dataset,
+            "certificate_store": certificate_store,
+        },
+    )
+    assert result["record"]["role"] == "checkpoint"
+    assert result["record"]["permutation_p"] == pytest.approx(2.0 / (2**12 + 1))
+    assert result["snapshot"]["bh"]["bh_pass"] is True
+    certificate = result["certificate"]
+    assert certificate is not None
+    assert certificate["candidate"] == candidate
+    assert certificate["champion_identity_at_scan_time"] == champion_identity
+    assert certificate["train_dataset"] == train_dataset
+    assert certificate["holdout_dataset"] == holdout_dataset
+    assert certificate["config_fingerprint"] == CONFIG.config_fingerprint()
+    assert certificate["gate_version"] == REFEREE_GATE_VERSION
+    assert certificate["referee_parameters_hash"] == referee_parameters_hash()
+    assert certificate["family_id"] == "fam-tc12"
+    assert certificate["hypothesis_id"] == "hyp-tc12"
+    assert certificate["gate_results"] == {
+        "calibrated_p": result["record"]["permutation_p"],
+        "bh_pass": True,
+        "ci": result["record"]["ci_cluster"],
+        "floors_met": True,
+    }
+
+    records, errors = certificate_store.list()
+    assert errors == []
+    assert len(records) == 1
+    assert records[0]["certificate_id"] == certificate["certificate_id"]
+
+    # A second evaluation act against the SAME (unchanged) store dedupes -- reused, never a second
+    # certificate minted.
+    second = run_evaluation_and_record(
+        "hyp-tc12",
+        hypothesis_store=hypothesis_store, family_store=family_store,
+        playbook_store=PlaybookStore(tmp_path / "unused-playbook"),
+        bar_store=BarStore(tmp_path / "unused-bars"), config=CONFIG,
+        null_store=RefereeNullStore(tmp_path / "unused-nulls"),
+        evaluation_store=RefereeEvaluationStore(tmp_path / "eval"),
+        snapshot_store=AdjudicationSnapshotStore(tmp_path / "eval"),
+        journal_store=journal_store,
+        certificate_mint={
+            "candidate": candidate, "champion_identity_at_scan_time": champion_identity,
+            "train_dataset": train_dataset, "holdout_dataset": holdout_dataset,
+            "certificate_store": certificate_store,
+        },
+    )
+    assert second["reused"] is True
+    assert second["certificate"] is None  # no mint attempt on the dedup/reused path
+    records_after, _errors = certificate_store.list()
+    assert len(records_after) == 1  # still exactly one
+
+
+def test_tc13_a_failed_attestation_never_mints_a_strategy_certificate_role_stays_pending(
+    journal_store, tmp_path, monkeypatch,
+):
+    """TC-13 (the Rider-1 gate, applied to the strategy family): the SAME otherwise-checkpoint-
+    eligible fixture as TC-12, forced through a deliberately failing oracle attestation --
+    ``role`` stays ``"pending"`` (never ``"checkpoint"``), no snapshot, and therefore no
+    certificate (the mint call site is only ever reached from inside the
+    ``recorded["role"] == "checkpoint"`` branch)."""
+    _plant_strong_strategy_effect(journal_store, n_clusters=12)
+    registry_dir = tmp_path / "registry"
+    family_store = FamilyStore(registry_dir)
+    hypothesis_store = HypothesisStore(registry_dir)
+    _register_strategy_hypothesis(family_store, hypothesis_store, "hyp-tc13", "fam-tc13")
+    certificate_store = CertificateStore(registry_dir)
+    real_attestation = run_oracle_attestation()
+    assert real_attestation["passed"] is True
+    monkeypatch.setattr(
+        referee_adjudicate_module, "run_oracle_attestation",
+        lambda: {**real_attestation, "passed": False},
+    )
+
+    result = run_evaluation_and_record(
+        "hyp-tc13",
+        hypothesis_store=hypothesis_store, family_store=family_store,
+        playbook_store=PlaybookStore(tmp_path / "unused-playbook"),
+        bar_store=BarStore(tmp_path / "unused-bars"), config=CONFIG,
+        null_store=RefereeNullStore(tmp_path / "unused-nulls"),
+        evaluation_store=RefereeEvaluationStore(tmp_path / "eval"),
+        snapshot_store=AdjudicationSnapshotStore(tmp_path / "eval"),
+        journal_store=journal_store,
+        certificate_mint={
+            "candidate": {"strategy_id": "structure_tape", "profile": PROFILE_DEFAULT},
+            "champion_identity_at_scan_time": {"strategy_id": STRATEGY_V1_ID, "profile": PROFILE_DEFAULT},
+            "train_dataset": {"id": "ds-train", "checksum": "abc", "split": "train"},
+            "holdout_dataset": {"id": "ds-holdout", "checksum": "def", "split": "holdout"},
+            "certificate_store": certificate_store,
+        },
+    )
+    assert result["record"]["confirmatory_eligible"] is True  # coverage floors WERE met
... [diff_bound] apps/backend/tests/test_referee_adjudicate.py: 42 more diff lines omitted — Read the file for full detail
diff --git a/apps/backend/tests/test_referee_registry.py b/apps/backend/tests/test_referee_registry.py
index 1954b3b..e063d3a 100644
--- a/apps/backend/tests/test_referee_registry.py
+++ b/apps/backend/tests/test_referee_registry.py
@@ -532,12 +532,14 @@ def test_tc13_cli_and_post_produce_byte_identical_stored_hypothesis_records(tmp_
     assert cli_record == post_record  # byte-identical stored records, two isolated stores
 
 
-# === TC-14: the five starter-family candidates (spec Sec7 S-1..S-5) all register cleanly =============
+# === TC-14: the six starter-family candidates (spec Sec7 S-1..S-5 + iter-9's S-6) all register
+# cleanly ===============================================================================================
 
 
 def _starter_family_payloads() -> list[dict]:
-    """spec Sec7's shortlist, verbatim (S-1..S-5) -- one family, the complete planned list."""
-    ids = ["hyp-s1", "hyp-s2", "hyp-s3", "hyp-s4", "hyp-s5"]
+    """spec Sec7's shortlist, verbatim (S-1..S-5) plus iter-9's own S-6 rider (the S-4 short-side
+    sibling) -- one family, the complete planned list."""
+    ids = ["hyp-s1", "hyp-s2", "hyp-s3", "hyp-s4", "hyp-s5", "hyp-s6"]
     family_kwargs = {
         "family_id": "fam-starter", "family_q": 0.10, "family_candidate_hypothesis_ids": ids,
     }
@@ -584,29 +586,42 @@ def _starter_family_payloads() -> list[dict]:
             "target_sessions": REFEREE_MIN_SESSIONS, "min_occurrences": REFEREE_MIN_OCCURRENCES,
             "registered_at": _REGISTERED_AT,
         },
+        {  # S-6 (iter-9 rider): B, range_trade:short at_wall vs other same-setup contexts, 1h
+            "hypothesis_id": "hyp-s6", **family_kwargs, "evidence_family": "playbook",
+            "estimand": "B", "setup_id": "range_trade", "side": "short",
+            "context_predicate": {"backing_bucket": "at_wall"}, "primary_measure_key": "1h",
+            "primary_horizon": "1h", "sidedness": "greater", "null_spec_id": None,
+            "test_spec_id": REFEREE_TEST_PERM_SPEC_ID, "target_sessions": REFEREE_MIN_SESSIONS,
+            "min_occurrences": REFEREE_MIN_OCCURRENCES, "registered_at": _REGISTERED_AT,
+        },
     ]
 
 
-def test_tc14_all_five_starter_candidates_register_cleanly_with_distinct_ids(stores):
+def test_tc14_all_six_starter_candidates_register_cleanly_with_distinct_ids(stores):
     family_store, hypothesis_store, _wd, _cert, _pb = stores
     recorded = []
     for payload in _starter_family_payloads():
         recorded.append(register_hypothesis(family_store, hypothesis_store, payload, confirm=True))
 
     hypothesis_ids = {r["hypothesis_id"] for r in recorded}
-    assert len(hypothesis_ids) == 5  # five DISTINCT ids
-    assert hypothesis_ids == {"hyp-s1", "hyp-s2", "hyp-s3", "hyp-s4", "hyp-s5"}
+    assert len(hypothesis_ids) == 6  # six DISTINCT ids
+    assert hypothesis_ids == {"hyp-s1", "hyp-s2", "hyp-s3", "hyp-s4", "hyp-s5", "hyp-s6"}
 
     by_id = {r["hypothesis_id"]: r for r in recorded}
     assert by_id["hyp-s1"]["estimand"] == "A" and by_id["hyp-s1"]["primary_horizon"] == "5m"
     assert by_id["hyp-s2"]["estimand"] == "A" and by_id["hyp-s2"]["primary_horizon"] == "1h"
     assert by_id["hyp-s3"]["estimand"] == "A" and by_id["hyp-s3"]["primary_horizon"] == "to_close"
     assert by_id["hyp-s4"]["estimand"] == "B" and by_id["hyp-s4"]["null_spec_id"] is None
+    assert by_id["hyp-s4"]["side"] == "long"
     assert by_id["hyp-s5"]["estimand"] == "C" and by_id["hyp-s5"]["null_spec_id"] == "referee-null-context-v1"
+    assert by_id["hyp-s6"]["estimand"] == "B" and by_id["hyp-s6"]["null_spec_id"] is None
+    assert by_id["hyp-s6"]["side"] == "short"  # the S-4 short-side sibling
 
     families, _errors = family_store.list()
     assert len(families) == 1  # one shared family -- the starter family
-    assert families[0]["candidate_hypothesis_ids"] == ["hyp-s1", "hyp-s2", "hyp-s3", "hyp-s4", "hyp-s5"]
+    assert families[0]["candidate_hypothesis_ids"] == [
+        "hyp-s1", "hyp-s2", "hyp-s3", "hyp-s4", "hyp-s5", "hyp-s6",
+    ]
 
 
 # === J-07 (iter-8): the starter-family shortlist -- GET .../registry/shortlist =========================
@@ -619,16 +634,20 @@ def test_tc14_all_five_starter_candidates_register_cleanly_with_distinct_ids(sto
 # the non-vacuous proof that the S-4/S-5 wiring genuinely discriminates.
 
 
-def test_tc1_shortlist_serves_exactly_five_pinned_candidates_with_non_negative_readiness(
+def test_tc1_shortlist_serves_six_pinned_candidates_with_non_negative_readiness(
     stores, bar_store,
 ):
+    """TC-16 (the S-6 half) + TC-17 (the family_id/family_q half), both folded into this file's
+    own pre-existing TC-1 shortlist test rather than duplicated: the shortlist now serves SIX
+    pinned candidates (S-1..S-5 plus iter-9's own S-4 short-side sibling, S-6) beside the
+    starter family's own registration-mechanics fields."""
     _fam, _hyp, _wd, _cert, playbook_store = stores  # an EMPTY corpus -- the honest baseline
     response = shortlist_response(
         playbook_store=playbook_store, config_fingerprint=CONFIG.config_fingerprint(),
         bar_store=bar_store, config=CONFIG,
     )
     candidates = response["candidates"]
-    assert [c["candidate_id"] for c in candidates] == ["S-1", "S-2", "S-3", "S-4", "S-5"]
+    assert [c["candidate_id"] for c in candidates] == ["S-1", "S-2", "S-3", "S-4", "S-5", "S-6"]
     for candidate in candidates:
         assert candidate["n"] >= 0
         assert candidate["n_sessions"] >= 0
@@ -652,15 +671,30 @@ def test_tc1_shortlist_serves_exactly_five_pinned_candidates_with_non_negative_r
         "backing_bucket": "at_wall",
     }
     assert by_id["S-4"]["null_spec_id"] is None  # Estimand B: no null population (spec Sec3.2)
+    assert by_id["S-4"]["side"] == "long"
     assert by_id["S-5"]["estimand"] == "C" and by_id["S-5"]["null_spec_id"] == "referee-null-context-v1"
+    # TC-16: S-6 is S-4's own short-side sibling -- same estimand/context/measure/horizon shape,
+    # ``_starter_context_readiness`` computed identically (the SAME primitive, just filtered on
+    # side="short" instead of "long").
+    assert (by_id["S-6"]["estimand"], by_id["S-6"]["setup_id"], by_id["S-6"]["side"]) == (
+        "B", "range_trade", "short",
+    )
+    assert by_id["S-6"]["context_predicate"] == {"backing_bucket": "at_wall"}
+    assert by_id["S-6"]["null_spec_id"] is None
+    assert by_id["S-6"]["primary_measure_key"] == by_id["S-4"]["primary_measure_key"] == "1h"
 
-    # These five are the exact SAME pinned definitions test_tc14 already registers through the
+    # These six are the exact SAME pinned definitions test_tc14 already registers through the
     # write path -- proof the shortlist's own module constants and the registration fixture stay
     # in lockstep (never two independently-drifting copies).
     assert [c["candidate_id"] for c in REFEREE_STARTER_FAMILY_SHORTLIST] == [
-        "S-1", "S-2", "S-3", "S-4", "S-5",
+        "S-1", "S-2", "S-3", "S-4", "S-5", "S-6",
     ]
 
+    # TC-17: family_id/family_q are served top-level, previously only an unowned frontend literal
+    # (apps/frontend/app/desk/page.tsx's REFEREE_STARTER_FAMILY_ID/REFEREE_STARTER_FAMILY_Q).
+    assert response["family_id"] == "referee-starter-family"
+    assert response["family_q"] == pytest.approx(0.10)
+
 
 def test_tc2_zero_jbe_long_signals_amid_a_nonempty_corpus_serves_zero_never_a_divide_by_zero(
     stores, bar_store,
@@ -716,13 +750,15 @@ def test_shortlist_projected_days_is_measured_from_zero_never_net_of_historical_
 
 def test_get_registry_shortlist_route_honest_state_against_a_real_empty_store(route_ctx):
     """TC-6 (the shortlist half): against the real store, with no operator action taken, the
-    shortlist still serves 5 candidates and the registry's own hypotheses list stays empty -- the
-    honest not-yet-acted state, never fabricated."""
+    shortlist still serves 6 candidates (S-1..S-5 plus iter-9's S-6) and the registry's own
+    hypotheses list stays empty -- the honest not-yet-acted state, never fabricated."""
     client, _tmp = route_ctx
     resp = client.get("/research/desk/referee/registry/shortlist")
     assert resp.status_code == 200
     body = resp.json()
-    assert [c["candidate_id"] for c in body["candidates"]] == ["S-1", "S-2", "S-3", "S-4", "S-5"]
+    assert [c["candidate_id"] for c in body["candidates"]] == ["S-1", "S-2", "S-3", "S-4", "S-5", "S-6"]
+    assert body["family_id"] == "referee-starter-family"
+    assert body["family_q"] == pytest.approx(0.10)
 
     registry = client.get("/research/desk/referee/registry")
     assert registry.json()["hypotheses"] == []
@@ -746,9 +782,9 @@ class _FakeWallResolver:
         }
 
 
-def _context_signal(*, entry: float, symbol: str) -> dict:
+def _context_signal(*, entry: float, symbol: str, side: str = "long") -> dict:
     return {
-        "setup_id": "range_trade", "side": "long", "symbol": symbol,
+        "setup_id": "range_trade", "side": side, "symbol": symbol,
         "trigger_ts": _et_instant_iso(2026, 6, 21, 10, 0),  # fixed instant -- irrelevant to the fake
         "entry": entry, "invalidation_price": entry - 0.5,
     }
@@ -784,18 +820,45 @@ def test_starter_context_readiness_discriminates_at_wall_from_off_wall_and_dedup
     assert n_sessions == 2  # 2026-06-21 and 2026-06-22 -- the same-session pair dedupes to one date
 
 
-def test_shortlist_s4_s5_readiness_reflects_the_at_wall_context_resolve(
+def test_starter_context_readiness_discriminates_the_s6_short_side_too(stores):
+    """TC-16's own non-vacuous proof for S-6 specifically (the S-4 short-side sibling, iter-9): the
+    IDENTICAL ``_starter_context_readiness`` primitive, filtered on ``side="short"`` instead of
+    ``"long"``, genuinely discriminates a short-side ``at_wall`` occurrence from a long-side one at
+    the SAME price (never conflating the two sides into one pool)."""
+    _fam, _hyp, _wd, _cert, playbook_store = stores
+    _plant_playbook_signals(
+        playbook_store, "2026-06-21",
+        [
+            _context_signal(entry=100.0, symbol="RTS", side="short"),  # at_wall, SHORT
+            _context_signal(entry=100.0, symbol="RTL", side="long"),  # at_wall, but LONG -- never counts
+        ],
+    )
+    records, _errors = playbook_store.list()
+    newest_by_date = referee_registry_module._newest_per_session_date(records)
+    n, n_sessions = referee_registry_module._starter_context_readiness(
+        newest_by_date, CONFIG.config_fingerprint(),
+        setup_id="range_trade", side="short", backing_bucket="at_wall",
+        context_resolver=_FakeWallResolver(),
+    )
+    assert n == 1 and n_sessions == 1  # RTS only -- RTL's long side never leaks in
+
+
+def test_shortlist_s4_s5_s6_readiness_reflects_the_at_wall_context_resolve(
     stores, bar_store, monkeypatch,
 ):
     """End-to-end wiring proof (not just the isolated helper above): ``shortlist_response()``
-    itself serves nonzero S-4/S-5 readiness when the corpus genuinely carries ``at_wall``
-    ``range_trade:long`` occurrences, by constructing a REAL ``BandMapResolver`` whose class this
-    test monkeypatches to the fake wall (the class-level substitution ``referee_adjudicate.py``'s
-    own estimand-B/C tests never needed, since those call the pooling function directly with an
-    injected resolver instead of letting it construct one)."""
+    itself serves nonzero S-4/S-5/S-6 readiness when the corpus genuinely carries ``at_wall``
+    ``range_trade`` occurrences on the matching side, by constructing a REAL ``BandMapResolver``
+    whose class this test monkeypatches to the fake wall (the class-level substitution
+    ``referee_adjudicate.py``'s own estimand-B/C tests never needed, since those call the pooling
+    function directly with an injected resolver instead of letting it construct one)."""
     _fam, _hyp, _wd, _cert, playbook_store = stores
     _plant_playbook_signals(
-        playbook_store, "2026-06-21", [_context_signal(entry=100.0, symbol="RTA")],
+        playbook_store, "2026-06-21",
+        [
+            _context_signal(entry=100.0, symbol="RTA", side="long"),
+            _context_signal(entry=100.0, symbol="RTB", side="short"),
+        ],
     )
     monkeypatch.setattr(
         referee_registry_module, "BandMapResolver", lambda *args, **kwargs: _FakeWallResolver()
@@ -807,6 +870,8 @@ def test_shortlist_s4_s5_readiness_reflects_the_at_wall_context_resolve(
     by_id = {c["candidate_id"]: c for c in response["candidates"]}
     assert by_id["S-4"]["n"] == 1 and by_id["S-4"]["n_sessions"] == 1
     assert by_id["S-5"]["n"] == 1 and by_id["S-5"]["n_sessions"] == 1
+    assert by_id["S-6"]["n"] == 1 and by_id["S-6"]["n_sessions"] == 1
+    assert by_id["S-5"]["n"] == 1 and by_id["S-5"]["n_sessions"] == 1
 
 
 # === TC-9 / TC-10 (iter-8): the write path stays generic; discovery is boundary-gated on
@@ -852,6 +917,93 @@ def test_tc10_a_deep_backfilled_pre_boundary_record_lands_in_discovery_never_acc
     assert folded["accrual"]["informative_post_boundary_sessions"] == 1  # 2026-06-11 only
 
 
+# === TC-15 (goal-referee-iter-9 rider): a B/C hypothesis's accrual/discovery now apply the SAME
+# context_predicate/backing-bucket check the shortlist's own live readiness already applies ===========
+
+
+def test_tc15_a_context_hypothesis_accrual_and_discovery_agree_with_the_shortlist_readiness(
+    stores, bar_store, monkeypatch,
+):
+    """TC-15: before this rider, ``_hypothesis_accrual``/``_hypothesis_discovery`` counted EVERY
+    ``range_trade:long`` signal regardless of context, disagreeing with the shortlist's own S-4/S-5
+    live readiness (which already applied the ``at_wall`` predicate). A registered Estimand-B
+    hypothesis's own ``accrual``/``discovery`` now agree with ``_starter_context_readiness`` for the
+    IDENTICAL ``(setup_id, side, context_predicate)`` cell: an ``off_wall`` occurrence in the SAME
+    session as an ``at_wall`` one must never count toward either block."""
+    family_store, hypothesis_store, withdrawal_store, cert_store, playbook_store = stores
+    payload = _estimand_a_payload(
+        "hyp-tc15-b", "fam-tc15-b", estimand="B", setup_id="range_trade", side="long",
+        context_predicate={"backing_bucket": "at_wall"}, null_spec_id=None,
+    )
+    register_hypothesis(family_store, hypothesis_store, payload, confirm=True)
+
+    # Pre-boundary (discovery-only): one at_wall, one off_wall -- only the at_wall one counts.
+    _plant_playbook_signals(
+        playbook_store, "2026-06-01",
+        [
+            _context_signal(entry=100.0, symbol="RTA", side="long"),  # at_wall
+            _context_signal(entry=110.0, symbol="RTB", side="long"),  # off_wall -- must NEVER count
+        ],
+    )
+    # Post-boundary (accrual): one at_wall, one off_wall in the SAME session -- only at_wall counts.
+    _plant_playbook_signals(
+        playbook_store, "2026-06-11",
+        [
+            _context_signal(entry=99.95, symbol="RTC", side="long"),  # at_wall
+            _context_signal(entry=120.0, symbol="RTD", side="long"),  # off_wall -- must NEVER count
+        ],
+    )
+    # A SECOND post-boundary session, off_wall only -- must contribute to neither block.
+    _plant_playbook_signals(
+        playbook_store, "2026-06-12", [_context_signal(entry=130.0, symbol="RTE", side="long")],
+    )
+
+    monkeypatch.setattr(
+        referee_registry_module, "BandMapResolver", lambda *args, **kwargs: _FakeWallResolver()
+    )
+    response = registry_response(
+        family_store=family_store, hypothesis_store=hypothesis_store,
+        withdrawal_store=withdrawal_store, certificate_store=cert_store,
+        playbook_store=playbook_store, config_fingerprint=CONFIG.config_fingerprint(),
+        bar_store=bar_store, config=CONFIG,
+    )
+    folded = next(h for h in response["hypotheses"] if h["hypothesis_id"] == "hyp-tc15-b")
+    # Before this rider these would have read 2 (both signals per session counted blindly).
+    assert folded["discovery"]["n_sessions"] == 1  # 2026-06-01 only (its at_wall signal)
+    assert folded["discovery"]["n"] == 1
+    assert folded["accrual"]["informative_post_boundary_sessions"] == 1  # 2026-06-11 only
+
+    # Cross-check against the shortlist's own live readiness for the IDENTICAL cell (S-4:
+    # range_trade:long at_wall) -- both readers must agree, never independently drift.
+    shortlist = shortlist_response(
+        playbook_store=playbook_store, config_fingerprint=CONFIG.config_fingerprint(),
+        bar_store=bar_store, config=CONFIG,
+    )
+    s4 = next(c for c in shortlist["candidates"] if c["candidate_id"] == "S-4")
+    # The shortlist pools the WHOLE corpus (pre+post boundary, exploratory forever): RTA (06-01) +
+    # RTC (06-11) are the only two at_wall occurrences, across 2 distinct sessions.
+    assert s4["n"] == 2 and s4["n_sessions"] == 2
+
+
+def test_registry_call_sites_without_bar_store_are_unaffected_estimand_a_only(stores):
+    """Backward-compatibility proof: EVERY caller omitting the new optional ``bar_store``/
+    ``config`` (the pre-iter-9 call shape) still folds correctly for an Estimand-A hypothesis
+    (``context_predicate is None``, the ONLY kind this era's OWN real registrations use) -- the
+    short-circuit in the shared helper never even looks at ``context_resolver``."""
+    family_store, hypothesis_store, withdrawal_store, cert_store, playbook_store = stores
+    payload = _estimand_a_payload("hyp-tc15-compat", "fam-tc15-compat")
+    register_hypothesis(family_store, hypothesis_store, payload, confirm=True)
+    _plant_playbook_signals(playbook_store, "2026-06-11", [_signal("capitulation", "long")])
+
+    response = registry_response(  # no bar_store/config -- the pre-iter-9 call shape
+        family_store=family_store, hypothesis_store=hypothesis_store,
+        withdrawal_store=withdrawal_store, certificate_store=cert_store,
+        playbook_store=playbook_store, config_fingerprint=CONFIG.config_fingerprint(),
+    )
+    folded = next(h for h in response["hypotheses"] if h["hypothesis_id"] == "hyp-tc15-compat")
+    assert folded["accrual"]["informative_post_boundary_sessions"] == 1
+
+
 # === family/hypothesis coupling: consistency + "no candidate joins retroactively" =====================
 
 
diff --git a/apps/frontend/app/desk/page.tsx b/apps/frontend/app/desk/page.tsx
index 29c2c1b..4492f67 100644
--- a/apps/frontend/app/desk/page.tsx
+++ b/apps/frontend/app/desk/page.tsx
@@ -350,16 +350,12 @@ const PRIMARY_BUTTON_CLASS =
 const CANCEL_BUTTON_CLASS =
   "mt-1 rounded-md border border-slate-700 bg-transparent px-2.5 py-1 text-xs font-medium text-slate-400 transition-colors hover:border-slate-500 hover:text-slate-200 focus:outline-none focus:ring-1 focus:ring-red-500 disabled:cursor-not-allowed disabled:opacity-50";
 
-// goal-referee-iter-8 (J-07): the starter family's own registration-mechanics constants -- the
-// shortlist response (RefereeShortlistCandidate) carries every OTHER field a registration payload
-// needs verbatim, but not these three (spec Sec7's shortlist describes research QUESTIONS, not
-// registration mechanics). `family_q` mirrors REFEREE_DEFAULT_Q (0.10,
-// docs/referee-statistical-spec.md Sec1) -- the same value test_referee_registry.py's own
-// `_starter_family_payloads()` fixture already uses for all five candidates. The candidate id SET
-// itself is never hard-coded here — it is read live off the fetched shortlist's own
-// `candidate_id`s at submit time (goal.md J-07 Step 2: "no hard-coded hypothesis set").
-const REFEREE_STARTER_FAMILY_ID = "referee-starter-family";
-const REFEREE_STARTER_FAMILY_Q = 0.1;
+// goal-referee-iter-8 (J-07) / goal-referee-iter-9 (rider): the starter family's own
+// registration-mechanics fields -- `family_id`/`family_q` are now read live off the fetched
+// shortlist response itself (RefereeShortlistResponse, backend-owned as of iter-9; previously two
+// unowned local literals here). The candidate id SET is likewise never hard-coded — it is read
+// live off the fetched shortlist's own `candidate_id`s at submit time (goal.md J-07 Step 2: "no
+// hard-coded hypothesis set"). See `handleRegisterRefereeCandidate` below.
 
 // The as-of day text fields (forward-test era) — mirrors structure/page.tsx's own `INPUT_CLASS`
 // shape (each page owns its own copy of this tiny constant per this project's established
@@ -7763,6 +7759,8 @@ export default function DeskPage() {
   // candidate's OWN fields verbatim (never hand-typed or re-derived) plus the caller's own family
   // framing; on success, re-fetches the registry so the new row renders complete with its
   // status/accrual/discovery fold additions (which the POST response itself does not carry).
+  // goal-referee-iter-9 rider: `family_id`/`family_q` are now read live off the fetched shortlist
+  // response itself (backend-owned as of this iteration), never a local literal.
   async function handleRegisterRefereeCandidate(candidate: RefereeShortlistCandidate) {
     const shortlist = refereeShortlistResult?.data;
     if (!shortlist) return;
@@ -7771,8 +7769,8 @@ export default function DeskPage() {
     const result = await postRefereeRegistryHypothesis({
       confirm: true,
       hypothesis_id: candidate.candidate_id,
-      family_id: REFEREE_STARTER_FAMILY_ID,
-      family_q: REFEREE_STARTER_FAMILY_Q,
+      family_id: shortlist.family_id,
+      family_q: shortlist.family_q,
       family_candidate_hypothesis_ids: shortlist.candidates.map((c) => c.candidate_id),
       evidence_family: candidate.evidence_family,
       estimand: candidate.estimand,
diff --git a/apps/frontend/lib/types.ts b/apps/frontend/lib/types.ts
index 9ed44db..592a0ab 100644
--- a/apps/frontend/lib/types.ts
+++ b/apps/frontend/lib/types.ts
@@ -2156,8 +2156,13 @@ export interface RefereeShortlistCandidate {
   projected_days_to_target: number | null;
 }
 
+// goal-referee-iter-9 rider: `family_id`/`family_q` are the starter family's own
+// registration-mechanics fields, moved backend-side (previously only an unowned
+// apps/frontend/app/desk/page.tsx literal) -- served here for the first time.
 export interface RefereeShortlistResponse {
   candidates: RefereeShortlistCandidate[];
+  family_id: string;
+  family_q: number;
 }
 
 // The read-side fold additions GET /research/desk/referee/registry adds to every hypothesis
```
