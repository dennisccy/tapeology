# goal-fast_wall-iter-6 — Implementation Summary

**Phase:** goal-fast_wall-iter-6
**Date:** 2026-07-17
**Written by:** developer

---

## Features Implemented

- **A backend restart no longer re-pays the multi-minute "Case Studies" scan.** The touch-event scan
  behind the `/structure` page's Case Studies panel and the `/studies` page (the process that walks
  every stored 5-minute bar looking for price touches against the tradable levels) now saves its
  result to a small file on disk the moment it finishes, in addition to remembering it in memory.
  Restarting the backend server used to throw that memory away and force the whole multi-minute scan
  to run again on the very next page visit; now it reads the saved result instantly instead.
- **The saved result recognizes "the same question," not "the same object in memory."** Previously
  the in-memory shortcut only worked if the exact same internal settings object was reused
  byte-for-byte in computer memory — a technical quirk invisible to any user, but one that made the
  shortcut fragile. It now recognizes "the same settings and the same recorded price data" regardless
  of how that request was constructed internally, so the shortcut works reliably every time the
  underlying data and settings genuinely haven't changed.

---

## Changed Behavior

- **Case Studies / `/studies` scan speed after a restart**: Previously, every backend restart meant
  the next visit to `/structure` or `/studies` re-ran the full scan from scratch (multi-minute on the
  real, populated data set). Now the saved result from before the restart is reused instantly, and
  the scan only re-runs for real when the underlying recorded price data or the relevant settings
  actually change.

---

## Backend-Only Items

- None. This iteration is entirely an internal speed/reliability improvement to an existing
  computation — it changes nothing about what the Case Studies list, `/structure`, or `/studies` show
  or how a user interacts with them. There is no new endpoint, button, or setting to wire up.

---

## Incomplete Items

- None from this iteration's scope. All items from the phase spec's Definition of Done were
  completed and verified (see the dev handoff for the full evidence list).

---

## Config and Environment Changes

- `TAPEOLOGY_SETUPS_CACHE_DB` (new, optional) — points the new saved-result file to a specific
  location. If not set, it defaults to a file placed automatically next to the existing recorded-bars
  folder (mirrors how the project's other saved-result files already default their own location) —
  no action is required from an operator; the default just works.
- No other settings changed. No existing configuration value moved or was renamed. The project's
  internal "configuration fingerprint" (a technical checksum proving nothing about how existing
  numbers are calculated has shifted) is confirmed unchanged.

---

## Known Limitations

- This iteration's saved-result file is purely a rebuildable convenience — deleting it at any time is
  completely safe and costs nothing more than one slower scan on the very next request; no data is
  ever lost, and nothing about the actual displayed numbers can be affected by it.
- The visible speed improvement is only noticeable on the real, populated dataset (many recorded
  symbols/sessions) after a restart. On a freshly-set-up or mostly-empty system the scan is already
  fast, so there is nothing new to observe there — this was confirmed directly by browser-checking a
  deliberately empty test setup, which correctly still showed the same "no events yet" message as
  before, with no visual change anywhere on the page.
- No new button, panel, or setting was added anywhere in the product. If you view `/structure` or
  `/studies` today versus before this change, they should look and behave identically — the only
  difference is how quickly a restarted backend gets back up to speed.
