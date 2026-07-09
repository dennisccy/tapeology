# Phase goal-yahoo_fetch-iter-2 — UX Regression Review

**Date:** 2026-07-09

**Verdict:** UX-REGRESSION-WARN

---

## New Capability Discoverability

Three new backend capabilities ship this iteration (per `user-visible-changes.md` /
`implementation-summary.md`): (1) five additional fetchable Yahoo timeframes (`1w`/`1h`/`5m`/`1m`,
joining the existing `1d`), (2) a derived `4h` series resampled from real `1h` bars, (3) a
distinct, honest error message for unsupported-timeframe vs. out-of-retention failures.

- **Navigation path: none, for any of the three.** All three are reachable only via a direct
  `POST /research/bars` call (curl/script) or the MCP `bars` proxy. Zero clicks are possible
  because there is no UI element at all — no button, form field, or menu entry — that issues this
  request. Confirmed independently: `apps/frontend/lib/api.ts` defines only a `GET` wrapper for
  `/research/bars`; grep for a POST caller of that endpoint across `apps/frontend/` returns nothing
  (matches `ui-surface-map.md`'s own finding).
- **This is not an oversight — it is disclosed at every layer.** The phase spec's own metadata
  says `Frontend Present: no`; its IN SCOPE/OUT OF SCOPE sections name the fetch control as
  explicitly deferred to **J-05**; `plan.md`'s UI Evolution section states "none" five times with
  full rationale; `user-visible-changes.md`'s "Not Visible Yet" section says outright "There is
  still no on-screen control anywhere in the app to fetch bars from Yahoo Finance, at any
  timeframe." No artifact anywhere describes this capability as user-facing-complete. Per this
  agent's own Step 3 rule ("if capabilities are intentionally backend-only for this phase, that is
  acceptable") and the skill's own remediation for a hidden capability ("document explicitly why it
  is intentionally hidden" — already done, extensively), this does **not** warrant a Hidden
  Capability flag. It is listed here for completeness, not as an actionable gap.
- **Label confusion:** none found — no new UI label exists to be confused about.
- **Visual feedback:** N/A — no UI trigger exists to produce feedback from.

## Regression Risk

| Shared surface | Prior feature | This iteration's effect | Risk |
|---|---|---|---|
| `apps/frontend/app/structure/page.tsx` — `pickRepresentativeSeries()`, `TIMEFRAME_ORDER`, `StructureChart`, Levels & Zones table | structure_ui J-01–J-04 (`/structure` page: view real S/R levels + candles for a symbol) | Zero source diff (independently confirmed: `git diff --stat HEAD~1 -- apps/frontend/` is empty, and the frontend hasn't been touched since structure_ui's iter-3 commit `62e727b`). But this component's own pre-existing, generic timeframe-picking logic (`TIMEFRAME_ORDER = ["1m","5m","15m","1h","4h","8h","1d","1w","1mo"]`, shortest-available-wins) was written speculatively and, until this iteration, could only ever see `1d` series (Yahoo could fetch nothing else). Now that `1h`/`5m`/`1m`/`4h`/`1w` are fetchable via API/MCP, the **first** time any of those is registered for a symbol, `/structure` will silently and **permanently** switch that symbol's chart/table from `1d` to the new shortest-available timeframe on the very next page load — permanently because `BarStore` is append-only/immutable, so there is no way to "unregister" the series and no UI toggle to pick a different timeframe manually. | **Medium** |
| J-01/J-06 browser regression re-verification (Structure page renders real Yahoo candles; Cockpit feed badge stays "Simulated"; other pages unbroken) | yahoo_fetch iter-1 (J-01), all prior phases (J-06 sentinel) | Plan.md and the phase spec's NOTES *explicitly* required the browser-qa lane to "actually run and emit screenshot evidence" this iteration — carried forward verbatim as "the iter-0 lesson." It did not. See Flags below. | **Process gap — Medium** |

Detail on the `pickRepresentativeSeries` risk: this is not newly broken code (the component is
byte-identical) and it is not silent in the strictest sense — the existing on-page caption
("Candles: 1h series...") and the Levels & Zones table's Timeframe column would both show the
new value, per `ui-surface-map.md`'s own test recipe. But there is no prominent badge, alert, or
opt-in step before the switch happens, and once it happens it cannot be reverted through the UI.
Today this can only be triggered by someone with API/MCP access (not a browsing user, since no
UI fetch trigger exists yet), which caps the practical exposure — but it will become directly
reachable by ordinary users the moment **J-05** ships the on-screen fetch control, unless J-05
explicitly designs for it. `ui-impact-analyst` already surfaced this transparently and in detail
in both `user-visible-changes.md` and `ui-surface-map.md` — this review's contribution is
classifying it as a J-05 planning input, not asserting it as a defect in this iteration.

## UI vs Backend Parity

| Backend capability (implementation-summary.md) | UI exposure (user-visible-changes.md) | Verdict |
|---|---|---|
| Fetch `1w`/`1h`/`5m`/`1m` Yahoo timeframes | None — API/MCP only | Disclosed gap, intentional (J-05) |
| Fetch derived `4h` (resampled from `1h`) | None — API/MCP only | Disclosed gap, intentional (J-05) |
| Distinct unsupported-timeframe vs. out-of-retention error messages | None — only observable by calling the API directly | Disclosed gap, intentional (J-05) |

No backend capability is described as "complete" anywhere while being silently absent from the UI
narrative — `implementation-summary.md`'s own "Backend-Only Items" section states plainly "there
is still no on-screen button for it yet." The phase GOAL text itself scopes to "the operator" via
API/MCP, not a browser user, so the phase goal does not imply user-facing delivery this iteration.
Parity gap is real but fully disclosed, consistent with the session's established J-01→J-02→J-03→
J-04→J-05 sequencing (this is the second of five journeys; UI catches up at J-05).

## Flags

### Hidden Capabilities
- None requiring action. The three new fetch capabilities have no navigation path, but this is
  explicitly, consistently disclosed as intentional across the phase spec, plan, and both UI-impact
  reports, with a named future journey (J-05) that closes it. No remediation action is outstanding.

### Undiscoverable Capabilities
- None — nothing exists in the UI to assess for discoverability beyond "not present."

### Potential Regressions
- **Browser regression evidence for J-01/J-06 was not captured this iteration, despite the plan
  explicitly mandating it.** `plan.md`'s "Frontend Present: yes" section states this flag was set
  *specifically* so the browser-qa lane would run and "emit evidence for the J-01/J-06 regression
  checks," and the phase spec's NOTES carry forward "the iter-0 lesson": "a 'passing' without [a
  screenshot] is unevidenced." Neither happened:
  - `browser-qa-agent` recorded **SKIPPED, 0/10** — frontend and backend both unreachable
    (connection refused) at its run time (~16:16).
  - `demo-narrator` also recorded **SKIPPED** — frontend unreachable after 90s of retries (~16:18),
    even though its own captured frontend log shows the Next.js server briefly served two
    successful `GET / 200` responses earlier in its lifetime.
  - QA's own report (`reports/qa/goal-yahoo_fetch-iter-2-qa.md`) shows the frontend **was**
    reachable (`HTTP 200` at `:3301`) when QA ran (~15:57) — so the service window closed sometime
    between QA and the browser-qa lane. QA's own browser checks (TC-13/14/15) were skipped for a
    *different* reason (no Chrome MCP tool in its headless environment), not service unavailability.
  - The iter-2 evidence directory (`reports/qa/goal-yahoo_fetch-iter-2-evidence/`) is confirmed
    **empty** (`ls` returns zero files) — contrast with iter-1's evidence directory, which holds 19
    screenshots including exactly this kind of J-01/J-06 regression proof (`TC-13-cockpit-home.png`,
    `TC-14-structure-page.png`, etc.).
  - I independently re-probed both services during this review (`curl` to `:3301` and `:8301/health`)
    and got connection-refused on both — the services remain down as of this writing.
  - **This is a known, previously-diagnosed pattern in this exact codebase, not a new phenomenon.**
    `docs/handoffs/goal-structure_ui-iter-4-dev.md` documents the identical failure mode from
    structure_ui iter-3 ("services were reachable through dev+review+QA... and had gone unreachable
    by the time browser-qa-agent... and demo-narrator ran") and concluded, after a fresh cold-start
    test, that it found "no evidence of a persistent blocker" — i.e., environmental/timing, not a
    code defect, though the exact trigger was never pinned down.
  - **Mitigating evidence that no actual regression occurred:** the developer's diff-verification
    (zero changes to `config.py`, `main.py`, `alpaca.py`, `research/levels.py`, and all of
    `apps/frontend/**`), QA's own artifact checks (TC-17 through TC-20, all PASS), and QA's live
    integration test suite (`test_real_yahoo_keyless_daily_fetch_returns_real_bars`, explicitly
    labeled "J-01 regression," PASSED) all independently support that J-01/J-06 are intact at the
    code and API level. My own independent grep of `apps/frontend/` source found zero "yahoo" text
    leakage (the only two hits are an unrelated `next/dist` type-definition field, not product code).
  - **Net assessment:** high confidence nothing actually broke, but the specific evidence artifact
    the plan explicitly required (a screenshot proving `/structure` still renders real candles and
    the Cockpit badge still reads "Simulated") does not exist for this iteration. This is a
    verification-process gap, not a confirmed regression.
- **`pickRepresentativeSeries` latent timeframe-switch** — see Regression Risk table above. Not a
  defect in this iteration (zero code changed, no user can trigger it via the UI yet), but a
  concrete input for J-05 planning: once a fetch control exists, an operator could silently and
  permanently change what a previously-daily symbol displays on `/structure` by fetching an
  intraday timeframe, with only caption text (no badge/alert) marking the change.

### Visual Consistency
- N/A — zero new UI shipped this iteration (confirmed: `git diff --stat -- apps/frontend/` empty
  both by the dev handoff and by this review's independent check against `HEAD~1`). No page or
  component exists to assess against the DESIGN SYSTEM tokens. Matches `plan.md`'s own "Visual
  Requirements: N/A" statement.

## Recommendation

1. **Re-run the browser-qa (and ideally demo-narrator) lane with both services confirmed up and
   held open before the lane starts**, to capture the J-01/J-06 screenshot evidence the plan
   explicitly required and the iter-0 lesson explicitly warns not to skip. This mirrors the exact
   remediation `goal-structure_ui-iter-4` already used successfully for the same class of gap
   (a dedicated developer step that starts services, verifies them, and hands a stable window to
   the next pipeline stage). This is the only outstanding action from this review — treat as
   priority given the plan's own "MUST emit evidence" language and the carried-forward lesson.
2. **Feed the `pickRepresentativeSeries` latent-switch finding into J-05's design**, not as a
   blocker for J-02's closure. When the `/structure` fetch control ships, consider a visible
   timeframe indicator/selector (not just caption text) and/or an explicit confirmation before a
   fetch would change a symbol's default displayed timeframe, so the switch documented above is a
   deliberate user choice rather than an incidental side effect of fetching data for another
   purpose.
3. No action required on the zero-UI-exposure gap for the three new backend capabilities — it is
   intentional, fully and consistently disclosed, and correctly sequenced to J-05.
