# goal-rapid-microscope-iter-14 Audit Report

**Date:** 2026-08-19
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

The phase goal is achieved: Scout Ledger, Walk-Forward and Validation Vault render on `/desk`
verbatim from their already-shipped endpoints, and the central mandate — that the new UI must not
reopen the subtraction attack the last four rounds closed — **holds under execution, not
inspection**. I built a real vault fixture through `vault.py`'s own API covering all three shard
stages and both universe stages, served it from a scoped backend, rendered it in Chrome, ran the
operator compute act first (TR-2's own discipline), and swept the rendered DOM plus every network
body for every withheld identity: zero leaks, with a passing counter-test proving the sweep was
live. Two IMPORTANT defects that review, QA and the browser lane all passed were found and fixed:
the Scout/Walk-Forward progress polls never stopped (they survived unmount and compounded one
immortal 700 ms backend poll per triggered run), and the Scout trial table's React key was the
candidate *spec* hash, so a second click of the button this iteration ships made every row a
duplicate-key child. Remaining gaps are documented, none of them opacity-related.

---

## 2. Findings

### Frontend Findings

**F1 — IMPORTANT (fixed): the Scout / Walk-Forward progress polls never stop — they survive unmount and compound one immortal backend poll per triggered run.**

`apps/frontend/app/desk/page.tsx:9934` (`pollScoutComputeUntilTerminal`) and `:9997`
(`pollWalkforwardComputeUntilTerminal`) as shipped. Both are plain `for (;;)` drivers awaiting
`refreshChainSleep(700)` with no stop signal of any kind, and `if (!next.ok || !next.data) continue`
means a permanently unreachable backend loops forever too.

Measured in Chrome against a scoped rig (compute GET stubbed to a permanent `running` so the
terminal exit could not mask the leak):

| observation | result |
|---|---|
| polls while `/desk` mounted | 700 ms cadence, correct |
| navigate away via `next/link` (`deskSectionStillMounted: false`) | polls continue: 15 → 21 → 27 over 8 s |
| return to `/desk`, trigger a second run, navigate away again | 5 → 11 → 12 polls / 4 s — a **second** immortal loop; the first never died |

This is the "guard satisfied in letter while its intent was evaded" shape the dispatch asked me to
look for, though the evaded rule is not the one the dev handoff names. Avoiding a new `useEffect`
kept `test_desk_refresh_chain_guard.py`'s 21/9/1 census green, but it also skipped the discipline
that makes that census safe — and this same file already owns that discipline and states it
verbatim at `page.tsx:10154-10161`: *"Unmounting (a nav away mid-chain) stops the driver at its
next check — no POST after the page is gone, no setState on an unmounted component, **no orphaned
wait loop**."* The Scout/Walk-Forward polls are the identical construct and were the one pair not
observing it.

**Fix applied** (`page.tsx`, current lines 9701-9711, 9962-9964, 9986, 10031-10033, 10052,
10189-10196): one `microComputePollStopRef` — a `useRef`, which spends no `useEffect(` /
`setInterval(` / `setTimeout(` literal — checked twice per loop iteration, raised by the page's
**existing** unmount cleanup effect (no second effect opened) and lowered by each trigger handler,
mirroring `refreshChainStopRef`'s own reset at `:10530` so a React StrictMode mount/unmount/mount
cannot wedge it.

Post-fix verification (all executed, not asserted):
- `pytest tests/test_desk_refresh_chain_guard.py tests/test_desk_ui_guards.py -q --junitxml` →
  **109 tests / 0 failures / 0 errors**; every other page.tsx-reading guard
  (`test_desk_hover_tooltip_guard`, `test_desk_screen_compare_ui_guard`,
  `test_desk_topup_library_reach_guard`, `test_desk_topup_window_disclosure_guard`,
  `test_referee_registry`) → **77 / 0 / 0**; plus `test_copy_discipline` + `test_mcp_server` +
  `test_meta_routes` in the 196-test guard batch → **0 failures**. The pinned 21/9/1 census still
  passes.
- `tsc --noEmit -p tsconfig.json` → exit 0.
- Live re-measure of the exact same experiment: polls freeze at **3** the instant `/desk` unmounts
  and are still 3 after 10 further seconds (`leaked: false`).
- Terminal path unbroken: a real run against the scoped backend still refreshes the ledger and the
  run log (run-history rows 1 → 2, button returns to "Run Screen", no Cancel).

**F2 — IMPORTANT (fixed): the Scout Ledger's trial rows are keyed by the candidate SPEC hash, so a second "Run Screen" makes every row a duplicate-key child.**

`apps/frontend/app/desk/page.tsx:6197` region as shipped — `family.trials.map((trial) => (<tr
key={trial.candidate_id} …>))`. `candidate_id` identifies the candidate *specification*, not the
ledger row. A second click of the very button this iteration ships re-registers the same bounded
reference grid, and `list_scout_families` then legitimately serves N trial rows per `candidate_id`.

Reproduced live on the scoped rig: after two runs, `GET /research/desk/micro/scout` served **4
trials per family with only 2 distinct `candidate_id`s** (distinct `registered_at`,
`superseded_by: null` on all four), and Chrome logged six copies of

> `Encountered two children with the same key, cand-c4b98c8f6a9a89e4. … Non-unique keys may cause
> children to be duplicated and/or omitted — the behavior is unsupported and could change in a
> future version.`

All four rows happened to render on that mount, so nothing is being dropped *today* — but React
does not guarantee that, on a surface whose entire purpose is "every candidate trial and kill
reason on the record". QA's UT-01 "no console errors" assertion held only because the real store
has zero scout families; a populated ledger breaks it.

**Fix applied** (`page.tsx:6220-6232`): `key={`${trial.candidate_id}-${trialIndex}`}`, with a
comment recording why the index is a sound tiebreak here (an append-only ledger rendered verbatim
in ledger order — rows are never reordered, inserted mid-list, or removed).

Post-fix verification: a **third** run (6 trials/family, 3 run-history rows) produced a console
carrying only the React DevTools info line — zero key errors — and rendered row counts still match
the served trial counts exactly. `tsc --noEmit` exit 0; the 109/77/196 guard runs above were all
taken after this fix.

**F3 — GAP (documented, not fixed): the Microscope Readiness section silently drops the endpoint's own withheld-shard disclosure.**

`apps/frontend/lib/types.ts:2514-2519` — `MicroReadinessResponse` declares only
`totals`/`shards`/`study_floors`/`integrity_errors`. `apps/backend/app/research/micro_readiness.py:477-496`
also serves `sealed_tranche` (`shard_count`, `symbol_days`, `by_universe`) and
`joinable_corpus.withheld_excluded`; neither is typed or rendered.

Demonstrated against my fixture: the endpoint returned `sealed_tranche: {"shard_count": 3,
"symbol_days": 3, "by_universe": {"starter-tranche-v1": {...}}}` and `withheld_excluded: 3`, while
the rendered section showed **"Distinct datasets 2"** with no on-screen statement that three shards
were withheld. Spec §7.5 point 6 is explicit that "Silent exclusion is forbidden", and the UI is a
served surface.

Not fixed, deliberately. It is pre-existing (the type dates to iteration 1 at commit `3f04090`;
`sealed_tranche` arrived at iteration 9), it is not introduced by this diff, and this phase spec
forbids this round from touching it ("No existing section's markup, `data-testid`, or heading
changes"); T-1 forbids improvising past that. I weighed IMPORTANT and settled on GAP for those
reasons — but it is the single highest-value item for iteration 15, because iteration 14 is exactly
the round that puts a populated Validation Vault on the same page as that understated total.

**F4 — OBSERVATION: `decay_view.fold_rows` is keyed by `fold_index` alone** (`page.tsx:6455`
region), the same class as F2. `walkforward.decay_view` (`walkforward.py:733-746`) does not dedupe,
but a re-run mints a new `sequence_id`, so fold indices are unique within a sequence and I could
not construct a duplicate. Left untouched — no demonstrated defect, and speculative hardening is
scope creep.

### Test Findings

**T1 — IMPORTANT (unresolved lane gap, closed by auditor probe): TC-13's explicit "not recorded `DEFERRED-BUDGET` again" was recorded `DEFERRED-BUDGET` again.**

`reports/phase-goal-rapid-microscope-iter-14-ui-test-results.md`, "Deferred (iteration budget)"
table: `UT-J-07 … DEFERRED-BUDGET … not run this iteration`. The phase spec's DoD item 4 and TC-13
name this regression by name ("J-07's `/research/desk/micro/graduation` route is genuinely
re-checked against the live backend (not recorded `DEFERRED-BUDGET` again)"). The QA report
nevertheless scores TC-13 ✓ PASS.

I closed the substance rather than leaving it open: `GET /research/desk/micro/graduation` against a
live backend → **HTTP 200**, `{"families":[],"message":"No candidates ledgered.",
"chain_verification":{"ok":true,"failed_at_row":null,"reason":null}}`; and
`pytest tests/test_micro_graduation.py --junitxml` → **19 tests / 0 failures / 0 errors**, which is
where J-07's own acceptance (the fixture walk plus the diagnostic-only and failed-sealed
counter-tests) actually lives. Recorded here so the evaluator does not read the DoD as met *by the
browser lane*: it was met by this audit.

**T2 — OBSERVATION: the QA report's TC-13 evidence claim states a method that cannot establish it.**
`reports/qa/goal-rapid-microscope-iter-14-qa.md:142` — "evidence files on disk verified by test
suite execution". A pytest run verifies no screenshot path. I verified it independently: **all 23
cited `…-evidence/*.png` files exist on disk**, including `J-01-verify.png` … `J-05-verify.png`. The
iteration-13 `evidence_makeup` debt IS genuinely closed for J-01–J-05 — the QA sentence's stated
method simply is not what closes it.

**T3 — OBSERVATION (positive): the widened `_PRICE_ARITHMETIC_FIELDS` is a real check, not decoration.**
Mutation-tested rather than read: injecting `family.variants_tried - 1` into `page.tsx` made
`test_desk_page_never_derives_a_price_via_arithmetic_on_distance_or_band_edges` FAIL, naming
`[('family.variants_tried', '')]`. Reverted (file byte-identical to the pre-mutation copy, `diff`
clean) and re-ran → 109 passed. Note the dev handoff calls this an "allow-list"; it is a *deny*-list
— adding a field strengthens the sweep, which is what the spec asked for, so the semantics are
right even though the naming is inverted.

### Prior findings re-checked — none re-filed, one escalated

| # | prior finding | re-check result |
|---|---|---|
| (a) | Scout never renders `family_root_id` | **Confirmed, severity unchanged.** The only `family_root_id` in `page.tsx` is line 6696 (the Vault shard row). Confirmed live against a populated ledger: the family header reads `cumulative_delta__none__trades_20 — 2 variants tried`, no root id anywhere. A genuine miss against the spec's "New information displayed" list; nothing on screen is *misstated*, so it stays a GAP. |
| (b) | Walk-Forward's empty state reuses "No candidates ledgered." | **Reachability upgraded.** I rendered it live (scoped store, zero sequences): the section really does show "No candidates ledgered." to an operator. It is a reachable user-visible state, not an unreachable copy-paste artifact — but still cosmetic. Not re-filed. |
| (c) | poll loops never check an unmount/stop signal | **Escalated and fixed — see F1.** The reviewer's MINOR/code-quality read understated it: it survives unmount, compounds per run, and is unbounded on a backend outage. |
| (d) | Vault's error state drops the `validation-vault-section` wrapper testid | **Confirmed** at `page.tsx:6598-6605` (`UnavailablePanel` is returned *instead of* the wrapper `<div>`); already executed live by browser-QA UT-10, which found the correct amber typed error in all three sections. Severity unchanged. |

---

## 3. Domain Assessment

### The opacity mandate (TC-15 / TR-2 / TR-27 / TR-28) — verified by execution

The dev verified the Vault's two-stage paths by TypeScript exhaustiveness; the reviewer hand-traced
a fixture's JSON through the JSX. Neither ran it. I did.

**Fixture** (built through `vault.py`'s own public API — `register_universe` / `seal_shard` /
`assign_shard` / `expose_shard` — reusing the shape of `test_vault.py`'s TR-2/TR-27 subtraction
test, into a scratchpad dataset dir so the real store was never touched):

- universe `starter-tranche-v1`: 2 symbols × 2 dates, **not** fully released → `committed`
  - `ZQXBBB/2031-03-17` → **sealed**
  - `ZQXAAA/2031-03-17` → **assigned**
  - `ZQXAAA/2031-03-18` → **exposed**
  - `ZQXBBB/2031-03-18` → recorded, never ledger-tracked (an untracked pool member)
- universe `released-tranche-v1`: 1 × 1, fully exposed → `revealed`

All four shard/universe rendering paths therefore appear in **one** payload on **one** page — TC-4
and TC-5 are exercised for real for the first time.

**Rendered result** (`reports/qa/goal-rapid-microscope-iter-14-evidence/AUDIT-vault-fixture-both-stages.png`,
1.58 MB full-page): 4 shard rows with states `sealed / assigned / exposed / exposed`; the sealed row
shows the surrogate `vshard-…`, universe, `~10^0` bucket, HMAC commitment, `sealed_at`, `sealed`,
and then **seven consecutive `sealed — opaque` cells** — no symbol, no date, no dataset id, no
family root, no raw checksum. 2 universe rows with disclosures `committed / revealed`; the committed
row shows `2 (size only — committed)` twice and `committed — no nonce yet`; the revealed row shows
`ZQXCCC`, `2031-04-01` and the nonce.

**The sweep** — run *after* the operator compute act (a real 6/6-candidate Scout screening run
completed against the fixture corpus), because TR-2's own text requires the rig to have computed
something before sweeping, and with every `<details>` force-opened so the JSON dumps were in the
DOM text too:

| withheld value | in rendered HTML | in visible text | in any network body |
|---|---|---|---|
| sealed symbol `ZQXBBB` | no | no | no |
| sealed `dataset_id` | no | no | no |
| sealed raw `content_checksum` | no | no | no |
| untracked member's `dataset_id` | no | no | no |
| untracked member's checksum | no | no | no |
| assigned-but-withheld checksum | no | no | no |

Counter-test (so "absent" means something): every value that *is* legitimately public — `ZQXAAA`,
`ZQXCCC`, the exposed content checksum, the sealed shard's HMAC commitment, the surrogate shard id,
the revealed nonce — was found present in the same sweep. The sweep is live.

**Cross-section inference (the part the dispatch specifically asked for).** Each section issues only
its own endpoints — the instrumented fetch log for a full expand cycle is exactly
`micro/readiness`, `micro/scout` + `micro/scout/runs`, `micro/walkforward` + `micro/walkforward/runs`,
and one `micro/vault`. `ValidationVaultSection` takes a single `vaultResult` prop and nothing else
(`page.tsx:6590-6594`); no client-side join exists to make. The readiness endpoint independently
withheld all three unresolved pool members and reported them only as aggregates. The union of every
value the page renders is therefore a subset of the union of the four endpoints' own bodies:
**the frontend adds no inference surface beyond what `GET /research/desk/micro/vault` already
discloses.** TC-6 and TC-15 hold.

Under the governing test — registered universe granted, plus everything the page shows — the still-
unexposed members of `starter-tranche-v1` reduce to `{ZQXBBB/2031-03-17, ZQXBBB/2031-03-18}`, and
the page shows exactly **one** opaque `sealed` row among them. Which of the two is the sealed shard
is not determinable: §7.5 point 7's "unexposed pool members stay mutually indistinguishable" holds
through the new UI layer.

One structural residue worth stating plainly, as an **OBSERVATION, not a finding**: because §7.5
reveals symbol and date at *assignment*, a pool whose members have all-but-one left through
assignment/exposure identifies its last member to anyone who knows the rule. That is the spec's own
design (and the reason the rule stays `committed` publicly until whole-pool release), it is owned by
`vault.py`, it is unchanged by this iteration, and §7.6's ≥30-symbol-day starter tranche keeps real
pools far from that edge. Nothing in this diff moves it.

### Verbatim-rendering and honesty

Spot-checked the served JSON against the DOM on the populated paths: the Walk-Forward fold table,
sequence verdict and recency line were byte-matched by the dev and re-confirmed structurally here;
the Scout trial table renders `withheld_excluded: 3` per trial (a count, never ids — §7.5 point 6
satisfied at the UI layer, which makes F3's readiness omission the odd one out rather than the
pattern). Nested candidate/fold-shaped payloads are dumped verbatim via `JSON.stringify` rather than
guessed field-by-field, so nothing served is silently dropped — a good call.

### Definition of Done

| # | DoD item | verdict | basis |
|---|---|---|---|
| 1 | Scout + Walk-Forward render (TC-1, TC-2, TC-9) | met | reviewer PASS (`spec_alignment: complete`) + executed QA rows UT-02, UT-03 against the running system |
| 1b | TC-7 / TC-8 compute controls | **met by this audit** | browser-QA did **not** execute them (UT-05/UT-07 "NOT clicked"; UT-06/UT-08/UT-09 SKIP) and dev saw only the head of the chain. I executed both: Scout idle → "Screening…" disabled + "1 / 6 candidates" + Cancel; Walk-Forward idle → "Running…" disabled + "4 / 12 steps" + Cancel → Cancel → `POST …/walkforward/compute/cancel` called exactly once → idle terminal state, loop stopped, no hang |
| 2 | Vault renders read-only; opacity holds across **both** shard and **both** universe stages (TC-3–TC-6, TC-15) | met | full trace above, on a real fixture, rendered and swept |
| 3 | J-08 scored `partial` | on track | dev handoff and spec both say panels-only; MCP half deferred |
| 4 | J-01–J-05, J-07 green with REAL evidence on disk (TC-13) | **partial** | J-01–J-05 replay PASS with all cited evidence confirmed present on disk; **J-07 was `DEFERRED-BUDGET` again** — see T1, closed by my own probe |
| 5 | No anti-goal violation; auditor re-runs the TR-2/TR-27/TR-28 sweep on the rendered page | met | §3 above |
| 6 | Zero client-side arithmetic (TC-9) | met | guard green **and** mutation-tested (T3) |
| 7 | `EXPECTED_TOOLS` still exactly 22; zero MCP file touched | met | parsed the literal → 22 names; `git status apps/backend/app/mcp/` empty |
| 8 | Frozen rails (TC-11) | met | `Config().config_fingerprint()` → `08e471b10130e1e2` (live import); `config.py` diff empty; all six `referee_*.py` diffs empty; `micro_chain_ledger.py`, `vault.py`, `scout.py`, `scout_ledger.py`, `walkforward.py`, `walkforward_ledger.py`, `micro_routes.py`, `micro_readiness.py`, `docs/rapid-validation-spec.md` all byte-untouched |
| 9 | Full suite ≥ 3228 collected, 0 failures (TC-10) | met | my own run, `--junitxml`: **tests=3228, failures=0, errors=0, skipped=8** (625 s) — 3220 passed, exactly the claimed baseline |
| 10 | Unit tests pass, no regressions | met | above, plus 273 page.tsx-reading guard tests green after my fixes |
| 11 | Dev handoff written | met | present, and unusually honest — it discloses the un-verified TC-4/TC-5/TC-8 gaps rather than papering over them, which is what let this audit go straight to them |

Only the four authorized files are modified (`git status apps/` → `test_desk_ui_guards.py`,
`desk/page.tsx`, `lib/api.ts`, `lib/types.ts`), including after my fixes.

---

## 4. Fixes Applied During This Audit

| # | Severity | File | Change |
|---|----------|------|--------|
| 1 | Important | `apps/frontend/app/desk/page.tsx` | F1 — added `microComputePollStopRef` (a `useRef`, so the pinned 21/9/1 effect/interval/timeout census is untouched), checked twice per iteration in both `pollScoutComputeUntilTerminal` and `pollWalkforwardComputeUntilTerminal`, raised by the page's **existing** unmount cleanup effect and lowered by each trigger handler. Stops the orphaned, compounding post-unmount polling loop. |
| 2 | Important | `apps/frontend/app/desk/page.tsx` | F2 — Scout trial rows keyed `${trial.candidate_id}-${trialIndex}` instead of the candidate spec hash alone, so a re-run's legitimately repeated `candidate_id` no longer produces duplicate React keys on the "every trial on the record" table. |

Both fixes are confined to the two findings — `git diff` on my own edits contains nothing else (the
only lines I touched are the ref declaration, four loop guards, two resets, one line inside the
existing unmount cleanup, and the one `key=` expression). Evidence for each is cited inline in §2:
suite/guard runs with `--junitxml` counts, `tsc --noEmit` exit 0, and a live before/after
measurement in Chrome for each.

Nothing in the dev handoff is invalidated by these fixes except its "Known Issues" bullet on
mid-run reload resilience, which is unchanged and still accurate, and its third bullet's framing of
the poll design as a clean trade — it now also observes the file's own unmount-stop contract.

---

## 5. Recommended Next Step

**Proceed to iteration 15** (the four MCP proxy tools plus the `EXPECTED_TOOLS` 22 → 26 bump), with
three items carried:

1. **F3 first, inside iteration 15's own scope** — extend `MicroReadinessResponse` and the
   Microscope Readiness section to render `sealed_tranche` and `joinable_corpus.withheld_excluded`.
   It is a one-section change, it closes a "silent exclusion is forbidden" gap at the UI layer, and
   it matters more now that a populated Vault can sit on the same page as an understated corpus
   total. Iteration 14 was contractually barred from touching that section; iteration 15 is not.
2. **The two recorded MINORs** — render `family_root_id` in the Scout family header (the spec's own
   "New information displayed" list names it) and give the Walk-Forward empty state its own copy
   ("No sequences ledgered."). Both are now confirmed live, both are one line.
3. **T1's process point** — J-07 has now been deferred by the browser lane in two consecutive
   iterations while the DoD named that exact regression. Its route and its 19 fixture tests are
   green (I checked), so nothing is broken; the lane's budget-trim rule is what needs the
   attention, not the product.

When the MCP half lands, the four new proxies must be swept with the same fixture-and-render
methodology used here rather than field-inspected — the MCP surface is a served surface, and this
era's record is that the opaque-pool fault class is only ever caught by executing it.
