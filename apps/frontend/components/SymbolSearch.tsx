"use client";

import { useEffect, useRef, useState } from "react";
import { searchSymbols } from "@/lib/api";
import { SYMBOL_SEARCH_DEBOUNCE_MS, SYMBOL_SEARCH_MIN_QUERY } from "@/lib/config";
import type { SymbolMatch } from "@/lib/types";

// Symbol input with a debounced, cancellable suggestions dropdown (J-13 / J-30). In Live /
// Historical mode the box offers real `GET /symbols/search` matches (symbol + name) rendered
// verbatim — no business logic. Selecting a suggestion fills the symbol; free-text entry always
// still works (the user can ignore the dropdown and submit whatever they typed).
//
// J-30 responsiveness: a quiet `SYMBOL_SEARCH_DEBOUNCE_MS` after the last keystroke fires a lookup
// ONLY when the query is at least `SYMBOL_SEARCH_MIN_QUERY` long (mirroring the backend min-query),
// and each new lookup ABORTS the previous in-flight request via an AbortController — so rapid
// typing never piles up and a slow earlier response can never overwrite a newer result. Both
// tuning constants come from config (no inline literal here).
export function SymbolSearch({
  value,
  onChange,
  onPick,
  placeholder,
  ariaLabel,
  inputClassName,
}: {
  value: string;
  onChange: (value: string) => void;
  onPick: (symbol: string) => void;
  placeholder: string;
  ariaLabel: string;
  inputClassName: string;
}) {
  const [matches, setMatches] = useState<SymbolMatch[]>([]);
  const [loading, setLoading] = useState(false);
  const [open, setOpen] = useState(false);
  const boxRef = useRef<HTMLDivElement>(null);

  // Debounced + cancellable lookup. A quiet SYMBOL_SEARCH_DEBOUNCE_MS after the last keystroke
  // fires a lookup, but only once the query reaches SYMBOL_SEARCH_MIN_QUERY (a too-short query is
  // dropped client-side, mirroring the backend — no over-broad scan). Each run owns an
  // AbortController; the cleanup aborts the prior request so a newer keystroke cancels the older
  // in-flight fetch (no pile-up, no out-of-order overwrite). An aborted request resolves to `[]`
  // in `searchSymbols`, so a cancelled query never overwrites a newer result or shows an error.
  useEffect(() => {
    const query = value.trim();
    if (query.length < SYMBOL_SEARCH_MIN_QUERY) {
      setMatches([]);
      setLoading(false);
      return;
    }
    setLoading(true);
    const controller = new AbortController();
    let active = true;
    const id = setTimeout(async () => {
      const results = await searchSymbols(query, controller.signal);
      // Guard with both the abort signal and the `active` flag: if this effect was cleaned up
      // (newer keystroke) the request was aborted and we must not apply its (empty) result.
      if (!active || controller.signal.aborted) return;
      setMatches(results);
      setLoading(false);
      setOpen(true);
    }, SYMBOL_SEARCH_DEBOUNCE_MS);
    return () => {
      active = false;
      clearTimeout(id);
      controller.abort(); // cancel any in-flight request from this run (real cancellation)
    };
  }, [value]);

  // Close the dropdown on an outside click.
  useEffect(() => {
    function onDocMouseDown(e: MouseEvent) {
      if (boxRef.current && !boxRef.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", onDocMouseDown);
    return () => document.removeEventListener("mousedown", onDocMouseDown);
  }, []);

  function pick(match: SymbolMatch) {
    onPick(match.symbol);
    setOpen(false);
  }

  const showDropdown = open && value.trim().length > 0 && (loading || matches.length > 0);

  return (
    <div ref={boxRef} className="relative">
      <input
        aria-label={ariaLabel}
        value={value}
        onChange={(e) => {
          onChange(e.target.value);
          setOpen(true);
        }}
        onFocus={() => {
          if (matches.length > 0) setOpen(true);
        }}
        placeholder={placeholder}
        autoComplete="off"
        role="combobox"
        aria-expanded={showDropdown}
        aria-autocomplete="list"
        className={inputClassName}
      />
      {showDropdown && (
        <ul
          role="listbox"
          aria-label="Symbol suggestions"
          className="absolute left-0 top-full z-30 mt-1 max-h-64 w-72 overflow-auto rounded border border-slate-700 bg-slate-900 py-1 shadow-lg shadow-black/40"
        >
          {matches.length === 0 && loading ? (
            <li className="px-3 py-2 text-xs text-slate-500">Searching…</li>
          ) : (
            matches.map((match) => (
              <li key={match.symbol} role="option" aria-selected={false}>
                <button
                  type="button"
                  // preventDefault on mousedown keeps input focus so the click registers
                  onMouseDown={(e) => e.preventDefault()}
                  onClick={() => pick(match)}
                  className="flex w-full items-baseline justify-between gap-3 px-3 py-1.5 text-left transition-colors hover:bg-slate-800 focus:bg-slate-800 focus:outline-none"
                >
                  <span className="font-mono text-sm text-slate-100">{match.symbol}</span>
                  <span className="truncate text-xs text-slate-400">{match.name}</span>
                </button>
              </li>
            ))
          )}
        </ul>
      )}
    </div>
  );
}
