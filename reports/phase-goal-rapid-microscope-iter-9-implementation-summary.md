# Goal Iteration 9 — Implementation Summary

**Phase:** goal-rapid-microscope-iter-9
**Date:** 2026-08-18
**Written by:** developer

---

## Features Implemented

- **The Validation Vault (storage + logic, no screen yet)**: the system can now keep a list of
  "recording plans" (which stocks, which dates, all decided and written down before any data is
  fetched) and, separately, track individual chunks of recorded data through a strict one-way
  lifecycle: **sealed → assigned → exposed**. "Sealed" means a chunk of data is locked away —
  nobody can see which stock or which date it covers, only a rough size category and a fingerprint
  that proves it hasn't been tampered with. It only becomes visible once it is formally "assigned"
  to a specific research question, and that assignment can happen at most once per chunk, ever —
  there is no way to look at a sealed chunk, decide you don't like what you see, and quietly ask
  again. This is the honesty mechanism that will let future research claim "this held up on data
  nobody could have peeked at first."
- **Which stock-days are secretly sealed, decided by an unpredictable coin flip.** The decision of
  which data chunks get sealed away is computed from a secret password-like value (never stored in
  the code or written to any log) combined with the stock symbol and date — so nobody, including
  the system operator, can predict or influence which chunks end up locked away before they exist.
- **A new read-only status page endpoint** (`GET /research/desk/micro/vault`) that shows the
  current state of every recording plan and every tracked data chunk — but, faithfully, shows
  almost nothing about a chunk that is still sealed (no stock name, no date, no exact count of
  trades — just "there's something here, roughly this big, sealed since this time"). Nothing
  renders this on a screen yet — that comes in a later iteration.
- **Sealed chunks are unfindable, not merely unlabelled** (added in the post-audit fix round — see
  the section at the bottom). The identifier and fingerprint the Vault shows for a sealed chunk are
  meaningless stand-ins that cannot be traced back to the real file, and the product's ordinary
  file-listing, file-detail and backtest endpoints refuse a sealed file outright. Without this, the
  hiding was decorative: the real id was on display, and one click on another page gave up the
  stock, the date and the exact trade counts.
- **A safety fix for a known gap**: a status-tracking mechanism elsewhere in the system (which
  records "has this data window ever been looked at before?") did not yet know sealed data
  existed, so a freshly-sealed chunk could have been mistakenly marked "already looked at" by that
  OTHER mechanism, defeating the whole point of sealing it. This is now fixed — sealed chunks are
  invisible to that other mechanism until the Vault itself formally reveals them.
- **A place to record WHY a data-format assumption was made**: recorded stock-tick data now also
  carries a short note explaining exactly how the system decided whether trade-size numbers should
  be read as "shares" or "round lots" for that specific recording — not just the answer, but the
  reasoning and the date-based rule that produced it, for future auditing.

## Changed Behavior

*(Rewritten after the audit's fix round — see "The sealing loophole, and how it was closed" at the
bottom. Before that round this section honestly read "None"; it no longer can.)*

- **The list of recorded data files** (`GET /research/datasets`) now leaves OUT any file that is
  currently sealed in the Vault, and says how many it left out (a new `sealed_withheld` count) — so
  a reader can always tell "nothing was recorded" apart from "recorded, and sealed". Asking for a
  sealed file directly now returns a polite refusal ("this dataset is sealed — withheld until its
  exposure is recorded") instead of the file's details.
- **The corpus status page data** (`GET /research/desk/micro/readiness`, the Microscope Readiness
  table on `/desk`) no longer lists a sealed file as its own row. Sealed files are summarised as
  totals only — how many, covering how many stock-days, per recording plan.
- **Starting a backtest against a sealed file is refused.** A backtest is exactly the kind of result
  that would expose what the sealed data contains, and its stored result re-publishes the file's
  full details on two other pages, so it is blocked at the door.
- **Everything above is inert until something is actually sealed.** Nothing is sealed today, so
  every list, every page and every number is byte-for-byte what it was before this iteration. The
  protections are switched on by the act of sealing, not by this release.

## Backend-Only Items

- The entire Validation Vault (sealing, assigning, revealing data chunks; recording-plan
  bookkeeping) — the underlying machinery and its one read-only status endpoint exist and are
  fully tested, but there is no button, screen, or command an operator can currently press to
  actually START sealing real data. That comes with a later iteration's credentialed recording
  run — an explicit, deliberately separate, human-attended step.
- The data-format reasoning note (which stock/date recording decided "shares" vs. "round lots" and
  why) — storage capability exists; nothing displays it on any screen yet.

## Incomplete Items

- This iteration completed the THIRD of five planned steps toward "the recorder and the Vault"
  capability. The remaining two steps — actually registering a real list of stocks to record and
  running a real, credentialed recording session against genuine market data, then refreshing the
  corpus status page with the results — were deliberately NOT attempted this iteration, by explicit
  operator instruction (to keep this round focused and inside its time budget).
- The Vault's "reveal" step (the final part of sealed → assigned → exposed) does not yet record an
  actual research verdict (pass/fail) — it only performs the mechanical "this is no longer hidden"
  transition. Recording an actual research outcome against revealed data is a later capability.

## Config and Environment Changes

- `TAPEOLOGY_VAULT_SECRET_FILE` — a NEW setting naming the file path where the Vault's secret
  password lives (outside the project's code folder, never committed to version control). If this
  is not set, or the file cannot be read, the system refuses to make sealing decisions rather than
  guessing or using a fallback password — no default value exists. **The operator created this file
  on 2026-08-18 at `~/.config/tapeology/vault-secret` (permissions 0600) and must export the
  variable for any run that seals data.** Its published fingerprint is
  `e4b64e4399878594ff358d00f5f75261e0720919c0eb32f9629897222eee6a8d`; the secret itself has never
  been read, printed or logged by any agent, and after the fix round it now also determines the
  stand-in ids and scrambled fingerprints the Vault shows — so losing it means losing the ability to
  audit those, exactly as the specification already warned for the sealing coin flip.
- `TAPEOLOGY_MICRO_VAULT_DIR` — an optional setting to move where the Vault's own records are
  stored on disk; if not set, it defaults to a folder next to where recorded stock data already
  lives. Purely a storage-location convenience, not a behavior change.

## Known Limitations

- No real, credentialed recording session was run this iteration (explicitly out of scope, per
  operator instruction) — every part of the Vault has been tested against realistic stand-in data,
  not yet against a genuine freshly-recorded stock-day. That is next iteration's job.
- The rule for "which shard belongs to which research question" was implemented in the stricter of
  two reasonable readings of the written specification (a locked chunk, once claimed by one
  research question, can never be claimed by a second one — even an unrelated one). This is a
  disclosed judgment call, not a discovered problem; the alternative reading would only be LESS
  strict, and nothing currently in the system exercises the difference.
- **One door is still open and was deliberately left open, because closing it was ruled out of
  scope for this round:** the "build snapshots" compute button on `/desk` would still read a sealed
  file's contents if an operator pressed it while sealed files existed. Nothing is sealed today, so
  nothing is at risk right now — but this must be closed before the first real sealing run. It is
  named precisely, with file and line numbers, in the developer handoff's carried-forward list so
  the next round cannot lose it.

---

## The sealing loophole, and how it was closed (the fix round)

An independent audit of this iteration found a real hole and failed the round. Recorded here in
plain language because it is the most important thing that happened in this iteration.

**What was wrong.** The Vault correctly showed almost nothing about a sealed chunk — but the little
it did show included the chunk's own internal file id and its content fingerprint. Both of those are
*also* published elsewhere in the product. So anyone could take the id from the Vault page, paste it
into the ordinary "show me this recorded file" page, and get back the stock symbol, the exact date,
and the exact number of trades and quotes — precisely the facts sealing exists to hide. Hiding the
right *fields* was not enough, because a value that merely *identifies* the chunk somewhere else
leaks everything that other place shows. Nothing was actually exposed (nothing has ever been
sealed), but the hole would have gone live the moment real sealing began — the very next step.

**What the operator decided.** Rather than have an agent pick, the choice went to the project owner,
who chose "opaque stand-in ids plus a polite refusal" over two alternatives (a fully separate
storage area for sealed data — strongest but a much bigger build; or accepting the leak with a
written caveat — cheapest but a materially weaker vault). The decision is now written into the
project's own specification as a named revision.

**What was built.** The Vault now shows a meaningless stand-in id in place of the real file id, and
a scrambled version of the fingerprint instead of the real one — both computed with the Vault's
secret, so they cannot be reverse-engineered by anyone who does not hold it, yet remain exactly
reproducible for the operator who does. The real id is revealed when a chunk is formally assigned to
a research question; the real fingerprint when it is finally exposed, at which point the scrambled
version can be checked against it. Meanwhile the ordinary product pages simply refuse sealed ids.

**How we know it works.** The old test asked "does the Vault page show only the approved fields?" —
which the broken version passed. The new test does the opposite: it seals a chunk of data built to
have a stock symbol, a date and trade counts that appear nowhere else in the product, then calls
**every single read endpoint the product has** (about 66 of them, discovered automatically so a
future endpoint cannot escape the check) and demands that none of them return any of those values
anywhere. Then it performs the attack itself — taking every value the Vault does show and trying to
look each one up as a file id. None resolve.

To be precise about the evidence: the leak was first reproduced against the unfixed code by a
throwaway script written before any fix, using this same sweep technique — it reported **21 separate
leak findings** across the file list, the file-detail page, the corpus status page and the Vault page
itself. The permanent test that now lives in the suite is the cleaned-up, hermetic version of that
script (purpose-built data, throwaway storage), so the two are not literally the same run; what
carries over is the method, and the 21-finding result is what motivated the rig. The permanent test
reports zero findings on the fixed code, and it caught two genuine problems of its own on its first
run — an error message that echoed the file id back, and three endpoints "leaking" numbers that
turned out to be real values from the operator's own unrelated data because the test rig was reading
live storage. Both were fixed rather than explained away.

---

# Addendum — post-re-audit fix round (2026-08-18): "a locked vault that every report actually respects"

## What the second audit found, in plain language

The vault's lock worked at the **front door** — asking the system directly about a sealed chunk of
recorded data was refused. But two of the desk's own reports never use the front door: the **Edge
Report** (the "which strategy actually profits" sweep on `/structure`) and the **PnL sweep** (the
candidate-versus-champion comparison) each walk the whole recording folder themselves and run their
measurements straight off the files. So the moment an operator pressed Compute, those reports would
have read a sealed chunk's trades, measured them, and published that chunk's identity — its id, its
fingerprint, its stock, its dates, its exact trade counts — on the backtests list and, permanently,
in the append-only profit ledger. Once written, an append-only row cannot be withdrawn.

The owner ruled on the fix, and it is now recorded as a named revision of the methodology spec
(**r4**). This round implements that ruling.

## What changed for the operator

- **Every report that walks the recording folder now skips sealed chunks — and says how many it
  skipped.** A count only, never which ones. The number appears in the Edge Report body, in the PnL
  sweep report, in the snapshot-build progress, in every Scout ledger row, in the desk screen's
  recorded snapshot, in the walkforward corpus request, and — if a promotion is ever recorded — in
  the permanent PnL ledger row itself. Silent shrinking of a report's basis is now impossible by
  construction: the count travels with the result.
- **A report whose entire corpus is sealed says so.** Previously it would have looked identical to
  "we measured everything and found nothing" — an empty result with no explanation. It now carries
  an explicit sentence stating that nothing was measured because every chunk is withheld.
- **The "has tick evidence" badge on the desk screen no longer betrays the vault.** A stock whose
  only recorded tape is a sealed chunk used to light that badge up, which quietly revealed which
  stocks are in the sealed set. It no longer does.
- **The tape drill-in on a setup will not replay sealed tape.** If the only recording covering a
  setup's moment is sealed, the drill-in shows its normal, honest "no recorded tape for this
  moment" state instead.
- **Sealing with an empty password is now refused.** An empty secret would have made every sealed
  chunk's supposedly-opaque identity trivially guessable — the vault would have looked locked while
  being wide open.

## What did NOT change

- **Nothing an operator sees today moves at all.** No chunk of data is sealed yet, and with an empty
  vault every one of these exclusions removes nothing and every disclosed count is `0`. Reports,
  ledgers, cached results, screens and the fingerprint `08e471b10130e1e2` are all exactly as before.
- No screen, page or button changed — this round touched no frontend file.
- The operator's real recorded data on disk is byte-for-byte untouched (verified by hashing the
  whole folder before and after: 18 files, identical hash).
- No new configuration setting was added; the Referee's own modules were not touched.

## Backend-only items

Everything in this round is backend-only. The disclosure counts are served on existing endpoints
(the Edge Report, the snapshot compute status, the Scout ledger, the desk screen record) but no
screen displays them yet — the Validation Vault section of `/desk` is a later iteration's work.

## Incomplete / deferred, stated honestly

- **One decision is still owed by the owner before any real data is sealed:** if the vault's own
  ledger file were ever truncated or tampered with, the system currently "fails open" — every sealed
  chunk would silently become readable again. Making it fail closed instead means a damaged vault
  file would start returning errors on pages that work today, which is a trade the owner should
  choose, not an agent. Eleven places now depend on that answer.
- **One count still ignores the seal:** the Referee's readiness figures (how many recordings exist,
  the tick-data gate) would count a sealed chunk. Fixing it requires editing a Referee module, and
  those files are deliberately frozen for this era with their fingerprints pinned. r4 and that
  freeze genuinely collide; the owner should settle it alongside the item above.
- The credentialed recording run that would actually seal the first chunk (J-06 step 4) has still
  not been run. Until it is, all of this machinery is real but dormant — which is exactly why it
  could be changed this round without disturbing a single recorded result.

## Tests

The full backend suite was re-run after the last code change of this round: **3,164 tests, 0
failures, 0 errors, 8 skipped** (~10 minutes). Twenty-one new tests were added, including a trap
that presses the real compute buttons FIRST and only then checks every endpoint for a leak — the
previous version of that trap passed only because its test rig had computed nothing, which is the
exact blind spot this round was called in to close. That new trap was verified to fail when the fix
is removed.
