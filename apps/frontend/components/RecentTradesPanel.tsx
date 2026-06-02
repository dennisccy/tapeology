import type { TradeRow } from "@/lib/types";
import { fmt, sideColor } from "@/lib/format";
import { EmptyHint, Panel } from "./Panel";

export function RecentTradesPanel({ trades }: { trades: TradeRow[] }) {
  return (
    <Panel title="Recent Trades">
      {trades.length === 0 ? (
        <EmptyHint>No trades yet.</EmptyHint>
      ) : (
        <table className="w-full font-mono text-sm">
          <thead>
            <tr className="text-xs uppercase text-slate-500">
              <th className="pb-1 text-left font-medium">Price</th>
              <th className="pb-1 text-right font-medium">Size</th>
              <th className="pb-1 text-right font-medium">Side</th>
            </tr>
          </thead>
          <tbody>
            {trades.slice(0, 15).map((t, i) => (
              <tr key={i} className="border-t border-slate-800/60">
                <td className="py-0.5 text-left text-slate-200">{fmt(t.price)}</td>
                <td className="py-0.5 text-right text-slate-300">{t.size}</td>
                <td className={`py-0.5 text-right uppercase ${sideColor(t.side)}`}>
                  {t.side}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </Panel>
  );
}
