# Goal Session i_will_be_super_rich — Lessons Learned

Append-only ledger of takeaways from prior iterations. The goal-evaluator
appends one entry per iteration; the goal-decomposer reads this file before
planning each iteration to avoid repeating known pitfalls.

Each entry should be 1-3 sentences capturing a non-obvious lesson — surprising
failures, regression triggers, or decisions that worked well. Avoid
restating the verdict (the evaluator-log.md already does that).

---

## iter-0 — 2026-06-04T00:20:39Z

**Verdict:** CONTINUE (baseline)
**Lesson:** Browser QA found that switching tickers via the **Watch** button does NOT stop the
previous backend watch — only the explicit **Stop** button tears a watch down, so re-submitting
SIM-BUYER→SIM-SELLER→… leaves every prior engine instance alive (each `…/state` still 200). Harmless
for the in-memory sim, but with the live provider this becomes a **real vendor WebSocket/connection
leak** every time a user switches symbols without pressing Stop.
**Applies to:** any iter wiring the live provider / watch lifecycle (J-12 live, J-15 stale-recover,
and the J-10 data-source selector) — make a new Watch (or a source/symbol switch) implicitly
`DELETE` the prior watch and close its socket.

## iter-1 — 2026-06-04T09:39:35Z

**Verdict:** CONTINUE
**Lesson:** A latent credential-name mismatch is waiting to break the first real-data wiring: the
stale `apps/backend/.env` uses `ALPACA_SECRET_KEY`, but the new adapter (`app/providers/adapters/alpaca.py`)
reads `ALPACA_API_SECRET` — and nothing loads `.env` at all (no dotenv loader; `start-backend.sh`
doesn't source it). It was harmless this iteration (verification was credentials-absent, so the gate
*should* report unavailable), but the moment J-11/J-12 add real creds, `real_data_available()` will
wrongly return False with valid keys present unless the env names are aligned to the adapter's
(`ALPACA_API_KEY` / `ALPACA_API_SECRET`) AND a loader/export is added.
**Applies to:** any iter wiring real Alpaca credentials or a real provider (J-11 historical, J-12 live,
J-13 symbol search) — align env-var names to `adapters/alpaca.py` and add a dotenv loader/export before
expecting the creds-present branch to work. Also: J-11+ "real fetch" needs a credentialed verification
path (gated run or a recorded real-vendor fixture — never synthesized data, per the no-fabrication
anti-goal); plan it before building.
