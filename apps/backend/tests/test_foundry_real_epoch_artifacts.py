"""goal-hypothesis-foundry-iter-5 audit addition: regression guards over the era's ONE real,
Git-frozen epoch (``docs/hypothesis-foundry/*.json`` + ``reports/hypothesis-foundry/
source-registry-audit.md``, committed together in ``dff64eaa``).

**Why this file exists.** The iteration that produced those artifacts shipped tests for the route
read path, the hermetic fixture views, and the anti-goal grep guard -- but none for the frozen
artifacts themselves, even though the phase spec's own TESTING REQUIREMENTS list TC-1..TC-10 as
unit/integration coverage. Because ``docs/goal.md`` §8.1 permits **at most one real epoch_id** for
this entire era, those five files can never be regenerated to repair a later corruption: they are
exactly the kind of artifact that needs a standing guard, not a one-time manual verification. Every
test below is READ-ONLY -- nothing here generates, rewrites, or mutates any tracked artifact.

TC ids refer to ``docs/phases/goal-hypothesis-foundry-iter-5.md``'s Test-first contract.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import subprocess
from pathlib import Path

import pytest

from app.research import foundry_compiler as fc
from app.research import foundry_freeze as fz
from app.research import micro_readiness
from app.research import micro_routes

BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_DIR.parents[1]
TRACKED_DIR = REPO_ROOT / "docs" / "hypothesis-foundry"
AUDIT_REPORT_REL = "reports/hypothesis-foundry/source-registry-audit.md"
TRACKED_REL_PATHS = (
    "docs/hypothesis-foundry/source-registry.json",
    "docs/hypothesis-foundry/epoch-manifest.json",
    "docs/hypothesis-foundry/freeze-set.json",
    "docs/hypothesis-foundry/freeze-record.json",
    AUDIT_REPORT_REL,
)

# The closed §7.1 source-disposition vocabulary, spelled out here rather than imported as a set so
# that a future widening of the production module cannot silently widen this assertion too.
LEGAL_DISPOSITIONS = frozenset(
    {
        "COMPILED",
        "ALIASED_PROXY_ONLY",
        "ALIASED_VARIANT_VOCABULARY",
        "ALIASED_LINEAGE",
        "EXCLUDED_PREVIOUSLY_KILLED",
        "EXCLUDED_PREREQUISITE_UNMET",
        "EXCLUDED_GATE_CLOSED",
        "BLOCKED_SPEC_GAP",
        "BLOCKED_MISSING_PRIMITIVE",
        "BLOCKED_UNSUPPORTED_STUDY_FORM",
        "BLOCKED_UNSUPPORTED_RELATION",
        "BLOCKED_DIRECTION",
        "BLOCKED_VARIANT_EXPLOSION",
        "BLOCKED_UNIT_CONTRACT",
    }
)


def _load_json(name: str) -> dict:
    return json.loads((TRACKED_DIR / name).read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def registry() -> dict:
    return _load_json("source-registry.json")


@pytest.fixture(scope="module")
def manifest() -> dict:
    return _load_json("epoch-manifest.json")


@pytest.fixture(scope="module")
def freeze_record() -> dict:
    return _load_json("freeze-record.json")


@pytest.fixture(scope="module")
def records_by_id(registry) -> dict:
    return {r["source_id"]: r for r in registry["records"]}


def _git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=str(REPO_ROOT), capture_output=True, text=True)


def _require_git_checkout() -> None:
    if _git("rev-parse", "HEAD").returncode != 0:
        pytest.skip("not a git checkout -- the Git-visible freeze barrier cannot be verified here")


@pytest.fixture(scope="module")
def freeze_set() -> dict:
    return _load_json("freeze-set.json")


# === goal-hypothesis-foundry-iter-6 (closes audit findings B1/B2/B7): the regenerated freeze-set /
# freeze-record bookkeeping. Same-iteration read-only guards over the COMMITTED bytes, per the
# iter-5 lesson this iteration's own BACKGROUND explicitly carries forward. ==========================


def test_b1_every_freeze_set_entry_is_repo_relative_not_absolute(freeze_set):
    entries = freeze_set["entries"]
    assert entries, "empty freeze set"
    for key in entries:
        assert not key.startswith("/"), f"expected a repo-relative freeze-set key, got absolute: {key}"


def test_b7_freeze_set_covers_the_tracked_registry_and_manifest_plus_both_foundry_clis(freeze_set):
    covered = set(freeze_set["entries"])
    required_suffixes = (
        "docs/hypothesis-foundry/source-registry.json",
        "docs/hypothesis-foundry/epoch-manifest.json",
        "apps/backend/scripts/generate_hypothesis_foundry_real_epoch.py",
        "apps/backend/scripts/run_hypothesis_foundry_real_exhaust.py",
    )
    for suffix in required_suffixes:
        assert any(entry.endswith(suffix) for entry in covered), f"freeze-set is missing {suffix}"
    # goal.md §8.4 never names `freeze-record.json`/`freeze-set.json` as freeze-set members (only
    # "the Foundry methodology/spec and tracked REGISTRY/MANIFEST files") -- and `freeze-record.json`
    # genuinely CANNOT be a member: its own content embeds `freeze_set_hash`, so pinning its file
    # hash inside the very freeze-set that hash is computed over is the identical self-reference
    # `freeze-set.json` is already excluded for, one hop removed. Neither appears.
    for excluded_suffix in (
        "docs/hypothesis-foundry/freeze-record.json", "docs/hypothesis-foundry/freeze-set.json",
    ):
        assert not any(entry.endswith(excluded_suffix) for entry in covered), (
            f"{excluded_suffix} must NOT be a freeze-set member (self-reference)"
        )


def test_b7_freeze_record_carries_the_era_open_evidence_class_contract(freeze_record):
    # §10.1/goal.md Success Criteria 16: every real Foundry evaluation this era is
    # constitutionally locked to ONE evidence class.
    assert freeze_record["era_open_evidence_class_contract"] == "historical_exposed_diagnostic"


def test_freeze_record_freeze_set_hash_matches_the_committed_freeze_set(freeze_record, freeze_set):
    """goal-hypothesis-foundry-iter-6 audit addition (finding B1 in the iter-6 audit report).

    ``freeze-record.json`` is deliberately NOT a freeze-set member (its own content embeds
    ``freeze_set_hash``, so pinning its file hash inside the very freeze-set that hash is computed
    over is genuinely circular -- see
    ``test_b7_freeze_set_covers_the_tracked_registry_and_manifest_plus_both_foundry_clis``). The
    iter-6 dev handoff justified that exclusion by asserting freeze-record.json's integrity "is
    instead protected by the existing ``verify_commit_is_ancestor`` + ``freeze_set_hash``
    field-equality check every reader (the route, the exhaust CLI) already performs" -- but no such
    field-equality check existed anywhere in the repository: ``verify_freeze_set_unchanged`` only
    re-hashes the paths ``entries`` enumerates, and neither ``micro_routes.read_epoch_manifest_view``
    nor ``run_hypothesis_foundry_real_exhaust.run_real_exhaust`` ever compares the two files' own
    ``freeze_set_hash`` values. This test IS that check, in the one place the era can still add one
    without touching a frozen science file: a read-only guard over the committed bytes.

    A hand-edit of ``freeze-record.json`` that swapped in a different ``freeze_set_hash`` (the value
    copied verbatim into the era's one irreversible §8.5 epoch-opening ledger row) would otherwise
    pass every existing check in this repository."""
    assert freeze_record["freeze_set_hash"] == freeze_set["freeze_set_hash"], (
        "freeze-record.json's pinned freeze_set_hash disagrees with the committed freeze-set.json "
        "it claims to pin -- the two tracked artifacts have drifted apart"
    )
    # Belt and braces: the freeze-set's own hash is a pure function of its recorded entries, so the
    # equality above transitively pins the freeze-record to the enumerated path+sha256 set itself.
    assert fz._sha256(fz._canonical(freeze_set["entries"])) == freeze_record["freeze_set_hash"]


def test_tc8_verify_freeze_set_unchanged_and_commit_ancestry_both_pass_against_the_new_freeze_commit(
    freeze_record, freeze_set,
):
    _require_git_checkout()
    fz.verify_freeze_set_unchanged(freeze_set, repo_root=REPO_ROOT)  # must not raise
    head = _git("rev-parse", "HEAD").stdout.strip()
    assert fz.verify_commit_is_ancestor(freeze_record["freeze_commit"], head, cwd=REPO_ROOT)


def test_b2_every_freeze_set_path_hash_matches_the_freeze_commits_own_committed_bytes(freeze_record, freeze_set):
    """The direct fix for B2: not just ancestry (``freeze_commit`` is *an* ancestor of ``HEAD``),
    but genuine byte-completeness -- ``git show {freeze_commit}:{path}`` for every pinned entry
    hashes to EXACTLY the pinned digest, proving ``freeze_commit`` really does contain the bytes
    the freeze-set was computed over (not merely an unrelated earlier commit that happens to be an
    ancestor)."""
    _require_git_checkout()
    freeze_commit = freeze_record["freeze_commit"]
    mismatches = []
    for rel_path, expected_hash in freeze_set["entries"].items():
        show = _git("show", f"{freeze_commit}:{rel_path}")
        if show.returncode != 0:
            mismatches.append((rel_path, "missing from freeze_commit's own tree"))
            continue
        actual = hashlib.sha256(show.stdout.encode("utf-8")).hexdigest()
        # `git show` normalizes line endings identically to how the file was hashed on write
        # (both are plain `read_bytes()`/`read_text()` UTF-8 -- no CRLF translation anywhere in
        # this pipeline), so a direct string-encode comparison is valid here.
        if actual != expected_hash:
            mismatches.append((rel_path, f"expected {expected_hash}, git show gives {actual}"))
    assert mismatches == [], f"freeze_commit does not contain the pinned bytes for: {mismatches}"


# === TC-1..TC-5: the frozen registry's own content ===============================================


def test_tc1_registry_holds_exactly_eleven_records_each_with_one_legal_disposition(registry):
    records = registry["records"]
    assert len(records) == 11
    ids = [r["source_id"] for r in records]
    assert len(set(ids)) == 11, f"duplicate source_id in the frozen registry: {ids}"
    for record in records:
        assert record["disposition"] in LEGAL_DISPOSITIONS, record["source_id"]
        # §1.4's required per-record fields that the first draft of this artifact silently dropped
        # (the fresh-context audit's finding 1) -- guarded so a future serializer change cannot
        # reintroduce the omission.
        assert record["audit_note"].strip(), f"{record['source_id']}: empty audit_note"
        assert record["source_hash"], f"{record['source_id']}: empty source_hash"
        assert record["quoted_spans"], f"{record['source_id']}: no quoted spans"


def test_tc1_registry_hash_and_dispositions_are_reproduced_by_the_real_generator(registry, manifest):
    """Recompiles the real 11 source records through the REAL ``compile_sources`` and asserts the
    committed ``source_registry_hash`` and every committed disposition come back identical -- the
    guard that makes the frozen JSON provably a product of the generator rather than a file anyone
    could hand-edit afterwards."""
    spec = importlib.util.spec_from_file_location(
        "_generate_real_epoch_for_audit_test",
        BACKEND_DIR / "scripts" / "generate_hypothesis_foundry_real_epoch.py",
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    records = module.build_real_source_records()
    assert len(records) == 11
    result = fc.compile_sources(
        records, foundry_spec_version=registry["foundry_spec_version"], epoch_id="pending", blueprints={}
    )
    assert result.source_registry_hash == registry["source_registry_hash"]
    assert result.source_registry_hash == manifest["source_registry_hash"]
    committed = {r["source_id"]: r["disposition"] for r in registry["records"]}
    assert dict(result.dispositions) == committed
    # §12 / J-06: a sparse (here empty) compiled set is the honest outcome, never rescued.
    assert len(result.candidate_specs) == 0
    assert manifest["families"] == []


def test_tc2_card_9_1_study_2_is_excluded_previously_killed(records_by_id):
    record = records_by_id["card-9.1-study-2-delta-divergence-excluded"]
    assert record["disposition"] == "EXCLUDED_PREVIOUSLY_KILLED"
    assert set(record["aliases_lineage_ids"]) == {"card-9.1", "study-2-delta-divergence-level-tests"}


def test_tc3_card_9_2_is_excluded_prerequisite_unmet(records_by_id):
    assert records_by_id["card-9.2-delta-by-price-profile-excluded"]["disposition"] == "EXCLUDED_PREREQUISITE_UNMET"


def test_tc4_every_wave2_card_9_8_through_9_11_is_excluded_gate_closed(records_by_id):
    """The registry represents Cards 9.8-9.11 as ONE combined record (mirroring goal.md §1.2's own
    single-arrow treatment of that foursome), so each constituent card id must be reachable through
    that record's ``aliases_lineage_ids`` -- otherwise a required source object would have silently
    disappeared (§7.1's own rule), which is what TC-4 actually protects against."""
    record = records_by_id["cards-9.8-9.11-wave2-gate-closed"]
    assert record["disposition"] == "EXCLUDED_GATE_CLOSED"
    for card in ("card-9.8", "card-9.9", "card-9.10", "card-9.11"):
        assert card in record["aliases_lineage_ids"], f"{card} is not accounted for anywhere"


def test_tc5_both_pilot_proxies_are_aliased_proxy_only_with_their_do_not_preserved(records_by_id):
    for source_id, study_id in (
        ("pilot-study-1-range-wall-failed-aggression", "range_wall_failed_aggression"),
        ("pilot-study-3-capitulation-exhaustion", "capitulation_exhaustion"),
    ):
        record = records_by_id[source_id]
        assert record["disposition"] == "ALIASED_PROXY_ONLY", source_id
        assert record["lineage_id"] == study_id
        do_not = micro_readiness.PILOT_STUDY_STATUS[study_id]["do_not"]
        assert do_not, study_id
        # §1.1: "their existing `do_not` restriction is preserved" -- verified against the live
        # frozen source of truth, not against a copy typed into the registry.
        assert do_not in record["source_excerpt"], source_id
        assert any(do_not == span["text"] for span in record["quoted_spans"]), source_id


# === TC-6: the outcome-access tripwire ===========================================================


def test_tc6_outcome_access_census_is_zero_in_the_artifact_and_on_the_served_view(manifest):
    assert manifest["outcome_access_census"] == 0
    served = micro_routes.read_epoch_manifest_view()
    assert served["outcome_access_census"] == 0
    assert served["epoch_id"] == manifest["epoch_id"]
    assert served["source_registry_hash"] == manifest["source_registry_hash"]
    assert served["source_dispositions"] == manifest["source_dispositions"]
    assert len(served["source_dispositions"]) == 11
    # No outcome-shaped value may appear anywhere in the manifest (§8.2's own closing rule).
    blob = json.dumps(manifest)
    for forbidden in ("p_value", "p_screen", "effect_bps", "forward_return", "observation_count", "pnl"):
        assert forbidden not in blob, f"outcome-shaped key {forbidden!r} present in the real manifest"


# === TC-9: the Git-visible pre-outcome barrier ===================================================


def test_tc9_all_five_tracked_artifacts_share_one_commit_that_is_an_ancestor_of_head():
    _require_git_checkout()
    head = _git("rev-parse", "HEAD").stdout.strip()
    commits = set()
    for rel in TRACKED_REL_PATHS:
        log = _git("log", "--format=%H", "--diff-filter=A", "--", rel)
        assert log.returncode == 0 and log.stdout.strip(), f"{rel} was never added in this history"
        commits.add(log.stdout.split()[-1])
    assert len(commits) == 1, f"the five tracked artifacts were not added in ONE commit: {commits}"
    freeze_commit_of_artifacts = commits.pop()
    assert _git("merge-base", "--is-ancestor", freeze_commit_of_artifacts, head).returncode == 0
    for rel in TRACKED_REL_PATHS:
        assert _git("cat-file", "-e", f"HEAD:{rel}").returncode == 0, f"{rel} absent from HEAD's tree"


def test_tc9_freeze_commit_is_an_ancestor_of_head(freeze_record):
    _require_git_checkout()
    head = _git("rev-parse", "HEAD").stdout.strip()
    assert fz.verify_commit_is_ancestor(freeze_record["freeze_commit"], head, cwd=REPO_ROOT)


def test_tc9_exactly_one_real_exhaust_runner_entrypoint_exists_and_it_is_freeze_gated():
    """goal-hypothesis-foundry-iter-6 (J-07): this test USED TO be satisfied by absence (no real
    exhaust entrypoint could exist before step 8 began). This iteration's entire purpose is to add
    EXACTLY ONE legitimate such entrypoint -- ``scripts/run_hypothesis_foundry_real_exhaust.py`` --
    so the guard EVOLVES into a positive check (per the iter-3 lesson: an end-to-end claim must be
    grep-verified to cross the real module boundary, not asserted in prose): still zero offenders
    beyond the one now-allowed file, AND that file's own call site is reached only AFTER its own
    freeze-integrity verification and single-flight lock acquisition (line-order, since this
    module's own real exhaust sequence is a plain top-to-bottom function body with no branching
    that could reorder those three calls relative to each other)."""
    allowed = {
        "app/research/foundry_runner.py",
        "app/research/foundry_hermetic_summary.py",
        "scripts/run_hypothesis_foundry_real_exhaust.py",
    }
    call_site = re.compile(r"\b(run_family|run_one_candidate)\s*\(")
    offenders = []
    for py_file in list((BACKEND_DIR / "app").rglob("*.py")) + list((BACKEND_DIR / "scripts").rglob("*.py")):
        rel = py_file.relative_to(BACKEND_DIR).as_posix()
        if rel in allowed:
            continue
        if call_site.search(py_file.read_text(encoding="utf-8", errors="ignore")):
            offenders.append(rel)
    assert offenders == [], f"an UNEXPECTED Foundry exhaust/runner entrypoint now exists: {offenders}"

    exhaust_cli = (BACKEND_DIR / "scripts" / "run_hypothesis_foundry_real_exhaust.py").read_text(encoding="utf-8")
    freeze_verify_idx = exhaust_cli.index("fz.verify_freeze_set_unchanged(")
    single_flight_idx = exhaust_cli.index("fr.SingleFlightLock(")
    run_family_idx = call_site.search(exhaust_cli).start()
    assert freeze_verify_idx < single_flight_idx < run_family_idx, (
        "the real exhaust CLI's own run_family/run_one_candidate call site must be reached only "
        "AFTER its own freeze-integrity verification and single-flight lock acquisition"
    )


# === TC-10: replay verifies, drift refuses -- no second epoch ====================================


def test_tc10_replaying_the_committed_generation_inputs_returns_the_same_epoch_id(manifest):
    """Non-destructive replay of §8.3 against the REAL committed inputs: a fresh store re-mints the
    identical ``epoch_id``/``manifest_hash`` (so the committed identity is a pure function of the
    recorded inputs, not of when it was run), and replaying against a populated store verifies
    rather than creating a second epoch."""
    inputs = manifest["_generation_inputs"]
    fresh: dict = {}
    minted = fz.generate_or_verify_manifest(fresh, inputs)
    assert minted.epoch_id == manifest["epoch_id"]
    assert minted.manifest_hash == manifest["manifest_hash"]
    assert minted.inputs_hash == manifest["_inputs_hash"]

    replayed = fz.generate_or_verify_manifest(fresh, inputs)
    assert replayed.epoch_id == minted.epoch_id
    assert len(fresh) == 1, "a second epoch slot was created on replay"


def test_tc10_drifted_generation_inputs_are_refused_rather_than_minting_epoch_2(manifest):
    inputs = dict(manifest["_generation_inputs"])
    fresh: dict = {}
    fz.generate_or_verify_manifest(fresh, inputs)
    drifted = dict(inputs)
    drifted["source_registry_hash"] = "0" * 64
    with pytest.raises(fz.ManifestDriftRefused):
        fz.generate_or_verify_manifest(fresh, drifted)


# === goal-hypothesis-foundry-iter-6 TC-7: a DELETED manifest store refuses rather than silently
# minting a second epoch. The drift guard directly above only fires when an EXISTING slot disagrees
# with the new inputs -- an EMPTY store has nothing to disagree with, so before this iteration's fix
# a missing `epoch-manifest.json` looked exactly like a first-ever generation and would have been
# silently overwritten with whatever the current inputs happened to be. These are the tests that
# make the refusal itself a standing guarantee rather than a one-time manual verification. ==========


def _load_generation_module():
    """Loads the real generation CLI as a module -- the same importlib load
    ``test_tc1_registry_hash_and_dispositions_are_reproduced_by_the_real_generator`` performs, so
    these tests exercise the SHIPPED function rather than a copy. Import-time side effects: none
    beyond constant/dataclass definition (the script's own work all sits inside ``main``)."""
    spec = importlib.util.spec_from_file_location(
        "_generate_real_epoch_for_tc7_test",
        BACKEND_DIR / "scripts" / "generate_hypothesis_foundry_real_epoch.py",
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_tc7_deleted_manifest_store_refuses_instead_of_silently_minting_a_new_epoch(tmp_path, monkeypatch):
    """The refusal half of TC-7: ``epoch-manifest.json`` gone while its SIBLING
    ``freeze-record.json`` (written in the same generation run, immediately after it) still stands
    as proof a real generation already happened -> typed ``ManifestStoreMissingError``, never an
    empty store. Fully hermetic: both paths point into ``tmp_path``; the real tracked artifacts are
    never read, written, or deleted by this test."""
    module = _load_generation_module()
    missing_manifest = tmp_path / "epoch-manifest.json"
    standing_freeze_record = tmp_path / "freeze-record.json"
    standing_freeze_record.write_text(json.dumps({"freeze_commit": "0" * 40}), encoding="utf-8")
    monkeypatch.setattr(module, "FREEZE_RECORD_PATH", standing_freeze_record)

    assert not missing_manifest.exists()
    with pytest.raises(module.ManifestStoreMissingError):
        module._load_existing_manifest_store(missing_manifest)


def test_tc7_first_ever_generation_still_gets_a_genuinely_fresh_store(tmp_path, monkeypatch):
    """The other half of TC-7 -- the refusal must NOT be a blanket one, or the very first real
    generation could never run: with NEITHER file on disk (a true fresh install), the loader still
    returns an empty store."""
    module = _load_generation_module()
    monkeypatch.setattr(module, "FREEZE_RECORD_PATH", tmp_path / "freeze-record.json")
    assert module._load_existing_manifest_store(tmp_path / "epoch-manifest.json") == {}


def test_tc7_the_real_committed_manifest_reconstructs_a_populated_replay_store(manifest):
    """Positive control over the REAL committed artifact (read-only): the loader reconstructs the
    populated one-slot store that makes a re-run replay-VERIFY, and every reconstructed field is the
    committed one -- so the refusal above is guarding a path that genuinely works when the file is
    present."""
    module = _load_generation_module()
    store = module._load_existing_manifest_store(module.EPOCH_MANIFEST_PATH)
    assert list(store) == ["epoch"]
    record = store["epoch"]
    assert record.epoch_id == manifest["epoch_id"]
    assert record.manifest_hash == manifest["manifest_hash"]
    assert record.inputs_hash == manifest["_inputs_hash"]
    assert record.payload == manifest["_generation_inputs"]


# === §8.4/§8.5: the freeze-set actually pins the science files in THIS checkout ===================


def test_freeze_set_entries_still_match_the_science_files_in_this_checkout(freeze_set):
    """Recomputes sha256 for every enumerated freeze-set path and compares against the pinned
    digest -- the §8.5 "recomputed freeze-set hashes are the enforceable primitive" check, run over
    the real committed freeze-set.

    goal-hypothesis-foundry-iter-6 (closes audit finding B1): the committed ``freeze-set.json`` now
    records REPO-RELATIVE paths (``apps/backend/app/research/...``, ``docs/...``), so every entry
    resolves identically -- and portably, across any checkout/worktree of this same commit -- by
    joining it directly onto ``REPO_ROOT``, with no marker-based workaround. See
    ``test_tc8_verify_freeze_set_unchanged_and_commit_ancestry_both_pass_against_the_new_freeze_
    commit`` for the equivalent check run through the real production ``verify_freeze_set_unchanged``
    function rather than this test's own direct recompute."""
    entries = freeze_set["entries"]
    assert entries, "empty freeze set"
    # The pinned hash must be a pure function of the recorded entries.
    assert fz._sha256(fz._canonical(entries)) == freeze_set["freeze_set_hash"]

    drifted = []
    for rel, expected in entries.items():
        assert not rel.startswith("/"), f"expected a repo-relative freeze-set key, got: {rel}"
        path = REPO_ROOT / rel
        assert path.is_file(), f"freeze-set path missing from this checkout: {rel}"
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            drifted.append(rel)
    assert drifted == [], f"frozen science files changed after the freeze: {drifted}"


# === §1.4: every quoted span is traceable to the ratified source file it cites ====================

# `foundry_source_registry.lint_quoted_spans` only proves a span is a substring of its OWN record's
# `source_excerpt`, and `source_hash` is sha256 of that same self-authored excerpt -- so nothing in
# the production path ties the frozen registry to the ratified files it cites (iter-5 audit finding
# B3). This is the missing half of §1.4's "mechanical registry lint verifies that every quoted span
# is an exact substring of the cited ratified source".
#
# The recorded spans are ASCII de-markup transcriptions of markdown/Python sources, so the
# comparison normalizes both sides identically: markdown emphasis/backticks/list+blockquote markers
# and comment hashes are stripped, whitespace is collapsed, and the typographic/mathematical
# Unicode the sources use is mapped to the ASCII the registry records.
_UNICODE_TO_ASCII = [
    ("≥", ">="), ("≤", "<="), ("−", "-"), ("—", "--"), ("–", "-"),
    ("μ", "mu"), ("·", "*"), ("×", "x"), ("≈", "~="), ("→", "->"),
    ("’", "'"), ("‘", "'"), ("“", '"'), ("”", '"'), ("…", "..."),
    ("σ", "sigma"), ("±", "+-"),
]

# The two spans that are faithful TRANSLITERATIONS of mathematical notation rather than character-
# for-character quotations. Listed explicitly so any OTHER divergence fails this test; each is
# paired with an ASCII-invariant fragment of the same sentence that must still be present in the
# cited file, so the citation stays anchored.
_KNOWN_TRANSLITERATIONS = {
    # docs/research-directions.md Card 9.1: "CD_t = Σ_{i≤t, side_i ≠ unknown} sign(side_i)·size_i"
    "CD_t = sum over i<=t, side_i != unknown of sign(side_i)*size_i (session-anchored, RTH prints, shares).":
        "(session-anchored, RTH prints, shares)",
    # docs/research-directions.md Card 9.6: "P(next same | run ≥ k)` for k ∈ {5, 10, 20}"
    "observed P(next same | run >= k) for k in {5, 10, 20} vs a seeded within-session shuffle of the "
    "side sequence (permutation baseline, 1,000 shuffles, seeded).":
        "vs a seeded within-session shuffle of the",
}


def _normalize(text: str) -> str:
    for unicode_char, ascii_text in _UNICODE_TO_ASCII:
        text = text.replace(unicode_char, ascii_text)
    text = text.replace("`", "").replace("**", "").replace("*", "")
    text = re.sub(r"(?m)^[ \t]*(>[ \t]?)+", "", text)
    text = re.sub(r"(?m)^[ \t]*#+[ \t]?", "", text)
    text = re.sub(r"(?m)^[ \t]*[-+][ \t]", "", text)
    return re.sub(r"\s+", " ", text).strip()


def test_every_quoted_span_is_traceable_to_the_ratified_source_file_it_cites(registry):
    sources: dict[str, str] = {}
    pilot_status_values = {
        value
        for entry in micro_readiness.PILOT_STUDY_STATUS.values()
        for value in entry.values()
        if isinstance(value, str) and value
    }

    unmatched: list[tuple[str, str]] = []
    for record in registry["records"]:
        source_path = REPO_ROOT / record["source_path"]
        assert source_path.is_file(), f"{record['source_id']} cites a path that does not exist"
        if record["source_path"] not in sources:
            sources[record["source_path"]] = _normalize(source_path.read_text(encoding="utf-8"))
        body = sources[record["source_path"]]

        for span in record["quoted_spans"]:
            text = span["text"]
            # §1.4's own internal lint: the span sits at its recorded offset in the excerpt.
            start = span["location"]
            assert record["source_excerpt"][start:start + len(text)] == text, record["source_id"]
            if _normalize(text) in body:
                continue
            # A span quoted from a Python dict literal is compared against the live VALUE, since
            # the raw file splits long literals across implicit-concatenation line breaks.
            if text in pilot_status_values:
                continue
            anchor = _KNOWN_TRANSLITERATIONS.get(" ".join(text.split()))
            if anchor is not None:
                assert _normalize(anchor) in body, f"{record['source_id']}: transliteration anchor lost"
                continue
            unmatched.append((record["source_id"], text[:120]))

    assert unmatched == [], (
        "quoted spans that are no longer traceable to their cited ratified source "
        f"(source drift, or a citation that was never exact): {unmatched}"
    )
