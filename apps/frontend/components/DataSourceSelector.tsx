import type { DataSourceMode } from "@/lib/types";

// Exactly three data-source modes (J-10). Display order Live / Historical / Simulated; the
// default selection is Simulated (owned by the page), which preserves the current flow.
const MODES: { value: DataSourceMode; label: string }[] = [
  { value: "live", label: "Live" },
  { value: "historical", label: "Historical" },
  { value: "sim", label: "Simulated" },
];

// A hand-built 3-way segmented control styled like the existing TopBar controls (no component
// library). Switching the source is handled by the page, which tears down any active watch first.
export function DataSourceSelector({
  mode,
  onChange,
}: {
  mode: DataSourceMode;
  onChange: (mode: DataSourceMode) => void;
}) {
  return (
    <div
      role="group"
      aria-label="Data source"
      className="inline-flex rounded border border-slate-700 bg-slate-950 p-0.5"
    >
      {MODES.map((m) => {
        const active = m.value === mode;
        return (
          <button
            key={m.value}
            type="button"
            aria-pressed={active}
            onClick={() => onChange(m.value)}
            className={`rounded px-3 py-1 text-xs font-semibold transition-colors focus:outline-none focus:ring-1 focus:ring-emerald-400 ${
              active
                ? "bg-slate-700 text-slate-100"
                : "text-slate-400 hover:text-slate-200 active:text-slate-100"
            }`}
          >
            {m.label}
          </button>
        );
      })}
    </div>
  );
}
