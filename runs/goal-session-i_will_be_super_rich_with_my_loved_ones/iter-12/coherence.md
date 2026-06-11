**Verdict:** COHERENCE-PASS

## Iteration 12 — Journal list surface + restart honesty (J-51)

Audited against blueprint `runs/goal-session-i_will_be_super_rich_with_my_loved_ones/state/blueprint.md`
(status: APPROVED). Iteration diff: `git diff 8faefece5491c769b89c1672cb5e1e20813b33fe` plus
untracked new files. No UI surface map was present; surfaces derived from the diff and git status.

---

### Part A — Data Contract check

**Row 21 (Journal rows + analytics aggregates)** — the journal-rows half ships this iteration.

- Single owner confirmed. The new `journal_row()` function in
  `apps/backend/app/research/journal_rows.py` is the **one** projection builder for compact list rows.
  It is the only caller of the persisted `ThesisRecord` fields for this purpose; no second function
  or second code path computes the same projection.
- Single serving path confirmed. `GET /research/journal` (implemented in
  `apps/backend/app/research/routes.py:228-305`) is the only endpoint that serves journal rows; the
  frontend `fetchJournal()` in `apps/frontend/lib/api.ts:510-542` calls exactly this endpoint and no
  other.
- No client-side recomputation. `JournalTable.tsx` renders all fields verbatim (status, resolution,
  reason, stamps). The only presentation transforms are the shared `formatDateDMY` date formatter and
  taxonomy-owned display labels read from `GET /research/taxonomy` — both are re-format-only, not a
  second computation. No violation.
- `resolution` is derived inside `journal_row()` as `thesis.status if is_terminal else None` — this
  is a pure projection of the already-persisted `status` field, not an independent computation.
  Consistent with the blueprint note "a resolution IS the terminal status." No violation.
- The `config_fingerprint` exclusion for `journal_list_default_limit` and `journal_list_max_limit`
  is documented in `apps/backend/app/config.py:427-441` with the correct rationale (serving-only
  values cannot affect persisted research values) and they are added to the `excluded` set in
  `config_fingerprint()`. Blueprint row 21 additive note references this. No violation.

**Row 24 (Taxonomies + research display copy)** — additive: `STATUSES` and `RESOLUTIONS` dicts
added to `apps/backend/app/research/taxonomy.py`, exposed via `GET /research/taxonomy`. The frontend
reads them from that single endpoint; no labels are hardcoded in any component. No violation.

**Rows 15–19** — none recomputed or re-served by any new path in this iteration. The diff touches
only the list endpoint, the row-projection module, and the filter bar. No violation.

**New displayed values not in the Data Contract at the start of this iteration:**
All values displayed on `/journal` (declared date, ticker, bound source, data feed, setup, direction,
status/resolution with reason, entry/exit-mark presence) are registered reads of already-persisted
fields from row 21 (journal-rows half) as extended in the blueprint's iter-12 additive note. No
genuinely new concept is introduced outside the contract.

**Part A result: no violations.**

---

### Part B — Information Architecture check

**New route: `/journal`**
- Blueprint canonical home: `Journal /journal` section (feature/journey table rows for J-51,
  J-55–J-57 home listed as `/journal` → `/journal/[id]`). The new page lives exactly at `/journal`.
  No parallel shell. No duplicate home.
- Navigation path: `apps/frontend/components/NavBar.tsx` adds a persistent top-bar `NavBar`
  component mounted in `apps/frontend/app/layout.tsx` (layout-level, present on every page). The
  NavBar contains an explicit `Link` to `href="/journal"` with `enabled: true`. The `/journal` route
  is therefore reachable in **1 click** from any page. Requirement of ≤2 clicks satisfied.
- No dead link for Studies: the `Studies` entry is listed in the NavBar but rendered as a disabled
  `<span aria-disabled="true">` (not a `<Link>`), consistent with the blueprint's build-order note
  ("Studies entry lands together with `/studies` page — the approved skeleton must never carry a dead
  link"). This is the documented and approved behavior. No violation.
- The blueprint IA skeleton (Cockpit · Journal · Studies) is now partially live in precisely the form
  the iter-12 build-out note describes. No skeleton deviation.

**Existing routes: `/` (Cockpit)**
The `NavBar` is inserted above the cockpit body via `layout.tsx`. No cockpit route or component was
moved or replaced. The cockpit remains at `/` and is reachable in 1 click. No violation.

**Part B result: no violations.**

---

### Part C — Advisory observations

- The `JournalTable` component renders a `▤` character (U+25A4) as a decorative icon in the empty
  state (`apps/frontend/components/JournalTable.tsx:58`). The risk-flag coherence cleanup (replacing
  the `⚠` emoji prefix with a class-based left accent rule in `ThesisStrip.tsx`) was the spec-mandated
  change; this `▤` character in JournalTable is a different location and was introduced in the same
  iteration. It is a unicode box-drawing character rather than an emoji, so it does not strictly
  violate the spec's emoji prohibition, but it is a mild inconsistency with the text/class-based
  design system principle. Advisory only. **WARN.**

No other advisory issues.

---

### Summary

| Check | Result |
|---|---|
| Part A: Data Contract (journal rows via single owner + single endpoint) | PASS |
| Part A: No second computation of any registered value | PASS |
| Part A: No client-side recomputation of contract values | PASS |
| Part A: config_fingerprint exclusion documented correctly | PASS |
| Part B: `/journal` reachable from persistent nav in ≤2 clicks | PASS (1 click) |
| Part B: No parallel shell or duplicate home | PASS |
| Part B: Studies disabled (no dead link) per approved build-order note | PASS |
| Part C: `▤` icon in JournalTable empty state | WARN (advisory) |

**No objective violations in Part A or Part B. One advisory note in Part C. Verdict: COHERENCE-PASS.**
