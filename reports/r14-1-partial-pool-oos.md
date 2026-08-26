# r14.1 — corpus identity and partial-pool OOS correctness

**Repo** `dennisccy/tapeology` · **Branch** `goal/rapid-microscope` · **Base** `3a9044aa`
**Spec revision** r14.1 · **`config_fingerprint`** `08e471b10130e1e2` (unchanged)

**No real protected data was fetched, recorded, probed, released, assigned, exposed or evaluated.**
No universe registered, no candidate registered, no Tier-B re-screen, no sealed row read, no
append-only ledger rewritten, no threshold/geometry/panel/HMAC change.

---

## ROOT CAUSES

r14 fixed the preflight's own errors and, in doing so, built an architecture that could not run and
could still be laundered. Five root causes, each with the same shape — **a policy decision made at
the wrong boundary**:

| # | root cause | where the decision belonged |
|---|---|---|
| 1 | The reader decided membership by **session date**, so any withheld member poisoned the whole date. | Membership is a property of the CORPUS, precommitted; the reader should only be handed it. |
| 2 | `corpus_id` was a **free-text claim** the registrar explicitly did not parse. | Freshness is a fact about DATA — a bound universe, a provable recorder output, a creation instant. |
| 3 | Every inventory scanned the **globally visible store**. | A corpus id names one body of evidence, never "whatever dates happen to match". |
| 4 | Release accepted the dataset's identity **from the caller**. | The store owns symbol/date/checksum/schema_basis/created_utc. |
| 5 | The decoy emerged from **whichever release happened to be refused last**. | The partition is derivable before any release; deriving it later is a selection freedom. |

Plus one ordering defect: exposure was appended **after** the outcome read, so a crash between them
produced a window that had been read but recorded fresh.

---

## MIXED-DATE OOS FIX (A)

Seal assignment is per `(symbol, session_date)`, so a healthy 8-symbol date is normally MIXED.

**The corpus is now defined, not discovered.** `micro_corpus.eligible_oos_members` derives the
eligible set from — and only from — the registered universe rule, the HMAC not-selected status, the
frozen release plan's `releasable` class, the permanent incident exclusions, the deterministic
reserved decoy, and the store's already-verified metadata. Never from an observed outcome.

A sealed member is therefore a **non-member**, not an exclusion. It is not filtered out downstream;
its id never enters the manifest the reader is handed, so the reader is structurally incapable of
touching it. Per fold the reader:

- takes `membership ∩ window` (both narrowings applied before the read);
- proves every **expected** member has a current snapshot, else refuses;
- asserts each returned anchor is both inside the window and from a member (purge at both ends);
- reports `realized_breadth` — `n_observations`, `n_sessions`, `n_symbols`, and the actual symbol
  list — computed from the observations, never assumed from the panel;
- discloses the excluded class COUNTS (sealed / barred / decoy / rejected), never identities.

`WF_FOLD_MIN_OBSERVATIONS`, `WF_FOLD_MIN_SIGNAL_SESSIONS`, `WF_FOLD_MIN_SYMBOLS` are unchanged and
applied to that realized breadth.

**The required trap passes**: a real 6-released / 2-sealed date reads exactly 6, the 2 sealed ids
receive **zero** read calls (proven with a spy on `scout._cached_dataset_rows`), the date stays
usable, and breadth reports 6 rather than 8.

---

## CORPUS IDENTITY BINDING (B)

`register_fresh_corpus_era` is now structured and immutable, and `micro_corpus.register_bound_corpus_era`
proves the universe exists before the row is written:

```
corpus_id · universe_id · universe_registered_at · rule_commitment ·
vault_secret_commitment · expected_pair_count · freshness_boundary
```

Those seven are `CORPUS_ERA_FROZEN_FIELDS`. Re-registration is idempotent **only** when every one is
byte-identical; anything else raises `ConflictingCorpusEraError`. `provenance_note` survives as
free text and is inert — notes may say why, never what.

A genuine fresh OOS member must be provably: in the bound universe's registered pool · a genuine
recorder output (`schema_basis == RECORDER_SCHEMA_BASIS`) · created at or after the
`freshness_boundary` · not a legacy collision · not the reserved decoy · not incident-barred · not
still withheld. Sacrificial probe dates and screening-exposed dates are barred by the r14
`clean_oos_candidate_dates` predicate at date-rule time.

---

## ANTI-LAUNDERING PROOF

Four routes, each closed and each with a counter-test:

| route | what stops it |
|---|---|
| **relabel** — point a new `corpus_id` at exposed legacy data | membership requires `schema_basis == RECORDER_SCHEMA_BASIS`; a legacy dataset is a §7.2.2 collision and is neither a member nor releasable |
| **same-date sibling** — a legacy dataset sharing a date with a real member | same predicate, plus the `freshness_boundary` on `created_utc` |
| **cross-universe** — a member of another registered universe | the position must be in THIS universe's `expected_recording_pairs`, via the frozen plan |
| **re-point** — re-register a `corpus_id` against a different universe | `ConflictingCorpusEraError` |

The decisive counter-test (`test_the_corpus_relabel_attack_is_refused`) takes an exposed legacy
dataset sitting on a releasable pool pair, registers a brand-new corpus id, and attempts both a
membership read and a release. Both refuse.

---

## RELEASE DATASET IDENTITY (D)

`vault.release_unselected_dataset(dataset_store, …, dataset_id, universe_id, vault_secret)` is the
public/operator boundary. It takes **no** `symbol`, `session_date`, `content_checksum` or
`event_count` — a test asserts their absence from the signature — and derives each from
`DatasetStore.get`. Seven refusals, all before the append:

1. empty secret, or a secret not matching the universe's committed `vault_secret_commitment`;
2. unregistered universe;
3. dataset identity — genuine recorder output · created at/after the universe's registration ·
   a real member of the registered pool;
4. no committed release plan;
5. the plan does not mark this position releasable — one check covering the sealed path, the
   barred positions and the reserved decoy;
6. the dataset already carries any shard row (also stops a sealed member taking the shortcut);
7. §7.2.2's residual floor, re-checked against the state the release would produce.

Disclosure-incident lookup is case-normalized and universe-scoped.

---

## DECOY / RELEASE PLAN (E)

**`RELEASE_PLAN_RULE_V1`**, documented as r14.1 and hashed into the plan identity.
`build_release_plan` partitions the pool into four disjoint classes from the registered rule, the
HMAC and the incident ledger — and nothing else:

```
sealed_path     HMAC-SELECTED; only ever public via seal → assign → expose
barred          incident-disclosed; permanently no sealed/blind/OOS credit
reserved_decoy  the lowest decoy_rank among the remainder
releasable      everything left — THE bound OOS corpus's member set
```

`decoy_rank = HMAC-SHA256(secret, "rapid-microscope-decoy-r14.1:{universe}:{symbol}:{date}")` —
**domain-separated** from `compute_seal`'s own message, so a revealed decoy leaks nothing about any
other position's seal bit. §7.2.1(h)'s `sha256("rapid-microscope-tier-b-r10:" + ticker)` ranking is
the precedent.

`required_reserved_decoys` is derived, not chosen: with `P` pairs, `S` selected and `I` barred, the
floor `P − I − R > S` gives `R ≤ P − I − S − 1`, so the reserve is exactly **one** whenever
anything is sealed, and **zero** when nothing is.

A **hiding commitment** (`nonce ‖ canonical plan`) is persisted pre-release in a fifth hash chain
(`vault_release_plan_ledger.jsonl`); only class SIZES are served while the pool is unresolved.
A conflicting re-commit refuses.

**The reserve lifts exactly when nothing is hidden.** Without that, the frozen plan would have made
whole-pool release permanently unreachable — the decoy is never in `releasable`. The rule's own
purpose releases it, never an operator's judgment.

Proven: same universe + same secret ⇒ same decoy and the same final released set under **opposite**
release orders. (`plan_hash` deliberately differs across two separate universe *registrations*,
because it binds the nonced `rule_commitment` — determinism is a property within one registration.)

---

## EXPOSURE PRECOMMIT ORDER (F)

Order is now: validate direction/purpose · require the corpus baseline · resolve `membership ∩
window` · prove completeness · **append the exposure** · only then read a snapshot row.

- A spy asserts the exposure row already exists at the first `_cached_dataset_rows` call.
- A simulated crash inside `extract_anchors`, after the precommit, leaves the window burned — a
  later spec classifies it `historical_exposed_diagnostic`.
- A completeness refusal happens **before** the precommit, so a fold that never ran burns nothing.

That asymmetry is deliberate: a window wrongly marked exposed costs evidence; a window wrongly
marked fresh costs the scientific claim.

---

## OPERATOR PATH (G, H)

The `pairs != 80` check was unconditional, making 8 × 105 = 840 structurally impossible.

- **Starter tranche**: every original invariant retained and still enforced — `_is_starter()` gates
  the frozen 80-pair identity, and a starter date-rule that is not 80 pairs still refuses.
- **A later era**: same frozen 8-symbol panel (no Tier-B re-screen), any date rule ≥ 10 dates, the
  §7.6 concentration floors still binding, no exact-80 requirement.
- **Artifacts**: a later era writes to `reports/universe-<id>/`, so it cannot overwrite the
  starter's committed `acceptance.json`, `recording-runs.json` or TR-2 analysis.

Four new stages, **dry by default**, requiring an explicit `--commit`:

```
python -m scripts.j06_operator corpus-era   --universe-id ID --dates-file P --corpus-id C [--commit]
python -m scripts.j06_operator release-plan --universe-id ID --dates-file P              [--commit]
python -m scripts.j06_operator release      --universe-id ID --dates-file P              [--commit]
python -m scripts.j06_operator probe        --corpus-id C --probe-date D --probe-note T  [--commit]
```

**None was executed in this task.** A real campaign needs no Python-console ceremony.

---

## PILOT READINESS AUDIT (I)

Audited against goal.md's own stated mechanisms, not against the convenience of the current grid.

| pilot | verdict | why |
|---|---|---|
| **1. range-wall failed aggression** | **PARTIAL_PROXY_ONLY** → *r14.2:* **`PARKED_PENDING_OWNER_SPEC`** | The mechanism is a THREE-part conjunction: high aggression into the wall · collapsing impact efficiency · **opposite-side `refill_consistent` replenishment**. `failed_aggression_score = dominant_side_volume_share × flatness` covers the first two as one composite; the `refill_consistent` co-occurrence is genuinely unbuilt, and `scout.py`'s own frozen comment says so ("remains T-1 … never invented here"). The current request is a defensible proxy, not the study. |
| **2. delta divergence at level tests** | **FULL_MECHANISM_READY** *(r14.2: now CONTINUOUS-first — `price_extension_bps` × `delta_weakening_multiple`)* | `micro_features.divergence_at_level` implements Card 9.1 verbatim, and `scout._extract_divergence_anchors` supplies the dedicated PAIRED-touch path: consecutive touches τ1 < τ2 of the SAME band within one dataset, cumulative delta read off each touch's own snapshot row, `available_at = τ2`. Nothing is proxied. *(Mechanism-complete ≠ Mode-B-freezable: `sidedness` is still `None`.)* |
| **3. capitulation exhaustion** | **PARTIAL_PROXY_ONLY** → *r14.2:* **`PARKED_PENDING_OWNER_SPEC`** | The mechanism is a SEQUENCE — extreme **sell** aggression, *then* collapsing negative impact efficiency / replenishment — separating capitulation signals that snap back from those that do not. The request is a single `failed_aggression_score ≥ 0.7` threshold at a `capitulation` playbook signal: direction-agnostic (dominant-side share, not sell-specific), with no then-sequence and no replenishment term. |

**A gap shared by all three**: goal.md J-09 step 1 says *"Continuous mechanism-defined
representations first; any threshold variant from the bounded grid"*. All three requests are
threshold transforms; no continuous representation is registered. That ordering is part of the
predeclaration, not a stylistic preference.

**No candidate formula was changed.** The frozen spec does not unambiguously define the missing
plumbing for pilots 1 and 3 (§3 names the features; it does not define a two-feature co-occurrence
condition or an ordered event sequence), so building either would be invention, not implementation.

---

## TESTS

| suite | result |
|---|---|
| `tests/test_micro_r14_1_partial_pool_oos.py` (new) | **34 passed** |
| `tests/test_micro_r14_corpus_lifecycle.py` (updated) | **32 passed** (was 44; 12 retired — see below) |
| **full backend suite** | **3 679 passed · 8 skipped · 0 failed · 0 errors** (exit 0) |
| | baseline 3 657 / 8; delta is exactly **+34 new − 12 retired = +22**, so **no pre-existing test changed outcome** |
| `apps/frontend` `tsc --noEmit` | **exit 0** |

The r14 file's release section is **retired with a pointer**, not deleted silently: r14.1 replaced
the boundary it tested, and re-asserting the same properties against a retired signature would only
let the two copies drift. Every property it covered is re-asserted against the corrected boundary.

Coverage of the brief's own list: mixed 6+2 date reads 6 with 2 untouched · all-members-missing
snapshot fails closed · legacy same-date sibling excluded · corpus-relabel attack refused ·
conflicting corpus-era re-registration refused · dataset-id/pair mismatch refused · deterministic
decoy independent of order · release outside the frozen plan refused · selected member refused ·
incident-barred member refused · crash after precommit ⇒ later spec diagnostic · 105-date / 840-pair
operator preflight legal · starter 80-pair invariants unchanged · later-era artifacts isolated · no
sealed row read.

---

## REAL LEDGER INVARIANTS

Unchanged on disk: Scout ledger **18 rows** · vault shard ledger **21 rows, all `sealed`** (0
assigned, 0 exposed) · exposure registry **174 rows** · walk-forward ledger **7 rows**. All four
existing vault chains verify; the starter universe's rule is still `committed`, never revealed. The
fifth (release-plan) chain exists in code and has **no real rows** — no plan has been committed for
any real universe.

---

## VERIFICATION

> ### ⚠ CORRECTED BY r14.2 — read this first
>
> The proof below establishes **3 CONSTRUCTIBLE folds**, not 3 *sufficient* ones. 105 distinct
> session dates are the calendar minimum for `build_folds` to produce three folds under
> `DIAGNOSTIC_GEOMETRY`; whether any of them clears `WF_FOLD_MIN_OBSERVATIONS`(30),
> `WF_FOLD_MIN_SIGNAL_SESSIONS`(8) and `WF_FOLD_MIN_SYMBOLS`(2) depends on the OBSERVATIONS inside
> each test window and is unknowable from a date count. A sparse candidate yields three
> constructible folds and zero sufficient ones. **105 does NOT guarantee a walk-forward survivor is
> reachable.**
>
> One line of the proof below also overstated its own scope: the per-fold
> `WF_FOLD_MIN_SIGNAL_SESSIONS` assertion compares a **dataset-date** count against a floor that
> means **signal sessions** (sessions carrying qualifying observations). It reads as a sufficiency
> check and is not one. See `reports/r14-2-evidence-once.md` → *105 CONSTRUCTIBLE VS SUFFICIENT*,
> and the two hermetic tests (negative and positive) added there.

The claim the brief required before anything may be called recordable:

> **a 105-date synthetic universe with an actual HMAC mixed partition produces 3 walk-forward folds
> while every selected shard remains unread.**

Proven by `test_a_105_date_bound_corpus_produces_three_folds_with_every_selected_shard_unread`:

- 8 frozen panel symbols × 105 dates = **840 pairs**, partitioned by production `compute_seal`;
- the selected count falls in a genuine ~25 % band (asserted as a band, not a value, because it is a
  real draw), sealed members are spread across **>90** of the 105 dates, and every class sums to 840;
- every plan-releasable member is released; membership excludes every selected position and the
  decoy **by precommitment**;
- `mc.corpus_session_dates` yields **105** dates and `wf.build_folds` yields
  **`WF_MIN_SUFFICIENT_FOLDS` = 3 CONSTRUCTIBLE** folds covering 60 validation sessions
  *(r14.2: constructible — sufficiency is a separate, observation-dependent question)*;
- for each fold, and for each of its train/embargo/test windows, the resolved member ids are
  **disjoint from every sealed id**; each fold clears `WF_FOLD_MIN_SYMBOLS` on realized membership
  *(r14.2: the `WF_FOLD_MIN_SIGNAL_SESSIONS` assertion here counts DATASET dates, not sessions
  carrying qualifying observations — it is a membership-breadth check, never a sufficiency one)*;
- per-date membership is genuinely mixed (`min < 8`), so the fix is exercised, not bypassed;
- `run_tick_family_fold_request` on the bound corpus registers the **membership hash**, not a date
  list, and returns the excluded-class disclosure.

---

## REMAINING BLOCKERS

1. **Storage** — unresolved; operator decision (r14 spike: `PROVISION_STORAGE`).
2. **Tick retention before 2025-11-03** — unverified; needs the sacrificial probe.
3. **No Mode B rule is freezable** — all three pilots carry `sidedness: None`, and two are
   PARTIAL_PROXY_ONLY against their own stated mechanisms. Freezing a direction needs one Scout run
   on the exposed legacy corpus; treating a partial proxy as the full pilot needs an owner ruling.
4. **The `refill_consistent` co-occurrence and the capitulation sequence are unbuilt** — and the
   frozen spec does not define their plumbing unambiguously, so building them is a spec question
   first.
5. Paired bar backfill for AG/LYFT/WULF (1d+1h) and SPY (1h).

---

## NEXT OPERATOR ACT

Decide storage. Then the burned-date probe. Then an owner ruling on whether pilots 1 and 3 proceed
as declared partial proxies or wait for their full mechanisms.

**It is not safe to record**, and storage alone would not make it so: blockers 2, 3 and 4 are
scientific, not operational.
