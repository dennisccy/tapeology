#!/usr/bin/env bash
# store-scope.sh — make "the automated run never touched the operator's real
# store" a MECHANISM instead of a claim.
#
# WHY: a project can ship a launcher that stands up a fixture-scoped backend for
# browser/replay work, and the pipeline can still run its lanes against whatever
# backend happens to be listening on the QA port. That is exactly what happened
# in tapeology's goal-playbook-iter-8: the deterministic replay lane replayed a
# golden containing a "Run Backscan" click against the operator's AMBIENT
# backend, computed three real S&P-100 playbook records and appended a run-ledger
# row into an append-only store that by the project's own rails can never be
# pruned — while the iteration's own acceptance said that could no longer happen.
# A launcher nothing is obliged to use is not a mechanism; a gate is.
#
# THE GATE, three verbs:
#   require              — refuse to run any browser lane unless the project's
#                          own assert command PROVES the backend under test is
#                          the scoped one. One prepare attempt in between, when
#                          the project declares a prepare command. rc 1 = the
#                          caller must NOT dispatch a browser lane.
#   snapshot <manifest>  — record every regular file under the project's
#                          protected store paths (size + mtime), before the run.
#   verify <manifest> [report.md]
#                        — re-read those paths and hard-fail (rc 1) on ANY
#                          delta: added, removed, or modified. Writes a
#                          disclosure artifact either way, so a later reader
#                          cites an executed check instead of prose.
#
# PROJECT-NEUTRAL BY CONSTRUCTION (the host-guard precedent): with no
# project-extensions/store-scope/store-scope.env — or with STORE_SCOPE_ENABLED
# not 1 — every verb is a no-op exiting 0 and prints nothing but a single
# skip line to stderr. Nothing about any other project's behavior changes.
#
# Config (project-extensions/store-scope/store-scope.env):
#   STORE_SCOPE_ENABLED=1
#   STORE_SCOPE_LABEL="..."             human name used in logs/disclosure
#   STORE_SCOPE_PROTECTED_PATHS="a b"   repo-relative dirs/files, space-separated
#   STORE_SCOPE_ASSERT_CMD="..."        exits 0 iff the backend under test is scoped
#   STORE_SCOPE_PREPARE_CMD="..."       optional; run once when the assert fails
#
# Both commands run with the project root as CWD and inherit the caller's
# environment (CHAIN_BACKEND_PORT, FRONTEND_URL, ... are therefore visible).
#
# Usage: store-scope.sh require | snapshot <manifest> | verify <manifest> [report.md]
# Exit:  0 = ok/no-op · 1 = refusal (require) or breach (verify) · 2 = bad usage
set -uo pipefail

ROOT="${STORE_SCOPE_ROOT:-$(git -C "$PWD" rev-parse --show-toplevel 2>/dev/null || pwd)}"
[[ "$ROOT" == */incredible_auto_dev ]] && ROOT="${ROOT%/incredible_auto_dev}"
ENV_FILE="$ROOT/project-extensions/store-scope/store-scope.env"

_ss_log()  { echo "[store-scope] $*"; }
_ss_warn() { echo "[store-scope] $*" >&2; }

# shellcheck disable=SC1090
[[ -f "$ENV_FILE" ]] && source "$ENV_FILE" 2>/dev/null

CMD="${1:-}"
[[ -n "$CMD" ]] || { echo "usage: store-scope.sh require | snapshot <manifest> | verify <manifest> [report.md]" >&2; exit 2; }

if [[ "${STORE_SCOPE_ENABLED:-0}" != "1" ]]; then
  _ss_warn "no store-scope declared for $ROOT — nothing to guard ($CMD)."
  exit 0
fi

LABEL="${STORE_SCOPE_LABEL:-store scope}"
PATHS="${STORE_SCOPE_PROTECTED_PATHS:-}"

# One manifest line per regular file: "<size> <mtime> <repo-relative path>",
# sorted by path so two manifests diff deterministically. Deliberately stat-based
# (never a content hash): the guard must stay cheap enough to run around EVERY
# browser lane, and any write that a checksum would catch moves size or mtime
# too. A missing protected path contributes nothing and is not an error — a
# store directory that does not exist yet is a legitimate state, and its later
# CREATION shows up as its first file appearing.
_ss_manifest() {  # $1 = output file
  local out="$1" p
  : > "$out" || return 1
  for p in $PATHS; do
    [[ -e "$ROOT/$p" ]] || continue
    ( cd "$ROOT" && find "$p" -type f -printf '%s\t%T@\t%p\n' 2>/dev/null ) >> "$out"
  done
  LC_ALL=C sort -t"$(printf '\t')" -k3 -o "$out" "$out" 2>/dev/null || true
}

case "$CMD" in

  require)
    if [[ -z "${STORE_SCOPE_ASSERT_CMD:-}" ]]; then
      _ss_warn "$LABEL: store-scope is enabled but declares no STORE_SCOPE_ASSERT_CMD — the backend under test CANNOT be proven scoped; the snapshot/verify gate is the only remaining guard."
      exit 0
    fi
    if ( cd "$ROOT" && eval "$STORE_SCOPE_ASSERT_CMD" ); then
      _ss_log "$LABEL: backend under test is provably scoped — browser lanes may run."
      exit 0
    fi
    if [[ -n "${STORE_SCOPE_PREPARE_CMD:-}" ]]; then
      _ss_warn "$LABEL: backend under test is NOT scoped — running the project's prepare command once before deciding."
      ( cd "$ROOT" && eval "$STORE_SCOPE_PREPARE_CMD" ) || _ss_warn "$LABEL: prepare command exited non-zero (continuing to the re-assert, which is the only thing that decides)."
      if ( cd "$ROOT" && eval "$STORE_SCOPE_ASSERT_CMD" ); then
        _ss_log "$LABEL: backend scoped by the prepare command — browser lanes may run."
        exit 0
      fi
    fi
    _ss_warn "$LABEL: REFUSING the browser lane — the backend under test is not scoped and could not be made scoped. Running it would let an automated pass write into the operator's real store (the exact defect this guard exists to prevent)."
    exit 1
    ;;

  snapshot)
    MANIFEST="${2:-}"
    [[ -n "$MANIFEST" ]] || { echo "usage: store-scope.sh snapshot <manifest>" >&2; exit 2; }
    mkdir -p "$(dirname "$MANIFEST")" 2>/dev/null || true
    _ss_manifest "$MANIFEST" || { _ss_warn "$LABEL: could not write the baseline manifest at $MANIFEST — verify will report UNKNOWN rather than a false CLEAN."; exit 0; }
    _ss_log "$LABEL: baseline captured — $(wc -l < "$MANIFEST" | tr -d ' ') file(s) under: ${PATHS}"
    exit 0
    ;;

  verify)
    MANIFEST="${2:-}"
    REPORT="${3:-}"
    [[ -n "$MANIFEST" ]] || { echo "usage: store-scope.sh verify <manifest> [report.md]" >&2; exit 2; }
    NOW="$(mktemp "${TMPDIR:-/tmp}/store-scope-now.XXXXXX")"
    _ss_manifest "$NOW"
    VERDICT="CLEAN"; ADDED=""; REMOVED=""; MODIFIED=""
    if [[ ! -s "$MANIFEST" && ! -s "$NOW" ]]; then
      : # both empty: nothing protected exists yet — genuinely clean
    fi
    if [[ ! -f "$MANIFEST" ]]; then
      VERDICT="UNKNOWN"
      _ss_warn "$LABEL: no baseline manifest at $MANIFEST — this run cannot prove the store was untouched (absent beats a false CLEAN)."
    else
      # Path sets first (added/removed), then, for paths present in BOTH, a
      # stat comparison (modified). One awk pass each, keyed on the tab-
      # delimited path field so a path containing spaces cannot smear columns.
      ADDED="$(LC_ALL=C comm -13 <(cut -f3- "$MANIFEST" | LC_ALL=C sort) <(cut -f3- "$NOW" | LC_ALL=C sort))"
      REMOVED="$(LC_ALL=C comm -23 <(cut -f3- "$MANIFEST" | LC_ALL=C sort) <(cut -f3- "$NOW" | LC_ALL=C sort))"
      MODIFIED="$(awk -F'\t' 'NR==FNR{a[$3]=$1"\t"$2; next} ($3 in a) && a[$3] != $1"\t"$2 {print $3}' \
                    "$MANIFEST" "$NOW")"
      [[ -n "${ADDED//[[:space:]]/}" || -n "${REMOVED//[[:space:]]/}" || -n "${MODIFIED//[[:space:]]/}" ]] && VERDICT="BREACH"
    fi
    if [[ -n "$REPORT" ]]; then
      mkdir -p "$(dirname "$REPORT")" 2>/dev/null || true
      {
        echo "# Store-scope guard — $LABEL"
        echo ""
        echo "**Verdict:** $VERDICT"
        echo ""
        echo "- Protected paths: \`${PATHS}\`"
        echo "- Baseline manifest: \`$MANIFEST\` ($( [[ -f "$MANIFEST" ]] && wc -l < "$MANIFEST" | tr -d ' ' || echo 0 ) file(s))"
        echo "- Post-run scan: $(wc -l < "$NOW" | tr -d ' ') file(s)"
        echo "- Checked: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
        echo ""
        if [[ "$VERDICT" == "CLEAN" ]]; then
          echo "_Every protected path holds exactly the files it held before this run, byte-size and"
          echo "mtime unchanged. The automated lanes wrote nothing into the operator's store._"
        elif [[ "$VERDICT" == "UNKNOWN" ]]; then
          echo "_No baseline was captured for this run, so nothing here proves the store was untouched._"
        else
          echo "_An automated lane wrote into a protected store path. Records and ledgers in this"
          echo "project are append-only, so these files cannot simply be deleted — they are listed"
          echo "here so the next reader knows what caused them._"
          echo ""
          echo "| Change | Path |"
          echo "|--------|------|"
          for f in $ADDED;    do [[ -n "$f" ]] && echo "| ADDED | \`$f\` |"; done
          for f in $REMOVED;  do [[ -n "$f" ]] && echo "| REMOVED | \`$f\` |"; done
          for f in $MODIFIED; do [[ -n "$f" ]] && echo "| MODIFIED | \`$f\` |"; done
        fi
      } > "$REPORT" 2>/dev/null || _ss_warn "$LABEL: could not write the disclosure artifact at $REPORT."
    fi
    rm -f "$NOW" 2>/dev/null || true
    if [[ "$VERDICT" == "BREACH" ]]; then
      _ss_warn "$LABEL: STORE-SCOPE BREACH — an automated lane wrote into a protected store path:"
      for f in $ADDED;    do [[ -n "$f" ]] && _ss_warn "  ADDED    $f"; done
      for f in $REMOVED;  do [[ -n "$f" ]] && _ss_warn "  REMOVED  $f"; done
      for f in $MODIFIED; do [[ -n "$f" ]] && _ss_warn "  MODIFIED $f"; done
      [[ -n "$REPORT" ]] && _ss_warn "  disclosure: $REPORT"
      exit 1
    fi
    _ss_log "$LABEL: store-scope verified $VERDICT${REPORT:+ (disclosure: $REPORT)}."
    exit 0
    ;;

  *)
    echo "usage: store-scope.sh require | snapshot <manifest> | verify <manifest> [report.md]" >&2
    exit 2
    ;;
esac
