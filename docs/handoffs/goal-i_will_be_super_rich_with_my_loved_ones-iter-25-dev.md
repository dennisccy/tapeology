# goal-i_will_be_super_rich_with_my_loved_ones-iter-25 Dev Handoff

**Phase:** goal-i_will_be_super_rich_with_my_loved_ones-iter-25
**Date:** 2026-06-13
**Agent:** developer
**Status:** complete

## What Was Built

J-66 cue-discipline sweep — the last cue-layer journey. Three pieces:

1. **Comprehensive copy-lint test (the J-66 acceptance backstop)** — a new
   `apps/backend/tests/test_copy_discipline.py` that generalises the three seeded per-surface
   checks (stance / checklist / feed-basis) into an all-surface lint with three legs:
   - **(a) full taxonomy walk** — recursively walks every string leaf in the entire
     `GET /research/taxonomy` payload.
   - **(b) representative served copy** — verdict labels, checklist stance evidence (all four
     stances) + nearest-counterevidence, management-stance pending evidence, hint evidence (all
     four patterns) + baseline citation + unvalidated string, all six risk-flag measured-evidence
     sentences, the analytics + studies measurement-framing/captions, excursion absence copy, and
     the new sound-cue copy — built from the same backend owners the runtime uses.
   - **(c) frontend source scan** — quoted string literals + JSX text across
     `apps/frontend/components/**` + `apps/frontend/app/**` (comments + import lines stripped, since
     dev comments paraphrase the anti-goal vocabulary while describing the discipline).
   The **curated word-boundary lexicon** bans imperative trade *constructions* ("buy now", "you
   should …", "go long/short", "enter/exit the trade/position", "take-profit", "stop-loss"),
   predictions ("will rise/fall/break …", "about to", "price/target price"), and certainty/edge/
   profitability *claims* (guaranteed / edge / win-rate / profit) — the claim words are cleared by a
   **sentence-level negation marker** so the measurement-framing honesty copy ("not a profitability
   claim, an edge, a win rate, or a forecast") stays clean. It deliberately does NOT fire on factual
   side descriptors ("aggressive buy ratio", "Large sell print absorbed", `buyer_control`), the
   user's own action marks ("Mark entry", "entry-and-exit-marked"), or UI field instructions ("Enter
   a ticker symbol").
   - **The lint CAN fail:** 14 parametrised seeded-banned-phrase counter-tests (one+ per category)
     assert the lint fires; 14 legitimate-descriptive cases assert it does NOT false-positive (both
     failure directions checked).

2. **iter-24 reviewer NOTE fixed (feed-honesty consolidation, data-contract row 26):**
   `routes.py:1207/1232` no longer hardcode `data_feed = "sip"` for the reference / historical study
   kinds — both now read `registry.config.historical_feed` (the same key the one
   `data_feed_for_scenario` mapping exposes for the historical-replay path), so the create-time stamp
   equals the runner's later re-stamp by construction. Defaults unchanged (`historical_feed="sip"`)
   ⇒ byte-identical — **zero re-pins** (the pinned reference study still asserts `data_feed == "sip"`).
   A new test asserts the create-time stamp equals the one mapping's output for both reference and
   historical study kinds.

3. **Optional sound cue (capability 33's final item):**
   - **Backend:** new serving-only `sound_cue_cooldown_seconds` config key (default 3.0 s) with its
     rationale comment, excluded from `config_fingerprint`, plus a fingerprint-stability test + a
     real-threshold counter-test **in the same commit** (the `study_list_max`/`hint_log_max` pattern).
     New `SOUND_CUE_COPY` taxonomy block (toggle label, off-by-default/transition-only description,
     fired-indicator label, the reused "Descriptive only — not trading advice" register line); served
     additively as `taxonomy.sound_cue` with the config cooldown value (`taxonomy_payload` now accepts
     a config; the route passes `registry.config`).
   - **Frontend:** new `SoundCue.tsx` rendered in the thesis-strip cue area (the pre-registered
     cue-layer home). **Default OFF on every fresh load**, never persisted; fires a brief Web Audio
     beep ONLY on a verdict/stance TRANSITION (the served `cueKey` = verdict + active-stance value,
     read verbatim — the UI derives no stance), respects the served cooldown, and shows a visible
     fired-indicator pulse (browser-verifiable without audio hardware). All copy is taxonomy-owned.

## Files Changed

- `apps/backend/app/config.py` -- new serving-only `sound_cue_cooldown_seconds` key + its
  `config_fingerprint` exclusion (with rationale comment).
- `apps/backend/app/research/taxonomy.py` -- `SOUND_CUE_COPY` block; `taxonomy_payload(config=None)`
  now serves the additive `sound_cue` block (copy + config cooldown); `TYPE_CHECKING` Config import.
- `apps/backend/app/research/routes.py` -- reference/historical study `data_feed` now reads
  `registry.config.historical_feed` (was hardcoded `"sip"`); `/taxonomy` route passes the registry
  config.
- `apps/backend/tests/test_copy_discipline.py` -- NEW comprehensive J-66 copy-lint (taxonomy walk +
  served copy + frontend scan) + seeded-violation counter-tests + false-positive guards.
- `apps/backend/tests/test_research_api.py` -- new `test_taxonomy_serves_sound_cue_copy_and_config_cooldown_canary`.
- `apps/backend/tests/test_research_hints.py` -- new sound-cue fingerprint stability + counter pair.
- `apps/backend/tests/test_studies_api.py` -- new creation-stamp-equals-mapping tests (reference +
  historical kinds); `data_feed_for_scenario` import.
- `apps/frontend/components/SoundCue.tsx` -- NEW optional sound-cue toggle + fired-indicator.
- `apps/frontend/components/ThesisStrip.tsx` -- wire `SoundCue` into the active-thesis cue area;
  `cueKeyFor` helper (reads served verdict + active stance verbatim).
- `apps/frontend/lib/types.ts` -- `SoundCueTaxonomy` type + `sound_cue?` on `ResearchTaxonomy`.
- `apps/frontend/app/globals.css` -- `.sound-cue-pulse` keyframe for the fired-indicator.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -v`
Result: **848 passed, 1 skipped, 0 failed (exit 0)** — exceeds the ≥812 bar. Observer-equivalence
green; reference study pins held (zero re-pins); the copy-lint + counter-tests green; the
creation-stamp == mapping tests green; the sound-cue fingerprint stability + counter pair green.

Frontend type-check: `cd apps/frontend && node_modules/.bin/tsc --noEmit` → exit 0.

Live canary (iter-6 discipline — this iteration changes taxonomy copy): started uvicorn on a spare
port and confirmed `GET /research/taxonomy` serves the new `sound_cue` block live (cooldown 3.0,
register verbatim), then killed the process. No stray servers left.

## Known Issues

- **Sound playback is best-effort.** The Web Audio beep needs a prior user gesture in some browsers;
  if audio is blocked/unsupported the **visible fired-indicator still fires**, so transition-only +
  cooldown behaviour stays browser-verifiable without audio hardware (by design — the QA leg keys on
  the indicator, not the sound).
- **J-67 live-IEX pixel legs remain market-hours-gated** (next US open 15-06-2026 14:30 UTC+01:00) —
  not attempted this weekend; flagged for the J-68 backlog iteration (which also needs the J-12/J-14/
  J-15 market-hours legs). The gated leg stays documented, never faked.
- **Frontend build (`npm run build`) was intentionally NOT run** against the harness's shared `.next`
  (iter-2/iter-18 lesson); `tsc --noEmit` was used for the type-check instead.
- The OFF-default sound toggle is rendered in the **active** thesis strip (where a verdict/stance
  exists to transition on); the idle declare line stays untouched (J-68 strip-idle clause — nothing
  else moves, and the idle line keeps costing no taxonomy request).
