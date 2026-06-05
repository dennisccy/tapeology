// Timezone helpers for the cockpit. Two concerns live here:
//
//   1. DISPLAY (pre-existing): render a backend UTC instant in the operator's local zone with an
//      explicit zone label, so a UTC value is never mis-read as local time.
//   2. HISTORICAL WINDOW RESOLUTION (J-20, Data Contract row 12): resolve the user's selected
//      LOCAL date + start/end times — or a one-click US-session ET preset — to explicit tz-aware
//      ISO-8601 UTC instants ONCE, before the POST /watch body is built. This replaces the prior
//      naive `${date}T${startTime}` construction that the backend then (correctly) treated as UTC,
//      which forced operators to hand-convert ET->UTC. The fix is to stop sending naive values.
//
// No second timezone conversion happens after this module: the backend fetches exactly the
// resolved instants (it does not re-localize a tz-aware value). The ET session anchors are named
// constants and the ET->local/UTC mapping is computed via the IANA `America/New_York` zone, so it
// is DST-correct (no hardcoded -04:00 / -05:00 offset).

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

// --- Historical-window resolution (Data Contract row 12 owner) -------------------------------

// The US regular-trading-hours session anchors, as ET wall-clock times. Named constants — never
// scattered literals (no-magic-numbers). These are display/preset values, NOT engine thresholds.
export const ET_SESSION_OPEN = { hour: 9, minute: 30 } as const; // 09:30 ET
export const ET_SESSION_CLOSE = { hour: 16, minute: 0 } as const; // 16:00 ET

// The IANA zone the US-equity session is defined in. Using the zone (not a fixed offset) is what
// makes the ET<->UTC mapping DST-correct: America/New_York is EDT (-04:00) in summer, EST
// (-05:00) in winter, and Intl resolves the right one for the chosen date.
export const US_MARKET_TZ = "America/New_York" as const;

// The operator's local IANA zone label (e.g. "Asia/Hong_Kong"), for the "your entry is read in
// THIS zone" hint on the picker. Falls back to a fixed-offset label, then to "local time", so it
// always shows SOMETHING explicit — it never silently omits the zone.
export function localZoneLabel(): string {
  try {
    const tz = Intl.DateTimeFormat().resolvedOptions().timeZone;
    if (tz) return tz;
  } catch {
    /* fall through */
  }
  const offset = localOffsetLabel();
  return offset ? `local time (${offset})` : "local time";
}

// A signed "UTC±HH:MM" label for the operator's current local offset (display only).
export function localOffsetLabel(): string {
  // getTimezoneOffset() is minutes BEHIND UTC (positive when local is behind UTC), so negate it
  // to get the conventional sign (UTC+08:00 for Hong Kong).
  const minutesBehind = new Date().getTimezoneOffset();
  const sign = minutesBehind <= 0 ? "+" : "-";
  const abs = Math.abs(minutesBehind);
  const hh = String(Math.floor(abs / 60)).padStart(2, "0");
  const mm = String(abs % 60).padStart(2, "0");
  return `UTC${sign}${hh}:${mm}`;
}

// Offset (in MINUTES east of UTC, e.g. +480 for Hong Kong, -240 for New York in EDT) of the given
// IANA `timeZone` AT the given UTC instant. DST-correct: it asks Intl what wall-clock time that
// zone shows for the instant, then differences against the same instant read as UTC. Pure.
function zoneOffsetMinutes(timeZone: string, instant: Date): number {
  // Read the instant's wall-clock fields AS SHOWN in the target zone.
  const dtf = new Intl.DateTimeFormat("en-US", {
    timeZone,
    hour12: false,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
  const parts = dtf.formatToParts(instant);
  const get = (type: string) => Number(parts.find((p) => p.type === type)?.value);
  let hour = get("hour");
  if (hour === 24) hour = 0; // some engines render midnight as 24
  // Re-assemble those wall fields as if they were UTC; the gap from the true instant is the offset.
  const asUtc = Date.UTC(
    get("year"),
    get("month") - 1,
    get("day"),
    hour,
    get("minute"),
    get("second"),
  );
  return Math.round((asUtc - instant.getTime()) / 60000);
}

// The exact UTC instant for a given ET wall-clock date+time, DST-correct via America/New_York.
// e.g. (2026-06-02, 9, 30) -> the Date for 2026-06-02T13:30:00Z (EDT, -04:00); the SAME inputs on
// a winter date resolve to 14:30:00Z (EST, -05:00). Used to map the US-session quick-picks.
export function etWallTimeToUtc(
  isoDate: string,
  hour: number,
  minute: number,
): Date {
  const [y, m, d] = isoDate.split("-").map(Number);
  // First guess: treat the ET wall fields as UTC. That is off by exactly the ET offset, so we
  // measure the zone's offset AT that guess and correct. (One correction step is exact for the
  // RTH session, which is never within an hour of a DST transition boundary.)
  const guess = new Date(Date.UTC(y, m - 1, d, hour, minute, 0));
  const offsetMin = zoneOffsetMinutes(US_MARKET_TZ, guess);
  return new Date(guess.getTime() - offsetMin * 60000);
}

// Format a UTC instant as a LOCAL "HH:MM" (24h), for filling the <input type="time"> controls
// from a quick-pick (the time input is in the operator's local zone).
export function utcToLocalTimeInput(instant: Date): string {
  const hh = String(instant.getHours()).padStart(2, "0");
  const mm = String(instant.getMinutes()).padStart(2, "0");
  return `${hh}:${mm}`;
}

// A short local-time annotation for a UTC instant (e.g. "06:30 PM" in the operator's zone), used
// to label each quick-pick with its LOCAL equivalent so the user sees both ET and their own time.
export function localTimeAnnotation(instant: Date): string {
  return instant.toLocaleTimeString(undefined, {
    hour: "2-digit",
    minute: "2-digit",
  });
}

// One resolved US-session quick-pick: the local "HH:MM" values to drop into the start/end time
// inputs, plus a human local-equivalent annotation, for the chosen calendar date.
export interface SessionPreset {
  startTimeInput: string; // local HH:MM for <input type=time>
  endTimeInput: string;
  startLocal: string; // local-equivalent annotation (e.g. "09:30 PM")
  endLocal: string;
}

// Compute the local-time fills + annotations for an ET session window (start/end ET wall times)
// on the chosen date. Returns null when no date is selected (the caller disables the quick-pick),
// so a preset can NEVER produce a malformed/empty window.
export function resolveSessionPreset(
  isoDate: string,
  start: { hour: number; minute: number },
  end: { hour: number; minute: number },
): SessionPreset | null {
  if (!isoDate) return null;
  const startUtc = etWallTimeToUtc(isoDate, start.hour, start.minute);
  const endUtc = etWallTimeToUtc(isoDate, end.hour, end.minute);
  return {
    startTimeInput: utcToLocalTimeInput(startUtc),
    endTimeInput: utcToLocalTimeInput(endUtc),
    startLocal: localTimeAnnotation(startUtc),
    endLocal: localTimeAnnotation(endUtc),
  };
}

// THE row-12 resolver. Takes the user's selected LOCAL calendar date (YYYY-MM-DD) and LOCAL
// start/end clock times (HH:MM) and returns explicit tz-aware ISO-8601 UTC instants (`...Z`),
// resolved ONCE here before the POST body is built. `new Date("YYYY-MM-DDTHH:MM")` parses as the
// operator's LOCAL time, and `.toISOString()` emits the equivalent UTC instant — so what the user
// picked locally is exactly what is fetched, with no naive value and no silent UTC shift.
//
// Returns `undefined` for a missing/half-filled field (the caller then sends no window and the
// backend returns its honest 422), and `undefined` if the inputs do not parse — it never emits a
// malformed instant.
export function resolveLocalWindowInstant(
  isoDate: string,
  time: string,
): string | undefined {
  if (!isoDate || !time) return undefined;
  const local = new Date(`${isoDate}T${time}`);
  if (Number.isNaN(local.getTime())) return undefined;
  return local.toISOString(); // tz-aware UTC (`...Z`)
}
