# Iteration 9 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** full

## Summary

The sealed-evidence vault was built and it works: I sealed a test recording myself and the program
served only a made-up label, a rough size, a scrambled fingerprint and the word "sealed" — the real
name, real date, real fingerprint and exact count were all absent, and a second attempt to move the
same recording was refused. Four new safety traps are armed, two long-standing small faults are
closed, and nothing that already worked broke: I ran the whole test suite myself and got 3,166
tests, 3,158 passed, 0 failures. But the vault does not yet keep its main promise. The independent
checker attacked its own fix and showed that anyone can still work out WHICH recordings are hidden,
by listing the public ones and seeing which combinations are missing — it recovered all 5 of 5. So
the work so far is safe to look at, but not yet safe to hide your real tape in.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 The era transition stands | passing | passing | `reports/qa/goal-rapid-microscope-iter-9-evidence/UT-03-result.png` (opened by me) + replay `J-01-verify.png`; screenshot values re-computed under the post-r4 code and identical |
| J-02 The micro observer | passing | passing (browser row DEFERRED-BUDGET) | evaluator re-derived: 18 snapshot feature files, exactly 3,815,933 rows; test_micro_snapshots 34 / test_micro_observer 31 / test_micro_features 50 green |
| J-03 Structure x flow | passing | passing (browser row DEFERRED-BUDGET) | evaluator re-derived on the real store: `joinable_corpus.total` 2, `by_setup_id {range_trade: 2}`, 0 integrity errors; test_micro_join 37 green |
| J-04 The Scout and the ledger | passing | passing (browser row DEFERRED-BUDGET) | test_scout 52 + test_scout_ledger 20 green in my own suite run; NOTE: no real scout ledger exists on disk, so `verify_chain()` could not be re-run this round — stated as the honest limit |
| J-05 The walk-forward engine | passing | passing (browser row DEFERRED-BUDGET) | evaluator re-ran its own acceptance under post-r4 code: literal `11 < 105 -- refused (TR-15)`, exit 1, scoped ledger empty, real store hash unchanged; ledger `verify_chain()` ok over 1 spec + 5 diagnostic folds |
| J-06 The recorder and the Vault | partial | partial (step 3 of 5 landed) | `UT-01-result.png` (opened by me — Validation Vault genuinely absent) + my own seal probe (no symbol/date/raw id/raw checksum/exact count served; TR-12 refusal fires); TR-2/4/12/20 new, test_vault.py 42 green |
| J-07 Graduation | failing | failing | `micro_graduation.py` and `test_micro_graduation.py` both absent on disk (checked by `ls`) |
| J-08 The surface and MCP v6 | failing | failing | `EXPECTED_TOOLS` still exactly 22 by AST; `UT-02-result.png` shows only the 8 shipped `/desk` sections; 0 frontend files changed |
| J-09 The pilot studies | failing | failing | the three study ids still appear only as floor rows (each `floor_unmet`, 60 required vs 11 available on the real corpus); no study spec is ledgered |
| J-10 The kept product stands | partial | partial (traps 15 → 19 of 22) | `UT-04-result.png` + `UT-05-result.png` (both opened by me — live cockpit tape; `/structure` band `300.11-302.2 · Class A · score 171`); fingerprint, 6 referee hashes, 22-tool list and real-store hash all re-verified by me; TR-3, TR-17, TR-22 still absent |

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| Secrets/credentials committed | OK | The scan report's 2 CRITICALs are both false positives and I checked each. `_VAULT_SECRET_FILE_ENV = "TAPEOLOGY_VAULT_SECRET_FILE"` (vault.py:194) is an env-var NAME. `raw_secret_text` (test_vault.py:211) is a synthetic throwaway used to ASSERT non-leakage; its sha256 `0f9314d9…` is NOT the owner's recorded commitment `e4b64e43…`. The real secret path is never hardcoded in any `.py`. My own seal probe confirms the secret never reaches the served payload. |
| Paid/external SaaS, new runtime dependency | OK | Zero dependency manifests touched (no requirements/pyproject/package.json in the diff or in `git status`). `vault.py` imports only stdlib (hashlib, hmac, json, math, os, datetime, pathlib) plus two in-repo modules. No vendor call is made this iteration. |
| License changes | OK | No LICENSE file in the diff or in `git status`. |
| Fabricated/substituted data | OK | Nothing was recorded; the operator's real store hashes `f7bbcf28…` across 18 files, newest mtime 2026-07-15, identical before and after every command I ran. Readiness serves real disk truth (12 symbol-days / 18 datasets / 3.0089 session-equivalents, all three floors honestly unmet). The new `sealed_tranche` block is an honest all-zero row. |
| No exploratory read of a sealed shard (fail-closed) | OPEN — minor, latent, owner-owed | The read side genuinely holds today. But audit B4: the withholding predicates read `all_rows()` without `verify_chain()`, so a truncated ledger silently UN-withholds every sealed shard across 11 consumers — the opposite of the fail-closed the rail demands. Unreachable now (I confirmed no vault ledger exists anywhere under `.data`, `seal_shard` has zero production callers, `withheld_dataset_ids` empty on both stores). Becomes critical at step 4. |
| Sealed exposure is family-level and single-shot | OK | I re-attempted a second lifecycle transition on the same shard and got a typed `ShardLifecycleOrderError`. TR-12 keys on identity, not row count. |
| The vault secret never enters repo/log/payload/screenshot | OK | Only `sha256(secret)` is persisted; my probe found the raw secret absent from the served payload. |
| Single source of truth | OK | `coherence.md` = COHERENCE-PASS; `exclude_withheld` traced as the ONE predicate at every corpus enumerator. |
| Immutable data / append-only / frozen splits | OK | Real store byte-identical. The two new §2.6 manifest fields are excluded from `_content_checksum` structurally (it hashes only symbol/data_feed/epoch_anchor/events). |
| Deterministic and seeded; no fingerprint movement | OK | `Config().config_fingerprint()` printed `08e471b10130e1e2` when I ran it. |
| Frozen foundations / Referee byte-untouched | OK — but see collision | All six `referee_*.py` sha256 hashes identical to the iteration-0 listing, compared by me. OPEN (minor, owner-owed): audit B5 — `referee_evidence.py:333` counts withheld shards, so r4 collides with the freeze pin. Inert today. |
| Read-only MCP | OK | No MCP file changed; `EXPECTED_TOOLS` still the 22-tuple by AST. |
| The 12 legacy tick symbol-days stay permanently exploratory | OK | All 18 shards report `exposure_state: exploratory`. The iter-6 latent hole is now CLOSED (`walkforward.py:1267` excludes sealed ids from the r2 seed). |
| The ~150-symbol-day gate never lowered | OK | `referee_tick_gate_symbol_days: 150`; all three pilot floors honestly `floor_unmet`. |
| The denominator never shrinks | OK | r4's `withheld_excluded` disclosure is exactly this rail; all counts are 0 today. |
| Spec §7.3 "sealed membership cannot be inferred from public information" | OPEN — minor today, HARD GATE on step 4 | Audit B2: cartesian closure of `GET /research/datasets` recovers the sealed set exactly (5 of 5), with the B1 fix in place; nothing inside `vault.py` can close it. B3 is a third instance (recorder-compute route serves per-chunk symbol/date/raw id). Scored minor strictly because nothing is sealed and no real tape exists, so no recorded artifact is damaged. |

## Next-Step Recommendation

Build **J-07 "Graduation — provenance in, nothing laundered out"** next, under the full pipeline
with the independent checker. It is the next step in order, it runs entirely on made-up test data,
and it needs no decision from you — so it is real work that can start immediately while the vault
questions wait. Keep the independent checker in the loop: it has now found a real honesty fault in
five of the five full rounds it has run, and J-07 is exactly the kind of work where one would hide
(it is the step that must carry every failed trial into the export, with nothing quietly dropped).

Do **not** let the next round record real tape. J-06's last two steps are blocked until you decide
three things, all the same kind of question you have already answered twice:

1. **The big one.** Anyone can still work out which recordings are hidden, by listing the public
   ones and noticing which combinations are missing. Pick one: hide the whole batch's names and
   dates until the batch is finished with; add extra recordings so "missing" no longer means
   "hidden"; or accept it in writing and state plainly that hiding protects the DATA, not the
   MEMBERSHIP.
2. **Damaged-record behaviour.** Should a damaged vault record make everything refuse (safe), or
   make everything open (what happens today)?
3. **A frozen file.** One of the six frozen judge files counts hidden recordings toward a research
   threshold; fixing it means touching a file this era promised never to touch.

Please also settle the timing stamp that is one quote too early — it has been waiting since round 2.
Carry three passenger items: fix the recorder progress page so it stops showing a hidden recording's
name and date (cheap, but do it after decision 1 sets the direction); add the three missing traps
TR-3, TR-17 and TR-22; and re-run the browser check, since this round's pictures were taken before
the last fix landed (I re-computed the values by hand and they match, so nothing is scored down, but
the pictures should be refreshed). One process note worth keeping: your ruling to split the work
into smaller rounds rather than raise the clock budget WORKED — the full pipeline finished, the
checker ran three times, and it caught a real fault everything else had passed. Keep scoping one
step per round.

**In one sentence for you to act on:** approve building the Graduation step next, and answer the
three vault questions above before any real tape is recorded or hidden.
