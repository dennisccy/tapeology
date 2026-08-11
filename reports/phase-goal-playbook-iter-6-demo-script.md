# Demo Script — goal-playbook-iter-6

**Mode:** record
**Date:** 2026-08-11
**Frontend URL:** http://localhost:3301

## Highlights

### Step 01 — Open the Desk page

- **Narration:** The Desk page brings together session analysis, briefing, runs, and playbook signals in one view. Let's explore the new Range Trade and Double Top detectors that landed this iteration.
- **Action:** Navigate to /desk
- **Point out:** The page loads without error, showing the Screen History calendar and Forward Returns. Scroll down to find the Playbook Signals section with the date input and Run Playbook button.
- **Screenshot:** reports/demo/goal-playbook-iter-6/step-01.png

### Step 03 — Run the Playbook

- **Narration:** Click 'Run Playbook' to detect and measure all nine setup families on this session's recorded bars. This is a fully explicit operator act — nothing runs automatically.
- **Action:** Click the element
- **Point out:** The button briefly shows 'Computing…' and then returns to 'Run Playbook'. A confirmation message appears: 'Playbook run complete for 2026-06-22.' The signals table populates below with detected setups.
- **Screenshot:** reports/demo/goal-playbook-iter-6/step-03.png

### Step 04 — Expand and view the Range Trade signal  [NEW]

- **Narration:** Range Trade is a new detector that finds where price tested and held a support zone twice and then reversed up. The RTAAA row displays this pattern with side 'long' and reveals its geometry when clicked.
- **Action:** Click "RTAAA"
- **Point out:** The RTAAA row in the signals table shows the chip 'Range Trade' with side 'long'. When expanded, it displays the trigger price, invalidation level, and a new geometry line: 'range <N> MBR wide · low zone touches <N> · high zone touches <N> · broke at slot <N>'.
- **Screenshot:** reports/demo/goal-playbook-iter-6/step-04.png

### Step 05 — Expand and view the Double Top signal  [NEW]

- **Narration:** Double Top detects reversals where price forms two roughly-equal swing highs and breaks through the valley between them. The DTAAA row displays this pattern with side 'short' and its own geometry metrics.
- **Action:** Click "DTAAA"
- **Point out:** The DTAAA row shows the chip 'Double Top' with side 'short' in the same signals table. When expanded, it reveals: 'gap <N> MBR · separation <N> bar(s) · depth <N> MBR · nominal risk <N> MBR · broke at slot <N>'. These fields are unique to the double-extreme family and did not exist before this iteration.
- **Screenshot:** reports/demo/goal-playbook-iter-6/step-05.png

### Step 08 — Playbook now detects all nine setups

- **Narration:** The Playbook now detects and displays all nine setup families in one cohesive Playbook Signals section. Range Trade, Double Top, and Double Bottom join the five that shipped in earlier iterations, completing the book's full detector set.
- **Action:** Navigate to /desk
- **Point out:** The Playbook Signals table can now show up to nine setup types. All new detectors use the exact same chip styling, table layout, and row-expansion interaction pattern as the five existing families. Zero new navigation, zero new buttons, zero breaking changes.
- **Screenshot:** reports/demo/goal-playbook-iter-6/step-08.png

## Full tour (text only)

### Step 02 — Enter the session date  [NEW]

- **Narration:** The Playbook intro now lists all eight setup families — the five that shipped earlier plus the three new ones: range-trade, double-top, and double-bottom. We'll use the fixture date 2026-06-22, which contains both a Range Trade signal and a Double Top signal.
- **Action:** Type "2026-06-22" into the element
- **Point out:** The amber panel reads: 'Run Playbook detects and measures the opening-range-break, …, capitulation, range-trade, double-top, and double-bottom families…' The date input is filled with '2026-06-22'.

### Step 06 — Verify the five prior setup families unchanged

- **Narration:** The five setups from earlier iterations — opening-range-break, jump-base-explosion, drop-base-implosion, cup-and-handle, and capitulation — continue to render with identical wording and values. No regression.
- **Action:** Navigate to /desk
- **Point out:** Earlier rows in the same signals table show the original five setup chips with their pre-existing geometry lines. Each prior detector's wording, layout, and metrics are pixel-for-pixel identical to before this iteration.

### Step 07 — Confirm all other Desk sections are intact

- **Narration:** Every other section on Desk — Screen History, Forward Returns, Briefing, Runs, Pins, Compare, and Provenance — continues to work with no layout shifts or missing content. The new detectors integrate seamlessly.
- **Action:** Navigate to /desk
- **Point out:** Scrolling the page reveals all sections render correctly with unchanged spacing and structure. The only visible change is the three new setup chips (Range Trade, Double Top, Double Bottom) in the signals table.
