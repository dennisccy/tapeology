**Verdict:** COHERENCE-PASS

## Iteration 5 — The /performance page: PnL per enhancement, honestly (J-05)

**Session:** tape_to_profit
**Iteration index:** 5
**Snapshot SHA:** 15ecd4b1fa4bd0e5429a2129ec5755c0633a62ad

**Diff note:** the snapshot SHA is a `git stash` commit (`git cat-file -t` → `commit`; its message
is `WIP on goal/tape_to_profit: 9d89ec6 goal(tape_to_profit): iter 4…`) taken mid-way through the
interrupted prior dispatch of THIS iteration — `git merge-base --is-ancestor HEAD 15ecd4b1…`
confirms HEAD (`9d89ec6`, the iter-4 commit) is an ancestor of it, i.e. it already contains the
J-05 implementation. `git diff 15ecd4b1… --stat` therefore shows only
`runs/goal-session-tape_to_profit/telemetry.jsonl` (append-only pipeline log) — confirming THIS
dispatch's re-verification made no additional code changes ("verified as-is", the spec's
explicitly anticipated successful outcome for a resume dispatch). The real "what did iteration 5
change" comparison is `git diff HEAD` (iter-4's commit → current working tree, tracked + `git
status` untracked files combined), which I used throughout: 7 modified tracked source/test files
(`apps/backend/app/meta.py`, `apps/backend/app/research/routes.py`,
`apps/backend/app/mcp/__init__.py`, `apps/backend/tests/test_meta_routes.py`,
`apps/backend/tests/test_mcp_server.py`, `apps/frontend/lib/api.ts`, `apps/frontend/lib/types.ts`)
plus untracked new files read directly (`apps/backend/app/research/profiles.py`,
`apps/backend/tests/test_profiles_api.py`, `apps/frontend/app/performance/page.tsx`,
`runs/goal-session-tape_to_profit/journey-scripts/J-05.json`, and the `J-01.json` evolution).
`Frontend Present: yes` — the era's first frontend iteration; no `ui-surface-map` report exists
(`reports/phase-goal-tape_to_profit-iter-5-ui-surface-map.md` absent, expected for a lean
iteration), so surfaces were derived directly from the diff. Independent corroboration: the
reviewer's report (`reports/reviews/goal-tape_to_profit-iter-5-review.md`, verdict PASS)
reproduced 988 passed/1 skipped and confirmed zero diff on every protected file; browser QA
(`reports/phase-goal-tape_to_profit-iter-5-ui-test-results.md`, UT-J-05) ran a live in-page 24/24
page-equals-API check.

---

## Step 1 — Data Contract Check

No violations found.

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Row 32 — PnL-ledger rows (now also displayed on `/performance`) | OK | Single fetch `fetchPnlLedger()` (`apps/frontend/lib/api.ts:812-828`) calls `GET /research/pnl/ledger` only — the pre-existing row-32 endpoint (zero diff to `apps/backend/app/research/pnl_ledger.py`, confirmed via `git diff HEAD --stat` returning empty for that path). The page renders every numeric via `String(m.net_r)` / `String(m.net_usd)` / `String(m.n)` (`apps/frontend/app/performance/page.tsx:58-60`) — no arithmetic, no re-derivation, matched by the reviewer's independent "zero client-side arithmetic" finding and QA's 24/24 exact-value check |
| Row 32 — register string | OK | Rendered as `{ledger.register}` straight from the API payload (`page.tsx:251`); grepped all of `apps/frontend` for the literal register text or a `REGISTER =`-style constant — zero hits anywhere in frontend source, including comments. No second copy exists |
| Row 32 — "insufficient sample" label | OK (formatting, not computation) | The API serves only a boolean `insufficient_sample` and a numeric `min_sample_size` (`apps/backend/app/research/pnl_ledger.py:212,214` — `values["insufficient_sample"] = values["n"] < min_n`); the frontend interpolates both verbatim served values into display text, `` `insufficient sample (n < ${minN})` `` (`page.tsx:64`, `minN` = `ledger.min_sample_size` prop) — this is display formatting of two verbatim served values per Part A rule 3, not a duplicate computation; the threshold is never hardcoded |
| Row 33 — Indicator profiles + champion pointer (serving side landed THIS iteration, per spec) | OK | Computed once in `profiles_projection()` (`apps/backend/app/research/profiles.py:31-39`), which imports — never redeclares — `PROFILE_DEFAULT` (`apps/backend/app/research/backtests.py:125`) and `STRATEGY_V1_ID` (`apps/backend/app/config.py:22`); a dedicated source-scan test (`apps/backend/tests/test_profiles_api.py:57-64`) asserts no literal `"default"`/`"v1"` string exists in `profiles.py`. Exactly ONE route, `GET /research/profiles` (`apps/backend/app/research/routes.py:1614-1620`), calls `profiles_projection()` directly; non-GET verbs are FastAPI's automatic 405 (no handler registered) |
| Row 33 — champion, frontend consumption | OK | `fetchProfiles()` (`apps/frontend/lib/api.ts:830-846`) → `GET /research/profiles` only; the champion summary panel reads `profiles.champion.strategy_id` / `.profile` (`page.tsx:295,301`) directly off that payload — never inferred from ledger provenance, never a hardcoded literal, exactly the watchpoint the iteration spec called out |
| Row 35 — UI route map | OK | `/performance` added at its single owner, the `UI_ROUTES` tuple in `apps/backend/app/meta.py:29` — the ONLY route-list edit in the diff. `apps/frontend/components/NavBar.tsx` has zero diff and zero `git status` entry; read in full — it fetches `GET /meta/ui-routes` and renders `nav:true` entries with no hardcoded fallback list (`NavBar.tsx:42-56`, `84-110`). `test_meta_routes.py` pins 5 entries / 4 nav-true / `/performance` present |
| MCP surface | OK | `git diff HEAD -- apps/backend/app/mcp/__init__.py` is exactly one hunk, two doc-string sentences (module docstring) — no proxy/dispatch/handler code touched. `/research/profiles` becomes reachable only through the pre-existing generic `get_endpoint` allowlist dispatch (no new tool registered); `test_mcp_server.py` adds byte-identity coverage on the live 200 and relocates (not deletes) the honest-404 leg to a permanently-unknown path |
| New-value scan | OK — nothing unregistered | The only new displayed values this iteration (profile registry + champion pointer) map exactly onto pre-registered Data Contract row 33; no value appeared that isn't already a contract row |

## Step 2 — Information Architecture Check

No violations found.

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| `/performance` page | OK — canonical home | Blueprint IA table: "J-05 performance page \| `/performance` \| Performance" — the page lives at exactly `apps/frontend/app/performance/page.tsx` (Next.js App Router → route `/performance`), matching verbatim |
| Reachability | OK — 1 click (≤2 bar) | `apps/frontend/app/layout.tsx:21` mounts `<NavBar/>` globally in the root layout (unchanged, zero diff) — every page carries the top bar. `NavBar.tsx` renders `nav:true` entries from `GET /meta/ui-routes`, which now includes `/performance`; the golden-script evidence (`J-05.json` steps 1-2, `J-01.json` step 4) and QA's spot-check on `/journal` and `/studies` (`reports/phase-goal-tape_to_profit-iter-5-ui-test-results.md`, UT-J-05) confirm the 4-link bar renders identically on every page — Performance is a direct top-bar link, one click from anywhere |
| Duplicate home | OK — none | No second PnL/ledger/performance page exists anywhere in the diff or `apps/frontend/app`; `git diff HEAD --stat` shows zero changes to `/`, `/journal`, `/studies` |
| Parallel shell | OK — none | `apps/frontend/app/performance/page.tsx:216-333` returns only `<div><main>…</main></div>` — no own `<nav>`, header bar, or layout; the persistent top bar is exclusively the shared root layout's `<NavBar/>`, untouched by this iteration |
| Hardcoded route/link | OK — none | Grepped all of `apps/frontend/**/*.{ts,tsx}` for a literal `/performance` string outside the new page itself: zero hits in source; the only matches are Next.js's generated, gitignored `.next/types/*.ts` build artifacts, not source. The nav entry exists solely at its row-35 single owner, `app/meta.py` |

- **No duplicate home, no parallel shell, no hidden feature.** `/performance` is reached exactly
  where the blueprint pre-declared it, via the pre-existing route-map mechanism with zero
  NavBar/frontend nav edits — the "ships together with the page" no-dead-link rule the blueprint
  requires.

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- None material. This iteration is unusually explicit about single-ownership at every point the
  iteration spec itself flagged as a coherence watchpoint (arithmetic-free rendering, champion
  sourced only from `/research/profiles`, register string sourced only from the API payload, zero
  hardcoded route list, `profiles.py` reusing rather than duplicating the two id constants, a
  dedicated source-scan test enforcing that, zero diff to every protected compute module, and an
  MCP diff confirmed to be documentation strings only) — independent inspection of the diff and
  source confirms every one of them, corroborated by the reviewer's independent re-run and
  browser-QA's 24/24 page-equals-API check.

## Summary

Iteration 5 executes exactly the blueprint's pre-declared skeleton: the ONE new nav entry of the
era lands solely through its single owner (`UI_ROUTES` in `app/meta.py`, row 35), picked up by the
already-generic `NavBar.tsx` with no frontend nav edit; the new `/performance` page is a pure,
arithmetic-free verbatim renderer of two registered endpoints (`GET /research/pnl/ledger`, row 32,
and the newly-landed `GET /research/profiles`, row 33) sharing the shared root-layout shell with no
duplicate home anywhere; and row 33's serving side is landed from the existing single-copy
`PROFILE_DEFAULT` / `STRATEGY_V1_ID` constants with a test enforcing no literal duplication. The
MCP diff is documentation strings only, with zero proxy/handler logic touched. No Data Contract
violation, no Information Architecture violation — COHERENCE-PASS.
