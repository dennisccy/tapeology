"""J-66 copy-discipline lint — the all-surface, automated backstop (iter-25).

The product's defining anti-goal: EVERY research surface speaks in present-tense, descriptive,
thesis-attributed language — NEVER an imperative trade command (buy / sell / enter / exit as a
command, "you should …", price targets, take-profit / stop-loss advice), NEVER a prediction
("price will rise", "about to break"), NEVER a certainty / edge / profitability claim. The three
seeded per-surface checks in ``test_research_api.py`` (stance / checklist / feed-basis) proved one
surface each; THIS module generalises them into a comprehensive lint that walks:

  (a) the ENTIRE ``GET /research/taxonomy`` payload — every label, evidence template, caption,
      register line, and honest-absence string (the single backend owner of research copy); and
  (b) representative SERVED copy — a live verdict + its evidence, the checklist stance evidence +
      nearest-counterevidence, a hint card's evidence + baseline citation, the analytics + studies
      captions, and the studies/analytics measurement framing; and
  (c) the FRONTEND source literals (``apps/frontend/components`` + ``apps/frontend/app``) — UI
      strings that never travel through the taxonomy are still covered (goal.md J-66: "backed by a
      copy-lint test over UI strings").

LEXICON CURATION IS THE HARD PART (the reviewer should diff this against goal.md J-66's own list and
check BOTH failure directions). "buy" / "sell" as factual SIDE descriptors ("aggressive buy ratio",
"Large sell print absorbed", ``buyer_control``) and "entry" / "exit" as the user's OWN journaled
ACTION marks ("Mark entry", "entry-and-exit-marked") are legitimate descriptive tape / journal
language — a naive substring ban is wrong in BOTH directions. The ban therefore targets imperative
CONSTRUCTIONS and forecasts, not bare side / action words:

  * imperative trade COMMANDS — "buy now", "sell here", "you should buy", "go long / short",
    "enter the trade / position", "exit the trade / position", "take profit", "stop loss" (as
    advice), "should buy / sell / enter / exit";
  * predictions — "will rise / fall / break / …", "going to …", "about to …", "price target",
    "target price";
  * certainty / edge / profitability CLAIMS — "guaranteed", "edge", "win rate", "profitable",
    "profit" — but ONLY as a POSITIVE claim: the measurement-framing copy that DENIES them ("not a
    profitability claim, an edge, a win rate, or a forecast") is the honesty mechanism and is CLEARED
    by a sentence-level negation marker (not / never / no / without / n't).

The seeded-violation counter-test (``test_lint_rejects_a_seeded_imperative_phrase`` et al.) proves
the lint CAN fail — a lint that cannot fail proves nothing.
"""

from __future__ import annotations

import pathlib
import re

import pytest
from fastapi.testclient import TestClient

from app.config import CONFIG
from app.main import app, manager
from app.research import taxonomy as tax
from app.research.routes import ResearchRegistry, set_registry
from app.research.store import JournalStore


# --- The curated lexicon -------------------------------------------------------------------------
# Each entry is (compiled regex, human label). Word boundaries + multi-word constructions keep the
# ban off legitimate side / action descriptors. Matching is case-insensitive over the lowercased text.

# 1) IMPERATIVE TRADE COMMANDS — unconditional bans (no legitimate descriptive form).
_IMPERATIVE_PATTERNS = [
    (re.compile(r"\b(buy|sell)\s+(now|here|it|this|them|more)\b"), "imperative buy/sell command"),
    (re.compile(r"\byou\s+should\b"), "advice ('you should')"),
    (re.compile(r"\bshould\s+(buy|sell|enter|exit|go|take|cut|hold|add|trim|short|long)\b"),
     "advice ('should <action>')"),
    (re.compile(r"\bgo\s+(long|short)\b"), "imperative 'go long/short'"),
    # "enter / exit" ONLY when paired with a trade-position object (never a ticker / date / field).
    (re.compile(r"\b(enter|exit)\s+(the\s+)?(trade|position|market|long|short|here|now)\b"),
     "imperative enter/exit a position"),
    (re.compile(r"\btake[\s-]?profit\b"), "take-profit advice"),
    (re.compile(r"\bstop[\s-]?loss\b"), "stop-loss advice"),
    (re.compile(r"\bcut\s+(your\s+)?(loss|losses|position)\b"), "imperative 'cut your position'"),
    (re.compile(r"\badd\s+to\s+(your\s+)?position\b"), "imperative 'add to position'"),
]

# 2) PREDICTION / FORECAST — unconditional bans (a verdict describes NOW, never a forecast).
_PREDICTION_PATTERNS = [
    (re.compile(r"\bwill\s+(rise|fall|go|move|reach|break|continue|hit|drop|climb|reverse|"
                r"bounce|rally|tank|spike|run|head|push|pull|sell|buy)\b"),
     "forecast ('will <move>')"),
    (re.compile(r"\bgoing\s+to\s+(rise|fall|go|move|reach|break|hit|drop|climb|reverse|run)\b"),
     "forecast ('going to <move>')"),
    (re.compile(r"\babout\s+to\b"), "forecast ('about to')"),
    (re.compile(r"\b(price|profit)\s+target\b"), "price target"),
    (re.compile(r"\btarget\s+price\b"), "target price"),
]

# 3) CERTAINTY / EDGE / PROFITABILITY CLAIMS — banned ONLY as a POSITIVE claim. A sentence-level
# negation marker clears them (the measurement-framing honesty copy leads with "not …" / "never …").
_CLAIM_PATTERNS = [
    (re.compile(r"\bguarantee[ds]?\b"), "certainty claim ('guaranteed')"),
    (re.compile(r"\bsure\s+thing\b"), "certainty claim ('sure thing')"),
    (re.compile(r"\ban?\s+edge\b|\bhas\s+edge\b|\bour\s+edge\b|\byour\s+edge\b"), "edge claim"),
    (re.compile(r"\bwin[\s-]?rate\b"), "win-rate-as-edge claim"),
    (re.compile(r"\bprofitabl\w*\b"), "profitability claim"),
    (re.compile(r"\bprofits?\b"), "profit claim"),
    (re.compile(r"\bbeat\s+the\s+market\b"), "edge claim ('beat the market')"),
]

# Sentence-level negation markers that clear a CLAIM word (the honest "this is NOT a profit/edge
# claim" framing). Checked within the SENTENCE the claim word sits in.
_NEGATION = re.compile(r"\b(not|never|no|without|n't|isn't|aren't|nor)\b")


def _sentences(text: str) -> list[str]:
    """Split into rough sentences for the sentence-level negation check (claim words only)."""
    return re.split(r"(?<=[.!?;:])\s+|\n+", text)


def find_violations(text: str) -> list[str]:
    """Return the list of human-readable violation labels for one string (empty == clean).

    Imperative + prediction patterns are unconditional. Claim patterns fire ONLY when the sentence
    they appear in carries NO negation marker — so the measurement-framing copy that DENIES an
    edge / profit / win-rate / forecast stays clean (it is the honesty mechanism), while a bare
    positive claim ("this setup has an edge") is rejected."""
    if not text:
        return []
    low = text.lower()
    found: list[str] = []
    for pattern, label in _IMPERATIVE_PATTERNS + _PREDICTION_PATTERNS:
        if pattern.search(low):
            found.append(label)
    # Claim words: clear them if the containing sentence is negated.
    for sentence in _sentences(low):
        negated = bool(_NEGATION.search(sentence))
        if negated:
            continue
        for pattern, label in _CLAIM_PATTERNS:
            if pattern.search(sentence):
                found.append(label)
    return found


# --- Walk every string in an arbitrary JSON-ish structure ----------------------------------------

def _walk_strings(node, path="$"):
    """Yield ``(json_path, string_value)`` for every string leaf in a nested dict/list structure."""
    if isinstance(node, str):
        yield path, node
    elif isinstance(node, dict):
        for k, v in node.items():
            yield from _walk_strings(v, f"{path}.{k}")
    elif isinstance(node, (list, tuple)):
        for i, v in enumerate(node):
            yield from _walk_strings(v, f"{path}[{i}]")


@pytest.fixture
def client(tmp_path):
    store = JournalStore(str(tmp_path / "journal.db"), CONFIG)
    registry = ResearchRegistry(store, CONFIG)
    set_registry(registry)
    manager.set_on_engine_created(registry.on_engine_created)
    with TestClient(app) as c:
        yield c
    for ticker in list(manager._engines.keys()):
        manager.stop(ticker)
    manager.set_on_engine_created(None)
    set_registry(None)
    store.close()


# --- (a) the ENTIRE taxonomy payload -------------------------------------------------------------

def test_lint_full_taxonomy_payload_is_clean(client):
    payload = client.get("/research/taxonomy").json()
    offenders: list[str] = []
    for json_path, value in _walk_strings(payload):
        violations = find_violations(value)
        if violations:
            offenders.append(f"{json_path}: {violations} :: {value!r}")
    assert not offenders, (
        "J-66 copy-discipline lint found imperative/predictive/claim language in the SERVED taxonomy "
        "payload (the single backend owner of research copy):\n" + "\n".join(offenders)
    )


# --- (b) representative SERVED copy (verdict + evidence, stance/checklist, hint, captions) --------

def _representative_served_copy() -> dict:
    """Build a representative sample of every SERVED dynamic copy string from the same backend owners
    the runtime uses (the projection helpers), so the lint covers copy the static taxonomy walk does
    not — a live verdict + evidence projection, the checklist stance evidence + counterevidence, a
    hint card's evidence + baseline citation, and the analytics/studies captions."""
    sample: dict = {}
    # A live verdict + evidence projection for EACH setup × direction (the confirming / weakening /
    # rejecting / invalidated evidence the strip renders verbatim — built from the same templates).
    sample["verdict_weakening"] = tax.VERDICTS  # the verdict labels themselves
    # The checklist aggregate-stance evidence for all four stances + the nearest-counterevidence line.
    sample["checklist_stance_evidence"] = {
        s: tax.checklist_stance_evidence(s, 6, 8)
        for s in ("conditions_met", "conditions_not_met", "tape_against", "no_fresh_tape")
    }
    sample["checklist_counterevidence"] = {
        "met": tax.checklist_nearest_counterevidence("Spread within stability", "12.0 bps", met=True),
        "unmet": tax.checklist_nearest_counterevidence("Trade speed at floor", "0.40 t/s", met=False),
    }
    # The management-stance pending evidence + the absence copies (the J-54 honest case).
    sample["stance_pending_evidence"] = tax.STANCE_PENDING_EVIDENCE
    # A hint card record — evidence for each pattern + a baseline citation + the unvalidated string.
    sample["hint_evidence"] = {
        pid: tax.hint_evidence(pid, 45.0) for pid in tax.HINT_PATTERNS
    }
    sample["hint_baseline_citation"] = tax.hint_baseline_citation(40, 18, 12, 10, 30)
    sample["hint_baseline_unvalidated"] = tax.HINT_BASELINE_UNVALIDATED
    # The risk-flag measured-evidence sentences (the strip's amber advisory chips).
    sample["risk_flag_evidence"] = {
        "chasing": tax.chasing_entry_evidence(0.0044, 0.0040, "buy"),
        "too_tight": tax.invalidation_too_tight_evidence(0.04, 0.02, 2.0),
        "wide_spread": tax.wide_spread_illiquid_evidence(45.0, 30.0, "bps"),
        "low_speed": tax.low_trade_speed_evidence(0.20, 0.50),
        "against_tape": tax.against_expected_tape_evidence("seller_control", ["bid_absorption"]),
        "before_warmup": tax.before_warmup_evidence(12, 40),
    }
    # The analytics + studies measurement-framing + captions (the most edge-claim-prone surfaces).
    sample["analytics_copy"] = tax.ANALYTICS_COPY
    sample["study_copy"] = tax.STUDY_COPY
    sample["study_status_absence"] = tax.STUDY_STATUS_ABSENCE_COPY
    sample["excursion_not_applicable"] = tax.EXCURSION_NOT_APPLICABLE_COPY
    sample["excursion_not_tracked"] = tax.EXCURSION_NOT_TRACKED_COPY
    sample["sound_cue_copy"] = tax.SOUND_CUE_COPY
    return sample


def test_lint_representative_served_copy_is_clean():
    sample = _representative_served_copy()
    offenders: list[str] = []
    for json_path, value in _walk_strings(sample):
        violations = find_violations(value)
        if violations:
            offenders.append(f"{json_path}: {violations} :: {value!r}")
    assert not offenders, (
        "J-66 copy-discipline lint found imperative/predictive/claim language in representative SERVED "
        "dynamic copy (verdict evidence, stance/checklist, hint cards, analytics/studies captions):\n"
        + "\n".join(offenders)
    )


# --- (c) the FRONTEND source literals ------------------------------------------------------------

_FRONTEND_ROOT = pathlib.Path(__file__).resolve().parents[2] / "frontend"
# JSX text content + quoted string literals. We extract candidate user-facing strings and lint them.
# The lexicon is multi-word / boundary-anchored, so it never fires on code identifiers ("entry",
# "exit") — only on imperative constructions / forecasts a real UI string would carry.
_STRING_LITERAL = re.compile(r"""(["'`])((?:\\.|(?!\1).)*?)\1""", re.DOTALL)
_JSX_TEXT = re.compile(r">([^<>{}]+)<")
# Comments are developer notes, NOT user-facing copy — they often paraphrase the very anti-goal
# vocabulary ("never \"profit/loss\"", "no buy/sell wording") while DESCRIBING the discipline, so
# they MUST be stripped before extracting candidate strings or the lint false-positives on its own
# documentation. JSX comments ``{/* … */}``, block comments ``/* … */``, and ``//`` line comments.
_JSX_COMMENT = re.compile(r"\{/\*.*?\*/\}", re.DOTALL)
_BLOCK_COMMENT = re.compile(r"/\*.*?\*/", re.DOTALL)
_LINE_COMMENT = re.compile(r"//[^\n]*")


def _strip_comments(source: str) -> str:
    source = _JSX_COMMENT.sub(" ", source)
    source = _BLOCK_COMMENT.sub(" ", source)
    source = _LINE_COMMENT.sub(" ", source)
    return source


def _frontend_candidate_strings(source: str):
    """Yield candidate user-facing strings from a .tsx/.ts source: quoted string literals + JSX text.
    Comments (developer notes that paraphrase the anti-goal vocabulary) and import lines (module paths)
    are skipped — only real user-facing copy is linted."""
    source = _strip_comments(source)
    for line in source.splitlines():
        stripped = line.strip()
        if stripped.startswith("import ") or stripped.startswith("from "):
            continue
        for m in _STRING_LITERAL.finditer(line):
            yield m.group(2)
    for m in _JSX_TEXT.finditer(source):
        text = m.group(1).strip()
        if text:
            yield text


def test_lint_frontend_source_literals_are_clean():
    files = sorted(_FRONTEND_ROOT.glob("components/**/*.tsx")) + \
        sorted(_FRONTEND_ROOT.glob("app/**/*.tsx")) + \
        sorted(_FRONTEND_ROOT.glob("app/**/*.ts"))
    assert files, "no frontend source files found — the frontend-scan leg cannot be vacuous"
    offenders: list[str] = []
    for path in files:
        source = path.read_text()
        for candidate in _frontend_candidate_strings(source):
            violations = find_violations(candidate)
            if violations:
                rel = path.relative_to(_FRONTEND_ROOT)
                offenders.append(f"{rel}: {violations} :: {candidate!r}")
    assert not offenders, (
        "J-66 copy-discipline lint found imperative/predictive/claim language in FRONTEND source "
        "string literals (UI copy that never travels through the taxonomy):\n" + "\n".join(offenders)
    )


# --- the lint CAN fail (the seeded-violation counter-tests) --------------------------------------
# A lint that cannot fail proves nothing. Each banned category is seeded and asserted rejected; and a
# legitimate descriptive side / action label is asserted CLEAN (the false-positive direction).

@pytest.mark.parametrize(
    "phrase",
    [
        "Buy now while the tape is hot.",
        "You should sell here.",
        "Go long on this setup.",
        "Enter the trade at the level.",
        "Exit the position before the close.",
        "Set your take-profit at 102.",
        "Move your stop-loss up.",
        "Price will rise to 105.",
        "The tape is about to break out.",
        "Our price target is 110.",
        "This setup is guaranteed to work.",
        "This setup has an edge over the market.",
        "Our win-rate is 70%.",
        "This strategy is profitable.",
    ],
)
def test_lint_rejects_a_seeded_banned_phrase(phrase):
    # The counter-test: each seeded imperative / prediction / certainty / edge / profit phrase MUST be
    # flagged — proving the lint actually fires (an empty result here would be a vacuous lint).
    assert find_violations(phrase), f"lint failed to flag a seeded banned phrase: {phrase!r}"


@pytest.mark.parametrize(
    "phrase",
    [
        # Factual SIDE descriptors — the tape reader's legitimate vocabulary (must NOT false-positive).
        "Aggressive buy ratio reads high.",
        "Large sell print absorbed at the bid.",
        "The tape reads buyer_control with positive buy_price_impact.",
        "Seller aggression increasing.",
        # The user's OWN journaled ACTION marks — legitimate journal language.
        "Mark entry",
        "Mark exit",
        "Entry-and-exit-marked theses only, kept apart from the confirmation-anchored figures.",
        "Record your entry; record your exit.",
        # UI field instructions — "Enter a ticker" is typing into a field, never a trade command.
        "Enter a ticker symbol to watch.",
        "Enter a valid date as dd-MM-yyyy.",
        # The measurement-framing honesty copy — DENIES edge / profit / win-rate / forecast (negated).
        "These are journaled measurements — not a profitability claim, an edge, a win rate, or a forecast.",
        "Realized move in R units, never currency, never a profit/loss claim.",
        # A descriptive present-tense verdict — control + impact NOW, not a forecast.
        "Control on your side is sustained — buyers keep pressing price up; the tape confirms your thesis.",
        # The sound-cue description (off by default, transition-only) — descriptive, never imperative.
        "Plays a brief sound the moment the published verdict or management stance changes. Off by default.",
    ],
)
def test_lint_does_not_false_positive_on_legitimate_descriptive_copy(phrase):
    # The OTHER failure direction (the reviewer must check both): legitimate descriptive tape / journal /
    # UI-field / measurement-framing language MUST stay clean — a naive substring ban is wrong here.
    assert not find_violations(phrase), (
        f"lint FALSE-POSITIVED on legitimate descriptive copy: {phrase!r} -> {find_violations(phrase)}"
    )
