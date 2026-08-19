# Iteration State — rapid-microscope

**After iteration:** 12 · **Date:** 2026-08-19 · **Verdict:** ESCALATE

## Journeys

6 passing (J-01..J-05, J-07) · 2 partial (J-06 step 3 hardened, steps 4-5 unbuilt; J-10 traps 23/28, sentinel green 7th run) · 2 failing (J-08, J-09 — never yet scoped) — 10 total

## Active blockers

- **NEXT ROUND MUST RUN FULL WITH THE AUDITOR.** Iteration 12's spec asked for `full`; the arbiter demoted it to lean and the audit lane never ran on an iteration shipping security-critical vault code. Owner: engine/dispatch. My ESCALATE exists to force it.
- **New, mine (dev-owned):** `vault.py:1541` — an unprovable `recover_shard_ledger` marks visible shards `exposure_unknown` correctly, but a shard whose ONLY row was in the destroyed suffix silently leaves the withheld set (reads as never-sealed, publicly listable), and `rewrite_from_recovery` re-heals the tail anchor so `verify_chain()` reports `ok: True` again. Reproduced end to end. Inert today (0 universes, 0 sealed shards, no `micro_vault` dir, 0 production call sites); **must close before J-06 step 4.**
- **Reviewer MINOR, needs a call (dev or owner):** `vault.py:880` — `seal_shard`/`assign_shard`/`expose_shard` gate `verify_chain()` on their own shard ledger only; the spec text literally says "both ledgers". No disclosure hole today (serving paths gate both); it is a developer scope call against unambiguous spec text.
- Three older minor items open, all DECIDED, none owner-blocked: depletion stamp one quote early (TR-26); `referee_evidence` seal-unaware count (disclose-only); the two graduation improvisations (TR-23/TR-24).
- **Nothing waits on the owner.** J-06 step 4 (real tape) stays shut until the recovery hole closes.

## Last 2 verdicts

- iter 12: ESCALATE — three gates built and independently attacked by me (all hold), but the audit lane was cut and I found a real recovery-path hole myself; ESCALATE is the only verdict that forces `full` next round.
- iter 11: CONTINUE — r5 opacity built and attacked; recommended `full` in prose only, which the arbiter downgraded (the mistake this verdict corrects).

## Do not redo

- **TR-25/TR-27/TR-28 are BUILT and verified by me**, not just by the dev's tests: 4 vault predicates fail closed on a truncated AND an interior-mutated ledger; a 1,404-guess dictionary attack on `rule_commitment` scored 0 hits; 50 consecutive counts collapse to one volume bucket. Do not re-implement — only fix the recovery hole above.
- **The reveal gate is already widened** to whole-ORIGINAL-pool release (`_whole_pool_released_universe_ids`), paired with the nonce in the same diff. Do not ship a second "whole pool released" predicate.
- **Symbol case-normalization is done** in `unresolved_pool_universe_by_dataset_id` (TC-12/TC-13 green). Date-format normalization was deliberately NOT done and is not a known gap.
- **J-07's missing golden script is a genuine, disclosed infeasibility**, not an omission: `demo_runner.normalize_url()` rewrites any localhost URL onto the frontend base_url, so no golden can reach J-07's backend-only route. Disclosed at `state/golden-gaps`. Do not re-investigate; re-verify J-07 through the LLM browser lane.
- **Evidence retakes are DONE** — the readiness table and the whole-product sentinel were re-captured and I opened both. Do not schedule another retake round.
- **Frozen rails re-verified by me this round**: fingerprint `08e471b10130e1e2`, six `referee_*.py` hashes unchanged, MCP tools 22, zero new Config fields, zero frontend diff, real `.data` store byte-untouched (18 datasets, no `micro_vault`). Suite 3212/3204/8/0.
