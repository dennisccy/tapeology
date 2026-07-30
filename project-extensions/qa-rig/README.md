# QA rig — headed capture (owner-approved 2026-07-30)

Photographs things a headless screenshot structurally cannot see: **native browser UI drawn
outside the web-contents surface**, above all native HTML `title` tooltips.

## Why this exists

Era-B journey **J-14** requires "one screenshot of a row tooltip carrying its `bands_by_class`
line". That hint is a native `title` attribute on the ranked row's drill-in anchor
(`apps/frontend/app/desk/page.tsx:346`). Chrome renders native tooltips as a **separate X window
owned by the browser process**, so CDP's `Page.captureScreenshot` — the mechanism behind every
headless screenshot, Playwright's included — never contains it, no matter how long you hover.

Three goal-mode iterations (19, 20, 21) tried and failed; the session halted `STALLED` asking the
owner to choose between rewording the clause, adding an on-page panel, approving a headed capture
rig, or accepting the gap. **The owner approved the rig** (2026-07-30). The acceptance bar is
unchanged — a screenshot is still required, T-10 still says *no screenshot ⇒ `unknown`, never
`passing`*. This is only the sanctioned way to take it.

## What it is

* **Its own X server.** `Xvfb` on `:99` — the user's real desktop is never captured, and nothing
  the rig does can appear on it.
* **A real headed Chrome** on that display, with CDP on a private port (`9333`, deliberately not
  `9222`/`9223`, which the Chrome-MCP server and the framework's browser lanes already own).
* **A real pointer.** `xdotool` moves the X pointer onto the element, which is what makes Chrome
  raise the tooltip; a synthesized CDP hover is not enough for a screen-level capture.
* **An X-level grab.** Pillow's XCB grabber photographs the whole display, tooltip window included.

No system packages and no `sudo`: `Xvfb`/`xdotool` are `apt-get download`ed and `dpkg -x`-extracted
into `~/.cache/tapeology-qa-rig/prefix` on first use. Removing that directory removes the rig.

## Use

```bash
./project-extensions/qa-rig/xrig.sh up            # first run also fetches the tools (~1 MB)

python3 project-extensions/qa-rig/capture-native-tooltip.py \
  --url http://localhost:3301/desk \
  --hover-selector '[data-testid="desk-row-drill-in"]' \
  --require-title 'bands by class' \
  --out      reports/qa/<iter>-evidence/J-14-tooltip.png \
  --crop-out reports/qa/<iter>-evidence/J-14-tooltip-crop.png

./project-extensions/qa-rig/xrig.sh down          # when the pass is finished
```

The capture prints one JSON object: the hovered element's full `title` text, the tooltip window's
id and geometry, the pointer position, and the paths written. Quote the `title` in the QA report —
it is the string the photographed popup is rendering.

`--crop-out` writes a zoomed crop of exactly the tooltip window (padded), so a reviewer can read
the line at size instead of hunting for it in a 1600×1200 frame. Provide both.

## It cannot report a false positive

| Guard | Behaviour | Exit |
|---|---|---|
| No element carries a `title` containing `--require-title` | nothing written | `4` |
| No new X window appeared while hovering (i.e. no tooltip rendered) | nothing written | `3` |
| Rig down / state file missing / Playwright missing | nothing written | `2` |
| Tooltip photographed | full frame + optional crop written | `0` |

Verified 2026-07-30: a bogus `--require-title` exits 4, hovering a `<h1>` (no `title`) exits 3,
the real selector exits 0 — and only the passing run left a PNG on disk.

## Knobs

`QA_RIG_HOME` (default `~/.cache/tapeology-qa-rig`) · `QA_RIG_DISPLAY` (`:99`) ·
`QA_RIG_CDP_PORT` (`9333`) · `QA_RIG_SCREEN` (`1600x1200x24`).

`xrig.sh up` refuses to start if the CDP port already answers for a browser that is not the rig's —
attaching to the wrong Chrome is precisely how the first prototype produced a black screenshot.

## Notes for goal-mode lanes

* The rig is **additive**. Ordinary browser QA keeps running exactly as it does today; reach for
  the rig only for an acceptance line that names native browser UI.
* Chrome is pinned to the host-guard CPU mask (`project-extensions/host-guard/host-guard.env`)
  when the project declares one — a rig browser is a burst source like any other.
* Start the app first (`scripts/start-backend.sh`, `scripts/start-frontend.sh`); the rig drives a
  browser, it does not manage your services.
