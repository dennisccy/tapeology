// Render an ISO-8601 UTC instant (e.g. a market `next_open` from GET /market/clock) in the
// operator's LOCAL zone with an explicit zone label, so the backend's UTC value is never
// mis-read as local time. Falls back to the raw string if it cannot be parsed — never invents a
// time. Used by the Live market-status indicator and the honest "market is closed" panel.
export function formatMarketTime(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    timeZoneName: "short",
  });
}
