#!/usr/bin/env python3
"""anti_goal_disposition.py — the ONE definition of when an anti-goal violation blocks.

WHY THIS EXISTS
---------------
The ledger (`journey-history.json` -> `anti_goal_violations`) could express only two states:
`resolved: true` and `resolved: false`. Reality has three. An owner regularly decides that a
genuinely-unresolved finding belongs to a future named revision, or to framework-maintenance
backlog, and therefore should not bar the CURRENT product era from closing. Under a two-state
ledger the only way to record that decision was to set `resolved: true` — which falsifies the
ledger, because `resolved` means "actually fixed, made impossible, or otherwise genuinely
discharged by evidence" and a deferral is none of those.

So this module adds a THIRD state and keeps the other two honest:

    resolved                   the finding was actually discharged. Unchanged meaning.
    unresolved / BLOCKING      the default. No valid disposition, or one that fails a check.
    unresolved / NON-BLOCKING  still real, still visible, still `resolved: false`, but the
                               owner has durably ruled it out of the current era's closure
                               criteria.

A closure report must always be able to say "closed with N known non-blocking deferred/backlog
findings", and must never claim they were fixed. Nothing here deletes a finding, rewrites its
evidence, or touches historical iteration artifacts.

THE DISPOSITION (additive; absence is exactly today's behaviour)
----------------------------------------------------------------
    "owner_disposition": {
      "kind": "deferred_named_revision" | "framework_backlog",
      "blocks_current_era": false,
      "ruled_at": "<ISO-8601 timestamp>",
      "ruling": "<why the owner ruled this out of the current era>",
      "future_revision_or_backlog": "<where it now lives>",
      "escalation_condition": "<verbatim, if the finding recorded one>",
      "escalation_tripped": false
    }

FAIL CLOSED, ALWAYS
-------------------
Every ambiguity resolves to BLOCKING, never to non-blocking:

  * an unresolved **critical** violation is ALWAYS blocking — no disposition can waive it.
    This mechanism exists for explicitly accepted MINOR findings, not as a gate bypass;
  * a missing, non-dict, or empty disposition blocks;
  * an unknown `kind` blocks;
  * a missing or non-`false` `blocks_current_era` blocks;
  * a missing/blank `ruled_at`, `ruling` or `future_revision_or_backlog` blocks;
  * when the finding records an `escalation_condition`, an absent or non-`false`
    `escalation_tripped` blocks — a deferral can never silently outrank a tripped
    escalation condition;
  * a missing or unrecognized `severity` is treated as critical (the methodology's own
    "when unsure whether critical, treat as critical" rule), and therefore blocks.

`escalation_tripped` is an ASSERTION the evaluator re-tests each round and records; this module
cannot evaluate prose conditions itself. It can, and does, refuse to honour a disposition whose
condition is unattested or attested as tripped.

Usage:
  anti_goal_disposition.py summary <journey-history.json>   # counts + per-entry table; exit 1
                                                            # if any BLOCKING entry remains
  anti_goal_disposition.py self-test
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

# The only dispositions that can make an unresolved finding non-blocking.
VALID_KINDS = frozenset({"deferred_named_revision", "framework_backlog"})

# Severities this module understands. Anything else is treated as critical (fail-closed).
CRITICAL_SEVERITIES = frozenset({"critical"})
MINOR_SEVERITIES = frozenset({"minor"})

# Non-empty strings the disposition must carry to be auditable at all.
REQUIRED_TEXT_FIELDS = ("ruled_at", "ruling", "future_revision_or_backlog")

# Classification results.
RESOLVED = "resolved"
BLOCKING = "blocking"
NON_BLOCKING = "non_blocking"


def _nonempty_str(value) -> bool:
    return isinstance(value, str) and value.strip() != ""


def classify(violation: dict) -> tuple[str, str]:
    """Classify ONE ledger entry. Returns (state, reason).

    `state` is one of RESOLVED / BLOCKING / NON_BLOCKING. `reason` is a short human string
    naming the rule that decided it — it goes straight into the evaluator's report, so an
    owner can always see WHY a finding did or did not bar closure.
    """
    if not isinstance(violation, dict):
        return BLOCKING, "entry is not an object (fail-closed)"

    if violation.get("resolved") is True:
        return RESOLVED, "resolved: true — genuinely discharged"
    if violation.get("resolved") not in (False, None):
        # A truthy-but-not-True value ("yes", 1, "partial") is ambiguous, never a pass.
        return BLOCKING, f"ambiguous resolved value {violation.get('resolved')!r} (fail-closed)"

    severity = violation.get("severity")
    sev = severity.strip().lower() if isinstance(severity, str) else None
    if sev not in MINOR_SEVERITIES:
        # critical, unknown, or missing — all fail closed to blocking.
        if sev in CRITICAL_SEVERITIES:
            return BLOCKING, "unresolved CRITICAL violation — never waivable"
        return BLOCKING, f"unrecognized severity {severity!r} — treated as critical (fail-closed)"

    disp = violation.get("owner_disposition")
    if disp is None:
        return BLOCKING, "unresolved, no owner disposition recorded"
    if not isinstance(disp, dict) or not disp:
        return BLOCKING, "owner_disposition is not a non-empty object (fail-closed)"

    kind = disp.get("kind")
    if kind not in VALID_KINDS:
        return BLOCKING, f"unknown owner_disposition kind {kind!r} (fail-closed)"

    if disp.get("blocks_current_era") is not False:
        return BLOCKING, (
            f"blocks_current_era is {disp.get('blocks_current_era')!r}, not false"
        )

    missing = [f for f in REQUIRED_TEXT_FIELDS if not _nonempty_str(disp.get(f))]
    if missing:
        return BLOCKING, f"owner_disposition missing/blank: {', '.join(missing)} (fail-closed)"

    # A recorded escalation condition must carry a current, explicit not-tripped attestation.
    if _nonempty_str(disp.get("escalation_condition")):
        tripped = disp.get("escalation_tripped")
        if tripped is not False:
            return BLOCKING, (
                f"escalation_condition recorded but escalation_tripped is {tripped!r}, "
                "not false (fail-closed)"
            )

    return NON_BLOCKING, f"owner-dispositioned {kind}, blocks_current_era: false"


def classify_all(violations) -> list[tuple[str, str, dict]]:
    if not isinstance(violations, list):
        return []
    return [(*classify(v), v) for v in violations]


def summarize(violations) -> dict:
    """Counts the evaluator's decision tree needs, plus the closure-report phrasing."""
    rows = classify_all(violations)
    return {
        "total": len(rows),
        "resolved": sum(1 for s, _, _ in rows if s == RESOLVED),
        "unresolved_blocking": sum(1 for s, _, _ in rows if s == BLOCKING),
        "unresolved_non_blocking": sum(1 for s, _, _ in rows if s == NON_BLOCKING),
        "unresolved_critical": sum(
            1
            for s, _, v in rows
            if s == BLOCKING
            and v.get("resolved") is not True
            and isinstance(v.get("severity"), str)
            and v["severity"].strip().lower() in CRITICAL_SEVERITIES
        ),
    }


def _load(path: str):
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise SystemExit(f"[anti-goal-disposition] cannot read {path}: {exc}")
    return data.get("anti_goal_violations", []) or []


def cmd_summary(path: str) -> int:
    violations = _load(path)
    rows = classify_all(violations)
    counts = summarize(violations)
    print(f"[anti-goal-disposition] {path}")
    print(
        f"  total={counts['total']}  resolved={counts['resolved']}  "
        f"unresolved_blocking={counts['unresolved_blocking']}  "
        f"unresolved_non_blocking={counts['unresolved_non_blocking']}  "
        f"unresolved_critical={counts['unresolved_critical']}"
    )
    for state, reason, v in rows:
        if state == RESOLVED:
            continue
        print(f"  [{state.upper():<12}] {v.get('iter', '?')} ({v.get('severity')}) — {reason}")
    return 1 if counts["unresolved_blocking"] else 0


# ── self-test ────────────────────────────────────────────────────────────────

def _self_test() -> int:
    failures: list[str] = []

    def check(name, fn):
        try:
            fn()
        except Exception as exc:  # noqa: BLE001
            failures.append(f"{name}: {exc!r}")

    def _disp(**over):
        base = {
            "kind": "framework_backlog",
            "blocks_current_era": False,
            "ruled_at": "2026-08-24T00:00:00Z",
            "ruling": "owner ruled this framework-owned and out of the current era",
            "future_revision_or_backlog": "framework backlog: scripts/automation/**",
        }
        base.update(over)
        return base

    def _v(**over):
        base = {"iter": "iter-1", "anti_goal": "x", "severity": "minor",
                "evidence": "e", "resolved": False}
        base.update(over)
        return base

    # A. unresolved minor, no disposition -> BLOCKS
    def t_a():
        state, reason = classify(_v())
        assert state == BLOCKING, (state, reason)
        assert "no owner disposition" in reason, reason

    # B. unresolved CRITICAL + a valid non-blocking disposition -> STILL BLOCKS
    def t_b():
        state, reason = classify(_v(severity="critical", owner_disposition=_disp()))
        assert state == BLOCKING, (state, reason)
        assert "CRITICAL" in reason, reason
        # ...and via the other disposition kind too — the waiver is refused on severity alone.
        state2, _ = classify(
            _v(severity="critical", owner_disposition=_disp(kind="deferred_named_revision"))
        )
        assert state2 == BLOCKING, state2

    # C. unresolved minor + malformed/unknown disposition -> BLOCKS
    def t_c():
        cases = [
            ("unknown kind", _disp(kind="just_ignore_it")),
            ("kind missing", {k: v for k, v in _disp().items() if k != "kind"}),
            ("blocks_current_era true", _disp(blocks_current_era=True)),
            ("blocks_current_era missing", {k: v for k, v in _disp().items()
                                            if k != "blocks_current_era"}),
            ("blocks_current_era stringy", _disp(blocks_current_era="false")),
            ("ruling blank", _disp(ruling="   ")),
            ("ruled_at missing", {k: v for k, v in _disp().items() if k != "ruled_at"}),
            ("reference missing", {k: v for k, v in _disp().items()
                                   if k != "future_revision_or_backlog"}),
            ("not an object", "framework_backlog"),
            ("empty object", {}),
        ]
        for label, disp in cases:
            state, reason = classify(_v(owner_disposition=disp))
            assert state == BLOCKING, f"{label} should block, got {state} ({reason})"

    # D. unresolved minor + valid deferred_named_revision -> NON-BLOCKING
    def t_d():
        state, reason = classify(
            _v(owner_disposition=_disp(kind="deferred_named_revision",
                                       future_revision_or_backlog="referee spec rev 2"))
        )
        assert state == NON_BLOCKING, (state, reason)

    # E. unresolved minor + valid framework_backlog -> NON-BLOCKING
    def t_e():
        state, reason = classify(_v(owner_disposition=_disp()))
        assert state == NON_BLOCKING, (state, reason)

    # F. resolved: true -> non-blocking by existing semantics, and NOT reported as a deferral
    def t_f():
        state, reason = classify(_v(resolved=True))
        assert state == RESOLVED, (state, reason)
        counts = summarize([_v(resolved=True)])
        assert counts["resolved"] == 1 and counts["unresolved_non_blocking"] == 0, counts
        # a truthy-but-not-True value must not sneak through
        assert classify(_v(resolved="yes"))[0] == BLOCKING

    # G. escalation condition tripped (or unattested) -> a deferral cannot override it
    def t_g():
        tripped = _disp(escalation_condition="re-score CRITICAL if a production caller appears",
                        escalation_tripped=True)
        state, reason = classify(_v(owner_disposition=tripped))
        assert state == BLOCKING, (state, reason)
        assert "escalation" in reason, reason
        unattested = _disp(escalation_condition="re-score CRITICAL if X")
        state2, reason2 = classify(_v(owner_disposition=unattested))
        assert state2 == BLOCKING, (state2, reason2)
        # explicitly not tripped -> honoured
        ok = _disp(escalation_condition="re-score CRITICAL if X", escalation_tripped=False)
        assert classify(_v(owner_disposition=ok))[0] == NON_BLOCKING

    # Mutation guard: the whole point is that these three states stay distinct.
    def t_states_distinct():
        rows = [
            _v(iter="r", resolved=True),
            _v(iter="b"),
            _v(iter="n", owner_disposition=_disp()),
        ]
        counts = summarize(rows)
        assert counts == {"total": 3, "resolved": 1, "unresolved_blocking": 1,
                          "unresolved_non_blocking": 1, "unresolved_critical": 0}, counts

    def t_unknown_severity_fails_closed():
        for sev in (None, "", "moderate", 3):
            state, reason = classify(_v(severity=sev, owner_disposition=_disp()))
            assert state == BLOCKING, f"severity {sev!r} should fail closed, got {state}"

    tests = [
        ("A_unresolved_minor_no_disposition_blocks", t_a),
        ("B_unresolved_critical_with_disposition_still_blocks", t_b),
        ("C_malformed_or_unknown_disposition_blocks", t_c),
        ("D_valid_deferred_named_revision_non_blocking", t_d),
        ("E_valid_framework_backlog_non_blocking", t_e),
        ("F_resolved_true_keeps_existing_semantics", t_f),
        ("G_tripped_or_unattested_escalation_still_blocks", t_g),
        ("states_stay_distinct", t_states_distinct),
        ("unknown_severity_fails_closed", t_unknown_severity_fails_closed),
    ]
    for name, fn in tests:
        check(name, fn)

    for f in failures:
        print(f"  FAIL {f}", file=sys.stderr)
    print(f"[anti-goal-disposition self-test] {len(tests) - len(failures)} passed, "
          f"{len(failures)} failed")
    return 1 if failures else 0


def main(argv: list[str]) -> int:
    if argv and argv[0] in ("self-test", "--self-test"):
        return _self_test()
    if len(argv) == 2 and argv[0] == "summary":
        return cmd_summary(argv[1])
    sys.stderr.write(
        "usage: anti_goal_disposition.py summary <journey-history.json>\n"
        "       anti_goal_disposition.py self-test\n"
    )
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
