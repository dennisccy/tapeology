"use client";

import { useEffect, useState } from "react";
import { fetchTaxonomy } from "@/lib/api";
import type { Hint, ResearchTaxonomy } from "@/lib/types";

// The setup-forming hint dock (capability 33, J-65): sits UNDER the tape-state panel on `/` (its
// pre-registered blueprint home). It renders the served active hint VERBATIM — pattern + evidence,
// setup-type context, baseline citation, and a declare affordance — and is visible ONLY when a hint is
// active (no empty-state chrome; the dock is simply absent otherwise). The backend computes the
// evidence + baseline citation once; the dock renders them, never derives anything.
//
// Copy discipline (J-66): the dock carries the backend-owned "Descriptive only — not trading advice"
// register line and never adds an imperative/predictive word of its own. The declare affordance only
// PREFILLS the thesis declare form (setup + direction); the user still types the invalidation price —
// one click never creates a thesis. It is hidden while a thesis is already active on the ticker (the
// no-dead-control pattern — no affordance that would only produce a 409).

export function HintDock({
  hint,
  thesisActive,
  onDeclare,
}: {
  // The active hint off the live snapshot's `hint` key (or null/undefined when none).
  hint: Hint | null | undefined;
  // Whether a thesis is already active on the ticker — when true the declare affordance is hidden
  // (a thesis-active ticker would 409 a second declare; no dead control).
  thesisActive: boolean;
  // Prefill the thesis declare form from this hint (setup + direction + the hint id for the
  // declared-from linkage). Invalidation is left for the user to type.
  onDeclare: (hint: Hint) => void;
}) {
  const [taxonomy, setTaxonomy] = useState<ResearchTaxonomy | null>(null);

  // Load the taxonomy ONLY when a hint is actually active (the dock is absent otherwise, so the idle
  // cockpit costs no request). The dock reads the per-hint evidence/citation off the hint object; the
  // taxonomy supplies the dock title + register line + declare-affordance copy (the dock hardcodes none).
  useEffect(() => {
    if (!hint || taxonomy) return;
    let cancelled = false;
    fetchTaxonomy().then((t) => {
      if (!cancelled && t) setTaxonomy(t);
    });
    return () => {
      cancelled = true;
    };
  }, [hint, taxonomy]);

  // Absent unless a hint is active (no empty-state chrome — the blueprint's "visible only when active").
  if (!hint) return null;

  const copy = taxonomy?.hints?.copy;
  const dockTitle = copy?.dock_title ?? "Setup forming";
  const register = copy?.dock_register ?? "Descriptive only — not trading advice.";
  const declareLabel = copy?.declare_label ?? "Prefill a thesis from this hint";
  const declareCaption = copy?.declare_caption ?? "You still type the invalidation price yourself.";

  return (
    <section
      data-testid="hint-dock"
      // Amber/neutral styling per the design system (absorption/unclear semantics), matching the
      // risk-flag chip register: a left accent rule + a subtle amber surface.
      className="rounded-lg border-l-2 border-amber-500 border-y border-r border-y-amber-700/60 border-r-amber-700/60 bg-amber-900/20 p-4"
    >
      <div className="flex items-baseline justify-between gap-2">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-amber-400">
          {dockTitle}
        </h3>
        <span className="text-[10px] uppercase tracking-wide text-amber-500/70">
          {hint.pattern_label}
        </span>
      </div>

      {/* Plain-language evidence with its measured value — rendered verbatim (no naked output). */}
      <p data-testid="hint-evidence" className="mt-2 text-sm text-amber-200/90">
        {hint.evidence}
      </p>

      {/* The baseline citation — the user's studied baseline, or the honest unvalidated string. */}
      <p data-testid="hint-baseline" className="mt-2 font-mono text-xs text-amber-300/80">
        {hint.baseline_citation}
      </p>

      {/* The declare affordance — PREFILLS the declare form (one click never creates a thesis). Hidden
          while a thesis is already active on the ticker (no dead control that would only 409). */}
      {!thesisActive && (
        <div className="mt-3">
          <button
            type="button"
            data-testid="hint-declare"
            onClick={() => onDeclare(hint)}
            className="rounded-md border border-amber-600 bg-amber-800/40 px-3 py-1.5 text-sm font-medium text-amber-100 transition-colors hover:border-amber-500 hover:bg-amber-700/40 focus:outline-none focus:ring-1 focus:ring-amber-500 active:bg-amber-700/60"
          >
            {declareLabel}
          </button>
          <p className="mt-1.5 text-xs text-amber-500/70">{declareCaption}</p>
        </div>
      )}

      <p className="mt-3 text-xs text-amber-600/70">{register}</p>
    </section>
  );
}
