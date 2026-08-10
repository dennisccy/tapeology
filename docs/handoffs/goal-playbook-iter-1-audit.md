# goal-playbook-iter-1 Audit Report

**Date:** 2026-08-10
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

J-01's phase goal is genuinely achieved: I re-derived the canonical signal by hand against the
code (not the handoff), re-ran the full suite myself, probed the live route with hostile inputs,
and drove `compute_playbook` end-to-end through a real `BarStore` — the record shape, signature
recipe, store discipline and lookahead law all hold. One IMPORTANT honesty defect was found and
fixed during this audit: the 5m opening-range fallback sliced positionally, so a session whose
early 5m bars are missing was served a *fabricated* opening range (and a signal derived from it)
disclosed exactly like a genuine one; it now fails closed to the already-wired honest absence, with
a regression test. Remaining items are documented gaps and owner rulings — none of them touch the
record shape, signature recipe or store discipline that J-02 through J-09 build on top of.

---

## 2. Findings

### Backend Findings

**B1 — IMPORTANT (fixed): the 5m opening-range fallback built an "opening range" from bars outside
the opening window and served it as genuine**

`apps/backend/app/research/desk_playbook_features.py:123` (pre-fix:
`first_bars = session_5m[:five_min_bars_needed]`).

The 1m basis correctly filtered to the ET 09:30–09:45 epoch window
(`desk_playbook_features.py:106`), but the 5m fallback took the first three bars of the session
*positionally*, whatever their timestamps. Spec §2 primitive 2 defines the opening range "over ET
09:30–09:45" for **both** bases; §0's fail-closed discipline and §3.1's edge case ("No 1m and no 5m
OR ⇒ silent symbol-session (disclosed absence)") require the null, and `compute_playbook`
(`desk_playbook.py:364-374`) already had that absence row wired.

Failure scenario — reproduced end-to-end before the fix, via `compute_playbook` over a real
`BarStore`, with a member (`GAP`) whose 5m series is missing its 09:30 and 09:35 bars and which has
no 1m series at all:

```
SIGNAL GAP open_high_break basis= 5m or= 99.8 100.9 bars_used= 3
             slots_to_break= 3 trigger_ts= 2026-06-22T13:55:00.000000Z
ABSENCES: []
```

That "opening range" is the 09:40 / 09:45 / 09:50 bars, disclosed as `opening_range_basis: "5m"`,
`or_bars_used: 3` — indistinguishable from a real one — with `slots_to_break: 3` naming the 09:55
bar as the session's 4th five-minute slot. No absence, no diagnostic. This is a fabricated value
where the honest answer is an absence, and it would have propagated into every J-02 measurement,
J-07 back-scan row and J-08 evidence cell built on that record.

**Fix applied.** Both bases now read the same epoch window
(`first_bars = [bar for bar in session_5m if bar.epoch < window_end][:five_min_bars_needed]`) —
one behavioural line at the single choke point, no new rule, no new threshold. Post-fix the same
end-to-end fixture yields:

```
ABSENCES: [{'symbol': 'GAP', 'reason': 'no opening range could be built -- neither 1m nor
            5m bars cover the first 15 minutes of the session'}]
```

…while the legitimate 5m-degrade member (`DEG`: thin 1m series, complete 5m opening window) still
fires unchanged with `basis= 5m or= 100.0 101.0`. Regression test added at
`apps/backend/tests/test_desk_playbook_features.py::test_opening_range_5m_fallback_never_builds_from_bars_outside_the_opening_window`.
Verification is cited in §4.

**B2 — GAP: spec §4's `halted_formation` policy is entirely unimplemented**

`docs/playbook-detector-spec.md:340-342` makes it binding on every detector: "a timestamp
discontinuity > 5 minutes inside a formation window voids that formation (`halted_formation`
diagnostic, ADAPTATION)". `grep -rn "halted_formation"` matches only the spec doc and iter-0's
diff — nothing under `apps/`.

Residual consequence after B1's fix: slots are positional by design
(`desk_playbook_features.py:66-87` returns a list whose index *is* the slot;
`desk_playbook_detect.py:207` derives `first_eligible_slot = or_minutes // 5`). So (a) a session
missing 5m bars *after* the opening range still mis-numbers `slots_to_break` and the RVOL baseline
slots, and (b) a symbol whose 1m opening range is buildable while its 5m slots 0–2 are absent takes
`first_eligible_slot = 3` past genuinely eligible trigger bars. The phase spec's IN SCOPE, DoD and
TC-1..TC-16 do not require §4, so this is not a scope failure — but it must land before J-07's
back-scan runs over real recorded sessions.

**B3 — GAP: `PLAYBOOK_OR_MIN_1M_BARS = 10` is not a row in the spec's self-declared "COMPLETE
tunable surface"**

`apps/backend/app/research/desk_playbook.py:94`. The value comes from spec §2 primitive 2's prose
("fewer than 10 of the 15 one-minute bars on file ⇒ fall back"), so the threshold *does* pre-exist
the code that uses it and the anti-goal is not breached; it is §1's table that is incomplete.
Naming it (rather than inlining the literal) is the right call — it flows through
`playbook_parameters()` at `:215` and into the signature like every other threshold. Already
self-disclosed by dev and by the reviewer. Needs an owner ruling on whether §1 gains the row.

**B4 — GAP: the `principles` mapping is an undisclosed interpretation of unquantified spec prose**

`apps/backend/app/research/desk_playbook_detect.py:276`:
`principles = ["P4"] if spike_verdict == "constructive" else []`.

Spec §3.1 says only "Principles: P4 when pre-break pullbacks were shallow and dry, else
structural-only" — no mechanical definition. The code adopts §0's `constructive` discriminator
("approach RVOLs non-decreasing and none ≥ SURGE") as the proxy. This is defensible (it invents no
threshold and reuses a discriminator the spec already defines, whose own gloss is "steady
climb/base"), but it is nonetheless a detector rule that does not exist in the spec, which T-1 and
the "no rule outside the spec" anti-goal say to record and surface for an owner ruling rather than
settle in code. Neither the dev handoff nor the review flags it.

I was genuinely unsure between GAP and IMPORTANT here. It gates nothing, cannot be swept, and its
worst case is a mislabelled disclosure — so GAP — but it should be ruled on before J-08 groups
evidence by principle.

**B5 — GAP: `attempt_count` silently excludes the opening-range bars and is structurally always 0
for a slot-3 trigger**

`apps/backend/app/research/desk_playbook_detect.py:266` scans
`session_bars[first_eligible_slot:trigger_idx]`. Spec §0 defines it as "pre-trigger zone touches of
`[T − NEAR_EXTREME·MBR, T]` with the re-arm rule" — slots 0–2 are pre-trigger. Excluding them is
defensible (they define the level, so they touch the zone by construction), but it is an
undocumented narrowing, and for any trigger at the first eligible slot the slice is `[3:3]` — empty.
The canonical fixture's `attempt_count: 0` is therefore structural, not observed. Disclosure only,
never a gate.

**B6 — OBSERVATION: `entry_kind` inverts the measurement rail's own tie convention**

`desk_playbook_detect.py:234` / `:239` label a trigger bar opening *exactly* at `T` as `gap_open`;
`desk_forward.py:723` puts the same tie on the level side (`edge`). Confirmed live: a fixture with
`trigger_bar.open == trigger_price` returns `entry_kind: "gap_open"`, `entry: 101.0`. No arithmetic
consequence — `_measure_from` only echoes `entry_kind` into its output (`desk_forward.py:551`) and
never reads it — and spec §0's wording ("near side" / "beyond") does not cover equality. Worth
aligning when J-02 wires the rail.

**B7 — OBSERVATION: `or_width_mbr` divides by MBR with no local guard**

`desk_playbook_detect.py:292`. Unreachable through `compute_playbook`, which records an absence when
`baseline["mbr"] == 0.0` (`desk_playbook.py:348`), and unreachable via the narrowness gate for any
positive width; only a degenerate direct call with `width == 0 and mbr == 0` raises
`ZeroDivisionError`. `_relative_strength_strong` guards the same case explicitly at `:99`, so the
asymmetry is worth closing before J-04 adds detectors that call in directly.

**B8 — OBSERVATION: targeted reads swallow integrity errors while the bulk read surfaces them**

`desk_playbook.py:490` (`get`) and `:505` (`_records_for_date`) return `None` / skip on
`PlaybookIntegrityError`, so `?id=` and `?date=` render a corrupt record indistinguishable from an
absent one (and `versions` undercounts), while `GET /research/desk/playbook` with no query surfaces
it in `integrity_errors`. I checked this against the precedents before judging it: `ForwardStore.get`
(`desk_forward.py`, whose docstring states exactly this contract and the reasoning) and
`ScreenStore._records_for_date` (`desk_screen.py:923-940`) do the identical thing. Precedent-faithful,
not a new hole — recorded so a future honesty pass fixes all three together rather than one.

### Frontend Findings

None. `git status --porcelain apps/frontend` is empty; no UI surface exists for this iteration by
design (Frontend Present: no).

### Test Findings

**T1 — GAP: TC-4 and TC-5 are verified at the piece level, never as the composition their text
states**

Both TCs are written as "when `compute_playbook(session_date)` runs".
`test_desk_playbook_features.py::test_opening_range_degrades_to_5m_basis_below_the_1m_floor` tests
the primitive in isolation; `test_desk_playbook_detect.py::test_5m_basis_opening_range_still_fires_with_the_basis_disclosed`
and `::test_ambiguous_outside_bar_fires_no_signal_and_records_a_diagnostic` hand-build the
`or_result` dict and never touch the store-backed walk. The QA report's TC-04 row cites the
features-level test, which does not execute what TC-4 asserts.

I executed the composition myself through a real `BarStore` and both hold: a thin-1m/complete-5m
member produced `SIGNAL DEG open_high_break basis= 5m ... bars_used= 3`, and the both-sides-break
member produced `DIAGNOSTICS: [{'symbol': 'AMB', 'diagnostic': 'ambiguous_outside_bar', 'at_utc':
'2026-06-22T13:45:00.000000Z'}]` with no signal. Behaviour is correct; the regression coverage is
what is missing.

**T2 — GAP: TC-14 (the J-10 golden replay) was executed by nobody**

The DoD's second item names deterministic replay of
`runs/goal-session-playbook/journey-scripts/J-10.json` as the verification method. The dev handoff
defers it to the browser-qa-agent; the QA report's TC-14 row reads "DEFERRED to browser-qa-agent …
N/A"; `reports/phase-goal-playbook-iter-1-ui-test-results.md` records "**Browser QA Verdict:**
SKIPPED — Backend-only phase (Frontend Present: no). No browser tests executed." Nobody ran it, and
no server is listening on :3301/:8301 to replay it against now.

I verified the structural preconditions instead: zero diff under `apps/frontend`; the
`desk_routes.py` diff is +75 lines, every one inside a single new block (one import, one
`get_playbook_store` dependency, one `_playbook_meta_only` projection, one route) with no existing
handler touched; the app imports cleanly and the whole suite's `TestClient` traffic passes;
`/research/desk/playbook` collides with no existing path. A J-10 regression is structurally
implausible — but *implausible* is not *replayed*. J-10's status for this iteration is honestly
`unknown-by-replay`, not `verified`. QA's "Test coverage: 16/16 TCs addressed" overstates it;
15 were executed.

**T3 — GAP: the detector's populated-SPY branches remain untested (carried forward)**

Filed by the reviewer as MINOR at `desk_playbook_detect.py:119` and disclosed in the dev handoff's
Known Issues. Every fixture in `test_desk_playbook_detect.py` passes `index_bars=[]`, so
`_market_block`'s supportive/against/neutral branches and every `relative_strength_strong=True`
path execute in zero tests; only the "no SPY bars" branch ever runs. `market_context` itself is
unit-tested (`test_desk_playbook_features.py:283`) and I hand-traced the detector-side arithmetic
against spec §0 and found it correct. Unchanged by this audit — the right fix is one detector-level
fixture with a populated SPY series, and it belongs with J-02's own work.

**T4 — OBSERVATION: the review report misdiagnoses a pytest flag interaction as an environment bug**

`reports/reviews/goal-playbook-iter-1-review.md:12-14` claims pytest's final summary line "is
silently suppressed by an unrelated, pre-existing env/pytest-9.1.1 quirk reproduced even on an
isolated single-file run". It is not a quirk: `apps/backend/pyproject.toml:9` sets
`addopts = "-q"`, so an additional `-q` on the command line takes verbosity to −2 and drops the
footer, while the dev/QA command (`-v`, net default verbosity) prints it normally. I reproduced
both halves — a single-file run at default verbosity prints `8 passed in 0.09s`, my own explicit
`-q` full-suite run ends at the warnings-summary link with no footer. Harmless to this phase (the
reviewer's junit-derived numbers match mine exactly), but it would mislead a future agent into
distrusting this suite's own output.

---

## 3. Domain Assessment

The core domain logic is sound, and I verified it by re-deriving it rather than reading about it.

**Lookahead law (spec §0) holds.** The only two gates are the narrowness gate, which reads the
opening-range window's bars alone (`desk_playbook_detect.py:204`), and the strict price-crossing at
bar `t` (`:211-213`). Every other bar-`t` and post-`t` quantity — `rvol_trigger_bar`,
`session_bar_count`, `bars_to_close` — is disclosure-only, exactly as §0 permits and requires. The
market block reads index bars strictly before the trigger epoch (`:133-137`,
`desk_playbook_features.py:281`), `_relative_strength_strong` slices `session_bars[:trigger_idx]`
(`:102`), and `spiky_approach` reads bar `trigger_idx - 1` (`:256-260`). Baselines are prior
sessions only (`desk_playbook_features.py:141`). The generic property test is real, not decorative:
it asserts truncation-invariance of the core detection fields and byte-identity of the *whole*
signal under post-trigger mutation, and it is structured so J-04/J-05/J-06 extend
`_LOOKAHEAD_FIXTURES` without touching the assertion bodies.

**The canonical signal is arithmetically correct.** I hand-computed all fifteen top-level fields and
every nested disclosure from the fixture bars against spec §0/§3.1 — trigger at slot 3,
`trigger_price 101.0`, `entry max(100.8, 101.0) = 101.0` with `entry_kind "level"`,
`invalidation 100.0 − 0.30·1.0 = 99.7`, `or_width_mbr 1.0`, approach RVOLs `[0.5, 0.5, 0.5]` →
`constructive`, `bars_to_close 2` — and every one matches. The mirror short side is
sign-symmetric and independently correct (`entry min(100.2, 100.0) = 100.0`,
`invalidation 101.0 + 0.30·1.0 = 101.3`). Break strictness is strict on both sides; the ambiguous
outside bar returns before any side is chosen, so "neither side previously broken" holds by
construction.

**The pre-registration machinery is real.** All forty §1 constants are transcribed at their spec
values (I checked every row of the table against `desk_playbook.py:81-138`), and every one flows
through `playbook_parameters()` into `compute_playbook_input_signature`. The monkeypatch test proves
liveness genuinely — `playbook_parameters()` reads module globals at call time, so patching
`PLAYBOOK_NARROW_OR_MAX_MBR` moves both the served blob and the key, and the recompute mints a new
version instead of raising. `PLAYBOOK_SETUPS` deliberately declares only the two ids whose detectors
exist, which is the honest choice: J-04 extending the tuple re-keys future records rather than
back-claiming a compute that never happened.

**Store discipline is genuine, not decorative.** The id is a pure function of the 2-pin key; every
load verifies a whole-record checksum; a duplicate key raises with the original file byte-identical
(the test asserts the file's SHA-256 before and after); a file present at the key's path but failing
verification triggers the refuse-to-overwrite branch rather than a silent replace; and there is no
`update`/`delete` method, asserted structurally. The route takes no store/manager dependency at all,
so it is incapable of triggering a compute on a GET.

**The one design decision I want to call out as genuinely good:** `desk_playbook_detect.py` and
`desk_playbook_features.py` hold no constants — every threshold arrives as `params`, the caller's
already-built `playbook_parameters()` dict. That makes "the recorded parameters blob matches what
the detector actually used" true by construction rather than by discipline, and it keeps the import
graph acyclic. It removes a whole class of silent drift from J-02 through J-09.

**The weak seam** is that everything is positional-index-based (slots), which is exactly right on a
complete session and silently wrong on a gapped one. B1 was the acute form of that and is fixed;
B2 is the residual, and spec §4 already prescribes the cure.

---

## 4. Fixes Applied During This Audit

| # | Severity | File | Change |
|---|----------|------|--------|
| 1 | Important | `apps/backend/app/research/desk_playbook_features.py` | `opening_range`'s 5m fallback now filters to the same `09:30 .. 09:30+or_minutes` epoch window the 1m basis already used, instead of slicing `session_5m[:3]` positionally — a gapped session is now the honest absence the caller already had wired, not a fabricated opening range. One behavioural line + docstring stating why. |
| 2 | Important | `apps/backend/tests/test_desk_playbook_features.py` | Added `test_opening_range_5m_fallback_never_builds_from_bars_outside_the_opening_window` — a session whose 5m series starts at 09:40 must yield `None`, never a `basis: "5m"` range built from 09:40/09:45/09:50. |
| 3 | n/a | `docs/handoffs/goal-playbook-iter-1-dev.md` | Amended the two statements fix 1 invalidated (the `opening_range` description and the features test count), marked as audit amendments. |

**Verification of the fix (all commands run with the pipeline's isolated `TMPDIR`):**

- `cd apps/backend && .venv/bin/python -m pytest tests/test_desk_playbook_features.py::test_opening_range_5m_fallback_never_builds_from_bars_outside_the_opening_window -q` → `.  [100%]` (the new test fails on the pre-fix code and passes on the fixed code).
- `cd apps/backend && .venv/bin/python -m pytest tests/test_desk_playbook_features.py tests/test_desk_playbook_detect.py tests/test_desk_playbook.py -q` → collected **43**, failures **0**, errors **0**, skipped **0**.
- End-to-end re-run of `compute_playbook` through a real `BarStore`: the gapped member now yields
  `ABSENCES: [{'symbol': 'GAP', 'reason': 'no opening range could be built -- neither 1m nor 5m bars cover the first 15 minutes of the session'}]`, and the legitimate degrade member still fires
  `SIGNAL DEG open_high_break basis= 5m or= 100.0 101.0` — no behaviour change to the good path.
- Full backend suite after the fix (junit XML, exit 0): **collected 1977, passed 1969, failed 0,
  errors 0, skipped 8** — exactly the pre-audit 1968/8 plus my one regression test, zero
  regressions. `Config().config_fingerprint()` → `08e471b10130e1e2`, unchanged.
- Diff discipline re-checked: the only files I touched are
  `desk_playbook_features.py`, `test_desk_playbook_features.py` and the dev handoff.
  `git status --porcelain` over `desk_forward.py`, `desk_screen*.py`, `setups.py`, `bars.py`,
  `levels.py`, `app/config.py`, `app/mcp/__init__.py` and `apps/frontend` is **empty**.
  No new finding is introduced: the fix removes a value rather than adding one, and its only new
  outcome is an honest absence on a path that previously fabricated data.

**Independent verification of the pre-existing claims (not taken from the handoffs):**

| Claim | How I checked it | Result |
|---|---|---|
| TC-13 suite floor | full suite, junit XML | 1976 collected / **1968 passed** / 8 skipped / 0 failed (pre-audit) |
| TC-13 fingerprint | `Config().config_fingerprint()` | `08e471b10130e1e2` |
| TC-13 frozen-file diffs | `git status --porcelain` per file | zero on all seven protected files + `apps/frontend` |
| TC-1 honest-empty | live `TestClient` GET | `200 {"playbooks":[],"latest":null,"integrity_errors":[]}` |
| TC-12 route shapes | live GETs incl. `?id=`/`?date=`/both | `200` / `200` / `422` as specified |
| Route hardening (not spec'd) | `?id=../../../../etc/passwd`, `?id=/etc/passwd`, `?date=../../..`, `?date=*`, `?date=a/../../b` | all honest `200` with `null`; no traversal, no 500 |
| TC-4 / TC-5 composition | `compute_playbook` over a real `BarStore` | both hold (see T1) |
| TC-2 arithmetic | hand-derived every field from the fixture bars | matches |

---

## 5. Recommended Next Step

**Proceed to J-02.** The signal contract, signature recipe and store discipline that J-02 through
J-09 depend on are correct and now honest on gapped sessions. Carry the following forward rather
than re-opening this iteration:

1. **Owner rulings (B3, B4)** — whether spec §1 gains the `PLAYBOOK_OR_MIN_1M_BARS` row, and what
   the mechanical definition of §3.1's P4 condition is. Both are spec-completeness decisions, not
   code defects, and both should be settled in `docs/playbook-detector-spec.md` before J-08 groups
   evidence by principle.
2. **Spec §4's `halted_formation` (B2)** — must land before J-07's back-scan touches real recorded
   sessions, together with the positional-slot hardening it implies.
3. **Test debt to close inside J-02's own cycle (T1, T3)** — one `compute_playbook`-level fixture
   each for the 5m-basis degrade and the ambiguous outside bar, and one detector-level fixture with
   a populated SPY series exercising a non-null `direction` and `relative_strength_strong: true`.
4. **J-10 (T2)** — replay `journey-scripts/J-10.json` at the start of the next iteration that
   brings a server up. It should be recorded as `unknown-by-replay` for iter-1, not `passing`:
   nothing indicates a regression and the frontend diff is provably empty, but no replay was run
   and the honest status is the one the evidence supports.
