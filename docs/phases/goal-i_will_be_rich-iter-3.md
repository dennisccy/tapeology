# Goal Iteration 3 — Fix the dynamic-Tailwind color layer; take J-01/J-02 green

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_will_be_rich
- **Iteration:** 3
- **Mode:** next
- **Depth:** lean
- **Frontend Present:** yes
- **Target journeys:** J-01, J-02
- **Required-still-passing journeys:** J-08
- **Anti-goal reminders:**
  - **Single source of truth.** Tape state, confidence, and each feature MUST be computed exactly once in the engine and read identically by REST, WebSocket, and the UI; the API and frontend MUST NOT recompute them. The same ticker MUST NOT show different values across views. *(critical)*
  - **No fabricated data.** On a provider gap/failure the system MUST surface an explicit stale/no-data state and MUST NOT synthesize trades, quotes, prices, or a tape state to force a green journey. *(critical)*
  - **Price impact over raw aggression.** The classifier MUST distinguish absorption from control; high one-sided aggression with no price progress MUST resolve to the matching absorption state, never to control. Keying on aggression ratios alone is a defect. *(critical)*

## GOAL

Make the cockpit's load-bearing color semantics (green = buyer/positive, red = seller/negative, amber = absorption/unclear) actually render in the served bundle, so the `SIM-BUYER` buyer-control read is green at a glance — promoting J-01 and J-02 from `partial` to `passing` while J-08 stays green.

## BACKGROUND

iter-2 fully browser-proved every **data/behavior** assertion for J-01/J-02 (buyer_control @ 0.888, positive buy_price_impact +0.390, spread = ask − bid, live WS updates without reload) and took J-08 to the first fully-green journey. Both were blocked from green by exactly one real, root-caused UI defect: the cockpit's color layer renders colorless. The evaluator's explicit next step is "fix the color layer first, re-verify the three targets, **do NOT advance to J-03 yet**," at **lean** depth. This iteration does exactly that and nothing else.

**Confirmed root cause (verified this planning pass).** `apps/frontend/tailwind.config.ts` has `content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"]` — **`./lib` is not scanned**, so the color classes that exist *only* as literal return strings in `apps/frontend/lib/format.ts` (`stateColor`, `stateBarColor`, `sideColor`, `impactColor`) are never emitted by Tailwind's content scanner. Compounding it, several of these classes appear elsewhere only in *variant* or *bg-vs-text* forms (e.g. `hover:bg-emerald-500` in `TopBar.tsx:49`, `bg-emerald-400` dot at `:9`), which generate different selectors and do **not** produce the needed base utilities — so the base utilities `.text-emerald-400` and `.bg-amber-500` are genuinely missing. Measured in iter-2: the "Buyer Control" headline and positive impact compute slate `rgb(226,232,240)` and the confidence-bar fill is transparent.

**Lessons applied (mandatory reading for the developer/QA):**
- **iter-2 lesson — dynamic Tailwind classes are silently dropped; verify color by measurement, not by eye.** Any Tailwind class produced only by runtime string-building (never a static `className` in a scanned file) is absent from the build. A "looks green" screenshot glance gave a false PASS in iter-2; the computed-style/stylesheet probe gave the correct FAIL. **Color assertions in this iteration MUST use `getComputedStyle` + a stylesheet-rule probe, not a visual glance.** The first state verified (buyer→emerald) does NOT prove the others: `bg-rose-500` (J-03 bar), `text-amber-400`/`bg-amber-500` (J-04/J-05/J-06 absorption/unclear) share the identical dynamic-only pattern and stay latent-broken until present in the bundle.
- **iter-1 lesson — an all-SKIPPED browser run is not verification.** Backend-PASS + clean build is NOT evidence the UI journeys work. Precondition before driving the browser on this Next.js app: `rm -rf apps/frontend/.next` and restart the managed dev server with `NEXT_PUBLIC_API_URL` set, so the run is a real HTTP 200, not a 500-trap SKIP.

## IN SCOPE

### Backend
- [ ] None. No engine/classifier/API/config change this iteration.

### Frontend
- [ ] Make **every** color class returned dynamically by `apps/frontend/lib/format.ts` present as a **base utility** in the actually-served Tailwind bundle (dev server *and* `npm run build`). The complete set is the 8 classes the file can return:
  - `text-emerald-400`, `text-rose-400`, `text-amber-400`, `text-slate-400`, `text-slate-300`
  - `bg-emerald-500`, `bg-rose-500`, `bg-amber-500`
- [ ] Preferred root-cause fix: **add `./lib/**/*.{ts,tsx}` to the `content` globs** in `tailwind.config.ts` (the literal strings already live in `format.ts`, so scanning the file emits all 8). An explicit `safelist` array listing the 8 classes is an equally acceptable mechanism — pick one; the requirement is the *outcome* (all 8 base utilities present), self-documenting, and robust to the colors not happening to appear statically elsewhere. Do not rely on incidental static usage in other components.

### New user-facing capability
None new. This restores the **already-specified** at-a-glance color language of the existing cockpit: the buyer-control read finally shows as green (headline state, confidence-bar fill, BUY trade rows, positive buy_price_impact) instead of colorless.

### New information displayed
None. No new values, panels, or metrics. Color is presentation of existing engine-computed values only.

### New user actions
None.

### UI surface changes
No new pages, panels, routes, or controls. Single `/` cockpit unchanged in structure; only the color rendering of existing elements is corrected.

### Product surface delta
The cockpit becomes legible at a glance per the goal's Design Direction ("green = buy-side / positive impact … color encodes side and impact consistently everywhere") instead of rendering side/impact in slate. No behavior, data, or navigation change.

### Blueprint conformance
No new surfaces — the single `/` cockpit (the only Information-Architecture home) is unchanged. The color semantics this iteration fixes are **already documented** in `blueprint.md` (IA shell: "green = buy-side / positive impact, red = sell-side / negative impact, amber = absorption / unclear"; tape-state panel "color encodes side/impact"). This iteration brings the implementation into conformance with the existing, approved blueprint — `blueprint.md` is unchanged and **no re-approval is requested**.

### Data-contract additions
None. No new displayed value; no new computing module; no new endpoint. The single-source-of-truth contract is untouched (a colorless number and a green number are the same number — see J-08).

## OUT OF SCOPE

- **No backend changes** — no edits to the engine, classifier, feature engine, `config.py`, or any API/route. Do NOT relax the buyer_control positive-`buy_price_impact` guard.
- **J-03 (SIM-SELLER / seller_control) is NOT started this iteration.** Per the iter-1/iter-2 discipline (and the evaluator's explicit recommendation), close verification of the current targets before opening a new scenario. J-03 is the next iteration's work.
- **No new panels, routes, controls, or values.**
- **Stream-status-dot consolidation is DEFERRED** (drive the top-bar dot from the engine's canonical `snapshot.stream_status` instead of the client `connStatus`). It is a *data-sourcing* concern, not a color concern, and exercising `stale`/`closed` belongs to the J-04/J-05 (no-data) or J-09 (teardown) iteration. **Not forgotten** — it MUST be consolidated before those journeys land; it is simply not part of this color-only pass.
- **No refactor of `format.ts`** beyond what the fix requires; the dynamic color-helper functions stay as-is (the fix is to make their output reachable by the build, not to rewrite them).

## DEFINITION OF DONE

- [ ] **J-01 passes via browser-qa-agent** on `SIM-BUYER`: all six panels render live values (unchanged from iter-2) **and** the cockpit's color layer is green — verified by `getComputedStyle`, not by eye.
- [ ] **J-02 passes via browser-qa-agent** on `SIM-BUYER`: the "Buyer Control" headline state label, the confidence-bar fill, BUY trade-side cells, and the positive `buy_price_impact` value all compute an **emerald** color (NOT slate `rgb(226,232,240)`); state still settles on buyer_control @ confidence ≥ threshold with positive buy_price_impact (guard intact, not relaxed).
- [ ] **All 8 dynamic color classes resolve to a real rule in the served stylesheet** — confirmed by a stylesheet-rule probe returning non-null for `.text-emerald-400`, `.text-rose-400`, `.text-amber-400`, `.text-slate-400`, `.text-slate-300`, `.bg-emerald-500`, `.bg-rose-500`, `.bg-amber-500` — including the amber/rose ones that `SIM-BUYER` does not render, so J-03/J-04/J-05/J-06 are not left latent-broken.
- [ ] **J-08 remains green** — UI ≡ REST value agreement re-verified (the color fix changed no value; this is the guard that proves it).
- [ ] No anti-goal violation introduced — single source of truth holds (no value recomputed or re-derived in the UI), no fabricated data, price-impact guard intact.
- [ ] Frontend `npm run build` is clean; backend pytest re-run shows no regression (expected 24/24 unchanged).
- [ ] Dev handoff written at `docs/handoffs/goal-i_will_be_rich-iter-3-dev.md`.

## TESTING REQUIREMENTS

- **Browser (the real gate):**
  - **Precondition (iter-1 lesson):** `rm -rf apps/frontend/.next`, restart the managed dev server with `NEXT_PUBLIC_API_URL` set, confirm HTTP 200 before driving the browser. An all-SKIPPED run does not count as verification.
  - **J-01, J-02** on `SIM-BUYER`: re-verify the data/behavior assertions that already passed in iter-2, **plus** the color layer.
  - **Color verification method (iter-2 lesson — NOT a screenshot glance):**
    - `getComputedStyle` on (a) the headline state label, (b) the confidence-bar fill element, (c) a BUY trade-side cell, (d) the positive `buy_price_impact` value → assert each is emerald (Tailwind v3 defaults, `theme.extend` empty: `text-emerald-400` → `rgb(52, 211, 153)`, `bg-emerald-500` → `rgb(16, 185, 129)`) and explicitly **not** slate `rgb(226, 232, 240)`. Confirm exact tokens against the project's Tailwind palette if in doubt.
    - Stylesheet-rule probe over `document.styleSheets` asserting each of the 8 classes above resolves to a real rule (non-null).
  - **J-08** re-verify: UI tape_state/confidence/features still exactly match `GET /tape/SIM-BUYER/state` and `.../features`.
- **Unit/integration:** no new backend code — re-run `cd apps/backend && .venv/bin/python -m pytest tests/ -v` to confirm no regression. Frontend: `cd apps/frontend && npm run build` must succeed and the served bundle must contain the 8 base utilities.
- **Error cases:** presentation-only change, so no new input validation. The key non-happy-path check is the **latent-class guard**: confirm the amber and rose base utilities exist in the bundle even though `SIM-BUYER` never renders those states (stylesheet-rule probe), pre-empting the identical defect for J-03/J-04/J-05/J-06.

## NOTES

- **Depth = lean** is deliberate: the defect is precisely root-caused, the fix is a single isolated config (or safelist) change with zero logic/data/API impact, and the lean cycle still runs browser-qa — the real gate here. **Escalate to full only if** browser re-verify surfaces a second defect (e.g. the fix misses a class, or a dev-server/build interaction regresses the served bundle).
- **Why this is not a regression risk to J-08:** the change touches only which CSS utilities are emitted; it cannot alter an engine-computed value. J-08 is in Required-still-passing precisely to prove that empirically.
- **Forward value:** fixing all 8 classes now (not just the emerald ones `SIM-BUYER` exercises) pre-empts the identical latent breakage for the color-critical upcoming journeys — J-03 (`bg-rose-500` bar), J-04/J-05 (amber `text-amber-400`/`bg-amber-500`, where amber is *how the user distinguishes absorption from control*), and J-06 (amber unclear). That is why the DoD requires the rose/amber utilities to be present even though they don't render on `SIM-BUYER`.
- **Coherence:** iter-2 was COHERENCE-PASS; this iteration adds no value/endpoint/route/nav and introduces no new coherence surface. The one open advisory (stream-status dot) is explicitly deferred above and not worsened here.
