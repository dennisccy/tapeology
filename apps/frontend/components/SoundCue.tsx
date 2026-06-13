"use client";

import { useEffect, useRef, useState } from "react";
import type { SoundCueTaxonomy } from "@/lib/types";

// The OPTIONAL sound cue (capability 33 final item, J-66) — the cockpit cue area's last cue-layer
// control. It is an EXPLICIT toggle that is DEFAULT OFF on every fresh load; when enabled it plays a
// brief sound ONLY on a stance/verdict TRANSITION — read VERBATIM from the served row-15/row-25 values
// (the UI derives no stance/verdict of its own) — and respects the served `sound_cue_cooldown_seconds`
// debounce between fires. A small visible fired-indicator (a brief pulse) makes the transition-only +
// cooldown behaviour browser-verifiable WITHOUT audio hardware.
//
// Discipline (the cue-layer anti-goals):
//   * DEFAULT OFF: `enabled` starts false on every mount and is NEVER persisted (no localStorage) —
//     a fresh load is always silent (the OFF-default leg). The toggle state is a CLIENT-LOCAL UI
//     preference; it is never sent to the backend and never stored.
//   * TRANSITION-ONLY: the cue fires only when the served `cueKey` (the verdict + active stance values
//     concatenated) CHANGES to a different value — never on the first value seen, never on a re-render
//     with an unchanged value. The UI reads the served values verbatim; it computes no stance/verdict.
//   * COOLDOWN: after a fire, no second fire until the served cooldown (seconds) has elapsed.
//   * COPY from taxonomy: the toggle label, description, fired-indicator label, and register line are
//     all backend-owned (the frontend hardcodes none) — strictly descriptive (J-66).
//
// The sound itself is a short Web Audio beep generated on the fly (no asset, no new dependency). If the
// browser blocks audio (no user gesture / unsupported), the VISIBLE fired-indicator still fires — the
// transition-only + cooldown behaviour stays verifiable. Color: neutral slate (a UI affordance, not a
// side/impact signal — it must not borrow the green/red/amber palette).

export function SoundCue({
  // The served transition key — the verdict + active-stance values concatenated, read VERBATIM off the
  // projection by the caller (the UI derives nothing). `null`/empty when there is no live verdict yet.
  cueKey,
  // The taxonomy-owned sound-cue block (label / description / register / cooldown). Absent on a
  // pre-J-66 backend ⇒ the toggle renders nothing rather than fabricate copy.
  taxonomy,
}: {
  cueKey: string | null | undefined;
  taxonomy: SoundCueTaxonomy | null | undefined;
}) {
  // DEFAULT OFF on every fresh load — never persisted.
  const [enabled, setEnabled] = useState(false);
  // The visible fired-indicator pulse (a brief on/off so the fire is browser-observable). A monotonic
  // counter drives a key so each fire restarts the CSS pulse even on back-to-back fires.
  const [firedPulse, setFiredPulse] = useState(0);
  // The previously-seen served cueKey (to detect a real transition) and the last-fire wall ms (cooldown).
  const prevCueKey = useRef<string | null | undefined>(undefined);
  const lastFiredMs = useRef<number>(0);

  const cooldownSeconds = taxonomy?.cooldown_seconds ?? 0;

  // Fire on a TRANSITION of the served cueKey while enabled + past the cooldown. Reading the served
  // value verbatim — no client-side stance/verdict derivation.
  useEffect(() => {
    const prev = prevCueKey.current;
    // Always track the latest seen value so a later change is measured against it. The FIRST value seen
    // (prev === undefined) is never a transition — it seeds the baseline.
    prevCueKey.current = cueKey;
    if (!enabled) return; // OFF ⇒ never fires (the absence leg) — but baseline still tracked above.
    if (prev === undefined || cueKey == null || cueKey === "") return; // no baseline / no live value
    if (cueKey === prev) return; // unchanged ⇒ not a transition
    // A real transition. Respect the served cooldown (no second fire within it).
    const now = Date.now();
    if (now - lastFiredMs.current < cooldownSeconds * 1000) return;
    lastFiredMs.current = now;
    setFiredPulse((n) => n + 1);
    playBeep();
  }, [cueKey, enabled, cooldownSeconds]);

  // When the toggle is turned OFF, reset the fire bookkeeping so a later re-enable starts clean (the
  // next transition after re-enabling is measured from the value present at re-enable — never a stale
  // fire). Turning OFF never fires.
  useEffect(() => {
    if (!enabled) {
      lastFiredMs.current = 0;
    }
  }, [enabled]);

  if (!taxonomy) return null; // pre-J-66 backend ⇒ no fabricated copy
  const copy = taxonomy.copy;

  return (
    <div
      data-testid="sound-cue"
      data-enabled={enabled}
      className="mt-3 flex flex-col gap-1.5 border-t border-slate-800 pt-3"
    >
      <div className="flex flex-wrap items-center justify-between gap-2">
        {/* The explicit toggle — a labelled switch, default OFF. Hover/focus/active states included. */}
        <label className="flex cursor-pointer items-center gap-2 text-xs text-slate-400">
          <button
            type="button"
            role="switch"
            aria-checked={enabled}
            data-testid="sound-cue-toggle"
            onClick={() => setEnabled((v) => !v)}
            className={`relative inline-flex h-5 w-9 shrink-0 items-center rounded-full border transition-colors focus:outline-none focus:ring-1 focus:ring-slate-500 ${
              enabled
                ? "border-slate-500 bg-slate-600 hover:bg-slate-500 active:bg-slate-400"
                : "border-slate-700 bg-slate-800 hover:bg-slate-700 active:bg-slate-600"
            }`}
          >
            <span
              aria-hidden
              className={`inline-block h-3.5 w-3.5 transform rounded-full bg-slate-200 transition-transform ${
                enabled ? "translate-x-4" : "translate-x-0.5"
              }`}
            />
          </button>
          <span className="font-medium text-slate-300">{copy.toggle_label}</span>
        </label>

        {/* The fired-indicator — a brief slate pulse shown each time the cue fires, so transition-only
            + cooldown behaviour is verifiable without audio hardware. The `key` restarts the animation
            on each fire. Absent until the first fire. */}
        {firedPulse > 0 && (
          <span
            key={firedPulse}
            data-testid="sound-cue-fired"
            data-fire-count={firedPulse}
            className="sound-cue-pulse rounded-full bg-slate-700 px-2 py-0.5 text-[11px] font-medium uppercase tracking-wider text-slate-200"
          >
            {copy.fired_indicator_label}
          </span>
        )}
      </div>

      {/* The off-by-default / transition-only description + the reused register line, both backend-owned
          and rendered VERBATIM (the frontend hardcodes neither). */}
      <p className="text-[11px] leading-tight text-slate-500">{copy.description}</p>
      <p className="text-[11px] text-slate-600">{copy.register}</p>
    </div>
  );
}

// A short Web Audio beep — generated on the fly so there is no audio asset and no new dependency. Wrapped
// in try/catch so a blocked/unsupported AudioContext never throws into render (the VISIBLE fired-
// indicator still fires, keeping the behaviour browser-verifiable without audio hardware).
function playBeep() {
  try {
    const AudioCtx =
      typeof window !== "undefined"
        ? window.AudioContext || (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext
        : undefined;
    if (!AudioCtx) return;
    const ctx = new AudioCtx();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = "sine";
    osc.frequency.value = 660;
    gain.gain.value = 0.05; // quiet — a brief cue, never an alarm
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.start();
    // A short envelope so it is a brief blip, then close the context.
    gain.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + 0.15);
    osc.stop(ctx.currentTime + 0.16);
    osc.onended = () => {
      try {
        ctx.close();
      } catch {
        /* already closed */
      }
    };
  } catch {
    /* audio blocked/unsupported — the visible fired-indicator still fired */
  }
}
