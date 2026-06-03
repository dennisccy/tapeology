"use client";

import { useState } from "react";
import type { FeatureSet } from "@/lib/types";
import { impactColor } from "@/lib/format";
import { Metric, Panel } from "./Panel";

// [feature key, label, unit suffix, decimals, color-by-sign?]
const FEATURE_ROWS: [string, string, string, number, boolean][] = [
  ["trade_speed", "Trade speed", "/s", 2, false],
  ["volume_speed", "Volume speed", "/s", 1, false],
  ["aggressive_buy_ratio", "Aggressive buy ratio", "", 3, false],
  ["aggressive_sell_ratio", "Aggressive sell ratio", "", 3, false],
  ["net_aggressive_volume", "Net aggressive volume", "", 0, true],
  ["buy_price_impact", "Buy price impact", "", 3, true],
  ["sell_price_impact", "Sell price impact", "", 3, true],
  ["average_spread", "Average spread", "", 3, false],
  ["large_print_count", "Large prints", "", 0, false],
  // Absorption triplet (price impact, not aggression) — neutral readouts, not color-by-sign.
  ["absorption_score", "Absorption score", "", 3, false],
  ["bid_refresh_score", "Bid refresh score", "", 3, false],
  ["ask_refresh_score", "Ask refresh score", "", 3, false],
];

export function FeaturesPanel({
  features,
  primaryWindow,
}: {
  features: Record<string, FeatureSet>;
  primaryWindow: string;
}) {
  const windows = Object.keys(features);
  const [selected, setSelected] = useState(primaryWindow);
  const active = features[selected] ?? features[primaryWindow] ?? {};

  return (
    <Panel title="Features" className="lg:col-span-1">
      <div className="mb-3 flex flex-wrap gap-1">
        {windows.map((w) => (
          <button
            key={w}
            type="button"
            onClick={() => setSelected(w)}
            className={`rounded px-2 py-1 font-mono text-xs transition-colors ${
              w === selected
                ? "bg-slate-700 text-slate-100"
                : "bg-slate-800/50 text-slate-400 hover:bg-slate-700/50"
            }`}
          >
            {w}
          </button>
        ))}
      </div>
      <div>
        {FEATURE_ROWS.map(([key, label, unit, decimals, colorBySign]) => {
          const value = active[key];
          const text =
            value == null ? "—" : `${value.toFixed(decimals)}${unit}`;
          const color = colorBySign && value != null ? impactColor(value) : "text-slate-200";
          return <Metric key={key} label={label} value={text} valueClassName={color} />;
        })}
      </div>
    </Panel>
  );
}
