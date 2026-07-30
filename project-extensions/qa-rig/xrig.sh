#!/usr/bin/env bash
# xrig.sh — the owner-approved HEADED capture rig (tapeology, approved 2026-07-30).
#
# WHY THIS EXISTS: goal.md's T-10 demands a SCREENSHOT for browser acceptance lines, and era-B
# J-14 needs a photograph of a ranked row's drill-in tooltip carrying its `bands_by_class` line.
# That hint is a native HTML `title` (apps/frontend/app/desk/page.tsx:346). Chrome draws native
# tooltips as a SEPARATE X window owned by the browser process — outside the web-contents surface
# that CDP's `Page.captureScreenshot` (and therefore every headless screenshot, Playwright's
# included) can see. Three goal-mode iterations (19, 20, 21) burned on this and the session halted
# STALLED asking the owner to choose. The owner chose "approve a headed/desktop capture rig".
#
# WHAT IT IS: a throwaway X server (Xvfb) + a real headed Chrome on it + an X-level screen grab.
# Nothing is installed system-wide and no sudo is used: the two X tools are `apt-get download`ed
# and `dpkg -x`-extracted into a user-owned prefix. The user's real desktop is NEVER captured —
# the rig owns its own display, so the grab contains only the rig's browser.
#
# CONTRACT: this script only starts/stops/reports. The capture itself lives in
# capture-native-tooltip.py, which reads the state file this script writes.
#
#   ./project-extensions/qa-rig/xrig.sh up       # ensure tools, Xvfb + headed Chrome are running
#   ./project-extensions/qa-rig/xrig.sh status   # print state (exit 0 = up, 1 = down)
#   ./project-extensions/qa-rig/xrig.sh env      # print the state file (eval-able)
#   ./project-extensions/qa-rig/xrig.sh down     # stop Chrome + Xvfb (tools/prefix are kept)
#
# Knobs (env): QA_RIG_HOME (default ~/.cache/tapeology-qa-rig), QA_RIG_DISPLAY (default :99),
# QA_RIG_CDP_PORT (default 9333 — deliberately NOT 9222/9223, which the superpowers-chrome MCP
# server and framework browser lanes already use; colliding there silently attaches the capture
# to the WRONG Chrome, which is exactly how the first prototype of this rig produced a black
# screenshot), QA_RIG_SCREEN (default 1600x1200x24).
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
RIG_HOME="${QA_RIG_HOME:-$HOME/.cache/tapeology-qa-rig}"
RIG_DISPLAY="${QA_RIG_DISPLAY:-:99}"
RIG_CDP_PORT="${QA_RIG_CDP_PORT:-9333}"
RIG_SCREEN="${QA_RIG_SCREEN:-1600x1200x24}"
PREFIX="$RIG_HOME/prefix"
STATE="$RIG_HOME/state.env"
XVFB="$PREFIX/usr/bin/Xvfb"
XDOTOOL="$PREFIX/usr/bin/xdotool"
XLIBS="$PREFIX/usr/lib/x86_64-linux-gnu"
CHROME_PROFILE="$RIG_HOME/chrome-profile"

log() { printf '[xrig] %s\n' "$*" >&2; }

# The host-guard mask (project-extensions/host-guard/host-guard.env) exists because unguarded
# all-core bursts have hard-reset this machine. A rig browser is a burst source like any other,
# so pin it to the same mask when the project declares one.
_taskset_prefix() {
  local hg="$REPO_ROOT/project-extensions/host-guard/host-guard.env"
  [[ -r "$hg" ]] || return 0
  # shellcheck disable=SC1090
  local mask; mask="$(. "$hg" >/dev/null 2>&1; printf '%s' "${HOST_GUARD_CPU_LIST:-}")"
  [[ -n "$mask" ]] && command -v taskset >/dev/null 2>&1 && printf 'taskset -c %s' "$mask"
}

ensure_tools() {
  [[ -x "$XVFB" && -x "$XDOTOOL" ]] && return 0
  log "fetching Xvfb + xdotool into $PREFIX (user-space, no sudo, no system install)"
  mkdir -p "$RIG_HOME/debs" "$PREFIX"
  ( cd "$RIG_HOME/debs" && apt-get download xvfb xdotool libxdo3 >/dev/null )
  for d in "$RIG_HOME"/debs/*.deb; do dpkg -x "$d" "$PREFIX"; done
  [[ -x "$XVFB" && -x "$XDOTOOL" ]] || { log "FAILED: tools missing after extraction"; exit 2; }
  # Fail loudly NOW if a shared library is missing, rather than mid-capture.
  if LD_LIBRARY_PATH="$XLIBS" ldd "$XDOTOOL" | grep -q "not found"; then
    log "FAILED: xdotool has unresolved libraries"; exit 2
  fi
  log "tools ready"
}

xvfb_pid() { pgrep -f "Xvfb $RIG_DISPLAY " 2>/dev/null | head -1; }
chrome_pid() { pgrep -f -- "--user-data-dir=$CHROME_PROFILE" 2>/dev/null | head -1; }

# A CDP port that answers but belongs to somebody else's browser is worse than a dead port: the
# capture would drive the wrong Chrome. Prove ownership by matching the profile dir.
cdp_is_ours() {
  local pid; pid="$(chrome_pid || true)"
  [[ -n "$pid" ]] || return 1
  tr '\0' ' ' < "/proc/$pid/cmdline" 2>/dev/null | grep -q -- "--remote-debugging-port=$RIG_CDP_PORT"
}

up() {
  ensure_tools
  mkdir -p "$CHROME_PROFILE"
  if [[ -z "$(xvfb_pid || true)" ]]; then
    log "starting Xvfb on $RIG_DISPLAY ($RIG_SCREEN)"
    setsid "$XVFB" "$RIG_DISPLAY" -screen 0 "$RIG_SCREEN" -nolisten tcp \
      >"$RIG_HOME/xvfb.log" 2>&1 </dev/null &
    sleep 2
    [[ -n "$(xvfb_pid || true)" ]] || { log "FAILED: Xvfb did not start (see $RIG_HOME/xvfb.log)"; exit 2; }
  fi
  if ! cdp_is_ours; then
    if curl -sf -m 2 "http://127.0.0.1:$RIG_CDP_PORT/json/version" >/dev/null 2>&1; then
      log "FAILED: port $RIG_CDP_PORT is already serving CDP for a browser that is not ours."
      log "        Set QA_RIG_CDP_PORT to a free port and retry."
      exit 2
    fi
    local chrome; chrome="$(command -v google-chrome || command -v google-chrome-stable || command -v chromium || true)"
    [[ -n "$chrome" ]] || { log "FAILED: no chrome binary found"; exit 2; }
    log "starting headed Chrome on $RIG_DISPLAY, CDP :$RIG_CDP_PORT"
    # --ozone-platform=x11 is load-bearing: this session is a Wayland desktop, and without it
    # Chrome ignores DISPLAY and lands on the user's real screen instead of the rig's.
    DISPLAY="$RIG_DISPLAY" setsid $(_taskset_prefix) "$chrome" \
      --ozone-platform=x11 --no-sandbox --disable-gpu --disable-dev-shm-usage \
      --no-first-run --no-default-browser-check --disable-background-networking --disable-sync \
      --remote-debugging-port="$RIG_CDP_PORT" --user-data-dir="$CHROME_PROFILE" \
      --window-position=0,0 --window-size="${RIG_SCREEN%x*}" about:blank \
      >"$RIG_HOME/chrome.log" 2>&1 </dev/null &
    for _ in $(seq 1 20); do
      curl -sf -m 2 "http://127.0.0.1:$RIG_CDP_PORT/json/version" >/dev/null 2>&1 && break
      sleep 1
    done
    cdp_is_ours || { log "FAILED: rig Chrome did not come up (see $RIG_HOME/chrome.log)"; exit 2; }
  fi
  cat >"$STATE" <<EOF
QA_RIG_HOME=$RIG_HOME
QA_RIG_DISPLAY=$RIG_DISPLAY
QA_RIG_CDP=http://127.0.0.1:$RIG_CDP_PORT
QA_RIG_XDOTOOL=$XDOTOOL
QA_RIG_XLIBS=$XLIBS
EOF
  log "up — display $RIG_DISPLAY, CDP http://127.0.0.1:$RIG_CDP_PORT, state $STATE"
}

status() {
  local x c; x="$(xvfb_pid || true)"; c="$(chrome_pid || true)"
  printf 'Xvfb(%s): %s\nChrome(CDP :%s): %s\nstate: %s\n' \
    "$RIG_DISPLAY" "${x:-down}" "$RIG_CDP_PORT" "${c:-down}" "$([[ -r $STATE ]] && echo "$STATE" || echo none)"
  [[ -n "$x" && -n "$c" ]]
}

down() {
  local c x; c="$(chrome_pid || true)"; x="$(xvfb_pid || true)"
  [[ -n "$c" ]] && { kill "$c" 2>/dev/null || true; sleep 1; }
  [[ -n "$x" ]] && { kill "$x" 2>/dev/null || true; }
  rm -f "$STATE"
  log "down"
}

case "${1:-up}" in
  up) up ;;
  down) down ;;
  status) status ;;
  env) [[ -r "$STATE" ]] && cat "$STATE" || { log "rig is down"; exit 1; } ;;
  *) log "usage: xrig.sh [up|down|status|env]"; exit 2 ;;
esac
