# Goal Session clean_slate — Assumption Ledger

Append-only. The goal-evaluator (and other judges) log an entry whenever scoring
required *interpreting* the goal rather than just reading evidence. The human
reviews these to catch (and veto) silent interpretation calls early.

## iter-0 — goal-evaluator

**Ambiguity:** J-05's literal goal.md acceptance ties full closure to the post-J-04 end state ("full
suite green under the new pin" + a cumulative diff-vs-inventory cross-check), and the iteration spec
explicitly delegates to the evaluator whether to record J-05 as passing-on-today's-kept-product-evidence
or partial-pending-later-journeys. Separately, the spec's expected "Case Study drill-in" clause is
unreachable in the shipped app (`SHOW_CASE_STUDIES = false`).
**We chose:** `partial`, not `passing`. Two grounds: (1) the full acceptance is not yet evaluable
pre-J-04, and (2) a genuine acceptance clause (Case Studies drill-in) is unmet. Not `failing`, because
the checkable kept-product core (sim cockpit + both charts, AAPL wall band, honest Edge-Report state, full
suite green under the current pin) all verified intact via opened screenshots.
**Reversible:** yes (J-05 is re-scored in a later iteration once J-04 lands and the Case Studies
restore-vs-rescope question is resolved).

## iter-1 — goal-evaluator

**Ambiguity:** J-01's acceptance lists "the full remaining backend suite is green" as a clause, but
the suite is 1165 passed / **1 failed** / 7 skipped. The one failure
(`test_mcp_server.py::test_static_live_tools_json_byte_identical_to_rest`, line 244) is the MCP
`journal` tool proxying to the now-correctly-404 `GET /research/journal` — a test the iteration spec
explicitly leaves untouched (J-03's 15-tool contract update) and whose transient red state the
J-01→J-03 dependency order necessarily produces.
**We chose:** Read "full suite green" as "green modulo the J-03-owned MCP-contract test the ordering
leaves transiently red" and scored J-01 `passing` (not `partial`). Grounds: every substantive J-01
acceptance clause is met and independently re-verified; the failure is a scoping/ordering artifact
(and itself evidence the demolition worked), not a kept-value regression; review/QA/audit/coherence
all treat J-01 as complete; calling it `partial` would falsely imply J-01 has remaining work of its
own when the residual red test is J-03's by explicit design.
**Reversible:** yes (if the operator prefers strict literal "0 failed" journey-closure, J-01 can be
re-scored `partial` until J-03 lands and the MCP test goes green; nothing downstream is foreclosed).

## iter-2 — goal-decomposer

**Ambiguity:** goal.md's I-9 byte-comparison protocol step 2 says "At J-01/J-02/J-03 end: re-capture —
every kept route must be byte-identical (the fingerprint has not moved yet; `/research/taxonomy` is the
ONE sanctioned diff, its payload having slimmed in J-01)." Read literally in isolation, this could mean
taxonomy is the ONLY route payload EVER allowed to differ across all three journeys — which would
contradict J-02's own explicit acceptance clause ("`GET /meta/ui-routes` lists only the kept routes"),
since trimming `app/meta.py`'s `UI_ROUTES` tuple necessarily changes `GET /meta/ui-routes`'s response body.
**We chose:** Read the I-9 protocol as a per-journey CUMULATIVE sanctioned-diff list, not a single fixed
exception: J-01's own re-capture (iter-1) showed taxonomy as its one sanctioned diff; this iteration's
(J-02's) re-capture is scoped against iter-1's own post-J-01 capture
(`runs/goal-session-clean_slate/iter-1/kept-route-after.txt`) and is expected to show exactly ONE new
sanctioned diff (`meta.ui-routes`, 6→2 rows) on top of the already-accepted taxonomy diff, with every
other kept route staying byte-identical. This is the only reading consistent with J-02's own acceptance
text, and is codified as TC-14 in `docs/phases/goal-clean_slate-iter-2.md`.
**Reversible:** yes — if this reading is wrong, the fix is purely evidentiary (re-label the ui-routes diff
in the eval), not a code change; the underlying `app/meta.py` edit is required by J-02's own acceptance
regardless of how the I-9 diff is narrated.

## iter-2 — goal-evaluator

**Ambiguity:** J-01's Required-still-passing check (TC-14 / I-9 protocol step 2) says every kept
`/research`+`/tape`+`/meta` route must re-capture byte-identical except the sanctioned diffs, but the
re-capture showed THREE diffs: the sanctioned `meta.ui-routes` shrink PLUS `research.backtests.list`
and `research.pnl_ledger`. Read literally, two unexplained kept-route diffs are a J-01 regression signal.
**We chose:** Scored J-01 `passing` — accepting the dev's root-cause that the 2 extra diffs are a
launch-cwd DATA artifact (this iteration's dev-server ran with cwd `apps/backend/` and read the real
full-history `tapeology_journal.db`; iter-1's capture read a near-empty repo-root db — different INPUT
data, not different code). I did NOT re-run the dev's full byte-for-byte db-swap sha proof, but
independently confirmed the decisive fact: `backtests.py`, `pnl_ledger.py`, and `store.py` (the entire
read/serialize path for those two routes) are 0-diff vs the pre-iteration snapshot. Since the code is
byte-identical, a differing output can only come from a differing db file, so it is not a code regression.
**Reversible:** yes — if the operator wants strict literal I-9 byte-identity, the fix is evidentiary
(re-capture both iter-1 and iter-2 against the SAME pinned db path), not a code change; nothing downstream
is foreclosed.

## iter-3 — goal-decomposer

**Ambiguity:** goal.md's I-6 lists the resulting 15-tool contract in a specific prose order
(`..., strategies, pnl_ledger, taxonomy, edge_report, ui_route_map, get_endpoint`), but the current
code's natural residual order after deleting exactly the `journal`/`analytics`/`studies` rows in
place is `..., strategies, edge_report, pnl_ledger, taxonomy, ui_route_map, get_endpoint` — the
identical 15-item set, with `edge_report`/`pnl_ledger`/`taxonomy` sequenced differently than the
prose enumeration. Since `list_tools()`'s return order feeds an exact tuple-equality test
(`EXPECTED_TOOLS`), some ordering has to be chosen when the 3 dead rows are removed.
**We chose:** Read "this exact list" as specifying tool MEMBERSHIP (which 15 names), not a mandated
ORDER, and kept the code's natural residual order (surgically deleting the 3 dead rows in place, per
core.md's Surgical Changes principle) rather than reordering 3 additional lines for zero functional
benefit — no MCP client depends on `list_tools()`'s ordinal position, and no other I-row in goal.md
is about sequence.
**Reversible:** yes — a one-line reorder of 3 `types.Tool` blocks (and the matching `EXPECTED_TOOLS`
tuple) if a future review insists on literal prose-order matching; no other code or test depends on
the internal sequence.

## iter-4 — goal-decomposer

**Ambiguity:** goal.md's I-4 "Confirmed DELETE list" names 18 Config fields as safe to delete and
separately states a closure rule for fields "beyond the confirmed list." This planning pass grepped
every one of the 18 named fields (plus every neighboring field in the same journal-era block,
`app/config.py` lines ~508-885) against all of `apps/` for live readers outside `config.py` itself, and
found the confirmed list is both over- and under-inclusive. Over-inclusive: 4 of its 18 names
(`study_arm_sustain_seconds`, `study_arm_cooldown_seconds`, `study_occurrence_r_spread_multiple`,
`study_occurrence_r_floor`) are read live by `Config.strategy_definition()` (`app/config.py`, building
the KEPT `v1`/`structure_tape`/`structure_tape_map` strategy grammar served via
`GET /research/strategies`) and directly by `backtests.py:225`'s R-stop formula — deleting them would
crash every backtest/edge-report compute, a severe kept-value regression, not a cosmetic gap.
Relatedly, `analytics_min_sample_size` (not on the confirmed list, but plausible by name/history) is
still read by `pnl_ledger.py` and must also stay. Under-inclusive: 9 fields NOT on the confirmed list
(`invalidation_k_consecutive`, `journal_list_default_limit`, `journal_list_max_limit`,
`chase_return_threshold`, `invalidation_too_tight_spread_multiple`, `process_outcome_grade_map`,
`process_violated_min_failed_checks`, `process_flagged_min_risk_flags`, `sound_cue_cooldown_seconds`)
qualify for deletion under I-4's own closure rule — verified zero readers outside `config.py`, meaning
their sole historical reader was a module I-2 already deleted in J-01/J-02.
**We chose:** Corrected the delete list to 23 fields (14 of the confirmed 18, minus the 4
wrongly-listed ones, plus the 9 verified closure-rule finds), and explicitly excluded the 4 study_*
fields and `analytics_min_sample_size` from deletion — per T-14 ("inventory contradictions stop the
line... the fix is a documented inventory correction, never a silent improvisation"). The full
evidentiary grep trail (file:line citations) is in `docs/phases/goal-clean_slate-iter-4.md`'s NOTES.
**Reversible:** yes — if any individual classification is wrong, the fix is a further grep-verified
correction to the field list before/during execution; no code has been written yet (this is a
planning-time correction), so nothing downstream is foreclosed.

## iter-4 — goal-decomposer

**Ambiguity:** goal.md's J-04 Step 3 says re-running `python -m app.research.pnl_baseline` under the
new epoch "appends the new-epoch founding row beside the untouched old rows," but names no Config
value to change to make that happen. This planning pass traced the actual mechanism:
`seed_founding_row` (`app/research/pnl_baseline.py:105`) looks up the ledger by
`config.pnl_founding_enhancement_id` — a fixed literal (`"founding-baseline-strategy-v1-default"`) —
and the `pnl_ledger` table's `enhancement_id` column is the store's SQL PRIMARY KEY
(`store.py:append_pnl_ledger_row`), so a second run under an unchanged id is refused as an idempotent
no-op ("already present") before the new fingerprint ever enters the picture. Literally following
goal.md's instruction as written, unmodified, would therefore silently fail to produce the required
new-epoch row (the CLI would just print "already present" and exit 0).
**We chose:** Scoped the fix narrowly: bump `Config.pnl_founding_enhancement_id` /
`pnl_founding_enhancement_title`'s literal DEFAULT VALUES — both already-existing era-3 J-04 fields,
not new fields, so the "no new Config fields" non-goal holds — to a new, distinct, self-documenting
string, landed in the SAME commit as the field deletions, before computing the one new pin (both
fields are fingerprint-INCLUDED by the module's own docstring, so they legitimately participate in
that one hash). `pnl_ledger.py`'s writer and `store.py`'s primary-key/`DuplicateEnhancementError`
discipline are NOT touched — that "one honest row per enhancement" guarantee is correct and
load-bearing; the fix works by giving the new epoch's row a different key, exactly as an operator
manually choosing a new enhancement id for a genuinely new enhancement would.
**Reversible:** yes — the exact literal chosen is cosmetic (any distinct, honest string satisfies the
mechanism); a different naming convention later only affects the NEW row's id/title, never the old row
or any pin.
