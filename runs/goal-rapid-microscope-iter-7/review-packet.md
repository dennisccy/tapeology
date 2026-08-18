# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 8. Shown in full: 8.

```diff
diff --git a/apps/backend/app/providers/adapters/alpaca.py b/apps/backend/app/providers/adapters/alpaca.py
index 3a3037c..e09209f 100644
--- a/apps/backend/app/providers/adapters/alpaca.py
+++ b/apps/backend/app/providers/adapters/alpaca.py
@@ -166,6 +166,32 @@ def _to_iso_utc(value) -> str | None:
     return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
 
 
+def _venue_str(value) -> str | None:
+    """Coerce a vendor venue/exchange value to a plain vendor-neutral string (Card-5.1
+    preservation, era "The Rapid Microscope" J-06 step 1). The SDK's ``Trade``/``Quote`` models
+    type ``exchange``/``bid_exchange``/``ask_exchange`` as ``Optional[Union[Exchange, str]]`` —
+    ``Exchange`` is a ``str, Enum`` mixin whose bare ``str()`` yields ``"Exchange.Q"`` (the member
+    repr, NOT the letter), so this reads ``.value`` when present (an ``Exchange`` member) and
+    falls back to the value itself (already a plain str, or ``None``). No vendor type ever leaks
+    past this seam."""
+    if value is None:
+        return None
+    return getattr(value, "value", value)
+
+
+def _conditions_list(value) -> list[str] | None:
+    """Coerce a vendor conditions value to a plain ``list[str]`` (Card-5.1 preservation). The
+    SDK types ``conditions`` as ``Optional[Union[List[str], str]]`` — a lone code sometimes
+    arrives as a bare string rather than a one-element list; this normalizes both shapes so every
+    ``RawTrade``/``RawQuote.conditions`` is uniform. ``None`` passes through (never an empty list
+    standing in for "absent")."""
+    if value is None:
+        return None
+    if isinstance(value, str):
+        return [value]
+    return list(value)
+
+
 @contextmanager
 def _mapped_vendor_timeout(detail: str = "market data provider timed out"):
     """Map the vendor SDK's HTTP timeout to the NEUTRAL ``VendorTimeout`` (J-28).
@@ -366,7 +392,13 @@ class AlpacaAdapter:
             trades_resp, quotes_resp = t_future.result(), q_future.result()
 
         trades = [
-            RawTrade(t.timestamp.timestamp(), float(t.price), int(t.size))
+            RawTrade(
+                t.timestamp.timestamp(), float(t.price), int(t.size),
+                conditions=_conditions_list(getattr(t, "conditions", None)),
+                exchange=_venue_str(getattr(t, "exchange", None)),
+                tape=getattr(t, "tape", None),
+                trade_id=getattr(t, "id", None),
+            )
             for t in trades_resp.data.get(symbol, [])
         ]
         quotes = [
@@ -376,6 +408,10 @@ class AlpacaAdapter:
                 float(q.ask_price),
                 int(q.bid_size),
                 int(q.ask_size),
+                conditions=_conditions_list(getattr(q, "conditions", None)),
+                tape=getattr(q, "tape", None),
+                bid_exchange=_venue_str(getattr(q, "bid_exchange", None)),
+                ask_exchange=_venue_str(getattr(q, "ask_exchange", None)),
             )
             for q in quotes_resp.data.get(symbol, [])
         ]
@@ -472,7 +508,13 @@ class AlpacaAdapter:
 
         for trades_resp, quotes_resp in sub_results:
             trades.extend(
-                RawTrade(t.timestamp.timestamp(), float(t.price), int(t.size))
+                RawTrade(
+                    t.timestamp.timestamp(), float(t.price), int(t.size),
+                    conditions=_conditions_list(getattr(t, "conditions", None)),
+                    exchange=_venue_str(getattr(t, "exchange", None)),
+                    tape=getattr(t, "tape", None),
+                    trade_id=getattr(t, "id", None),
+                )
                 for t in trades_resp.data.get(symbol, [])
             )
             quotes.extend(
@@ -482,6 +524,10 @@ class AlpacaAdapter:
                     float(q.ask_price),
                     int(q.bid_size),
                     int(q.ask_size),
+                    conditions=_conditions_list(getattr(q, "conditions", None)),
+                    tape=getattr(q, "tape", None),
+                    bid_exchange=_venue_str(getattr(q, "bid_exchange", None)),
+                    ask_exchange=_venue_str(getattr(q, "ask_exchange", None)),
                 )
                 for q in quotes_resp.data.get(symbol, [])
             )
@@ -677,7 +723,19 @@ class AlpacaAdapter:
         )
 
         async def _on_trade(t) -> None:
-            await queue.put(RawTrade(t.timestamp.timestamp(), float(t.price), int(t.size)))
+            # Same Card-5.1 preservation fields as the historical fetch (trivial to populate here
+            # too, since the SDK's live callback objects carry the identical attribute shape) —
+            # never persisted (the live path is never recorded to a dataset), so this is purely
+            # for consistency, not new plumbing (no new import, no new store write).
+            await queue.put(
+                RawTrade(
+                    t.timestamp.timestamp(), float(t.price), int(t.size),
+                    conditions=_conditions_list(getattr(t, "conditions", None)),
+                    exchange=_venue_str(getattr(t, "exchange", None)),
+                    tape=getattr(t, "tape", None),
+                    trade_id=getattr(t, "id", None),
+                )
+            )
 
         async def _on_quote(q) -> None:
             await queue.put(
@@ -687,6 +745,10 @@ class AlpacaAdapter:
                     float(q.ask_price),
                     int(q.bid_size),
                     int(q.ask_size),
+                    conditions=_conditions_list(getattr(q, "conditions", None)),
+                    tape=getattr(q, "tape", None),
+                    bid_exchange=_venue_str(getattr(q, "bid_exchange", None)),
+                    ask_exchange=_venue_str(getattr(q, "ask_exchange", None)),
                 )
             )
 
diff --git a/apps/backend/app/providers/adapters/base.py b/apps/backend/app/providers/adapters/base.py
index 72ae76c..71f86f1 100644
--- a/apps/backend/app/providers/adapters/base.py
+++ b/apps/backend/app/providers/adapters/base.py
@@ -63,22 +63,44 @@ def split_window(start, end, chunk_seconds: float) -> list[tuple]:
 
 @dataclass(frozen=True)
 class RawTrade:
-    """A vendor-neutral executed trade: UTC epoch seconds, price, size."""
+    """A vendor-neutral executed trade: UTC epoch seconds, price, size.
+
+    The four trailing fields are the Card-5.1 data-preservation prerequisite (era "The Rapid
+    Microscope" J-06 step 1, ``docs/rapid-validation-spec.md`` section 7.1 r2) — OPTIONAL,
+    default-``None`` immutable vendor identifiers populated ONLY when the concrete adapter's SDK
+    response actually carries them: ``conditions`` (the trade condition codes), ``exchange`` (the
+    venue the trade occurred on), ``tape``, and ``trade_id`` (the vendor's own trade id — named
+    ``trade_id`` rather than ``id`` to avoid shadowing the builtin). Absent-key backward
+    compatible: every existing construction call site (none of which pass these) is unaffected,
+    and the frozen engine never reads them (they exist for research consumers only)."""
 
     epoch: float
     price: float
     size: int
+    conditions: list[str] | None = None
+    exchange: str | None = None
+    tape: str | None = None
+    trade_id: int | None = None
 
 
 @dataclass(frozen=True)
 class RawQuote:
-    """A vendor-neutral top-of-book quote: UTC epoch seconds, bid/ask and their sizes."""
+    """A vendor-neutral top-of-book quote: UTC epoch seconds, bid/ask and their sizes.
+
+    The four trailing fields are the SAME Card-5.1 preservation prerequisite ``RawTrade`` carries
+    (see its docstring), quote-shaped: ``conditions`` (the quote condition codes), ``tape``, and
+    the bid/ask venue equivalents ``bid_exchange``/``ask_exchange`` — optional, default-``None``,
+    populated only when the adapter's SDK response provides them."""
 
     epoch: float
     bid: float
     ask: float
     bid_size: int
     ask_size: int
+    conditions: list[str] | None = None
+    tape: str | None = None
+    bid_exchange: str | None = None
+    ask_exchange: str | None = None
 
 
 @dataclass(frozen=True)
diff --git a/apps/backend/app/providers/base.py b/apps/backend/app/providers/base.py
index bfe3a75..e85b82e 100644
--- a/apps/backend/app/providers/base.py
+++ b/apps/backend/app/providers/base.py
@@ -29,6 +29,12 @@ class TradeEvent:
     engine re-derives the authoritative aggressor side from the quote in effect at
     ``timestamp`` via the aggressor classifier. ``timestamp`` is a logical second offset
     — never wall-clock — so the engine stays deterministic.
+
+    The four trailing fields mirror ``RawTrade``'s own Card-5.1 preservation fields (era "The
+    Rapid Microscope" J-06 step 1, spec section 7.1 r2) — optional, default-``None``, threaded
+    straight through from the historical provider's ``RawTrade`` when present. The engine ignores
+    them entirely (``FEATURE_NAMES`` and the classifier read only ``price``/``size``/``side``);
+    they exist for research consumers (the dataset store's stored rows) only.
     """
 
     ticker: str
@@ -36,11 +42,19 @@ class TradeEvent:
     price: float
     size: int
     side: Side = Side.UNKNOWN
+    conditions: list[str] | None = None
+    exchange: str | None = None
+    tape: str | None = None
+    trade_id: int | None = None
 
 
 @dataclass(frozen=True)
 class QuoteEvent:
-    """Top-of-book quote (best bid / best ask and their sizes)."""
+    """Top-of-book quote (best bid / best ask and their sizes).
+
+    The four trailing fields mirror ``RawQuote``'s own Card-5.1 preservation fields (see
+    ``TradeEvent``'s docstring) — optional, default-``None``, engine-ignored, research-only.
+    """
 
     ticker: str
     timestamp: float
@@ -48,6 +62,10 @@ class QuoteEvent:
     ask: float
     bid_size: int
     ask_size: int
+    conditions: list[str] | None = None
+    tape: str | None = None
+    bid_exchange: str | None = None
+    ask_exchange: str | None = None
 
 
 # Reserved for a later iteration (Level 2). Declared so the union/interface can grow
diff --git a/apps/backend/app/providers/historical.py b/apps/backend/app/providers/historical.py
index f17f179..4ff3bb6 100644
--- a/apps/backend/app/providers/historical.py
+++ b/apps/backend/app/providers/historical.py
@@ -68,10 +68,16 @@ class HistoricalProvider:
             ts = epoch - t0  # logical seconds, monotonic non-decreasing
             if kind == _QUOTE_ORDER:
                 yield QuoteEvent(
-                    self.ticker, ts, record.bid, record.ask, record.bid_size, record.ask_size
+                    self.ticker, ts, record.bid, record.ask, record.bid_size, record.ask_size,
+                    conditions=record.conditions, tape=record.tape,
+                    bid_exchange=record.bid_exchange, ask_exchange=record.ask_exchange,
                 )
             else:
-                yield TradeEvent(self.ticker, ts, record.price, record.size, Side.UNKNOWN)
+                yield TradeEvent(
+                    self.ticker, ts, record.price, record.size, Side.UNKNOWN,
+                    conditions=record.conditions, exchange=record.exchange,
+                    tape=record.tape, trade_id=record.trade_id,
+                )
 
 
 class ProgressiveHistoricalProvider:
@@ -132,7 +138,13 @@ class ProgressiveHistoricalProvider:
             ts = epoch - t0  # logical seconds, monotonic non-decreasing across the whole window
             if kind == _QUOTE_ORDER:
                 yield QuoteEvent(
-                    self.ticker, ts, record.bid, record.ask, record.bid_size, record.ask_size
+                    self.ticker, ts, record.bid, record.ask, record.bid_size, record.ask_size,
+                    conditions=record.conditions, tape=record.tape,
+                    bid_exchange=record.bid_exchange, ask_exchange=record.ask_exchange,
                 )
             else:
-                yield TradeEvent(self.ticker, ts, record.price, record.size, Side.UNKNOWN)
+                yield TradeEvent(
+                    self.ticker, ts, record.price, record.size, Side.UNKNOWN,
+                    conditions=record.conditions, exchange=record.exchange,
+                    tape=record.tape, trade_id=record.trade_id,
+                )
diff --git a/apps/backend/app/research/datasets.py b/apps/backend/app/research/datasets.py
index 76f7861..89e36a9 100644
--- a/apps/backend/app/research/datasets.py
+++ b/apps/backend/app/research/datasets.py
@@ -60,6 +60,7 @@ from ..providers.base import Event, QuoteEvent, Side, TradeEvent
 from ..providers.historical import HistoricalProvider
 from .dataset_index import DatasetIndex
 from .feed_basis import data_feed_for_scenario
+from .micro_features import QUOTE_SIZE_UNITS
 
 # The frozen split vocabulary (assigned at registration, immutable forever after).
 SPLIT_TRAIN = "train"
@@ -150,16 +151,34 @@ def _iso_utc(epoch: float) -> str:
 
 def _event_to_row(event: Event) -> dict:
     """One provider-neutral stored row per engine event (TradeEvent/QuoteEvent fields only —
-    never a vendor payload). The dataset-level ``symbol`` owns the ticker; rows do not repeat it."""
+    never a vendor payload). The dataset-level ``symbol`` owns the ticker; rows do not repeat it.
+
+    era "The Rapid Microscope" J-06 step 1 (spec section 7.1 r2): the Card-5.1 preservation
+    fields (``conditions``/``exchange``/``tape``/``trade_id`` on a trade row;
+    ``conditions``/``tape``/``bid_exchange``/``ask_exchange`` on a quote row) are emitted
+    PRESENT-ONLY — a key is added ONLY when the source event carries a non-``None`` value. An
+    event built with every new field ``None`` (every call site before J-06 steps 2-5 land the
+    recorder) serializes to the EXACT SAME row shape as before this change — never an emitted
+    ``"conditions": null`` for a field that used to be absent entirely (the ``observer=``-kwarg
+    absent-key precedent, applied to stored rows)."""
     if isinstance(event, TradeEvent):
-        return {
+        row = {
             "type": _ROW_TRADE,
             "ts": event.timestamp,
             "price": event.price,
             "size": event.size,
             "side": event.side.value,
         }
-    return {
+        if event.conditions is not None:
+            row["conditions"] = list(event.conditions)
+        if event.exchange is not None:
+            row["exchange"] = event.exchange
+        if event.tape is not None:
+            row["tape"] = event.tape
+        if event.trade_id is not None:
+            row["trade_id"] = event.trade_id
+        return row
+    row = {
         "type": _ROW_QUOTE,
         "ts": event.timestamp,
         "bid": event.bid,
@@ -167,13 +186,39 @@ def _event_to_row(event: Event) -> dict:
         "bid_size": event.bid_size,
         "ask_size": event.ask_size,
     }
+    if event.conditions is not None:
+        row["conditions"] = list(event.conditions)
+    if event.tape is not None:
+        row["tape"] = event.tape
+    if event.bid_exchange is not None:
+        row["bid_exchange"] = event.bid_exchange
+    if event.ask_exchange is not None:
+        row["ask_exchange"] = event.ask_exchange
+    return row
 
 
 def _row_to_event(symbol: str, row: dict) -> Event:
+    """The exact inverse of ``_event_to_row``. ``row.get(...)`` (never ``row[...]``) on every
+    Card-5.1 preservation field: a legacy row that predates this change simply lacks the key, so
+    every one of the four fields defaults cleanly to ``None`` — the narrow risk surface the
+    iteration-6 evaluator flagged as this era's most dangerous change so far. Round-trips exactly
+    for a row that DOES carry them (TC-2)."""
     if row["type"] == _ROW_TRADE:
-        return TradeEvent(symbol, row["ts"], row["price"], row["size"], Side(row["side"]))
+        return TradeEvent(
+            symbol, row["ts"], row["price"], row["size"], Side(row["side"]),
+            conditions=row.get("conditions"),
+            exchange=row.get("exchange"),
+            tape=row.get("tape"),
+            trade_id=row.get("trade_id"),
+        )
     if row["type"] == _ROW_QUOTE:
-        return QuoteEvent(symbol, row["ts"], row["bid"], row["ask"], row["bid_size"], row["ask_size"])
+        return QuoteEvent(
+            symbol, row["ts"], row["bid"], row["ask"], row["bid_size"], row["ask_size"],
+            conditions=row.get("conditions"),
+            tape=row.get("tape"),
+            bid_exchange=row.get("bid_exchange"),
+            ask_exchange=row.get("ask_exchange"),
+        )
     raise DatasetIntegrityError(f"unknown stored event type {row.get('type')!r}")
 
 
@@ -414,12 +459,30 @@ class DatasetStore:
         data_feed: str,
         epoch_anchor: float | None,
         events: list[Event],
+        schema_basis: str | None = None,
+        quote_size_unit: str | None = None,
     ) -> dict:
         """Persist ONE new dataset (record + register in a single explicit action). The split tag
         is assigned HERE and frozen: content already registered under any split raises the
-        409-style ``DatasetAlreadyRegistered`` (there is no update/re-tag/delete path at all)."""
+        409-style ``DatasetAlreadyRegistered`` (there is no update/re-tag/delete path at all).
+
+        ``schema_basis``/``quote_size_unit`` (era "The Rapid Microscope" J-06 step 1, spec
+        section 2.6) are OPTIONAL, additive manifest fields — stamped into ``meta`` only when a
+        caller supplies them (the ``observer=``-kwarg precedent: every existing call site, none
+        of which pass these, leaves the manifest shape byte-unchanged, TC-3). Neither is part of
+        the CONTENT checksum (``_content_checksum`` hashes ``symbol``/``data_feed``/
+        ``epoch_anchor``/``events`` only) — they are manifest metadata, not tape content. A
+        supplied ``quote_size_unit`` is validated against the EXISTING
+        ``micro_features.QUOTE_SIZE_UNITS`` tuple (the sole unit vocabulary in the repo — this
+        module defines no second one) and rejected explicitly, never silently accepted, exactly
+        like the ``split`` check immediately below."""
         if split not in VALID_SPLITS:
             raise ValueError(f"unknown split {split!r} — expected one of {sorted(VALID_SPLITS)}")
+        if quote_size_unit is not None and quote_size_unit not in QUOTE_SIZE_UNITS:
+            raise ValueError(
+                f"unknown quote_size_unit {quote_size_unit!r} — expected one of "
+                f"{sorted(QUOTE_SIZE_UNITS)} (micro_features.QUOTE_SIZE_UNITS, spec section 2.6)"
+            )
         if not events:
             raise EmptyWindowError("no events in the requested window — nothing was recorded")
         rows = [_event_to_row(event) for event in events]
@@ -450,6 +513,10 @@ class DatasetStore:
             "epoch_anchor": epoch_anchor,
             "created_utc": _iso_utc(datetime.now(timezone.utc).timestamp()),
         }
+        if schema_basis is not None:
+            meta["schema_basis"] = schema_basis
+        if quote_size_unit is not None:
+            meta["quote_size_unit"] = quote_size_unit
         record = {"meta": meta, "events": rows}
         payload = {"file_checksum": _sha256(_canonical(record)), "record": record}
         self._root.mkdir(parents=True, exist_ok=True)
@@ -518,9 +585,15 @@ def record_from_source(
     end: str | None = None,
     config: Config,
     historical_fetch: Callable[[], HistoricalWindow] | None = None,
+    schema_basis: str | None = None,
+    quote_size_unit: str | None = None,
 ) -> dict:
     """Record + register ONE dataset from a historical source (the explicit research action).
 
+    ``schema_basis``/``quote_size_unit`` (era "The Rapid Microscope" J-06 step 1) pass straight
+    through to ``DatasetStore.record`` — see that method's own docstring; omitted by every
+    existing caller (none pass these yet), so the manifest shape is byte-unchanged for them.
+
     ``reference`` loads the committed keyless PG SIP fixture (optionally sliced to
     ``[start, end)``); ``historical`` calls the injected ``historical_fetch`` built on the
     EXISTING neutral adapter seam (credentials / no-data / timeouts surface that seam's explicit
@@ -561,6 +634,8 @@ def record_from_source(
         data_feed=data_feed_for_scenario(scenario, config),
         epoch_anchor=provider.epoch_anchor,
         events=events,
+        schema_basis=schema_basis,
+        quote_size_unit=quote_size_unit,
     )
 
 
diff --git a/apps/backend/app/research/walkforward.py b/apps/backend/app/research/walkforward.py
index c580fce..c2f14fc 100644
--- a/apps/backend/app/research/walkforward.py
+++ b/apps/backend/app/research/walkforward.py
@@ -152,6 +152,7 @@ __all__ = [
     "TICK_LEGACY_CORPUS_ID",
     "playbook_observations",
     "run_diagnostic_walkforward",
+    "run_tick_family_fold_request",
     "main",
 ]
 
@@ -1001,6 +1002,50 @@ def _tick_dataset_session_dates(dataset_store: DatasetStore) -> list[str]:
     return sorted(session_dates)
 
 
+def run_tick_family_fold_request(ledger: WalkForwardLedger, config: Config) -> dict:
+    """The tick-family fold request (goal.md J-05, iter-7) — the genuine production entry point
+    goal.md's own acceptance clause names: "the tick-family fold request returns the typed
+    floor-refusal naming `11 < 105`". Before this function, the ONE production fold-building call
+    site (``run_diagnostic_walkforward``) was hardcoded to the playbook corpus, so that sentence
+    was proven only by a synthetic-date unit test, never by a genuine caller against the real
+    tick corpus (iter-6 evaluator's own finding).
+
+    Resolves the REAL legacy tick corpus's session dates via the EXISTING
+    ``_tick_dataset_session_dates`` helper (no second inventory mechanism) against a fresh
+    ``DatasetStore`` pointed at ``config.dataset_dir_resolved()``, registers
+    ``DIAGNOSTIC_GEOMETRY`` for ``TICK_LEGACY_CORPUS_ID`` (mirroring
+    ``run_diagnostic_walkforward``'s own register-then-check ordering immediately above its
+    ``build_folds`` call, so the frozen geometry is committed to the ledger even for a
+    below-floor corpus — idempotent on repeat calls via ``register_fold_spec``'s own "identical
+    geometry replays the existing row" contract), then calls the ALREADY-WIRED
+    ``require_sufficient_sessions_for_folds`` (TR-15).
+
+    At today's real corpus (11 distinct ET session dates, far under the 105-session
+    ``WF_MIN_SUFFICIENT_FOLDS`` floor) this ALWAYS raises ``InsufficientSessionsForFoldsError``
+    naming the exact shortfall — the typed refusal IS this function's whole acceptance surface
+    (T-7 "insufficient is an answer"), never a bug to work around. Evaluating actual folds over
+    the tick corpus (a tick-level "observations" reader, evidence-class classification,
+    ``evaluate_mode_b_fold``) is J-06/J-09 scope — the corpus cannot clear this floor until the
+    recorder (J-06) grows it, so that machinery is deliberately NOT built here (T-1: never invent
+    a code path this iteration's diff cannot exercise or verify)."""
+    tick_dataset_store = DatasetStore(config.dataset_dir_resolved())
+    session_dates = _tick_dataset_session_dates(tick_dataset_store)
+    corpus_manifest_hash = _sha256(_canonical(session_dates))
+    floors = {
+        "wf_fold_min_observations": WF_FOLD_MIN_OBSERVATIONS,
+        "wf_fold_min_signal_sessions": WF_FOLD_MIN_SIGNAL_SESSIONS,
+        "wf_fold_min_symbols": WF_FOLD_MIN_SYMBOLS,
+    }
+    register_fold_spec(
+        ledger, corpus_id=TICK_LEGACY_CORPUS_ID, corpus_manifest_hash=corpus_manifest_hash,
+        geometry=DIAGNOSTIC_GEOMETRY, floors=floors,
+    )
+    require_sufficient_sessions_for_folds(session_dates, DIAGNOSTIC_GEOMETRY)
+    # Unreachable at today's 11-session corpus (the line above always raises first); kept minimal
+    # (no `build_folds`/fold-evaluation call) rather than a speculative branch nothing can test.
+    return {"corpus_id": TICK_LEGACY_CORPUS_ID, "session_count": len(session_dates)}
+
+
 def playbook_observations(
     playbook_store, *, setup_ids: tuple[str, ...], horizon_label: str, default_signature: str, exclude_session_dates: tuple[str, ...] = ()
 ) -> list[dict]:
@@ -1198,12 +1243,27 @@ def main() -> int:
     """``python -m app.research.walkforward --diagnostic`` -- runs the diagnostic acceptance run
     against the operator's REAL playbook/universe/bar stores, synchronously, in-process (the
     ``scout``/``micro_snapshots`` CLI-warmer precedent), persisting through the SAME ledger
-    ``GET /research/desk/micro/walkforward`` serves."""
+    ``GET /research/desk/micro/walkforward`` serves.
+
+    ``--family tick_legacy`` (iter-7, goal.md J-05) is a SEPARATE mode: requests a fold build for
+    the real legacy tick corpus via ``run_tick_family_fold_request`` instead of the diagnostic
+    playbook run -- today this always prints the typed below-floor refusal (e.g. "11 < 105"),
+    since the tick corpus does not yet clear ``WF_MIN_SUFFICIENT_FOLDS``. Route-level wiring
+    (``POST /walkforward/compute``'s own family parameter) is deferred -- CLI-only this
+    iteration, since no UI/MCP consumer needs it yet."""
     parser = argparse.ArgumentParser(
         description="Walk-forward CLI warmer -- run the diagnostic acceptance run over the real "
         "155-session playbook corpus, persisting through the SAME ledger the walkforward routes serve."
     )
     parser.add_argument("--diagnostic", action="store_true", help="run the diagnostic acceptance run (the only mode this iteration).")
+    parser.add_argument(
+        "--family",
+        choices=["tick_legacy"],
+        default=None,
+        help="request a fold build for a named corpus family instead of --diagnostic. "
+        "'tick_legacy' resolves the real legacy tick corpus's session dates and requests its "
+        "fold build (today this always prints the typed below-floor refusal).",
+    )
     args = parser.parse_args()
 
     config = CONFIG
@@ -1213,8 +1273,23 @@ def main() -> int:
     universe_store = UniverseStore(config.desk_universe_dir_resolved())
     bar_store = BarStore(config.bar_dir_resolved())
 
+    if args.family is not None:
+        try:
+            result = run_tick_family_fold_request(ledger, config)
+        except InsufficientSessionsForFoldsError as exc:
+            # TC-6/TC-7: the SAME typed-refusal print+exit shape as --diagnostic's own handling
+            # below -- never a second, divergent error path.
+            print(f"tick-family fold request refused ({args.family}): {exc}")
+            return 1
+        print(
+            f"tick-family fold request complete ({args.family}): {result['session_count']} "
+            f"session(s) clear the WF_MIN_SUFFICIENT_FOLDS floor for corpus "
+            f"'{result['corpus_id']}'."
+        )
+        return 0
+
     if not args.diagnostic:
-        print("nothing to do -- pass --diagnostic to run the acceptance run.")
+        print("nothing to do -- pass --diagnostic or --family tick_legacy.")
         return 0
 
     try:
diff --git a/apps/backend/tests/test_datasets.py b/apps/backend/tests/test_datasets.py
index 2cf6c1d..6ae7ae6 100644
--- a/apps/backend/tests/test_datasets.py
+++ b/apps/backend/tests/test_datasets.py
@@ -27,6 +27,7 @@ Locked disciplines (each an anti-goal or a J-02 acceptance clause):
 
 from __future__ import annotations
 
+import ast
 import json
 import os
 import time
@@ -38,6 +39,7 @@ import pytest
 from app.config import CONFIG, Config
 from app.engine.tape_engine import TapeEngine
 from app.providers.adapters.base import HistoricalWindow
+from app.providers.base import QuoteEvent, Side, TradeEvent
 from app.providers.historical import HistoricalProvider
 from app.research.datasets import (
     SPLIT_HOLDOUT,
@@ -453,3 +455,127 @@ def test_dataset_dir_env_override_wins(monkeypatch):
     monkeypatch.delenv("TAPEOLOGY_DATASET_DIR")
     default = CONFIG.dataset_dir_resolved()
     assert default.endswith(str(Path(".data") / "datasets"))
+
+
+# --- era "The Rapid Microscope" J-06 step 1 (spec section 7.1/2.6 r2): the Card-5.1 data- -------
+# --- preservation prerequisite -- TC-1, TC-2, TC-3, TC-9 (docs/phases/goal-rapid-microscope- -----
+# --- iter-7.md). This is the era's most dangerous change so far (iteration-6 evaluator's own -----
+# --- words): it mutates the shared event/row schema every dataset-reading journey depends on. ---
+
+
+def test_tc1_an_event_with_every_new_field_absent_serializes_to_the_pre_change_row_shape(tmp_path):
+    """TC-1 (backward compatibility, the narrow risk surface): an event built the way EVERY call
+    site built one before this iteration (every Card-5.1 field left at its default ``None``)
+    must serialize to the EXACT same row shape legacy data already has on disk -- no
+    ``conditions``/``exchange``/``tape``/``trade_id`` key on a trade row, no
+    ``conditions``/``tape``/``bid_exchange``/``ask_exchange`` key on a quote row, and no
+    ``schema_basis``/``quote_size_unit`` key in the manifest -- ever appearing for an absent
+    value. Reloading must reconstruct byte-identical events (the ``_row_to_event`` half of the
+    same round trip the 18 real on-disk datasets exercise)."""
+    store = DatasetStore(tmp_path / "datasets")
+    events = [
+        QuoteEvent("PG", 0.0, 148.49, 148.53, 700, 100),
+        TradeEvent("PG", 0.02, 148.53, 100, Side.UNKNOWN),
+    ]
+    meta = store.record(
+        symbol="PG", source="test", source_kind="reference", source_id="",
+        split=SPLIT_TRAIN, window_start_utc="2026-06-09T17:00:00Z",
+        window_end_utc="2026-06-09T17:00:01Z", data_feed="sip", epoch_anchor=0.0, events=events,
+    )
+    assert "schema_basis" not in meta
+    assert "quote_size_unit" not in meta
+
+    on_disk = json.loads((tmp_path / "datasets" / f"{meta['id']}.json").read_text())
+    rows = on_disk["record"]["events"]
+    trade_row = next(r for r in rows if r["type"] == "trade")
+    quote_row = next(r for r in rows if r["type"] == "quote")
+    for key in ("conditions", "exchange", "tape", "trade_id"):
+        assert key not in trade_row, f"trade row unexpectedly carries {key!r} for an absent value"
+    for key in ("conditions", "tape", "bid_exchange", "ask_exchange"):
+        assert key not in quote_row, f"quote row unexpectedly carries {key!r} for an absent value"
+
+    assert store.load_events(meta["id"]) == events
+
+
+def test_tc2_preservation_fields_round_trip_exactly_through_record_and_load_events(tmp_path):
+    """TC-2: a freshly constructed TradeEvent/QuoteEvent carrying real preservation values
+    round-trips through ``record()`` -> ``load_events()`` with every field equal to the
+    original."""
+    store = DatasetStore(tmp_path / "datasets")
+    trade = TradeEvent(
+        "PG", 0.02, 148.53, 100, Side.UNKNOWN,
+        conditions=["@", "I"], exchange="Q", tape="C", trade_id=123456789,
+    )
+    quote = QuoteEvent(
+        "PG", 0.0, 148.49, 148.53, 700, 100,
+        conditions=["R"], tape="C", bid_exchange="P", ask_exchange="Q",
+    )
+    meta = store.record(
+        symbol="PG", source="test", source_kind="reference", source_id="",
+        split=SPLIT_TRAIN, window_start_utc="2026-06-09T17:00:00Z",
+        window_end_utc="2026-06-09T17:00:01Z", data_feed="sip", epoch_anchor=0.0,
+        events=[quote, trade],
+    )
+    reloaded = store.load_events(meta["id"])
+    reloaded_trade = next(e for e in reloaded if isinstance(e, TradeEvent))
+    reloaded_quote = next(e for e in reloaded if isinstance(e, QuoteEvent))
+    assert reloaded_trade == trade
+    assert reloaded_quote == quote
+
+
+def test_tc3_schema_basis_and_quote_size_unit_are_stamped_verbatim_when_supplied(tmp_path):
+    """TC-3: ``record(..., schema_basis=..., quote_size_unit=...)`` stamps both into the manifest
+    verbatim and they survive a store reload; an unrecognised ``quote_size_unit`` (outside
+    ``micro_features.QUOTE_SIZE_UNITS``) is rejected explicitly, never silently accepted."""
+    store = DatasetStore(tmp_path / "datasets")
+    meta = store.record(
+        symbol="PG", source="test", source_kind="reference", source_id="",
+        split=SPLIT_TRAIN, window_start_utc="2026-06-09T17:00:00Z",
+        window_end_utc="2026-06-09T17:00:01Z", data_feed="sip", epoch_anchor=0.0,
+        events=[TradeEvent("PG", 0.0, 148.53, 100, Side.UNKNOWN)],
+        schema_basis="v2_preservation", quote_size_unit="shares",
+    )
+    assert meta["schema_basis"] == "v2_preservation"
+    assert meta["quote_size_unit"] == "shares"
+
+    reloaded = DatasetStore(tmp_path / "datasets").get(meta["id"])
+    assert reloaded["schema_basis"] == "v2_preservation"
+    assert reloaded["quote_size_unit"] == "shares"
+
+    with pytest.raises(ValueError):
+        store.record(
+            symbol="PG", source="test2", source_kind="reference", source_id="",
+            split=SPLIT_TRAIN, window_start_utc="2026-06-09T17:01:00Z",
+            window_end_utc="2026-06-09T17:01:01Z", data_feed="sip", epoch_anchor=0.0,
+            events=[TradeEvent("PG", 0.0, 149.0, 50, Side.UNKNOWN)],
+            quote_size_unit="not-a-real-unit",
+        )
+
+
+def test_tc9_no_second_quote_size_unit_vocabulary_or_early_dated_rule_constant_exists():
+    """TC-9: ``micro_features.QUOTE_SIZE_UNITS`` stays the SOLE unit-vocabulary tuple in the repo
+    (this iteration validates against it, never defines a second copy), and
+    ``ALPACA_QUOTE_SIZE_UNIT_EFFECTIVE`` -- the dated-vendor-rule constant the assumption ledger's
+    iter-7 entry explicitly reserves for a future ``tick_recorder.py`` -- is not yet defined
+    anywhere. This iteration ships storage CAPABILITY only (a caller-supplied
+    ``schema_basis``/``quote_size_unit``), never the date-to-unit DECISION rule."""
+    app_dir = Path(__file__).resolve().parents[1] / "app"
+    offending_effective: list[str] = []
+    offending_second_tuple: list[str] = []
+    py_files = sorted(p for p in app_dir.rglob("*.py") if "__pycache__" not in p.parts)
+    assert len(py_files) > 50, f"only {len(py_files)} app modules scanned -- has the tree moved?"
+    for path in py_files:
+        tree = ast.parse(path.read_text(), filename=str(path))
+        for node in ast.walk(tree):
+            if isinstance(node, ast.Assign):
+                targets = [t.id for t in node.targets if isinstance(t, ast.Name)]
+            elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
+                targets = [node.target.id]
+            else:
+                continue
+            if "ALPACA_QUOTE_SIZE_UNIT_EFFECTIVE" in targets:
+                offending_effective.append(str(path.relative_to(app_dir)))
+            if "QUOTE_SIZE_UNITS" in targets and path.name != "micro_features.py":
+                offending_second_tuple.append(str(path.relative_to(app_dir)))
+    assert offending_effective == [], f"ALPACA_QUOTE_SIZE_UNIT_EFFECTIVE defined early: {offending_effective}"
+    assert offending_second_tuple == [], f"a second QUOTE_SIZE_UNITS assignment exists: {offending_second_tuple}"
diff --git a/apps/backend/tests/test_walkforward.py b/apps/backend/tests/test_walkforward.py
index a6aa1b4..681510a 100644
--- a/apps/backend/tests/test_walkforward.py
+++ b/apps/backend/tests/test_walkforward.py
@@ -1016,6 +1016,68 @@ def test_the_cli_with_no_flag_does_nothing(monkeypatch):
     assert wf.main() == 0
 
 
+# === iter-7 TC-6/TC-8: the tick-family fold request reaches a genuine production entry point ========
+# TC-7 (the SAME CLI path against the operator's real 11-distinct-date `.data/datasets` corpus) is a
+# manual, by-hand run -- see the dev handoff for its pasted output, per goal.md J-05's own wording
+# ("the developer runs by hand ... the evaluator independently re-runs this same command").
+
+
+def test_tc6_the_family_flag_prints_the_typed_refusal_naming_the_real_shortfall(tmp_path, monkeypatch, capsys):
+    """``python -m app.research.walkforward --family tick_legacy`` -- goal.md J-05's remaining
+    acceptance clause ("the tick-family fold request returns the typed floor-refusal naming
+    `11 < 105`") reached through a genuine production entry point, never a synthetic-date unit
+    test alone (unlike ``test_tc20_...`` below, which is left unmodified -- TC-8). Seeds 11
+    distinct-session-date tick fixture datasets under ``TAPEOLOGY_DATASET_DIR`` (the SAME
+    distinct-session-date count the real corpus and TC-20's own synthetic fixture both use) via
+    a real ``DatasetStore``, then runs the new CLI flag end to end against this hermetic store."""
+    import sys
+
+    tick_dir = tmp_path / "datasets"
+    tick_store = DatasetStore(str(tick_dir))
+    for day in range(1, 12):  # 11 distinct ET session dates -> 11 < 105
+        _plant_tick_dataset(
+            tick_store, symbol="AAPL",
+            window_start_utc=f"2026-06-{day:02d}T13:30:00Z",
+            window_end_utc=f"2026-06-{day:02d}T20:00:00Z",
+            price=100.00 + day,
+        )
+
+    monkeypatch.setenv("TAPEOLOGY_DATASET_DIR", str(tick_dir))
+    monkeypatch.setenv("TAPEOLOGY_DESK_UNIVERSE_DIR", str(tmp_path / "universe"))
+    monkeypatch.setenv("TAPEOLOGY_BAR_DIR", str(tmp_path / "bars"))
+    monkeypatch.setenv("TAPEOLOGY_MICRO_WALKFORWARD_DIR", str(tmp_path / "wf"))
+    monkeypatch.setenv("TAPEOLOGY_MICRO_EXPOSURE_REGISTRY_DIR", str(tmp_path / "exposure"))
+    monkeypatch.setattr(sys, "argv", ["walkforward.py", "--family", "tick_legacy"])
+
+    exit_code = wf.main()
+    assert exit_code != 0
+
+    captured = capsys.readouterr()
+    assert captured.err == ""  # never an unhandled traceback
+    assert "11 < 105" in captured.out
+    assert "TR-15" in captured.out
+
+    ledger = wl.WalkForwardLedger(str(tmp_path / "wf"))
+    assert ledger.rows_of_kind(wl.ROW_KIND_FOLD_RESULT) == []
+    # The fold spec IS registered (`register_fold_spec` fires before
+    # `require_sufficient_sessions_for_folds`, mirroring the diagnostic path's own ordering) --
+    # provenance even for a below-floor corpus, this iteration's own developer-call.
+    fold_spec = wl.latest_fold_spec(ledger, wf.TICK_LEGACY_CORPUS_ID)
+    assert fold_spec is not None
+    assert fold_spec["geometry"] == wf.DIAGNOSTIC_GEOMETRY
+
+
+def test_tc6_an_unknown_family_value_is_refused_by_argparse_itself(monkeypatch, capsys):
+    """A defensive edge: an unrecognised ``--family`` value never silently no-ops -- argparse's
+    own ``choices`` refusal fires before any store is touched."""
+    import sys
+
+    monkeypatch.setattr(sys, "argv", ["walkforward.py", "--family", "not-a-real-family"])
+    with pytest.raises(SystemExit) as exc_info:
+        wf.main()
+    assert exc_info.value.code != 0
+
+
 # === route wiring: the 3 walkforward routes actually work end to end (micro_routes.py) ===============
 
 
```

## Excluded-path stat (dependency/lockfile visibility)

 runs/goal-session-rapid-microscope/telemetry.jsonl   | 9 +++++++++
 runs/goal-session-rapid-microscope/trace/trace.jsonl | 2 ++
 2 files changed, 11 insertions(+)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
