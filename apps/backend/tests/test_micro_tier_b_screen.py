"""Tier-B resolution protocol — §7.2.1 (r10, owner ruling 2026-08-21).

Every branch here is fixture-driven and hermetic: the owner ruling requires that every source parser
and every FAIL-CLOSED branch be verified BEFORE the screen runs, because the screen runs exactly
once (§7.2.1 (j)) and a bug would burn that single shot.
"""

from __future__ import annotations

import hashlib

import pytest

from app.research import micro_tier_b_screen as tb

# --- fixtures: byte-exact miniatures of the real directory files ----------------------------------

_NASDAQ = (
    b"Symbol|Security Name|Market Category|Test Issue|Financial Status|Round Lot Size|ETF|NextShares\n"
    b"AAPL|Apple Inc. - Common Stock|Q|N|N|100|N|N\n"
    b"DKNG|DraftKings Inc. Class A Common Stock|Q|N|N|100|N|N\n"
    b"AAAP|Pacer Barings CLO Market Flex ETF|G|N|N|100|Y|N\n"
    b"TSTNG|Test Issue Inc. - Common Stock|Q|Y|N|100|N|N\n"
    b"WRNTW|Someco Inc. - Warrant|Q|N|N|100|N|N\n"
    b"UNITU|Someco Inc. - Unit|Q|N|N|100|N|N\n"
    b"PFDPR|Someco Inc. - 7% Series A Preferred Stock|Q|N|N|100|N|N\n"
    b"ADRCO|Foreign Co. - American Depositary Shares|Q|N|N|100|N|N\n"
    b"WEIRD|Someco Inc. - Something Unclassifiable|Q|N|N|100|N|N\n"
    b"File Creation Time: 0821202607:00|||||||\n"
)

_OTHER = (
    b"ACT Symbol|Security Name|Exchange|CQS Symbol|ETF|Round Lot Size|Test Issue|NASDAQ Symbol\n"
    b"PG|Procter & Gamble Company (The) Common Stock|N|PG|N|100|N|PG\n"
    b"ETSY|Etsy, Inc. Common Stock|N|ETSY|N|100|N|ETSY\n"
    b"ARCAF|Some Arca Company Common Stock|P|ARCAF|N|100|N|ARCAF\n"
    b"RIGHT|Someco Inc. Rights|A|RIGHT|N|100|N|RIGHT\n"
    b"File Creation Time: 0821202607:00||||||\n"
)


def test_the_parsers_read_the_real_column_layout():
    nasdaq = tb.parse_nasdaqlisted(_NASDAQ)
    other = tb.parse_otherlisted(_OTHER)
    aapl = next(r for r in nasdaq if r["ticker"] == "AAPL")
    assert aapl["exchange_code"] == "Q" and aapl["exchange"] == "Nasdaq"
    assert aapl["etf"] == "N" and aapl["test_issue"] == "N"
    pg = next(r for r in other if r["ticker"] == "PG")
    assert pg["exchange_code"] == "N" and pg["exchange"] == "NYSE"
    # the File Creation Time sentinel is never a candidate row
    assert not any(r["ticker"].startswith("FILE CREATION") for r in nasdaq + other)


def test_a_changed_column_order_is_refused_rather_than_guessed():
    """A silently re-ordered directory would make every flag read the wrong column, so the parser
    refuses outright instead of producing a plausible-looking universe."""
    bad = _NASDAQ.replace(b"Symbol|Security Name|Market Category", b"Security Name|Symbol|Market Category", 1)
    with pytest.raises(ValueError, match="unexpected directory header"):
        tb.parse_nasdaqlisted(bad)


def test_the_embedded_nasdaq_file_creation_time_is_recovered():
    assert tb.embedded_file_creation_time(_NASDAQ) == "0821202607:00"
    assert tb.embedded_file_creation_time(_OTHER) == "0821202607:00"
    with pytest.raises(ValueError, match="no 'File Creation Time:'"):
        tb.embedded_file_creation_time(b"Symbol|Security Name|Market Category|Test Issue|"
                                       b"Financial Status|Round Lot Size|ETF|NextShares\n")


@pytest.mark.parametrize(
    "name,flags,expected",
    [
        ("Apple Inc. - Common Stock", {}, None),
        ("DraftKings Inc. Class A Common Stock", {}, None),
        ("Someco Inc. - Warrant", {}, "warrant"),
        ("Someco Inc. Rights", {}, "right"),
        ("Someco Inc. - Unit", {}, "unit"),
        ("Someco Inc. - 7% Series A Preferred Stock", {}, "preferred"),
        ("Someco Inc. - Depositary Shares", {}, "preferred"),
        ("Foreign Co. - American Depositary Shares", {}, "adr"),
        ("Someco 5.5% Notes due 2030", {}, "note_or_etn"),
        ("Some Index Fund", {}, "fund"),
        ("Someco Inc. - Something Unclassifiable", {}, "unresolved_security_type"),
        ("Apple Inc. - Common Stock", {"test_issue": "Y"}, "test_issue"),
        ("Apple Inc. - Common Stock", {"etf": "Y"}, "etf_flag"),
    ],
)
def test_every_mechanical_exclusion_branch_fires_exactly_as_frozen(name, flags, expected):
    row = {"ticker": "X", "security_name": name, "exchange_code": "Q",
           "test_issue": "N", "etf": "N", **flags}
    assert tb.mechanical_exclusion_reason(row) == expected


def test_an_ambiguous_security_type_is_excluded_not_silently_admitted():
    """§7.2.1 (b) fail-closed branch, stated explicitly by the owner: 'If security type is
    ambiguous, do not silently guess it into the universe.'"""
    row = {"ticker": "WEIRD", "security_name": "Someco Inc. - Something Unclassifiable",
           "exchange_code": "Q", "test_issue": "N", "etf": "N"}
    assert tb.mechanical_exclusion_reason(row) == "unresolved_security_type"


def test_a_non_primary_venue_is_excluded_before_the_six_factor_screen():
    """§7.2.1 (c): NYSE Arca / Cboe / IEX are not primary common-equity listing venues here."""
    row = {"ticker": "X", "security_name": "Someco Inc. Common Stock", "exchange_code": "P",
           "test_issue": "N", "etf": "N"}
    assert tb.mechanical_exclusion_reason(row) == "non_primary_listing_venue"


def test_a_look_alike_company_name_is_not_mistaken_for_an_instrument_type():
    """Whole-word matching, not bare substring: 'Unitil' is not a unit and 'Preferred Apartment
    Communities' is not a preferred share. A substring parser would silently shrink the universe."""
    for name in ("Unitil Corporation Common Stock",
                 "Preferred Apartment Communities Inc Common Stock"):
        row = {"ticker": "X", "security_name": name, "exchange_code": "N",
               "test_issue": "N", "etf": "N"}
        assert tb.mechanical_exclusion_reason(row) is None, name


def test_the_candidate_universe_records_every_exclusion_with_its_reason():
    """§7.2.1 (j): no hidden manual exclusions -- every excluded row keeps a frozen reason."""
    uni = tb.build_candidate_universe(_NASDAQ, _OTHER)
    survivors = {c["ticker"] for c in uni["candidates"]}
    assert survivors == {"AAPL", "DKNG", "PG", "ETSY"}
    reasons = {e["ticker"]: e["exclusion_reason"] for e in uni["excluded"]}
    assert reasons == {
        "AAAP": "etf_flag", "TSTNG": "test_issue", "WRNTW": "warrant", "UNITU": "unit",
        "PFDPR": "preferred", "ADRCO": "adr", "WEIRD": "unresolved_security_type",
        "ARCAF": "non_primary_listing_venue", "RIGHT": "right",
    }
    # every input row is accounted for -- nothing vanishes silently
    assert len(uni["candidates"]) + len(uni["excluded"]) + len(uni["duplicate_rows"]) == uni["total_rows"]


def test_the_membership_hash_identifies_the_set_not_its_enumeration():
    assert tb.membership_hash(["AAPL", "PG"]) == tb.membership_hash(["pg", " aapl "])
    assert tb.membership_hash(["AAPL", "PG"]) != tb.membership_hash(["AAPL", "PG", "MSFT"])


def test_the_replacement_rank_key_is_the_frozen_salted_hash():
    """The salt is frozen in source; a silent change would re-order every future resolution."""
    assert tb.TIER_B_R10_SALT == "rapid-microscope-tier-b-r10:"
    expected = hashlib.sha256(b"rapid-microscope-tier-b-r10:SOFI").hexdigest()
    assert tb.replacement_rank_key("sofi ") == expected


def test_the_parser_version_hash_changes_when_a_rule_changes(monkeypatch):
    """§7.2.1 (a): a silent edit to an exclusion regex must not masquerade as the same parser."""
    before = tb.parser_version_hash()
    monkeypatch.setattr(tb, "_EXCLUSION_PATTERNS", tb._EXCLUSION_PATTERNS + (("x", r"\bzzz\b"),))
    assert tb.parser_version_hash() != before


# --- (h) deterministic resolution -----------------------------------------------------------------


def test_passing_seeds_are_retained_in_their_documented_order_not_alphabetically():
    out = tb.resolve_tier_b(passing_seeds=["RKLB", "DKNG", "SOFI"], passing_replacements=[])
    assert out["resolved"] == ["DKNG", "SOFI", "RKLB"]  # PROVISIONAL_SEEDS order, not sorted()
    assert out["replacements_taken"] == []


def test_replacements_fill_only_the_missing_slots_and_rank_by_the_frozen_hash():
    survivors = ["ZZZZ", "MMMM", "AAAA", "QQQQ"]
    out = tb.resolve_tier_b(passing_seeds=["ETSY"], passing_replacements=survivors)
    assert out["resolved"][0] == "ETSY"
    assert len(out["resolved"]) == 3
    # exactly the two lowest-ranked survivors, by the salted hash -- NOT alphabetical
    expected = sorted(survivors, key=tb.replacement_rank_key)[:2]
    assert out["replacements_taken"] == expected
    ranked = [r["ticker"] for r in out["replacement_ranking"]]
    assert ranked == sorted(survivors, key=tb.replacement_rank_key)


def test_the_ordering_is_not_alphabetical_which_the_owner_explicitly_rejected():
    """Guards the intent, not just the mechanism: if the hash ordering ever silently degraded to a
    lexical sort, this fixture would stop distinguishing them."""
    survivors = ["AAAA", "BBBB", "CCCC", "DDDD", "EEEE", "FFFF"]
    hashed = sorted(survivors, key=tb.replacement_rank_key)
    assert hashed != sorted(survivors), "the frozen ranking degenerated to ticker-alphabetical"


def test_no_seed_is_grandfathered_when_it_does_not_pass():
    """The five provisional names are SEEDS. A seed absent from `passing_seeds` never appears."""
    out = tb.resolve_tier_b(passing_seeds=[], passing_replacements=["AAAA", "BBBB", "CCCC"])
    for seed in tb.PROVISIONAL_SEEDS:
        assert seed not in out["resolved"]


def test_fewer_than_three_eligible_names_is_a_hard_stop_never_a_loosened_criterion():
    """§7.2.1 (h)'s owner-mandated STOP."""
    with pytest.raises(tb.TierBResolutionImpossible, match="STOP and escalate to the owner"):
        tb.resolve_tier_b(passing_seeds=["DKNG"], passing_replacements=["AAAA"])


def test_exactly_three_are_taken_even_when_many_survive():
    survivors = [f"S{i:03d}" for i in range(50)]
    out = tb.resolve_tier_b(passing_seeds=[], passing_replacements=survivors)
    assert len(out["resolved"]) == 3


def test_a_replacement_already_chosen_as_a_seed_is_never_double_counted():
    out = tb.resolve_tier_b(passing_seeds=["DKNG"], passing_replacements=["DKNG", "AAAA", "BBBB"])
    assert out["resolved"].count("DKNG") == 1
    assert len(out["resolved"]) == 3


# === the six frozen criteria — every branch, especially every FAIL-CLOSED branch ===================


def test_the_frozen_thresholds_are_exactly_card_5_2s():
    """If any of these drifts, a criterion was widened -- the one thing the owner ruling forbids."""
    assert (tb.PRICE_MIN_USD, tb.PRICE_MAX_USD) == (15.0, 100.0)
    assert (tb.MARKET_CAP_MIN_USD, tb.MARKET_CAP_MAX_USD) == (2_000_000_000.0, 20_000_000_000.0)
    assert tb.ADV_MIN_SHARES == 3_000_000.0
    assert tb.SPREAD_MAX_BPS == 8.0
    assert (tb.ADV_SESSIONS, tb.SPREAD_SESSIONS) == (30, 5)


@pytest.mark.parametrize("close,status", [
    (15.0, tb.STATUS_PASS), (100.0, tb.STATUS_PASS), (57.3, tb.STATUS_PASS),
    (14.99, tb.STATUS_FAIL), (100.01, tb.STATUS_FAIL),
])
def test_price_boundaries_are_inclusive_exactly_as_written(close, status):
    assert tb.evaluate_price(close)["status"] == status


def test_a_missing_close_is_unresolved_not_a_fail_and_never_a_pass():
    r = tb.evaluate_price(None)
    assert r["status"] == tb.STATUS_UNRESOLVED and r["reason"] == "no_close_available"


def test_adv_is_thirty_completed_sessions_not_calendar_days():
    r = tb.evaluate_adv([4_000_000.0] * 30, sessions=[f"d{i}" for i in range(30)])
    assert r["status"] == tb.STATUS_PASS and r["adv"] == 4_000_000.0
    assert len(r["sessions"]) == 30


def test_fewer_than_thirty_sessions_is_unresolved_not_a_short_window_mean():
    r = tb.evaluate_adv([9_000_000.0] * 29)
    assert r["status"] == tb.STATUS_UNRESOLVED
    assert r["reason"] == "insufficient_sessions_29_of_30" and r["adv"] is None


def test_adv_uses_the_most_recent_thirty_when_more_are_supplied():
    volumes = [100.0] * 40 + [5_000_000.0] * 30   # older window would fail the floor
    r = tb.evaluate_adv(volumes)
    assert r["status"] == tb.STATUS_PASS and r["adv"] == 5_000_000.0


def test_adv_boundary_is_the_written_floor():
    assert tb.evaluate_adv([3_000_000.0] * 30)["status"] == tb.STATUS_PASS
    assert tb.evaluate_adv([2_999_999.0] * 30)["status"] == tb.STATUS_FAIL


def test_market_cap_is_shares_times_close_with_full_provenance():
    r = tb.evaluate_market_cap(
        200_000_000, 50.0, cik="0000320193", accession="0000320193-26-000042",
        concept="dei:EntityCommonStockSharesOutstanding", fact_period_end="2026-06-30",
        filing_date="2026-07-25", price_session="2026-08-20", price_source="yahoo-daily",
    )
    assert r["status"] == tb.STATUS_PASS and r["market_cap_usd"] == 10_000_000_000.0
    for key in ("cik", "accession", "concept", "fact_period_end", "filing_date",
                "raw_shares_outstanding", "price_session", "price_source", "raw_close"):
        assert r[key] is not None, key


def test_multi_class_capitalization_fails_closed_with_no_invented_aggregation():
    """§7.2.1 (d), the owner's explicit fail-closed branch."""
    r = tb.evaluate_market_cap(200_000_000, 50.0, multi_class=True)
    assert r["status"] == tb.STATUS_UNRESOLVED
    assert r["reason"] == "multi_class_capitalization_ambiguous" and r["market_cap_usd"] is None


@pytest.mark.parametrize("shares,close,reason", [
    (None, 50.0, "missing_shares_outstanding"),
    (200_000_000, None, "missing_close"),
    (0, 50.0, "non_positive_shares"),
])
def test_missing_or_impossible_market_cap_inputs_fail_closed(shares, close, reason):
    r = tb.evaluate_market_cap(shares, close)
    assert r["status"] == tb.STATUS_UNRESOLVED and r["reason"] == reason


def test_market_cap_boundaries_are_inclusive_exactly_as_written():
    assert tb.evaluate_market_cap(1, 2_000_000_000.0)["status"] == tb.STATUS_PASS
    assert tb.evaluate_market_cap(1, 20_000_000_000.0)["status"] == tb.STATUS_PASS
    assert tb.evaluate_market_cap(1, 1_999_999_999.0)["status"] == tb.STATUS_FAIL
    assert tb.evaluate_market_cap(1, 20_000_000_001.0)["status"] == tb.STATUS_FAIL


def test_primary_listing_passes_only_on_an_agreeing_primary_venue():
    assert tb.evaluate_primary_listing("Nasdaq", "Nasdaq")["status"] == tb.STATUS_PASS
    assert tb.evaluate_primary_listing("NYSE", "NYSE")["status"] == tb.STATUS_PASS


def test_a_listing_disagreement_fails_closed_never_toward_the_passing_source():
    """§7.2.1 (c): 'Record any disagreement and fail closed rather than choosing whichever source
    makes the candidate pass.'"""
    r = tb.evaluate_primary_listing("Nasdaq", "NYSE")
    assert r["status"] == tb.STATUS_UNRESOLVED and r["reason"] == "directory_sec_disagreement"
    assert r["directory_exchange"] == "Nasdaq" and r["sec_exchange"] == "NYSE"


def test_a_missing_sec_cross_check_is_unresolved_not_a_silent_confirmation():
    r = tb.evaluate_primary_listing("Nasdaq", None)
    assert r["status"] == tb.STATUS_UNRESOLVED and r["reason"] == "sec_cross_check_unavailable"


@pytest.mark.parametrize("directory,sec,reason", [
    ("NYSE Arca", "NYSE Arca", "directory_venue_not_primary"),
    ("Nasdaq", "NYSE Arca", "sec_venue_not_primary"),
])
def test_non_primary_venues_fail(directory, sec, reason):
    r = tb.evaluate_primary_listing(directory, sec)
    assert r["status"] == tb.STATUS_FAIL and r["reason"] == reason


def test_a_non_common_security_fails_the_listing_criterion():
    r = tb.evaluate_primary_listing("Nasdaq", "Nasdaq", security_is_common=False)
    assert r["status"] == tb.STATUS_FAIL and r["reason"] == "not_common_stock"


# --- (g) pending M&A ------------------------------------------------------------------------------

_SEARCHED = [{"form": "8-K", "accession": "0000000000-26-000001", "filed": "2026-05-02"}]


def test_a_pending_definitive_transaction_fails():
    r = tb.evaluate_pending_ma(
        [{"status": "pending", "form": "DEFM14A", "accession": "x"}],
        filings_searched=_SEARCHED, retrieved_utc="2026-08-21T00:00:00Z",
    )
    assert r["status"] == tb.STATUS_FAIL and r["reason"] == "definitive_transaction_pending"


@pytest.mark.parametrize("status", ["closed", "terminated", "rumour"])
def test_closed_terminated_or_rumoured_transactions_do_not_fail(status):
    """The owner ruling is explicit: rumour alone does not fail, and a completed or terminated
    transaction does not remain a failure merely because it was recent."""
    r = tb.evaluate_pending_ma(
        [{"status": status, "form": "8-K", "accession": "x"}],
        filings_searched=_SEARCHED, retrieved_utc="2026-08-21T00:00:00Z",
    )
    assert r["status"] == tb.STATUS_PASS


def test_an_8k_item_101_hit_alone_is_not_a_failure_only_a_classification_duty():
    """§7.2.1 (g): 'An 8-K Item 1.01 alone is NOT a failure -- it is a search hit requiring
    transaction classification.'"""
    r = tb.evaluate_pending_ma(
        [{"status": "closed", "form": "8-K", "item": "1.01", "accession": "x"}],
        filings_searched=_SEARCHED, retrieved_utc="2026-08-21T00:00:00Z",
    )
    assert r["status"] == tb.STATUS_PASS


def test_no_search_hit_without_a_recorded_search_basis_is_not_evidence():
    """The owner's sharpest fail-closed branch: an empty result with no recorded basis never passes."""
    r = tb.evaluate_pending_ma([], filings_searched=None, retrieved_utc=None)
    assert r["status"] == tb.STATUS_UNRESOLVED and r["reason"] == "no_recorded_search_basis"


def test_a_complete_search_that_genuinely_found_nothing_does_pass():
    r = tb.evaluate_pending_ma([], filings_searched=_SEARCHED, retrieved_utc="2026-08-21T00:00:00Z")
    assert r["status"] == tb.STATUS_PASS and r["reason"] == "no_pending_definitive_transaction"


def test_an_unclassified_transaction_is_unresolved_never_assumed_benign():
    r = tb.evaluate_pending_ma(
        [{"status": "unknown", "form": "S-4"}],
        filings_searched=_SEARCHED, retrieved_utc="2026-08-21T00:00:00Z",
    )
    assert r["status"] == tb.STATUS_UNRESOLVED and r["reason"] == "transaction_status_unclassified"


def test_the_flagged_form_list_is_the_frozen_one():
    assert set(tb.PENDING_MA_FORMS) == {"8-K", "PREM14A", "DEFM14A", "S-4", "F-4", "SC 13E3"}


# --- (f) spread -----------------------------------------------------------------------------------


def test_spread_cap_is_inclusive_over_the_five_session_window():
    five = ["s1", "s2", "s3", "s4", "s5"]
    assert tb.evaluate_spread(8.0, sessions=five)["status"] == tb.STATUS_PASS
    assert tb.evaluate_spread(8.01, sessions=five)["status"] == tb.STATUS_FAIL


def test_a_missing_spread_measurement_is_unresolved_never_an_assumed_tight_spread():
    r = tb.evaluate_spread(None)
    assert r["status"] == tb.STATUS_UNRESOLVED and r["reason"] == "no_spread_measurement"


def test_a_wrong_length_spread_window_is_unresolved():
    """§7.2.1 (f) fixes the window at five completed sessions; a different window is a different
    statistic, so it cannot silently satisfy the criterion."""
    r = tb.evaluate_spread(3.0, sessions=["s1", "s2", "s3"])
    assert r["status"] == tb.STATUS_UNRESOLVED and r["reason"] == "session_window_3_of_5"


def test_more_passing_seeds_than_slots_takes_exactly_three_by_documented_order():
    """§7.2.1 (h) step 4 / (i): the starter tranche is EXACTLY three Tier-B names. Four passing
    seeds must not yield a four-name tranche -- the surplus drops by the documented seed order,
    never by a post-screen human choice. (Caught live: the real screen left four seeds standing.)"""
    out = tb.resolve_tier_b(
        passing_seeds=["RKLB", "SOFI", "AFRM", "DKNG"], passing_replacements=["AAAA"],
    )
    assert out["resolved"] == ["DKNG", "AFRM", "SOFI"]
    assert out["replacements_taken"] == []


def test_all_five_seeds_passing_still_takes_exactly_three():
    out = tb.resolve_tier_b(passing_seeds=list(tb.PROVISIONAL_SEEDS), passing_replacements=[])
    assert out["resolved"] == ["DKNG", "ETSY", "AFRM"]


# === (d) the r11 market-cap source hierarchy ======================================================


def test_the_primary_source_wins_whenever_it_is_available():
    basis = tb.select_shares_basis(
        primary={"shares": 100, "multi_class": False, "accn": "p"},
        fallback={"shares": 999, "multi_class": False, "accn": "f"},
    )
    assert basis["shares"] == 100 and basis["shares_source"] == tb.SHARES_SOURCE_PRIMARY


def test_the_fallback_is_used_only_when_the_primary_is_unavailable():
    basis = tb.select_shares_basis(
        primary=None, fallback={"shares": 999, "multi_class": False, "accn": "f"},
    )
    assert basis["shares"] == 999 and basis["shares_source"] == tb.SHARES_SOURCE_FALLBACK


def test_neither_source_available_is_unresolved_and_there_is_no_third_source():
    basis = tb.select_shares_basis(primary=None, fallback=None)
    assert basis["available"] is False and basis["shares"] is None
    cap = tb.evaluate_market_cap(basis["shares"], 50.0)
    assert cap["status"] == tb.STATUS_UNRESOLVED


def test_the_fallback_does_not_override_the_multi_class_fail_closed_rule():
    """r11 is explicit: the fallback is EVIDENCE RECOVERY, not a new capitalization methodology. A
    cover page disclosing Class A and Class B still fails closed -- summing them, taking A only, or
    substituting float/weighted-average diluted shares are all forbidden."""
    classes = [{"class_name": "Class A", "shares": 400_000_000},
               {"class_name": "Class B", "shares": 100_000_000}]
    assert tb.cover_page_multi_class(classes) is True
    basis = tb.select_shares_basis(
        primary=None,
        fallback={"shares": 400_000_000, "multi_class": tb.cover_page_multi_class(classes),
                  "classes": classes, "accn": "0000000000-26-000001"},
    )
    assert basis["shares_source"] == tb.SHARES_SOURCE_FALLBACK
    cap = tb.evaluate_market_cap(basis["shares"], 30.0, multi_class=basis["multi_class"])
    assert cap["status"] == tb.STATUS_UNRESOLVED
    assert cap["reason"] == "multi_class_capitalization_ambiguous"
    assert cap["market_cap_usd"] is None


def test_a_single_class_cover_page_resolves_normally_through_the_fallback():
    classes = [{"class_name": "Common Stock", "shares": 200_000_000}]
    assert tb.cover_page_multi_class(classes) is False
    basis = tb.select_shares_basis(
        primary=None, fallback={"shares": 200_000_000, "multi_class": False, "classes": classes},
    )
    cap = tb.evaluate_market_cap(basis["shares"], 50.0, multi_class=basis["multi_class"])
    assert cap["status"] == tb.STATUS_PASS and cap["market_cap_usd"] == 10_000_000_000.0


def test_an_empty_or_absent_class_list_is_not_treated_as_multi_class():
    assert tb.cover_page_multi_class(None) is False
    assert tb.cover_page_multi_class([]) is False


def test_a_zero_share_fallback_is_not_selected_as_a_basis():
    """A present-but-zero count is not an unambiguous point-in-time basis."""
    basis = tb.select_shares_basis(primary=None, fallback={"shares": 0, "multi_class": False})
    assert basis["available"] is False and basis["shares_source"] is None


def test_a_multi_class_signal_survives_even_when_no_single_class_basis_exists():
    """Fidelity of the RECORDED REASON, not just the outcome. A source that disclosed Class A and
    Class B did not 'fail to find' the fact -- it found data the frozen rule refuses to collapse.
    Reporting that as `missing_shares_outstanding` would understate the multi_class_unresolved
    count the owner ruling asks for. (Caught live: DKNG was mislabelled this way.)"""
    classes = [{"class_name": "ClassA", "shares": 496_454_048},
               {"class_name": "ClassB", "shares": 393_013_951}]
    basis = tb.select_shares_basis(
        primary=None,
        fallback={"shares": None, "multi_class": True, "classes": classes},
    )
    assert basis["available"] is False and basis["shares"] is None
    assert basis["multi_class"] is True
    assert basis["reason"] == "sources_disclosed_multiple_common_classes"
    assert basis["classes"] == classes
    cap = tb.evaluate_market_cap(basis["shares"], 30.0, multi_class=basis["multi_class"])
    assert cap["status"] == tb.STATUS_UNRESOLVED
    assert cap["reason"] == "multi_class_capitalization_ambiguous"


def test_a_genuinely_absent_fact_still_reports_as_absent_not_as_multi_class():
    basis = tb.select_shares_basis(primary=None, fallback={"shares": None, "multi_class": False})
    assert basis["multi_class"] is False
    assert basis["reason"] == "neither_primary_nor_fallback_yielded_a_point_in_time_shares_basis"


# === (f) exposed sessions may never become sealed recording dates =================================


def test_the_five_screening_sessions_are_frozen_in_source():
    assert tb.SCREENING_EXPOSED_SESSIONS == (
        "2026-08-14", "2026-08-17", "2026-08-18", "2026-08-19", "2026-08-20")


def test_a_date_rule_reusing_a_screening_session_is_refused():
    """§7.2.1 (f): those sessions are EXPOSED. Recording one would hand sealed historical-OOS
    credit to a date the spread screen already looked at."""
    with pytest.raises(tb.ExposedSessionInRecordingUniverse, match="2026-08-18"):
        tb.assert_no_exposed_session(["2026-07-01", "2026-08-18", "2026-07-03"])


def test_a_clean_date_rule_passes_the_exposed_session_check():
    out = tb.assert_no_exposed_session(["2026-07-01", "2026-07-02", "2026-07-06"])
    assert out["ok"] is True
    assert out["checked_against"] == list(tb.SCREENING_EXPOSED_SESSIONS)


# === (f) window COMPLETENESS (owner ruling 2026-08-21) ============================================

_FIVE = ["2026-08-14", "2026-08-17", "2026-08-18", "2026-08-19", "2026-08-20"]


def test_a_vendor_failure_on_one_required_session_makes_the_spread_unresolved():
    """The live bug this closes: FLUT hit a VendorTimeout on 2026-08-19 and a FOUR-session median
    was still reported as a definitive `fail`. A short window is a different statistic, not a
    repairable one -- and there is no date substitution."""
    got = tb.evaluate_spread(
        14.98, sessions=_FIVE, observations=96_216, source="alpaca-sip-historical-quotes",
        completed_sessions=[s for s in _FIVE if s != "2026-08-19"],
    )
    assert got["status"] == tb.STATUS_UNRESOLVED
    assert got["reason"] == "incomplete_session_window_missing_1_of_5"
    assert got["missing_sessions"] == ["2026-08-19"]


def test_a_session_that_produced_zero_eligible_observations_also_blocks_a_verdict():
    got = tb.evaluate_spread(3.0, sessions=_FIVE, completed_sessions=_FIVE[:4])
    assert got["status"] == tb.STATUS_UNRESOLVED
    assert got["missing_sessions"] == ["2026-08-20"]


def test_a_complete_five_of_five_window_still_returns_a_verdict():
    assert tb.evaluate_spread(4.98, sessions=_FIVE, completed_sessions=_FIVE)["status"] == tb.STATUS_PASS
    assert tb.evaluate_spread(10.78, sessions=_FIVE, completed_sessions=_FIVE)["status"] == tb.STATUS_FAIL


def test_the_accepted_winners_each_had_a_complete_five_of_five_window():
    """The accepted AG/LYFT/WULF resolution is NOT reopened -- this verifies it never depended on
    the bug, by re-deriving each winner's verdict from the persisted per-session record."""
    import json
    from pathlib import Path

    art = Path(__file__).resolve().parents[3] / "reports/tier-b-screen-r10/spread.json"
    rows = {r["ticker"]: r for r in json.loads(art.read_text())["rows"]}
    for tic, expected in (("AG", tb.STATUS_PASS), ("LYFT", tb.STATUS_PASS), ("WULF", tb.STATUS_PASS)):
        row = rows[tic]
        complete = [s["session"] for s in row["per_session"]
                    if "error" not in s and s.get("eligible_observations", 0) > 0]
        assert len(complete) == 5, f"{tic} was not 5/5: {complete}"
        again = tb.evaluate_spread(row["median_bps"], sessions=_FIVE,
                                   completed_sessions=complete, source=row["spread"]["source"])
        assert again["status"] == expected, (tic, again)
