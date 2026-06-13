# Goal Iteration 24 — J-67: the feed basis is always labeled (cockpit feed badge + stamp display, one config-owned mapping)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_will_be_super_rich_with_my_loved_ones
- **Iteration:** 24
- **Mode:** normal
- **Depth:** lean
- **Frontend Present:** yes
- **Target journeys:** J-67
- **Required-still-passing journeys:** J-01, J-08, J-59, J-63, J-65, J-68
- **Anti-goal reminders:**
  - "**Source, feed, and config honesty.** Every research record MUST be stamped with its bound source, its `data_feed`, and a `config_fingerprint` over the entire frozen config; a thesis MUST never be evaluated against a different source than it was declared on; analytics and studies MUST NOT pool across feeds or fingerprints; and SIP-derived research MUST NOT be presented as validating IEX-live behaviour without the explicit basis label. *(critical)*"
  - "**The research layer is read-only over the engine.** It MUST NOT mutate engine, classifier, or feature state or outputs: the same event stream yields **byte-identical** tape state/confidence/features/history with or without an active thesis or attached observers (equivalence-tested). An observer failure MUST surface explicitly and never kill the feed. *(critical)*"
  - "**Single source of truth.** Tape state, confidence, and each feature MUST be computed exactly once in the engine and read identically by REST, WebSocket, and the UI; the API and frontend MUST NOT recompute them. The same ticker MUST NOT show different values across views. *(critical)*"
  - "**No magic numbers.** Every window length, threshold, large-print size, impact/absorption cutoff, and confidence boundary MUST come from config — no such literal in engine/classifier code."

## GOAL

The cockpit always labels the feed basis of the current watch (sim | iex | sip) with the honest IEX-vs-SIP disclosure on live, and every research row visibly carries its stored `data_feed` stamp — completing J-67, the last cue-layer copy surface before the J-66 sweep audits it.

## BACKGROUND

The iter-23 evaluator (CONTINUE, lean recommended — the full-pipeline `qa_complete` harness halt is still open) named J-67 the natural iter-24 target: records already store and mostly display `data_feed`, so the gap is the cockpit badge plus small display gaps. Codebase verification confirms: the cockpit and the summary/WS snapshot carry **no** feed-basis value today; the scenario→`data_feed` mapping exists in TWO copies (`app/research/monitor.py:76` canonical, `app/research/hints.py:58` local copy) and both **hardcode** "iex"/"sip" instead of reading the config-owned `live_feed`/`historical_feed` keys — which would break J-67's "upgrading live to SIP remains a single config value (no relabeling code)" clause the moment an operator flipped the config; and `HintLog.tsx` does not display the stored stamp. Carry-along per the evaluator and the iter-23 reviewer NOTE: the `hint_log_max` config comment claims a fingerprint-stability test pair that does not exist — add it (lesson iter-23: **comments claiming test coverage must be cross-checked against the suite** — this iteration makes that comment true rather than deleting it).

## IN SCOPE

### Backend

- [ ] **Consolidate the scenario→`data_feed` mapping to ONE shared function** (blueprint row 26, iter-24 note): fold the `app/research/hints.py` local copy into a single owner (developer chooses a placement that avoids the monitor↔hints import cycle — e.g. a small leaf module both import); `monitor.py`, `hints.py`, `studies.py`, and `routes.py` all read the one function. No behavior change.
- [ ] **Make the one mapping config-aligned:** `live …` → `config.live_feed`, `historical …` → `config.historical_feed`, everything else → `"sim"` — replacing the hardcoded `"iex"`/`"sip"` literals. Defaults are unchanged (`live_feed="iex"`, `historical_feed="sip"`) so every existing stamp, pinned test, and persisted record is byte-identical; a SIP-entitled operator upgrading live becomes ONE config value with zero relabeling code (J-67's final acceptance clause, now provable). Both keys are already IN `config_fingerprint` (not in the exclusion set) — no fingerprint change.
- [ ] **Serve the current-watch feed basis** (new blueprint row 29): an additive `data_feed` metadata field on the row-6 snapshot projection — `GET /tape/{ticker}/summary`, re-exposed by WS verbatim — computed once server-side by the one mapping from the snapshot's scenario descriptor. Follow the iter-9 `end_reason` / iter-21 `delivery_lag_seconds` precedent exactly: projection/display metadata only, never read by classification, observer signature unchanged, equivalence suite green with **zero re-pins**.
- [ ] **Taxonomy (row 24, additive):** feed-basis display copy via the existing `GET /research/taxonomy` — per-feed badge labels (sim | iex | sip) and the live disclosure line, verbatim from goal.md: "live verdicts read the single-venue IEX feed; historical replay and studies use SIP — spreads and prints differ". The frontend hardcodes none of it.
- [ ] **Carry-along test pair:** `hint_log_max` fingerprint-stability test + real-threshold counter-test, matching the `test_study_list_page_size_is_serving_only_excluded_from_fingerprint` / `test_a_real_threshold_still_changes_fingerprint` precedent in `tests/test_studies.py` — the assurance pair the `config.py` comment already claims.

### Frontend (if applicable)

- [ ] **Cockpit feed-basis badge** in the `/` status area (beside the watched-source indicator / lag readout): renders the served row-29 value verbatim with row-24 labels; when the served basis is the live IEX feed, the disclosure line renders with it. Honest absence when no watch — never a fabricated basis.
- [ ] **Hint-log feed stamp** (row 22, additive): the `/journal` hints view displays each stored row's `data_feed` stamp (persisted value verbatim, labels from taxonomy) — closing the one confirmed display gap.
- [ ] **Display-gap sweep for stored stamps:** verify thesis rows (`JournalTable`), journal detail incl. action marks (`JournalDetailView`), analytics partitions (`AnalyticsView`), and study rows/results (`StudyList`/`StudyResultsView`) each display the stored `data_feed` — greps show these already reference it; fill any residual gap additively, change nothing that already displays it.

### New user-facing capability

The user can always see which market-data basis the current watch reads — and on live, an explicit one-line disclosure that live verdicts read the single-venue IEX feed while SIP-derived research (historical replay, studies) differs in spreads and prints.

### New information displayed

- A feed-basis badge (sim | iex | sip) in the cockpit status area, in all modes.
- The IEX-vs-SIP disclosure line on the live cockpit.
- A `data_feed` stamp on each hint-log row.

### New user actions

None — this iteration is display + honesty labeling only. No new buttons, forms, or controls.

### UI surface changes

- `/` cockpit status area: + feed-basis badge (+ disclosure line on live).
- `/journal` hints view: + feed stamp per row.
- No new pages, routes, or nav changes.

### Product surface delta

The cue layer's copy surface is complete: every research record's feed stamp is now visible everywhere records are shown, and the live cockpit discloses its IEX basis wherever SIP-derived research sits nearby — the J-66 discipline sweep can now audit a finished surface.

### Blueprint conformance

No new routes. Both surfaces land at pre-registered homes: the feed badge at the `/` cockpit status area (feature-homes row "J-66 …, J-67 (feed labels) — live feed badge + stamps") and the hint-log stamp under the existing `/journal` Journal home. Iter-24 build-out note added to `blueprint.md` (additive — no skeleton change, no reapproval needed).

### Data-contract additions

- **Row 29 (NEW, registered in `blueprint.md`):** Current-watch feed basis (sim | iex | sip) — computed by the ONE consolidated scenario→`data_feed` mapping (row 26's function; config-aligned to `live_feed`/`historical_feed`), served ONLY as an additive metadata field on the row-6 snapshot projection (`GET /tape/{t}/summary` + WS verbatim); the badge renders it verbatim; never client-derived.
- **Row 24 (additive):** feed-basis badge labels + the live disclosure line via the existing taxonomy endpoint.
- **Row 22 (additive):** the hint-log view displays the already-persisted row-26 stamp — read, never recomputed.
- **Row 26 (additive note):** the stamp mapping consolidates to one owner and reads the config-owned per-mode feed keys.
- No value already in the contract gains a second computation or serving path; the `hints.py` duplicate mapping is REMOVED, not paralleled.

## OUT OF SCOPE

- J-66 (cue-discipline sweep, copy-lint test over UI strings, the optional sound cue) — deliberately next, so it audits the COMPLETE cue surface including this badge.
- The J-68 backlog re-verification (J-11/J-14/J-16/J-18/J-20/J-22/J-23/J-27/J-28/J-29/J-32 partial, J-15 gated) — its own later effort.
- Any engine, classifier, or provider change. The vendor adapter's `_data_feed` name→enum mapping (`alpaca.py`) is untouched — the vendor enum stays inside the one adapter.
- Actually upgrading live to SIP — the config flip remains the operator's choice; this iteration only proves it relabels with no code change.
- Any change to analytics pooling/partitioning — already enforced and passing (J-59); re-verify only.
- Backfilling or restamping any existing persisted record — stamps are assigned once at creation and stay as stored.

## DEFINITION OF DONE

- [ ] Target journey J-67 passes via browser-qa-agent (badge + stamps + partitioning legs; the live-declared-row leg per its credential gating below)
- [ ] Required-still-passing journeys J-01, J-08, J-59, J-63, J-65, J-68 (byte-identity clause) remain green
- [ ] Observer-equivalence suite green with ZERO re-pins; no file under `app/engine/` or `app/providers/` in the diff (adapter untouched)
- [ ] Exactly ONE scenario→`data_feed` mapping function remains in the codebase, reading `config.live_feed`/`config.historical_feed`
- [ ] The `hint_log_max` fingerprint stability + counter test pair exists and passes (the config comment's claim is now true)
- [ ] No anti-goal violation introduced
- [ ] Unit tests pass; no regressions (full backend suite exit 0)
- [ ] Dev handoff written at `docs/handoffs/goal-i_will_be_super_rich_with_my_loved_ones-iter-24-dev.md`

## TESTING REQUIREMENTS

- Browser: **J-67** —
  1. Watch a sim ticker: the cockpit badge reads the sim basis (and the hint-log rows in `/journal` show their stored feed stamp).
  2. Live mode: the badge + the exact disclosure line render (browser-verifiable without a feed per goal.md; if credentials + market hours permit, additionally declare a live thesis and confirm the stored `iex` stamp on its journal row — else document this as the journey's credential-gated leg, never fake it).
  3. Historical: badge reads the SIP basis — browser-side if the harness date entry permits, else REST-verify `GET /tape/{t}/summary` on a credentialed historical watch and document.
  4. Analytics view: partitions remain segregated by feed + fingerprint (no pooled rollup) — re-verify in pixels.
  - Required-still-passing: J-01 cockpit panels, J-08 REST==UI spot-check (now including the new summary field == WS verbatim), J-63 checklist coexists in the same status area, J-65 hint dock/log unregressed by the new column.
- Unit/integration:
  - The one mapping: `live X` → `config.live_feed`, `historical X …` → `config.historical_feed`, sim scenarios → `sim`; flipping `live_feed="sip"` in an injected config relabels NEW stamps and the served basis with no code change (the J-67 single-config-value clause); defaults unchanged ⇒ existing stamp tests pass unmodified.
  - Summary projection: the additive `data_feed` field equals the WS frame's value verbatim (the row-15/row-22 REST==WS test precedent); present for sim/live/historical watches.
  - Observer equivalence: suite green, equivalence file unchanged (zero re-pins).
  - `hint_log_max`: stability test (changing it does NOT move `config_fingerprint`) + counter-test (a real threshold DOES) — the `test_studies.py` precedent pair.
  - Taxonomy: feed-basis copy block served; disclosure string matches goal.md verbatim.
- Error cases:
  - `GET /tape/{ticker}/summary` for a not-watched ticker stays 404 — no fabricated feed basis.
  - No watch ⇒ no badge (honest absence, never a default "live"/"iex" guess).
  - Unknown/unmapped scenario descriptor falls through to `sim` only for genuine sim scenarios — `live `/`historical ` prefixes always resolve via config, never a silent literal.

## NOTES

- **RESUME CONTEXT (read first — updated on second resume):** the session paused mid-iter-24 again (AWAITING_PUMP) and is resuming; this spec is re-confirmed sound and current against the state (J-67 still `failing` in journey-history; iter-23 eval CONTINUE + COHERENCE-PASS recommends exactly this scope; blueprint rows 22/24/26/29 + the iter-24 build-out note already registered additively, no reapproval pending). **The implementation is now COMPLETE in the working tree, uncommitted** (WIP snapshot re-stamped `3425b8c` over iter-23 HEAD `dc7ba29`; the first abort's stash was `6ea9018`): NEW `apps/backend/app/research/feed_basis.py` (the consolidated config-aligned mapping), `apps/backend/tests/test_feed_basis.py`, `apps/frontend/components/FeedBasisBadge.tsx`, plus the modifications enumerated in the dev handoff. The developer ALREADY verified it end-to-end and wrote `docs/handoffs/goal-i_will_be_super_rich_with_my_loved_ones-iter-24-dev.md` + `…-iter-24-frontend.md` (full suite **812 passed / 1 skipped, exit 0**; `tsc --noEmit` exit 0; live ASGI smoke: taxonomy `feed_basis` canary, sim summary `data_feed`, 404 honest absence, REST==WS verbatim; AST test proves exactly ONE mapping definition). On re-dispatch the developer MUST verify-and-complete against this spec — **not restart, not `git checkout`/discard the unstaged files** (memorialized harness caution), **not trust untested**: if the tree still matches the dev handoff, a fresh full-suite re-run + handoff confirmation is the entire dev step. **Downstream is NOT done:** reviewer, QA, and browser-qa have not run — `reports/qa/goal-i_will_be_super_rich_with_my_loved_ones-iter-24-evidence/` exists and is EMPTY (zero pixels), and J-67 cannot flip without browser evidence (iter-2/3 lesson). Nothing in the tree is pre-approved; the remaining pipeline evaluates the finished diff as usual. QA note: the dev handoff documents a `TAPEOLOGY_JOURNAL_DB=":memory:"` per-connection SQLite isolation artifact on the WS path — use a file-based temp DB for probes; it is not a code defect.
- **Lesson applied (iter-23):** "comments claiming test coverage must be cross-checked against the suite" — the `hint_log_max` comment's claimed assurance pair is the carry-along here; reviewer should confirm the pair actually exists in the suite this time, not just the comment.
- **Why consolidate the mapping now:** iter-23's coherence audit tolerated the `hints.py` local copy as a display-stamp mapping; this iteration makes the mapping config-sensitive, and editing two copies in lockstep is exactly the drift the coherence-auditor exists to prevent. One function, multiple registered consumers — the row-27 `r_basis` pattern.
- **Byte-identity caution:** the new summary field must follow the `end_reason`/`delivery_lag_seconds` precedent precisely — projection metadata, not classifier input. Any equivalence re-pin is a spec violation here, not a judgment call.
- **Browser-QA cautions carried forward:** restart/canary the backend AFTER dev completes (iter-6 lesson: server start time > newest patched-file mtime — the taxonomy `feed_basis` block is this iteration's code-identity canary); md5-checksum the evidence dir and never cite byte-identical idle frames (iter-22); capture absence legs on their exact preconditions (iter-20); no `npm run build` against the live dev server's shared `.next` (iter-18).
- **Depth stays lean:** the full-pipeline `qa_complete` harness halt remains open (iter-23 eval, open item 3); restore full depth the moment it is fixed.
- After this iteration: J-66 (sweep + copy-lint + sound cue OFF-by-default) next, then the J-68 "J-01–J-37 all green" backlog — the last items before GOAL_ACHIEVED consideration.
