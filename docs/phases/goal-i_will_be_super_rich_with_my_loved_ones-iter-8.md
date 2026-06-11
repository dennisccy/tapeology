# Goal Iteration 8 — Real dominance rule for directional_impact (restore J-42) + action marks: mark entry/exit (J-52)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_will_be_super_rich_with_my_loved_ones
- **Iteration:** 8
- **Mode:** normal
- **Depth:** lean
- **Frontend Present:** yes
- **Target journeys:** J-42, J-52
- **Required-still-passing journeys:** J-01, J-02, J-08, J-19, J-38, J-39, J-40, J-41, J-43, J-44, J-45, J-46, J-50
- **Anti-goal reminders:**
  - "Journal integrity. Verdict timelines are append-only: never edited, backfilled, fabricated, or recomputed at read time; nothing is recorded before declaration; gaps (pause, watch restart, stale spans) are explicit events; data-end resolves to an explicit `expired`, never a fabricated outcome; action marks are recorded exactly as the user stated them — never inferred fills. Abandoned theses remain visible in every denominator (no survivorship pruning), and an entry-marked thesis can never be abandoned." *(critical)*
  - "No execution path. Tapeology MUST NOT place, route, simulate, or recommend orders, and MUST NOT integrate any broker/brokerage or trading API. It only reads and classifies the tape." *(critical)* — Mark entry / Mark exit are **journaling record actions** over the user's own already-taken action, never a fill, never a simulated execution.
  - "No profitability or edge claims. No currency P&L, equity curves, compounding, or win-rate-as-edge presentation anywhere. R statistics are journaled measurements and MUST always appear with their n, the abandonment bucket, the null baseline (where one applies), and the spread/R cost figure." *(critical)* — the J-52 realized move renders in **R units only**, labeled a journaled measurement, with spread-at-mark beside it; never currency P&L.
  - "No naked outputs. Every published verdict, stance, hint, risk flag, execution check, and grade MUST carry plain-language evidence derived from canonical engine values. A verdict without evidence is a defect." *(critical)*
  - "No prediction language. A verdict or stance describes what the tape is doing **now** relative to the declared thesis — never a forecast of what price will do." *(critical)*
  - "The research layer is read-only over the engine. It MUST NOT mutate engine, classifier, or feature state or outputs: the same event stream yields **byte-identical** tape state/confidence/features/history with or without an active thesis or attached observers (equivalence-tested)." *(critical)*
  - "No new indicators, no auto-tuning. Confirmation rules, stances, hints, and studies MUST be composed from the EXISTING engine features and states only; research thresholds are config-owned research defaults …; no parameter optimizer, grid search, or automatic threshold fitting of any kind." *(critical)*
  - "Evidence before cues." *(critical)* — no checklist/stance/hint code in this iteration (build order binding: cues J-63–J-67 strictly last, after evidence J-58–J-62).

## GOAL

A confirming thesis no longer brands its own progress statement "violated" (a true favorable-vs-adverse dominance rule in `_evaluate_statement`), and the user can journal their actual entry and exit on the active thesis — recorded verbatim, displayed in R units, with Abandon withdrawn the moment an entry exists.

## BACKGROUND

The iter-7 evaluator (CONTINUE, lean) mandated exactly this scope. (1) The iter-6 `directional_impact` fix over-corrected: in `apps/backend/app/research/monitor.py::_evaluate_statement` (lines 89–98) the adverse-side cutoff fires FIRST with no dominance weighing, so a clean CONFIRMING SIM-BUYER tape (buy_price_impact +0.42, aggressive_buy_ratio 0.92, minority sell_price_impact −0.14 ≤ max_sell_price_impact −0.02) brands "Price keeps making progress in your direction" **violated** one line under evidence saying the tape confirms the thesis — internally contradictory UI, seen in three separate iter-7 captures; J-42 was honestly downgraded passing→partial on its "statements read met" clause. The docstring promises a dominance test the code does not implement. (2) J-52 is the top feature target: iter-7 already laid the store support (`ActionRecord`, `insert_action`, `get_actions`, `has_entry_mark` in `store.py`) and the entry-marked-refuses-abandon guard (unit-proven + live-probed); missing are the endpoint, the strip controls, verbatim recording with spread-at-mark, and the R-unit display. J-52 also closes J-50's deferred "entry-marked ⇒ no Abandon button" UI clause and unblocks J-47 (re-attach), J-48 (entry/confirmation marks), J-53, and J-54.

Lessons applied (binding, from `state/lessons.md`): four-quadrant proof in pixels for ANY verdict/statement-semantics change — never just the reported quadrant; mandatory pre-capture server-freshness canary; capture verdict states at the asserted moment (Pause) before sim teardown; scroll-into-view/full-page for below-the-fold captures; diff the executed browser test list against this spec's matrix; `NEXT_DIST_DIR=.next-qa` if any frontend build is needed (never against the live dev server's shared `.next`); any `store.py` schema change ships a **versioned migration** proven against a committed old-schema fixture plus a persistent-DB check (`CREATE TABLE IF NOT EXISTS` alone is never a migration). Depth stays **lean**: the engine halts at `qa_complete` for FULL iterations (carry-forward operator defect, still open).

## IN SCOPE

### Backend
- [ ] **Dominance rule in `_evaluate_statement` (`directional_impact`)** in `apps/backend/app/research/monitor.py`: replace the adverse-fires-first ordering with a real dominance comparison composing ONLY the existing primary-window `buy_price_impact` / `sell_price_impact` read verbatim from the snapshot. Semantics (direction-aware; long shown, short symmetric):
  - neither side clears its existing config-owned materiality cutoff (`min_buy_price_impact` / `max_sell_price_impact`) → **not_yet** (no evidence is not a failure);
  - only the favorable side is material → **met**; only the adverse side is material → **violated**;
  - BOTH material → the **dominant** side rules by impact magnitude (favorable dominant → met; adverse dominant → violated). If any tolerance/ratio beyond plain magnitude comparison is needed, it is a **config-owned research default** with a documented calibration — no inline literal (no-magic-numbers rule extends).
  - Truth anchors: SIM-BUYER long (buy +0.42 vs sell −0.14) → **met**; SIM-SELLER long (sell ≈ −0.28 dominant) → **violated**; SIM-BUYER short → **violated**; SIM-SELLER short → **met**. Update the docstring to match the implemented rule.
- [ ] **`POST /research/thesis/{id}/action`** in `apps/backend/app/research/routes.py`: body `{kind: "entry" | "exit", price}`. Records the mark **verbatim** (price exactly as submitted — never inferred, never a simulated fill), stamped at the **current logical + wall time** and with **spread-at-mark** taken once from the current snapshot at recording (a moment value; never recomputable later). Guards: 404 unknown thesis; 409 thesis already resolved; 409 duplicate entry / duplicate exit; 409 exit before entry; 422 unknown kind / non-positive or malformed price. Writes go through the existing single writer queue (`BEGIN IMMEDIATE`), never from event processing or the WS serialization path.
- [ ] **Schema/migration (only if needed):** if the existing `actions` table lacks a spread-at-mark (or logical/wall timestamp) column, bump `journal_schema_version` with an in-place `ALTER` migration in one writer transaction, proven by a test against a committed old-schema fixture (iter-4 lesson). No backfill of append-only rows.
- [ ] **Marks + realized-R in the projections (computed once):** the row-15 thesis projection (REST `…/thesis/active` ≡ WS `thesis` key verbatim) and `GET /research/journal/{id}` gain the recorded action marks and, **derived in ONE server-side function** (single module — no second computation path, no client math): `R = |entry − invalidation|`; after both marks the **realized move in R** (signed by direction); spread-at-mark per mark. With no marks, these keys are absent/null — **no realized metric is shown** (no dishonest zero).
- [ ] **Abandon withdrawal surfaced once:** the projection exposes the entry-marked fact (e.g. via the marks themselves or an explicit flag derived from `has_entry_mark`) so the UI reads it — the UI never guesses. The existing API guard (entry-marked refuses `abandoned` → 409) stays green.

### Frontend (if applicable)
- [ ] **Strip controls (`apps/frontend/components/ThesisStrip.tsx`):** on an active thesis, **Mark entry** and (once entered) **Mark exit** controls; the price field **prefilled from the current last**, editable, submitted verbatim to `POST /research/thesis/{id}/action` via one new `lib/api.ts` function. Inline verbatim error display (role=alert, consistent with the iter-7 `resolve-error` pattern); buttons disable during submit; no silent dead-clicks.
- [ ] **Entry-marked ⇒ no Abandon:** the moment the projection shows an entry mark, the **Abandon control is not rendered at all** (Played out + Mark exit remain) — closing J-50's deferred UI clause. An unmarked thesis still shows Abandon (J-50 must not regress).
- [ ] **Recorded marks + R display:** the strip shows the recorded entry/exit (price in mono + time), and after both marks the **realized move in R units** in mono, labeled as a journaled measurement with the **spread-at-mark** shown beside it. Present-tense, descriptive, thesis-attributed copy; "Descriptive only — not trading advice" stays in frame; never currency, never "profit/loss" framing.

### New user-facing capability
The user journals their actual entry and exit on the active thesis from the strip — prices recorded exactly as stated — and reads the realized move in R units afterwards; and a confirming thesis's progress statement now honestly reads MET while the tape confirms.

### New information displayed
Recorded entry/exit marks (verbatim price + time) on the strip and in the journal detail; realized move in R with spread-at-mark; corrected `directional_impact` statement statuses (met on a dominant favorable tape).

### New user actions
**Mark entry** and **Mark exit** buttons with an editable, last-prefilled price field on the active thesis strip. (Abandon is *withdrawn* once entry-marked — an action removal that is itself the J-50 deferred clause.)

### UI surface changes
Thesis strip only: mark controls, recorded-marks line, realized-R readout, conditional Abandon. No new pages, no nav changes, no chart changes.

### Product surface delta
The thesis strip completes its journaling half: declare → verdicts → marks → resolve, with the anti-survivorship guard now visible in pixels (no Abandon on a position), and the statement panel stops contradicting the verdict above it.

### Blueprint conformance
All work lives at the registered canonical home: `/` thesis strip (Cockpit) — blueprint IA row "J-38–J-46, J-49, J-50, **J-52**, J-53 … `/` thesis strip". Marks read back at `/journal/[id]` per Data Contract row 18 (page itself still future — J-55). No new pages; no nav-skeleton change; no reapproval needed.

### Data-contract additions
- **Row 18 (Action marks) — additive extension:** each mark additionally stamps **spread-at-mark** once at recording from the current snapshot (moment value, never recomputed).
- **New row 27 — Realized move in R + R basis + spread-at-mark display:** computed once by a single research projection function (R = |entry − invalidation|; realized move signed by direction; only when the marks exist); served via the row-15 thesis projection and `GET /research/journal/{id}`. The strip renders it verbatim — no client-side arithmetic. Kept distinct from row 20 (excursion outcomes, J-58 — confirmation-/entry-anchored horizon populations) and feeds row 21's acted-trade R distribution later without a second computation path.
- The `directional_impact` fix introduces **no new displayed value** — it corrects the status of an existing row-15 field using existing canonical features.

(Registered in `runs/goal-session-i_will_be_super_rich_with_my_loved_ones/state/blueprint.md` — additive edits only.)

## OUT OF SCOPE

- **Chart marks (J-48 clause of J-52):** "marks appear on the chart" defers to J-48 (no geometry layer exists yet) — same deferred-clause convention as J-45's level line. Do NOT build chart overlays this iteration.
- J-47 re-attach/survive-interruption (next after J-52), J-53 management stance, J-54 execution checks, J-55/J-56/J-57 journal page + review + grades, J-58+ excursions/analytics/studies.
- Any checklist/stance/hint code (Evidence-before-cues, binding build order).
- Engine, classifier, feature, or provider changes of any kind (research layer stays observer-only; equivalence suite must stay green).
- Any change to resolve semantics beyond hiding Abandon when entry-marked (the 409 guard already exists).

## DEFINITION OF DONE

- [ ] J-42 passes via browser-qa-agent: SIM-BUYER trend_continuation/long CONFIRMING **and** stmt2 reads MET in fresh-server pixels.
- [ ] J-52 passes (chart clause explicitly deferred to J-48): entry + exit marked from the strip, recorded verbatim, realized R + spread-at-mark displayed, no-Abandon-once-entered proven in pixels, journal-detail readback recorded.
- [ ] J-41 does NOT regress: SIM-SELLER trend_continuation/long still REJECTING with stmt2 VIOLATED in fresh-server pixels (mandatory re-capture — the dominance change touches the same code path).
- [ ] J-50 does not regress: an UNMARKED thesis still offers and executes Abandon.
- [ ] Required-still-passing journeys remain green; no anti-goal violation introduced.
- [ ] Backend suite passes (≥ current 383 passed / 1 skipped) including the new four-quadrant + guard-matrix + (if schema changed) migration tests; observer-equivalence tests green; frontend builds.
- [ ] Dev handoff written at `docs/handoffs/goal-i_will_be_super_rich_with_my_loved_ones-iter-8-dev.md`.

## TESTING REQUIREMENTS

- **BINDING precondition (applies to EVERY browser capture in this iteration):** restart the QA backend after dev completes and run the server-freshness canary before any capture — uvicorn start time MUST be newer than the newest patched file's mtime (or a content canary against a freshly patched response). A capture against a stale server is void (iter-6 lesson). Use Pause to freeze each asserted moment before sim teardown; scroll-into-view/full-page for anything below the fold; diff the executed browser test list against the matrix below before reporting.
- Browser (journey matrix):
  - **J-42:** watch SIM-BUYER, declare trend_continuation/long (invalidation far below), after dwell capture CONFIRMING with evidence citing buyer control/positive impact AND stmt2 ("Price keeps making progress in your direction rather than stalling") reading **MET**; remains confirming (no flapping).
  - **J-41 (non-regression, mandatory):** watch SIM-SELLER, declare trend_continuation/long (invalidation far below), capture REJECTING with plain-language seller evidence AND stmt2 reading **VIOLATED**; thesis stays active.
  - **J-52:** on the confirming SIM-BUYER thesis, Mark entry (verify prefill = current last; submit), capture the recorded mark and the **absence of the Abandon control**; Mark exit; capture the realized move in **R** with spread-at-mark; resolve Played out; read back `GET /research/journal/{id}` showing both marks verbatim (price + logical & wall time) — record the REST evidence in the report.
  - **J-50 (non-regression):** declare a fresh thesis WITHOUT marks and confirm Abandon is offered and works.
- Unit/integration:
  - **Four-quadrant `directional_impact` tests (mandatory):** favorable-dominant tape × {long ⇒ met, short ⇒ violated}; adverse-dominant tape × {long ⇒ violated, short ⇒ met}; plus flat/no-material-progress ⇒ not_yet, and a both-material dominance case each way. Never just the reported quadrant (lesson).
  - Action endpoint guard matrix: 404 unknown thesis; 409 resolved / duplicate entry / duplicate exit / exit-before-entry; 422 bad kind / bad price; verbatim price + logical & wall stamps + spread-at-mark persisted; entry-marked-refuses-abandon 409 stays green.
  - Realized-R single-path test: projection and journal detail return the identical computed values; absent without marks.
  - If the actions table gains a column: migration test against a committed old-schema fixture + persistent-DB restart check.
  - Observer-equivalence suite stays green (engine untouched).
- Error cases: malformed/non-positive price → 422 with explicit message surfaced inline verbatim; marking on a resolved thesis → 409; double-click submit → one mark + one 409, no duplicate record.

## NOTES

- Evaluator mandate (iter-7 eval, Next-Step 1–2) is followed verbatim: dominance fix + four-quadrant proof + both-sided pixels first, J-52 as the feature target second.
- J-52's "marks appear on the chart" clause is deliberately deferred to J-48 (the established J-45→J-48 convention); the evaluator scores J-52 on the strip/journal/verbatim/R clauses. State the deferral in the QA report so the clause is tracked, not silently dropped.
- Carry-forward operator flag (unchanged from iter-6/7): the engine halts at `qa_complete` for FULL iterations — lean remains mandatory until the harness is fixed. This iteration is lean.
- The dominance rule must not relax the iter-6 direction-awareness: an incidentally positive `buy_price_impact` on a genuinely falling tape must still read violated for a long (J-41 anchors this in pixels).
- `config_fingerprint` note: if the dominance rule adds a config value, the fingerprint changes by design (it hashes the entire frozen config) — that is correct behavior, not a defect; new records simply carry the new stamp.
