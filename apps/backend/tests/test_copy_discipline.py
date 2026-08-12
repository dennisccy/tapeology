"""J-66 copy-discipline lint — the all-surface, automated backstop (iter-25).

The product's defining anti-goal: EVERY research surface speaks in present-tense, descriptive,
thesis-attributed language — NEVER an imperative trade command (buy / sell / enter / exit as a
command, "you should …", price targets, take-profit / stop-loss advice), NEVER a prediction
("price will rise", "about to break"), NEVER a certainty / edge / profitability claim. The
feed-basis seeded check in ``test_research_api.py`` proved one surface; THIS module generalises it
into a comprehensive lint that walks:

  (a) the ENTIRE ``GET /research/taxonomy`` payload — every label, register line, and disclosure
      string (the single backend owner of research copy); and
  (b) the FRONTEND source literals (``apps/frontend/components`` + ``apps/frontend/app``) — UI
      strings that never travel through the taxonomy are still covered (goal.md J-66: "backed by a
      copy-lint test over UI strings").

era-5D J-01 ("The Clean Slate" demolition interlude, I-8 UPDATE row): a THIRD leg used to walk a
representative sample of served dynamic copy built from taxonomy functions that only the deleted
verdict/stance/checklist/hint/risk-flag/analytics/studies surfaces ever called. Every one of those
functions/constants is gone (I-2 taxonomy SLIM row); there is no surviving "representative served
copy" distinct from the (a) taxonomy-payload walk to sample it from (the feed-basis strings — the
one dynamic-ish copy left — are already fully covered by (a)), so that leg is DROPPED rather than
repointed at unrelated kept modules (no new lint surface was asked for this iteration). The rail-2
lint RULES themselves (the curated lexicon, the negation-clearing logic) are untouched.

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
from app.main import app
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
    with TestClient(app) as c:
        yield c
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


# --- (b) the FRONTEND source literals ------------------------------------------------------------
#
# The scan roots below cover `components/`, `app/` AND `lib/`. `lib/` was added when
# `lib/playbookShapes.ts` became the first module there to carry genuinely user-facing copy (a
# chart caption, legend labels, and the sentence shown when a record predates its shape anchors) --
# until then every user-visible string lived in a component or a page, and the lint would simply
# never have seen these. A pure helper module is exactly where an unlinted string is easiest to
# miss, so the roots follow the copy rather than the file type.

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
        sorted(_FRONTEND_ROOT.glob("components/**/*.ts")) + \
        sorted(_FRONTEND_ROOT.glob("app/**/*.tsx")) + \
        sorted(_FRONTEND_ROOT.glob("app/**/*.ts")) + \
        sorted(_FRONTEND_ROOT.glob("lib/**/*.ts"))
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
        "Enter a valid date as yyyy-MM-dd.",
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
