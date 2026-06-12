# Phase goal-i_will_be_super_rich_with_my_loved_ones-iter-17 — What to Click (Operator Verification Guide)

**Phase:** goal-i_will_be_super_rich_with_my_loved_ones-iter-17
**Time required:** ~3 minutes
**Written by:** ui-test-designer

---

## Context

This iteration changed only internal engine code — no new screens, buttons, or fields were added. The sole verification goal is to confirm the existing cockpit still produces the correct output after the engine performance refactor (capability-34). Two regression sentinels are checked: J-68 (cockpit visual identity) and J-08 (REST == UI agreement).

---

## Prerequisites

- Frontend running and reachable at `http://localhost:3650`
- Backend running and reachable at `http://localhost:8000` (confirm with `curl http://localhost:8000/health` — should return HTTP 200)
- No special login required (sim mode is accessible without credentials)

---

## Verification Steps

1. Open `http://localhost:3650` in your browser
   - **Expect:** The home or watch page loads. No error page, no blank screen, no "Cannot connect" message.

2. Type `SIM-BUYER` into the ticker input field and click the "Watch" button
   - **Expect:** The browser navigates to a cockpit page (URL contains `SIM-BUYER`). The page begins rendering panels. Wait up to 15 seconds for the cockpit to stabilize.

3. Look at the **Confidence** value displayed on the cockpit (labeled "Confidence" or shown as a decimal/percentage)
   - **Expect:** A non-zero decimal in the range (0, 1] — approximately `0.86`. If it shows `0`, `undefined`, or is blank, the engine output is broken.

4. Look at the **tape state classification label** displayed alongside the confidence value
   - **Expect:** The label reads `buyer_control`. Any other value (blank, `error`, `0`, `undefined`) is a failure.

5. Look at the **Observations panel** (scroll down if needed — labeled "Observations" or similar)
   - **Expect:** At least one observation text row is visible with a non-empty description. An empty list or rows showing "undefined" indicate engine output is missing.

6. Look at the **Event Log panel** (labeled "Event Log" or "Events")
   - **Expect:** At least one timestamped event row is visible. A completely empty log or an error placeholder is a failure.

7. Open a new browser tab and navigate to `http://localhost:8000/tape/SIM-BUYER/state`
   - **Expect:** The browser shows a JSON response (HTTP 200). The JSON must contain `"classification": "buyer_control"` and a `"confidence"` value that matches (within rounding) what the cockpit displayed in step 3.
   - **Broken looks like:** HTTP 404 or 500, missing `classification` field, or `classification` value that differs from the cockpit label.

---

## What "Working Correctly" Looks Like

- Cockpit renders all panels with visible, non-blank content
- State label reads `buyer_control` with a confidence value near 0.86
- REST endpoint returns the same classification and confidence the cockpit displays

## Common Issues

- **Blank cockpit or "Cannot connect":** Confirm both services are up — run `curl http://localhost:8000/health` (backend) and check that `http://localhost:3650` responds in the browser (frontend).
- **Cockpit shows 0 confidence or blank state:** The engine may not have processed enough events yet — wait 10–15 more seconds after the watch starts before checking.
- **REST returns 404 for `/tape/SIM-BUYER/state`:** The backend route may use a different path prefix — try `http://localhost:8000/tape/SIM-BUYER` (without `/state`) and locate the classification and confidence fields in the returned JSON.
