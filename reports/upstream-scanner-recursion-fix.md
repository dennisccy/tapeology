# Handoff: goal-mode secret-scan recursion blocks GOAL_ACHIEVED

**For:** a Claude session working in the **`incredible_auto_dev`** framework repo (github.com:dennisccy/incredible_auto_dev).
**From:** the `tapeology` project, which vendors this framework at `incredible_auto_dev/` and ran a goal-mode session (`yahoo_fetch`) that is **substantively complete but cannot get the formal `GOAL_ACHIEVED` stamp** because of a bug in the framework's secret-scan gate.

---

## 1. What happened (symptom)

A goal-mode session finished all its product work — every Must-have journey passes, browser-verified, zero product source changed for several iterations. But the deterministic achievement gate keeps returning **CONTINUE instead of GOAL_ACHIEVED**, blocked solely on the secret-scan check:

- `goal-gates.sh` fails the achievement gate when `runs/<sid>/iter-<N>/scan-report.md` contains a line matching `^\*\*Result:\*\* CRITICAL` (goal-gates.sh:126).
- Every CRITICAL finding resolves to a **fake / example credential** — AWS's public documentation example access-key (`AKIA…`-shaped, authenticates nothing) and a `hunter2`-style joke password — and is confirmed **absent from product source** (`git diff <snapshot> -- apps/` is empty).
- Worse, the finding count **compounds every iteration** (observed 1 → 3 → rising). Two consecutive iterations spent entirely trying to clear it made it *worse*, not better.
- Three different consumer agents (developer, reviewer, coherence-auditor) reported the scan "CLEAN" in the same iteration where the canonical artifact was actually CRITICAL — a **stale-read / timing race**.

Net effect: the harness is flagging the harness's **own generated output** as leaked secrets, in a self-reinforcing loop, and no amount of in-session fixing converges.

---

## 2. Root cause

### 2a. The recursion (primary bug)

`goal_gate_build_diff_artifacts()` in **`scripts/automation/lib/goal-gates.sh:46-72`** builds the text that gets scanned (`$full_diff`) as:

1. `git diff <snapshot_sha>` (tracked changes since the iteration's start), **plus**
2. **every untracked file** in the repo, each rendered as fully-added content via `git diff --no-index /dev/null <file>` (goal-gates.sh:58-65, capped at 200 files).

It then writes the scan result to `runs/<sid>/iter-<N>/scan-report.md` and a bounded diff view to `runs/<sid>/iter-<N>/iter-diff.md` (goal-gates.sh:68-71).

**There is no path exclusion on step 2.** At evaluation time the iteration's work is not yet committed (goal mode commits only at the push step, *after* evaluation), so a large set of the harness's own generated artifacts are *untracked* and get folded into `$full_diff` and scanned:

- `runs/<sid>/iter-<N>/scan-report.md` ← **the scanner's own previous output**, which literally lists prior findings (including the matched token snippets)
- `runs/<sid>/iter-<N>/iter-diff.md` ← the bounded diff view (also quotes them)
- `runs/<sid>/trace/trace.jsonl` ← captures every agent message verbatim
- `reports/**/*.md`, `reports/**/*.html` ← iteration summaries + the session-index HTML

These artifacts quote secret-looking tokens for an innocent reason: when the evaluator / iteration-summarizer **explain the false positive in prose**, the example token lands in their output; and `scan-report.md` itself enumerates the findings. On the next build, `git ls-files --others` includes those files → they re-enter `$full_diff` → the scanner re-detects the tokens and lists them in a fresh `scan-report.md` → which is itself untracked → which the *next* build scans again. **Self-referential, monotonically growing.**

This is the core bug: **a secret scanner is scanning the harness's own generated reports, traces, and its own prior scan output.** It should scan product **source**, not generated bookkeeping.

### 2b. Aggravating factors (secondary)

- **`scan_diff.py` self-test embeds literal fixture secrets.** `scripts/automation/lib/scan_diff.py`'s `self-test` block contains literal added-line fixtures (a `password = "…"` assignment and an `AKIA…`-shaped key). Any edit to `scan_diff.py` therefore re-adds these literals as added lines in *its own* tracked diff, tripping the scanner on the very file meant to fix it.
- **The `_KNOWN_FAKE_CREDENTIALS` allowlist is incomplete and the wrong tool.** It is defined at `scan_diff.py:68` and only consulted inside the `_CRITICAL_PATTERNS` loop (`scan_diff.py:159`), so it does **not** cover the generic `secret-assignment` critical path (`scan_diff.py:169`) — joke passwords still trip. More fundamentally, value-based allowlisting is fragile and dangerous: it collides with the judgment fixture below, and blanket-allowlisting a token blinds the detector.
- **False-CLEAN timing race.** Consumer agents that reconstruct-and-scan the diff themselves (or read an early copy) can observe CLEAN while the canonical `iter-<N>/scan-report.md` is regenerated to CRITICAL moments later. The gate and its consumers disagree.

### 2c. The constraint any fix must respect

There is a deliberate judgment fixture — `tests/judgment/goal-evaluator/case-05-secret-committed/` — that **commits a fake secret into PRODUCT source on purpose, to prove the scanner detects real leaks.** Its `tools/regen.sh` hard-asserts the `aws-access-key` rule still fires. So the fix must **distinguish**:

- ✅ fake secret in **product source** (case-05) → must stay **CRITICAL**, vs
- ❌ example token quoted in the **harness's own generated report/trace/summary** (the recursion) → must be **excluded**.

A **path-based exclusion of generated artifacts** achieves this cleanly. A **value-based allowlist does not** (it breaks case-05 and blinds the detector) — this was tried in-session and failed.

---

## 3. Recommended fix

**Primary (breaks the recursion at its root):**
In `goal_gate_build_diff_artifacts()` (`scripts/automation/lib/goal-gates.sh`, the untracked-file loop at ~lines 58-65, and ideally the `git diff` at ~52 too), **exclude the harness's own generated/bookkeeping paths** from what is fed to the scanner. At minimum exclude `runs/`, `reports/`, and any `*/trace/*`; scan only genuine project source (e.g. restrict to `apps/`, or a configurable source-root, or reuse the same exclusion list the reviewer/coherence diff commands already apply — they exclude `runs/*` and `reports/*`, but this gate does not). A secret scanner must scan source, not the pipeline's own output.

**Hardening:**
1. In `scan_diff.py`, build the `self-test` fixture secrets by **runtime string concatenation** so the source file never contains a literal token that matches its own patterns. (Do the same in any docs/spec templates that must reference example keys.)
2. Given the primary fix removes the generated-artifact source, keep `_KNOWN_FAKE_CREDENTIALS` minimal — or, if retained, apply it consistently across both the `_CRITICAL_PATTERNS` and `secret-assignment` paths. Prefer path-scope over value-allowlist.
3. Close the **false-CLEAN race**: consumers (developer/reviewer/coherence-auditor prompts, and the evaluator) should read the **final canonical** `runs/<sid>/iter-<N>/scan-report.md` written by the gate, not a self-reconstruction. Consider a completion sentinel or having the gate stamp the report so consumers can detect a stale read.

**Acceptance criteria:**
- New regression test: an iteration whose `$full_diff` includes a generated `scan-report.md` / `iter-diff.md` / summary that *quotes* example credentials must scan **CLEAN**.
- `python3 scripts/automation/lib/scan_diff.py self-test` and `bash scripts/automation/lib/goal-gates.sh --self-test` still pass.
- `tests/judgment/goal-evaluator/case-05-secret-committed` still yields **CRITICAL** (path-based exclusion must not blind detection of a fake secret committed to *source*); `tools/regen.sh` still green.
- Editing `scan_diff.py` itself does not make `scan_diff.py`'s own diff trip the scanner.

---

## 4. Ready-to-paste prompt for the upstream Claude

> The goal-mode secret-scan gate in this framework has a self-referential recursion bug that makes the deterministic `GOAL_ACHIEVED` gate unreachable even when the product is clean. Please fix it.
>
> **Bug:** `goal_gate_build_diff_artifacts()` in `scripts/automation/lib/goal-gates.sh` builds the scanned text (`$full_diff`) from `git diff <snapshot>` **plus every untracked file in the repo** (the untracked loop ~lines 58-65), with **no path exclusion**. Because goal mode commits work only at the push step (after evaluation), the harness's own generated artifacts are untracked at scan time and get scanned: `runs/<sid>/iter-<N>/scan-report.md` (the scanner's own prior output, which lists matched token snippets), `runs/<sid>/iter-<N>/iter-diff.md`, `runs/<sid>/trace/trace.jsonl`, and `reports/**/*.{md,html}`. Those quote example/fake credentials (AWS's public `AKIA…` example key; `hunter2`-style test passwords) because evaluator/summarizer prose *explains* the findings and `scan-report.md` *lists* them. So each build re-scans the last build's output and the count compounds. `scan_diff.py` (`_CRITICAL_PATTERNS` at line ~48; generic `secret-assignment` at ~169) has no notion that it's scanning its own reports.
>
> **Fix:** make the secret scan operate on project **source only** — exclude `runs/`, `reports/`, and `*/trace/*` (and any other generated/bookkeeping output) from both the untracked-file enumeration and the tracked `git diff` in `goal_gate_build_diff_artifacts()`. The reviewer/coherence diff commands already carry an exclusion list (`runs/*`, `reports/*`, lockfiles, binaries, etc.) — reuse or share it.
>
> **Do NOT** fix this by value-allowlisting the example tokens: `tests/judgment/goal-evaluator/case-05-secret-committed/` deliberately commits a fake secret **into product source** and its `tools/regen.sh` asserts the scanner still flags it. The fix must keep case-05 CRITICAL (fake secret in *source*) while excluding the harness's own generated reports (example token in *generated output*). That distinction is path-based, not value-based.
>
> **Also harden:** (a) build `scan_diff.py`'s `self-test` fixture secrets via runtime concatenation so editing `scan_diff.py` doesn't make its own diff trip the scanner; (b) ensure the gate's consumers read the final canonical `scan-report.md`, not a self-reconstruction, to close a stale-read race that reported false-CLEAN.
>
> **Acceptance:** add a regression test where the scanned diff includes a generated `scan-report.md` quoting example credentials and must come out CLEAN; keep `scan_diff.py self-test` and `goal-gates.sh --self-test` green; keep the `case-05-secret-committed` fixture CRITICAL with `regen.sh` green.

---

## 5. State of the vendored copy in tapeology (for cleanup)

While diagnosing this in-session, the goal-mode developer made **local, uncommitted** edits to the vendored framework on branch `goal/yahoo_fetch` (3 files, working-tree only — no commit landed):

- `incredible_auto_dev/scripts/automation/lib/scan_diff.py` (added `_KNOWN_FAKE_CREDENTIALS` allowlist + `--include-known-fakes` bypass + `finditer`)
- `incredible_auto_dev/tests/judgment/goal-evaluator/tools/regen.sh`
- `incredible_auto_dev/tests/judgment/goal-evaluator/case-05-secret-committed/notes.md`

These were an attempted (value-based) workaround that the analysis above supersedes. To restore clean parity with `auto_dev/main@1814e24` before the proper upstream fix lands:

```bash
git checkout -- \
  incredible_auto_dev/scripts/automation/lib/scan_diff.py \
  incredible_auto_dev/tests/judgment/goal-evaluator/tools/regen.sh \
  incredible_auto_dev/tests/judgment/goal-evaluator/case-05-secret-committed/notes.md
```

Once the upstream framework fix is released, `git subtree`/content-sync the vendored `incredible_auto_dev/` back up to it, then re-run the goal session's final gate — it should certify `GOAL_ACHIEVED` cleanly (all six journeys already pass; the product diff is empty).
