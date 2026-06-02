import { EmptyHint, Panel } from "./Panel";

export function ObservationsPanel({ observations }: { observations: string[] }) {
  return (
    <Panel title="Observations">
      {observations.length === 0 ? (
        <EmptyHint>No observations yet.</EmptyHint>
      ) : (
        <ul className="space-y-1.5">
          {observations.map((o, i) => (
            <li key={i} className="flex gap-2 text-sm text-slate-300">
              <span className="text-slate-600">•</span>
              <span>{o}</span>
            </li>
          ))}
        </ul>
      )}
    </Panel>
  );
}
