# Project Configuration

Filled for **Tapeology** (iteration 1). Agents read this file to understand the stack,
conventions, and constraints. Keep edits surgical and additive.

---

## PROJECT GOAL

```
Goal document: docs/goal.md
```

The goal doc defines the vision, target users, success criteria, key capabilities, and
non-goals/anti-goals. All agents read it (and the approved coherence blueprint at
`runs/goal-session-i_will_be_rich/state/blueprint.md`) before starting any iteration.

---

## PROJECT

```
Name:        Tapeology
Description: Standalone real-time tape-reading system for US stocks — given one ticker, it
             watches simulated order flow and classifies the current tape state
             (price impact, not raw aggression). Phase 1 is in-memory and simulated.
Repository:  (local)
```

---

## STACK

```
Backend:
  Language:    Python 3.12
  Framework:   FastAPI (uvicorn ASGI), WebSocket + REST
  ORM/DB lib:  N/A (Phase 1 is in-memory; no database)
  Migrations:  N/A
  Test runner: pytest (with the anyio plugin for async API tests)
  Package mgr: uv (pip-compatible); venv at apps/backend/.venv/
  Venv/env:    apps/backend/.venv/

Frontend:
  Enabled:     yes
  Framework:   Next.js 15 (App Router)
  Language:    TypeScript
  Styling:     Tailwind CSS v3
  Package mgr: npm

Database:
  Type:        None (Phase 1 in-memory)
  Location:    N/A

Services:
  Backend URL:  http://localhost:8000  (QA harness uses a deterministic offset port, e.g. :8650)
  Frontend URL: http://localhost:3000  (QA harness offset, e.g. :3650)
  Health check: http://localhost:8000/health
```

The frontend reads the backend base URL from `NEXT_PUBLIC_API_URL` (the QA harness sets it;
`NEXT_PUBLIC_API_BASE` is an accepted alias), defaulting to `http://localhost:8000`. The
WebSocket URL is derived by swapping `http` → `ws`.

---

## DESIGN SYSTEM

```
Component library: none (hand-built panels; keep them clean and consistent)
Icon library:      none (text/Unicode glyphs only)

Visual style:      instrument-panel "tape cockpit" — clean, dense, legible at a glance
Color mode:        dark

Color palette (Tailwind tokens):
  Background:      slate-950 (#020617)
  Surface:         slate-900/60 panels, slate-800 borders
  Buy / positive:  emerald-400 / emerald-500   (green)
  Sell / negative: rose-400 / rose-500          (red)
  Absorption/unclear: amber-400 / amber-500     (amber)
  Text primary:    slate-200
  Text muted:      slate-400 / slate-500

Typography:
  Body:            system sans (Tailwind default stack)
  Numerics:        font-mono (system monospace) for ALL prices / sizes / ratios

Spacing:           Tailwind default 4px grid
Effects:           restrained — subtle borders, a confidence bar, status dot. No clutter.
Responsive:        single-column on narrow, 2-col md, 3-col lg panel grid.
```

**Color semantics are load-bearing and consistent everywhere:** green = buy-side / positive
impact, red = sell-side / negative impact, amber = absorption / unclear. No profitability
claim and nothing presented as trading advice anywhere in the UI.

---

## TEST COMMANDS

```
Backend tests:  cd apps/backend && .venv/bin/python -m pytest tests/ -v
Frontend build: cd apps/frontend && npm run build   (type-check + compile; no unit suite yet)
Frontend tests: N/A (user-facing behavior is covered by browser QA)
Migrations:     N/A
Lint:           N/A
```

---

## SERVICE START COMMANDS

The conventional framework scripts already match this layout (they use a deterministic
per-project offset port and wire `NEXT_PUBLIC_API_URL` from the backend port):

```
Start backend:  bash scripts/start-backend.sh    (uvicorn main:app --app-dir apps/backend)
Start frontend: bash scripts/start-frontend.sh   (npx next dev)
```

Backend entrypoint: `apps/backend/main.py` re-exports the app, so both `main:app` and
`app.main:app` resolve. Health endpoint: `GET /health`.

---

## PHASE SPECS

```
Phase spec directory:   docs/phases/
Phase spec naming:      <phase-id>.md   (goal mode: goal-<sid>-iter-<N>.md)
```

---

## ROADMAP

| Phase | Name | Status |
|-------|------|--------|
| iter-0 | Verify-only baseline + blueprint approval | ✅ Complete |
| iter-1 | Tape-cockpit walking skeleton, proven on SIM-BUYER (J-01/J-02/J-08) | ✅ Complete |
| iter-2+ | SIM-SELLER (J-03), absorption pair (J-04/J-05), unclear-chop (J-06), transitions (J-07), stop/re-watch (J-09) | Future |

---

## ARCHITECTURE PRINCIPLES

```
- Single source of truth: every tape state, confidence, and feature is computed exactly
  once in the engine (one immutable snapshot per tick). REST, WS, and the UI READ it —
  they never recompute spread, ratios, impacts, or confidence.
- Price impact, not raw aggression: directional states require real price progress on the
  matching side; high one-sided aggression with no price progress is absorption, not control.
- Provider-agnostic engine: the engine/API depend only on the provider interface
  (TradeEvent / QuoteEvent); swapping the simulator for a live feed touches neither.
- Deterministic engine: same ordered event stream (+ seed) ⇒ identical features/state/
  confidence. No wall-clock or randomness in classification (wall-clock only paces delivery).
- No magic numbers: every window/threshold/cutoff/confidence boundary lives in app/config.py;
  none inline in engine/classifier code.
- Honest uncertainty: weak/mixed/cold-start ⇒ unclear at low confidence; no fabricated data
  (unknown ticker ⇒ 400, not-watched read ⇒ 404 — never a synthesized snapshot).
- Frontend has no business logic — it renders engine values verbatim and calls the API only.
```

---

## DATA MODEL RULES

```
- Events are immutable frozen dataclasses; timestamps are LOGICAL seconds (floats), never
  wall-clock.
- The engine snapshot is a frozen dataclass; API responses are pure projections of it.
- No persistence in Phase 1 — all state is in process memory.
```

---

## GIT WORKFLOW

```
Branch naming:      goal/<session-id>  (goal mode)
PR title format:    goal(<sid>): iter <N> — <summary>
Main branch:        main
Never commit:
  - .env / .env.*        (except .env.example)
  - apps/backend/.venv/  (virtualenv)
  - node_modules/, .next/
  - __pycache__/, .pytest_cache/
```

---

## NOTES FOR AGENTS

```
- Reserved sim tickers: SIM-BUYER (live this iter), SIM-SELLER, SIM-BIDABS, SIM-ASKABS,
  SIM-CHOP (registered but not driven to their states yet — later iterations).
- SIM-BUYER resolves to buyer_control at confidence ~0.87 within ~3-4s of watching.
- The buyer_control rule already REQUIRES positive buy_price_impact and is covered by a
  negative guard test — do not relax it to an aggression-only shortcut.
```
