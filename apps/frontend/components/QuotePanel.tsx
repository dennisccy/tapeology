import type { Market } from "@/lib/types";
import { fmt } from "@/lib/format";
import { Metric, Panel } from "./Panel";

export function QuotePanel({ market }: { market: Market }) {
  return (
    <Panel title="Quote">
      <Metric label="Bid" value={fmt(market.bid)} valueClassName="text-emerald-300" />
      <Metric label="Ask" value={fmt(market.ask)} valueClassName="text-rose-300" />
      <Metric label="Spread" value={fmt(market.spread)} />
      <Metric label="Last" value={fmt(market.last)} />
    </Panel>
  );
}
