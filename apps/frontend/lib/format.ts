// Presentation helpers. Color semantics (consistent everywhere):
//   green  = buy-side / positive impact
//   red    = sell-side / negative impact
//   amber  = absorption / unclear

export function fmt(value: number | null | undefined, decimals = 2): string {
  if (value == null || Number.isNaN(value)) return "—";
  return value.toFixed(decimals);
}

const STATE_LABELS: Record<string, string> = {
  buyer_control: "Buyer Control",
  seller_control: "Seller Control",
  bid_absorption: "Bid Absorption",
  ask_absorption: "Ask Absorption",
  unclear: "Unclear",
};

export function stateLabel(state: string): string {
  return STATE_LABELS[state] ?? state;
}

export function stateColor(state: string): string {
  if (state === "buyer_control") return "text-emerald-400";
  if (state === "seller_control") return "text-rose-400";
  return "text-amber-400"; // bid/ask absorption, unclear
}

export function stateBarColor(state: string): string {
  if (state === "buyer_control") return "bg-emerald-500";
  if (state === "seller_control") return "bg-rose-500";
  return "bg-amber-500";
}

export function sideColor(side: string): string {
  if (side === "buy") return "text-emerald-400";
  if (side === "sell") return "text-rose-400";
  return "text-slate-400";
}

export function impactColor(value: number): string {
  if (value > 0) return "text-emerald-400";
  if (value < 0) return "text-rose-400";
  return "text-slate-300";
}
