"use client";

import { useEffect, useRef, useState } from "react";
import { searchSymbols } from "@/lib/api";
import type { SymbolMatch } from "@/lib/types";

const DEBOUNCE_MS = 250;

// Symbol input with a debounced suggestions dropdown (J-13). In Live / Historical mode the box
// offers real `GET /symbols/search` matches (symbol + name) rendered verbatim — no business
// logic. Selecting a suggestion fills the symbol; free-text entry always still works (the user
// can ignore the dropdown and submit whatever they typed).
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

  // Debounced lookup: a quiet 250ms after the last keystroke fetches suggestions.
  useEffect(() => {
    const query = value.trim();
    if (!query) {
      setMatches([]);
      setLoading(false);
      return;
    }
    setLoading(true);
    let active = true;
    const id = setTimeout(async () => {
      const results = await searchSymbols(query);
      if (!active) return;
      setMatches(results);
      setLoading(false);
      setOpen(true);
    }, DEBOUNCE_MS);
    return () => {
      active = false;
      clearTimeout(id);
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
