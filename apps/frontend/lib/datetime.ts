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

// --- THE one shared dd-MM-yyyy date/time formatter (J-35) ------------------------------------
//
// Every date the UI renders flows through these two functions, so the WHOLE product shows ONE
// consistent format: dates as `dd-MM-yyyy` and date-times as `dd-MM-yyyy HH:mm[:ss]` (24h), in the
// operator's LOCAL zone. No `MM/DD/YYYY`, ISO `YYYY-MM-DD`, or "Jun 8"-style date remains anywhere.
// These are presentation-only (not a new computed/served value) — they read a backend instant and
// format it; they never recompute a tape value.

function pad2(n: number): string {
  return String(n).padStart(2, "0");
}

// Format a Date (or a parseable instant) as `dd-MM-yyyy` in the operator's LOCAL zone. Returns
// "—" for an unparseable value (never invents a date).
export function formatDateDMY(value: Date | number | string): string {
  const d = value instanceof Date ? value : new Date(value);
  if (Number.isNaN(d.getTime())) return "—";
  return `${pad2(d.getDate())}-${pad2(d.getMonth() + 1)}-${d.getFullYear()}`;
}

// Format a Date (or a parseable instant) as `dd-MM-yyyy HH:mm:ss` (24h) in the operator's LOCAL
// zone. `withSeconds=false` drops the `:ss`. Returns "—" for an unparseable value.
export function formatDateTimeDMY(
  value: Date | number | string,
  withSeconds = true,
): string {
  const d = value instanceof Date ? value : new Date(value);
  if (Number.isNaN(d.getTime())) return "—";
  const date = formatDateDMY(d);
  const time = withSeconds
    ? `${pad2(d.getHours())}:${pad2(d.getMinutes())}:${pad2(d.getSeconds())}`
    : `${pad2(d.getHours())}:${pad2(d.getMinutes())}`;
  return `${date} ${time}`;
}

// Render an ISO-8601 UTC instant (e.g. a market `next_open` from GET /market/clock) in the
// operator's LOCAL zone as `dd-MM-yyyy HH:mm` with an explicit zone label (J-35) — so the backend's
// UTC value is never mis-read as local time AND the format is the one shared `dd-MM-yyyy` form (no
// "Jun 8"). Falls back to the raw string if it cannot be parsed — never invents a time. Used by the
// Live market-status indicator and the honest "market is closed" panel.
export function formatMarketTime(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return `${formatDateTimeDMY(d, false)} ${localOffsetLabel()}`;
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

// --- Custom dd-MM-yyyy date input parse/validate (J-35) --------------------------------------
//
// The native `<input type="date">` is replaced by a custom validated `dd-MM-yyyy` text input. The
// field carries the explicit LOCAL zone label and resolves to the SAME tz-aware instant as before:
// we parse the user's `dd-MM-yyyy` into the internal `YYYY-MM-DD` the row-12 resolver
// (`resolveLocalWindowInstant`) and the ET quick-pick helpers already expect, so timezone
// correctness is UNCHANGED (no silent UTC shift — J-20 stays green). `dd-MM-yyyy` is the SINGLE
// entry+display format (entry here, display via formatDateDMY); the internal ISO form is plumbing
// only and is never shown to the user.

// Parse a `dd-MM-yyyy` string to the internal `YYYY-MM-DD` (the form the row-12 resolver and ET
// presets consume). Returns `undefined` for any malformed or out-of-range value — e.g. `31-02-2026`
// (Feb has no 31st), `1-1-2026` (un-padded), `2026-01-01` (wrong order), or empty — so an invalid
// entry never silently produces a window (J-24: it drives inline validation, never a silent no-op).
// The round-trip check (re-formatting the constructed date must equal the input) rejects overflow
// dates like 31-02 that the Date constructor would otherwise roll forward to 03-03.
export function parseDMYToIsoDate(value: string): string | undefined {
  const m = /^(\d{2})-(\d{2})-(\d{4})$/.exec(value.trim());
  if (!m) return undefined;
  const day = Number(m[1]);
  const month = Number(m[2]);
  const year = Number(m[3]);
  if (month < 1 || month > 12 || day < 1 || day > 31) return undefined;
  // Construct at NOON local to avoid any DST edge near midnight, then verify the fields survived
  // (rejects 31-02 etc., which would otherwise overflow into the next month).
  const d = new Date(year, month - 1, day, 12, 0, 0);
  if (
    d.getFullYear() !== year ||
    d.getMonth() !== month - 1 ||
    d.getDate() !== day
  ) {
    return undefined;
  }
  return `${m[3]}-${m[2]}-${m[1]}`; // YYYY-MM-DD
}

// True iff `value` is a well-formed, in-range `dd-MM-yyyy` date (used to gate the Watch button and
// the quick-picks; an empty string is NOT valid).
export function isValidDMY(value: string): boolean {
  return parseDMYToIsoDate(value) !== undefined;
}

// --- Watched-source descriptor date formatting (J-35) ----------------------------------------
//
// The backend's row-6 watched-source descriptor (`scenario`) is rendered VERBATIM in the cockpit
// (single source of truth — the UI never recomputes the watched source). For a HISTORICAL watch it
// embeds the window as ISO-8601 instants, e.g. `historical AAPL 2024-05-14T13:30:00.000Z–...Z`.
// J-35 requires every date the UI SHOWS to read `dd-MM-yyyy`. This is a pure DISPLAY reformat of
// the descriptor string — it replaces any embedded ISO-8601 instant with its `dd-MM-yyyy HH:mm`
// local-zone form via the ONE shared formatter; it changes no value, only how the date is shown.
// A descriptor with no ISO instant (e.g. a sim scenario, or `live AAPL`) is returned unchanged.
const ISO_INSTANT_RE =
  /\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(?::\d{2})?(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?/g;

export function formatWatchedSource(scenario: string): string {
  return scenario.replace(ISO_INSTANT_RE, (iso) => formatDateTimeDMY(iso, false));
}
