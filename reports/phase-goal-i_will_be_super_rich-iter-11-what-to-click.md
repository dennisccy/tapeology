# Phase goal-i_will_be_super_rich-iter-11 — What to Click (Operator Verification Guide)

**Phase:** goal-i_will_be_super_rich-iter-11
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3650`
- Backend running with valid Alpaca credentials in `apps/backend/.env`
- Backend has been running for at least 10 seconds (symbol universe pre-warms on startup)

---

## Verification Steps

1. Open `http://localhost:3650` in your browser
   - **Expect:** The cockpit page loads. A symbol search input field is visible. Mode options ("Simulated", "Historical", "Live") are visible. No error banner is shown.
   - **Broken looks like:** A blank white page, a "Cannot connect" browser error, or a red error banner covering the page.

2. Click the symbol search input field and type the single letter "A". Wait 2 seconds without typing anything more.
   - **Expect:** No suggestions appear in the dropdown below the input. No "Searching..." spinner appears. The input is ready for more typing.
   - **Broken looks like:** A dropdown appears with suggestions after typing just "A", or a loading spinner that never resolves.

3. Clear the field (select all and delete) then type "AAPL" at a normal pace. Wait 1 second after the last letter.
   - **Expect:** A dropdown appears within approximately 1 second showing at least one suggestion that includes "AAPL". The result appears promptly — no multi-second stall.
   - **Broken looks like:** The dropdown does not appear after 3 seconds, or a visible stall of 3+ seconds occurs before suggestions show.

4. Clear the field and type "TS" quickly, then immediately type "AAP" (the field now shows "TSAAP" or similar — that is fine). Then clear the field and type "AAP" only. Wait 1 second.
   - **Note:** This checks that rapid typing does not leave stale "TS" results visible. In practice, type quickly and end with "AAP" in the field.
   - **Expect:** The dropdown shows suggestions matching "AAP" (e.g., "AAPL"). No "TSLA" or other "TS"-matching results appear alongside or instead of the "AAP" results.
   - **Broken looks like:** "TSLA" or other "TS" results appear in the dropdown alongside or replacing the "AAP" results.

5. Select "Historical" mode. Type "AAPL" in the symbol search and select "AAPL" from the dropdown. In the date/window picker, choose the widest possible window for a recent past US market day (a full trading session or many hours). Click the "Watch" button. Wait up to 15 seconds.
   - **Expect:** Within 5–12 seconds, a failure/error panel appears containing the text "try a shorter range". The cockpit does NOT show any tape-state classification or confidence value. The error is shown inside the app — the browser does not show its own timeout page.
   - **Broken looks like:** A generic "please try again" message with no actionable instruction, a blank failure panel with no message text, or the browser itself showing a timeout error.

6. Without changing mode or symbol, now choose a short window: select the same recent past date but pick only a 2-minute window during market hours (e.g., 09:30–09:32 ET). Click the "Watch" button. Observe the cockpit over the next 15 seconds.
   - **Expect:** Within 1–2 seconds of clicking "Watch", a waiting/loading indicator appears in the cockpit (an amber pulsing dot or progress state — not a blank screen). Within approximately 10–15 seconds, the tape-state panel shows a non-idle classification (e.g., "Buyer Control", "Seller Control", or "Balanced") with a non-zero confidence value and real feature values.
   - **Broken looks like:** The cockpit stays blank for more than 5 seconds after clicking Watch, or the tape-state panel shows all-zero features after the fetch completes.

7. Click the "Stop" button (or equivalent stop/reset control) to end the current watch. Then, without changing any settings (same symbol, same date, same 2-minute window), click the "Watch" button again and immediately note the time.
   - **Expect:** The cockpit re-populates in under 2 seconds — noticeably faster than the first watch in step 6. The same tape-state classification reappears. No loading spinner lingers for more than 2 seconds.
   - **Broken looks like:** The second watch takes the same 10–15 seconds as the first, or a vendor error appears on the re-watch.

8. Select "Simulated" mode. Click the symbol search field, type "SIM-BUYER" (do not select from the dropdown — just type it directly). Click the "Watch" button. Wait up to 60 seconds.
   - **Expect:** The cockpit populates and the tape-state panel settles on "Buyer Control" (or "buyer_control") with a non-zero confidence value. Features panel shows non-zero values. No error message blocks the watch.
   - **Broken looks like:** An error message appears for "SIM-BUYER", the cockpit stays blank/idle indefinitely, or the tape-state shows a different classification consistently.

---

## What "Working Correctly" Looks Like

- Typing a single character in symbol search produces no dropdown, no spinner — instant silence
- Typing two or more characters quickly shows only the final query's suggestions — no stale results from an earlier keystroke
- A Historical watch for a busy full-day window produces the exact phrase "try a shorter range" in the error panel (not a generic message)
- A Historical watch for a short 2-minute window warms up fast — real classifications appear within ~15 seconds, and a second identical watch takes under 2 seconds

## Common Issues

- **No symbol suggestions appear at all after typing "AAPL":** The backend may still be warming the symbol universe. Wait 10–15 more seconds after backend startup and try again.
- **"try a shorter range" text not appearing in the error panel:** Check that the backend has real Alpaca credentials in `apps/backend/.env`. Without credentials, Historical mode may fail with a different error.
- **Re-watch (step 7) is not faster than the first watch:** Ensure you are clicking Watch with the exact same symbol, date, and window as the first watch. Any change in parameters triggers a fresh vendor fetch, not a cache hit.
- **SIM-BUYER watch never populates (step 8):** Check that the backend is running and that Simulated mode is selected (not Historical). The SIM-BUYER ticker only works in Simulated mode.
