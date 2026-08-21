"""Operator runner for the Tier-B screen (spec §7.2.1, r10).

Acquires the evidence the pure evaluators in ``app.research.micro_tier_b_screen`` consume, and
persists the complete provenance record §7.2.1 (a)/(j) requires. Split into explicit stages so the
operator can run them in order and inspect each before the next -- the screen is ONE SHOT.

    python -m scripts.tier_b_screen_r10 freeze     # (a) retrieve + immutably preserve the snapshot
    python -m scripts.tier_b_screen_r10 universe   # (b) parse + mechanical exclusions
    python -m scripts.tier_b_screen_r10 bars       # price + ADV over the frozen candidate set

Every stage writes into ``ARTIFACT_DIR`` and never mutates a file another stage wrote. NOTHING here
issues a J-06 tape call: the recorder is not imported, and the only market data touched is the
SCREENING basis §7.2.1 (e)/(f) defines (which is EXPOSED data by construction).
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.research import micro_tier_b_screen as tb  # noqa: E402

ARTIFACT_DIR = Path(__file__).resolve().parents[3] / "reports" / "tier-b-screen-r10"

_DIRECTORY_URLS = {
    "nasdaqlisted": "https://www.nasdaqtrader.com/dynamic/SymDir/nasdaqlisted.txt",
    "otherlisted": "https://www.nasdaqtrader.com/dynamic/SymDir/otherlisted.txt",
}
#: SEC requires a descriptive User-Agent naming a contact; this is reference data, never market tape.
_USER_AGENT = "tapeology-research/1.0 (dennis_chan_1987@yahoo.com.hk)"


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read()


def stage_freeze() -> dict:
    """§7.2.1 (a). Retrieve both directories ONCE and preserve them immutably: exact raw bytes,
    SHA-256 of each, Nasdaq's embedded file-creation timestamp, the retrieval UTC timestamp, and the
    parser version + hash. A later reader reproduces the exact candidate universe from these BYTES,
    never from the live URL, which Nasdaq overwrites daily."""
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    manifest_path = ARTIFACT_DIR / "source-snapshot.json"
    if manifest_path.exists():
        raise SystemExit(
            f"REFUSING: {manifest_path} already exists. The source snapshot is frozen exactly once "
            "(§7.2.1 (a)/(j)); re-freezing would silently re-cut the universe under a new cutoff."
        )
    retrieved_utc = _utc_now()
    entry = {}
    for name, url in _DIRECTORY_URLS.items():
        raw = _fetch(url)
        (ARTIFACT_DIR / f"{name}.txt").write_bytes(raw)
        entry[name] = {
            "url": url,
            "bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(),
            "embedded_file_creation_time": tb.embedded_file_creation_time(raw),
        }
    manifest = {
        "spec_revision": "r10",
        "stage": "source_snapshot",
        "screening_cutoff_utc": retrieved_utc,
        "retrieved_utc": retrieved_utc,
        "parser_version": tb.PARSER_VERSION,
        "parser_version_hash": tb.parser_version_hash(),
        "files": entry,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return manifest


def _load_snapshot() -> tuple[dict, bytes, bytes]:
    manifest = json.loads((ARTIFACT_DIR / "source-snapshot.json").read_text())
    nas = (ARTIFACT_DIR / "nasdaqlisted.txt").read_bytes()
    oth = (ARTIFACT_DIR / "otherlisted.txt").read_bytes()
    for name, raw in (("nasdaqlisted", nas), ("otherlisted", oth)):
        actual = hashlib.sha256(raw).hexdigest()
        expected = manifest["files"][name]["sha256"]
        if actual != expected:
            raise SystemExit(f"REFUSING: {name} on disk does not match the frozen snapshot hash")
    return manifest, nas, oth


def stage_universe() -> dict:
    """§7.2.1 (b). Parse the FROZEN bytes and apply the mechanical exclusions, recording every
    excluded row with its frozen reason. Verifies the on-disk bytes still hash to the frozen
    manifest first -- the universe is never rebuilt from anything but the preserved snapshot."""
    manifest, nas, oth = _load_snapshot()
    uni = tb.build_candidate_universe(nas, oth)
    out = {
        "spec_revision": "r10",
        "stage": "candidate_universe",
        "screening_cutoff_utc": manifest["screening_cutoff_utc"],
        "source_snapshot_sha256": {k: v["sha256"] for k, v in manifest["files"].items()},
        "parser_version": uni["parser_version"],
        "parser_version_hash": uni["parser_version_hash"],
        "total_rows": uni["total_rows"],
        "distinct_tickers": uni["distinct_tickers"],
        "candidate_count": len(uni["candidates"]),
        "excluded_count": len(uni["excluded"]),
        "pre_filter_membership_hash": uni["membership_hash"],
        "candidates": [
            {k: c[k] for k in ("ticker", "security_name", "exchange", "exchange_code", "source_file")}
            for c in uni["candidates"]
        ],
        "excluded": [
            {k: e[k] for k in ("ticker", "security_name", "exchange_code", "exclusion_reason")}
            for e in uni["excluded"]
        ],
    }
    (ARTIFACT_DIR / "candidate-universe.json").write_text(
        json.dumps(out, indent=2, sort_keys=True) + "\n"
    )
    return out


def stage_bars(chunk_size: int = 150) -> dict:
    """Price (Card 5.2: USD 15-100) and ADV (§7.2.1 (e): 30 COMPLETED SESSIONS) over the frozen
    candidate set, from the project's canonical Yahoo daily-bar basis.

    The exact per-candidate session list and raw inputs are persisted (§7.2.1 (d)/(e)). Sessions are
    taken strictly before the cutoff date, and a candidate with fewer than 30 completed sessions is
    ``unresolved`` -- never a short-window mean."""
    import warnings

    warnings.filterwarnings("ignore")
    import yfinance as yf

    universe = json.loads((ARTIFACT_DIR / "candidate-universe.json").read_text())
    cutoff_date = universe["screening_cutoff_utc"][:10]
    tickers = [c["ticker"] for c in universe["candidates"]]

    rows: dict[str, dict] = {}
    started = time.time()
    for i in range(0, len(tickers), chunk_size):
        batch = tickers[i:i + chunk_size]
        try:
            df = yf.download(batch, period="6mo", interval="1d", auto_adjust=False,
                             progress=False, threads=True, group_by="column")
        except Exception as exc:  # noqa: BLE001 -- a vendor failure is disclosed, never silent
            for t in batch:
                rows[t] = {"error": f"{type(exc).__name__}: {exc}"}
            continue
        if df is None or df.empty:
            for t in batch:
                rows[t] = {"error": "empty_response"}
            continue
        close_all, vol_all = df["Close"], df["Volume"]
        sessions_all = [str(d)[:10] for d in close_all.index]
        keep = [n for n, d in enumerate(sessions_all) if d < cutoff_date]
        for t in batch:
            try:
                closes = [close_all[t].iloc[n] for n in keep]
                vols = [vol_all[t].iloc[n] for n in keep]
            except Exception:  # noqa: BLE001 -- symbol absent from the batch response
                rows[t] = {"error": "absent_from_response"}
                continue
            pairs = [(sessions_all[n], c, v) for n, c, v in zip(keep, closes, vols)
                     if c == c and v == v]  # drop NaN rows (holidays / halted)
            if not pairs:
                rows[t] = {"error": "no_completed_sessions"}
                continue
            sess = [p[0] for p in pairs]
            rows[t] = {
                "sessions": sess,
                "last_session": sess[-1],
                "last_close": float(pairs[-1][1]),
                "volumes": [float(p[2]) for p in pairs],
            }
        sys.stderr.write(
            f"  bars {min(i + chunk_size, len(tickers))}/{len(tickers)}  "
            f"{time.time() - started:.0f}s\n"
        )

    results = []
    for c in universe["candidates"]:
        t = c["ticker"]
        row = rows.get(t, {"error": "not_fetched"})
        if "error" in row:
            price = tb.evaluate_price(None, source="yahoo-daily")
            adv = tb.evaluate_adv([], source="yahoo-daily")
            price["reason"] = adv["reason"] = row["error"]
        else:
            price = tb.evaluate_price(row["last_close"], session=row["last_session"],
                                      source="yahoo-daily")
            adv = tb.evaluate_adv(row["volumes"], sessions=row["sessions"], source="yahoo-daily")
        results.append({"ticker": t, "exchange": c["exchange"], "price": price, "adv": adv})

    survivors = [r["ticker"] for r in results
                 if r["price"]["status"] == tb.STATUS_PASS and r["adv"]["status"] == tb.STATUS_PASS]
    out = {
        "spec_revision": "r10",
        "stage": "price_and_adv",
        "screening_cutoff_utc": universe["screening_cutoff_utc"],
        "price_basis": "yahoo-daily official close, last completed session strictly before cutoff",
        "adv_basis": f"arithmetic mean of raw share volume over the {tb.ADV_SESSIONS} most recent "
                     "fully completed regular sessions strictly before cutoff",
        "candidate_count": len(results),
        "survivor_count": len(survivors),
        "survivors": sorted(survivors),
        "results": results,
    }
    (ARTIFACT_DIR / "price-adv.json").write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    return out


_STAGES = {"freeze": stage_freeze, "universe": stage_universe, "bars": stage_bars}
# `sec` takes tickers on the command line, so it is dispatched separately in main().


def main() -> int:
    if len(sys.argv) >= 3 and sys.argv[1] == "sec":
        out = stage_sec([t.strip().upper() for t in sys.argv[2].split(",") if t.strip()])
        print(json.dumps({k: v for k, v in out.items() if not isinstance(v, list)},
                         indent=2, sort_keys=True))
        return 0
    if len(sys.argv) != 2 or sys.argv[1] not in _STAGES:
        print(f"usage: python -m scripts.tier_b_screen_r10 {{{'|'.join(_STAGES)}}}")
        return 2
    out = _STAGES[sys.argv[1]]()
    summary = {k: v for k, v in out.items() if not isinstance(v, list)}
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0



# --- SEC evidence (§7.2.1 (c) cross-check, (d) market cap, (g) pending M&A) ------------------------

_SEC_TICKERS_URL = "https://www.sec.gov/files/company_tickers_exchange.json"
_SEC_CONCEPT = ("https://data.sec.gov/api/xbrl/companyconcept/CIK{cik:010d}"
                "/dei/EntityCommonStockSharesOutstanding.json")
_SEC_SUBMISSIONS = "https://data.sec.gov/submissions/CIK{cik:010d}.json"
#: SEC fair-access policy is 10 requests/second; stay well under it.
_SEC_PAUSE_SECONDS = 0.15
_SEC_EXCHANGE_NAMES = {"Nasdaq": "Nasdaq", "NYSE": "NYSE", "NYSE American": "NYSE American",
                       "NYSEAmerican": "NYSE American", "NYSE Arca": "NYSE Arca", "CBOE": "Cboe"}


def _sec_ticker_index() -> dict:
    """``company_tickers_exchange.json`` -> {ticker: {cik, sec_exchange, tickers_for_cik}}. The
    per-CIK ticker count is what surfaces a multi-class issuer (§7.2.1 (d))."""
    payload = json.loads(_fetch(_SEC_TICKERS_URL))
    fields = payload["fields"]
    i_cik, i_tic, i_exch = fields.index("cik"), fields.index("ticker"), fields.index("exchange")
    by_cik: dict[int, list[str]] = {}
    rows = {}
    for row in payload["data"]:
        cik, tic, exch = row[i_cik], str(row[i_tic]).upper(), row[i_exch]
        by_cik.setdefault(cik, []).append(tic)
        rows[tic] = {"cik": cik, "sec_exchange_raw": exch}
    for tic, r in rows.items():
        r["tickers_for_cik"] = sorted(by_cik[r["cik"]])
        r["sec_exchange"] = _SEC_EXCHANGE_NAMES.get(str(r["sec_exchange_raw"]), None)
    return rows


def _latest_shares_fact(cik: int, cutoff_date: str) -> dict | None:
    """The latest ``dei:EntityCommonStockSharesOutstanding`` fact legally available at the cutoff,
    plus a multi-class signal: two DIFFERENT values sharing one period end means the concept is
    reported per share class, which one ticker price cannot represent (§7.2.1 (d))."""
    try:
        payload = json.loads(_fetch(_SEC_CONCEPT.format(cik=cik)))
    except Exception:  # noqa: BLE001 -- absence is unresolved, never a guess
        return None
    facts = []
    for unit_rows in payload.get("units", {}).values():
        for f in unit_rows:
            if f.get("filed") and f["filed"] <= cutoff_date and f.get("val"):
                facts.append(f)
    if not facts:
        return None
    facts.sort(key=lambda f: (f.get("filed", ""), f.get("end", "")))
    latest = facts[-1]
    same_period = {f["val"] for f in facts if f.get("filed") == latest.get("filed")}
    return {
        "val": latest["val"], "accn": latest.get("accn"), "form": latest.get("form"),
        "end": latest.get("end"), "filed": latest.get("filed"),
        "multi_class_signal": len(same_period) > 1,
        "distinct_values_same_filing": sorted(same_period),
    }


def _ma_filing_search(cik: int, cutoff_date: str, months: int = 24) -> dict:
    """§7.2.1 (g): the frozen search record. Returns every flagged filing in the window plus the
    complete list of forms actually searched -- 'no search hit' is only evidence WITH this record."""
    from datetime import date

    payload = json.loads(_fetch(_SEC_SUBMISSIONS.format(cik=cik)))
    recent = payload.get("filings", {}).get("recent", {})
    forms = recent.get("form", [])
    dates = recent.get("filingDate", [])
    accns = recent.get("accessionNumber", [])
    docs = recent.get("primaryDocument", [])
    items = recent.get("items", [""] * len(forms))
    cy, cm, cd = (int(x) for x in cutoff_date.split("-"))
    y, m = cy - months // 12, cm
    window_start = date(y, m, min(cd, 28)).isoformat()

    searched, hits = [], []
    for n, form in enumerate(forms):
        filed = dates[n] if n < len(dates) else ""
        if not (window_start <= filed <= cutoff_date):
            continue
        rec = {"form": form, "filed": filed,
               "accession": accns[n] if n < len(accns) else None,
               "items": items[n] if n < len(items) else "",
               "primary_document": docs[n] if n < len(docs) else None}
        searched.append(rec)
        base = form.split("/")[0].strip().upper()
        if any(base == f.upper() or base.startswith(f.upper()) for f in tb.PENDING_MA_FORMS):
            if base == "8-K":
                flagged_items = {"1.01", "2.01"}
                if not (set(str(rec["items"]).split(",")) & flagged_items):
                    continue
            hits.append(rec)
    return {
        "window_start": window_start, "window_end": cutoff_date,
        "forms_searched_count": len(searched),
        "flagged_hits": hits,
        "retrieved_utc": _utc_now(),
    }


def stage_sec(tickers: list[str]) -> dict:
    """Market cap, primary-listing cross-check, and the pending-M&A search record for the named
    tickers. Classification of each flagged hit is a SEPARATE, evidence-based step -- this stage
    only produces the frozen search record §7.2.1 (g) requires."""
    universe = json.loads((ARTIFACT_DIR / "candidate-universe.json").read_text())
    price_adv = json.loads((ARTIFACT_DIR / "price-adv.json").read_text())
    cutoff_date = universe["screening_cutoff_utc"][:10]
    dir_exch = {c["ticker"]: c["exchange"] for c in universe["candidates"]}
    closes = {r["ticker"]: r["price"] for r in price_adv["results"]}

    index = _sec_ticker_index()
    out_rows = []
    for tic in tickers:
        entry = index.get(tic)
        if entry is None:
            out_rows.append({"ticker": tic, "sec_lookup": "ticker_not_in_sec_index",
                             "market_cap": tb.evaluate_market_cap(None, None),
                             "listing": tb.evaluate_primary_listing(dir_exch.get(tic), None)})
            continue
        cik = entry["cik"]
        time.sleep(_SEC_PAUSE_SECONDS)
        shares = _latest_shares_fact(cik, cutoff_date)
        time.sleep(_SEC_PAUSE_SECONDS)
        ma = _ma_filing_search(cik, cutoff_date)
        price = closes.get(tic, {})
        multi = bool(shares and shares["multi_class_signal"]) or len(entry["tickers_for_cik"]) > 1
        cap = tb.evaluate_market_cap(
            shares["val"] if shares else None, price.get("close"),
            multi_class=multi, cik=f"{cik:010d}",
            accession=shares.get("accn") if shares else None,
            concept="dei:EntityCommonStockSharesOutstanding",
            fact_period_end=shares.get("end") if shares else None,
            filing_date=shares.get("filed") if shares else None,
            price_session=price.get("session"), price_source=price.get("source"),
        )
        listing = tb.evaluate_primary_listing(dir_exch.get(tic), entry["sec_exchange"])
        out_rows.append({
            "ticker": tic, "cik": f"{cik:010d}", "tickers_for_cik": entry["tickers_for_cik"],
            "sec_exchange_raw": entry["sec_exchange_raw"], "shares_fact": shares,
            "market_cap": cap, "listing": listing, "ma_search": ma,
        })
    out = {"spec_revision": "r10", "stage": "sec_evidence",
           "screening_cutoff_utc": universe["screening_cutoff_utc"],
           "evaluated_count": len(out_rows), "rows": out_rows}
    path = ARTIFACT_DIR / "sec-evidence.json"
    prior = json.loads(path.read_text())["rows"] if path.exists() else []
    seen = {r["ticker"] for r in out_rows}
    out["rows"] = [r for r in prior if r["ticker"] not in seen] + out_rows
    out["evaluated_count"] = len(out["rows"])
    path.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    return out

if __name__ == "__main__":
    raise SystemExit(main())
