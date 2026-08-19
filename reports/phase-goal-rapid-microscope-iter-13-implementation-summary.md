# goal-rapid-microscope-iter-13 — Implementation Summary

**Phase:** goal-rapid-microscope-iter-13
**Date:** 2026-08-19
**Written by:** developer

> Revised after the code review failed this iteration and the owner ruled on the finding. The
> ruling is recorded as **spec revision r8** ("recovery is halt-only this era"). This summary
> describes what the product does *after* that ruling was implemented.

---

## What this iteration is about, in plain language

The Validation Vault keeps a tamper-evident logbook of every sealed research shard: which ones are
sealed, which have been handed to a family, which have been used. The logbook is hash-chained, and a
small sidecar file ("the anchor") records how many entries there should be and a fingerprint of the
last one. If the logbook is damaged, the whole vault refuses to answer any question until a lawful
recovery restores it — because a vault that silently forgets a shard was already used would let that
shard be used a second time, which is the single worst failure this system can have.

This iteration fixed the recovery procedure itself.

---

## Features Implemented

- **Recovery now demands proof, and nothing else will do.** A recovery attempt succeeds only if the
  reconstructed logbook reproduces the anchor's own fingerprint exactly. Every other outcome —
  missing, wrong, reordered, padded, or merely unproven — refuses. The damaged file is left exactly
  as it was, the vault stays unavailable, and the attempt is written to a permanent, separate
  incident record that says why the proof failed.
- **Every refused attempt is on the record.** The incident record now names the anchor's expected
  entry count and fingerprint beside what the attempt actually produced, and whether the attempted
  logbook even held together on its own terms. An operator reading it can tell "you were one entry
  short" apart from "your entries do not match the history".
- **The trap suite grew by the owner's six enumerated attacks (TR-29).** Each one hands the recovery
  procedure a reconstruction that the *old* rule would have accepted, and each one must be refused —
  including the exact attack found in review: destroy the entry for one shard, hand back a
  same-length reconstruction naming an unrelated shard instead. Two further attacks found by
  attacking the fix during this work are also now permanent tests.

---

## Changed Behavior

- **A recovery that cannot be proven no longer partially resumes.** Previously (as shipped earlier
  in this same iteration), if a reconstruction merely *named* as many entries as the anchor expected,
  the vault resumed service and flagged the affected shards as "exposure unknown". That path is gone.
  Matching the entry count proves nothing about identity — the review demonstrated a same-length
  reconstruction naming a fabricated shard, after which the genuinely destroyed shard vanished from
  every record, the logbook reported itself healthy, and the destroyed shard could be sealed again
  from scratch as if it had never existed. Now: no proof, no resumption.
- **The "exposure unknown" shard state no longer exists.** It was only ever produced by the branch
  above. A shard is `sealed`, `assigned`, or `exposed` — there is no fourth, "we are not sure"
  state, because a vault that is not sure is a vault that stays closed.
- **Two ways a "proof" could be faked are closed.** An empty reconstruction can no longer prove that
  a logbook was always empty (which used to wipe every sealed record and make every shard look
  brand new), and a reconstruction built on entries the file itself no longer authenticates can no
  longer be certified as complete.
- **Nothing else changed.** No screen, number, endpoint, tool, or stored file behaves differently.
  The recovery procedure has no user-facing entry point yet — it is an operator-invoked repair
  routine with no route, no button, and no CLI wired to it.

---

## Backend-Only Items

- `vault.recover_shard_ledger` — the lawful-recovery procedure described above — has **no UI wiring
  and no serving endpoint**, by design. It is invoked deliberately by an operator during an incident,
  never by a page load. The vault's own read-only surface (`GET /research/desk/micro/vault`) is
  unchanged and continues to refuse everything while a logbook is damaged.

---

## Incomplete Items

- **Graded recovery is deliberately not built.** The owner's ruling defers it to a future named spec
  revision that must first give the logbook a real identity commitment (enough to prove the exact
  historical sequence, not merely a count or a set of names). Designing that was explicitly out of
  scope here, and no stored file format was changed.
- **The iteration-13 phase spec text is now out of date** where it still asks for the deleted
  "mark the affected shards as unknown and resume" behaviour. The canonical spec
  (`docs/rapid-validation-spec.md`, revision r8) and the recorded owner ruling govern; the phase spec
  and its plan file were not rewritten.
- Journey J-06's operator steps 4–5 (running the real recorder against the tranche) remain untouched,
  as in the first pass — out of scope for this iteration.

---

## Config and Environment Changes

None. No new environment variable, no new configuration field, no migration, no new dependency. The
configuration fingerprint is unchanged at `08e471b10130e1e2`.

---

## Known Limitations

- **Safety was traded for availability, on purpose.** A vault whose history cannot be proven now
  stays unavailable indefinitely — there is no partial-service mode. One lost logbook entry can
  block an entire tranche until a provable reconstruction exists. The owner's governing sentence:
  unknown or unprovable exposure history means the vault is unavailable, never "fresh".
- **The anchor sidecar remains the only external proof point.** Anyone or anything able to rewrite
  both the logbook *and* its anchor can still present a self-consistent forgery, and no check in the
  system would detect it. Closing that requires the identity commitment deferred to a future
  revision. This is a known bound on what today's guarantee means, recorded rather than glossed.
- **Recovery has no operator interface.** Running it today means calling it from Python during an
  incident. That is acceptable while it has zero production call sites, but it means the procedure's
  usability has never been exercised by a real operator under real pressure.
