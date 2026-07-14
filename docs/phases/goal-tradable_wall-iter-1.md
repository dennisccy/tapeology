# Goal Iteration 1 — J-01 The tradable level map (1,800 levels → ≤10 bands)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** tradable_wall
- **Iteration:** 1
- **Mode:** next
- **Depth:** full
- **Frontend Present:** no
- **Target journeys:** J-01
- **Required-still-passing journeys:** J-07
- **Anti-goal reminders (verbatim from `docs/goal.md`):**
  - **The tradable map is a lens, never a second levels engine.** `research/tradability.py` consumes `compute_levels` output verbatim (plus bars for scale context); it never re-detects pivots/extremes and never alters the frozen raw computation or its parameters. *(critical)*
  - **Morning-markup discipline.** Any session's map derives only from bars fully completed by the prior session's close; no forming-bar data enters a map, an event, or a chip. *(critical)*
  - **No lookahead** — every value computed as-of T uses only events/bars fully completed at T. *(critical)*
  - **Single source of truth** — each shared value is computed once, owned by one canonical endpoint, and read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor hard-fails violations. *(critical)*
  - **Frozen foundations** — the `v1` strategy, the `default` profile, the tape engine's five states and thresholds, the frozen structure computations, the JSON `BarStore`, and archived-era behaviour stay byte-identical. New work is additive and versioned beside them, never a mutation of them. *(critical)*
  - **Deterministic and seeded** — every random draw uses a config-owned recorded seed; identical requests reproduce byte-identical results; no wall-clock, no unseeded randomness in any research artifact.
  - **Read-only MCP** — MCP tools remain byte-identical proxies of GET endpoints; nothing on the MCP surface can change state. *(critical)*
  - **New strategy code is additive and registered — never a mutation.** `structure_tape_map` is a new config-owned registry entry beside frozen `v1`/`structure_tape`; no frozen definition, parameter, or output changes; the `config_fingerprint` stays `4d665603569b9dbf`. *(critical)* — applied here to J-01's new config constants: they MUST NOT alter `config_fingerprint`.

## GOAL

Distill the raw structure output into a *tradable level map*: a new backend module + owned endpoint (`GET /research/tradability`) + read-only MCP proxy that turns AAPL's ~1,800 levels / 212 zones (as of the 2026-06-22 session) into ≤10 quality-scored price **bands**, with the 300.48–302.07 resistance wall (round-number 300 flagged) ranking in the top 2 resistance bands — computed under morning-markup as-of discipline and consuming `compute_levels` verbatim.

## BACKGROUND

Iter-0 (verify-only baseline) confirmed all six feature journeys absent; the evaluator's explicit recommendation was **build J-01 alone at depth full**, because J-01 is the natural unblocker (J-02 scans its bands, J-04 arms `structure_tape_map` on them, J-05/J-06 render them) and its central failure mode is a *critical single-source-of-truth violation* — forking a second levels engine instead of consuming `compute_levels` verbatim. Per the priority rubric this is rule 3 (unblocker) with the smallest single-risky change set (rules 4–5); no journey regressed (rule 1) and iter-0 wrote no `coherence.md` (rule 2 N/A — zero-diff baseline). J-03/J-06 are correctly deferred (rule 6 — Alpaca-credential-gated, human-owned).

**Depth = full** is justified by intrinsic risk (not ESCALATE — the baseline surprised nothing): J-01 establishes a NEW canonical value + owner crossing the backend + MCP boundary; it introduces new morning-markup **as-of resolution** logic that touches the critical no-lookahead rail (verified: no existing session-calendar/prior-close helper exists — this is genuinely new correctness-bearing code); and it requires unit tests well beyond a browser smoke (determinism, as-of/holiday resolution, REST==MCP byte-identity, `config_fingerprint` stability, `levels.py` byte-identity). These match the "touches data model / requires new tests beyond browser smoke" full-depth triggers.

**Anti-pattern watch (from iter-0 eval + goal rails):** the "lens, never a second levels engine" rail is the primary trap — `tradability.py` must read `compute_levels(...)` output only and never re-detect pivots/extremes; and the new config constants must be excluded from `config_fingerprint` (following the established `bar_timeframes` era-4 exclusion precedent, pinned by a fingerprint-stability test + a real-threshold counter-test) so `4d665603569b9dbf` stays frozen. `lessons.md` is empty (no prior lessons to apply).

## IN SCOPE

### Backend

- [ ] Add `apps/backend/app/research/tradability.py` as the SINGLE owner of the tradable level map. It MUST:
  - Consume `compute_levels(store, symbol, as_of_epoch, config)` output **verbatim** (the `levels` + `confluence_zones` lists) — never re-detect pivots/extremes, never re-open or re-window raw bars for level detection, never touch `levels.py`'s 5 bps / 20 bps parameters. Bars may be read ONLY for price-scale context (band-width sizing) and for the as-of resolution below.
  - Resolve **morning-markup as-of**: for a requested `as_of` inside a session, compute the map from data no newer than the **prior completed session's close** (AAPL 2026-06-22 → basis = the 2026-06-18 close; the 2026-06-19 market holiday has no session, so 06-18 is the prior completed session). Prefer deriving the basis from the stored daily bars (the last completed daily bar strictly before the requested session) so holidays are handled by the data, with no hardcoded calendar. The resolved as-of is what is passed to `compute_levels`.
  - Cluster the levels into price **bands** per side (support / resistance) using a config-owned, **price-scale-aware** band width; keep at most **K bands per side** (config-owned cap, `K ≤ 5`), so ≤10 bands total.
  - Score each band's quality from the config-owned factors: distinct-timeframe breadth, daily touch count, recency, and round-number confluence (config-owned round-number rule; the psychological 300 level is flagged).
  - Inherit each band's A/B/C **class** as a projection of its best member zone (class stays owned by `levels.py` — no re-grading).
  - Be fully deterministic: identical inputs → byte-identical output (stable sort/tie-break; no wall-clock, no unseeded randomness).
  - Honest empty states: a symbol with no bar series, or a symbol with series but no derivable bands at the resolved as-of, returns an explicit empty map (never a fabricated band).
- [ ] Add config-owned constants for the above (band cap `K`, band-width scaling, quality-score weights, round-number rule) to `app/config.py`, pre-registered as named constants (no magic numbers). Add each to the `config_fingerprint` **exclusion set** (they shape only the NEW derived-lens layer, never any frozen tape/level/backtest/strategy output) so `config_fingerprint` stays `4d665603569b9dbf` — following the era-4 `bar_timeframes`/`bar_dir` exclusion precedent.
- [ ] Add `GET /research/tradability?symbol=&as_of=` to `app/research/routes.py` as the single serving endpoint, mirroring the `GET /research/levels` route pattern: parse the ISO `as_of` to epoch once at the route boundary; return the module output verbatim (`{"symbol","as_of", ...}`); missing `symbol` → 422, malformed `as_of` → 422 (never a silent "now" default).
- [ ] Add the read-only MCP proxy `tradability` (thin verbatim `httpx` GET passthrough of `/research/tradability`, two required params `symbol` + `as_of`, following the existing `levels` two-param proxy in `app/mcp/__init__.py`). Read-only; no state change; body byte-identical to the REST response.

### Frontend (if applicable)

- None. This iteration is backend + API + MCP only. The map's UI home (`/structure` → Tradable Map default view) is delivered later by **J-05**; this iteration delivers the canonical value + endpoint that J-05 will render. `Frontend Present: no` — UI pipeline stages (UI impact, UI test design, browser-QA, UX regression) are N/A-stubbed.

### New user-facing capability

An agent/operator (via REST or the MCP `tradability` tool) can request a symbol's tradable level map as of a session and receive ≤10 quality-scored, class-inherited price bands per the morning-markup basis — the distilled signal behind the raw 1,800-level noise. (No screen yet; surfaced in J-05.)

### New information displayed

None on-screen this iteration. The new canonical value (tradable-map bands: price range, side, quality score, member refs, round-number flag, inherited class) is served by `GET /research/tradability` for downstream journeys to render.

### New user actions

None (no UI this iteration).

### UI surface changes

None. Nav is frozen for Era 5B (no new entry).

### Product surface delta

The API + MCP surface gains one read-only capability (`/research/tradability` + `tradability` tool). No visible product screen changes yet; this is the backend foundation the `/structure` declutter (J-05) and cockpit overlay (J-06) will consume.

### Blueprint conformance

J-01 implements the **already-registered** Data-Contract row "Tradable level map — bands" (owner `app/research/tradability.py`, endpoint `GET /research/tradability?symbol=&as_of=`) drafted in `blueprint.md` at baseline. Its Information-Architecture home is `/structure` → **Tradable Map** (Structure section), delivered by J-05. No new surface, no nav change → no `blueprint.md` edit and no re-approval request needed.

### Data-contract additions

None new. The `Tradable level map — bands` value is already registered in `blueprint.md` (single computing module `app/research/tradability.py`; single serving endpoint `GET /research/tradability`; MCP `tradability` is a byte-identical read-only mirror, not a second computation). This iteration reads the existing `Raw levels + A/B/C zones` value from its registered canonical source (`levels.py` / `GET /research/levels`) verbatim — it introduces no second computation or second endpoint for any existing value. Band **class** remains a projection of the member zones' A/B/C (class stays owned by `levels.py`).

## OUT OF SCOPE

- No touch-event scanner / `setups.py` / case registry (J-02).
- No credentialed recording, `record_from_source` invocation, or dataset creation (J-03).
- No `structure_tape_map` strategy, no `edge_report.py` changes, no backtest-runner arming path (J-04).
- No `/structure` UI: no Tradable Map view, no raw-levels toggle, no Case Studies / Edge Report sections (J-05).
- No cockpit `PriceChart` changes, no band overlay, no confluence chip (J-06).
- No change to `app/research/levels.py` or its 5 bps / 20 bps parameters — frozen; consumed verbatim only.
- No 12-symbol panel config constant (that belongs to J-02's scanner; J-01 is driven by the request `symbol` param).
- No champion / promotion / sweep changes; no new nav entry; no change to `config_fingerprint`.

## DEFINITION OF DONE

- [ ] J-01 verified by the QA stage + goal-evaluator via live API + MCP assertions (backend-only iteration — browser-QA is N/A-stubbed; these are the same API/MCP probes that recorded J-01 `failing` at baseline): `GET /research/tradability?symbol=AAPL&as_of=<instant inside the 2026-06-22 session>` returns **≤10 bands total** (and ≤5 per side).
- [ ] In that AAPL 2026-06-22 map, a **resistance band containing both 300.48 and 302.07** (round-number 300 flagged) ranks in the **top 2** resistance bands by quality score.
- [ ] The map derives from **no bar newer than the 2026-06-18 close** (morning-markup as-of): assert no member/basis timestamp exceeds the 2026-06-18 session close.
- [ ] **Repeat-call determinism:** two identical requests return byte-identical JSON.
- [ ] **REST == MCP:** the `tradability` MCP proxy body is byte-for-byte equal to the REST response body for the same params.
- [ ] **Frozen levels:** `GET /research/levels?symbol=AAPL&as_of=...` output is byte-identical to before (raw computation unchanged).
- [ ] `config_fingerprint` == `4d665603569b9dbf` (live-confirmed; the new tradability constants are excluded from the hash and pinned by a fingerprint-stability test + a real-threshold counter-test).
- [ ] "Lens, not a second engine" confirmed by reviewer + auditor reading `tradability.py`: it contains no pivot/extreme detection and no second levels computation — it consumes `compute_levels` output only.
- [ ] Required-still-passing journey **J-07** remains green (full backend suite green, engine equivalence byte-identical, all era-1–5 surfaces intact).
- [ ] No anti-goal violation introduced (coherence-auditor + scan-report clean).
- [ ] Unit tests pass; no regressions.
- [ ] Dev handoff written at `docs/handoffs/goal-tradable_wall-iter-1-dev.md`.

## TESTING REQUIREMENTS

- **Journey verification (API + MCP; no DOM this iteration — browser-QA stage is N/A for `Frontend Present: no`, so QA + the goal-evaluator run these probes):** J-01 — assert the pinned AAPL 2026-06-22 acceptance against the live `GET /research/tradability` and the MCP `tradability` proxy (≤10 bands, 300.48–302.07 resistance band top-2 with round-number 300 flagged, morning-markup basis = 2026-06-18 close, byte-identical repeat call, REST==MCP byte-identity).
- **Unit/integration (must have tests asserting exact values):**
  - Band clustering + quality scoring on the AAPL fixture: exact band count, the top-2 resistance band's price range spanning 300.48–302.07, round-number flag true, inherited class present.
  - Morning-markup as-of resolution: a request inside the 2026-06-22 session resolves basis to the 2026-06-18 close; the 2026-06-19 holiday is skipped (basis is 06-18, not 06-19).
  - No-lookahead property: shifting the requested `as_of` earlier within the same session never pulls a bar past the prior-session close into the map (and never changes an already-emitted band from a strictly-later request in a lookahead-revealing way).
  - Determinism: identical requests produce byte-identical serialized output.
  - REST == MCP byte-identity for the same params.
  - `config_fingerprint` stability: new tradability constants excluded (fingerprint stays `4d665603569b9dbf`) PLUS a real-threshold counter-test proving a genuine tape/level threshold change still moves the fingerprint (the established paired-test precedent).
  - `levels.py` byte-identity: `compute_levels` output unchanged (existing equivalence coverage must stay green).
- **Error cases (must be rejected / handled honestly):**
  - Missing `symbol` → 422; malformed `as_of` → 422 (no silent "now" default).
  - Symbol with no bar series → explicit empty map (honest flag), never a fabricated band.
  - Symbol with series but no derivable bands at the resolved as-of → explicit empty bands, never fabricated.

## NOTES

- **Evaluator watch-item carried forward (for the later J-04 iter, not this one):** `apps/backend/app/research/edge_report.py` already exists as the era-3 champion-only CLI — J-04 must EXTEND it additively for the 3-way report, never fork a second edge computation. Not in scope here; noted so it is not lost.
- **Reference implementation pattern:** the `GET /research/levels` route (`app/research/routes.py`, `get_levels`) is the exact parse-ISO-once-then-return-verbatim pattern for the new `/research/tradability` route; the `levels` MCP tool (two required params) is the pattern for the `tradability` proxy.
- **As-of resolution note:** no session-calendar/prior-close helper exists in the codebase today; deriving the morning-markup basis from the stored daily bars (last completed daily bar strictly before the requested session) is the recommended holiday-safe, no-hardcoded-calendar approach — this is the correctness-bearing new logic that motivates full depth.
- **No assumption-ledger entry this iteration:** the goal is unambiguous on the required outcome (K≤5/side, ≤10 total, basis = prior completed session close, 300 flagged round-number). The exact quality-score weights / round-number rule are config-owned design freedom the goal explicitly grants (pre-registered constants), not a goal-interpretation ambiguity — so nothing is logged to `assumptions.md`.
- **No blueprint edit:** the `tradability` Data-Contract row and its `/structure` → Tradable Map home already exist from the baseline draft; nav is frozen (no re-approval file).
