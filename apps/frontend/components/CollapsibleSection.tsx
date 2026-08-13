"use client";

import type { ReactNode } from "react";

// A `Panel` that starts closed. Six /desk sections are reference material — run ledgers, the index
// reconciliation history, provenance — read occasionally rather than every session, and rendered
// open they pushed the two surfaces that ARE read every session (the briefing and the playbook
// signals) below the fold. They are decluttered, not removed: every one is still on the page, still
// named, one click away.
//
// Three properties this component exists to hold, each load-bearing:
//
//   * THE HEADING STAYS VISIBLE WHILE CLOSED. Only the body is conditional. A shipped replay golden
//     resolves every assertion with `state="visible"`, so a section whose own title vanished when
//     closed would go from "collapsed" to "gone" for anything reading the page.
//   * THE BODY IS NOT RENDERED WHILE CLOSED, rather than hidden with CSS. That is what lets the
//     caller defer the section's own GET until first expand — a body mounted behind
//     `display: none` would still have to be fed.
//   * THE CONTROL IS A REAL BUTTON with `aria-expanded`/`aria-controls`. This page's rows use
//     click handlers on `<tr>`, which are unreachable by keyboard and announce nothing; the
//     playbook pool expansion already refused to propagate that gap, and so does this.
//
// The shell classes are `Panel`'s own, verbatim, so a closed section looks like every other panel
// on the page rather than like a control that lost its frame.
export function CollapsibleSection({
  id,
  title,
  open,
  onToggle,
  children,
}: {
  /** Stable slug — the expand control's testid and the body's `aria-controls` target. */
  id: string;
  /** Rendered verbatim, and identical to the `Panel` title this section used to carry. */
  title: string;
  open: boolean;
  onToggle: () => void;
  children: ReactNode;
}) {
  return (
    <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-4">
      <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-500">
        <button
          type="button"
          data-testid={`desk-section-expand-${id}`}
          aria-expanded={open}
          aria-controls={`desk-section-body-${id}`}
          onClick={onToggle}
          className="flex w-full items-center gap-1.5 rounded text-left uppercase tracking-wider transition-colors hover:text-slate-300 focus:outline-none focus-visible:ring-1 focus-visible:ring-emerald-500"
        >
          <span aria-hidden="true" className="text-[10px] text-slate-600">
            {open ? "▾" : "▸"}
          </span>
          {title}
        </button>
      </h2>
      {open && (
        <div id={`desk-section-body-${id}`} className="mt-3">
          {children}
        </div>
      )}
    </div>
  );
}
