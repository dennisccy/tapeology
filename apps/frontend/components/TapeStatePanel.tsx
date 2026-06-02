import { fmt, stateBarColor, stateColor, stateLabel } from "@/lib/format";
import { Panel } from "./Panel";

export function TapeStatePanel({
  state,
  confidence,
  warm,
}: {
  state: string;
  confidence: number;
  warm?: boolean;
}) {
  const pct = Math.max(0, Math.min(100, Math.round((confidence ?? 0) * 100)));
  return (
    <Panel title="Tape State">
      <div className={`text-2xl font-bold ${stateColor(state)}`}>
        {stateLabel(state)}
      </div>
      <div className="mt-2 text-sm text-slate-400">
        Confidence{" "}
        <span className="font-mono text-slate-200">{fmt(confidence, 3)}</span>
      </div>
      <div className="mt-2 h-2 w-full overflow-hidden rounded bg-slate-800">
        <div
          className={`h-2 rounded ${stateBarColor(state)} transition-all duration-300`}
          style={{ width: `${pct}%` }}
        />
      </div>
      {warm === false && (
        <div className="mt-2 text-xs text-amber-400">Warming up — collecting tape data…</div>
      )}
    </Panel>
  );
}
