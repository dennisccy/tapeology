"use client";

import { useCallback, useMemo, useState } from "react";

// The ONE table-sorting primitive on /desk. Every sortable table on that page reaches its display
// order through this hook and nowhere else, so there is exactly one comparator in the product
// rather than one per table.
//
// This hook exists inside a page whose standing contract is that it renders the order the backend
// served, verbatim. That contract is NOT weakened here, it is made precise:
//
//   * SERVED ORDER IS THE DEFAULT, and it is the literal untouched array -- not "a sort by whatever
//     key the record happened to be ordered on". While `sort === null` no comparator runs at all
//     (see the early return in `entries` below). A page that sorted by a guessed key on mount would
//     be choosing an order on the operator's behalf, which is the thing the contract forbids.
//   * A DIFFERENT ORDER IS AN EXPLICIT OPERATOR ACT -- it can only arise from `toggle`, which only
//     a header button calls. It is always disclosed (`TableSortNote`) and always reversible (the
//     third click of the tri-state cycle, or `reset`).
//   * NOTHING IS EVER DROPPED OR ADDED. `entries` is a TOTAL mapping of `items`: one entry in, one
//     entry out, always. This is what lets callers keep deriving position-meaning values from
//     `servedIndex` -- the ranked table's `rank` cell and the occurrence table's beyond-cap chip
//     both do, and both would silently lie if this hook could filter or truncate.
//   * `servedIndex` IS THE ROW'S POSITION IN THE RECORD, not on screen. It survives sorting, which
//     is strictly stronger than the page-offset arithmetic it replaced.
//
// Pinned by apps/backend/tests/test_table_sort_guards.py (each assertion there has a seeded
// counter-test; a guard that cannot fail proves nothing).
//
// No `useEffect` anywhere in this module, deliberately: /desk pins an exact effect/interval/timeout
// census (apps/backend/tests/test_desk_refresh_chain_guard.py), and a hook used a dozen times on
// that page must not be able to move those numbers.

export type SortDirection = "asc" | "desc";

// `null` IS the served order. It is a distinct third state rather than a flag beside a column, so
// "no order was chosen" cannot be confused with "ascending by the first column".
export type SortState = { columnId: string; direction: SortDirection } | null;

export type SortValue = string | number | boolean | null | undefined;

// How a column's values are ordered against each other:
//   text    -- locale compare, numeric-aware ("AAPL" < "BRK-B"; "5m" < "10m")
//   number  -- relational compare on the served number
//   instant -- an ISO timestamp, compared as parsed epoch ms rather than lexically (the served
//              stamps carry 6-digit microseconds, and a future "+00:00" form would sort wrong as
//              a plain string)
//   flag    -- boolean; false before true ascending
export type SortKind = "text" | "number" | "instant" | "flag";

export interface SortableColumn<T> {
  /** Unique within one table. Also the `data-column` attribute and the `aria-sort` target. */
  id: string;
  /** Rendered verbatim as the header text -- never re-worded by the header component. */
  label: string;
  kind: SortKind;
  /**
   * ONE served field read. This must not derive, combine or compute anything: /desk's standing
   * rule is that the page renders served values, and a comparator is not an exemption.
   *
   * `servedIndex` is passed alongside so a column that displays the row's own position in the
   * record (the ranked table's `rank`) can order by that position without the caller having to
   * pre-pair every row with an index the hook already knows.
   */
  value: (item: T, servedIndex: number) => SortValue;
  align?: "left" | "right";
  /** Default true. `false` renders a plain, non-interactive header cell. */
  sortable?: boolean;
  /** Extra prose appended to the header's `title` -- e.g. which of two paired rows it sorts on. */
  note?: string;
}

export interface SortedEntry<T> {
  readonly item: T;
  /** The item's index in the array as SERVED, regardless of where it now renders. */
  readonly servedIndex: number;
}

export interface TableSort<T> {
  entries: readonly SortedEntry<T>[];
  sort: SortState;
  isServedOrder: boolean;
  /** The active column's label, for the disclosure note. `null` in served order. */
  activeLabel: string | null;
  activeDirection: SortDirection | null;
  /** Tri-state: served -> ascending -> descending -> served. */
  toggle: (columnId: string) => void;
  reset: () => void;
  ariaSort: (columnId: string) => "ascending" | "descending" | "none";
}

// A value that cannot be ordered -- rendered as an em dash by every caller. Resolved to `null` here
// so the comparator has one missing-ness test instead of four scattered ones.
function sortValue<T>(column: SortableColumn<T>, entry: SortedEntry<T>): string | number | null {
  const raw = column.value(entry.item, entry.servedIndex);
  if (raw === null || raw === undefined) return null;
  if (column.kind === "text") {
    const text = String(raw).trim();
    return text === "" ? null : text;
  }
  if (column.kind === "flag") return raw ? 1 : 0;
  if (column.kind === "instant") {
    const parsed = Date.parse(String(raw));
    return Number.isNaN(parsed) ? null : parsed;
  }
  const numeric = Number(raw);
  // `Number.isNaN`, not `Number.isFinite`: an infinite served value is still orderable, and the
  // relational compare below handles it correctly. Only a genuine non-number is missing.
  return Number.isNaN(numeric) ? null : numeric;
}

function comparePresent(left: string | number, right: string | number, kind: SortKind): number {
  if (kind === "text") {
    return String(left).localeCompare(String(right), "en", {
      numeric: true,
      sensitivity: "base",
    });
  }
  // Relational, never `left - right`. Subtraction on served numerics is what /desk's arithmetic
  // lint exists to catch, and it is also simply wrong at the infinities.
  if (left < right) return -1;
  if (left > right) return 1;
  return 0;
}

export function useTableSort<T>(
  items: readonly T[],
  columns: readonly SortableColumn<T>[],
): TableSort<T> {
  const [sort, setSort] = useState<SortState>(null);

  const activeColumn = useMemo(
    () => (sort === null ? null : (columns.find((column) => column.id === sort.columnId) ?? null)),
    [columns, sort],
  );

  const entries = useMemo<readonly SortedEntry<T>[]>(() => {
    // The served order, materialised. One entry per item, in the order handed to this hook.
    const base: SortedEntry<T>[] = items.map((item, servedIndex) => ({ item, servedIndex }));
    // The default path returns here, BEFORE any comparator exists. An unresolvable column id (a
    // stale selection after the data underneath changed) lands here too -- falling back to the
    // served order is the only honest answer when the requested order cannot be computed.
    if (sort === null || activeColumn === null) return base;
    const direction = sort.direction;
    // A copy: `items` belongs to the caller and to the record it came from.
    return [...base].sort((a, b) => {
      const left = sortValue(activeColumn, a);
      const right = sortValue(activeColumn, b);
      // Missing values sort LAST in both directions. This branch returns before the direction flip
      // below can reach it -- otherwise "descending" would float every blank cell to the top, which
      // reads as data rather than as absence.
      if (left === null || right === null) {
        if (left === null && right === null) return a.servedIndex < b.servedIndex ? -1 : 1;
        return left === null ? 1 : -1;
      }
      const ranked = comparePresent(left, right, activeColumn.kind);
      if (ranked !== 0) return direction === "asc" ? ranked : -ranked;
      // Equal values keep the record's own order, which also makes the sort stable.
      return a.servedIndex < b.servedIndex ? -1 : 1;
    });
  }, [items, sort, activeColumn]);

  const toggle = useCallback((columnId: string) => {
    setSort((previous) => {
      if (previous === null || previous.columnId !== columnId) {
        return { columnId, direction: "asc" };
      }
      if (previous.direction === "asc") return { columnId, direction: "desc" };
      // Third click closes the cycle by returning to the served order -- the operator can always
      // get back to what the record said without reloading the page.
      return null;
    });
  }, []);

  const reset = useCallback(() => setSort(null), []);

  const ariaSort = useCallback(
    (columnId: string): "ascending" | "descending" | "none" => {
      if (sort === null || sort.columnId !== columnId) return "none";
      return sort.direction === "asc" ? "ascending" : "descending";
    },
    [sort],
  );

  return {
    entries,
    sort,
    isServedOrder: sort === null,
    activeLabel: activeColumn === null ? null : activeColumn.label,
    activeDirection: sort === null ? null : sort.direction,
    toggle,
    reset,
    ariaSort,
  };
}
