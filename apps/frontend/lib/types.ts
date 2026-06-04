// Shapes mirrored from the backend engine snapshot (app/serializers.py). The UI renders
// these values verbatim — it never recomputes spread, ratios, impacts, or confidence.

export interface Market {
  bid: number | null;
  ask: number | null;
  spread: number | null;
  last: number | null;
}

export interface TradeRow {
  timestamp: number;
  price: number;
  size: number;
  side: "buy" | "sell" | "unknown";
}

export type FeatureSet = Record<string, number>;

export interface TapeSnapshot {
  ticker: string;
  scenario: string;
  stream_status: string;
  warm?: boolean;
  timestamp: number;
  market: Market;
  tape_state: string;
  confidence: number;
  primary_window: string;
  features: Record<string, FeatureSet>; // keyed by window label, e.g. "30s"
  headline_features: FeatureSet;
  observations: string[];
  event_log: string[];
  recent_trades: TradeRow[];
}

export type ConnStatus = "idle" | "connecting" | "live" | "closed";

// The watch data-source mode (wire values; the selector renders Live / Historical / Simulated).
// "sim" is the default and preserves the existing backward-compatible no-body watch.
export type DataSourceMode = "sim" | "live" | "historical";

// Optional params carried by the watch body. Only `mode` is consumed by the backend this
// iteration; `start`/`end`/`speed` are sent for a Historical request but are not replayed yet
// (the real historical provider lands with J-11).
export interface WatchParams {
  mode: DataSourceMode;
  start?: string;
  end?: string;
  speed?: number;
}
