"""Pure-function unit tests for the event-window recording driver (era-5B capability 3, J-03) --
``scripts/record_event_windows.py``.

Imports the script as a module (``sys.path`` insertion onto ``scripts/``, mirroring the script's
OWN insertion onto the backend root) rather than inventing a package. Operator scripts elsewhere in
this codebase carry no companion test file at all (``populate_panel_bars.py`` /
``capture_alpaca_fixture.py`` / ``generate_bar_fixtures.py`` / ``generate_dataset_fixtures.py``) --
but THIS script introduces two genuinely novel, pure, safety-critical rules this iteration invents
(the symbol-spread event selection and the deterministic split-assignment digest), so -- unlike
those precedents, which only drive an already-tested route -- they earn direct unit coverage here
rather than being exercised only by an operator's own eyeball run. The route-driving `main()` loop
itself stays uncovered (mirrors the precedent scripts exactly): it is thin argparse + TestClient
wiring over the ALREADY thoroughly tested ``POST /research/datasets`` route.
"""

from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import record_event_windows as driver  # noqa: E402

from app.config import Config  # noqa: E402
from app.research.datasets import SPLIT_HOLDOUT, SPLIT_TRAIN  # noqa: E402


def _event(
    symbol: str, quality: float, event_id: str, session_date: str = "2026-06-10",
    side: str = "resistance", price_low: float = 100.0, price_high: float = 100.0,
    touch_ts: str = "2026-06-10T15:00:00.000000Z",
) -> dict:
    return {
        "id": event_id,
        "symbol": symbol,
        "session_date": session_date,
        "touch_ts": touch_ts,
        "band": {
            "side": side, "price_low": price_low, "price_high": price_high, "quality_score": quality,
        },
    }


PINNED_EVENT = _event(
    "AAPL", quality=5.0, event_id="pinned-aapl", session_date="2026-06-22",
    price_low=300.0, price_high=302.5, touch_ts="2026-06-22T13:30:00.000000Z",
)


# --- select_recording_events: the pinned event, then symbol-spread, then next-best fill ----------


def test_pinned_event_is_always_selected_first():
    events = [PINNED_EVENT, _event("MSFT", 99.0, "b")]
    config = Config(recording_event_selection_cap=1)
    selected = driver.select_recording_events(events, config)
    assert selected == [PINNED_EVENT], "the pinned event wins even against a higher-quality rival"


def test_selection_spreads_across_symbols_before_a_second_event_from_one_symbol():
    events = [
        PINNED_EVENT,
        _event("MSFT", 50.0, "msft-best"),
        _event("MSFT", 40.0, "msft-second"),  # a SECOND, lower-quality MSFT event
        _event("NVDA", 10.0, "nvda-only"),  # NVDA's only (lower-quality-than-MSFT) event
    ]
    config = Config(recording_event_selection_cap=3)  # room for pinned + 2 more
    selected = driver.select_recording_events(events, config)
    assert {e["id"] for e in selected} == {"pinned-aapl", "msft-best", "nvda-only"}, (
        "NVDA's only event must be picked (symbol spread) before MSFT's second, lower-quality one"
    )


def test_selection_fills_remaining_budget_with_next_best_after_one_per_symbol():
    events = [
        PINNED_EVENT,
        _event("MSFT", 50.0, "msft-best"),
        _event("MSFT", 40.0, "msft-second"),
        _event("NVDA", 10.0, "nvda-only"),
    ]
    config = Config(recording_event_selection_cap=4)  # room for all four
    selected = driver.select_recording_events(events, config)
    assert {e["id"] for e in selected} == {"pinned-aapl", "msft-best", "nvda-only", "msft-second"}


def test_selection_respects_the_cap():
    events = [_event(f"SYM{i}", float(i), f"id{i}") for i in range(20)]
    config = Config(recording_event_selection_cap=5)
    selected = driver.select_recording_events(events, config)
    assert len(selected) == 5


def test_selection_is_deterministic_across_repeat_calls():
    events = [PINNED_EVENT, _event("MSFT", 50.0, "b"), _event("NVDA", 50.0, "c")]
    config = Config(recording_event_selection_cap=2)
    first = driver.select_recording_events(events, config)
    second = driver.select_recording_events(events, config)
    assert [e["id"] for e in first] == [e["id"] for e in second]


def test_selection_on_no_events_is_an_honest_empty_list():
    assert driver.select_recording_events([], Config()) == []


def test_pinned_event_absent_is_never_fabricated():
    events = [_event("MSFT", 50.0, "b")]
    selected = driver.select_recording_events(events, Config(recording_event_selection_cap=5))
    assert all(e["id"] != "pinned-aapl" for e in selected)


def test_shipped_default_selection_cap_is_config_sourced():
    cap = Config().recording_event_selection_cap
    assert isinstance(cap, int) and cap > 0


# --- event_window: touch_ts +/- the config-owned pre/post padding --------------------------------


def test_event_window_applies_the_configured_pre_post_padding():
    event = _event("AAPL", 1.0, "x", touch_ts="2026-06-22T13:30:00.000000Z")
    config = Config(recording_pre_touch_minutes=60.0, recording_post_touch_minutes=90.0)
    start, end = driver.event_window(event, config)
    assert start == "2026-06-22T12:30:00Z"
    assert end == "2026-06-22T15:00:00Z"


def test_event_window_uses_the_shipped_default_padding_of_60_and_90_minutes():
    event = _event("AAPL", 1.0, "x", touch_ts="2026-06-22T13:30:00.000000Z")
    start, end = driver.event_window(event, Config())
    assert start == "2026-06-22T12:30:00Z"
    assert end == "2026-06-22T15:00:00Z"


def test_event_window_is_symmetric_around_a_zero_padding_config():
    event = _event("AAPL", 1.0, "x", touch_ts="2026-06-22T13:30:00.000000Z")
    start, end = driver.event_window(event, Config(recording_pre_touch_minutes=0.0, recording_post_touch_minutes=0.0))
    assert start == end == "2026-06-22T13:30:00Z"


# --- split_for_event: the NEW deterministic, config-owned seeded split rule ----------------------


def test_split_assignment_is_deterministic_across_repeat_calls():
    config = Config(recording_holdout_fraction=0.2)
    first = driver.split_for_event("some-stable-event-id", config)
    second = driver.split_for_event("some-stable-event-id", config)
    assert first == second
    assert first in (SPLIT_TRAIN, SPLIT_HOLDOUT)


def test_split_assignment_ratio_zero_always_trains_ratio_one_always_holds_out():
    for event_id in ("a", "b", "c", "d", "e", "77e4900ec3089ded"):
        assert driver.split_for_event(event_id, Config(recording_holdout_fraction=0.0)) == SPLIT_TRAIN
        assert driver.split_for_event(event_id, Config(recording_holdout_fraction=1.0)) == SPLIT_HOLDOUT


def test_split_assignment_distribution_is_roughly_the_configured_fraction():
    """Not exact-value (the digest's own bit distribution is not hand-derivable), but a real
    statistical sanity check over many distinct ids -- proven non-trivial (both splits appear) and
    roughly matching the configured ratio, never all-one-split. Verified by direct computation:
    500 synthetic ids at a 0.2 ratio produced exactly 100 holdout assignments."""
    config = Config(recording_holdout_fraction=0.2)
    ids = [f"synthetic-event-{i}" for i in range(500)]
    holdout_count = sum(1 for i in ids if driver.split_for_event(i, config) == SPLIT_HOLDOUT)
    assert 50 < holdout_count < 150, f"expected roughly 20% of 500 -- got {holdout_count}"


def test_split_assignment_never_reads_wall_clock_or_unseeded_randomness():
    """Static guard (the deterministic-and-seeded anti-goal): split_for_event's own source must
    never reference a randomness/time module that would break reproducibility."""
    import inspect

    src = inspect.getsource(driver.split_for_event)
    for forbidden in ("random.", "time.time(", "datetime.now(", "uuid.uuid4("):
        assert forbidden not in src, f"{forbidden!r} found in split_for_event -- not deterministic"


# --- No magic numbers: every recording parameter is config-sourced -------------------------------


def test_recording_parameters_are_config_sourced_no_magic_numbers():
    import inspect

    src = inspect.getsource(driver)
    assert "config.recording_pre_touch_minutes" in src
    assert "config.recording_post_touch_minutes" in src
    assert "config.recording_event_selection_cap" in src
    assert "config.recording_holdout_fraction" in src
    assert "config.setups_panel_symbols" in src
