# Phase goal-structure_ui-iter-3 — UX Regression Review

**Date:** 2026-07-07

**Verdict:** UX-REGRESSION-WARN

---

## New Capability Discoverability

| New capability | Navigation path | Clicks from home | Verdict |
|---|---|---|---|
| Comparison section (dataset selector, "Run comparison", results) | `/structure` (Structure tab, 1 of 5 persistent top-bar links present on every page) → scroll to the 3rd section, below Registry. No new route, no new nav entry, no menu/drawer. | 1 click + scroll | Discoverable |
| Side-by-side aggregates (`n`/net R/net $/`win_rate`/`max_drawdown_r`) | Inline inside the Comparison panel once "Run comparison" resolves — no separate tab/modal | same as above | Discoverable |
| Per-class A/B/C table + `insufficient_sample` chip | Inline, directly under each strategy's headline aggregates | same as above | Discoverable |
| Register / honesty disclaimer | Inline, amber line under each side's results | same as above | Discoverable |
| Champion pointer (read-only) + Founding-baseline row | Inline, a two-column row above the dataset selector | same as above | Discoverable |

Confirmed directly (not only from handoff prose) via `reports/qa/goal-structure_ui-iter-3-evidence/TC-01-structure-page.png` and `TC-02-comparison-section.png`: both screenshots show the Structure page's persistent 5-link nav (Cockpit / Journal / Studies / Performance / **Structure**) and all three sections (Levels & Zones → Registry → Comparison) stacked on one page, reachable by scroll alone with zero additional clicks or hidden controls. This is well within the skill's 2-click discoverability bar.

**Label clarity:** "Run comparison," "Comparison," "Champion (moved never by this view)," "Founding baseline (PnL ledger)" are consistent with vocabulary the app already established in Registry (iter-2) and `/performance`. No new jargon, no label that misdescribes its function.

**Visual feedback — code-confirmed, but not yet screenshot-confirmed for the populated state (see Evidence Gap flag below).** Read directly from `apps/frontent/app/structure/page.tsx` (verified in the actual source, not only the handoffs):
- Per-side progress: `"Queued…"` / `"Running…"` (line 575) plus a live `{backtest.events_processed} events processed` counter (line 578).
- The "Run comparison" button disables and relabels to `"Running…"` while in flight (lines 1153–1157), preventing double-submit.
- Six distinct honest-state components exist with distinct `data-testid`s and copy: `comparison-no-datasets` (1123), `comparison-run-error` (1162), `comparison-poll-error` (1165), plus per-side `failed`/`cancelled` blocks (rose-bordered, line 587).

**Design system conformance — screenshot-confirmed.** In `TC-02-comparison-section.png`, the new "COMPARISON" panel uses the identical chrome (border-slate-800, bg-slate-900/60, uppercase tracking-wide title) as the pre-existing "STRUCTURE" and "REGISTRY" panels in the same image — no new visual language introduced. The header subtitle (`data-testid="structure-framing"`, `page.tsx:843-844`) now previews all three sections, closing the iter-2 audit's F1 carry-forward item; confirmed both in source and in `TC-01-structure-page.png`.

---

## Regression Risk

| Shared surface | Prior feature it serves | This iteration's touch | Risk |
|---|---|---|---|
| `apps/frontend/components/StructureChart.tsx` | J-01 — levels/zones chart + iter-1 audit's z-index occlusion fix | **Zero diff** (`git diff --stat` confirmed empty this session); `z-10` fix and "No candles to draw at this as-of time." copy are still present at line 99-100 | **Low** — verified structurally, not just by claim |
| `apps/frontend/app/structure/page.tsx` (Registry section + champion badge) | J-02 — strategy registry/champion cards | Comparison section appended below; reuses (does not re-fetch) `registry.champion` state; iter-2 audit's own T2 "future test-hygiene item" (same-page testid collision risk) is the exact risk this iteration had to avoid | **Low** — resolved and verified: `champion-strategy`/`champion-profile` (lines 988/997, Registry) vs. `comparison-champion-strategy`/`comparison-champion-profile` (lines 1051/1060, Comparison) are distinct strings in source, and `TC-02-comparison-section.png` shows both panels rendering simultaneously with the same `v1`/`default` values and no visual collision |
| `apps/backend/app/meta.py`, `apps/frontend/components/NavBar.tsx` | J-04 — data-driven 5-link nav | **Zero diff** for both files this session | **Low** — `TC-01-structure-page.png` shows exactly 5 nav links |
| `apps/frontend/app/performance/**` | J-04 — `/performance` regression sentinel | **Zero diff** this session | **Low** |
| `apps/backend/**` (all) | J-04 — frozen foundations / `config_fingerprint` | **Zero diff** this session (confirmed independently via `git diff --stat -- apps/backend`) | **Low** |

No shared component in this iteration's actual diff (`apps/frontend/app/structure/page.tsx`, `lib/api.ts`, `lib/types.ts`, `README.md` — confirmed via `git diff --stat`) shows evidence of touching J-01/J-02/J-04 behavior beyond the one documented, deliberately-distinct-testid champion reuse. This is a well-contained, low-risk diff.

---

## UI vs Backend Parity

| Backend capability | Surfaced in `/structure`? | Assessment |
|---|---|---|
| Backtest aggregates (`n`/`net_r`/`net_usd`/`win_rate`/`max_drawdown_r`) via `GET /research/backtests/{id}` | Yes — per-side result block | Complete |
| `aggregates_by_class` + `insufficient_sample` | Yes — `BacktestClassTable`, inline chip | Complete |
| `register` string | Yes — verbatim per-side | Complete |
| Champion pointer | Yes — read-only, reused from Registry's own fetch | Complete |
| PnL ledger founding row | Yes — new founding-baseline panel | Complete |
| `result.null_baseline` (seeded random-entry baseline) | **No** — typed in `types.ts`, served by the backend, never rendered | Disclosed explicitly in `user-visible-changes.md`'s "Not Visible Yet"; not named anywhere in the phase spec's In-Scope/Data-contract bullets. **Acceptable gap**, not a defect against this iteration's own goal. |
| `POST /research/backtests/{id}/cancel` | **No** — exists, used by the Studies page for its own jobs, no Comparison-section control | Explicitly out of scope per the execution plan ("New user actions" names only the dataset selector + Run button). **Acceptable, intentional.** |
| `GET /research/backtests` (plural/list) | **No** — no way to browse or resume a previously-run comparison | Not required by this iteration's DoD or `docs/goal.md`; honestly disclosed. **Acceptable for this iteration**, worth a future card. |
| Full dataset metadata (checksum, event counts, source, timeframe) | **Partial** — selector shows only `symbol · split · id-prefix` | A `/datasets` library page is explicitly out of scope (roadmap Card 5.9). **Acceptable.** |

**Conclusion:** every backend capability this iteration's spec calls for is surfaced. The four gaps above are all pre-disclosed, explicitly out-of-scope, and none contradicts the phase's own "In Scope"/"Out of Scope" bullets — this is intentional scoping, not a silent parity failure.

---

## Flags

### Hidden Capabilities
None. The Comparison section lives on the already-navigable `/structure` page, appended below Registry, reachable by scrolling — no new route or control is needed to find it.

### Undiscoverable Capabilities
None. 1 click from the persistent top nav (Structure tab, present on every page) plus a same-page scroll — confirmed directly in `TC-01-structure-page.png` / `TC-02-comparison-section.png`, both showing the section fully rendered with no interaction beyond scrolling.

### Potential Regressions
None found. All three regression-risk surfaces (J-01 chart, J-02 registry/champion, J-04 nav/performance/backend) were checked against actual `git diff` output, not only handoff prose — see the Regression Risk table above for the specific files and line numbers.

### Visual Consistency
No issue. The new Comparison panel matches the established `/structure` page style exactly — confirmed via screenshot: identical `Panel` chrome, font-mono numerics, and the same amber/rose token usage as the pre-existing sections and as `StudyResultsView`'s established `results-failed` styling. No arbitrary/one-off spacing or color value found in the reviewed source. The founding-baseline panel's unrounded float values (e.g. `-0.16000000000000001136`) are the correct, intentional "verbatim, never reformatted" behavior this session's anti-goals require — not a rendering defect.

### Evidence Gap (flagged for the downstream auditor — not a UI defect)
- **The single riskiest and most novel render in this iteration — the populated/`done` Comparison result (side-by-side aggregates, per-class `insufficient_sample` chips, verbatim register, the honest keyless non-survivor outcome) — has no independent screenshot anywhere in this iteration's artifact trail.** The evidence directory (`reports/qa/goal-structure_ui-iter-3-evidence/`) holds exactly 3 images (`UT-01-navigate.png`, `TC-01-structure-page.png`, `TC-02-comparison-section.png`, all filesystem-timestamped ~08:33), and all three show only the pre-run **idle** state ("Choose a dataset, then Run comparison…", dataset placeholder unselected). The specific byte-for-byte values quoted in the dev handoff (`n=5`, `net_r=-1.2392857142863114`, `structure_tape` → `"no trades (n=0)"`, etc.) are the developer's own self-reported live check; the `qa` report correctly attributes them to "the dev handoff documents" rather than claiming to reproduce them; the dedicated `browser-qa-agent` recorded **SKIPPED, 0/26** ("frontend not running"); `demo-narrator` also recorded **SKIPPED** ("Frontend... did not respond after 90s"). This is exactly the gap this iteration's own phase spec quotes from `lessons.md`: **iter-0** ("no populated screenshot = `unknown`, not `passing`") and **iter-1(b)** ("independent re-run required, not the developer's/auditor's own verification alone").
- **Root cause is environmental/timing, not a code defect**, confirmed by timestamp: the frontend/backend were reachable through dev + review + QA (screenshots captured 08:33, `qa.md` written 08:35) and had gone unreachable by the time `browser-qa-agent` (08:48) and `demo-narrator` ran — my own precondition check against `localhost:3301`/`:8301` (this review) also found both unreachable. Direct source inspection (`page.tsx` state-branch structure, progress copy, disabled-button logic, honest-state testids cited above) shows a complete, internally consistent implementation matching every description in the dev/frontend handoffs and the `ui-surface-map` — nothing suggests the code itself is broken, only that its populated output is unconfirmed by an independent, photographic source this pass.
- **Secondary note on the `browser-qa-agent`'s own report:** it describes the evidence directory's contents as pre-existing "unrelated artifacts from a prior session," but the three named files carry timestamps ~15 minutes before that report was written and match this iteration's own naming convention and the `qa` agent's own description of what it captured — they are this iteration's own (partial) evidence, not a prior session's. This does not change the SKIPPED verdict (the services genuinely were down by the time `browser-qa-agent` ran), but a downstream reader should not conclude "zero browser evidence exists this iteration" — some exists (idle-state only), just not the populated-state evidence the Definition of Done specifically calls for.

---

## Recommendation

1. **Before J-03 is treated as fully closed, re-run `browser-qa-agent` (and ideally `demo-narrator`) against the live app** to capture independent, populated-state screenshot evidence: a completed comparison run showing the side-by-side aggregates, the per-class `insufficient_sample` chips, the verbatim register, and — if practical — at least one of the `failed`/`cancelled`/`no-datasets`/`poll-error` states. This mirrors the exact closure step iter-1's audit performed (its own T1 finding) and iter-2's audit re-confirmed (its UT-06 independent re-check) — J-03, as the session's single riskiest journey, warrants the same independent-confirmation discipline this iteration's own spec already cites (lessons iter-0, iter-1(b)) before certification.
2. No code change is recommended. Discoverability, regression-safety, and backend parity are all sound and verified directly (via `git diff`, source inspection, and the two idle-state screenshots that do exist), not merely asserted by the handoffs. The one open item is capturing the missing live evidence — an operational/QA-sequencing step, not a development task.
