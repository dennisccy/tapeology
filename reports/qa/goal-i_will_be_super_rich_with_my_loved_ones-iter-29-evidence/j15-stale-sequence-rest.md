# J-15 — Real live IEX feed: live → stale → live (canonical REST primary proof)

Source: live `IBM` watch through the running backend (creds loaded, market OPEN
Tue 2026-06-16 ~14:1x ET), polling the canonical `GET /tape/IBM/summary`
`stream_status` (data-contract row 6). The snapshot `timestamp` is the latest
real record's logical time; `recent_trades` is the count from `GET /tape/IBM/events`.

The watchdog (`watch_manager._feed_live`, `config.stale_gap_seconds = 10.0`) flips
to `stale` when NO real record (trade or quote) arrives within 10s, and recovers to
`live` on the next real record. No application code was changed to produce this.

## Observed (genuine, repeated cycles)

```
t=18s live   ts=2.707   (last record at 2.707; recovery cadence)
t=19s stale  ts=2.707   <-- >10s record gap -> flip to STALE; ts FROZEN
...   stale  ts=2.707   (no advance => no fabricated trades during lull)
t=26s live   ts=20.198  <-- real new record arrives -> recovery flip to LIVE
t=39s stale  ts=22.663  <-- next genuine lull
...
t=58s stale  ts=22.663
t=59s live   ts=52.971  <-- recovery
t=68-74 stale            (cycle)
t=90-96 stale            (cycle)
t=116-120 stale          (cycle)
```

## Recent-trades freeze proof (no fabrication during the gap)

```
t=1..15s  stale  ts=101.372  recent_trades=9   (FROZEN through the whole stale span)
t=16s     live   ts=151.389  recent_trades=9   (recovered on a real record; trades still 9)
```

The snapshot `timestamp` does NOT advance while `stale`, and the recent-trades count
stays frozen across the entire stale span — proving the engine fabricates no trade
during the lull and does no synthesized catch-up on resume (the no-fabricated-data
anti-goal, which is the heart of J-15). The recovery flip rejoins CURRENT real data.

## Authoritative pipeline proof

`TAPEOLOGY_LIVE_INTEGRATION=1 TAPEOLOGY_LIVE_SYMBOL=F .venv/bin/python -m pytest
tests/test_live_integration.py -v -s` => 1 passed (14.11s) against the real Alpaca
IEX socket: asserted stream_status == "live", event_count > 0, real bid/ask, valid
tape state, scenario == "live F".
