# Demo Script — goal-i_will_be_super_rich_with_my_loved_ones-iter-5

**Mode:** record
**Date:** 2026-06-10
**Frontend URL:** http://localhost:3650
**Iteration:** 5

## Highlights

### Step 01 — Open the Tapeology Cockpit

- **Narration:** We open the Cockpit — the single-page home for watching and judging the tape. The chart, live panels, and thesis strip load together with no errors.
- **Action:** Navigate to /
- **Point out:** The price chart fills the upper area, and just below it sits the thesis strip showing a clean declare affordance — ready for a new thesis.
- **Screenshot:** reports/demo/goal-i_will_be_super_rich_with_my_loved_ones-iter-5/step-01.png

### Step 02 — Watch SIM-BIDABS (bid absorption scenario)

- **Narration:** We type SIM-BIDABS into the Watch field — a simulated ticker that runs a sustained bid-absorption scenario — and submit. The cockpit acknowledges the watch immediately.
- **Action:** Type "SIM-BIDABS" into "Ticker"
- **Point out:** The heading updates to confirm we are now watching SIM-BIDABS, and the tape state panel begins showing live signals. The thesis strip remains in its idle declare state.
- **Screenshot:** reports/demo/goal-i_will_be_super_rich_with_my_loved_ones-iter-5/step-02.png

### Step 03 — Click Watch to start streaming

- **Narration:** Clicking Watch starts the live stream. The cockpit transitions from idle to an active session for SIM-BIDABS without any page reload.
- **Action:** Click the "Watch" button
- **Point out:** The tape state panel shows bid absorption activity and the price chart begins plotting real-time prints. The thesis strip below the chart is in its idle declare affordance — no chip, no error.
- **Screenshot:** reports/demo/goal-i_will_be_super_rich_with_my_loved_ones-iter-5/step-03.png

### Step 07 — Declare the thesis — strip transitions to active view  [NEW]

- **Narration:** Clicking Declare submits the thesis to the backend. This is the moment that was blocked by a missing database migration in the previous iteration — it now returns success and the strip immediately shows the active thesis.
- **Action:** Click the "Declare" button
- **Point out:** The strip transitions from the idle declare affordance to the active thesis view showing YOUR THESIS / absorption reversal / LONG / invalidation 99.00 / PENDING. A slate-grey chip labelled PENDING appears — the verdict engine has started judging.
- **Screenshot:** reports/demo/goal-i_will_be_super_rich_with_my_loved_ones-iter-5/step-07.png

### Step 08 — Verdict chip updates live to CONFIRMING  [NEW]

- **Narration:** With the thesis active we watch the chip. As the tape delivers buyer-control signals that match the reversal call, the chip transitions from PENDING to CONFIRMING — live, with no page reload.
- **Action:** Navigate to /
- **Point out:** The chip colour shifts from slate-grey to emerald-green and the label reads CONFIRMING. An evidence line below the chip explains in plain language why the tape is confirming the thesis right now.
- **Screenshot:** reports/demo/goal-i_will_be_super_rich_with_my_loved_ones-iter-5/step-08.png

### Step 09 — Watch SIM-SELLER to see a REJECTING verdict  [NEW]

- **Narration:** We switch to SIM-SELLER and declare a long trend-continuation thesis. Because sellers are in control on this ticker, the tape immediately works against the thesis and the chip reads REJECTING.
- **Action:** Navigate to /
- **Point out:** The verdict chip is rose-coloured and labelled REJECTING. The evidence line below it explains in plain language that opposing-side control is pressing price against the declared direction — no raw JSON, just a clear human-readable statement.
- **Screenshot:** reports/demo/goal-i_will_be_super_rich_with_my_loved_ones-iter-5/step-09.png

### Step 10 — INVALIDATED state — terminal treatment on the strip  [NEW]

- **Narration:** When three consecutive prints cross below the declared invalidation level the thesis auto-resolves to INVALIDATED. This is a terminal verdict: the strip shows the heavier rose chip with a glowing ring border, and the offending print is cited in the evidence.
- **Action:** Navigate to /
- **Point out:** The chip has a rose border with a rose ring around it — visually distinct from REJECTING which has no ring. The evidence reads the exact print count and the price that crossed the invalidation level. THESIS INVALIDATED — RESOLVED is shown below.
- **Screenshot:** reports/demo/goal-i_will_be_super_rich_with_my_loved_ones-iter-5/step-10.png

## Full tour (text only)

### Step 04 — Select absorption reversal setup  [NEW]

- **Narration:** In the declare form at the bottom of the cockpit we choose the absorption reversal setup type — the thesis that absorption has been absorbed and a reversal is coming.
- **Action:** Click the "Setup type" combobox
- **Point out:** The Setup type dropdown now shows absorption_reversal selected, and the Level price field is hidden because this setup does not use one — the UI enforces that constraint automatically.

### Step 05 — Choose absorption_reversal from the setup list  [NEW]

- **Narration:** We pick absorption_reversal from the dropdown list. This is the setup the tape on SIM-BIDABS is primed to confirm.
- **Action:** Click the "absorption_reversal" option
- **Point out:** The dropdown closes with absorption_reversal selected. The Level price field remains hidden — the form only shows fields that are relevant to the chosen setup.

### Step 06 — Set direction to long and enter invalidation price  [NEW]

- **Narration:** We select long as the direction and type 99.0 as the invalidation price — the level below current price that would prove the thesis wrong.
- **Action:** Type "99.0" into the "Invalidation price" field
- **Point out:** Direction is set to long and the invalidation field shows 99.00. All three required fields — setup, direction, invalidation — are now filled, and the Declare button is available.

### Step 11 — Inline validation — wrong-side invalidation is caught in the strip  [NEW]

- **Narration:** If we try to declare a long thesis with an invalidation price above the current last traded price the backend returns a 422 error. The error appears as visible text inside the strip itself — not a pop-up, not a toast, not hidden in the console.
- **Action:** Navigate to /
- **Point out:** The error message reads 'a long thesis's invalidation must be below the current last price' and sits inline inside the declare form. The form stays open so the value can be corrected immediately.

### Step 12 — Chart and panel grid are intact throughout

- **Narration:** Throughout all of the above — declaration, live verdict updates, and invalidation — the price chart and lower panel grid keep rendering normally. The thesis strip lives between them without displacing or clipping any other element.
- **Action:** Navigate to /
- **Point out:** Seven canvas elements and the SVG chart overlay are present. The TAPE STATE, QUOTE, and FEATURES panels all render below the thesis strip. Layout is intact with no overlapping or collapsed elements.
