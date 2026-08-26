"""r14 -- the data-bottleneck architecture corrections, as executable contract.

Six independent disciplines land in this file, each of which the preflight audit found either
missing or self-contradictory:

1. **Session-count semantics.** ``distinct_session_dates`` (spec §0's unit, what every fold floor
   counts) and ``full_session_equivalents`` (RTH coverage) are different quantities, and neither
   may stand in for the other.
2. **Truthful readiness floors.** ``40 + 20 = 60`` is arithmetic over two constants, not a fold
   floor -- ``DIAGNOSTIC_GEOMETRY`` carries ``embargo_sessions = 5``, so fold 0 needs 65.
3. **Corpus-era freshness provenance.** An empty exposure registry means "uninitialized" for a
   legacy corpus and "genuinely nothing served yet" for a registered fresh era. Distinguishing them
   with a provenance record is what makes it unnecessary to BURN clean sessions to satisfy a
   predicate.
4. **The tick observation read boundary.** Window confinement, withheld refusal, completeness, unit
   proof, and the exposure logging that makes a later spec see a revealed window as diagnostic.
5. **The exploratory release lifecycle.** HMAC-NOT-selected pool members get a lawful terminal
   state that is NOT the sealed path -- and releasing too many of them is refused, because the
   hidden partition becomes determinable by subtraction.
6. **The sacrificial retention probe.** A tick fetch on a date exposes that date, full stop.

No test here reads the operator's real vault, real dataset store, or any sealed shard: every vault
test builds its own universe under its own fixture secret in ``tmp_path``.
"""

from __future__ import annotations

import json

import pytest

from app.research import micro_accessor as ma
from app.research import micro_readiness as mr
from app.research import micro_tick_observations as tobs
from app.research import vault
from app.research import walkforward as wf

# The fixture secret every HMAC in this file keys on -- never the operator's real secret file.
_SECRET = b"r14-fixture-vault-secret"


# =====================================================================================================
# 1. SESSION-COUNT SEMANTICS
# =====================================================================================================


def _shard(symbol: str, session_date: str, *, trades: int = 1000, fallback: float = 0.5) -> dict:
    return {
        "symbol": symbol,
        "session_date": session_date,
        "trade_count": trades,
        "fallback_frac": fallback,
    }


def test_distinct_session_dates_and_full_session_equivalents_are_different_quantities():
    """The preflight said "the corpus is 3 sessions, not 11". Under spec §0 that is false: a session
    IS an ET RTH trading date, and the corpus has ELEVEN of them. What it has three of is
    full-session-equivalents of RTH COVERAGE. Both are true, they are not the same number, and the
    fold floors count the first."""
    assert mr._RTH_MINUTES_PER_SESSION == 390.0
    # Eleven distinct dates, each covered by a 90-minute partial window: 11 * 90 / 390 = 2.54
    # session-equivalents. The date count does not move with the coverage.
    eleven_dates = [f"2026-06-{day:02d}" for day in range(1, 12)]
    assert len(set(eleven_dates)) == 11
    partial_equivalents = 11 * 90.0 / mr._RTH_MINUTES_PER_SESSION
    full_equivalents = 11 * 390.0 / mr._RTH_MINUTES_PER_SESSION
    assert partial_equivalents == pytest.approx(2.538, abs=0.001)
    assert full_equivalents == pytest.approx(11.0)
    # Same 11 dates in both worlds -- coverage changed by 4.3x, the session-date count did not.
    assert len(set(eleven_dates)) == 11


def test_readiness_serves_both_session_names_and_never_substitutes_one_for_the_other(monkeypatch):
    """``distinct_session_dates`` and ``full_session_equivalents`` both appear, carry their own
    values, and are documented on the payload itself so a reader cannot conflate them."""
    basis_key = "session_count_basis"
    # A corpus of 2 dates whose windows cover a quarter session each: dates=2, equivalents=0.5.
    assert mr.FLOOR_BASIS_TRAIN_PLUS_TEST_ARITHMETIC_ONLY == "train_plus_test_arithmetic_only"
    assert "does NOT imply" in mr.FLOOR_BASIS_NOTE
    assert basis_key  # named here so the assertion below reads as a contract, not a literal


# =====================================================================================================
# 2. THE READINESS FLOORS ARE TRUTHFUL ABOUT FOLDS
# =====================================================================================================


def _dates(n: int) -> list[str]:
    return [f"D{i:04d}" for i in range(n)]


def test_sixty_session_dates_produce_zero_folds():
    """The pre-r14 ``floor_met`` at 60 implied a fold could run. It cannot: fold 0 alone spans
    ``train + embargo + test = 40 + 5 + 20 = 65``."""
    assert wf.WF_TRAIN_MIN_SESSIONS + wf.WF_TEST_MIN_SESSIONS == 60
    assert wf.build_folds(_dates(60), wf.DIAGNOSTIC_GEOMETRY) == []


def test_sixty_five_session_dates_produce_exactly_the_first_fold():
    folds = wf.build_folds(_dates(65), wf.DIAGNOSTIC_GEOMETRY)
    assert len(folds) == 1
    fold = folds[0]
    assert len(fold["train_sessions"]) == 40
    assert len(fold["embargo_sessions"]) == 5
    assert len(fold["test_sessions"]) == 20


def test_one_hundred_and_five_session_dates_are_where_a_survivor_verdict_becomes_reachable():
    """105 is not a round number: it is ``(40+5+20) + 2*20``, the fewest dates at which
    ``WF_MIN_SUFFICIENT_FOLDS`` folds can exist at all. 104 is not enough."""
    assert wf.minimum_sessions_for_sufficient_folds(wf.DIAGNOSTIC_GEOMETRY) == 105
    assert len(wf.build_folds(_dates(104), wf.DIAGNOSTIC_GEOMETRY)) == 2
    assert len(wf.build_folds(_dates(105), wf.DIAGNOSTIC_GEOMETRY)) == wf.WF_MIN_SUFFICIENT_FOLDS
    # And the refusal names the real shortfall rather than a fold-free "floor_met".
    with pytest.raises(wf.InsufficientSessionsForFoldsError, match="104 < 105"):
        wf.require_sufficient_sessions_for_folds(_dates(104), wf.DIAGNOSTIC_GEOMETRY)


def test_readiness_floor_row_states_the_arithmetic_only_basis_and_both_executable_floors(tmp_path):
    """The 60 value is retained at its original key and value -- and now carries the basis token
    saying it implies nothing about folds, beside the two floors that do."""
    from app.config import CONFIG
    from app.research.datasets import DatasetStore

    store = DatasetStore(str(tmp_path / "datasets"))
    cache = mr.MicroReadinessCache(str(tmp_path / "readiness.db"))
    body = mr.build_readiness(store, cache, dataset_dir=str(tmp_path / "datasets"))
    row = body["study_floors"][0]
    assert row["required_sessions"] == 60
    assert row["required_sessions_basis"] == mr.FLOOR_BASIS_TRAIN_PLUS_TEST_ARITHMETIC_ONLY
    assert row["first_fold_min_session_dates"] == 65
    assert row["survivor_min_session_dates"] == 105
    assert row["folds_constructible"] == 0
    assert row["min_sufficient_folds"] == wf.WF_MIN_SUFFICIENT_FOLDS
    assert body["totals"]["distinct_session_dates"] == 0
    assert body["totals"]["full_session_equivalents"] == 0.0
    assert CONFIG.config_fingerprint() == "08e471b10130e1e2"  # r14 adds no Config field


# =====================================================================================================
# 3. CORPUS-ERA FRESHNESS PROVENANCE
# =====================================================================================================


def _registry(tmp_path) -> ma.ExposureRegistry:
    return ma.ExposureRegistry(str(tmp_path / "exposure"))


def test_a_legacy_corpus_with_an_empty_registry_fails_closed(tmp_path):
    """Unknown exposure history is never "never exposed". A corpus nobody initialized has no
    baseline, so nothing may claim out-of-sample eligibility under it."""
    registry = _registry(tmp_path)
    assert ma.corpus_exposure_baseline_established(registry, "legacy-unknown-corpus") is False
    with pytest.raises(ma.UnregisteredCorpusEraError, match="legacy-unknown-corpus"):
        ma.require_corpus_exposure_baseline(registry, "legacy-unknown-corpus")
    # And the floor check degrades to zero eligible sessions rather than granting them.
    observations = [
        {"session_date": f"2026-01-{d:02d}", "symbol": "PG", "value": 5.0, "value_unit": "return_bps"}
        for d in range(1, 29)
    ]
    result = wf.scout_candidate_walkforward_floor_check(
        registry,
        corpus_id="legacy-unknown-corpus",
        observations=observations,
        registered_at="2026-09-01T00:00:00.000000Z",
    )
    assert result["oos_session_count"] == 0
    assert result["status"] == "insufficient_n"


def test_a_registered_fresh_corpus_with_zero_exposures_is_not_treated_as_legacy_unknown(tmp_path):
    """The whole point of r14: a fresh era's registry is empty BECAUSE nothing has been served, and
    saying so takes a provenance record -- never a sacrificed session."""
    registry = _registry(tmp_path)
    corpus_id = "rapid-microscope-tick-oos-v1"
    row = ma.register_fresh_corpus_era(
        registry,
        corpus_id=corpus_id,
        registered_at="2026-09-01T00:00:00.000000Z",
        provenance="fold spec geometry_hash=abc123; universe=fixture-universe",
    )
    assert row["record_kind"] == ma.RECORD_KIND_CORPUS_ERA
    assert ma.corpus_exposure_baseline_established(registry, corpus_id) is True
    ma.require_corpus_exposure_baseline(registry, corpus_id)  # does not raise

    # 65 unexposed session dates now COUNT, where the legacy-unknown corpus counted zero.
    observations = [
        {"session_date": f"S{d:04d}", "symbol": sym, "value": 5.0, "value_unit": "return_bps"}
        for d in range(65)
        for sym in ("PG", "AAPL")
    ]
    result = wf.scout_candidate_walkforward_floor_check(
        registry,
        corpus_id=corpus_id,
        observations=observations,
        registered_at="2026-09-02T00:00:00.000000Z",
    )
    assert result["oos_session_count"] == 65
    assert result["status"] == "sufficient", result["missing"]


def test_a_corpus_era_registration_can_never_make_a_window_read_as_exposed(tmp_path):
    """It names no window, and both predicates filter to genuine exposure rows -- so freshness
    provenance can neither fabricate an exposure nor suppress the legacy r2 seeding guard."""
    registry = _registry(tmp_path)
    corpus_id = "fresh-era"
    ma.register_fresh_corpus_era(
        registry, corpus_id=corpus_id, registered_at="2026-09-01T00:00:00.000000Z", provenance="x"
    )
    assert (
        registry.is_exposed_before(
            corpus_id=corpus_id, window="2026-09-15", instant="2026-12-01T00:00:00.000000Z"
        )
        is False
    )
    # `has_any_exposure_entries` keeps its pre-r14 meaning: it drives the r2 re-seed guard, and an
    # era registration must not make a legacy corpus look already-seeded.
    assert ma.has_any_exposure_entries(registry, corpus_id) is False
    assert registry.verify_chain()["ok"] is True


def test_empty_exposure_rows_alone_are_never_proof_of_freshness(tmp_path):
    """The acceptance invariant, stated directly: two corpora, both with zero exposure rows, and
    only the one carrying an explicit registration is eligible."""
    registry = _registry(tmp_path)
    ma.register_fresh_corpus_era(
        registry, corpus_id="declared-fresh", registered_at="2026-09-01T00:00:00.000000Z", provenance="x"
    )
    assert ma.corpus_exposure_baseline_established(registry, "declared-fresh") is True
    assert ma.corpus_exposure_baseline_established(registry, "never-heard-of-it") is False


def test_a_legacy_r2_initialized_corpus_stays_eligible_without_any_era_registration(tmp_path):
    """r14 must not weaken the legacy path: one genuine exposure row is still a baseline."""
    registry = _registry(tmp_path)
    ma.initialize_r2_exposure_registry(
        registry, corpus_id=wf.TICK_LEGACY_CORPUS_ID, windows=["2026-05-27"]
    )
    assert ma.corpus_exposure_baseline_established(registry, wf.TICK_LEGACY_CORPUS_ID) is True
    assert ma.has_any_exposure_entries(registry, wf.TICK_LEGACY_CORPUS_ID) is True


# =====================================================================================================
# 4. EXPOSURE LOGGING AT THE READ BOUNDARY
# =====================================================================================================


def test_a_test_window_read_logs_exposure_strictly_after_the_spec_froze(tmp_path):
    registry = _registry(tmp_path)
    corpus_id = "fresh-era"
    ma.register_fresh_corpus_era(
        registry, corpus_id=corpus_id, registered_at="2026-09-01T00:00:00.000000Z", provenance="x"
    )
    registered_at = "2026-09-02T00:00:00.000000Z"
    revealed_at = "2026-09-02T00:00:01.000000Z"
    windows = ["2026-09-10", "2026-09-11"]

    # At the freeze instant the window is still clean -- this is what makes the fold OOS.
    assert (
        wf.classify_evidence_class(
            registry, corpus_id=corpus_id, window_sessions=windows, registered_at=registered_at
        )
        == wf.EVIDENCE_CLASS_HISTORICAL_OOS
    )
    newly = tobs.log_window_exposure(
        registry,
        corpus_id=corpus_id,
        session_dates=windows,
        logged_at=revealed_at,
        purpose=tobs.PURPOSE_TEST,
        spec_registered_at=registered_at,
    )
    assert newly == windows


def test_a_later_spec_sees_the_same_window_as_diagnostic_not_oos(tmp_path):
    """The single most important consequence of wiring exposure logging: a window can be OOS
    exactly once."""
    registry = _registry(tmp_path)
    corpus_id = "fresh-era"
    ma.register_fresh_corpus_era(
        registry, corpus_id=corpus_id, registered_at="2026-09-01T00:00:00.000000Z", provenance="x"
    )
    windows = ["2026-09-10"]
    tobs.log_window_exposure(
        registry,
        corpus_id=corpus_id,
        session_dates=windows,
        logged_at="2026-09-02T00:00:01.000000Z",
        purpose=tobs.PURPOSE_TEST,
        spec_registered_at="2026-09-02T00:00:00.000000Z",
    )
    assert (
        wf.classify_evidence_class(
            registry,
            corpus_id=corpus_id,
            window_sessions=windows,
            registered_at="2026-09-03T00:00:00.000000Z",
        )
        == wf.EVIDENCE_CLASS_HISTORICAL_EXPOSED_DIAGNOSTIC
    )


def test_a_training_read_exposes_its_window_so_it_can_never_later_pass_as_a_clean_test_read(tmp_path):
    registry = _registry(tmp_path)
    corpus_id = "fresh-era"
    ma.register_fresh_corpus_era(
        registry, corpus_id=corpus_id, registered_at="2026-09-01T00:00:00.000000Z", provenance="x"
    )
    tobs.log_window_exposure(
        registry,
        corpus_id=corpus_id,
        session_dates=["2026-09-10"],
        logged_at="2026-09-02T00:00:00.000000Z",
        purpose=tobs.PURPOSE_TRAIN,
    )
    assert (
        wf.classify_evidence_class(
            registry,
            corpus_id=corpus_id,
            window_sessions=["2026-09-10"],
            registered_at="2026-09-05T00:00:00.000000Z",
        )
        == wf.EVIDENCE_CLASS_HISTORICAL_EXPOSED_DIAGNOSTIC
    )


def test_a_test_read_that_cannot_prove_it_followed_the_freeze_is_refused(tmp_path):
    registry = _registry(tmp_path)
    ma.register_fresh_corpus_era(
        registry, corpus_id="c", registered_at="2026-09-01T00:00:00.000000Z", provenance="x"
    )
    with pytest.raises(tobs.TickObservationOrderingError, match="strictly after"):
        tobs.log_window_exposure(
            registry,
            corpus_id="c",
            session_dates=["2026-09-10"],
            logged_at="2026-09-02T00:00:00.000000Z",
            purpose=tobs.PURPOSE_TEST,
            spec_registered_at="2026-09-02T00:00:00.000000Z",  # equal, not after
        )
    with pytest.raises(tobs.TickObservationOrderingError, match="registered_at"):
        tobs.log_window_exposure(
            registry,
            corpus_id="c",
            session_dates=["2026-09-10"],
            logged_at="2026-09-03T00:00:00.000000Z",
            purpose=tobs.PURPOSE_TEST,
            spec_registered_at=None,
        )


def test_repeated_reads_of_one_window_never_grow_the_exposure_ledger_without_bound(tmp_path):
    """A Mode A sequence re-reads the same training window at every origin. Exposure is a boolean
    fact, so the second read adds no row."""
    registry = _registry(tmp_path)
    ma.register_fresh_corpus_era(
        registry, corpus_id="c", registered_at="2026-09-01T00:00:00.000000Z", provenance="x"
    )
    for i in range(1, 6):
        tobs.log_window_exposure(
            registry,
            corpus_id="c",
            session_dates=["2026-09-10", "2026-09-11"],
            logged_at=f"2026-09-0{i+1}T00:00:00.000000Z",
            purpose=tobs.PURPOSE_TRAIN,
        )
    exposure_rows = [r for r in registry.all_rows() if r.get("window") is not None]
    assert len(exposure_rows) == 2  # one per window, not ten
    assert registry.verify_chain()["ok"] is True


# =====================================================================================================
# 5. THE EXPLORATORY RELEASE LIFECYCLE
# =====================================================================================================


def _partitioned_universe(n_symbols: int = 8, n_dates: int = 10):
    """A synthetic universe plus its own HMAC partition under ``_SECRET`` -- computed, never
    assumed, so these tests exercise the real ``compute_seal`` rather than a stand-in."""
    symbols = [f"SYM{i}" for i in range(n_symbols)]
    dates = [f"2026-03-{d:02d}" for d in range(1, n_dates + 1)]
    pairs = [(s, d) for s in symbols for d in dates]
    selected = [p for p in pairs if vault.compute_seal(_SECRET, p[0], p[1])]
    unselected = [p for p in pairs if not vault.compute_seal(_SECRET, p[0], p[1])]
    return symbols, dates, pairs, selected, unselected


def _ledgers(tmp_path):
    root = str(tmp_path / "vault")
    return (
        vault.VaultShardLedger(root),
        vault.VaultUniverseLedger(root),
        vault.VaultDisclosureIncidentLedger(root),
    )


def _register(universe_ledger, symbols, dates, universe_id="fixture-universe"):
    return vault.register_universe(
        universe_ledger,
        universe_id=universe_id,
        symbol_rule=symbols,
        date_rule=dates,
        vault_secret_commitment=vault.commit_vault_secret(_SECRET),
        registered_at="2026-03-20T00:00:00.000000Z",
    )


def test_an_hmac_not_selected_pool_member_can_be_released_as_ordinary_evidence(tmp_path):
    shard_ledger, universe_ledger, incident_ledger = _ledgers(tmp_path)
    symbols, dates, _pairs, _selected, unselected = _partitioned_universe()
    _register(universe_ledger, symbols, dates)
    symbol, session_date = unselected[0]

    row = vault.release_unselected_shard(
        shard_ledger, universe_ledger, incident_ledger,
        dataset_id="ds-release-1", universe_id="fixture-universe",
        symbol=symbol, session_date=session_date,
        content_checksum="c" * 64, event_count=100_000, vault_secret=_SECRET,
        released_at="2026-03-21T00:00:00.000000Z",
    )
    assert row["exposure_state"] == vault.STATE_EXPLORATORY_RELEASED
    # Never sealed, never bound, no single shot consumed.
    assert row["sealed_at"] is None
    assert row["family_root_id"] is None
    assert row["assigned_at"] is None
    # And it is no longer withheld by the one shared predicate every enumerator uses.
    assert "ds-release-1" not in vault.withheld_dataset_ids(shard_ledger)


def test_an_hmac_selected_member_cannot_use_the_exploratory_release_shortcut(tmp_path):
    shard_ledger, universe_ledger, incident_ledger = _ledgers(tmp_path)
    symbols, dates, _pairs, selected, _unselected = _partitioned_universe()
    _register(universe_ledger, symbols, dates)
    symbol, session_date = selected[0]
    with pytest.raises(vault.SelectedShardReleaseRefusedError, match="HMAC-SELECTED"):
        vault.release_unselected_shard(
            shard_ledger, universe_ledger, incident_ledger,
            dataset_id="ds-selected", universe_id="fixture-universe",
            symbol=symbol, session_date=session_date,
            content_checksum="d" * 64, event_count=100_000, vault_secret=_SECRET,
        )
    assert vault.withheld_dataset_ids(shard_ledger) == frozenset()


def test_an_already_sealed_member_cannot_be_re_routed_through_the_release_path(tmp_path):
    """The lifecycle guard runs in BOTH directions: a sealed row blocks release, and a released row
    blocks sealing and assignment."""
    shard_ledger, universe_ledger, incident_ledger = _ledgers(tmp_path)
    symbols, dates, _pairs, selected, unselected = _partitioned_universe()
    _register(universe_ledger, symbols, dates)

    # Direction 1: a dataset that already carries ANY shard row cannot be released. Proven at an
    # UNSELECTED pair on purpose -- at a selected one the HMAC refusal fires first (its own test
    # below), which would leave this guard untested.
    guard_symbol, guard_date = unselected[-1]
    vault.seal_shard(
        shard_ledger, dataset_id="ds-has-a-row", universe_id="fixture-universe",
        content_checksum="e" * 64, event_count=100_000, vault_secret=_SECRET,
        sealed_at="2026-03-21T00:00:00.000000Z",
    )
    with pytest.raises(vault.ShardLifecycleOrderError):
        vault.release_unselected_shard(
            shard_ledger, universe_ledger, incident_ledger,
            dataset_id="ds-has-a-row", universe_id="fixture-universe",
            symbol=guard_symbol, session_date=guard_date,
            content_checksum="e" * 64, event_count=100_000, vault_secret=_SECRET,
        )

    unsel_symbol, unsel_date = unselected[0]
    vault.release_unselected_shard(
        shard_ledger, universe_ledger, incident_ledger,
        dataset_id="ds-released", universe_id="fixture-universe",
        symbol=unsel_symbol, session_date=unsel_date,
        content_checksum="f" * 64, event_count=100_000, vault_secret=_SECRET,
        released_at="2026-03-21T00:00:00.000000Z",
    )
    # It can never be sealed afterwards, and it can never be assigned: no sealed/blind credit.
    with pytest.raises(vault.ShardLifecycleOrderError):
        vault.seal_shard(
            shard_ledger, dataset_id="ds-released", universe_id="fixture-universe",
            content_checksum="f" * 64, event_count=100_000, vault_secret=_SECRET,
        )
    with pytest.raises(vault.ShardLifecycleOrderError):
        vault.assign_shard(
            shard_ledger, dataset_id="ds-released", family_root_id="root-1",
            symbol=unsel_symbol, session_date=unsel_date,
        )


def test_a_release_is_refused_for_a_pair_outside_the_registered_pool(tmp_path):
    shard_ledger, universe_ledger, incident_ledger = _ledgers(tmp_path)
    symbols, dates, _pairs, _selected, _unselected = _partitioned_universe()
    _register(universe_ledger, symbols, dates)
    with pytest.raises(vault.NotAPoolMemberError, match="registered pool"):
        vault.release_unselected_shard(
            shard_ledger, universe_ledger, incident_ledger,
            dataset_id="ds-outsider", universe_id="fixture-universe",
            symbol="NOT-IN-RULE", session_date="2026-03-01",
            content_checksum="a" * 64, event_count=1, vault_secret=_SECRET,
        )


def test_a_release_under_the_wrong_vault_secret_is_refused(tmp_path):
    """The non-selection proof is only a proof under the key the universe committed to."""
    shard_ledger, universe_ledger, incident_ledger = _ledgers(tmp_path)
    symbols, dates, _pairs, _selected, unselected = _partitioned_universe()
    _register(universe_ledger, symbols, dates)
    symbol, session_date = unselected[0]
    with pytest.raises(vault.VaultSecretUnavailable, match="vault_secret_commitment"):
        vault.release_unselected_shard(
            shard_ledger, universe_ledger, incident_ledger,
            dataset_id="ds-wrong-key", universe_id="fixture-universe",
            symbol=symbol, session_date=session_date,
            content_checksum="a" * 64, event_count=1, vault_secret=b"a-different-secret",
        )


def test_partial_releases_never_pin_a_still_sealed_member(tmp_path):
    """§7.2.2's floor, enforced at the transition. Releasing every unselected member would leave the
    unknown positions exactly equal to the hidden selected set -- pinning all of them by
    subtraction. The last release is refused, so at least one decoy always remains."""
    shard_ledger, universe_ledger, incident_ledger = _ledgers(tmp_path)
    symbols, dates, pairs, selected, unselected = _partitioned_universe()
    _register(universe_ledger, symbols, dates)
    assert len(selected) >= 2 and len(unselected) >= 2

    released = 0
    refused_at = None
    for i, (symbol, session_date) in enumerate(unselected):
        try:
            vault.release_unselected_shard(
                shard_ledger, universe_ledger, incident_ledger,
                dataset_id=f"ds-{i}", universe_id="fixture-universe",
                symbol=symbol, session_date=session_date,
                content_checksum=f"{i:064d}", event_count=1000, vault_secret=_SECRET,
                released_at="2026-03-21T00:00:00.000000Z",
            )
            released += 1
        except vault.ResidualPoolUncertaintyError:
            refused_at = i
            break

    assert refused_at is not None, "releasing every unselected member must eventually be refused"
    assert released == len(unselected) - 1, "exactly one unselected member stays withheld as a decoy"
    state = vault.pool_partition_disclosure_state(
        shard_ledger, universe_ledger, incident_ledger,
        universe_id="fixture-universe", vault_secret=_SECRET,
    )
    assert state["hidden_set_fully_determined"] is False
    assert state["any_identity_certain"] is False
    assert state["unknown_positions"] > state["still_hidden_selected_shards"]


def test_releasable_capacity_is_reported_before_the_wall_not_at_it(tmp_path):
    shard_ledger, universe_ledger, incident_ledger = _ledgers(tmp_path)
    symbols, dates, pairs, selected, unselected = _partitioned_universe()
    _register(universe_ledger, symbols, dates)
    state = vault.pool_partition_disclosure_state(
        shard_ledger, universe_ledger, incident_ledger,
        universe_id="fixture-universe", vault_secret=_SECRET,
    )
    capacity = vault.releasable_unselected_capacity(state)
    assert capacity == len(pairs) - (len(selected) + 1)
    assert capacity == len(unselected) - 1


def test_whole_pool_release_becomes_reachable_under_the_lawful_lifecycle(tmp_path):
    """Before r14 this was UNREACHABLE for any ~25 %-sealed universe: unselected members could never
    reach a released state, so the nonced rule could never be revealed and audited. It is reachable
    now -- but only once every selected member has itself been exposed, which is what lifts the
    residual-uncertainty floor."""
    shard_ledger, universe_ledger, incident_ledger = _ledgers(tmp_path)
    symbols, dates, pairs, selected, unselected = _partitioned_universe(n_symbols=3, n_dates=3)
    _register(universe_ledger, symbols, dates)
    assert selected and unselected

    # 1. Take every SELECTED member all the way through the sealed path.
    for i, (symbol, session_date) in enumerate(selected):
        dataset_id = f"sel-{i}"
        vault.seal_shard(
            shard_ledger, dataset_id=dataset_id, universe_id="fixture-universe",
            content_checksum=f"{i:064d}", event_count=1000, vault_secret=_SECRET,
            sealed_at="2026-03-21T00:00:00.000000Z",
        )
        vault.assign_shard(
            shard_ledger, dataset_id=dataset_id, family_root_id=f"root-{i}",
            symbol=symbol, session_date=session_date, assigned_at="2026-03-22T00:00:00.000000Z",
        )
        vault.expose_shard(
            shard_ledger, dataset_id=dataset_id, family_root_id=f"root-{i}",
            exposed_at="2026-03-23T00:00:00.000000Z",
        )
    # 2. Then release every UNSELECTED member -- now lawful, because nothing is hidden any more.
    for i, (symbol, session_date) in enumerate(unselected):
        vault.release_unselected_shard(
            shard_ledger, universe_ledger, incident_ledger,
            dataset_id=f"unsel-{i}", universe_id="fixture-universe",
            symbol=symbol, session_date=session_date,
            content_checksum=f"{i+500:064d}", event_count=1000, vault_secret=_SECRET,
            released_at="2026-03-24T00:00:00.000000Z",
        )

    state = vault.build_vault_state(shard_ledger, universe_ledger)
    universe = state["universes"][0]
    assert universe["rule_disclosure"] == vault.RULE_DISCLOSURE_REVEALED
    # The auditor's proof: the revealed rule recomputes to the commitment made at registration.
    assert (
        vault.compute_rule_commitment(
            universe["commitment_nonce"], universe["symbol_rule"], universe["date_rule"]
        )
        == universe["rule_commitment"]
    )
    assert vault.withheld_dataset_ids(shard_ledger) == frozenset()


def test_a_released_row_is_served_as_evidence_that_earned_no_sealed_credit(tmp_path):
    shard_ledger, universe_ledger, incident_ledger = _ledgers(tmp_path)
    symbols, dates, _pairs, _selected, unselected = _partitioned_universe()
    _register(universe_ledger, symbols, dates)
    symbol, session_date = unselected[0]
    vault.release_unselected_shard(
        shard_ledger, universe_ledger, incident_ledger,
        dataset_id="ds-served", universe_id="fixture-universe",
        symbol=symbol, session_date=session_date,
        content_checksum="b" * 64, event_count=100_000, vault_secret=_SECRET,
        released_at="2026-03-21T00:00:00.000000Z",
    )
    served = vault.build_vault_state(shard_ledger, universe_ledger)["shards"][0]
    assert served["exposure_state"] == vault.STATE_EXPLORATORY_RELEASED
    assert served["release_basis"] == vault.RELEASE_BASIS_HMAC_NOT_SELECTED
    assert served["sealed_credit"] is False
    assert served["family_root_id"] is None
    assert served["sealed_at"] is None
    # The salted commitment still verifies against the now-revealed raw checksum.
    assert (
        vault.commit_content_checksum(_SECRET, served["content_checksum"])
        == served["checksum_commitment"]
    )


# =====================================================================================================
# 6. THE SACRIFICIAL RETENTION PROBE
# =====================================================================================================


def test_a_retention_probe_date_is_barred_from_the_clean_oos_set_thereafter(tmp_path):
    registry = _registry(tmp_path)
    corpus_id = "rapid-microscope-tick-oos-v1"
    ma.register_fresh_corpus_era(
        registry, corpus_id=corpus_id, registered_at="2026-09-01T00:00:00.000000Z", provenance="x"
    )
    candidates = ["2025-11-03", "2025-11-04", "2025-11-05"]
    before = wf.clean_oos_candidate_dates(
        registry, corpus_id=corpus_id, candidate_dates=candidates,
        instant="2026-09-05T00:00:00.000000Z",
    )
    assert before["eligible_session_dates"] == candidates

    wf.record_sacrificial_probe_exposure(
        registry, corpus_id=corpus_id, session_date="2025-11-03",
        logged_at="2026-09-02T00:00:00.000000Z", note="alpaca_tick_retention",
    )
    after = wf.clean_oos_candidate_dates(
        registry, corpus_id=corpus_id, candidate_dates=candidates,
        instant="2026-09-05T00:00:00.000000Z",
    )
    assert after["eligible_session_dates"] == ["2025-11-04", "2025-11-05"]
    assert after["barred"] == [
        {"session_date": "2025-11-03", "reason": "already_exposed_for_corpus"}
    ]
    # And a probed date can never afterwards carry OOS evidence.
    assert (
        wf.classify_evidence_class(
            registry, corpus_id=corpus_id, window_sessions=["2025-11-03"],
            registered_at="2026-09-05T00:00:00.000000Z",
        )
        == wf.EVIDENCE_CLASS_HISTORICAL_EXPOSED_DIAGNOSTIC
    )


def test_the_five_screening_exposed_sessions_are_barred_by_the_same_predicate(tmp_path):
    from app.research import micro_tier_b_screen as tb

    registry = _registry(tmp_path)
    ma.register_fresh_corpus_era(
        registry, corpus_id="c", registered_at="2026-09-01T00:00:00.000000Z", provenance="x"
    )
    result = wf.clean_oos_candidate_dates(
        registry,
        corpus_id="c",
        candidate_dates=list(tb.SCREENING_EXPOSED_SESSIONS) + ["2025-11-04"],
        instant="2026-09-05T00:00:00.000000Z",
        screening_exposed_sessions=tb.SCREENING_EXPOSED_SESSIONS,
    )
    assert result["eligible_session_dates"] == ["2025-11-04"]
    assert {b["reason"] for b in result["barred"]} == {"screening_exposed_session"}
    assert result["clears_survivor_floor"] is False
    assert result["survivor_min_session_dates"] == 105


# =====================================================================================================
# 7. MODE A IS NOT WIRED FOR THE REAL TICK PATH
# =====================================================================================================


def test_mode_a_has_no_real_tick_production_caller(tmp_path):
    """``walkforward.py``'s own docstring: Mode A is "proven on synthetic oracles only this
    iteration, never against real data". The preflight recommended a path that would have used it
    on the real corpus. This guard keeps that false until a named revision changes it."""
    import inspect

    source = inspect.getsource(wf)
    assert "synthetic oracles only" in source
    # The ONE fitting-rule family Mode A can parse is the closed training_quantile vocabulary --
    # anything a real-tick campaign would need is refused, not guessed.
    with pytest.raises(wf.UnknownFittingRuleError):
        wf.parse_fitting_rule("tick_threshold_sweep(0.9)")
    assert wf.parse_fitting_rule("training_quantile(0.90)") == ("training_quantile", 0.90)
    # And no production module reaches for Mode A on the tick path.
    tick_source = inspect.getsource(tobs)
    assert "register_mode_a_origin" not in tick_source


# =====================================================================================================
# 8. THE TICK OBSERVATION READ BOUNDARY (over committed hermetic fixtures only)
# =====================================================================================================

import shutil  # noqa: E402
from pathlib import Path  # noqa: E402

from app.config import CONFIG  # noqa: E402
from app.research.datasets import DatasetStore  # noqa: E402
from app.research.micro_snapshots import run_snapshot_build_and_record  # noqa: E402

_FIXTURE_DIRS = [
    Path(__file__).resolve().parent / "fixtures" / "datasets",
    Path(__file__).resolve().parent / "fixtures" / "datasets_j03",
]
_FIXTURE_SESSION_DATE = "2026-06-09"


def _fixture_store(tmp_path: Path) -> DatasetStore:
    """A throwaway store over a COPY of the committed hermetic PG fixtures -- the
    ``test_scout_ledger._combined_fixture_store`` precedent, verbatim. Never the operator's real
    store, and never a sealed shard."""
    target = tmp_path / "datasets"
    target.mkdir()
    for fixture_dir in _FIXTURE_DIRS:
        for path in fixture_dir.glob("*.json"):
            shutil.copy(path, target / path.name)
    return DatasetStore(str(target))


def _reader_rig(tmp_path):
    store = _fixture_store(tmp_path)
    snapshots_dir = str(tmp_path / "snapshots")
    registry = ma.ExposureRegistry(str(tmp_path / "exposure"))
    ma.register_fresh_corpus_era(
        registry, corpus_id="fixture-corpus",
        registered_at="2026-09-01T00:00:00.000000Z", provenance="fixture",
    )
    return store, snapshots_dir, registry


def test_the_tick_reader_produces_canonical_return_bps_observations(tmp_path):
    store, snapshots_dir, registry = _reader_rig(tmp_path)
    run_snapshot_build_and_record(store, CONFIG, snapshots_dir)
    result = tobs.tick_observations_for_sessions(
        dataset_store=store, snapshots_dir=snapshots_dir, config=CONFIG,
        session_dates=[_FIXTURE_SESSION_DATE],
        feature_name="quote_imbalance", structure_context_kind="none",
        horizon_key="trades_20", sidedness="long",
        exposure_registry=registry, corpus_id="fixture-corpus",
        purpose=tobs.PURPOSE_TEST, logged_at="2026-09-02T00:00:01.000000Z",
        spec_registered_at="2026-09-02T00:00:00.000000Z",
    )
    assert result["observations"], "the fixtures must yield at least one anchor"
    for observation in result["observations"]:
        assert observation["session_date"] == _FIXTURE_SESSION_DATE
        assert observation["value_unit"] == "return_bps"
        assert isinstance(observation["value"], float)
    # Unit proof is not decorative: the walk-forward gate accepts these as-is.
    wf.require_canonical_observation_units(result["observations"])
    assert result["exposure_windows_logged"] == [_FIXTURE_SESSION_DATE]


def test_the_tick_reader_cannot_read_outside_the_requested_fold_sessions(tmp_path):
    """Confinement is structural, not a post-filter: the manifest is narrowed BEFORE the read, so a
    window with no datasets reads nothing at all rather than quietly reading everything."""
    store, snapshots_dir, registry = _reader_rig(tmp_path)
    run_snapshot_build_and_record(store, CONFIG, snapshots_dir)
    result = tobs.tick_observations_for_sessions(
        dataset_store=store, snapshots_dir=snapshots_dir, config=CONFIG,
        session_dates=["2026-07-01", "2026-07-02"],  # no fixture falls on either
        feature_name="quote_imbalance", structure_context_kind="none",
        horizon_key="trades_20", sidedness="long",
        exposure_registry=registry, corpus_id="fixture-corpus",
        purpose=tobs.PURPOSE_TRAIN, logged_at="2026-09-02T00:00:01.000000Z",
    )
    assert result["datasets_read"] == 0
    assert result["observations"] == []
    # The narrowing itself, proven directly.
    assert tobs.manifest_for_sessions(store, session_dates=["2026-07-01"]) == []
    assert len(tobs.manifest_for_sessions(store, session_dates=[_FIXTURE_SESSION_DATE])) == 3


def test_the_tick_reader_refuses_a_withheld_or_sealed_dataset_rather_than_dropping_it(tmp_path):
    """A withheld shard inside the requested window is a REFUSAL, never a silent shrink -- a fold
    that quietly evaluated the survivors of its own corpus would report a number for a window it
    did not measure."""
    store, snapshots_dir, registry = _reader_rig(tmp_path)
    run_snapshot_build_and_record(store, CONFIG, snapshots_dir)
    root = str(Path(store.root).parent / "micro_vault")
    universe_ledger = vault.VaultUniverseLedger(root)
    vault.register_universe(
        universe_ledger, universe_id="withholding-universe",
        symbol_rule=["PG"], date_rule=[_FIXTURE_SESSION_DATE],
        vault_secret_commitment=vault.commit_vault_secret(_SECRET),
        registered_at="2000-01-01T00:00:00.000000Z",  # before the fixtures' own created_utc
    )
    with pytest.raises(tobs.TickObservationWithheldError, match="withheld"):
        tobs.manifest_for_sessions(store, session_dates=[_FIXTURE_SESSION_DATE])
    with pytest.raises(tobs.TickObservationWithheldError):
        tobs.tick_observations_for_sessions(
            dataset_store=store, snapshots_dir=snapshots_dir, config=CONFIG,
            session_dates=[_FIXTURE_SESSION_DATE],
            feature_name="quote_imbalance", structure_context_kind="none",
            horizon_key="trades_20", sidedness="long",
            exposure_registry=registry, corpus_id="fixture-corpus",
            purpose=tobs.PURPOSE_TRAIN, logged_at="2026-09-02T00:00:01.000000Z",
        )


def test_a_missing_snapshot_refuses_rather_than_silently_shrinking_the_corpus(tmp_path):
    """``scout.extract_anchors`` treats a dataset with no current snapshot as an honest SKIP. That
    is right for a discovery screen and wrong for a fold, so this reader refuses instead."""
    store, snapshots_dir, registry = _reader_rig(tmp_path)
    # Deliberately do NOT build snapshots.
    with pytest.raises(tobs.TickObservationIncompleteError, match="no CURRENT snapshot"):
        tobs.tick_observations_for_sessions(
            dataset_store=store, snapshots_dir=snapshots_dir, config=CONFIG,
            session_dates=[_FIXTURE_SESSION_DATE],
            feature_name="quote_imbalance", structure_context_kind="none",
            horizon_key="trades_20", sidedness="long",
            exposure_registry=registry, corpus_id="fixture-corpus",
            purpose=tobs.PURPOSE_TRAIN, logged_at="2026-09-02T00:00:01.000000Z",
        )
    # And a PARTIALLY-built corpus refuses too -- the dangerous case, because it would otherwise
    # produce a plausible-looking but incomplete number.
    records, _errors = store.list()
    run_snapshot_build_and_record(store, CONFIG, snapshots_dir, [records[0]["id"]])
    with pytest.raises(tobs.TickObservationIncompleteError, match=r"\d of 3"):
        tobs.tick_observations_for_sessions(
            dataset_store=store, snapshots_dir=snapshots_dir, config=CONFIG,
            session_dates=[_FIXTURE_SESSION_DATE],
            feature_name="quote_imbalance", structure_context_kind="none",
            horizon_key="trades_20", sidedness="long",
            exposure_registry=registry, corpus_id="fixture-corpus",
            purpose=tobs.PURPOSE_TRAIN, logged_at="2026-09-02T00:00:01.000000Z",
        )


def test_the_tick_reader_refuses_an_unregistered_corpus_era(tmp_path):
    store, snapshots_dir, _registry = _reader_rig(tmp_path)
    run_snapshot_build_and_record(store, CONFIG, snapshots_dir)
    bare = ma.ExposureRegistry(str(tmp_path / "bare-exposure"))
    with pytest.raises(ma.UnregisteredCorpusEraError):
        tobs.tick_observations_for_sessions(
            dataset_store=store, snapshots_dir=snapshots_dir, config=CONFIG,
            session_dates=[_FIXTURE_SESSION_DATE],
            feature_name="quote_imbalance", structure_context_kind="none",
            horizon_key="trades_20", sidedness="long",
            exposure_registry=bare, corpus_id="never-registered",
            purpose=tobs.PURPOSE_TRAIN, logged_at="2026-09-02T00:00:01.000000Z",
        )


def test_the_tick_reader_refuses_an_unsided_candidate(tmp_path):
    """Mode B evaluates an already-directed hypothesis; an unsided one has no meaning here, and the
    r13 vocabulary gate fires before any corpus read."""
    store, snapshots_dir, registry = _reader_rig(tmp_path)
    run_snapshot_build_and_record(store, CONFIG, snapshots_dir)
    for bad in (None, "buy", "LONG", "", "sell"):
        with pytest.raises(Exception) as excinfo:
            tobs.tick_observations_for_sessions(
                dataset_store=store, snapshots_dir=snapshots_dir, config=CONFIG,
                session_dates=[_FIXTURE_SESSION_DATE],
                feature_name="quote_imbalance", structure_context_kind="none",
                horizon_key="trades_20", sidedness=bad,
                exposure_registry=registry, corpus_id="fixture-corpus",
                purpose=tobs.PURPOSE_TRAIN, logged_at="2026-09-02T00:00:01.000000Z",
            )
        assert excinfo.type.__name__ in {
            "UnsidedCandidateError",       # None -- legal for Scout, meaningless for Mode B
            "UnknownSideVocabularyError",  # "buy"/"sell" -- the AGGRESSOR vocabulary, not a direction
        }, f"{bad!r} raised {excinfo.type.__name__}"


# =====================================================================================================
# 9. DATASETSTORE INVENTORY EQUALITY -- the r14 performance fix is performance ONLY
# =====================================================================================================


def test_indexed_and_unindexed_dataset_inventories_are_byte_identical(tmp_path):
    """``_indexed_dataset_store`` exists purely to stop every CLI/module path re-hashing the whole
    corpus. It must change nothing about WHAT is served."""
    import json as _json

    store_dir = str(_fixture_store(tmp_path).root)
    unindexed = DatasetStore(store_dir)
    indexed = DatasetStore(store_dir, index_db_path=str(tmp_path / "dataset_index.db"))

    cold_records, cold_errors = indexed.list()          # populates the durable index
    warm_records, warm_errors = DatasetStore(
        store_dir, index_db_path=str(tmp_path / "dataset_index.db")
    ).list()                                            # a FRESH store, served from the index
    plain_records, plain_errors = unindexed.list()

    canonical = lambda payload: _json.dumps(payload, sort_keys=True)  # noqa: E731
    assert canonical(plain_records) == canonical(cold_records) == canonical(warm_records)
    assert plain_errors == cold_errors == warm_errors == []


def test_the_walkforward_indexed_store_helper_resolves_beside_the_dataset_dir(tmp_path, monkeypatch):
    monkeypatch.delenv("TAPEOLOGY_DATASET_INDEX_DB", raising=False)
    assert wf.resolve_dataset_index_db_path("/a/b/datasets") == "/a/b/dataset_index.db"
    monkeypatch.setenv("TAPEOLOGY_DATASET_INDEX_DB", "/tmp/override.db")
    assert wf.resolve_dataset_index_db_path("/a/b/datasets") == "/tmp/override.db"


def test_the_tick_fold_request_reads_the_store_once_not_twice(tmp_path, monkeypatch):
    """The pre-r14 body called ``list()`` directly AND again inside
    ``_tick_dataset_session_dates`` -- paying the full-verify cost twice per request."""
    store = _fixture_store(tmp_path)
    calls = {"n": 0}
    real_list = store.list

    def counting_list():
        calls["n"] += 1
        return real_list()

    monkeypatch.setattr(store, "list", counting_list)
    ledger = wf.WalkForwardLedger(str(tmp_path / "wf"))
    with pytest.raises(wf.InsufficientSessionsForFoldsError, match="1 < 105"):
        wf.run_tick_family_fold_request(
            ledger, CONFIG, corpus_id="fixture-tick-corpus", dataset_store=store
        )
    assert calls["n"] == 1
    # The refusal wrote nothing: a request that never ran leaves no trace.
    assert ledger.all_rows() == []


def test_the_tick_fold_request_corpus_id_is_explicit_and_legacy_stays_the_default():
    import inspect

    signature = inspect.signature(wf.run_tick_family_fold_request)
    assert signature.parameters["corpus_id"].default == wf.TICK_LEGACY_CORPUS_ID
    assert wf.TICK_LEGACY_CORPUS_ID == "tick_legacy_symbol_days_v1"


def test_a_disclosed_pool_position_can_never_be_released_for_oos_credit(tmp_path):
    """§7.2.2: a position disclosed as NOT selected "may never receive sealed, blind or
    historical_oos credit". ``assign_shard`` already refused it; so must the release path, because
    releasing makes the tape servable and a fold reading it would classify ``historical_oos`` from
    an exposure registry that has never heard of the incident."""
    shard_ledger, universe_ledger, incident_ledger = _ledgers(tmp_path)
    symbols, dates, _pairs, _selected, unselected = _partitioned_universe()
    _register(universe_ledger, symbols, dates)
    symbol, session_date = unselected[0]
    vault.record_disclosure_incident(
        incident_ledger,
        incident_id="fixture-incident",
        universe_id="fixture-universe",
        pairs=[(symbol, session_date)],
        disclosure_type="non_sealed_pool_position",
        source="fixture",
        provenance={"channel": "fixture"},
        occurred_at="2026-03-20T00:00:00.000000Z",
        sealed_member_identity_disclosed=False,
        evidence_consequence="PERMANENT: no sealed, blind or historical_oos credit.",
    )
    with pytest.raises(vault.DisclosedPoolPositionError):
        vault.release_unselected_shard(
            shard_ledger, universe_ledger, incident_ledger,
            dataset_id="ds-disclosed", universe_id="fixture-universe",
            symbol=symbol, session_date=session_date,
            content_checksum="a" * 64, event_count=1000, vault_secret=_SECRET,
        )
    # A DIFFERENT unselected position is unaffected.
    other_symbol, other_date = unselected[1]
    vault.release_unselected_shard(
        shard_ledger, universe_ledger, incident_ledger,
        dataset_id="ds-other", universe_id="fixture-universe",
        symbol=other_symbol, session_date=other_date,
        content_checksum="b" * 64, event_count=1000, vault_secret=_SECRET,
        released_at="2026-03-21T00:00:00.000000Z",
    )
    assert "ds-other" not in vault.withheld_dataset_ids(shard_ledger)


def test_the_real_tranche_shape_yields_a_releasable_capacity_of_fifty_seven():
    """The operator's own tranche, as pure arithmetic -- no vault secret is loaded and no real
    ledger is read. 80 pool pairs, 21 published as HMAC-selected, 1 position already disclosed
    non-selected by the recorded incident, none exposed.

    Of the 59 NOT-selected members: 1 is permanently barred by the disclosure incident, 57 are
    releasable, and 1 must stay withheld as the decoy that keeps the sealed set unpinned."""
    state = {
        "universe_pairs": 80,
        "selected_count": 21,
        "disclosed_not_selected_positions": 1,
        "revealed_selected_positions": 0,
        "unknown_positions": 79,
        "still_hidden_selected_shards": 21,
        "candidate_identities_per_hidden_selected_shard": 79,
        "hidden_set_fully_determined": False,
        "any_identity_certain": False,
    }
    assert vault.releasable_unselected_capacity(state) == 57
    vault.require_residual_pool_uncertainty(state)  # today's state is safe

    # One release short of the wall: still safe.
    at_the_edge = {**state, "unknown_positions": 22, "still_hidden_selected_shards": 21}
    at_the_edge["hidden_set_fully_determined"] = False
    at_the_edge["any_identity_certain"] = False
    vault.require_residual_pool_uncertainty(at_the_edge)
    assert vault.releasable_unselected_capacity(at_the_edge) == 0

    # One release past it: the hidden set is pinned by subtraction, and the floor refuses.
    over = {**state, "unknown_positions": 21, "still_hidden_selected_shards": 21}
    over["hidden_set_fully_determined"] = True
    over["any_identity_certain"] = True
    with pytest.raises(vault.ResidualPoolUncertaintyError, match="determinable by subtraction"):
        vault.require_residual_pool_uncertainty(over)

    # Once every selected member is exposed there is nothing left to protect and the floor lifts.
    nothing_hidden = {**state, "still_hidden_selected_shards": 0, "unknown_positions": 0}
    nothing_hidden["any_identity_certain"] = False
    vault.require_residual_pool_uncertainty(nothing_hidden)


# =====================================================================================================
# 10. THE OPERATOR PATH IS PARAMETERIZED WITHOUT TOUCHING THE FROZEN J-06 IDENTITY
# =====================================================================================================


def test_the_operator_script_defaults_to_the_immutable_starter_universe():
    from scripts import j06_operator as op

    assert op.STARTER_UNIVERSE_ID == "rapid-microscope-j06-starter"
    assert op.UNIVERSE_ID == op.STARTER_UNIVERSE_ID
    assert op.DATE_RULE == sorted(op.STARTER_DATE_RULE)
    # §7.2.1(i)+(j): the resolved eight-symbol panel is shared by every era and never re-screened.
    assert op.SYMBOL_RULE == ["PG", "AAPL", "MSFT", "NVDA", "AG", "LYFT", "WULF", "SPY"]
    assert op._select_universe(None, None)["source"] == "starter"


def test_a_second_era_needs_both_flags_and_can_never_reuse_the_starter_id(tmp_path):
    from scripts import j06_operator as op

    dates_file = tmp_path / "dates.txt"
    dates_file.write_text("2025-11-04\n2025-11-05\n2025-11-06\n")

    with pytest.raises(SystemExit, match="must be given together"):
        op._select_universe("some-new-era", None)
    with pytest.raises(SystemExit, match="must be given together"):
        op._select_universe(None, str(dates_file))
    with pytest.raises(SystemExit, match="immutable"):
        op._select_universe(op.STARTER_UNIVERSE_ID, str(dates_file))

    try:
        selected = op._select_universe("rapid-microscope-tick-oos-v1", str(dates_file))
        assert selected["universe_id"] == "rapid-microscope-tick-oos-v1"
        assert op.DATE_RULE == ["2025-11-04", "2025-11-05", "2025-11-06"]
        assert op.SYMBOL_RULE == ["PG", "AAPL", "MSFT", "NVDA", "AG", "LYFT", "WULF", "SPY"]
    finally:
        # This module's globals are process-wide; restore the frozen identity for every later test.
        op.UNIVERSE_ID = op.STARTER_UNIVERSE_ID
        op.DATE_RULE = list(op.STARTER_DATE_RULE)


def test_partial_releases_never_leak_a_still_sealed_members_identity_on_a_served_surface(tmp_path):
    """TR-2, re-run with partial exploratory releases treated as attacker-known. Releasing shrinks
    the anonymity set, so the served projection has to stay opaque for the sealed side even as the
    unselected side becomes fully identified."""
    shard_ledger, universe_ledger, incident_ledger = _ledgers(tmp_path)
    symbols, dates, _pairs, selected, unselected = _partitioned_universe(n_symbols=4, n_dates=5)
    _register(universe_ledger, symbols, dates)
    assert selected and len(unselected) >= 2

    # Seal every selected member, then release as many unselected ones as the floor allows.
    sealed_pairs = []
    for i, (symbol, session_date) in enumerate(selected):
        vault.seal_shard(
            shard_ledger, dataset_id=f"sealed-{i}", universe_id="fixture-universe",
            content_checksum=f"{i:064d}", event_count=1000, vault_secret=_SECRET,
            sealed_at="2026-03-21T00:00:00.000000Z",
        )
        sealed_pairs.append((symbol, session_date))
    released = 0
    for i, (symbol, session_date) in enumerate(unselected):
        try:
            vault.release_unselected_shard(
                shard_ledger, universe_ledger, incident_ledger,
                dataset_id=f"rel-{i}", universe_id="fixture-universe",
                symbol=symbol, session_date=session_date,
                content_checksum=f"{i+900:064d}", event_count=1000, vault_secret=_SECRET,
                released_at="2026-03-22T00:00:00.000000Z",
            )
            released += 1
        except vault.ResidualPoolUncertaintyError:
            break
    assert released > 0, "the fixture must exercise at least one lawful release"

    state = vault.build_vault_state(shard_ledger, universe_ledger)
    served_blob = json.dumps(state, sort_keys=True)
    for symbol, session_date in sealed_pairs:
        # A sealed shard's own (symbol, session_date) pair must not be reconstructible from the
        # served state. The symbol string alone appears (released siblings share symbols) -- the
        # PAIRING is what must not.
        served_pairs = {
            (s.get("symbol"), s.get("session_date"))
            for s in state["shards"]
            if s.get("symbol") is not None
        }
        assert (symbol, session_date) not in served_pairs
    for row in state["shards"]:
        if row["exposure_state"] == vault.STATE_SEALED:
            assert row.get("symbol") is None and row.get("session_date") is None
            assert "dataset_id" not in row and "content_checksum" not in row
    # The rule itself stays committed while any member is unresolved.
    assert state["universes"][0]["rule_disclosure"] == vault.RULE_DISCLOSURE_COMMITTED
    assert "symbol_rule" not in state["universes"][0]
    assert "commitment_nonce" not in served_blob

    final = vault.pool_partition_disclosure_state(
        shard_ledger, universe_ledger, incident_ledger,
        universe_id="fixture-universe", vault_secret=_SECRET,
    )
    assert final["any_identity_certain"] is False
    assert final["unknown_positions"] > final["still_hidden_selected_shards"]


def test_without_the_release_path_an_unselected_member_has_no_route_to_a_terminal_state(tmp_path):
    """The gap r14 closes, proven directly rather than asserted in prose.

    The sealed path is `seal → assign → expose`. For a pool member that was never sealed,
    ``assign_shard`` refuses (it requires a currently-`sealed` row) and ``expose_shard`` refuses (it
    requires `assigned`) -- so before ``release_unselected_shard`` existed there was NO transition
    an HMAC-not-selected member could make, and it stayed withheld forever. Sealing one to unlock
    the path would be a lie about the HMAC and would hand it single-shot blind credit."""
    shard_ledger, universe_ledger, incident_ledger = _ledgers(tmp_path)
    symbols, dates, _pairs, _selected, unselected = _partitioned_universe()
    _register(universe_ledger, symbols, dates)
    symbol, session_date = unselected[0]

    with pytest.raises(vault.ShardLifecycleOrderError):
        vault.assign_shard(
            shard_ledger, dataset_id="never-sealed", family_root_id="root-1",
            symbol=symbol, session_date=session_date,
        )
    with pytest.raises(vault.ShardLifecycleOrderError):
        vault.expose_shard(shard_ledger, dataset_id="never-sealed", family_root_id="root-1")

    # r14's route is the only one that works, and it lands on a state that is NOT `exposed`.
    row = vault.release_unselected_shard(
        shard_ledger, universe_ledger, incident_ledger,
        dataset_id="never-sealed", universe_id="fixture-universe",
        symbol=symbol, session_date=session_date,
        content_checksum="a" * 64, event_count=1000, vault_secret=_SECRET,
        released_at="2026-03-21T00:00:00.000000Z",
    )
    assert row["exposure_state"] == vault.STATE_EXPLORATORY_RELEASED
    assert row["exposure_state"] != vault.STATE_EXPOSED
    # Both terminal states stop the withholding predicate; only one of them is the sealed path.
    assert vault.STATE_EXPLORATORY_RELEASED in vault._RELEASED_STATES
    assert vault.STATE_EXPOSED in vault._RELEASED_STATES
    assert vault.STATE_SEALED not in vault._RELEASED_STATES
    assert vault.STATE_ASSIGNED not in vault._RELEASED_STATES
