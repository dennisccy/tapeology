import { EmptyHint, Panel } from "./Panel";

export function EventLogPanel({ log }: { log: string[] }) {
  // Newest first.
  const entries = [...log].reverse();
  return (
    <Panel title="Event Log">
      {entries.length === 0 ? (
        <EmptyHint>No events yet.</EmptyHint>
      ) : (
        <ul className="max-h-48 space-y-1 overflow-y-auto pr-1 font-mono text-xs">
          {entries.map((e, i) => (
            <li key={i} className="text-slate-400">
              {e}
            </li>
          ))}
        </ul>
      )}
    </Panel>
  );
}
