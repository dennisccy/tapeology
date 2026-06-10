# Goal iteration 2 — Implementation Summary

**Phase:** goal-i_will_be_super_rich_with_my_loved_ones-iter-2
**Date:** 2026-06-10
**Written by:** developer

---

## Features Implemented

- **Declare a thesis on the watched ticker**: while watching a ticker, the user can now declare a
  trade idea — one of four setup types (absorption reversal, trend continuation, level break-and-go,
  failed-move fade), a direction (long or short), and a required invalidation price — and watch the
  live tape judged against it.
- **Honest, explicit rejection of bad declarations**: an incoherent declaration is refused on screen
  with a plain reason and never silently fixed up. A thesis on a ticker that is not being watched is
  refused; a long thesis whose invalidation is not below the current price (or a short whose
  invalidation is not above it) is refused; a setup that needs a price level but was given none — or
  one that was given a level it does not use — is refused; an unknown setup or direction is refused;
  and a second thesis while one is already active is refused. Nothing is recorded when a declaration
  is refused.
- **Live "expected behaviour" read-out**: each declared thesis carries a frozen list of
  plain-language statements describing what the tape should do if the idea is valid. Each statement
  shows a live status — "met", "not yet", or "violated" — recomputed from the current tape read on
  every update.
- **A research record that survives**: every declared thesis and its timeline of judgements are
  written to a dedicated journal database (separate from any live tape data). The judgement timeline
  is append-only — entries are never edited or deleted.
- **Honest end-of-life for a thesis**: stopping the watch, the data stream ending, or a feed failure
  marks an active thesis "expired" with a final timeline entry. If the app is restarted while a
  thesis was still open (for example after a crash), a startup sweep marks it "expired" too — no
  thesis is ever left dangling as falsely "active".
- **One catalog, one source of labels**: the setup names, the rule for which setups need a price
  level, the statement wording, and the status/verdict labels all come from one backend catalog. The
  screen builds its form and its labels from that catalog — it invents none of them.
- **The thesis strip on the cockpit**: a new strip sits above the existing panel grid. When no
  thesis exists it is a single "Declare a thesis…" line that does not disturb the rest of the
  cockpit. When opened it becomes the declare form; once a thesis is declared it shows the active
  thesis, its statements with live statuses, a "Pending" badge, and an honesty stamp (the data source
  and feed it was declared on).

---

## Changed Behavior

- **The live stream now carries the active thesis**: the per-ticker live feed gained one extra piece
  of information — the active thesis (or "none"). The existing tape values (state, confidence,
  features, quote, trades, event log) are byte-for-byte unchanged whether a thesis exists or not.

---

## Backend-Only Items

- None. Everything built this iteration is reachable from the cockpit thesis strip. (The journal
  database stores extra tables — hints, actions, studies — that are created now but not written or
  surfaced yet; those belong to later iterations.)

---

## Incomplete Items

- **Verdict transitions** (confirming / weakening / rejecting / invalidated): intentionally deferred.
  This iteration the verdict stays "Pending" for every thesis; the engine that moves it through the
  other verdicts is the next iteration.
- **Entry risk flags**: intentionally omitted entirely (not shown as an empty list, which would
  falsely read as "no risks found"). Arrives in a later iteration.
- **Resolve / abandon / entry-and-exit marks / management stance / chart geometry / journal &
  studies pages**: all out of scope for this iteration per the spec; not built.

---

## Config and Environment Changes

- `TAPEOLOGY_JOURNAL_DB` — file path for the research journal database — default:
  `tapeology_journal.db` (created in the backend working directory; git-ignored). Set this to relocate
  the journal. The value `:memory:` is accepted for an in-process store. Tests inject a temporary
  path automatically, so the test suite never touches a real journal file.
- No database migration system is used — the full journal schema is created on first start and
  stamped with a schema version.

---

## Known Limitations

- The verdict badge always reads "Pending" this iteration by design; only the statement statuses
  change live. A reviewer/QA should expect "Pending" and should NOT treat it as a stuck value.
- The journal records research only — no trades, quotes, candles, or feature history are ever
  persisted there.
- When a watch is stopped, the one-time "expired" record is written from the live feed's callback
  rather than a background queue. It is a single small write and does not slow the per-event tape
  processing, but it is the one place a journal write happens on the feed's thread; if a future dense
  live feed shows lag here, it should be moved to a fire-and-forget write.
- Live-market behaviour for a real symbol still depends on vendor credentials and market hours
  (unchanged from prior iterations); the thesis feature itself works identically on simulated,
  historical, and live data, but was verified this iteration against the simulated `SIM-BIDABS`
  scenario and the live REST/WebSocket responses.
