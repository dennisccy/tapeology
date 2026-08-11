# Goal Iteration 9 — MCP contract v4 (20 tools) + the kept-product regression sentinel closes the era

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** playbook
- **Iteration:** 9
- **Mode:** next
- **Depth:** full
- **Full trigger:** 1 — Structural/cross-cutting: J-09 edits the shared MCP contract module
  (`app/mcp/__init__.py`'s `_STATIC_PATHS`, read by every MCP client) and J-10 audits/re-verifies
  the ENTIRE kept product (cockpit, `/structure`, every shipped `/desk` section, the MCP tool
  list, kept-route byte-identity, and the era's cumulative diff against its declared inventory) —
  more than 3 modules whose interactions no single journey's own tests cover. This is also the
  explicit "run it as a deep iteration with the auditor" request the evaluator has now made twice
  (iter-6 and iter-8 next-step recommendations) for exactly this closing pass.
- **Frontend Present:** yes
- **Target journeys:** J-09, J-10
- **Required-still-passing journeys:** J-01, J-02, J-03, J-04, J-05, J-06, J-07, J-08 (full
  regression widen — see BACKGROUND)
- **Anti-goal reminders:**
  - No execution path, ever — no brokerage/trading API, no order tickets, no live OR paper
    trading, no "just to test" exceptions. *(critical)*
  - No profit claims and no advice — every $ figure is a simulated measurement carrying R, n,
    fee/slippage assumptions, and its train/hold-out/forward basis. No prediction language, no
    imperative trading cues. *(critical)*
  - Frozen foundations — the `v1` strategy, the `default` profile, the tape engine's five states
    and thresholds, the frozen structure computations, the JSON `BarStore`, and every KEPT
    surface's behaviour stay byte-identical. New work is additive and versioned beside them, never
    a mutation of them. *(critical)*
  - Hold-out-only promotion — the champion pointer moves only on a genuine hold-out survival
    through the sweep gate (plus the era-6 statistical gates once they exist). Train-only wins are
    labeled overfit. Never lower a minimum sample size, widen a gate, or pool across
    feeds/fingerprints to manufacture a survivor. *(critical)*
  - No lookahead — every value computed as-of T uses only events/bars fully completed at T.
    *(critical)*
  - Single source of truth — each shared value is computed once, owned by one canonical endpoint,
    and read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor hard-fails violations.
    *(critical)*
  - Deterministic and seeded — every random draw uses a config-owned recorded seed; identical
    requests reproduce byte-identical results; no wall-clock, no unseeded randomness in any
    research artifact.
  - Read-only MCP — MCP tools remain byte-identical proxies of GET endpoints; nothing on the MCP
    surface can change state. *(critical)*
  - Immutable data — registered datasets and bar series are append-only, checksummed, never
    re-tagged, never deleted, never content-perturbed. Splits are frozen at registration.
    *(critical)*
  - Persistence stays scoped — no ambient recording of live streams; recording/fetching is an
    explicit, logged act. *(critical)*
  - Era-B desk anti-goals that remain binding: membership is never a signal; snapshots are
    append-only and pinned; every run is an explicit operator act; the briefing describes, never
    advises; no new statistics, gates, or strategies; the demolition stays demolished; the ledger
    never holds orders; the suite stays keyless and hermetic; the fingerprint pin does not move.
    *(all critical)*
  - No threshold exists outside the spec, and no code path sweeps one. Every detector rule and
    threshold exists in `docs/playbook-detector-spec.md` BEFORE the code that uses it; no code
    path iterates thresholds against outcomes (source-scan guard-tested); a threshold change is a
    spec revision + new signature, never an edit of recorded signals and never a sweep. *(critical)*
  - A signal is an observation, not a call. No signal, chip, or evidence cell uses advice,
    imperative, prediction, probability, expectancy, edge, or significance language; the served
    registers state what was NOT measured (no fills, no costs, returns not stop-adjusted);
    `invalidation_price` is geometry, never an order concept. *(critical)*
  - The evidence pools one signature. Distributions never mix parameter regimes; other signatures
    are listed, not merged; the min-n floor tags, it never filters; truncated values never enter a
    pool undisclosed. *(critical)*
  - No recorded playbook file is ever rewritten, backfilled, pruned, or superseded in v1. New
    signatures mint new versions beside old ones; a corrupt file is surfaced loudly, never
    overwritten; the store exposes no update or delete method (source-scan guard-tested).
    *(critical)*
  - No second implementation of the measurement rail. Measurement helpers are imported from
    `desk_forward.py` with a zero diff to that file; no playbook module re-implements horizons,
    MDD, truncation, or the seed discipline (import-graph guard-tested). *(critical)*
  - The enhancement loop stays inside its box — the goal-proposer may append journeys ONLY inside
    the `AUTO:journeys` marker block; it MUST NOT edit human-authored journeys, the Anti-goals
    section, or any other part of `docs/goal.md`. *(critical)*
  - Host-guard caps are law — never disable, widen, or bypass the declared CPU/BLAS/memory
    ceilings to make a run faster or a pause go away. *(critical)*

## GOAL

The operator can now reach the entire playbook (signals + evidence) through Claude/MCP exactly
like the rest of the desk (18 → 20 read-only tools), and the whole kept product — cockpit,
`/structure`, and every shipped `/desk` section, plus the playbook's own new sections — is proven
to still work byte-identically, closing Era B2 "The Playbook."

## BACKGROUND

Eight of ten journeys are passing (J-01 through J-08, all shipped iterations 1-8). The iter-8
evaluator's next-step recommendation named this exact pairing explicitly: "Build J-09 ... next —
add the two read-only Claude tools ... and then close J-10 ... by walking the whole product in a
real browser ... This is the last piece of the era, so run it as a deep iteration with the
auditor." Per the priority rubric, J-09 is a textbook unblocker (J-10's own acceptance names
"exactly 20 tools", and it stays `partial` until J-09 lands), and pairing it with J-10 in one full
pass matches the evaluator's own framing of these two as the era's closing act, not two
independent risky changes — J-09 is a small, mechanical, already-scoped dict-entry + test-contract
change (near-zero risk on its own), so this is one risky item (the full-product regression walk)
plus one trivial one, not two risky items (rule 5).

This iteration also carries the four cheap items the iter-8 evaluator flagged, all directly
protective of J-10's own biggest risk (the widest browser walk of the whole era, exactly the
surface the store-scope guard exists to protect): extend the guard to abort (not just disclose) a
detected breach at its two existing call sites, close the third ungated lane (the browser-qa
agent's own direct browser-driving path), and stop the guard's fixture-forcing from applying
repo-wide beyond this project. It also closes the still-open golden-replay gap for J-08 (no stored
script exists yet — T-11) and surfaces the evidence table's already-served `signature` field in
the UI (iter-8 carry item; the field is already returned by `GET /research/desk/playbook/evidence`
per `desk_playbook_evidence.py:407` and already typed in `apps/frontend/lib/types.ts:1789`, just
never rendered).

Given J-10 is a full-product regression pass, this iteration widens Required-still-passing to ALL
eight currently-passing journeys (J-01–J-08) rather than a smoke subset — the "every few
iterations, widen to a full regression" guidance and the era-close moment coincide here.

Lessons applied: (iter-8) a screenshot's filename is a claim, not evidence — the auditor/evaluator
must open every J-10 screenshot itself, never trust a QA report's ✓ marks or filenames; (iter-3/
iter-6/iter-8) a safe launcher nothing is obliged to use is not a mechanism, only a gate is — this
is why the store-scope carry items convert "disclose" into "abort"; (iter-7) never assert replay
text that also appears in a static blurb — the new J-08 golden script must target a
statically-rendered, section-unique string (T-11). Two owner-ruling questions from iter-6/iter-7/
iter-8 remain open (ratify/reject the §3.7 `range_trade` clarification; settle the three
narrower-than-spec disclosures) — human-owned, untouched by design (priority rubric rule 6);
neither blocks J-09 or J-10.

## IN SCOPE

### Backend
- [ ] Add `desk_playbook` → `/research/desk/playbook` and `desk_playbook_evidence` →
  `/research/desk/playbook/evidence` to `_STATIC_PATHS` (`apps/backend/app/mcp/__init__.py:86`) —
  both are no-required-param shapes (mirroring `desk_forward`/`desk_screen`): the base read serves
  an honest-empty or newest-record payload; the `?date=`/`?id=`/`?signature=` parameterized reads
  stay reachable only through the existing `get_endpoint`'s `/research/` allowlist (zero new route
  code).
- [ ] Update `apps/backend/tests/test_mcp_server.py`'s `EXPECTED_TOOLS` (and every place that
  asserts a tool count) to the 20-tool contract; add byte-identity coverage for both new tools
  against an EMPTY fixture backend (no playbook records) and a POPULATED one (at least one
  recorded playbook record with signals), mirroring the existing `desk_forward`/`desk_screen`
  coverage pattern; extend the honest-error/dead-backend coverage to the two new tools.
- [ ] Full backend suite + engine equivalence re-run to completion; confirm
  `Config().config_fingerprint()` still prints `08e471b10130e1e2`; confirm via `git diff` that
  `desk_forward.py`, `desk_playbook_detect.py`, `desk_playbook.py`, `docs/playbook-detector-spec.md`,
  `docs/goal.md`, `config.py`, `meta.py` all stay byte-unmodified (per the binding Do-not-redo
  list).
- [ ] Kept-route byte-identity check: diff every non-playbook backend route's response shape
  against the era-open baseline; confirm the only two exemptions are the MCP tool list (18→20) and
  the playbook routes this goal's own Data Contract adds; surface anything else as a defect before
  it lands.
- [ ] Confirm the era's cumulative diff (iterations 1-9 combined) stays inside the goal's declared
  inventory (the `desk_playbook*` modules/routes/sections/tools, the named guard-test extensions,
  and SPY freshness in the top-up walk) — anything outside it is surfaced, not silently merged.
- [ ] Store-scope guard hardening (extends the existing `require`/`snapshot`/`verify` mechanism
  built at iter-7/iter-8; changes no protected-path list, no assert/prepare commands):
  1. At both existing call sites (`browser-qa-phase.sh:250`, `goal-iter-lean.sh:350`), a `verify`
     BREACH now aborts/fails the calling lane's run rather than only writing a disclosure artifact
     and continuing.
  2. Gate the browser-qa agent's own direct browser-driving path (the third lane the iter-8 audit
     found ungated) with the same `require` call before it touches a browser.
  3. Scope the guard's fixture-forcing (`project-extensions/store-scope/store-scope.env`) so it
     applies to this project's own automation only — it must not force playbook test data onto a
     future unrelated project's lanes.
  - If any of these three prove out of a normal developer's reach inside this iteration's budget
    (they live in framework automation code, not app modules), drop the specific item, record why,
    and carry it forward rather than block J-09/J-10 (T-1's own escape hatch).
- [ ] Record `runs/goal-session-playbook/journey-scripts/J-08.json`, a stored golden replay script
  for the Playbook Evidence section, mirroring the J-06/J-07 pattern (fixture-scoped backend,
  asserts on a statically-rendered string unique to the Evidence section — never async list text,
  never a word that also appears in a blurb, per the iter-7 J-05 lesson).

### Frontend
- [ ] `/desk` Playbook Evidence section (`apps/frontend/app/desk/page.tsx`,
  `PlaybookEvidenceSection`): render the already-served `data.signature` field as a visible line
  (e.g., "Built from signature: <value>") above or beside the existing `data.register` disclosure
  paragraph — the same treatment `desk-evidence-other-signature-row` already gives other
  signatures, so every signature the section discusses (default and other) is now named on screen.
  No new API call, no new type field (`DeskPlaybookEvidence.signature` already exists in
  `apps/frontend/lib/types.ts:1789`).

### New user-facing capability
The operator (directly or through Claude/MCP) can now read both the playbook signal record and
the evidence distribution table via two new read-only MCP tools, completing conversational access
to Era B2's whole surface. On `/desk`, the Playbook Evidence section now discloses which input
signature its distributions were built from.

### New information displayed
The evidence table's built-from signature (already computed and served, never rendered) is now
visible on screen next to the section's disclosure paragraph.

### New user actions
None — no new buttons, forms, or controls. The two new MCP tools are read-only proxies, not
interactive UI elements.

### UI surface changes
One new text line inside the existing Playbook Evidence section on `/desk`. No new pages, panels,
cards, or nav entries.

### Product surface delta
The MCP surface grows from 18 to 20 read-only tools (contract v4), completing Key Capability #6.
The kept three-route product (Cockpit `/`, Structure `/structure`, Desk `/desk`) is re-verified
byte-identical end to end. No nav or route change.

### Blueprint conformance
J-09 has no page — it is the MCP tool surface only, proxying the already-registered "Playbook
records" and "Evidence aggregates" rows (blueprint's Data Contract), per the blueprint's own J-09
row ("MCP tool surface only; no page"). J-10 spans the blueprint's whole Information Architecture
(Cockpit, Structure, Desk, every shipped section) — its home is "every kept surface," per the
blueprint's own J-10 row. The Playbook Evidence signature display lives under the already-existing
"Evidence aggregates" home (`/desk`, Playbook Evidence section) — no new page, no nav-skeleton
change. `runs/goal-session-playbook/state/blueprint.md` updated (additive status edits only — see
below); no `blueprint.reapproval-requested` file needed.

### Data-contract additions
None. The `signature: string` field displayed this iteration is already part of the registered
"Evidence aggregates" row (owner `apps/backend/app/research/desk_playbook_evidence.py`, served by
`GET /research/desk/playbook/evidence`, already typed in `apps/frontend/lib/types.ts:1789` as
`DeskPlaybookEvidence.signature`) — this iteration only renders an already-served field; it
introduces no new value, computing module, or endpoint. The two new MCP tools (`desk_playbook`,
`desk_playbook_evidence`) are byte-identical GET proxies of the already-registered "Playbook
records" and "Evidence aggregates" rows — same owners, same endpoints, no new row.

## OUT OF SCOPE

- The two owner-ruling questions carried since iter-6/iter-7/iter-8 (ratify/reject the §3.7
  `range_trade` degenerate-trigger clarification; settle the three places where shipped code reads
  the spec more narrowly than written) — human-owned, untouched by design.
- Any new detector family, measurement change, or spec revision. The detector set (J-01–J-08) is
  complete; `docs/playbook-detector-spec.md` stays byte-unmodified this iteration.
- A redesign of the store-scope guard's protected-path list, assert/prepare commands, or manifest
  mechanism — only the three named hardening items (abort-on-breach, third-lane coverage,
  project-scoped forcing) are in scope; the shipped shape stays.
- Any `Config` field addition or fingerprint move. Zero new fields expected; the pin
  `08e471b10130e1e2` does not move.
- Any change to `desk_forward.py`, `desk_playbook_detect.py`, `desk_playbook.py`'s detection or
  measurement logic, `docs/playbook-detector-spec.md`, `docs/goal.md`, `config.py`, `meta.py`, or
  any other file the binding Do-not-redo list names as zero-diff.
- Re-recording golden scripts for J-01–J-07 (they already exist and replay green) — only J-08's
  gap is closed this iteration.
- A real (non-fixture) back-scan or playbook compute over the operator's live universe — every
  compute this iteration touches stays on the fixture-scoped rig.

## DEFINITION OF DONE

- [ ] J-09 passes: MCP tool count = 20 including `desk_playbook`/`desk_playbook_evidence`; both
  byte-identical to their curl equivalents in empty AND populated fixture states; `get_endpoint`
  proxies the parameterized reads verbatim; MCP suite green.
- [ ] J-10 passes via browser-qa-agent (full kept-product walk, screenshot per section) and
  deterministic replay (`journey-scripts/J-10.json`); kept-route byte-identity confirmed outside
  the two named exemptions; nav = exactly three routes; MCP = exactly 20 tools; era's cumulative
  diff stays inside its declared inventory.
- [ ] Required-still-passing J-01–J-08 remain green (deterministic replay where a golden exists —
  J-01 through J-07 — plus LLM browser-qa fallback for J-08 until its own golden lands this
  iteration).
- [ ] No anti-goal violation introduced: MCP stays a byte-identical read-only proxy; no `Config`
  field added; fingerprint pin unchanged; no recorded playbook file rewritten/pruned; store-scope
  guard tightened, not weakened.
- [ ] Full backend suite green; pass count ≥ 2158 (the iter-8 floor) and ≥ 1926 (the era-open
  floor); skip count = 8; no regressions.
- [ ] `journey-scripts/J-08.json` recorded and replays green on the fixture rig.
- [ ] Store-scope guard: a detected breach at either existing call site now aborts the lane; the
  browser-qa agent's own direct browser-driving path is gated; the fixture-forcing is scoped to
  this project only (or each item explicitly dropped-and-recorded per the escape hatch, not
  silently skipped).
- [ ] Playbook Evidence section on `/desk` visibly shows the built-from signature (screenshot).
- [ ] Dev handoff written at `docs/handoffs/goal-playbook-iter-9-dev.md`.

## TESTING REQUIREMENTS

- Browser: J-10 (full kept-product walk — cockpit sim tape + chart, `/structure` pinned-AAPL Load,
  every shipped `/desk` section, plus the Playbook Evidence signature display); J-08 (fresh golden
  replay recording).
- Unit/integration: `test_mcp_server.py` 20-tool contract + byte-identity for the two new tools in
  empty and populated states; full backend suite + engine equivalence; kept-route byte-identity
  diff against the era-open baseline; store-scope guard abort-on-breach behavior.
- Error cases: an unscoped backend under test must be REFUSED by the guard's `require` step (no
  lane dispatches); a detected mid-run breach must ABORT the lane (not merely disclose); a
  malformed/unreachable backend for the two new MCP tools must return the same honest-error shape
  `get_endpoint` already gives dead backends.

Test-first contract: every DEFINITION OF DONE checkbox and every Data-contract addition above maps
to at least one concrete scenario line, numbered sequentially, of exactly this shape:

- TC-1: given the backend MCP server after this iteration's change, when a client calls
  `tools/list`, then exactly 20 tool names are returned, including `desk_playbook` and
  `desk_playbook_evidence`.
- TC-2: given an EMPTY fixture backend (no recorded playbook records), when the MCP client calls
  `desk_playbook` with no arguments, then the response body is byte-identical to
  `curl GET /research/desk/playbook` on the same fixture (honest-empty shape, HTTP 200).
- TC-3: given a POPULATED fixture backend (at least one recorded playbook record), when the MCP
  client calls `desk_playbook`, then the response body is byte-identical to
  `curl GET /research/desk/playbook` (same record content and field shape).
- TC-4: given an EMPTY fixture backend, when the MCP client calls `desk_playbook_evidence`, then
  the response body is byte-identical to `curl GET /research/desk/playbook/evidence` (honest-empty
  cells, HTTP 200).
- TC-5: given a POPULATED fixture backend, when the MCP client calls `desk_playbook_evidence`,
  then the response body is byte-identical to `curl GET /research/desk/playbook/evidence`,
  including the `signature`, `cells`, and `register` fields.
- TC-6: given the MCP client, when it calls `get_endpoint` with
  `/research/desk/playbook?date=<recorded-date>`, then the response is byte-identical to the
  direct curl call on the same path (the parameterized read proxies verbatim).
- TC-7: given the full backend suite, when it is run to completion, then it exits 0 with pass
  count ≥ 2158 and skip count = 8.
- TC-8: given `Config().config_fingerprint()`, when invoked after this iteration's diff, then it
  prints `08e471b10130e1e2` unchanged.
- TC-9: given a real browser session on the freshly rebuilt (`rm -rf apps/frontend/.next`)
  frontend, when the operator opens the Cockpit page, then a screenshot shows the sim tape + chart
  rendering exactly as shipped.
- TC-10: given the same browser session, when the operator loads `/structure` and runs the
  pinned-AAPL Load, then a screenshot shows the structure levels/zones exactly as shipped.
- TC-11: given the same browser session, when the operator scrolls `/desk`, then screenshots show
  every shipped Era-B section (screen history calendar, forward returns, refresh chain + compute
  controls, ranked briefing, skipped members, runs/pins/compare/provenance) rendering unchanged.
- TC-12: given the era-open baseline route capture, when this iteration's kept routes are diffed
  against it, then every route matches byte-for-byte except the MCP tool list (18→20) and the
  newly-added playbook routes; any other delta is flagged as a defect in the auditor's report.
- TC-13: given the `/desk` Playbook Evidence section on a fixture rig with at least one recorded
  signature, when the operator opens the section, then a visible line names the built-from
  signature, matching the response's `signature` field value (screenshot).
- TC-14: given a browser lane (replay or LLM) whose backend-under-test is NOT the scoped fixture
  rig, when the store-scope guard's `require`/`verify` step runs, then the lane is refused/aborted
  (no dispatch, or a mid-run abort on breach) rather than merely disclosed.
- TC-15: given the browser-qa agent's own direct browser-driving path, when it launches against an
  unscoped backend, then the same guard gates it (previously this lane was ungated — confirmed
  fixed or explicitly dropped-and-recorded).
- TC-16: given `journey-scripts/J-08.json` freshly recorded, when it is replayed against the
  fixture rig, then it passes deterministically, asserting on a statically-rendered string unique
  to the Playbook Evidence section.
- TC-17: given the store-scope guard's fixture-forcing behavior, when it runs inside a different
  (non-tapeology) project's automation, then it does not force playbook test data onto that
  project (scoped to this project only — confirmed fixed or explicitly dropped-and-recorded).

## NOTES

- The evaluator's own next-step recommendation (iter-8 eval.md) named this exact pairing
  ("Build J-09 ... and then close J-10 ... run it as a deep iteration with the auditor") — this
  spec follows it verbatim rather than re-deriving scope.
- Lesson (iter-8): a screenshot's FILENAME is a claim, not evidence — whoever scores J-10 must
  open every cited screenshot itself and confirm it shows what it is cited for, never trust a QA
  report's ✓ marks or filenames at face value.
- Lesson (iter-3/iter-6/iter-8): a safe launcher nothing is obliged to use is not a mechanism —
  only a gate is. The store-scope hardening items convert the existing disclose-only `verify` into
  an abort-on-breach gate; if the framework-automation edits prove out of a normal developer's
  reach this iteration, drop and record rather than block J-09/J-10 (escape hatch, not a silent
  skip).
- Lesson (iter-7): never assert replay text that also appears in a static blurb — J-08's new
  golden script must target a string unique to the rendered evidence cells or breach table, not
  the section's own disclosure paragraph.
- Two owner-ruling questions remain open (§3.7 `range_trade` ratification; the three
  narrower-than-spec disclosures) — human-owned, explicitly out of scope this iteration.
- If this is genuinely the era's last iteration once J-09/J-10 pass, the evaluator should confirm
  whether GOAL_ACHIEVED applies; the proposer's usual dry-stop review (any new AUTO:journeys
  candidates) still runs per its own process.
