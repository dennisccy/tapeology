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


def test_tc9_no_real_exhaust_runner_entrypoint_exists_to_read_a_candidate_outcome():
    """J-07 is barred from this era's iteration 5: the real exhaust runner must not be able to run.
    It is satisfied by absence -- no CLI, route, or ``__main__`` anywhere under ``apps/backend``
    drives ``foundry_runner`` over real data. This guard fails the moment one appears, so the
    barrier stops being an unexamined claim in a handoff."""
    # The only non-test caller of the runner's candidate-evaluation entrypoints is the hermetic
    # oracle summary, which drives purely synthetic fixture anchors. Anything else -- a CLI under
    # `scripts/`, a route, a manager -- would be a path capable of reading a real outcome.
    allowed = {"app/research/foundry_runner.py", "app/research/foundry_hermetic_summary.py"}
    call_site = re.compile(r"\b(run_family|run_one_candidate)\s*\(")
    offenders = []
    for py_file in list((BACKEND_DIR / "app").rglob("*.py")) + list((BACKEND_DIR / "scripts").rglob("*.py")):
        rel = py_file.relative_to(BACKEND_DIR).as_posix()
        if rel in allowed:
            continue
        if call_site.search(py_file.read_text(encoding="utf-8", errors="ignore")):
            offenders.append(rel)
    assert offenders == [], f"a Foundry exhaust/runner entrypoint now exists: {offenders}"


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


# === §8.4/§8.5: the freeze-set actually pins the science files in THIS checkout ===================


def test_freeze_set_entries_still_match_the_science_files_in_this_checkout():
    """Recomputes sha256 for every enumerated freeze-set path and compares against the pinned
    digest -- the §8.5 "recomputed freeze-set hashes are the enforceable primitive" check, run over
    the real committed freeze-set.

    Deliberately resolves each entry RELATIVE to this checkout's root rather than using the key
    verbatim: the committed ``freeze-set.json`` records absolute, machine-local paths
    (``/home/.../tapeology/apps/backend/app/research/...``), so ``foundry_freeze.
    verify_freeze_set_unchanged`` -- which resolves the key literally -- cannot verify this
    freeze-set from any other checkout, and in a second worktree ON THE SAME MACHINE would verify
    the ORIGINAL tree's files while a runner executes the worktree's. That is an audit finding
    against the artifact (see the iter-5 audit report, finding B1), not something this test can
    repair; this test performs the portable equivalent so the drift guard exists in the meantime.
    """
    freeze_set = _load_json("freeze-set.json")
    entries = freeze_set["entries"]
    assert entries, "empty freeze set"
    # The pinned hash must be a pure function of the recorded entries.
    assert fz._sha256(fz._canonical(entries)) == freeze_set["freeze_set_hash"]

    drifted = []
    for recorded_path, expected in entries.items():
        marker = "apps/backend/" if "apps/backend/" in recorded_path else "docs/"
        rel = recorded_path[recorded_path.index(marker):]
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
