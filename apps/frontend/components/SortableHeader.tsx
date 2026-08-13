"use client";

import type { SortableColumn, TableSort } from "../lib/useTableSort";

// The presentation half of the /desk sorting primitive (the logic half is lib/useTableSort.ts).
//
// Two components, and both are load-bearing for the honesty contract the hook documents:
//
//   * `SortableHeader` is the ONLY way to enter a non-served order. It is a real `<button>` inside
//     the `<th>`, never a `<th onClick>`: the click-handler-on-a-row pattern used elsewhere on this
//     page is unreachable by keyboard and announces nothing, and a sort control is exactly where
//     that gap must not be propagated. Focus, Enter and Space come free from the button element.
//   * `TableSortNote` is the disclosure. A table showing a non-served order says so, in words, with
//     a control that puts it back. Without this the operator could not tell a sorted table from the
//     record's own ranking -- which is precisely the confusion /desk's served-order rule prevents.
//
// State is announced through `aria-sort` on the `<th>` (the ARIA-native channel a screen reader
// already reads when it enters the column), so the glyph beside the label is decorative and carries
// `aria-hidden` -- no duplicate announcement.
//
// Pinned by apps/backend/tests/test_table_sort_guards.py.

interface SortableHeaderProps<T> {
  column: SortableColumn<T>;
  sort: TableSort<T>;
  /** The table's own header cell class -- passed in so each table keeps its own metrics. */
  className: string;
  /**
   * When true the inactive sort glyph is invisible until the header is hovered or focused. Used by
   * the ranked briefing table alone, whose `<colgroup>` widths are MEASURED values -- an always-on
   * glyph would widen its idle headers and break a layout contract that cost a full iteration to
   * establish. Every other table sizes to content and shows the affordance permanently.
   */
  revealOnHover?: boolean;
  /**
   * Passed straight through to the `<th>`. A two-level header's identity columns span both rows;
   * dropping the span would leave the leaf row one cell short and shear the whole table.
   */
  rowSpan?: number;
}

function nextActionText(state: "none" | "ascending" | "descending"): string {
  if (state === "none") return "click to sort ascending";
  if (state === "ascending") return "click to sort descending";
  return "click to restore the served order";
}

export function SortableHeader<T>({
  column,
  sort,
  className,
  revealOnHover = false,
  rowSpan,
}: SortableHeaderProps<T>) {
  // A column can opt out entirely -- rendered as the plain cell it was before, same class and same
  // text, so nothing shifts on a table where one column has no orderable served value.
  if (column.sortable === false) {
    return (
      <th scope="col" className={className} rowSpan={rowSpan}>
        {column.label}
      </th>
    );
  }
  const state = sort.ariaSort(column.id);
  const active = state !== "none";
  const glyph = state === "ascending" ? "▲" : state === "descending" ? "▼" : "↕";
  const glyphClass = active
    ? "text-emerald-400"
    : revealOnHover
      ? "text-slate-600 opacity-0 transition-opacity group-hover:opacity-100 group-focus-visible:opacity-100"
      : "text-slate-600 opacity-40 transition-opacity group-hover:opacity-100";
  const title = `Sort by ${column.label} — ${nextActionText(state)}${
    column.note ? ` · ${column.note}` : ""
  }`;
  return (
    <th
      scope="col"
      className={className}
      rowSpan={rowSpan}
      aria-sort={state}
      data-testid="desk-sort-header"
      data-column={column.id}
    >
      <button
        type="button"
        onClick={() => sort.toggle(column.id)}
        title={title}
        className={`group inline-flex w-full items-center gap-1 rounded-sm text-inherit transition-colors hover:text-slate-300 focus:outline-none focus-visible:ring-1 focus-visible:ring-emerald-500 ${
          column.align === "right" ? "justify-end" : "justify-start"
        } ${active ? "text-slate-300" : ""}`}
      >
        {column.label}
        <span aria-hidden="true" className={glyphClass}>
          {glyph}
        </span>
      </button>
    </th>
  );
}

// Rendered directly above its own table, and ONLY while a sort is active: in the served order there
// is nothing to disclose and nothing to undo, so the row of chrome simply is not there.
export function TableSortNote<T>({ sort }: { sort: TableSort<T> }) {
  if (sort.isServedOrder || sort.activeLabel === null) return null;
  return (
    <p
      data-testid="desk-sort-active-note"
      className="mb-1 flex flex-wrap items-center gap-2 text-[11px] text-amber-200/80"
    >
      <span>
        sorted by {sort.activeLabel} ({sort.activeDirection === "asc" ? "ascending" : "descending"})
        — not the order the record served.
      </span>
      <button
        type="button"
        data-testid="desk-sort-reset"
        onClick={sort.reset}
        className="rounded border border-slate-700 px-1.5 py-0.5 text-[11px] text-slate-300 transition-colors hover:border-slate-500 hover:text-slate-200 focus:outline-none focus-visible:ring-1 focus-visible:ring-emerald-500"
      >
        Reset to served order
      </button>
    </p>
  );
}
