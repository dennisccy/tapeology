"""No-credential-in-artifacts gate (era-5B J-03 acceptance) -- Alpaca credential VALUES must never
appear literal in any source file, fixture, log, test artifact, or report (goal.md's "keys never
committed, never logged" CRITICAL anti-goal).

Distinct from the EXISTING ``test_alpaca_credential_names_confined_to_one_module``
(``test_real_data_gate.py``), which polices WHERE the two env-var NAMES ("ALPACA_API_KEY" /
"ALPACA_API_SECRET") may appear as CODE under ``app/`` -- referencing a NAME is normal and
required (the adapter reads it; this iteration's own dev handoff must document that the keys were
present/absent). This gate instead polices two DIFFERENT, complementary things:

  1. **J-03's own new CODE never carries generic secret-shaped vocabulary.** The recording driver
     only ever calls ``adapter.is_available()`` through the EXISTING neutral seam (architecture
     fact: it never reads ``ALPACA_API_KEY``/``ALPACA_API_SECRET`` directly) -- so J-03's code has
     no legitimate reason to contain a lowercase ``api_key`` / ``api_secret`` / ``token``
     assignment-shaped literal anywhere. The two env-var NAME strings themselves (uppercase,
     ``ALPACA_API_KEY`` / ``ALPACA_API_SECRET``) are DELIBERATELY NOT forbidden in code: the
     recording driver's own operator-facing guidance message legitimately prints them by name (so
     an operator knows what to set), and the dev handoff is REQUIRED to document them by name --
     exactly the same "a NAME reference is normal, a VALUE never is" distinction
     ``test_alpaca_credential_names_confined_to_one_module`` already draws for ``app/``. The
     committed tick-FIXTURE (pure market data, unlike code/docs) has no legitimate reason to
     contain ANY of these strings in ANY casing, so it is checked against the FULL set -- the
     EXACT existing ``test_real_gme_sip_fixture_carries_no_credentials`` precedent, reused
     verbatim. Unlike ``test_no_execution_path.py`` (which deliberately EXCLUDES ``fixtures/``
     from its scan), this gate's whole reason to exist is to include exactly the surface that scan
     skips.
  2. **If this environment currently has REAL credentials configured, their literal VALUES never
     appear anywhere in the scanned tree.** The strongest possible check -- run only when there is
     a real secret to compare against (never fabricated); the two env-var NAME strings themselves
     are explicitly NOT forbidden here (the dev handoff is REQUIRED to document whether the keys
     were configured, by name, per the DoD -- forbidding the name would conflict with that).

Proven non-vacuous (a file-count floor + named paths) and signal-bearing (a seeded temp file
containing a credential-shaped string trips the SAME matcher) -- the ``test_no_execution_path.py``
discipline, applied to secrets.
"""

from __future__ import annotations

import os
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]

# This gate itself names every pattern as data (the test_no_execution_path.py SELF-exemption
# precedent) -- it is scanning/policing code, not a candidate for the credential scan.
SELF = Path(__file__).resolve()

# J-03's own new/modified CODE surfaces (script + join code + config + tests) -- an explicit list,
# not a directory walk, so this gate's scope is exactly what THIS iteration introduces, never an
# accidental sweep over unrelated pre-existing files (which legitimately reference the env-var
# NAMES elsewhere in the suite via monkeypatch, and are already policed by
# test_alpaca_credential_names_confined_to_one_module).
J03_CODE_FILES = tuple(
    p for p in (
        BACKEND_DIR / "scripts" / "record_event_windows.py",
        BACKEND_DIR / "scripts" / "generate_setups_join_fixture.py",
        BACKEND_DIR / "app" / "research" / "setups.py",
        BACKEND_DIR / "app" / "research" / "routes.py",
        BACKEND_DIR / "app" / "config.py",
        BACKEND_DIR / "tests" / "test_setups.py",
        BACKEND_DIR / "tests" / "test_setups_api.py",
        BACKEND_DIR / "tests" / "test_record_event_windows.py",
        BACKEND_DIR / "tests" / "test_event_recording_integration.py",
        SELF,
    ) if p != SELF
)
J03_FIXTURE_DIR = BACKEND_DIR / "tests" / "fixtures" / "datasets_j03"

# CODE: only the lowercase generic-secret vocabulary (the env-var NAMES are legitimate prose there
# -- operator guidance + the dev handoff's required disclosure).
CODE_FORBIDDEN_SUBSTRINGS = ("api_key", "api_secret", "token")
# FIXTURE (pure market data -- no legitimate string in ANY casing): the FULL set
# test_real_gme_sip_fixture_carries_no_credentials already uses for the era-3 committed fixture,
# reused verbatim here (a proven, existing precedent, not a new invention).
FIXTURE_FORBIDDEN_SUBSTRINGS = ("api_key", "api_secret", "ALPACA_API_KEY", "ALPACA_API_SECRET", "token")


def _code_files() -> list[Path]:
    return [p for p in J03_CODE_FILES if p.exists()]


def _fixture_files() -> list[Path]:
    if not J03_FIXTURE_DIR.exists():
        return []
    return sorted(p for p in J03_FIXTURE_DIR.iterdir() if p.is_file())


def test_scan_is_not_vacuous():
    code_files = _code_files()
    assert len(code_files) >= 9
    names = {p.name for p in code_files}
    assert "record_event_windows.py" in names
    assert "setups.py" in names
    fixture_files = _fixture_files()
    assert J03_FIXTURE_DIR.exists(), "the committed J-03 tick-fixture directory must exist"
    assert any(p.suffix == ".json" for p in fixture_files), "the committed tick-fixture must be scanned"


def test_matcher_catches_a_seeded_counter_example(tmp_path):
    seeded = tmp_path / "seeded.py"
    seeded.write_text('api_secret = "abc123"  # a hardcoded credential value')
    text = seeded.read_text()
    assert any(forbidden in text for forbidden in CODE_FORBIDDEN_SUBSTRINGS)

    seeded_fixture = tmp_path / "seeded.json"
    seeded_fixture.write_text('{"ALPACA_API_KEY": "abc123", "token": "xyz"}')
    fixture_text = seeded_fixture.read_text()
    assert any(forbidden in fixture_text for forbidden in FIXTURE_FORBIDDEN_SUBSTRINGS)


def test_j03_surfaces_carry_no_credential_shaped_literal():
    offenders: list[str] = []
    for path in _code_files():
        text = path.read_text(errors="ignore")
        for forbidden in CODE_FORBIDDEN_SUBSTRINGS:
            if forbidden in text:
                offenders.append(f"{path.relative_to(BACKEND_DIR)}: {forbidden!r}")
    for path in _fixture_files():
        text = path.read_text(errors="ignore")
        for forbidden in FIXTURE_FORBIDDEN_SUBSTRINGS:
            if forbidden in text:
                offenders.append(f"{path.relative_to(BACKEND_DIR)}: {forbidden!r}")
    assert offenders == [], (
        "credential-shaped literal found in a J-03 surface — the keys-never-committed-or-logged "
        f"anti-goal is violated: {offenders}"
    )


def test_real_credential_values_if_configured_never_appear_in_j03_surfaces():
    """Defense in depth on an operator's credentialed machine: IF real Alpaca credentials are
    configured in this environment, their literal VALUES must never appear anywhere in J-03's own
    surfaces. The env-var NAMES themselves are deliberately NOT checked here (the dev handoff must
    document them by name, per the DoD) -- only the secret VALUES. An honest no-op (nothing to
    compare against) when no credentials are configured -- never fabricated."""
    key = os.environ.get("ALPACA_API_KEY", "").strip()
    secret = os.environ.get("ALPACA_API_SECRET", "").strip()
    if not key and not secret:
        return  # nothing configured in this environment -- nothing to check a value against
    for path in _code_files() + _fixture_files():
        text = path.read_text(errors="ignore")
        if key:
            assert key not in text, f"the real ALPACA_API_KEY value leaked into {path}"
        if secret:
            assert secret not in text, f"the real ALPACA_API_SECRET value leaked into {path}"
