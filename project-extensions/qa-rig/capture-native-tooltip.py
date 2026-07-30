#!/usr/bin/env python3
"""capture-native-tooltip.py — photograph a native HTML `title` tooltip (tapeology QA rig).

WHY: CDP screenshots (headless Chrome, Playwright, the framework's browser lanes) capture the web
contents surface only. Chrome draws a native `title` tooltip as a SEPARATE X window owned by the
browser process, so it is absent from every such screenshot no matter how long you hover. This
tool drives the owner-approved headed rig (project-extensions/qa-rig/xrig.sh) instead: it hovers
with the REAL X pointer and grabs the X screen, tooltip window included.

Evidence discipline (this is a T-10 artifact, so it must not be able to lie):
  * the hovered element's own `title` attribute is read from the DOM and printed verbatim, and a
    required substring must be present — otherwise exit 4 and write nothing;
  * the tooltip must actually appear as a NEW X window while hovering — otherwise exit 3 and write
    nothing. A blank or tooltip-less frame can therefore never be reported as a successful capture;
  * the tooltip window's geometry is reported and used for an optional zoomed crop, so a reviewer
    can see the popup at reading size next to the full-page frame.

Usage (rig must be up):
  python3 project-extensions/qa-rig/capture-native-tooltip.py \
      --url http://localhost:3301/desk \
      --hover-selector '[data-testid="desk-row-drill-in"]' \
      --require-title 'bands by class' \
      --out reports/qa/<iter>-evidence/J-14-tooltip.png \
      --crop-out reports/qa/<iter>-evidence/J-14-tooltip-crop.png

Prints one JSON object on stdout. Exit: 0 ok · 2 bad args/rig down · 3 no tooltip window ·
4 no element carrying the required title.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEFAULT_STATE = os.path.join(os.environ.get("QA_RIG_HOME", os.path.expanduser("~/.cache/tapeology-qa-rig")), "state.env")


def die(code: int, msg: str) -> None:
    print(json.dumps({"ok": False, "error": msg}), flush=True)
    sys.exit(code)


def read_state(path: str) -> dict:
    if not os.path.isfile(path):
        die(2, f"rig state file not found at {path} — run project-extensions/qa-rig/xrig.sh up first")
    state = {}
    with open(path) as fh:
        for line in fh:
            if "=" in line:
                k, v = line.strip().split("=", 1)
                state[k] = v
    return state


class X:
    """Thin wrapper over the rig's user-space xdotool + Pillow's XCB grabber."""

    def __init__(self, display: str, xdotool: str, xlibs: str):
        self.display = display
        self.xdotool = xdotool
        self.env = dict(os.environ, DISPLAY=display, LD_LIBRARY_PATH=xlibs)

    def _run(self, *args: str) -> str:
        return subprocess.run([self.xdotool, *args], env=self.env,
                              capture_output=True, text=True, check=False).stdout

    def move(self, x: float, y: float) -> None:
        subprocess.run([self.xdotool, "mousemove", str(int(x)), str(int(y))],
                       env=self.env, check=True)

    def windows(self) -> dict:
        out = {}
        for wid in self._run("search", "--onlyvisible", "--name", "").split():
            geom = {}
            for line in self._run("getwindowgeometry", "--shell", wid).splitlines():
                if "=" in line:
                    k, v = line.split("=", 1)
                    geom[k.strip().lower()] = v.strip()
            out[wid] = geom
        return out

    def grab(self):
        from PIL import ImageGrab
        return ImageGrab.grab(xdisplay=self.display)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True)
    ap.add_argument("--hover-selector", required=True,
                    help="CSS selector for the element carrying the native title")
    ap.add_argument("--require-title", default="",
                    help="substring the hovered element's title MUST contain (evidence guard)")
    ap.add_argument("--nth", type=int, default=-1,
                    help="hover this match index; default -1 = first match satisfying --require-title")
    ap.add_argument("--out", required=True, help="full-screen PNG path")
    ap.add_argument("--crop-out", default="", help="optional zoomed crop of the tooltip window")
    ap.add_argument("--state", default=DEFAULT_STATE)
    ap.add_argument("--hover-settle", type=float, default=2.5, help="seconds to wait for the tooltip")
    ap.add_argument("--scan-limit", type=int, default=40, help="max elements to scan for the title")
    args = ap.parse_args()

    state = read_state(args.state)
    display = state.get("QA_RIG_DISPLAY", ":99")
    cdp = state.get("QA_RIG_CDP", "http://127.0.0.1:9333")
    x = X(display, state["QA_RIG_XDOTOOL"], state.get("QA_RIG_XLIBS", ""))

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        die(2, "playwright is not importable by this python3 — python3 -m pip install --user playwright")

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(cdp)
        ctx = browser.contexts[0]
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        # Playwright applies a device-metrics override on attach; that decouples the layout viewport
        # from the real window and makes every screen-coordinate computation below wrong.
        ctx.new_cdp_session(page).send("Emulation.clearDeviceMetricsOverride")
        page.goto(args.url, wait_until="networkidle", timeout=90_000)
        page.wait_for_selector(args.hover_selector, timeout=90_000)

        loc = page.locator(args.hover_selector)
        count = loc.count()
        target = index = title = None
        if args.nth >= 0:
            index = args.nth
            target = loc.nth(index)
            title = target.get_attribute("title") or ""
            if args.require_title and args.require_title not in title:
                die(4, f"element #{index} title does not contain {args.require_title!r}")
        else:
            for i in range(min(count, args.scan_limit)):
                t = loc.nth(i).get_attribute("title") or ""
                if not args.require_title or args.require_title in t:
                    target, index, title = loc.nth(i), i, t
                    break
            if target is None:
                die(4, f"no element among {min(count, args.scan_limit)} matches carries "
                       f"a title containing {args.require_title!r}")

        target.scroll_into_view_if_needed()
        time.sleep(0.4)
        metrics = page.evaluate(
            "() => ({sx: window.screenX, sy: window.screenY, ow: window.outerWidth,"
            " oh: window.outerHeight, iw: window.innerWidth, ih: window.innerHeight})")
        box = target.bounding_box()
        if not box:
            die(4, "hover target has no bounding box (not rendered)")
        # Viewport origin on the X screen: horizontal window border is split evenly, the vertical
        # difference is the browser chrome above the contents (no window manager on the rig, so
        # there is no title bar to account for).
        origin_x = metrics["sx"] + (metrics["ow"] - metrics["iw"]) / 2
        origin_y = metrics["sy"] + (metrics["oh"] - metrics["ih"])
        px = origin_x + box["x"] + box["width"] / 2
        py = origin_y + box["y"] + box["height"] / 2

        x.move(5, 5)                      # park the pointer, then baseline the window list
        time.sleep(0.8)
        before = x.windows()
        x.move(px - 30, py - 10)          # two moves: Chrome shows tooltips on real motion
        time.sleep(0.25)
        x.move(px, py)
        time.sleep(args.hover_settle)
        after = x.windows()

        new = [(wid, g) for wid, g in after.items() if wid not in before]
        if not new:
            die(3, "no tooltip window appeared while hovering — nothing captured")
        wid, geom = max(new, key=lambda kv: int(kv[1].get("width", 0)) * int(kv[1].get("height", 0)))
        tip = {k: int(geom.get(k, 0)) for k in ("x", "y", "width", "height")}

        img = x.grab()
        os.makedirs(os.path.dirname(os.path.abspath(args.out)) or ".", exist_ok=True)
        img.save(args.out)
        crop_path = ""
        if args.crop_out:
            pad = 24
            left, top = max(tip["x"] - pad, 0), max(tip["y"] - pad, 0)
            right = min(tip["x"] + tip["width"] + pad, img.width)
            bottom = min(tip["y"] + tip["height"] + pad, img.height)
            os.makedirs(os.path.dirname(os.path.abspath(args.crop_out)) or ".", exist_ok=True)
            img.crop((left, top, right, bottom)).save(args.crop_out)
            crop_path = args.crop_out

    print(json.dumps({
        "ok": True,
        "url": args.url,
        "selector": args.hover_selector,
        "matched_index": index,
        "matched_of": count,
        "title": title,
        "tooltip_window": {"id": wid, **tip},
        "pointer": {"x": int(px), "y": int(py)},
        "screenshot": args.out,
        "crop": crop_path,
        "display": display,
    }, indent=2), flush=True)


if __name__ == "__main__":
    main()
