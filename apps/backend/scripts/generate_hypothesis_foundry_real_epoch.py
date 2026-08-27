"""Generates and verifies the Hypothesis Foundry's ONE real epoch (goal-hypothesis-foundry-iter-5,
Binding Execution Order step 6/7, J-06). This is the operator-act CLI the phase spec requires --
following ``record_foundry_era_open_baseline.py``'s own convention (argparse, prints a summary to
stderr, no implicit git operations: this script never runs ``git add``/``git commit`` itself).

**What this script does, in order:**

1. Builds the 11 real ``SourceRecord``\\ s required by ``docs/goal.md`` §1.1/§1.2, each citing exact
   quoted spans from the ratified repository text (``docs/research-directions.md``'s Era 9 Wave-1
   cards + Rapid-Microscope opening note + era ledger row; ``apps/backend/app/research/
   micro_readiness.py``'s ``PILOT_STUDY_STATUS`` for the two parked/proxy studies) -- never the
   existing 7/8-fixture hermetic set ``foundry_compiler.sources_compiler_hermetic_fixture_view``
   already uses (goal.md carried lesson 2).
2. Runs ``foundry_compiler.compile_sources`` over this real batch (no new compiler module, no new
   disposition path -- the exact same mechanical §2 precedence the hermetic fixtures already prove).
3. Calls ``foundry_freeze.generate_or_verify_manifest`` to mint (or verify/replay) the real
   ``epoch_id``/``manifest_hash``.
4. Writes ``source-registry.json``/``epoch-manifest.json`` FIRST (goal-hypothesis-foundry-iter-6:
   moved ahead of the freeze-set/freeze-record step so both tracked JSONs already exist on disk
   when ``foundry_freeze.generate_freeze_set`` scans and hashes them -- closes audit finding B7's
   freeze-set half). Then calls ``generate_freeze_set`` (repo-relative keys, closing B1) over the
   real ``apps/backend/app/research`` directory plus ``FREEZE_SET_EXTRA_PATHS`` (the spec, the two
   just-written tracked JSONs, and both the generation/exhaust CLI scripts -- see that constant's
   own module-level comment for why ``freeze-record.json``/``freeze-set.json`` themselves are
   deliberately NOT among them), then ``build_freeze_record`` to pin every required hash plus the
   §8.4 "era-open evidence-class contract" field (closing B7's freeze-record half), then writes
   ``freeze-set.json``/``freeze-record.json``.
5. Records this run's own outcome-access census (a dynamic call-trace over the actual compile/
   freeze-generation calls, counting every function CALL whose defining module is one of the
   forbidden Scout-ledger/walk-forward/Vault/Referee/PnL/Foundry-runner modules) -- must be ``0``,
   verified by an assertion before any file is written. This deliberately traces CALLS, not
   ``sys.modules`` membership: ``foundry_compiler``/``foundry_freeze`` themselves transitively
   *import* ``scout_ledger``/``walkforward``/``vault``/``referee_*``/``micro_accessor`` as
   unavoidable infrastructure (``scout.py`` needs their types/constants), which is not the same as
   this script's own generation logic ever *calling into* one of them to read a real outcome.

**freeze_commit ordering.** ``build_freeze_record`` takes ``freeze_commit`` as a plain string --
there is no way to know the hash of a commit before it exists. This script resolves it the same way
§8.4's ancestry check actually works: ``freeze_commit = git rev-parse HEAD`` AT GENERATION TIME,
BEFORE the new commit exists. That existing commit is trivially an ancestor of the new commit once
the five tracked files are committed on top of it. Do not attempt to self-reference the
not-yet-created commit; do not commit in two passes to "fix up" the hash.

**IMPORTANT (iter-5 audit correction).** ``freeze_commit`` is an ancestry ANCHOR, not a content
guarantee: it does NOT necessarily contain the science-file bytes the freeze-set hashes were
computed over. This script never modifies a science file, but it hashes the WORKING TREE, so any
freeze-set path carrying an uncommitted change at generation time is pinned at a byte state that
exists in no commit -- which is exactly what happened on the real iter-5 run
(``app/research/foundry_compiler.py`` was pinned from the working tree and matches neither
``freeze_commit`` nor the freeze commit's ``HEAD``). §8.4's enforceable primitive is the recomputed
freeze-set hash set, and that still holds; but the frozen state is only recoverable from Git once
every freeze-set path is itself committed. Commit the science-file changes BEFORE generating, or
immediately after -- until then a ``git checkout --`` on a pinned path destroys a state no second
epoch may recreate (§8.1).

**Replay.** Re-running this script with byte-identical inputs (the same 11 records, same repository
state) reads the EXISTING ``epoch-manifest.json`` (if present), reconstructs its
``ManifestRecord``, and calls ``generate_or_verify_manifest`` again -- verifying/no-opping the
existing ``epoch_id``/``manifest_hash`` rather than minting a second epoch (§8.3). A changed input
(e.g. an edited source record) raises ``ManifestDriftRefused`` -- this script does not catch that
exception; a drifted rerun is a genuine, visible failure, never silently swallowed into a second
epoch.

Run from ``apps/backend`` after a full green suite:

    .venv/bin/python scripts/generate_hypothesis_foundry_real_epoch.py
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import subprocess
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(BACKEND_DIR))

from app.env import load_env  # noqa: E402

load_env()

from app.config import CONFIG  # noqa: E402
from app.research import foundry_compiler as fc  # noqa: E402
from app.research import foundry_freeze as fz  # noqa: E402
from app.research import scout  # noqa: E402
from app.research.foundry_source_registry import (  # noqa: E402
    DISPOSITION_ALIASED_VARIANT_VOCABULARY,
    DISPOSITION_EXCLUDED_GATE_CLOSED,
    DISPOSITION_EXCLUDED_PREREQUISITE_UNMET,
    DISPOSITION_EXCLUDED_PREVIOUSLY_KILLED,
    FOUNDRY_SPEC_VERSION,
    BLOCKED_DIRECTION_SENTINEL,
    BLOCKED_UNSUPPORTED_STUDY_FORM_SENTINEL,
    THRESHOLD_LITERAL_RATIFIED,
    THRESHOLD_NATURAL_SEMANTIC_BOUNDARY,
    ProxyDeclaration,
    QuotedSpan,
    SourceRecord,
    SupersessionDeclaration,
)

# --- tracked §8.2 output paths (repo-relative) ------------------------------------------------------
FOUNDRY_DOCS_DIR = REPO_ROOT / "docs" / "hypothesis-foundry"
FOUNDRY_REPORTS_DIR = REPO_ROOT / "reports" / "hypothesis-foundry"
SOURCE_REGISTRY_PATH = FOUNDRY_DOCS_DIR / "source-registry.json"
EPOCH_MANIFEST_PATH = FOUNDRY_DOCS_DIR / "epoch-manifest.json"
FREEZE_SET_PATH = FOUNDRY_DOCS_DIR / "freeze-set.json"
FREEZE_RECORD_PATH = FOUNDRY_DOCS_DIR / "freeze-record.json"
AUDIT_REPORT_PATH = FOUNDRY_REPORTS_DIR / "source-registry-audit.md"
SPEC_PATH = REPO_ROOT / "docs" / "hypothesis-foundry-spec.md"
# goal-hypothesis-foundry-iter-6 (closes audit finding B7's freeze-set half). §8.4's own text names
# "the Foundry methodology/spec and tracked registry/manifest files" -- the tracked REGISTRY and
# MANIFEST are `source-registry.json`/`epoch-manifest.json`, never `freeze-record.json`/
# `freeze-set.json` themselves (§8.4 never names either of those two as freeze-set members, and
# freeze-record.json COULD NOT be: its own content embeds `freeze_set_hash`, so including its file
# hash inside the very freeze-set that hash is computed over is the identical self-reference
# freeze-set.json is already, explicitly, excluded for -- just one hop removed). "every Foundry
# scientific implementation module/CLI" additionally covers the real generation CLI (this script)
# and the real exhaust CLI (`run_hypothesis_foundry_real_exhaust.py`) -- both science-affecting,
# neither a sibling `app/research/*.py` import the scanner would auto-discover.
EXHAUST_CLI_PATH = BACKEND_DIR / "scripts" / "run_hypothesis_foundry_real_exhaust.py"
_THIS_GENERATION_CLI_PATH = Path(__file__).resolve()
FREEZE_SET_EXTRA_PATHS = (
    SPEC_PATH, SOURCE_REGISTRY_PATH, EPOCH_MANIFEST_PATH, _THIS_GENERATION_CLI_PATH, EXHAUST_CLI_PATH,
)

# --- §8.1's own import/IO tripwire: every module whose FUNCTIONS could hand this script a real
# candidate outcome, Scout row, walk-forward result, Vault state, Referee result, or PnL scan.
# Deliberately checked by tracing CALLS (`_outcome_access_guard` below), never `sys.modules`
# membership: `foundry_compiler`/`foundry_freeze` themselves transitively *import*
# `scout_ledger`/`walkforward`/`vault`/`referee_*`/`micro_accessor` as unavoidable infrastructure
# (`scout.py` needs their types/constants) -- that is not the same as this script's own generation
# logic ever *calling into* one of them.
_FORBIDDEN_OUTCOME_MODULES = frozenset(
    {
        "app.research.scout_ledger",
        "app.research.walkforward",
        "app.research.walkforward_ledger",
        "app.research.vault",
        "app.research.referee_adjudicate",
        "app.research.referee_evidence",
        "app.research.referee_null",
        "app.research.referee_registry",
        "app.research.referee_routes",
        "app.research.referee_stats",
        "app.research.pnl_scan",
        "app.research.pnl_baseline",
        "app.research.pnl_history",
        "app.research.pnl_ledger",
        "app.research.foundry_ledger",
        "app.research.foundry_runner",
        "app.research.foundry_interpreter",
        "app.research.micro_accessor",
    }
)


@contextlib.contextmanager
def _outcome_access_guard():
    """A ``sys.settrace``-based dynamic call tracer: while active, records the module name of
    EVERY function call whose defining module is one of ``_FORBIDDEN_OUTCOME_MODULES``. Yields the
    (initially empty) hit list the caller inspects after the ``with`` block -- ``len(hits)`` is
    this run's outcome-access census, which must be ``0``. Tracing calls (not import presence) is
    the only way to distinguish "this generation logic never executed a real outcome-reading
    function" from "a wholly unrelated module happens to be loaded because of an unavoidable
    infrastructure import chain"."""
    hits: list[str] = []

    def _tracer(frame, event, arg):
        if event == "call":
            module = frame.f_globals.get("__name__", "")
            if module in _FORBIDDEN_OUTCOME_MODULES:
                hits.append(module)
        return _tracer

    previous = sys.gettrace()
    sys.settrace(_tracer)
    try:
        yield hits
    finally:
        sys.settrace(previous)


def _hash_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _full_record_view(record: SourceRecord, disposition: str) -> dict:
    """The FULL §1.4 field set for one source record, for the checked-in `source-registry.json`
    artifact. Deliberately NOT `foundry_source_registry._canonical_source_record()` alone -- that
    function is the hash-CANONICALIZATION projection `source_registry_hash` is computed over, and
    correctly excludes `audit_note`/`source_hash`/`extra` because those must never affect the
    hash. Reusing it as the human/audit-facing artifact serializer would silently drop
    `audit_note` (§1.4's own required "why each compiler decision follows from the source rules"
    field) from the committed file -- a real defect a fresh-context audit caught in this
    iteration's own first draft. This function adds those fields back for the artifact only; it
    never feeds into any hash."""
    canonical = fc._canonical_source_record(record)  # noqa: SLF001 -- same module family, by design
    return {**canonical, "audit_note": record.audit_note, "source_hash": record.source_hash, "disposition": disposition}


def _git(*args: str) -> str:
    result = subprocess.run(["git", *args], cwd=str(REPO_ROOT), capture_output=True, text=True, check=True)
    return result.stdout.strip()


# === §1: the 11 real required source objects =========================================================
#
# Every `source_excerpt` below is a FAITHFUL ASCII TRANSCRIPTION of the cited ratified file, not a
# byte-exact copy (iter-5 audit correction to an earlier "copied VERBATIM" claim here): markdown
# emphasis/backticks/list+blockquote markers and Python comment hashes are stripped, wrapped lines
# are rejoined, typographic and mathematical Unicode is rendered in ASCII (>= for
# \N{GREATER-THAN OR EQUAL TO}, -- for an em dash, "sum over ... of" for a sigma with subscripts,
# "in" for set membership), and an excerpt may concatenate disjoint spans of one file behind a
# ` || ` separator. `lint_quoted_spans` (called inside `compile_sources`, never skipped) verifies
# each `QuotedSpan` against its own record's `source_excerpt` ONLY -- it does not reach the cited
# file, so it cannot by itself prove provenance. The check that DOES reach the cited files is
# `tests/test_foundry_real_epoch_artifacts.py::
# test_every_quoted_span_is_traceable_to_the_ratified_source_file_it_cites`; keep it green.
# No field below reads or is chosen because of any candidate outcome, p-value, effect, sample count,
# or prior Scout verdict -- every decision follows mechanically from the quoted text under
# `docs/goal.md` §2's owner meta-policy.
#
# Count reconciliation (11 records for 15 named items across §1.1/§1.2's own bullets): Study 1 and
# Study 3 are each ONE record (the "parked mechanism" and its "frozen pilot proxy declaration" are
# the SAME object under one id -- `micro_readiness.PILOT_STUDY_STATUS` and
# `scout.pilot_study_candidate_grid()` both key on the identical `range_wall_failed_aggression`/
# `capitulation_exhaustion` ids, never two separate registrations); Cards 9.8-9.11 are ONE combined
# record (goal.md §1.2 states their exclusion with one arrow, exactly like "Card 9.1 / Study 2", not
# with the per-card structure Cards 9.3-9.7 each get); Card 9.6 splits into its two named
# sub-statements per §1.3's own explicit instruction ("Card 9.6 may contain more than one study
# statement... They receive separate dispositions if their statistical forms differ"). This yields
# 2 (Study 1, Study 3) + 4 (Cards 9.3, 9.4, 9.5, 9.7) + 2 (Card 9.6's two sub-statements)
# + 1 (Card 9.1 / Study 2) + 1 (Card 9.2) + 1 (Cards 9.8-9.11) = 11 records, verified by TC-1.
# NOTE (iter-5 audit): this partition is an interpretive reading, not goal.md's own bullet count --
# §1.1 lists the two pilot proxies as their own bullets and §1.2 names four Wave-2 cards. Nothing is
# lost (each collapsed constituent id is carried in `aliases_lineage_ids`, per §7.1's "no required
# source silently disappears"), but `card-9.8`..`card-9.11` and the two proxy declarations do not
# exist as standalone `source_id`s. See `docs/handoffs/goal-hypothesis-foundry-iter-5-audit.md` B6.


def _study_1_range_wall_failed_aggression() -> SourceRecord:
    excerpt = (
        "`range_wall_failed_aggression` states a THREE-part conjunction: high aggression into the "
        "wall, collapsing impact efficiency, AND opposite-side `refill_consistent` replenishment. "
        "`failed_aggression_score` covers the first two as one composite; the refill co-occurrence "
        "is genuinely unbuilt, and `scout.py`'s own frozen comment says so. Neither gap is a coding "
        "task. Each needs the owner to SPECIFY the missing mechanism (what counts as \"then\", over "
        "what window, with what replenishment measure) before anything can implement it, and "
        "inventing that specification here would be choosing the hypothesis after seeing the tape. "
        "Both are therefore PARKED, and must not be screened as if they were their full stated "
        "mechanisms. || missing: opposite-side refill_consistent co-occurrence is unbuilt and "
        "unspecified || do_not: screen the failed_aggression_score proxy under this mechanism's "
        "name"
    )
    span_conjunction = (
        "`range_wall_failed_aggression` states a THREE-part conjunction: high aggression into the "
        "wall, collapsing impact efficiency, AND opposite-side `refill_consistent` replenishment."
    )
    span_do_not = "screen the failed_aggression_score proxy under this mechanism's name"
    span_missing = "opposite-side refill_consistent co-occurrence is unbuilt and unspecified"
    return SourceRecord(
        source_id="pilot-study-1-range-wall-failed-aggression",
        source_path="apps/backend/app/research/micro_readiness.py",
        section_ref="lines 116-158 (PILOT_STUDY_STATUS['range_wall_failed_aggression'])",
        quoted_spans=(
            QuotedSpan(text=span_conjunction, location=excerpt.index(span_conjunction)),
            QuotedSpan(text=span_missing, location=excerpt.index(span_missing)),
            QuotedSpan(text=span_do_not, location=excerpt.index(span_do_not)),
        ),
        source_excerpt=excerpt,
        mechanism_statement=(
            "At band-map wall touches, does high aggression-into-the-wall with collapsing impact "
            "efficiency and opposite-side refill_consistent replenishment precede rejection more "
            "than comparable touches without that signature (docs/goal-archive/"
            "goal-2026-08-26.md J-09 step 1, the Rapid Microscope's own predeclaration of this "
            "study, cited here as corroborating provenance for the mechanism's full stated shape; "
            "the operative PARKED/proxy ruling itself is micro_readiness.py's, quoted above)."
        ),
        operative_formula_refs=("failed_aggression_score",),
        direction_derivation=BLOCKED_DIRECTION_SENTINEL,
        comparator_derivation="complement_within_same_eligible_population",
        audit_note=(
            "Disposition is ALIASED_PROXY_ONLY under §2 step 1 (proxy_of set): the only "
            "operationalized artifact for this study is scout.py's own frozen "
            "pilot_study_candidate_grid()['range_wall_failed_aggression'] request "
            "(feature_name='failed_aggression_score', op='ge', value=0.5, "
            "structure_context_kind='band_touch', sidedness=None) -- a single-feature proxy for "
            "the quoted THREE-part conjunction, never the full mechanism itself. The quoted "
            "do_not restriction is preserved verbatim per goal.md §1.1 ('these proxies are source "
            "objects for provenance, not permission to launder a partial proxy as the full "
            "mechanism'). Independently of the proxy disposition, the full mechanism also carries "
            "two undefined magnitude words ('high' aggression, 'collapsing' impact efficiency) per "
            "§2.2's own listed example -- recorded via unresolved_magnitude_words below so an "
            "auditor sees the full mechanism could not compile even absent the proxy rule. No "
            "candidate outcome, p-value, effect, sample count, or Scout verdict was read to reach "
            "this disposition -- Study 1 was never screened this era (J-07 has not run)."
        ),
        lineage_id="range_wall_failed_aggression",
        threshold_provenance=THRESHOLD_LITERAL_RATIFIED,
        unresolved_magnitude_words=("high", "collapsing"),
        proxy_of=ProxyDeclaration(
            parked_study_source_id="range_wall_failed_aggression",
            do_not="screen the failed_aggression_score proxy under this mechanism's name",
        ),
    )


def _study_3_capitulation_exhaustion() -> SourceRecord:
    excerpt = (
        "`capitulation_exhaustion` states an ORDERED SEQUENCE: extreme SELL aggression, THEN "
        "collapsing negative impact efficiency / replenishment. The available request is a single "
        "direction-agnostic threshold at a `capitulation` signal -- no then-sequence, no "
        "replenishment term, not sell-specific. Neither gap is a coding task. Each needs the owner "
        "to SPECIFY the missing mechanism (what counts as \"then\", over what window, with what "
        "replenishment measure) before anything can implement it, and inventing that specification "
        "here would be choosing the hypothesis after seeing the tape. Both are therefore PARKED, "
        "and must not be screened as if they were their full stated mechanisms. || missing: the "
        "ordered sell-aggression-THEN-collapse sequence is unimplemented and underspecified (no "
        "defined then-window, no replenishment measure) || do_not: screen a single "
        "direction-agnostic threshold under this mechanism's name"
    )
    span_sequence = (
        "`capitulation_exhaustion` states an ORDERED SEQUENCE: extreme SELL aggression, THEN "
        "collapsing negative impact efficiency / replenishment."
    )
    span_do_not = "screen a single direction-agnostic threshold under this mechanism's name"
    span_missing = (
        "the ordered sell-aggression-THEN-collapse sequence is unimplemented and underspecified "
        "(no defined then-window, no replenishment measure)"
    )
    return SourceRecord(
        source_id="pilot-study-3-capitulation-exhaustion",
        source_path="apps/backend/app/research/micro_readiness.py",
        section_ref="lines 116-158 (PILOT_STUDY_STATUS['capitulation_exhaustion'])",
        quoted_spans=(
            QuotedSpan(text=span_sequence, location=excerpt.index(span_sequence)),
            QuotedSpan(text=span_missing, location=excerpt.index(span_missing)),
            QuotedSpan(text=span_do_not, location=excerpt.index(span_do_not)),
        ),
        source_excerpt=excerpt,
        mechanism_statement=(
            "Do event-level exhaustion signatures (extreme sell aggression then collapsing "
            "negative impact efficiency / replenishment) separate capitulation signals that snap "
            "back from those that do not (docs/goal-archive/goal-2026-08-26.md J-09 step 1, cited "
            "as corroborating provenance for the mechanism's full stated shape; the operative "
            "PARKED/proxy ruling itself is micro_readiness.py's, quoted above)."
        ),
        operative_formula_refs=("failed_aggression_score",),
        direction_derivation=BLOCKED_DIRECTION_SENTINEL,
        comparator_derivation="complement_within_same_eligible_population",
        audit_note=(
            "Disposition is ALIASED_PROXY_ONLY under §2 step 1 (proxy_of set): the only "
            "operationalized artifact for this study is scout.py's own frozen "
            "pilot_study_candidate_grid()['capitulation_exhaustion'] request "
            "(feature_name='failed_aggression_score', op='ge', value=0.7, "
            "structure_context_kind='playbook_signal', setup_id='capitulation', sidedness=None) -- "
            "a single, direction-agnostic threshold, never the quoted ordered sell-then-collapse "
            "sequence. The quoted do_not restriction is preserved verbatim. Independently of the "
            "proxy disposition, the full mechanism also carries two undefined magnitude words "
            "('extreme' sell aggression, 'collapsing' impact efficiency) plus an ordered THEN lag "
            "that §2.2 lists as new science ('inventing an ordered-sequence lag/window') --  "
            "recorded via unresolved_magnitude_words below. No candidate outcome, p-value, effect, "
            "sample count, or Scout verdict was read to reach this disposition -- Study 3 was "
            "never screened this era (J-07 has not run)."
        ),
        lineage_id="capitulation_exhaustion",
        threshold_provenance=THRESHOLD_LITERAL_RATIFIED,
        unresolved_magnitude_words=("extreme", "collapsing"),
        proxy_of=ProxyDeclaration(
            parked_study_source_id="capitulation_exhaustion",
            do_not="screen a single direction-agnostic threshold under this mechanism's name",
        ),
    )


def _card_9_3_top_of_book_imbalance() -> SourceRecord:
    excerpt = (
        "Hypothesis: L1 size imbalance at a zone touch (bid-heavy at support) adds confirm/veto "
        "information beyond the trade-derived features. Formulas: I_t = EWMA(bid_size / (bid_size "
        "+ ask_size)), halflife 5s (config), sizes in ROUND LOTS on both sides (ratio is unit-safe; "
        "never mixed with share counts -- T12). Sampled at arm-eligible events."
    )
    span = (
        "L1 size imbalance at a zone touch (bid-heavy at support) adds confirm/veto information "
        "beyond the trade-derived features."
    )
    return SourceRecord(
        source_id="card-9.3-top-of-book-imbalance",
        source_path="docs/research-directions.md",
        section_ref="Era 9, Wave 1, Card 9.3 (line 1196)",
        quoted_spans=(QuotedSpan(text=span, location=excerpt.index(span)),),
        source_excerpt=excerpt,
        mechanism_statement=(
            "L1 top-of-book size imbalance at a zone touch (bid-heavy at support) adds confirm/veto "
            "information beyond the existing trade-derived features."
        ),
        operative_formula_refs=("quote_imbalance",),
        direction_derivation=BLOCKED_DIRECTION_SENTINEL,
        comparator_derivation="complement_within_same_eligible_population",
        audit_note=(
            "The quoted hypothesis states the feature 'adds confirm/veto information' -- it is "
            "explicitly agnostic about sign (confirm OR veto), never asserting that bid-heavy at "
            "support mechanically implies long (or ask-heavy at resistance implies short). §2.2 "
            "forbids 'inventing a direction not mechanically implied by the ratified statement'; "
            "inventing a long/short mapping here would be exactly that. This is otherwise the "
            "cleanest natural-boundary candidate of the five Wave-1 cards: micro_features."
            "quote_imbalance()'s own signed formula ((bid_size - ask_size) / total) makes its zero "
            "boundary a genuine intrinsic sign boundary (positive = bid-heavy, per §2.3 category 3 "
            "and the quoted parenthetical's own 'bid-heavy' language) -- the block is direction "
            "alone, not the threshold. No candidate outcome, p-value, effect, or Scout verdict was "
            "read to reach this disposition."
        ),
        lineage_id="card-9.3",
        threshold_provenance=THRESHOLD_NATURAL_SEMANTIC_BOUNDARY,
    )


def _card_9_4_burst_climax_detection() -> SourceRecord:
    excerpt = (
        "Hypothesis: trade-arrival bursts at session extremes mark exhaustion (reversal lift); "
        "bursts at zone breaks mark genuine breaks (continuation lift). Formulas: burst z-score "
        "over w = 5s windows: z = (n_w - mu_m*w/60) / sqrt(mu_m*w/60) (Poisson), where mu_m = "
        "expected trades/min at ET minute m from the 5.5 intraday RVOL/arrival baseline (prior 20 "
        "sessions, T5). Burst iff z >= 4 (config). Volume climax: 1m volume >= p95 of "
        "minute-of-day baseline AND price at a session extreme."
    )
    span = (
        "trade-arrival bursts at session extremes mark exhaustion (reversal lift); bursts at zone "
        "breaks mark genuine breaks (continuation lift)."
    )
    return SourceRecord(
        source_id="card-9.4-burst-climax-detection",
        source_path="docs/research-directions.md",
        section_ref="Era 9, Wave 1, Card 9.4 (line 1210)",
        quoted_spans=(QuotedSpan(text=span, location=excerpt.index(span)),),
        source_excerpt=excerpt,
        mechanism_statement=(
            "Trade-arrival bursts at session extremes mark exhaustion (a reversal signature); "
            "bursts at zone breaks mark genuine breaks (a continuation signature)."
        ),
        operative_formula_refs=("volume_burst",),
        direction_derivation=BLOCKED_DIRECTION_SENTINEL,
        comparator_derivation="complement_within_same_eligible_population",
        audit_note=(
            "Two undefined magnitude/qualitative words appear in the quoted hypothesis without a "
            "ratified numeric or structural pin: 'session extremes' (how close to the session "
            "high/low counts as AT the extreme is never stated) and 'genuine breaks' ('genuine' is "
            "exactly the class of word §2.2 lists -- 'high', 'extreme', 'strong', 'near' -- whose "
            "numeric meaning would have to be invented). This is independent of, and prior to, the "
            "population question (neither 'session extreme' nor 'zone break' is a currently "
            "supported scout.STRUCTURE_CONTEXT_KINDS value: only 'band_touch', 'playbook_signal', "
            "and 'none' exist). It is also independent of the fact that the CURRENTLY BUILT "
            "feature (micro_features.volume_burst -- a ratio-to-baseline-median) does not "
            "implement the quoted Poisson z-score formula verbatim; the current brought-forward "
            "feature vocabulary does not preserve a legal climax threshold/context, matching "
            "docs/goal.md §12's own example for this card. No candidate outcome, p-value, effect, "
            "or Scout verdict was read to reach this disposition."
        ),
        lineage_id="card-9.4",
        unresolved_magnitude_words=("extremes", "genuine"),
    )


def _card_9_5_spread_dynamics_regime() -> SourceRecord:
    excerpt = (
        "Hypothesis: spread widening (EWMA_fast/EWMA_slow >= threshold) marks instability where "
        "entries underperform -- a veto; narrowing + one-sided 9.3 imbalance precedes breaks. "
        "Formulas: spread bps EWMAs, halflifes 10s/120s (config); widening iff ratio >= 1.5 "
        "(config)."
    )
    span = (
        "spread widening (EWMA_fast/EWMA_slow >= threshold) marks instability where entries "
        "underperform -- a veto; narrowing + one-sided 9.3 imbalance precedes breaks."
    )
    return SourceRecord(
        source_id="card-9.5-spread-dynamics-regime",
        source_path="docs/research-directions.md",
        section_ref="Era 9, Wave 1, Card 9.5 (line 1224)",
        quoted_spans=(QuotedSpan(text=span, location=excerpt.index(span)),),
        source_excerpt=excerpt,
        mechanism_statement=(
            "Spread widening marks instability where entries underperform (a veto on some other "
            "setup); spread narrowing plus one-sided top-of-book imbalance precedes breaks."
        ),
        operative_formula_refs=("average_spread",),
        direction_derivation=BLOCKED_DIRECTION_SENTINEL,
        comparator_derivation="complement_within_same_eligible_population",
        audit_note=(
            "The quoted mechanism is explicitly a co-occurrence/veto statement, never a "
            "standalone directional thesis: widening is stated only as 'a veto' (on some other, "
            "unnamed setup's entries) and narrowing-plus-imbalance is stated only to 'precede "
            "breaks' without naming the break's own direction. No mechanical long/short "
            "implication exists in the quoted text -- this is the same directionless archetype "
            "the hermetic fixture suite already models for this exact card (foundry_compiler."
            "sources_compiler_hermetic_fixture_view's 'fixture-directionless' record cites section "
            "'9.5' verbatim). No candidate outcome, p-value, effect, or Scout verdict was read to "
            "reach this disposition."
        ),
        lineage_id="card-9.5",
    )


def _card_9_6_shuffled_side_persistence() -> SourceRecord:
    excerpt = (
        "Hypothesis: long same-side print runs continue beyond chance (flow herding), and run "
        "length at a zone touch adds confirm information. Formulas: run = consecutive same-side "
        "prints (unknowns break runs, counted); observed P(next same | run >= k) for k in {5, 10, "
        "20} vs a seeded within-session shuffle of the side sequence (permutation baseline, 1,000 "
        "shuffles, seeded). Evaluate: the permutation comparison IS the study; then atlas for "
        "run-length-at-touch."
    )
    span = (
        "observed P(next same | run >= k) for k in {5, 10, 20} vs a seeded within-session shuffle "
        "of the side sequence (permutation baseline, 1,000 shuffles, seeded)."
    )
    span_evaluate = "the permutation comparison IS the study"
    return SourceRecord(
        source_id="card-9.6-shuffled-side-persistence",
        source_path="docs/research-directions.md",
        section_ref="Era 9, Wave 1, Card 9.6 (line 1234) -- shuffled-side persistence sub-statement",
        quoted_spans=(
            QuotedSpan(text=span, location=excerpt.index(span)),
            QuotedSpan(text=span_evaluate, location=excerpt.index(span_evaluate)),
        ),
        source_excerpt=excerpt,
        mechanism_statement=(
            "Same-side print runs continue beyond chance: the observed conditional continuation "
            "probability P(next print same side | run length >= k) is compared against a "
            "seeded within-session label-shuffle null, for k in {5, 10, 20}."
        ),
        operative_formula_refs=(),
        # Post-audit fix (fresh-context audit, 2026-08-27): the ORIGINAL draft set this to the
        # literal string "long", copying the quoted text's own adjective ("LONG same-side print
        # runs continue beyond chance") -- but that "long" modifies run LENGTH, not a trading
        # direction, and the auditor correctly flagged it as an unsupported value never derived
        # from the text. This study also genuinely has no return/outcome variable at all (its
        # dependent variable is "next print's side", never a price return), so no long|short
        # sidedness concept mechanically applies -- the honest value is the BLOCKED_DIRECTION
        # sentinel, applied uniformly with every other record here, never chosen to protect a
        # preferred disposition.
        direction_derivation=BLOCKED_DIRECTION_SENTINEL,
        comparator_derivation=BLOCKED_UNSUPPORTED_STUDY_FORM_SENTINEL,
        audit_note=(
            "Per §1.3, Card 9.6 contains more than one study statement; this record is the "
            "shuffled-side persistence sub-statement (the sibling run-length-at-touch sub-"
            "statement is a separate record, card-9.6-run-length-at-touch, cross-referenced via "
            "aliases_lineage_ids). This record is DOUBLY blocked, honestly: (1) it has no "
            "return/outcome variable at all -- its dependent variable is 'next print's side', "
            "never a price return -- so direction_derivation is honestly the BLOCKED_DIRECTION "
            "sentinel (the quoted text's own word 'long' is an adjective for run LENGTH, not a "
            "trading-direction claim -- a fresh-context audit caught an earlier draft's incorrect "
            "reuse of that word as a direction value, corrected here); (2) independently, its "
            "quoted evaluation method IS a comparison of an observed conditional probability "
            "against a label-shuffled null of the SAME sequence -- a materially different "
            "statistical form from scout.screen_candidate's candidate-vs-comparator outcome-mean "
            "block-permutation screen, which has no mechanism for a P(event|condition)-vs-shuffle "
            "test -- so comparator_derivation is honestly the BLOCKED_UNSUPPORTED_STUDY_FORM "
            "sentinel too. Per compile_source_disposition's own fixed, uniform precedence "
            "(direction checked before comparator, identically for every record), this record's "
            "mechanical disposition is BLOCKED_DIRECTION -- doubly justified, not a disposition "
            "picked to be more informative than the mechanical rule would produce. No candidate "
            "outcome, p-value, effect, or Scout verdict was read to reach this disposition."
        ),
        lineage_id="card-9.6-shuffled-side-persistence",
        aliases_lineage_ids=("card-9.6-run-length-at-touch",),
    )


def _card_9_6_run_length_at_touch() -> SourceRecord:
    excerpt = (
        "Hypothesis: long same-side print runs continue beyond chance (flow herding), and run "
        "length at a zone touch adds confirm information."
    )
    span = "run length at a zone touch adds confirm information"
    return SourceRecord(
        source_id="card-9.6-run-length-at-touch",
        source_path="docs/research-directions.md",
        section_ref="Era 9, Wave 1, Card 9.6 (line 1234) -- run-length-at-touch sub-statement",
        quoted_spans=(QuotedSpan(text=span, location=excerpt.index(span)),),
        source_excerpt=excerpt,
        mechanism_statement="Same-side print run length at a zone touch adds confirm information.",
        operative_formula_refs=(),
        direction_derivation=BLOCKED_DIRECTION_SENTINEL,
        comparator_derivation="complement_within_same_eligible_population",
        audit_note=(
            "Per §1.3, this is Card 9.6's second, distinct study statement (sibling: "
            "card-9.6-shuffled-side-persistence). Unlike its sibling, this clause's statistical "
            "form (a threshold on run length at a touch) matches the existing Scout screen's "
            "supported shape -- but, like Card 9.3, the quoted text states only that run length "
            "'adds confirm information' without naming which run side (buy-run vs sell-run) at "
            "which band side (support vs resistance) mechanically implies long vs short; no "
            "ratified mirrored-rejection statement (§3.2) exists for this feature either. "
            "Inventing that mapping would be a new scientific choice, not a mechanical derivation. "
            "docs/goal.md §12 itself frames this exact clause as one that 'may' compile only under "
            "'current source/code evidence at era open' -- that evidence does not resolve "
            "direction. No candidate outcome, p-value, effect, or Scout verdict was read to reach "
            "this disposition."
        ),
        lineage_id="card-9.6-run-length-at-touch",
        aliases_lineage_ids=("card-9.6-shuffled-side-persistence",),
    )


def _card_9_7_event_time_feature_windows() -> SourceRecord:
    card_hypothesis = (
        "Hypothesis: features over the last-N-trades / last-X-shares beat fixed-seconds windows at "
        "the open and lunch (where a 30s window means wildly different event counts)."
    )
    opening_note = (
        "9.7 (event-time feature windows -- last-N-trades / last-X-shares are first-class "
        "representations at frozen sizes)."
    )
    excerpt = card_hypothesis + " || " + opening_note
    span_hyp = (
        "features over the last-N-trades / last-X-shares beat fixed-seconds windows at the open "
        "and lunch"
    )
    span_note = (
        "9.7 (event-time feature windows -- last-N-trades / last-X-shares are first-class "
        "representations at frozen sizes)."
    )
    newer_ref = (
        "docs/research-directions.md, Rapid-Microscope opening note (2026-08-16), 'Brought "
        "forward' bullet, line 1108"
    )
    return SourceRecord(
        source_id="card-9.7-event-time-feature-windows",
        source_path="docs/research-directions.md",
        section_ref="Era 9, Wave 1, Card 9.7 (line 1244)",
        quoted_spans=(
            QuotedSpan(text=span_hyp, location=excerpt.index(span_hyp)),
            QuotedSpan(text=span_note, location=excerpt.index(span_note)),
        ),
        source_excerpt=excerpt,
        mechanism_statement=(
            "Event-time (last-N-trades / last-X-shares) feature windows may out-perform "
            "fixed-seconds windows at the open and lunch, where a fixed window spans wildly "
            "different event counts."
        ),
        operative_formula_refs=("event_time_window",),
        # Post-audit fix (fresh-context audit, 2026-08-27): an earlier draft set this to the
        # unsupported literal "long" (the same copy-paste issue flagged on the 9.6-shuffled
        # record). Card 9.7 is a pure windowing-representation comparison with no trading
        # direction concept at all -- the honest value is the BLOCKED_DIRECTION sentinel. This is
        # harmless to the disposition either way: supersession is checked BEFORE direction in
        # compile_source_disposition's fixed precedence, so ALIASED_VARIANT_VOCABULARY still wins.
        direction_derivation=BLOCKED_DIRECTION_SENTINEL,
        comparator_derivation="complement_within_same_eligible_population",
        audit_note=(
            "Per §1.3's own worked example, Card 9.7 is not itself a directional Scout hypothesis "
            "-- it is a windowing-representation question ('which windowing has higher |rho| "
            "where', per the card's own Evaluate line), so direction_derivation is honestly the "
            "BLOCKED_DIRECTION sentinel (harmless here: supersession is checked first). The "
            "2026-08-16 Rapid-Microscope opening note (quoted above) already brought the "
            "event-time window representations forward as 'first-class representations at frozen "
            "sizes', formula-superseding this card's own open question with an already-decided "
            "current representation. Per §1.3's formula-scoped supersession law, the newer frozen "
            "rule wins for this field and the older card becomes provenance only -- "
            "ALIASED_VARIANT_VOCABULARY, never a fabricated directional candidate manufactured "
            "merely to give this card a Scout screen. No candidate outcome, p-value, effect, or "
            "Scout verdict was read to reach this disposition."
        ),
        lineage_id="card-9.7",
        superseded_fields={"event_time_window": newer_ref},
        supersession=SupersessionDeclaration(
            newer_source_ref=newer_ref, alias_kind=DISPOSITION_ALIASED_VARIANT_VOCABULARY
        ),
    )


def _card_9_1_study_2_excluded() -> SourceRecord:
    card_formula = (
        "Formulas: CD_t = sum over i<=t, side_i != unknown of sign(side_i)*size_i (session-"
        "anchored, RTH prints, shares). Divergence between consecutive touches tau1 < tau2 of the "
        "SAME zone: bearish if price_extreme(tau2) > price_extreme(tau1) AND CD(tau2) <= "
        "CD(tau1) - delta where delta = 0.25 * median 120s volume (config fraction); bullish "
        "mirrored."
    )
    identity_note = (
        "9.1 (the CD_t accumulator verbatim; the symmetric divergence window SUPERSEDED by a "
        "trailing as-of definition -- see the dated amendment on the card itself; it is pilot "
        "study 2)."
    )
    ledger_row = (
        "Rapid-validation funnel shipped (observer/snapshots, Scout + hash-chained trial ledger, "
        "walk-forward, sealed Vault, graduation, MCP -> 28 tools): 13 real candidates, 0 survivors "
        "(killed_null 10 . killed_economic 6 . killed_insufficient_n 3), Study 2 killed on the "
        "merits (p 0.366), Studies 1/3 parked pending owner spec, zero `historical_oos`, Vault "
        "sealed/untouched -- the funnel kills honestly."
    )
    excerpt = card_formula + " || " + identity_note + " || " + ledger_row
    span_identity = "it is pilot study 2"
    span_kill = "Study 2 killed on the merits (p 0.366)"
    span_formula = (
        "CD_t = sum over i<=t, side_i != unknown of sign(side_i)*size_i (session-anchored, RTH "
        "prints, shares)."
    )
    return SourceRecord(
        source_id="card-9.1-study-2-delta-divergence-excluded",
        source_path="docs/research-directions.md",
        section_ref=(
            "Era 9 Card 9.1 (line 1157); Rapid-Microscope opening note (line 1099); era ledger "
            "row 2026-08-24 (line 2045)"
        ),
        quoted_spans=(
            QuotedSpan(text=span_formula, location=excerpt.index(span_formula)),
            QuotedSpan(text=span_identity, location=excerpt.index(span_identity)),
            QuotedSpan(text=span_kill, location=excerpt.index(span_kill)),
        ),
        source_excerpt=excerpt,
        mechanism_statement=(
            "Card 9.1's session cumulative-delta divergence-at-level mechanism is, by the "
            "Rapid-Microscope opening note's own identity statement, pilot Study 2 "
            "(delta_divergence_level_tests) -- already run through the Scout during the closed "
            "Rapid Microscope era and killed."
        ),
        operative_formula_refs=("CD_t",),
        direction_derivation=(
            "bearish if price_extreme(tau2) > price_extreme(tau1) AND CD(tau2) <= CD(tau1) - "
            "delta; bullish mirrored (Card 9.1's own stated rule -- provenance only, not "
            "recompiled)"
        ),
        comparator_derivation="complement_within_same_eligible_population",
        audit_note=(
            "goal.md §1.2: 'Card 9.1 / Study 2 -> EXCLUDED_PREVIOUSLY_KILLED. It may not be "
            "recompiled, reversed, rethresholded, or rerun in this epoch.' The Rapid-Microscope "
            "opening note establishes the identity (Card 9.1 IS pilot Study 2); the closed era's "
            "own ledger row records that Study 2 was already killed on the merits during that "
            "prior, immutable era. This record's disposition is fixed directly by the explicit "
            "exclusion rule, not re-derived from the cited p-value -- the p-value is quoted only "
            "as historical provenance of the prior kill, never re-examined, re-weighed, or used to "
            "choose this disposition (the disposition is EXCLUDED_PREVIOUSLY_KILLED regardless of "
            "what that p-value was)."
        ),
        lineage_id="card-9.1-study-2-delta-divergence-level-tests",
        aliases_lineage_ids=("card-9.1", "study-2-delta-divergence-level-tests"),
        explicit_exclusion=DISPOSITION_EXCLUDED_PREVIOUSLY_KILLED,
    )


def _card_9_2_prerequisite_unmet() -> SourceRecord:
    card_text = (
        "Hypothesis: price bins where heavy net delta produced NO price progress (absorption "
        "bins) mark defended prices that outperform volume-only bins as levels. Build: 8.2's "
        "binning, accumulating SIGNED volume; absorption bin = |delta_bin| >= p90 of session bins "
        "AND price traversal count through the bin >= K (it kept coming back). Level type "
        "delta_wall (feeds the zone engine like any source)."
    )
    deferred_note = "Deferred unchanged: 9.2 (delta-by-price profile; still needs Card 8.2's binning)."
    excerpt = card_text + " || " + deferred_note
    span_build = "Build: 8.2's binning, accumulating SIGNED volume"
    span_deferred = "Deferred unchanged: 9.2 (delta-by-price profile; still needs Card 8.2's binning)."
    return SourceRecord(
        source_id="card-9.2-delta-by-price-profile-excluded",
        source_path="docs/research-directions.md",
        section_ref="Era 9 Card 9.2 (line 1185); Rapid-Microscope opening note (line 1110)",
        quoted_spans=(
            QuotedSpan(text=span_build, location=excerpt.index(span_build)),
            QuotedSpan(text=span_deferred, location=excerpt.index(span_deferred)),
        ),
        source_excerpt=excerpt,
        mechanism_statement=(
            "Price bins where heavy net (signed) delta produced no price progress (absorption "
            "bins) mark defended prices that outperform volume-only bins as levels -- built on "
            "Card 8.2's price-binning infrastructure."
        ),
        operative_formula_refs=("delta_wall",),
        direction_derivation=BLOCKED_DIRECTION_SENTINEL,
        comparator_derivation="complement_within_same_eligible_population",
        audit_note=(
            "goal.md §1.2: 'Card 9.2 -> EXCLUDED_PREREQUISITE_UNMET while its required "
            "delta-by-price binning prerequisite is absent.' The card's own Build step names Card "
            "8.2's binning as its literal prerequisite; the Rapid-Microscope opening note "
            "explicitly confirms this was 'Deferred unchanged' -- the prerequisite was never "
            "built. This disposition follows mechanically from that unmet prerequisite alone, not "
            "from any candidate outcome (none was ever computed -- the prerequisite absence blocks "
            "compilation before any Scout screen could exist)."
        ),
        lineage_id="card-9.2",
        explicit_exclusion=DISPOSITION_EXCLUDED_PREREQUISITE_UNMET,
    )


def _cards_9_8_9_11_gate_closed() -> SourceRecord:
    gate_note = (
        "Wave 2 (9.8-9.11) stays gated. The 6.9 \"atlas\" this era's gate names was never built "
        "(executed era 6 re-scoped per evidence family). The gate is therefore RE-POINTED, not "
        "waived: Wave-2 detector cards open only on `historical_oos`-class Scout/walk-forward "
        "evidence from the rapid-microscope machinery meeting the same thresholds in spirit "
        "(|median rho| >= 0.03 AND sign_consistency >= 0.7 on discovery-class data, per-family)."
    )
    ledger_row = (
        "zero `historical_oos`, Vault sealed/untouched -- the funnel kills honestly."
    )
    excerpt = gate_note + " || " + ledger_row
    span_gate = (
        "Wave 2 (9.8-9.11) stays gated. The 6.9 \"atlas\" this era's gate names was never built "
        "(executed era 6 re-scoped per evidence family)."
    )
    span_repoint = (
        "The gate is therefore RE-POINTED, not waived: Wave-2 detector cards open only on "
        "`historical_oos`-class Scout/walk-forward evidence"
    )
    span_zero_oos = "zero `historical_oos`, Vault sealed/untouched"
    return SourceRecord(
        source_id="cards-9.8-9.11-wave2-gate-closed",
        source_path="docs/research-directions.md",
        section_ref=(
            "Rapid-Microscope opening note (line 1111); era ledger row 2026-08-24 (line 2045)"
        ),
        quoted_spans=(
            QuotedSpan(text=span_gate, location=excerpt.index(span_gate)),
            QuotedSpan(text=span_repoint, location=excerpt.index(span_repoint)),
            QuotedSpan(text=span_zero_oos, location=excerpt.index(span_zero_oos)),
        ),
        source_excerpt=excerpt,
        mechanism_statement=(
            "Cards 9.8 (iceberg/defended-level inference), 9.9 (stop-run sweep-and-reclaim "
            "detector), 9.10 (large-print analytics v2), and 9.11 (absorption-exhaustion timing) "
            "are Wave-2 detectors gated on prior-family historical_oos-class evidence meeting the "
            "6.9-in-spirit thresholds."
        ),
        operative_formula_refs=(),
        direction_derivation=BLOCKED_DIRECTION_SENTINEL,
        comparator_derivation="complement_within_same_eligible_population",
        audit_note=(
            "goal.md §1.2: 'Cards 9.8-9.11 -> EXCLUDED_GATE_CLOSED while their catalog gate lacks "
            "the required prior OOS-class evidence.' The Rapid-Microscope opening note re-points "
            "(never waives) the gate to historical_oos-class evidence; the closed era's own ledger "
            "row records zero historical_oos evidence exists anywhere in the corpus. The gate "
            "therefore remains closed for all four cards under the identical, unmet condition -- "
            "one combined record (mirroring goal.md §1.2's own single-arrow treatment of this "
            "foursome, the same structure as 'Card 9.1 / Study 2') rather than four independently-"
            "authored records that would all cite the identical unmet-gate fact. This disposition "
            "follows mechanically from the gate's own unmet threshold, never from re-examining any "
            "candidate outcome."
        ),
        lineage_id="cards-9.8-9.11-wave2-gate-closed",
        aliases_lineage_ids=("card-9.8", "card-9.9", "card-9.10", "card-9.11"),
        explicit_exclusion=DISPOSITION_EXCLUDED_GATE_CLOSED,
    )


def build_real_source_records() -> list[SourceRecord]:
    """The 11 real required source objects, in a fixed, arbitrary-but-stable order (never derived
    from anything outcome-shaped)."""
    return [
        _study_1_range_wall_failed_aggression(),
        _study_3_capitulation_exhaustion(),
        _card_9_3_top_of_book_imbalance(),
        _card_9_4_burst_climax_detection(),
        _card_9_5_spread_dynamics_regime(),
        _card_9_6_shuffled_side_persistence(),
        _card_9_6_run_length_at_touch(),
        _card_9_7_event_time_feature_windows(),
        _card_9_1_study_2_excluded(),
        _card_9_2_prerequisite_unmet(),
        _cards_9_8_9_11_gate_closed(),
    ]


# === generation entrypoint ============================================================================


def _existing_freeze_commit(path: Path) -> str | None:
    """Reads back a previously-written ``freeze-record.json``'s own ``freeze_commit`` -- ``None``
    only before the first-ever generation. See ``main``'s own comment for why this must never be
    recomputed on a later replay/verify run."""
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload.get("freeze_commit")


class ManifestStoreMissingError(Exception):
    """goal-hypothesis-foundry-iter-6 (TC-7). ``docs/hypothesis-foundry/epoch-manifest.json`` --
    the ONLY state this script reads to decide "has an epoch already been generated" -- is absent,
    but a SIBLING tracked artifact (``freeze-record.json``, always written in the SAME generation
    run immediately after the manifest) proves a real generation already happened. Silently
    treating this as "no epoch yet" would hand ``generate_or_verify_manifest`` an EMPTY store --
    which accepts whatever the CURRENT inputs happen to be as if this were the first-ever
    generation, with no drift check against what was actually frozen before (the drift check only
    fires when an EXISTING slot disagrees with the new inputs -- an empty slot has nothing to
    disagree with). That would silently overwrite ``epoch-manifest.json`` rather than genuinely
    verifying/refusing. Refused instead: restore ``epoch-manifest.json`` from Git history before
    re-running this script."""


def _load_existing_manifest_store(path: Path) -> dict:
    """Reconstructs the ``generate_or_verify_manifest`` in-memory ``store`` from a previously
    written ``epoch-manifest.json`` (if present) -- so a re-run replay-verifies rather than
    silently starting from an empty store (which would look like "no epoch yet" and mint a new
    one). Returns ``{}`` (a genuinely fresh store) only on the FIRST-EVER generation (neither this
    file nor its sibling ``freeze-record.json`` exists yet); raises ``ManifestStoreMissingError``
    when this file specifically has gone missing while ``freeze-record.json`` still stands as
    evidence a generation already happened (TC-7) -- see that exception's own docstring."""
    if not path.exists():
        if FREEZE_RECORD_PATH.exists():
            raise ManifestStoreMissingError(
                f"{path} is missing, but {FREEZE_RECORD_PATH} exists -- a prior real-epoch "
                "generation is already on record and its own replay-detection state must not be "
                "silently treated as a fresh install (spec §8.1: at most one real epoch_id ever)"
            )
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if "epoch_id" not in payload or "_inputs_hash" not in payload:
        return {}
    record = fz.ManifestRecord(
        epoch_id=payload["epoch_id"],
        manifest_hash=payload["manifest_hash"],
        inputs_hash=payload["_inputs_hash"],
        payload=payload["_generation_inputs"],
    )
    return {"epoch": record}


def main() -> int:
    records = build_real_source_records()

    # --- §1.4 mechanical lints + §2 dispositions + §8.1 outcome-access tripwire, all traced ------
    # together: `compile_sources` (lints + dispositions), `generate_or_verify_manifest`,
    # `generate_freeze_set`, and `build_freeze_record` are the ENTIRE real generation command
    # (§8.1's own scope: "checked-in source registry, current frozen feature/construct vocabulary,
    # Foundry compiler rules, current configuration/fingerprint metadata, ratified source hashes").
    # No blueprint is supplied for any record: every one of the 11 disposes to a non-COMPILED state
    # (see the per-record audit_note above), so `compile_sources` produces zero CandidateSpecs --
    # an honest, sparse first epoch (goal.md §12/J-06 acceptance: "a sparse or even empty compiled
    # set is acceptable and is not rescued").
    FOUNDRY_DOCS_DIR.mkdir(parents=True, exist_ok=True)
    FOUNDRY_REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    with _outcome_access_guard() as hits:
        result = fc.compile_sources(
            records, foundry_spec_version=FOUNDRY_SPEC_VERSION, epoch_id="pending", blueprints={}
        )
        if len(result.dispositions) != 11:
            raise AssertionError(
                f"expected exactly 11 source dispositions, got {len(result.dispositions)}"
            )

        generation_inputs = {
            "foundry_spec_version": FOUNDRY_SPEC_VERSION,
            "source_registry_hash": result.source_registry_hash,
            "compiler_hash": fc.compiler_hash(),
            "config_fingerprint": CONFIG.config_fingerprint(),
            "dispositions": dict(sorted(result.dispositions.items())),
        }
        store = _load_existing_manifest_store(EPOCH_MANIFEST_PATH)
        manifest_record = fz.generate_or_verify_manifest(store, generation_inputs)
        epoch_id = manifest_record.epoch_id
        is_replay = "epoch" in _load_existing_manifest_store(EPOCH_MANIFEST_PATH)
        # `candidate_spec_schema_hash` is deliberately equal to `compiler_hash` -- the
        # CandidateSpec dataclass is defined INSIDE foundry_compiler.py and no separate schema
        # module exists this era, so the schema's own identity IS that file's hash; a future era's
        # genuine schema separation would produce a distinct value.
        compiler_hash_value = fc.compiler_hash()

    census = len(hits)
    if census != 0:
        raise AssertionError(f"outcome-access census must be 0, got {census}: {hits}")

    # --- write the four tracked §8.2 artifacts ----------------------------------------------------
    source_dispositions = []
    for record in records:
        canonical = fc._canonical_source_record(record)  # noqa: SLF001 -- same module family
        source_dispositions.append(
            {
                "source_id": record.source_id,
                "disposition": result.dispositions[record.source_id],
                "lineage_refs": [canonical["lineage_id"]] if canonical["lineage_id"] else [],
                "alias_refs": canonical["aliases_lineage_ids"],
            }
        )

    source_registry_payload = {
        "foundry_spec_version": FOUNDRY_SPEC_VERSION,
        "source_registry_hash": result.source_registry_hash,
        "records": [_full_record_view(r, result.dispositions[r.source_id]) for r in records],
    }
    SOURCE_REGISTRY_PATH.write_text(
        json.dumps(source_registry_payload, indent=2, sort_keys=True), encoding="utf-8"
    )

    epoch_manifest_payload = {
        "epoch_id": epoch_id,
        "manifest_hash": manifest_record.manifest_hash,
        "source_registry_hash": result.source_registry_hash,
        "foundry_spec_version": FOUNDRY_SPEC_VERSION,
        "compiler_hash": compiler_hash_value,
        "config_fingerprint": CONFIG.config_fingerprint(),
        "outcome_access_census": census,
        "source_dispositions": source_dispositions,
        "families": [],  # zero compiled candidates this epoch -- every source disposed non-COMPILED
        # internal replay-verification state -- never read by the REST route, only by this script's
        # own `_load_existing_manifest_store` on a future re-run.
        "_inputs_hash": manifest_record.inputs_hash,
        "_generation_inputs": generation_inputs,
    }
    EPOCH_MANIFEST_PATH.write_text(
        json.dumps(epoch_manifest_payload, indent=2, sort_keys=True), encoding="utf-8"
    )

    # --- §8.4 freeze-set: goal-hypothesis-foundry-iter-6 (closes B1/B2/B7's freeze-set half). ------
    # Computed AFTER `source-registry.json`/`epoch-manifest.json` are on disk (both are covered
    # entries -- see `FREEZE_SET_EXTRA_PATHS`'s own module-level comment for why `freeze-record.json`
    # is deliberately NOT one of them), and keyed REPO-RELATIVE (`repo_root=REPO_ROOT`) rather than
    # by this machine's absolute path -- portable across checkouts/worktrees at the same commit.
    freeze_set = fz.generate_freeze_set(
        BACKEND_DIR / "app" / "research", extra_paths=FREEZE_SET_EXTRA_PATHS, repo_root=REPO_ROOT,
    )

    # --- §8.4 freeze record: pins every required science hash. `freeze_commit` is pinned ONCE, on
    # the very first generation, and never recomputed on a later replay/verify run -- a freeze whose
    # own commit identity silently advanced on every re-run would not be a freeze.
    # `_existing_freeze_commit` is `None` only before the first generation this repository has ever
    # produced. goal-hypothesis-foundry-iter-6 (closes B2): this iteration's own regeneration is
    # explicitly run AFTER this iteration's code changes are committed (see NOTES in this module's
    # own docstring), so a freshly-resolved `freeze_commit` here is a real ancestor commit that
    # already contains every pinned science file's bytes -- never a stale, pre-code-commit hash.
    freeze_commit = _existing_freeze_commit(FREEZE_RECORD_PATH) or _git("rev-parse", "HEAD")
    freeze_record = fz.build_freeze_record(
        freeze_commit=freeze_commit,
        manifest_hash=manifest_record.manifest_hash,
        source_registry_hash=result.source_registry_hash,
        spec_hash=_hash_file(SPEC_PATH),
        candidate_spec_schema_hash=compiler_hash_value,
        compiler_hash=compiler_hash_value,
        interpreter_hash=_hash_file(BACKEND_DIR / "app" / "research" / "foundry_interpreter.py"),
        runner_hash=_hash_file(BACKEND_DIR / "app" / "research" / "foundry_runner.py"),
        scout_screen_source_hash=_hash_file(BACKEND_DIR / "app" / "research" / "scout.py"),
        config_fingerprint=CONFIG.config_fingerprint(),
        freeze_set_hash=freeze_set["freeze_set_hash"],
        # goal-hypothesis-foundry-iter-6 (closes B7's freeze-record half). §10.1/goal.md Success
        # Criteria 16: every real Foundry evaluation this era is constitutionally locked to the ONE
        # `historical_exposed_diagnostic` evidence class -- the frozen contract, not a hash.
        era_open_evidence_class_contract=scout.EVIDENCE_CLASS_HISTORICAL_EXPOSED_DIAGNOSTIC,
    )

    FREEZE_SET_PATH.write_text(json.dumps(freeze_set, indent=2, sort_keys=True), encoding="utf-8")

    freeze_record_payload = {
        "freeze_commit": freeze_record.freeze_commit,
        "manifest_hash": freeze_record.manifest_hash,
        "source_registry_hash": freeze_record.source_registry_hash,
        "spec_hash": freeze_record.spec_hash,
        "candidate_spec_schema_hash": freeze_record.candidate_spec_schema_hash,
        "compiler_hash": freeze_record.compiler_hash,
        "interpreter_hash": freeze_record.interpreter_hash,
        "runner_hash": freeze_record.runner_hash,
        "scout_screen_source_hash": freeze_record.scout_screen_source_hash,
        "config_fingerprint": freeze_record.config_fingerprint,
        "freeze_set_hash": freeze_record.freeze_set_hash,
        "era_open_evidence_class_contract": freeze_record.era_open_evidence_class_contract,
    }
    FREEZE_RECORD_PATH.write_text(
        json.dumps(freeze_record_payload, indent=2, sort_keys=True), encoding="utf-8"
    )

    print(
        f"[generate-hypothesis-foundry-real-epoch] {'VERIFIED (replay)' if is_replay else 'GENERATED'}:\n"
        f"  epoch_id={epoch_id}\n"
        f"  manifest_hash={manifest_record.manifest_hash}\n"
        f"  source_registry_hash={result.source_registry_hash}\n"
        f"  freeze_set_hash={freeze_set['freeze_set_hash']}\n"
        f"  freeze_commit={freeze_commit}\n"
        f"  outcome_access_census={census}\n"
        f"  dispositions={dict(sorted(result.dispositions.items()))}\n"
        f"  compiled_candidates={len(result.candidate_specs)}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
