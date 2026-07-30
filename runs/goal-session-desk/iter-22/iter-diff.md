# Iteration diff (bounded)

Files changed: 3. Shown in full: 3.

```diff
diff --git a/project-extensions/qa-rig/README.md b/project-extensions/qa-rig/README.md
new file mode 100644
index 0000000..56d45a9
--- /dev/null
+++ b/project-extensions/qa-rig/README.md
@@ -0,0 +1,82 @@
+# QA rig — headed capture (owner-approved 2026-07-30)
+
+Photographs things a headless screenshot structurally cannot see: **native browser UI drawn
+outside the web-contents surface**, above all native HTML `title` tooltips.
+
+## Why this exists
+
+Era-B journey **J-14** requires "one screenshot of a row tooltip carrying its `bands_by_class`
+line". That hint is a native `title` attribute on the ranked row's drill-in anchor
+(`apps/frontend/app/desk/page.tsx:346`). Chrome renders native tooltips as a **separate X window
+owned by the browser process**, so CDP's `Page.captureScreenshot` — the mechanism behind every
+headless screenshot, Playwright's included — never contains it, no matter how long you hover.
+
+Three goal-mode iterations (19, 20, 21) tried and failed; the session halted `STALLED` asking the
+owner to choose between rewording the clause, adding an on-page panel, approving a headed capture
+rig, or accepting the gap. **The owner approved the rig** (2026-07-30). The acceptance bar is
+unchanged — a screenshot is still required, T-10 still says *no screenshot ⇒ `unknown`, never
+`passing`*. This is only the sanctioned way to take it.
+
+## What it is
+
+* **Its own X server.** `Xvfb` on `:99` — the user's real desktop is never captured, and nothing
+  the rig does can appear on it.
+* **A real headed Chrome** on that display, with CDP on a private port (`9333`, deliberately not
+  `9222`/`9223`, which the Chrome-MCP server and the framework's browser lanes already own).
+* **A real pointer.** `xdotool` moves the X pointer onto the element, which is what makes Chrome
+  raise the tooltip; a synthesized CDP hover is not enough for a screen-level capture.
+* **An X-level grab.** Pillow's XCB grabber photographs the whole display, tooltip window included.
+
+No system packages and no `sudo`: `Xvfb`/`xdotool` are `apt-get download`ed and `dpkg -x`-extracted
+into `~/.cache/tapeology-qa-rig/prefix` on first use. Removing that directory removes the rig.
+
+## Use
+
+```bash
+./project-extensions/qa-rig/xrig.sh up            # first run also fetches the tools (~1 MB)
+
+python3 project-extensions/qa-rig/capture-native-tooltip.py \
+  --url http://localhost:3301/desk \
+  --hover-selector '[data-testid="desk-row-drill-in"]' \
+  --require-title 'bands by class' \
+  --out      reports/qa/<iter>-evidence/J-14-tooltip.png \
+  --crop-out reports/qa/<iter>-evidence/J-14-tooltip-crop.png
+
+./project-extensions/qa-rig/xrig.sh down          # when the pass is finished
+```
+
+The capture prints one JSON object: the hovered element's full `title` text, the tooltip window's
+id and geometry, the pointer position, and the paths written. Quote the `title` in the QA report —
+it is the string the photographed popup is rendering.
+
+`--crop-out` writes a zoomed crop of exactly the tooltip window (padded), so a reviewer can read
+the line at size instead of hunting for it in a 1600×1200 frame. Provide both.
+
+## It cannot report a false positive
+
+| Guard | Behaviour | Exit |
+|---|---|---|
+| No element carries a `title` containing `--require-title` | nothing written | `4` |
+| No new X window appeared while hovering (i.e. no tooltip rendered) | nothing written | `3` |
+| Rig down / state file missing / Playwright missing | nothing written | `2` |
+| Tooltip photographed | full frame + optional crop written | `0` |
+
+Verified 2026-07-30: a bogus `--require-title` exits 4, hovering a `<h1>` (no `title`) exits 3,
+the real selector exits 0 — and only the passing run left a PNG on disk.
+
+## Knobs
+
+`QA_RIG_HOME` (default `~/.cache/tapeology-qa-rig`) · `QA_RIG_DISPLAY` (`:99`) ·
+`QA_RIG_CDP_PORT` (`9333`) · `QA_RIG_SCREEN` (`1600x1200x24`).
+
+`xrig.sh up` refuses to start if the CDP port already answers for a browser that is not the rig's —
+attaching to the wrong Chrome is precisely how the first prototype produced a black screenshot.
+
+## Notes for goal-mode lanes
+
+* The rig is **additive**. Ordinary browser QA keeps running exactly as it does today; reach for
+  the rig only for an acceptance line that names native browser UI.
+* Chrome is pinned to the host-guard CPU mask (`project-extensions/host-guard/host-guard.env`)
+  when the project declares one — a rig browser is a burst source like any other.
+* Start the app first (`scripts/start-backend.sh`, `scripts/start-frontend.sh`); the rig drives a
+  browser, it does not manage your services.
diff --git a/project-extensions/qa-rig/capture-native-tooltip.py b/project-extensions/qa-rig/capture-native-tooltip.py
new file mode 100755
index 0000000..a33f34e
--- /dev/null
+++ b/project-extensions/qa-rig/capture-native-tooltip.py
@@ -0,0 +1,206 @@
+#!/usr/bin/env python3
+"""capture-native-tooltip.py — photograph a native HTML `title` tooltip (tapeology QA rig).
+
+WHY: CDP screenshots (headless Chrome, Playwright, the framework's browser lanes) capture the web
+contents surface only. Chrome draws a native `title` tooltip as a SEPARATE X window owned by the
+browser process, so it is absent from every such screenshot no matter how long you hover. This
+tool drives the owner-approved headed rig (project-extensions/qa-rig/xrig.sh) instead: it hovers
+with the REAL X pointer and grabs the X screen, tooltip window included.
+
+Evidence discipline (this is a T-10 artifact, so it must not be able to lie):
+  * the hovered element's own `title` attribute is read from the DOM and printed verbatim, and a
+    required substring must be present — otherwise exit 4 and write nothing;
+  * the tooltip must actually appear as a NEW X window while hovering — otherwise exit 3 and write
+    nothing. A blank or tooltip-less frame can therefore never be reported as a successful capture;
+  * the tooltip window's geometry is reported and used for an optional zoomed crop, so a reviewer
+    can see the popup at reading size next to the full-page frame.
+
+Usage (rig must be up):
+  python3 project-extensions/qa-rig/capture-native-tooltip.py \
+      --url http://localhost:3301/desk \
+      --hover-selector '[data-testid="desk-row-drill-in"]' \
+      --require-title 'bands by class' \
+      --out reports/qa/<iter>-evidence/J-14-tooltip.png \
+      --crop-out reports/qa/<iter>-evidence/J-14-tooltip-crop.png
+
+Prints one JSON object on stdout. Exit: 0 ok · 2 bad args/rig down · 3 no tooltip window ·
+4 no element carrying the required title.
+"""
+from __future__ import annotations
+
+import argparse
+import json
+import os
+import subprocess
+import sys
+import time
+
+REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
+DEFAULT_STATE = os.path.join(os.environ.get("QA_RIG_HOME", os.path.expanduser("~/.cache/tapeology-qa-rig")), "state.env")
+
+
+def die(code: int, msg: str) -> None:
+    print(json.dumps({"ok": False, "error": msg}), flush=True)
+    sys.exit(code)
+
+
+def read_state(path: str) -> dict:
+    if not os.path.isfile(path):
+        die(2, f"rig state file not found at {path} — run project-extensions/qa-rig/xrig.sh up first")
+    state = {}
+    with open(path) as fh:
+        for line in fh:
+            if "=" in line:
+                k, v = line.strip().split("=", 1)
+                state[k] = v
+    return state
+
+
+class X:
+    """Thin wrapper over the rig's user-space xdotool + Pillow's XCB grabber."""
+
+    def __init__(self, display: str, xdotool: str, xlibs: str):
+        self.display = display
+        self.xdotool = xdotool
+        self.env = dict(os.environ, DISPLAY=display, LD_LIBRARY_PATH=xlibs)
+
+    def _run(self, *args: str) -> str:
+        return subprocess.run([self.xdotool, *args], env=self.env,
+                              capture_output=True, text=True, check=False).stdout
+
+    def move(self, x: float, y: float) -> None:
+        subprocess.run([self.xdotool, "mousemove", str(int(x)), str(int(y))],
+                       env=self.env, check=True)
+
+    def windows(self) -> dict:
+        out = {}
+        for wid in self._run("search", "--onlyvisible", "--name", "").split():
+            geom = {}
+            for line in self._run("getwindowgeometry", "--shell", wid).splitlines():
+                if "=" in line:
+                    k, v = line.split("=", 1)
+                    geom[k.strip().lower()] = v.strip()
+            out[wid] = geom
+        return out
+
+    def grab(self):
+        from PIL import ImageGrab
+        return ImageGrab.grab(xdisplay=self.display)
+
+
+def main() -> None:
+    ap = argparse.ArgumentParser()
+    ap.add_argument("--url", required=True)
+    ap.add_argument("--hover-selector", required=True,
+                    help="CSS selector for the element carrying the native title")
+    ap.add_argument("--require-title", default="",
+                    help="substring the hovered element's title MUST contain (evidence guard)")
+    ap.add_argument("--nth", type=int, default=-1,
+                    help="hover this match index; default -1 = first match satisfying --require-title")
+    ap.add_argument("--out", required=True, help="full-screen PNG path")
+    ap.add_argument("--crop-out", default="", help="optional zoomed crop of the tooltip window")
+    ap.add_argument("--state", default=DEFAULT_STATE)
+    ap.add_argument("--hover-settle", type=float, default=2.5, help="seconds to wait for the tooltip")
+    ap.add_argument("--scan-limit", type=int, default=40, help="max elements to scan for the title")
+    args = ap.parse_args()
+
+    state = read_state(args.state)
+    display = state.get("QA_RIG_DISPLAY", ":99")
+    cdp = state.get("QA_RIG_CDP", "http://127.0.0.1:9333")
+    x = X(display, state["QA_RIG_XDOTOOL"], state.get("QA_RIG_XLIBS", ""))
+
+    try:
+        from playwright.sync_api import sync_playwright
+    except ImportError:
+        die(2, "playwright is not importable by this python3 — python3 -m pip install --user playwright")
+
+    with sync_playwright() as p:
+        browser = p.chromium.connect_over_cdp(cdp)
+        ctx = browser.contexts[0]
+        page = ctx.pages[0] if ctx.pages else ctx.new_page()
+        # Playwright applies a device-metrics override on attach; that decouples the layout viewport
+        # from the real window and makes every screen-coordinate computation below wrong.
+        ctx.new_cdp_session(page).send("Emulation.clearDeviceMetricsOverride")
+        page.goto(args.url, wait_until="networkidle", timeout=90_000)
+        page.wait_for_selector(args.hover_selector, timeout=90_000)
+
+        loc = page.locator(args.hover_selector)
+        count = loc.count()
+        target = index = title = None
+        if args.nth >= 0:
+            index = args.nth
+            target = loc.nth(index)
+            title = target.get_attribute("title") or ""
+            if args.require_title and args.require_title not in title:
+                die(4, f"element #{index} title does not contain {args.require_title!r}")
+        else:
+            for i in range(min(count, args.scan_limit)):
+                t = loc.nth(i).get_attribute("title") or ""
+                if not args.require_title or args.require_title in t:
+                    target, index, title = loc.nth(i), i, t
+                    break
+            if target is None:
+                die(4, f"no element among {min(count, args.scan_limit)} matches carries "
+                       f"a title containing {args.require_title!r}")
+
+        target.scroll_into_view_if_needed()
+        time.sleep(0.4)
+        metrics = page.evaluate(
+            "() => ({sx: window.screenX, sy: window.screenY, ow: window.outerWidth,"
+            " oh: window.outerHeight, iw: window.innerWidth, ih: window.innerHeight})")
+        box = target.bounding_box()
+        if not box:
+            die(4, "hover target has no bounding box (not rendered)")
+        # Viewport origin on the X screen: horizontal window border is split evenly, the vertical
+        # difference is the browser chrome above the contents (no window manager on the rig, so
+        # there is no title bar to account for).
+        origin_x = metrics["sx"] + (metrics["ow"] - metrics["iw"]) / 2
+        origin_y = metrics["sy"] + (metrics["oh"] - metrics["ih"])
+        px = origin_x + box["x"] + box["width"] / 2
+        py = origin_y + box["y"] + box["height"] / 2
+
+        x.move(5, 5)                      # park the pointer, then baseline the window list
+        time.sleep(0.8)
+        before = x.windows()
+        x.move(px - 30, py - 10)          # two moves: Chrome shows tooltips on real motion
+        time.sleep(0.25)
+        x.move(px, py)
+        time.sleep(args.hover_settle)
+        after = x.windows()
+
+        new = [(wid, g) for wid, g in after.items() if wid not in before]
+        if not new:
+            die(3, "no tooltip window appeared while hovering — nothing captured")
+        wid, geom = max(new, key=lambda kv: int(kv[1].get("width", 0)) * int(kv[1].get("height", 0)))
+        tip = {k: int(geom.get(k, 0)) for k in ("x", "y", "width", "height")}
+
+        img = x.grab()
+        os.makedirs(os.path.dirname(os.path.abspath(args.out)) or ".", exist_ok=True)
+        img.save(args.out)
+        crop_path = ""
+        if args.crop_out:
+            pad = 24
+            left, top = max(tip["x"] - pad, 0), max(tip["y"] - pad, 0)
+            right = min(tip["x"] + tip["width"] + pad, img.width)
+            bottom = min(tip["y"] + tip["height"] + pad, img.height)
+            os.makedirs(os.path.dirname(os.path.abspath(args.crop_out)) or ".", exist_ok=True)
+            img.crop((left, top, right, bottom)).save(args.crop_out)
+            crop_path = args.crop_out
+
+    print(json.dumps({
+        "ok": True,
+        "url": args.url,
+        "selector": args.hover_selector,
+        "matched_index": index,
+        "matched_of": count,
+        "title": title,
+        "tooltip_window": {"id": wid, **tip},
+        "pointer": {"x": int(px), "y": int(py)},
+        "screenshot": args.out,
+        "crop": crop_path,
+        "display": display,
+    }, indent=2), flush=True)
+
+
+if __name__ == "__main__":
+    main()
diff --git a/project-extensions/qa-rig/xrig.sh b/project-extensions/qa-rig/xrig.sh
new file mode 100755
index 0000000..00c8134
--- /dev/null
+++ b/project-extensions/qa-rig/xrig.sh
@@ -0,0 +1,146 @@
+#!/usr/bin/env bash
+# xrig.sh — the owner-approved HEADED capture rig (tapeology, approved 2026-07-30).
+#
+# WHY THIS EXISTS: goal.md's T-10 demands a SCREENSHOT for browser acceptance lines, and era-B
+# J-14 needs a photograph of a ranked row's drill-in tooltip carrying its `bands_by_class` line.
+# That hint is a native HTML `title` (apps/frontend/app/desk/page.tsx:346). Chrome draws native
+# tooltips as a SEPARATE X window owned by the browser process — outside the web-contents surface
+# that CDP's `Page.captureScreenshot` (and therefore every headless screenshot, Playwright's
+# included) can see. Three goal-mode iterations (19, 20, 21) burned on this and the session halted
+# STALLED asking the owner to choose. The owner chose "approve a headed/desktop capture rig".
+#
+# WHAT IT IS: a throwaway X server (Xvfb) + a real headed Chrome on it + an X-level screen grab.
+# Nothing is installed system-wide and no sudo is used: the two X tools are `apt-get download`ed
+# and `dpkg -x`-extracted into a user-owned prefix. The user's real desktop is NEVER captured —
+# the rig owns its own display, so the grab contains only the rig's browser.
+#
+# CONTRACT: this script only starts/stops/reports. The capture itself lives in
+# capture-native-tooltip.py, which reads the state file this script writes.
+#
+#   ./project-extensions/qa-rig/xrig.sh up       # ensure tools, Xvfb + headed Chrome are running
+#   ./project-extensions/qa-rig/xrig.sh status   # print state (exit 0 = up, 1 = down)
+#   ./project-extensions/qa-rig/xrig.sh env      # print the state file (eval-able)
+#   ./project-extensions/qa-rig/xrig.sh down     # stop Chrome + Xvfb (tools/prefix are kept)
+#
+# Knobs (env): QA_RIG_HOME (default ~/.cache/tapeology-qa-rig), QA_RIG_DISPLAY (default :99),
+# QA_RIG_CDP_PORT (default 9333 — deliberately NOT 9222/9223, which the superpowers-chrome MCP
+# server and framework browser lanes already use; colliding there silently attaches the capture
+# to the WRONG Chrome, which is exactly how the first prototype of this rig produced a black
+# screenshot), QA_RIG_SCREEN (default 1600x1200x24).
+set -euo pipefail
+
+REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
+RIG_HOME="${QA_RIG_HOME:-$HOME/.cache/tapeology-qa-rig}"
+RIG_DISPLAY="${QA_RIG_DISPLAY:-:99}"
+RIG_CDP_PORT="${QA_RIG_CDP_PORT:-9333}"
+RIG_SCREEN="${QA_RIG_SCREEN:-1600x1200x24}"
+PREFIX="$RIG_HOME/prefix"
+STATE="$RIG_HOME/state.env"
+XVFB="$PREFIX/usr/bin/Xvfb"
+XDOTOOL="$PREFIX/usr/bin/xdotool"
+XLIBS="$PREFIX/usr/lib/x86_64-linux-gnu"
+CHROME_PROFILE="$RIG_HOME/chrome-profile"
+
+log() { printf '[xrig] %s\n' "$*" >&2; }
+
+# The host-guard mask (project-extensions/host-guard/host-guard.env) exists because unguarded
+# all-core bursts have hard-reset this machine. A rig browser is a burst source like any other,
+# so pin it to the same mask when the project declares one.
+_taskset_prefix() {
+  local hg="$REPO_ROOT/project-extensions/host-guard/host-guard.env"
+  [[ -r "$hg" ]] || return 0
+  # shellcheck disable=SC1090
+  local mask; mask="$(. "$hg" >/dev/null 2>&1; printf '%s' "${HOST_GUARD_CPU_LIST:-}")"
+  [[ -n "$mask" ]] && command -v taskset >/dev/null 2>&1 && printf 'taskset -c %s' "$mask"
+}
+
+ensure_tools() {
+  [[ -x "$XVFB" && -x "$XDOTOOL" ]] && return 0
+  log "fetching Xvfb + xdotool into $PREFIX (user-space, no sudo, no system install)"
+  mkdir -p "$RIG_HOME/debs" "$PREFIX"
+  ( cd "$RIG_HOME/debs" && apt-get download xvfb xdotool libxdo3 >/dev/null )
+  for d in "$RIG_HOME"/debs/*.deb; do dpkg -x "$d" "$PREFIX"; done
+  [[ -x "$XVFB" && -x "$XDOTOOL" ]] || { log "FAILED: tools missing after extraction"; exit 2; }
+  # Fail loudly NOW if a shared library is missing, rather than mid-capture.
+  if LD_LIBRARY_PATH="$XLIBS" ldd "$XDOTOOL" | grep -q "not found"; then
+    log "FAILED: xdotool has unresolved libraries"; exit 2
+  fi
+  log "tools ready"
+}
+
+xvfb_pid() { pgrep -f "Xvfb $RIG_DISPLAY " 2>/dev/null | head -1; }
+chrome_pid() { pgrep -f -- "--user-data-dir=$CHROME_PROFILE" 2>/dev/null | head -1; }
+
+# A CDP port that answers but belongs to somebody else's browser is worse than a dead port: the
+# capture would drive the wrong Chrome. Prove ownership by matching the profile dir.
+cdp_is_ours() {
+  local pid; pid="$(chrome_pid || true)"
+  [[ -n "$pid" ]] || return 1
+  tr '\0' ' ' < "/proc/$pid/cmdline" 2>/dev/null | grep -q -- "--remote-debugging-port=$RIG_CDP_PORT"
+}
+
+up() {
+  ensure_tools
+  mkdir -p "$CHROME_PROFILE"
+  if [[ -z "$(xvfb_pid || true)" ]]; then
+    log "starting Xvfb on $RIG_DISPLAY ($RIG_SCREEN)"
+    setsid "$XVFB" "$RIG_DISPLAY" -screen 0 "$RIG_SCREEN" -nolisten tcp \
+      >"$RIG_HOME/xvfb.log" 2>&1 </dev/null &
+    sleep 2
+    [[ -n "$(xvfb_pid || true)" ]] || { log "FAILED: Xvfb did not start (see $RIG_HOME/xvfb.log)"; exit 2; }
+  fi
+  if ! cdp_is_ours; then
+    if curl -sf -m 2 "http://127.0.0.1:$RIG_CDP_PORT/json/version" >/dev/null 2>&1; then
+      log "FAILED: port $RIG_CDP_PORT is already serving CDP for a browser that is not ours."
+      log "        Set QA_RIG_CDP_PORT to a free port and retry."
+      exit 2
+    fi
+    local chrome; chrome="$(command -v google-chrome || command -v google-chrome-stable || command -v chromium || true)"
+    [[ -n "$chrome" ]] || { log "FAILED: no chrome binary found"; exit 2; }
+    log "starting headed Chrome on $RIG_DISPLAY, CDP :$RIG_CDP_PORT"
+    # --ozone-platform=x11 is load-bearing: this session is a Wayland desktop, and without it
+    # Chrome ignores DISPLAY and lands on the user's real screen instead of the rig's.
+    DISPLAY="$RIG_DISPLAY" setsid $(_taskset_prefix) "$chrome" \
+      --ozone-platform=x11 --no-sandbox --disable-gpu --disable-dev-shm-usage \
+      --no-first-run --no-default-browser-check --disable-background-networking --disable-sync \
+      --remote-debugging-port="$RIG_CDP_PORT" --user-data-dir="$CHROME_PROFILE" \
+      --window-position=0,0 --window-size="${RIG_SCREEN%x*}" about:blank \
+      >"$RIG_HOME/chrome.log" 2>&1 </dev/null &
+    for _ in $(seq 1 20); do
+      curl -sf -m 2 "http://127.0.0.1:$RIG_CDP_PORT/json/version" >/dev/null 2>&1 && break
+      sleep 1
+    done
+    cdp_is_ours || { log "FAILED: rig Chrome did not come up (see $RIG_HOME/chrome.log)"; exit 2; }
+  fi
+  cat >"$STATE" <<EOF
+QA_RIG_HOME=$RIG_HOME
+QA_RIG_DISPLAY=$RIG_DISPLAY
+QA_RIG_CDP=http://127.0.0.1:$RIG_CDP_PORT
+QA_RIG_XDOTOOL=$XDOTOOL
+QA_RIG_XLIBS=$XLIBS
+EOF
+  log "up — display $RIG_DISPLAY, CDP http://127.0.0.1:$RIG_CDP_PORT, state $STATE"
+}
+
+status() {
+  local x c; x="$(xvfb_pid || true)"; c="$(chrome_pid || true)"
+  printf 'Xvfb(%s): %s\nChrome(CDP :%s): %s\nstate: %s\n' \
+    "$RIG_DISPLAY" "${x:-down}" "$RIG_CDP_PORT" "${c:-down}" "$([[ -r $STATE ]] && echo "$STATE" || echo none)"
+  [[ -n "$x" && -n "$c" ]]
+}
+
+down() {
+  local c x; c="$(chrome_pid || true)"; x="$(xvfb_pid || true)"
+  [[ -n "$c" ]] && { kill "$c" 2>/dev/null || true; sleep 1; }
+  [[ -n "$x" ]] && { kill "$x" 2>/dev/null || true; }
+  rm -f "$STATE"
+  log "down"
+}
+
+case "${1:-up}" in
+  up) up ;;
+  down) down ;;
+  status) status ;;
+  env) [[ -r "$STATE" ]] && cat "$STATE" || { log "rig is down"; exit 1; } ;;
+  *) log "usage: xrig.sh [up|down|status|env]"; exit 2 ;;
+esac
```
