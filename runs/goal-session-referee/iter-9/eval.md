# Iteration 9 Evaluation

**Verdict:** ESCALATE
**Depth Recommendation For Next Iteration:** full

## Summary

The promotion lock is real. The champion can no longer be replaced by a better-scoring trading
strategy unless a matching certificate from the new statistics machinery is on file — and I proved
that myself instead of reading it in a report: I minted a certificate through the real path, then
tried to promote with each pinned detail spoiled in turn, and every attempt was refused with its own
honest reason. J-08 "The strategy family and the promotion lock" moves from failing to passing, and
nothing else moved backwards. I am raising the depth because this round was planned as the deep pass
and was cut back to the short one for time — the third time this has happened — and because I found
a real weakness in the new certificate that the short pipeline only noted in passing: the
certificate names which strategy it is for, but nobody ever checks that the evidence behind it
actually came from that strategy.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 The era transition stands | passing | passing (not re-tested — deferred) | reports/phase-goal-referee-iter-9-ui-test-results.md:43 (DEFERRED-BUDGET); its own source file is not in this run's 10-file diff |
| J-02 The evidence contract | passing | passing (not re-tested — deferred) | results file :44 (DEFERRED-BUDGET); referee_evidence.py unchanged this run |
| J-03 The statistics core | passing | passing (not re-tested — deferred) | results file :45 (DEFERRED-BUDGET); referee_stats.py has ZERO diff (my own `git diff --stat`); its oracle tests green in my own full-suite run |
| J-04 Matched nulls | passing | passing (not re-tested — deferred) | results file :46 (DEFERRED-BUDGET); referee_null.py unchanged this run |
| J-05 The registry | passing | passing (re-verified by me directly) | results row deferred (:47), but referee_registry.py changed — I reviewed every hunk and deletion of `git diff a385f7e`; no write-path or boundary line touched; 47/47 of its tests green in my own suite run; reports/qa/goal-referee-iter-9-evidence/J-07-verify.png still shows the server-stamped 2026-08-15 boundary |
| J-06 Estimand engines + adjudication | passing | passing (re-verified by me directly) | results row deferred (:48), but referee_adjudicate.py changed — the old path is only re-indented into an `else:` branch, the mint is additive and double-gated; 54/54 of its tests green in my own suite run |
| J-07 The starter family | passing | passing (stale capture now cleared) | results file :18 PASS + reports/qa/goal-referee-iter-9-evidence/J-07-verify.png — I opened it: six candidate rows including the new S-6, and "Projected days" now reads 564 (the corrected number), so iteration 8's `evidence_makeup` flag is cleared |
| J-08 The strategy family + promotion lock | failing | **passing** | results file :20 is a correct SKIP (goal.md scopes J-08 "(Keyless; automated.)" — no browser step exists). My own verification: pnl_scan.py:349 authorizes before the ledger write at :367; `inspect.signature` shows `certificate_store` is required on both `run_sweep` and `_promote`; one `_promote` call site and one `set_champion_pointer` site; my isolated real-rail mint + tamper probe returned the right refusal for every spoiled pin; full suite 2,678 collected / 2,670 passed / 8 skipped / 0 failed (my own run) |
| J-09 The Referee on /desk + 22 MCP tools | failing | failing (not built — out of scope) | Only 1 of its 3 /desk sections exists; I parsed `EXPECTED_TOOLS` myself — still 20 tools, none referee-related |
| J-10 The kept product stands | partial | partial (kept half green again) | results file :19 PASS + reports/qa/goal-referee-iter-9-evidence/J-10-verify.png — I opened it: every shipped /desk section renders as shipped. Era-end clauses (three Referee sections, 22 tools) still wait on J-09 |

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| Secrets / credentials | OK | `iter-9/scan-report.md`: CLEAN, no findings on added lines; 0 untracked files in scope. No config or env file appears in the 10-file diff. |
| Paid / external SaaS, new runtime dependency | OK | No manifest changed — `pyproject.toml`, `requirements*.txt` and `package.json` are absent from the diff's file list (my own `git diff --stat`). scipy still absent. |
| License changes | OK | No LICENSE or license field in the diff; scan-report reports no license findings. |
| Fabricated / substituted data | OK | `reports/qa/goal-referee-iter-9-store-scope-guard.md` is CLEAN — all 11,274 protected files unchanged. I confirmed the operator's real registry directory does not exist on disk, so no hypothesis and no certificate was written into real records. Every test corpus is a fixture built in a tmp dir. |
| **Promotion is certificate-locked** (critical) | **MINOR VIOLATION — open** | The lock itself is genuine and fails closed (verified by me from four sides: required parameter, single call site, source scan, live tamper probe). But the certificate's candidate name is supplied by whoever calls the mint and is never checked against the evidence it was minted from. I demonstrated this: 12 planted backtests all belonging to `v1/default` minted a passing certificate naming `totally-unrelated-strategy/totally-unrelated-profile`, and the lock then authorized that unrelated candidate. Scored MINOR because no operator action can reach the mint this era — I grepped both production call sites of `run_evaluation_and_record` (referee_adjudicate.py:1512 and :1854) and neither passes `journal_store`/`certificate_mint` — and zero certificates exist on file, so every live promotion is refused with `no_certificate`. Recorded unresolved in journey-history so it must be closed before any future era wires the mint into a route. |
| No bypass flag / env override / default-allow | OK | I ran the guard's own scan logic myself: zero banned tokens in the shipped `pnl_scan.py` / `referee_adjudicate.py`, and a seeded `force_promote` mutation trips it. Caveat: the scan is token-list based, so a differently-named override (e.g. `TAPEOLOGY_PROMOTE_ANYWAY`) would not be caught — inherent to this project's source-scan guards, not new here. |
| A Playbook certificate can never satisfy a strategy promotion | OK | The mint is gated on `evidence_family == "strategy"` (referee_adjudicate.py:1422); a playbook checkpoint mints nothing (TC-11, and confirmed in my own reading of the gate). |
| Frozen foundations / fingerprint pin | OK | `Config().config_fingerprint()` printed `08e471b10130e1e2` in my own run. No `app/config.py` change; zero new Config fields. `pnl_scan.py` is the one deliberate exception goal.md itself names and inventories. |
| The Referee never feeds back | OK | `referee_stats.py`, `desk_forward.py`, `desk_playbook*.py`, `levels.py`, `tradability.py`, `backtests.py` all absent from the diff's file list. The import-ban guard tests passed in my own suite run. |
| No confirmatory output without a verified attestation | OK | The mint re-verifies the attestation before writing (`_mint_strategy_certificate` returns None otherwise); TC-13 covers the failed-attestation case and passed. |
| Never shrink the BH denominator / no gate loosens | OK | No change to family q or floors; the new `REFEREE_DEFAULT_Q = 0.10` moves the same value from an unowned browser literal into the backend, and the submitted number is identical (frontend diff read directly). |
| No profit claims / no advice / no annualized metrics | OK | Copy-discipline and annualization guard tests passed in my own full-suite run; the two new served fields carry no claim language. |
| Read-only MCP (20 tools this iteration) | OK | I parsed `EXPECTED_TOOLS` myself: 20 names, no referee tools yet, no writes added. |
| Enhancement loop stays in its box | OK | `docs/goal.md` is not in the diff; the journey spec hashes I computed are byte-identical to the recorded ones for all ten journeys. |
| Host-guard caps | OK | I ran every heavy command under the declared CPU mask (`taskset -c 4-7,12-15`). |

Coherence: `iter-9/coherence.md` is **COHERENCE-WARN**, not FAIL — no structural veto. Its one
advisory is a stale docstring: `authorize_promotion` still describes itself as "unwired", which I
confirmed is now false. Iteration 8's open advisory (the unowned `family_q` browser literal) is
genuinely closed — I read the frontend diff and the two local constants are deleted, not shadowed.

## Next-Step Recommendation

Build J-09 "The Referee on the Desk page and the 22-tool Claude connector" next, on its own, at
full depth. It is the last part left to build: the two missing Referee panels on the Desk page
(one for verdicts, one for compute controls and run history), the honest empty-state wording, and
growing the Claude connector from 20 read-only tools to 22. Full depth is needed for three reasons.
First, this round was planned as the deep pass and was trimmed to the short one for time — the third
time in this session — and every one of the three rounds where the deep checking lane actually ran
found a real fault the ordinary checks missed. Second, J-09 changes two protective counters that
the project's own rules say may be re-derived only once, on purpose, with a written reason. Third,
it needs real browser pictures of three new panels, which the short lane keeps deferring.

Four items must be settled inside that round rather than becoming their own:

1. Close the open promotion-lock weakness: make the certificate's evidence actually belong to the
   strategy the certificate names, or get an owner ruling that a caller-declared name is enough
   while the minting path stays unreachable. Whichever is chosen must be written down.
2. Fix the stale wording on the promotion-lock function, which still tells future readers it is not
   connected to anything (it is, as of this round) — the coherence audit's one advisory.
3. Make the "this check can fail" proof for the no-bypass scan real: today it inspects a hand-typed
   sentence instead of running the actual scan, so it would not notice if the scan were gutted.
4. Delete the duplicated assertion line the reviewer found in the registry tests.

One thing a person should do: this round's ten changed files are still uncommitted, and so are the
previous round's — they should be committed. Also still outstanding from iteration 2, outside this
project: the unrelated trendora backend on port 8255 has not been restarted. Neither blocks the next
round.

For a person to approve: "build the last Referee screens and the two new Claude connector tools
next, using the deeper checking pipeline, and fix the four small items listed above along the way."
