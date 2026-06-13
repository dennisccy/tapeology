# Goal Iteration 25 — J-66 cue-discipline sweep: all-surface copy walk, copy-lint test, sound cue OFF-by-default

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_will_be_super_rich_with_my_loved_ones
- **Iteration:** 25
- **Mode:** next
- **Depth:** lean
- **Frontend Present:** yes
- **Target journeys:** J-66
- **Required-still-passing journeys:** J-01, J-08, J-38, J-53, J-59, J-60, J-61, J-63, J-65, J-67
- **Anti-goal reminders:**
  - "**No unsolicited or unconditional trade commands.** Every actionable cue MUST be gated on a user-declared thesis with an invalidation, rendered as named checks with margins and evidence, in present-tense descriptive language. No imperative buy/sell/enter/exit wording, no price targets, no certainty language — anywhere. A hint is a logged description of a forming pattern, never a command and never a thesis by itself. *(critical)*"
  - "**No prediction language.** A verdict or stance describes what the tape is doing **now** relative to the declared thesis — never a forecast of what price will do. *(critical)*"
  - "**No trade/profit claims.** The product MUST NOT claim profitability or present output as trading advice; tape state is descriptive, not prescriptive."
  - "**Source, feed, and config honesty.** Every research record MUST be stamped with its bound source, its `data_feed`, and a `config_fingerprint` over the entire frozen config; … SIP-derived research MUST NOT be presented as validating IEX-live behaviour without the explicit basis label. *(critical)*"
  - "**No magic numbers.** Every window length, threshold, large-print size, impact/absorption cutoff, and confidence boundary MUST come from config — no such literal in engine/classifier code." (the session extends this to research code: every research value is a documented config default)
  - "**The research layer is read-only over the engine.** … the same event stream yields **byte-identical** tape state/confidence/features/history with or without an active thesis or attached observers (equivalence-tested). *(critical)*"

## GOAL

Every research surface provably speaks in present-tense, descriptive, thesis-attributed language — enforced by an automated copy-lint test — and the optional sound cue ships OFF-by-default, transition-only, cooldown-gated, with an explicit toggle.

## BACKGROUND

The iter-24 evaluator recommended J-66 at lean depth: with J-67's feed badge landed, the cue surface is COMPLETE, so the cue-discipline sweep can now audit everything at once — it is the last cue-layer journey before the J-68 backlog, the final items before GOAL_ACHIEVED consideration. Three per-surface copy-discipline seed checks already exist in `apps/backend/tests/test_research_api.py` (~lines 102, 134, 162 — stance, checklist, feed-basis strings); the sweep generalizes them into a comprehensive lint. The reviewer NOTE from iter-24 folds in: `apps/backend/app/research/routes.py:1207` and `:1232` pre-stamp study `data_feed = "sip"` with literals instead of the registered row-26 canonical mapping (pre-existing, non-regression — but it is exactly the feed-honesty drift the sweep exists to close). The evaluator's "opportunistic J-67 live-IEX pixel capture" is NOT possible this iteration: today is Saturday 13-06-2026 and the next US market open is 15-06-2026 14:30 UTC+01:00 (iter-24 lesson: the live badge is market-hours-gated, not merely credential-gated) — the gated leg stays documented, never faked.

## IN SCOPE

### Backend
- [ ] **Comprehensive copy-lint test over UI strings (the J-66 acceptance backstop).** Extend/consolidate the three seeded per-surface checks in `tests/test_research_api.py` into a lint that walks (a) the ENTIRE `GET /research/taxonomy` payload — every label, evidence template, caption, register line, honest-absence copy — and (b) representative SERVED copy (a live verdict + evidence projection, checklist/stance evidence, a hint card record, analytics captions, studies captions), banning imperative trade language (buy/sell/enter/exit as commands, "should", price targets, take-profit/stop-loss advice) and prediction/certainty claims ("will" forecasts, "guaranteed", "edge", profitability wording). The lexicon MUST be curated with word boundaries: factual side descriptors (aggressive **buy** ratio, "Large **sell** print absorbed", `buyer_control`, entry/**exit** action-mark labels for the user's OWN stated actions) are legitimate descriptive tape/journal language, not commands — a naive substring ban is wrong in both directions.
- [ ] **Frontend-string lint leg.** A test that scans `apps/frontend/components/` + `apps/frontend/app/` source literals with the same curated lexicon, so UI strings that never travel through taxonomy are still covered (goal.md J-66: "backed by a copy-lint test over UI strings").
- [ ] **Prove the lint can fail.** A counter-test seeds a banned phrase and asserts the lint rejects it (a lint that cannot fail proves nothing).
- [ ] **Fix the iter-24 reviewer NOTE:** replace the two hardcoded `data_feed = "sip"` study pre-stamps at `routes.py:1207/1232` with a read of the registered row-26 canonical source (the one config-aligned `data_feed_for_scenario` in `app/research/feed_basis.py` / the config-owned `historical_feed` key — whichever the one mapping exposes for the reference/historical kinds). Defaults unchanged ⇒ all existing stamps, the pinned reference study, and the full suite stay byte-identical (zero re-pins). Add a test asserting the creation-time stamp equals the one mapping's output for reference and historical study kinds.
- [ ] **`sound_cue_cooldown_seconds` config key** in `app/config.py` as a documented research default, served additively to the frontend (via the row-24 taxonomy payload alongside the sound-cue display copy). The cue is never persisted, so the key is serving-only: any `config_fingerprint` exclusion MUST ship the codified rationale comment + fingerprint-stability test + real-threshold counter-test in the SAME commit (the `study_list_max`/`hint_log_max` pattern; iter-23 lesson — never promised in prose).
- [ ] **Row-24 taxonomy additions:** sound-cue display copy (explicit toggle label, the off-by-default/transition-only description) reusing the existing "Descriptive only — not trading advice" register line; and, for any research surface the walk finds missing the register or carrying non-compliant copy, fix it AT THE TAXONOMY SOURCE (frontend hardcodes none).

### Frontend
- [ ] **Optional sound cue (J-66):** an explicit toggle in the `/` cockpit cue area (thesis strip / status area — the pre-registered cue-layer home), **default OFF** on every fresh load; when enabled, the cue fires ONLY on stance/verdict TRANSITIONS — read verbatim from the served row-15/row-25 values (the UI derives no stance of its own) — and respects the served `sound_cue_cooldown_seconds` between fires. Include a small visible fired-indicator (e.g. a brief toggle pulse) so transition-only + cooldown behavior is browser-verifiable without audio hardware. Toggle copy from taxonomy.
- [ ] **Copy fixes surfaced by the walk:** if any frontend-owned string violates the discipline, fix it (taxonomy-owned strings are fixed backend-side; genuinely frontend-local strings fixed in place and now covered by the lint leg).

### New user-facing capability
An optional, explicitly-toggled sound cue on stance/verdict transitions (off by default); product-wide assurance that no surface issues commands or predictions.

### New information displayed
The sound-cue toggle with its taxonomy-served label/description; the "Descriptive only — not trading advice" register confirmed (or restored) on every research surface.

### New user actions
One toggle: sound cue on/off (explicit, default OFF).

### UI surface changes
The `/` cockpit cue area gains the sound toggle + fired-indicator. No other surface changes except copy corrections found by the walk.

### Product surface delta
The cue layer is complete AND disciplined: every research surface audited in pixels against the no-imperative/no-prediction rules, with a permanent automated lint preventing regression; the sound cue is the final capability-33 item.

### Blueprint conformance
No new routes, no nav change. The sound toggle lives at the `/` Cockpit cue-layer home (rows 15/25 surface; J-66's registered home is "all research surfaces"). Additive build-out note added to `blueprint.md` (iter-25).

### Data-contract additions
No new contract row — the toggle state is a client-local UI preference, never a served or persisted value. Additive notes registered in `blueprint.md`: row 24 (sound-cue display copy + cooldown value served via taxonomy), row 26 (the routes.py study pre-stamp literals consolidate to the one registered mapping — closing the last hardcoded feed literal), and the Config list (`sound_cue_cooldown_seconds`, serving-only exclusion pattern). Never introduce a second computation/serving path for any registered value — the stamp fix is a consolidation TOWARD the registered owner.

## OUT OF SCOPE

- The J-68 backlog re-verification (J-11/J-14/J-16/J-18/J-20/J-22/J-23/J-27/J-28/J-29/J-32 partial, J-15 gated) — the next iteration(s).
- J-67's market-hours-gated live-IEX pixel legs — the market is closed all weekend (next open 15-06-2026 14:30 UTC+01:00); the gating stays documented, never faked.
- Any change under `app/engine/`, `app/providers/`, or to classifier behavior (J-68 byte-identity sentinel; zero re-pins required).
- Any change to verdict/stance/hint SEMANTICS — this iteration changes copy, stamps-at-creation, and adds one client-side cue; published values are untouched.
- The `qa_complete` full-pipeline harness halt (framework-side; depth stays lean while it is open).
- Sound persistence/back-end sound state, multiple sounds, volume controls — one transition cue, one toggle, nothing more.

## DEFINITION OF DONE

- [ ] Target journey J-66 passes via browser-qa-agent (all-surface copy walk + sound-cue legs in pixels)
- [ ] Required-still-passing journeys (J-01, J-08, J-38, J-53, J-59, J-60, J-61, J-63, J-65, J-67) remain green
- [ ] The copy-lint test (taxonomy walk + served-copy + frontend-scan legs) and its seeded-violation counter-test are committed and green
- [ ] `routes.py:1207/1232` literals are gone; the creation-stamp-equals-mapping test passes; full suite green (≥812 passed, exit 0) with ZERO re-pins; observer-equivalence green
- [ ] Any new serving-only fingerprint exclusion carries its rationale comment + stability test + counter-test in the same commit
- [ ] No anti-goal violation introduced
- [ ] Dev handoff written at `docs/handoffs/goal-i_will_be_super_rich_with_my_loved_ones-iter-25-dev.md`

## TESTING REQUIREMENTS

- Browser: **J-66** — (1) the all-surface walk, each surface captured with its copy legible: thesis strip across verdicts and stances (reuse the established SIM-BUYER / SIM-REVERSAL / SIM-SHIFT frames for confirming/weakening/invalidated and checklist/management stances), hint card + hint log (SIM-BUYER or SIM-BIDABS), chart geometry labels, `/journal` rows + `/journal/[id]` detail, the analytics view, `/studies`, and the register line on each research surface; (2) sound-cue legs on their EXACT preconditions (iter-20 lesson): fresh load ⇒ toggle visibly OFF and no cue ever fires; toggle ON ⇒ fired-indicator exactly at a real stance/verdict transition; no second fire within the served cooldown. Evidence discipline: scroll-into-view/full-page captures (iter-3), checksum the evidence dir (iter-22), restart the QA backend AFTER dev and verify with the `GET /research/taxonomy` canary (iter-6 — doubly relevant: taxonomy copy changes THIS iteration), and never `npm run build` against the live dev server's shared `.next` (iter-2/iter-18).
- Unit/integration: the comprehensive copy-lint (full taxonomy payload + served representative copy + frontend source scan) with the curated word-boundary lexicon; the seeded-banned-phrase counter-test; the study creation-stamp == one-mapping test for reference + historical kinds; fingerprint stability + counter pair for any new serving-only exclusion; full backend suite green; observer-equivalence green with zero re-pins.
- Error cases: the lint FAILS on a seeded imperative/prediction phrase; toggle OFF ⇒ zero cue fires across transitions; lexicon does NOT false-positive on legitimate descriptive side labels (aggressive buy ratio, sell-print absorption copy, entry/exit action-mark labels).

## NOTES

- **Lessons applied:** iter-6 (stale-server pixels — taxonomy canary before any capture; this iteration changes taxonomy copy, so a stale server would show OLD copy and falsify the walk), iter-2/iter-18 (QA build vs shared `.next`), iter-3 (below-the-fold capture discipline — the walk spans many below-fold surfaces), iter-20 (absence legs on exact preconditions — the OFF-default leg), iter-22 (md5 the evidence dir; React-controlled input automation), iter-23 (config assurance tests ship in the same commit as the exclusion claim), iter-24 (live pixels are market-hours-gated — do not attempt this weekend).
- **Lexicon curation is the hard part of the lint:** "buy"/"sell" as factual side descriptors are everywhere and legitimate (this is a tape reader); the ban targets imperative/advice constructions and forecasts. The reviewer should diff the lexicon against goal.md J-66's own list (buy / sell / enter / exit / "should" / targets, prediction/certainty claims) and check both failure directions.
- **J-67 gated legs:** the live-IEX badge/disclosure pixels and the live-declared `iex`-stamped row remain documented-gated (credentials + market hours); first opportunity is Monday 15-06-2026 after 14:30 UTC+01:00 — flag for the J-68 backlog iteration, which also needs market-hours legs (J-12/J-14/J-15).
- After J-66, only the J-68 backlog stands before GOAL_ACHIEVED consideration; the evaluator confirmed depth stays lean while the `qa_complete` harness halt remains open.
