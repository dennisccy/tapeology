"""Research API: ``GET /research/taxonomy`` — the feed-basis display copy (capability 28, J-67).

era-5D J-01 ("The Clean Slate" demolition interlude, I-8 UPDATE row): every thesis-declaration
test that used to live here (``POST /research/thesis``'s 404/409/422 validation matrix, "nothing
persisted on rejection", REST==WS thesis-projection verbatim, the stance/checklist/mistake-tag/
sound-cue/setup/direction/verdict taxonomy canaries, the declare-atomicity fault-injection test,
and the risk-flag tests) was dropped along with the deleted ``POST /research/thesis`` route and
the slimmed taxonomy payload (I-1, I-2 taxonomy SLIM row). The feed-basis surface check survives —
it is the one taxonomy family ``FeedBasisBadge.tsx`` still reads, and the route itself needs no
registry/store dependency any more (``taxonomy_payload()`` takes no arguments), so this file's
fixture is a plain temp-path-injected client, with no WatchManager engine-created wiring."""

import pytest
from fastapi.testclient import TestClient

from app.config import CONFIG
from app.main import app
from app.research.routes import ResearchRegistry, set_registry
from app.research.store import JournalStore


@pytest.fixture
def client(tmp_path):
    # Inject a temp-path store + registry BEFORE the app starts, so the lifespan leaves it in place
    # (skips building the default file store) — keeps the suite hermetic even though this route
    # itself no longer reads the registry.
    store = JournalStore(str(tmp_path / "journal.db"), CONFIG)
    registry = ResearchRegistry(store, CONFIG)
    set_registry(registry)
    with TestClient(app) as c:
        yield c
    set_registry(None)
    store.close()


def test_taxonomy_serves_feed_basis_copy_canary(client):
    # The feed-basis display copy (capability 28 honesty stamps, J-67; data-contract row 24 additive)
    # is backend-owned — served by GET /research/taxonomy. ALSO iter-24's code-identity canary: the
    # presence of `feed_basis` here proves the NEW server code is live before any browser capture. The
    # frontend hardcodes NONE of it (per-feed badge labels + the live IEX-vs-SIP disclosure line).
    payload = client.get("/research/taxonomy").json()
    assert "feed_basis" in payload
    feed_basis = payload["feed_basis"]
    labels = {f["id"]: f["name"] for f in feed_basis["feeds"]}
    # Era-5 J-05: "yahoo" -> "Yahoo Finance" is the additive entry the /structure fetch-control's
    # provenance badge reads (the frontend hardcodes no "Yahoo Finance" string anywhere).
    assert set(labels.keys()) == {"sim", "iex", "sip", "yahoo"}
    assert labels["yahoo"] == "Yahoo Finance"
    for name in labels.values():
        assert name  # every feed carries a non-empty display label
    # The live IEX-vs-SIP disclosure line is verbatim from goal.md (J-67 acceptance).
    assert feed_basis["live_disclosure"] == (
        "live verdicts read the single-venue IEX feed; historical replay and studies use SIP "
        "— spreads and prints differ"
    )
    # Copy discipline (J-66): no imperative / predictive words in any feed-basis string.
    blob = " ".join(list(labels.values()) + [feed_basis["live_disclosure"]]).lower()
    for word in (" buy ", " sell ", " enter ", " exit ", "should ", "will ", "predict", "target"):
        assert word not in f" {blob} ", f"forbidden word {word!r} in feed-basis copy"


def test_taxonomy_payload_is_exactly_feed_basis(client):
    # era-5D J-01: the slimmed taxonomy payload's ONLY key is feed_basis (I-2 taxonomy SLIM row) —
    # every deleted label family (setups/directions/verdicts/statuses/management_stances/
    # checklist_*/risk_flags/mistake_tags/excursions/analytics/studies/hints/sound_cue) is gone.
    payload = client.get("/research/taxonomy").json()
    assert set(payload.keys()) == {"feed_basis"}
