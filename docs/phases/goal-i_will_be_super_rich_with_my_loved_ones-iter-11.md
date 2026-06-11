# Goal Iteration 11 — Entry risk flags at declaration (J-49)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_will_be_super_rich_with_my_loved_ones
- **Iteration:** 11
- **Mode:** normal
- **Depth:** lean
- **Frontend Present:** yes
- **Target journeys:** J-49
- **Required-still-passing journeys:** J-01, J-02, J-08, J-38, J-39, J-42, J-47, J-48, J-50, J-52, J-68 (no-thesis sentinel frame)
- **Anti-goal reminders:**
  - "**No naked outputs.** Every published verdict, stance, hint, risk flag, execution check, and grade MUST carry plain-language evidence derived from canonical engine values. A verdict without evidence is a defect. *(critical)*"
  - "**No new indicators, no auto-tuning.** Confirmation rules, stances, hints, and studies MUST be composed from the EXISTING engine features and states only; research thresholds are config-owned research defaults calibrated against the sims/fixtures; no parameter optimizer, grid search, or automatic threshold fitting of any kind. *(critical)*"
  - "**No prediction language.** A verdict or stance describes what the tape is doing **now** relative to the declared thesis — never a forecast of what price will do. *(critical)*"
  - "**Journal integrity.** Verdict timelines are append-only: never edited, backfilled, fabricated, or recomputed at read time; nothing is recorded before declaration; gaps (pause, watch restart, stale spans) are explicit events; data-end resolves to an explicit `expired`, never a fabricated outcome; action marks are recorded exactly as the user stated them — never inferred fills. Abandoned theses remain visible in every denominator (no survivorship pruning), and an entry-marked thesis can never be abandoned. *(critical)*"
  - "**The research layer is read-only over the engine.** It MUST NOT mutate engine, classifier, or feature state or outputs: the same event stream yields **byte-identical** tape state/confidence/features/history with or without an active thesis or attached observers (equivalence-tested). An observer failure MUST surface explicitly and never kill the feed. *(critical)*"
  - "**No unsolicited or unconditional trade commands.** Every actionable cue MUST be gated on a user-declared thesis with an invalidation, rendered as named checks with margins and evidence, in present-tense descriptive language. No imperative buy/sell/enter/exit wording, no price targets, no certainty language — anywhere. A hint is a logged description of a forming pattern, never a command and never a thesis by itself. *(critical)*"
  - "**No trade/profit claims.** The product MUST NOT claim profitability or present output as trading advice; tape state is descriptive, not prescriptive."

## GOAL

When the user declares a thesis, the system computes entry risk flags ONCE from the live engine snapshot, freezes them on the thesis, and shows them as advisory amber chips on the thesis strip — each with its measured margin in plain language; creation always succeeds (advisory, never blocking).

## BACKGROUND

This is the iter-10 evaluator's primary recommendation (capability 26, J-49 — currently `failing`, never built by design: the projection deliberately omits `risk_flags` entirely, per the note at `apps/backend/app/research/monitor.py:21`). Everything it needs exists: the declaration route already freezes `entry_context`; the classifier owns the reusable stability gates (`warmup_min_events`, `max_stable_spread_bps` relative-spread gate, `min_trade_speed`); the single `build_projection` (row 15) and `GET /research/journal/{id}` are the registered read paths; taxonomy.py (row 24) owns research display copy. Depth is lean per the evaluator's explicit recommendation (and the upstream FULL-pipeline harness defect — engine halts at `qa_complete` — remains open). The blueprint Data Contract has been updated alongside this spec: row 15 gains an iter-11 additive note registering the `risk_flags` projection key (mirroring how `geometry` was registered in iter-10); row 17 already names the single owner (computed once at declaration by the research monitor; frozen on the thesis).

## IN SCOPE

### Backend

- [ ] **One flag-computation function, called once at declaration.** A single function in the research layer (e.g. in `monitor.py`) computes the full capability-26 flag set from the declaration-time engine snapshot + config, invoked exactly once inside `POST /research/thesis` (the same place `entry_context` is frozen). Never recomputed at read; never a second computation path. The six flags:
  - `before_warmup` — declaration-window trade count below the classifier's own `warmup_min_events` (reused, not duplicated).
  - `invalidation_too_tight` — |last − invalidation| < (new config research default: spread-multiple) × current spread.
  - `chasing_entry` — the recent directional impact return on the thesis's side (existing engine impact-as-return feature, direction-aware) already exceeds a new config research-default return threshold.
  - `wide_spread_illiquid` / `low_trade_speed` — reuse the classifier's EXISTING relative-spread (`max_stable_spread_bps`) and `min_trade_speed` stability gates verbatim — **no new thresholds for these two** (capability 26's explicit constraint).
  - `against_expected_tape` — setup-aware: the snapshot tape state at declaration vs the setup's expected tape (a long absorption_reversal declared during `bid_absorption` is NOT flagged; declared during `seller_control` it IS — per capability 26).
- [ ] **Flags are frozen with their measured evidence.** Each fired flag is stored as a structured entry carrying the flag name plus the measured values behind it (e.g. measured impact return vs threshold, invalidation distance vs spread-multiple band, spread bps / trade speed at declaration) so the journal/review can later show them verbatim with zero recompute. Plain-language chip copy and evidence templates live in `taxonomy.py` (row 24) — the frontend hardcodes none of them.
- [ ] **Advisory, never blocking.** Creation always succeeds with flags attached. The existing J-39 validation contract is untouched: incoherent input (wrong-side invalidation, missing/forbidden level, unknown enums) stays a **422, never a flag**.
- [ ] **Persistence: versioned migration v3 → v4.** The `theses` table gains a `risk_flags` column; bump `journal_schema_version` to 4 with an in-place `ALTER` migration step in `store._migrate`, proven by a test against a committed old-schema fixture. Pre-migration rows keep `NULL` — **never backfilled**; a NULL-flags thesis omits the `risk_flags` key from its projection (no dishonest empty list for a thesis that was never assessed).
- [ ] **Serving: additive `risk_flags` key on the row-15 projection.** Added inside the single `build_projection` (re-exposing the frozen stored value verbatim) so the live monitor, the surviving/not-evaluated path, REST `GET /research/thesis/active`, and the WS `thesis` key all carry identical flags. Extend the existing REST==WS parity test to cover `risk_flags` (as iter-10 did for `geometry`). `GET /research/journal/{id}` also carries the frozen flags (row 17: "→ row 15 / journal").
- [ ] **Config research defaults.** The two NEW thresholds (chase return threshold; invalidation-too-tight spread multiple) live in `config.py` as documented research defaults with their sim calibration noted — no literal in research code. They enter `config_fingerprint` automatically (by design — do NOT add them to the exclusion set).

### Frontend

- [ ] **Risk-flag chips on the thesis strip** (`ThesisStrip.tsx`): when the active-thesis projection carries non-empty `risk_flags`, render amber advisory chips (amber-400/500 per the design system — absorption/unclear semantics), each showing the taxonomy-owned label and its plain-language measured margin verbatim. No flags fired ⇒ no chips (and no "all clear" badge — no naked reassurance). The strip derives nothing; it renders the served strings/values verbatim, numerics in mono.
- [ ] Chips appear on declaration response and persist for the thesis lifetime (frozen — they never change as the tape moves), including on the surviving/not-evaluated strip.

### New user-facing capability
Declaring a thesis now produces an honest, frozen entry-risk assessment: the user immediately sees whether they declared before warm-up, with too-tight an invalidation, chasing an extended move, into an illiquid tape, or against the expected tape — with the measured margin for each.

### New information displayed
Amber risk-flag chips on the active-thesis strip, each with plain-language evidence (e.g. the measured impact return vs the config threshold; the invalidation distance vs the spread-multiple band).

### New user actions
None — flags are advisory and read-only. No new buttons or forms.

### UI surface changes
The existing thesis strip on `/` gains a risk-flag chip row when flags fired at declaration. No new pages, no nav change, no new panels.

### Product surface delta
The declare flow grows from "validated + accepted" to "validated + accepted + risk-assessed", completing the risk leg of the risk-and-lifecycle-honesty group (J-49–J-51) and feeding the future review surface (J-55) and `ignored_risk_flags` mistake tag (J-54/J-57) with frozen, evidence-backed records.

### Blueprint conformance
No new surfaces. J-49's registered canonical home is the `/` thesis strip (Cockpit section) — exactly where the chips render. No IA edit, no reapproval request.

### Data-contract additions
No new row. Row 17 (Entry risk flags — computed once at declaration by the research monitor; frozen on the thesis; served via `POST /research/thesis` response → row-15 projection / journal; advisory, never blocking; incoherent input = 422, never a flag) already names the single owner and endpoint. Row 15 gains an **iter-11 additive note** (registered in `blueprint.md` alongside this spec) for the additive `risk_flags` key: frozen at declaration, re-exposed verbatim by the single `build_projection`, served by `GET /research/thesis/active` + the WS `thesis` key + `GET /research/journal/{id}`, rendered verbatim by the strip; display copy from row-24 taxonomy. Never a second computation or serving path.

## OUT OF SCOPE

- The `/journal` page, journal list endpoint, or any review surface (J-51/J-55–J-57 — later iterations).
- Execution checks, mistake tags, and the `ignored_risk_flags` tag flow (J-54/J-57) — flags only feed them later.
- Management stance / entry checklist / hints (J-53, J-63–J-65 — cue layer, gated LAST behind J-58–J-62 per the binding build order).
- Any change to engine, classifier, providers, or verdict-transition rules. The classifier gates are READ for flag computation — never modified, never duplicated as second thresholds.
- Re-evaluating or mutating flags after declaration (they are frozen — a flag is a record of the entry moment, not a live indicator).
- Blocking or warning-gating thesis creation on flags (advisory only).
- Backfilling `risk_flags` onto pre-migration theses.

## DEFINITION OF DONE

- [ ] J-49 passes via browser-qa-agent: all four browser legs below verified in pixels.
- [ ] Required-still-passing journeys remain green (J-01, J-02, J-08, J-38, J-39, J-42, J-47, J-48, J-50, J-52, J-68 sentinel frame).
- [ ] No anti-goal violation introduced (notably: every flag carries plain-language evidence; descriptive present-tense copy only; research layer still read-only over the engine — observer-equivalence suite green).
- [ ] Unit tests pass; full backend suite green; no regressions.
- [ ] Versioned v3→v4 migration proven against a committed old-schema fixture; pre-migration rows never backfilled.
- [ ] REST==WS parity test extended to `risk_flags` and green.
- [ ] Blueprint row-15 additive note registered (done alongside this spec).
- [ ] Dev handoff written at `docs/handoffs/goal-i_will_be_super_rich_with_my_loved_ones-iter-11-dev.md`.

## TESTING REQUIREMENTS

- **Browser (J-49, per goal.md steps — all four legs, screenshots opened by the evaluator):**
  1. **`chasing_entry`:** Watch SIM-BUYER well past warm-up (an extended move); declare trend_continuation / long → amber `chasing_entry` chip with its measured margin in plain language.
  2. **`invalidation_too_tight`:** On a fresh watch, declare with an invalidation extremely close to the last (correct side) → amber `invalidation_too_tight` chip (distance < the config spread-multiple); creation succeeded.
  3. **Liquidity flags:** Watch SIM-CHOP; declare any thesis → `wide_spread_illiquid` and/or `low_trade_speed` chips (reusing the classifier's own stability gates).
  4. **`before_warmup`:** Declare immediately after Watch (before warm-up completes) → amber `before_warmup` chip.
  - Also capture one no-flags declaration frame (clean SIM-BUYER declare inside normal conditions where applicable) showing NO chips and the strip otherwise unchanged, plus the J-68 no-thesis sentinel frame.
  - Required-still-passing spot checks per the journey matrix; diff the executed browser test list against this spec's matrix before closing QA.
- **Unit/integration:**
  - One test per flag asserting it fires with the exact expected measured-evidence values, and at least one negative case per flag (just-inside-threshold ⇒ no flag).
  - `against_expected_tape` setup-aware matrix: long absorption_reversal during `bid_absorption` ⇒ NOT flagged; during `seller_control` ⇒ flagged (browser leg not required — unit-pinned).
  - Flags are frozen: projection re-reads return byte-identical flags as the tape moves on; the surviving/not-evaluated projection (same `build_projection`) carries the same frozen flags.
  - Advisory-never-blocking: a maximally-flagged declaration still returns 201/200-created; wrong-side invalidation still 422 with NO flags computed/persisted (J-39 unchanged).
  - Migration: open a committed v3-schema fixture DB ⇒ migrated to v4 in one writer transaction; old thesis rows keep NULL flags; their projection omits the `risk_flags` key.
  - REST==WS parity including `risk_flags`; observer-equivalence suite still green (read-only research layer).
- **Error cases:** incoherent input (wrong-side invalidation, missing/forbidden level, unknown setup/direction enums) remains a 422, never a flag; unknown ticker / not-watched declaration paths unchanged (404).

## NOTES

**Binding lessons applied (state/lessons.md):**
- **store.py schema change ⇒ versioned migration + committed old-schema fixture test** (`CREATE TABLE IF NOT EXISTS` alone is never a migration). This iteration bumps v3→v4 — follow the v1→v2→v3 pattern exactly (one `BEGIN IMMEDIATE` writer transaction, never backfilling).
- **Server-freshness canary is mandatory pre-capture:** restart the QA backend after dev changes; verify server start time > newest patched-file mtime (or a content canary — e.g. `risk_flags` present on a fresh declaration via REST) before any screenshot.
- **Scroll-into-view / full-page every below-the-fold capture** — the evaluator opens the PNGs; the strip chips must be fully in frame.
- **Diff the executed browser test list against this spec's journey matrix** before closing QA.
- **Never `npm run build` against the live dev server's shared `.next`** — use `NEXT_DIST_DIR=.next-qa` for any QA-side build.
- **New served value ⇒ blueprint registration with one owner** — done: row-15 additive note + pre-existing row 17.

**Other notes:**
- The two new config fields MUST enter `config_fingerprint` (research thresholds — by design every record stamps them); do not add them to the fingerprint exclusion set. Existing fingerprint tests asserting "any config value change ⇒ new hash" should cover them automatically.
- Honest-omission semantics carry forward: `risk_flags` ABSENT means "never assessed" (pre-migration thesis); an EMPTY list means "assessed at declaration, nothing fired". Do not collapse the two.
- Chip copy discipline (J-66 groundwork): present-tense, descriptive, measured — e.g. "recent buy impact +0.44% exceeds the 0.20% chase threshold" — never imperative, never predictive; "Descriptive only — not trading advice" footer stays on the strip.
- FULL-pipeline harness defect (engine halts at `qa_complete`) remains open upstream — depth is lean per evaluator recommendation; lean iterations 6–10 produced complete evaluator-verifiable evidence.
