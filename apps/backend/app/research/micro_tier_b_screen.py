"""Tier-B resolution — the frozen operational protocol (``docs/rapid-validation-spec.md`` §7.2.1,
revision r10, owner ruling 2026-08-21).

**What this closes.** §7.2 froze the mandatory ORDER of the Tier-B resolution and Card 5.2 froze the
six screening CRITERIA, but nothing was executable: the spec never named the candidate UNIVERSE that
replacement names are drawn from, nor the provenance protocol for the three externally-sourced
criteria (market cap, primary US listing, no pending M&A). r10 supplied that operational detail;
this module implements it, and NOTHING here may reinterpret a criterion.

**The six criteria are UNCHANGED and are not this module's to touch**: market cap USD 2B–20B; price
USD 15–100; trailing 30-session ADV ≥ 3M shares; median RTH quoted spread ≤ 8 bps; primary US
listing; no pending M&A.

**Fail-closed everywhere.** Every evaluator returns one of three statuses — ``pass``, ``fail``, or
``unresolved`` — and ``unresolved`` NEVER admits a candidate (§7.2.1 (b)/(c)/(d)). An ambiguous
security type, a multi-class capitalization that one price × one share count cannot represent, or a
directory-vs-SEC listing disagreement all resolve AGAINST the candidate, with the reason preserved.
That asymmetry is deliberate: admitting a name on missing evidence is exactly the laundering the
Validation Vault exists to prevent, while excluding one merely costs us a replacement.

**Determinism.** Nothing here consults a Tapeology research outcome, and no ordering is derived from
a screen result. Replacement survivors rank by ``sha256(TIER_B_R10_SALT + normalized_ticker)``
(§7.2.1 (h)) — ticker-alphabetical was explicitly REJECTED by the owner because it imports a lexical
bias. The five Card-5.2 provisional names are SEEDS that face the identical screen, never
grandfathered passes.

**Screen-once.** ``§7.2.1 (j)``: universe, source hierarchy, cutoff, criteria and selection rule are
frozen BEFORE the screen, and the screen then runs EXACTLY ONCE. This module therefore separates
pure, fixture-testable logic (parsing, exclusion, ranking, resolution) from the I/O that acquires
evidence, so every branch — including every fail-closed branch — is provable without a network call.

**No new ``Config`` field.** Every constant here is a plain module constant, frozen at authoring;
``config_fingerprint()`` is untouched.
"""

from __future__ import annotations

import hashlib
import re

__all__ = [
    "TIER_B_R10_SALT",
    "PROVISIONAL_SEEDS",
    "PARSER_VERSION",
    "STATUS_PASS",
    "STATUS_FAIL",
    "STATUS_UNRESOLVED",
    "PRIMARY_LISTING_EXCHANGES",
    "parse_nasdaqlisted",
    "parse_otherlisted",
    "embedded_file_creation_time",
    "mechanical_exclusion_reason",
    "build_candidate_universe",
    "membership_hash",
    "replacement_rank_key",
    "resolve_tier_b",
    "TierBResolutionImpossible",
    "parser_version_hash",
]

# --- frozen constants (§7.2.1) --------------------------------------------------------------------

#: The salt the owner ruling fixes for replacement ordering. Changing it would silently re-order
#: every future resolution, so it is frozen in source and covered by a test.
TIER_B_R10_SALT = "rapid-microscope-tier-b-r10:"

#: Card 5.2's provisional Tier-B names, in their ALREADY-DOCUMENTED order (§7.2.1 (h) step 1 retains
#: passing names in this order). Seeds, never grandfathered passes.
PROVISIONAL_SEEDS: tuple[str, ...] = ("DKNG", "ETSY", "AFRM", "SOFI", "RKLB")

#: Bumped whenever the parsing/exclusion rules below change, and recorded in the provenance row so a
#: later reader knows exactly which rules produced a given candidate universe (§7.2.1 (a)).
PARSER_VERSION = "tier-b-screen-parser-r10-v1"

STATUS_PASS = "pass"
STATUS_FAIL = "fail"
STATUS_UNRESOLVED = "unresolved"

#: §7.2.1 (c): the only venues a primary US listing may name. `otherlisted` exchange codes are
#: single letters; `nasdaqlisted` membership implies Nasdaq. NYSE Arca (`P`), Cboe/BATS (`Z`) and
#: IEX (`V`) are NOT primary common-equity listing venues for this screen.
PRIMARY_LISTING_EXCHANGES: dict[str, str] = {"N": "NYSE", "A": "NYSE American", "Q": "Nasdaq"}

_NASDAQ_HEADER = "Symbol|Security Name|Market Category|Test Issue|Financial Status|Round Lot Size|ETF|NextShares"
_OTHER_HEADER = "ACT Symbol|Security Name|Exchange|CQS Symbol|ETF|Round Lot Size|Test Issue|NASDAQ Symbol"
_FILE_CREATION_PREFIX = "File Creation Time:"


class TierBResolutionImpossible(Exception):
    """§7.2.1 (h): fewer than three eligible Tier-B names exist in total. A HARD STOP — the caller
    must escalate to the owner, never loosen a criterion and never substitute a name by hand."""


# --- (b) the mechanical, non-common-equity exclusion vocabulary ------------------------------------
#
# Matched against the directory's own `Security Name`. Ordered most-specific-first so a name like
# "... Class A Common Stock Warrant" excludes as a warrant rather than admitting as common stock.
# Every pattern is a whole-word/suffix match, never a bare substring, so "Unitil Corporation" is not
# mistaken for a unit and "Preferred Apartment Communities" is not mistaken for a preferred share.
_EXCLUSION_PATTERNS: tuple[tuple[str, str], ...] = (
    ("warrant", r"\bwarrants?\b"),
    ("right", r"\brights?\b"),
    ("unit", r"\bunits?\b"),
    # `adr` MUST precede `preferred`: "American Depositary Shares" contains "Depositary Shares", and
    # the more specific instrument wins (a fixture proved the reversed order mislabelled every ADR).
    ("adr", r"\bamerican depositary\b|\bamerican depository\b|\bADR\b|\bADS\b"),
    # Bare "\bpreferred\b" over-matched real company names ("Preferred Apartment Communities Inc
    # Common Stock") and silently shrank the universe -- a fixture caught it. Require the
    # instrument phrasing.
    ("preferred", r"\bpreferred (stock|shares?|securit\w+)\b|\bpfd\b"
                  r"|\bdeposit(a|o)ry shares?\b|%\s*(series\s+\w+\s+)?preferred\b"),
    ("note_or_etn", r"\bnotes?\b|\bdebenture\b|\bETN\b|\bexchange[- ]traded note\b"),
    ("fund", r"\bfund\b|\btrust\b|\bETF\b|\bportfolio\b|\bindex\b|\bSPDR\b"),
    ("when_issued", r"\bwhen[- ]issued\b"),
    ("subscription", r"\bsubscription\b"),
    ("convertible", r"\bconvertible\b"),
)

#: A row is admitted ONLY if its security name positively looks like common stock. Anything else is
#: `unresolved` and excluded (§7.2.1 (b): "If security type is ambiguous, do not silently guess it
#: into the universe").
_COMMON_STOCK_PATTERN = re.compile(
    r"\b(common stock|common shares|ordinary shares|class [a-z] common stock"
    r"|class [a-z] ordinary shares|common stock, class [a-z])\b",
    re.IGNORECASE,
)


def parser_version_hash() -> str:
    """A content hash over the exclusion vocabulary and the common-stock predicate, recorded beside
    ``PARSER_VERSION`` in the provenance row -- so a silent edit to a regex cannot masquerade as the
    same parser (§7.2.1 (a): "parser/version hash")."""
    payload = "|".join(
        [PARSER_VERSION, _COMMON_STOCK_PATTERN.pattern]
        + [f"{name}={pattern}" for name, pattern in _EXCLUSION_PATTERNS]
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _split_rows(raw: bytes, expected_header: str) -> list[list[str]]:
    """Split a Nasdaq Trader directory file into its data rows, refusing outright if the header is
    not the one this parser was written against -- a silently changed column order would otherwise
    mis-read every flag. Drops the trailing ``File Creation Time:`` sentinel row."""
    text = raw.decode("utf-8", errors="strict")
    lines = [ln for ln in text.split("\n") if ln.strip()]
    if not lines or lines[0].strip() != expected_header:
        raise ValueError(
            f"unexpected directory header -- this parser ({PARSER_VERSION}) was written against "
            f"{expected_header!r} and refuses to guess a changed column order"
        )
    rows = []
    for line in lines[1:]:
        if line.startswith(_FILE_CREATION_PREFIX):
            continue
        rows.append(line.split("|"))
    return rows


def embedded_file_creation_time(raw: bytes) -> str:
    """Nasdaq's own embedded file-creation timestamp (§7.2.1 (a)) -- the vendor's statement of WHEN
    this snapshot was cut, independent of when we retrieved it."""
    text = raw.decode("utf-8", errors="strict")
    for line in text.split("\n"):
        if line.startswith(_FILE_CREATION_PREFIX):
            return line[len(_FILE_CREATION_PREFIX):].strip().rstrip("|").strip()
    raise ValueError("directory file carries no 'File Creation Time:' line")


def parse_nasdaqlisted(raw: bytes) -> list[dict]:
    """``nasdaqlisted``: Symbol|Security Name|Market Category|Test Issue|Financial Status|
    Round Lot Size|ETF|NextShares. Every row is Nasdaq-listed, so the venue is Nasdaq (``Q``)."""
    out = []
    for cols in _split_rows(raw, _NASDAQ_HEADER):
        if len(cols) < 8:
            continue
        out.append({
            "ticker": cols[0].strip().upper(),
            "security_name": cols[1].strip(),
            "exchange_code": "Q",
            "exchange": "Nasdaq",
            "test_issue": cols[3].strip().upper(),
            "etf": cols[6].strip().upper(),
            "source_file": "nasdaqlisted",
        })
    return out


def parse_otherlisted(raw: bytes) -> list[dict]:
    """``otherlisted``: ACT Symbol|Security Name|Exchange|CQS Symbol|ETF|Round Lot Size|Test Issue|
    NASDAQ Symbol. The ``Exchange`` column is the listing venue code."""
    out = []
    for cols in _split_rows(raw, _OTHER_HEADER):
        if len(cols) < 8:
            continue
        code = cols[2].strip().upper()
        out.append({
            "ticker": cols[0].strip().upper(),
            "security_name": cols[1].strip(),
            "exchange_code": code,
            "exchange": PRIMARY_LISTING_EXCHANGES.get(code, ""),
            "test_issue": cols[6].strip().upper(),
            "etf": cols[4].strip().upper(),
            "source_file": "otherlisted",
        })
    return out


def mechanical_exclusion_reason(row: dict) -> str | None:
    """§7.2.1 (b). ``None`` means the row survives to the six-factor screen; any string is the frozen
    reason it was excluded BEFORE that screen. Applied in a fixed order so a row that matches several
    categories always reports the same reason."""
    if row.get("test_issue") == "Y":
        return "test_issue"
    if row.get("etf") == "Y":
        return "etf_flag"
    name = row.get("security_name", "")
    for reason, pattern in _EXCLUSION_PATTERNS:
        if re.search(pattern, name, re.IGNORECASE):
            return reason
    if not _COMMON_STOCK_PATTERN.search(name):
        # Ambiguous security type -- excluded with provenance, never silently admitted.
        return "unresolved_security_type"
    if row.get("exchange_code") not in PRIMARY_LISTING_EXCHANGES:
        # §7.2.1 (c): not a primary US listing venue for this screen.
        return "non_primary_listing_venue"
    return None


def build_candidate_universe(nasdaq_raw: bytes, other_raw: bytes) -> dict:
    """The complete, reproducible pre-filter candidate set (§7.2.1 (a)/(b)).

    Returns the surviving candidates, EVERY excluded row with its frozen reason (no hidden manual
    exclusions -- §7.2.1 (j)), and the pre-filter membership hash. Duplicate tickers across the two
    directories are resolved deterministically toward the FIRST occurrence in
    ``nasdaqlisted``-then-``otherlisted`` order and recorded, never silently merged."""
    rows = parse_nasdaqlisted(nasdaq_raw) + parse_otherlisted(other_raw)
    seen: dict[str, dict] = {}
    duplicates: list[dict] = []
    for row in rows:
        if row["ticker"] in seen:
            duplicates.append(row)
            continue
        seen[row["ticker"]] = row

    candidates, excluded = [], []
    for ticker in sorted(seen):
        row = seen[ticker]
        reason = mechanical_exclusion_reason(row)
        if reason is None:
            candidates.append(row)
        else:
            excluded.append({**row, "exclusion_reason": reason})
    return {
        "parser_version": PARSER_VERSION,
        "parser_version_hash": parser_version_hash(),
        "total_rows": len(rows),
        "distinct_tickers": len(seen),
        "duplicate_rows": duplicates,
        "candidates": candidates,
        "excluded": excluded,
        "membership_hash": membership_hash([c["ticker"] for c in candidates]),
    }


def membership_hash(tickers: list[str]) -> str:
    """§7.2.1 (a): the pre-filter membership hash -- order-independent by construction (sorted), so
    it identifies the SET rather than any particular enumeration of it."""
    payload = "\n".join(sorted(t.strip().upper() for t in tickers))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def replacement_rank_key(ticker: str) -> str:
    """§7.2.1 (h) step 3: ``sha256(TIER_B_R10_SALT + normalized_ticker)``. Deterministic, frozen
    before the screen, and independent of every Tapeology outcome and of lexical ticker order."""
    return hashlib.sha256((TIER_B_R10_SALT + ticker.strip().upper()).encode("utf-8")).hexdigest()


def resolve_tier_b(passing_seeds: list[str], passing_replacements: list[str], *, needed: int = 3) -> dict:
    """§7.2.1 (h) steps 1-4, applied to ALREADY-SCREENED results.

    ``passing_seeds`` are those Card-5.2 provisional names that passed the identical six-factor
    screen, and are retained in their already-documented ``PROVISIONAL_SEEDS`` order.
    ``passing_replacements`` are every OTHER eligible survivor; they are ranked by
    ``replacement_rank_key`` and only enough are taken to reach exactly ``needed``.

    Raises ``TierBResolutionImpossible`` when fewer than ``needed`` eligible names exist in total --
    the owner's hard STOP. This function never widens a criterion and never sees one."""
    seeds_in_order = [t for t in PROVISIONAL_SEEDS if t in set(passing_seeds)]
    # §7.2.1 (h) step 4 / (i): the starter tranche takes EXACTLY `needed` Tier-B names. When more
    # seeds pass than there are slots, the surplus is dropped by the already-documented seed order --
    # never by a post-screen human choice, and never by taking all of them.
    chosen = list(seeds_in_order)[:needed]
    ranked = sorted(
        (t for t in dict.fromkeys(passing_replacements) if t not in set(chosen)),
        key=replacement_rank_key,
    )
    for ticker in ranked:
        if len(chosen) >= needed:
            break
        chosen.append(ticker)
    if len(chosen) < needed:
        raise TierBResolutionImpossible(
            f"only {len(chosen)} eligible Tier-B name(s) exist ({chosen!r}); §7.2.1 (h) requires "
            f"{needed} and forbids loosening any criterion or substituting a name by hand -- STOP "
            "and escalate to the owner"
        )
    return {
        "resolved": chosen,
        "passing_seeds_in_documented_order": seeds_in_order,
        "replacement_ranking": [
            {"ticker": t, "rank_key": replacement_rank_key(t)} for t in ranked
        ],
        "replacements_taken": [t for t in chosen if t not in seeds_in_order],
        "salt": TIER_B_R10_SALT,
    }


# === the six frozen criteria — PURE evaluators (§7.2.1 (c)-(g)) ===================================
#
# Each takes already-acquired evidence and returns {status, reason, **raw inputs}. Keeping them pure
# is what makes every fail-closed branch provable on fixtures BEFORE the one-shot screen (§7.2.1
# (j)). The thresholds below are Card 5.2's, restated verbatim and NEVER tuned here.

PRICE_MIN_USD, PRICE_MAX_USD = 15.0, 100.0
MARKET_CAP_MIN_USD, MARKET_CAP_MAX_USD = 2_000_000_000.0, 20_000_000_000.0
ADV_MIN_SHARES = 3_000_000.0
ADV_SESSIONS = 30
SPREAD_MAX_BPS = 8.0
SPREAD_SESSIONS = 5

__all__ += [
    "PRICE_MIN_USD", "PRICE_MAX_USD", "MARKET_CAP_MIN_USD", "MARKET_CAP_MAX_USD",
    "ADV_MIN_SHARES", "ADV_SESSIONS", "SPREAD_MAX_BPS", "SPREAD_SESSIONS",
    "evaluate_price", "evaluate_adv", "evaluate_market_cap", "evaluate_primary_listing",
    "evaluate_pending_ma", "evaluate_spread", "PENDING_MA_FORMS",
]


def _result(status: str, reason: str, **fields) -> dict:
    return {"status": status, "reason": reason, **fields}


def evaluate_price(close: float | None, *, session: str | None = None, source: str | None = None) -> dict:
    """Card 5.2: price USD 15-100, on the most recent completed official close at or before the
    cutoff. A missing close is ``unresolved`` (fail-closed), never treated as out-of-range."""
    if close is None:
        return _result(STATUS_UNRESOLVED, "no_close_available", close=None, session=session, source=source)
    ok = PRICE_MIN_USD <= float(close) <= PRICE_MAX_USD
    return _result(
        STATUS_PASS if ok else STATUS_FAIL,
        "in_range" if ok else "out_of_range",
        close=float(close), session=session, source=source,
    )


def evaluate_adv(volumes: list[float], *, sessions: list[str] | None = None, source: str | None = None) -> dict:
    """§7.2.1 (e): the arithmetic mean of raw share volume over the 30 most recent fully completed
    regular US trading SESSIONS strictly before the cutoff -- never 30 calendar days.

    Fewer than 30 completed sessions is ``unresolved``: a mean over a short window is a DIFFERENT
    statistic, and silently accepting it would be exactly the criterion-loosening the owner
    forbade."""
    if len(volumes) < ADV_SESSIONS:
        return _result(
            STATUS_UNRESOLVED, f"insufficient_sessions_{len(volumes)}_of_{ADV_SESSIONS}",
            adv=None, sessions=sessions, source=source,
        )
    window = [float(v) for v in volumes[-ADV_SESSIONS:]]
    if any(v < 0 for v in window):
        return _result(STATUS_UNRESOLVED, "negative_volume", adv=None, sessions=sessions, source=source)
    adv = sum(window) / ADV_SESSIONS
    ok = adv >= ADV_MIN_SHARES
    return _result(
        STATUS_PASS if ok else STATUS_FAIL,
        "meets_floor" if ok else "below_floor",
        adv=adv, sessions=(sessions[-ADV_SESSIONS:] if sessions else None), source=source,
    )


def evaluate_market_cap(
    shares_outstanding: float | None,
    close: float | None,
    *,
    multi_class: bool = False,
    cik: str | None = None,
    accession: str | None = None,
    concept: str | None = None,
    fact_period_end: str | None = None,
    filing_date: str | None = None,
    price_session: str | None = None,
    price_source: str | None = None,
) -> dict:
    """§7.2.1 (d): latest SEC-reported common shares outstanding available as of the cutoff x the
    most recent completed official close at or before the cutoff.

    **Fails closed on ambiguity.** Where a multi-class (or otherwise ambiguous) capitalization means
    one ticker price x one share figure does not unambiguously represent issuer market cap, the
    status is ``unresolved`` and the candidate does NOT advance. The owner ruling is explicit that
    no aggregation rule may be invented after seeing candidates -- so this function has none."""
    prov = {
        "cik": cik, "accession": accession, "concept": concept,
        "fact_period_end": fact_period_end, "filing_date": filing_date,
        "raw_shares_outstanding": shares_outstanding,
        "price_session": price_session, "price_source": price_source, "raw_close": close,
    }
    if multi_class:
        return _result(STATUS_UNRESOLVED, "multi_class_capitalization_ambiguous",
                       market_cap_usd=None, **prov)
    if shares_outstanding is None or close is None:
        missing = "shares_outstanding" if shares_outstanding is None else "close"
        return _result(STATUS_UNRESOLVED, f"missing_{missing}", market_cap_usd=None, **prov)
    if float(shares_outstanding) <= 0:
        return _result(STATUS_UNRESOLVED, "non_positive_shares", market_cap_usd=None, **prov)
    cap = float(shares_outstanding) * float(close)
    ok = MARKET_CAP_MIN_USD <= cap <= MARKET_CAP_MAX_USD
    return _result(STATUS_PASS if ok else STATUS_FAIL,
                   "in_range" if ok else "out_of_range", market_cap_usd=cap, **prov)


def evaluate_primary_listing(
    directory_exchange: str | None, sec_exchange: str | None, *, security_is_common: bool = True,
) -> dict:
    """§7.2.1 (c). Passes only §12(b)-registered common stock whose primary venue is Nasdaq, NYSE or
    NYSE American, with the frozen directory snapshot as listing owner and the SEC cover page as the
    authoritative cross-check.

    **A disagreement FAILS CLOSED** -- recorded, never resolved toward whichever source lets the
    candidate pass. A missing SEC cross-check is likewise ``unresolved``: the ruling asks for a
    cross-check, and an absent one is not a silent confirmation."""
    prov = {"directory_exchange": directory_exchange, "sec_exchange": sec_exchange}
    if not security_is_common:
        return _result(STATUS_FAIL, "not_common_stock", **prov)
    if directory_exchange not in PRIMARY_LISTING_EXCHANGES.values():
        return _result(STATUS_FAIL, "directory_venue_not_primary", **prov)
    if sec_exchange is None:
        return _result(STATUS_UNRESOLVED, "sec_cross_check_unavailable", **prov)
    if sec_exchange not in PRIMARY_LISTING_EXCHANGES.values():
        return _result(STATUS_FAIL, "sec_venue_not_primary", **prov)
    if sec_exchange != directory_exchange:
        return _result(STATUS_UNRESOLVED, "directory_sec_disagreement", **prov)
    return _result(STATUS_PASS, "primary_us_listing_confirmed", **prov)


#: §7.2.1 (g): the forms flagged for transaction-status inspection. Presence is a SEARCH HIT
#: requiring classification -- explicitly NOT a failure by itself.
PENDING_MA_FORMS: tuple[str, ...] = ("8-K", "PREM14A", "DEFM14A", "S-4", "F-4", "SC 13E3")


def evaluate_pending_ma(
    classified_transactions: list[dict] | None,
    *,
    filings_searched: list[dict] | None = None,
    retrieved_utc: str | None = None,
    search_window_months: int = 24,
) -> dict:
    """§7.2.1 (g). FAILS iff public SEC/issuer evidence establishes a DEFINITIVE, announced
    merger/acquisition/business-combination/take-private involving the candidate that remains
    PENDING. Rumour alone does not fail; closed or terminated transactions do not fail.

    Each entry of ``classified_transactions`` is ``{"status": "pending"|"closed"|"terminated"|
    "rumour", ...}``. **A missing or empty search record is ``unresolved``, never a pass** -- the
    owner ruling is explicit that "no search hit" without the complete frozen search record is not
    evidence."""
    prov = {
        "filings_searched": filings_searched, "retrieved_utc": retrieved_utc,
        "search_window_months": search_window_months,
        "classified_transactions": classified_transactions,
    }
    if filings_searched is None or retrieved_utc is None:
        return _result(STATUS_UNRESOLVED, "no_recorded_search_basis", **prov)
    if classified_transactions is None:
        return _result(STATUS_UNRESOLVED, "transactions_not_classified", **prov)
    unclassified = [t for t in classified_transactions
                    if t.get("status") not in ("pending", "closed", "terminated", "rumour")]
    if unclassified:
        return _result(STATUS_UNRESOLVED, "transaction_status_unclassified", **prov)
    pending = [t for t in classified_transactions if t.get("status") == "pending"]
    if pending:
        return _result(STATUS_FAIL, "definitive_transaction_pending", **prov)
    return _result(STATUS_PASS, "no_pending_definitive_transaction", **prov)


def evaluate_spread(
    median_bps: float | None, *, sessions: list[str] | None = None,
    observations: int | None = None, source: str | None = None,
) -> dict:
    """Card 5.2: median RTH quoted spread <= 8 bps, over the §7.2.1 (f) window of the 5 most recent
    fully completed regular sessions strictly before the cutoff. A missing measurement is
    ``unresolved`` (fail-closed) -- never an assumed-tight spread."""
    prov = {"sessions": sessions, "observations": observations, "source": source}
    if median_bps is None:
        return _result(STATUS_UNRESOLVED, "no_spread_measurement", median_bps=None, **prov)
    if sessions is not None and len(sessions) != SPREAD_SESSIONS:
        return _result(STATUS_UNRESOLVED,
                       f"session_window_{len(sessions)}_of_{SPREAD_SESSIONS}",
                       median_bps=float(median_bps), **prov)
    ok = float(median_bps) <= SPREAD_MAX_BPS
    return _result(STATUS_PASS if ok else STATUS_FAIL,
                   "within_cap" if ok else "exceeds_cap", median_bps=float(median_bps), **prov)
