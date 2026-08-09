// Date/time helpers for the whole UI. Two concerns live here:
//
//   1. DISPLAY: render a backend UTC instant as `yyyy-MM-dd HH:mm:ss ET` — one format, one clock,
//      on every page.
//   2. HISTORICAL WINDOW RESOLUTION (Data Contract row 12): resolve the user's selected date +
//      start/end times — entered as US-Eastern wall-clock — to explicit tz-aware ISO-8601 UTC
//      instants ONCE, before the POST /watch body is built. The backend fetches exactly the
//      resolved instants (it does not re-localize a tz-aware value), so no second timezone
//      conversion happens after this module.
//
// The ET<->UTC mapping is computed via the IANA `America/New_York` zone, so it is DST-correct (no
// hardcoded -04:00 / -05:00 offset).

// --- THE one shared yyyy-MM-dd / US-Eastern formatter ----------------------------------------
//
// Every date the UI renders flows through these functions, so the WHOLE product shows ONE
// consistent format on ONE clock: dates as `yyyy-MM-dd` and date-times as `yyyy-MM-dd HH:mm[:ss]`
// (24h), in US EXCHANGE time. No `MM/DD/YYYY`, no `dd-MM-yyyy`, no "Jun 8"-style date, and no
// operator-local rendering remains anywhere.
//
// The exchange clock — not the reader's — because every instant this product shows is a fact
// about a trading session: a screen's recorded-at time, a wall touch, a bar's own stamp. Read on
// a reader's local clock those become unanchored ("09:30" means the open in New York and
// something else everywhere else), and the reader has to carry an offset in their head to compare
// two cells. Rendering on the session's own clock removes the conversion entirely. The `ET` suffix
// is carried explicitly (see `ET_SUFFIX`) so a value is never mis-read as local time; the raw UTC
// string stays reachable in a `title` wherever a page shows a provenance stamp.
//
// These are presentation-only — they read a backend instant and format it; they never recompute a
// tape value.

// The IANA zone the US-equity session is defined in. Using the zone (not a fixed offset) is what
// makes the ET<->UTC mapping DST-correct: America/New_York is EDT (-04:00) in summer, EST
// (-05:00) in winter, and Intl resolves the right one for the chosen date.
export const US_MARKET_TZ = "America/New_York" as const;

// The explicit zone marker appended to every rendered date-time. Bare DATES carry no suffix (a
// calendar day has no clock to be ambiguous about).
export const ET_SUFFIX = "ET" as const;

// The wall-clock fields of an instant AS SHOWN in the US-market zone. Assembled from
// `formatToParts` rather than a locale pattern (`en-CA` etc.): a locale is free to change its
// separators, and the output format here is load-bearing.
function etParts(d: Date): {
  year: number;
  month: number;
  day: number;
  hour: number;
  minute: number;
  second: number;
} {
  const parts = new Intl.DateTimeFormat("en-US", {
    timeZone: US_MARKET_TZ,
    hour12: false,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  }).formatToParts(d);
  const get = (type: string) => Number(parts.find((p) => p.type === type)?.value);
  let hour = get("hour");
  if (hour === 24) hour = 0; // some engines render midnight as 24
  return {
    year: get("year"),
    month: get("month"),
    day: get("day"),
    hour,
    minute: get("minute"),
    second: get("second"),
  };
}

function pad2(n: number): string {
  return String(n).padStart(2, "0");
}

function toDate(value: Date | number | string): Date {
  return value instanceof Date ? value : new Date(value);
}

// Format a Date (or a parseable instant) as `yyyy-MM-dd` — the US-market calendar date the instant
// falls on. Returns "—" for an unparseable value (never invents a date).
export function formatDateET(value: Date | number | string): string {
  const d = toDate(value);
  if (Number.isNaN(d.getTime())) return "—";
  const p = etParts(d);
  return `${p.year}-${pad2(p.month)}-${pad2(p.day)}`;
}

// Format a Date (or a parseable instant) as `yyyy-MM-dd HH:mm:ss ET` (24h, US-market clock).
// `seconds: false` drops the `:ss`; `zone: false` drops the ` ET` suffix (for a field the caller
// has already labelled as ET, e.g. an input's value). Returns "—" for an unparseable value.
export function formatDateTimeET(
  value: Date | number | string,
  opts: { seconds?: boolean; zone?: boolean } = {},
): string {
  const { seconds = true, zone = true } = opts;
  const d = toDate(value);
  if (Number.isNaN(d.getTime())) return "—";
  const p = etParts(d);
  const date = `${p.year}-${pad2(p.month)}-${pad2(p.day)}`;
  const time = seconds
    ? `${pad2(p.hour)}:${pad2(p.minute)}:${pad2(p.second)}`
    : `${pad2(p.hour)}:${pad2(p.minute)}`;
  return zone ? `${date} ${time} ${ET_SUFFIX}` : `${date} ${time}`;
}

// Format a Date (or a parseable instant) as `HH:mm:ss` (24h, US-market clock) — the TIME ALONE,
// for a column whose date is already fixed and stated once (the forward touch table: every row
// belongs to the one screen-date session named above it, so repeating the date on ~40 rows of a
// 23-column table would cost width and say nothing). `seconds: false` drops the `:ss`.
//
// It reads the same `etParts` every other formatter here reads, so a time in such a column and a
// full stamp elsewhere on the page can be compared without converting anything. Never use it for a
// value whose date is NOT already on screen — a bare clock time with no day is the ambiguity this
// module exists to remove.
export function formatTimeET(
  value: Date | number | string,
  opts: { seconds?: boolean } = {},
): string {
  const { seconds = true } = opts;
  const d = toDate(value);
  if (Number.isNaN(d.getTime())) return "—";
  const p = etParts(d);
  return seconds
    ? `${pad2(p.hour)}:${pad2(p.minute)}:${pad2(p.second)}`
    : `${pad2(p.hour)}:${pad2(p.minute)}`;
}

// Format a backend DAY MARKER as `yyyy-MM-dd`. A day marker is a calendar day the backend
// transmits either bare (`2026-07-09`) or as that day's UTC midnight (`2026-08-07T00:00:00Z`) —
// `requested_window.start`/`.end` (built as `now.date().isoformat() + "T00:00:00Z"`) and
// `latest_window_end_utc` (stored verbatim from a fetch request body, which is why BOTH shapes
// occur) are the two on this product.
//
// It names a DAY, not an instant, so it is read LEXICALLY — the leading 10 characters ARE the
// date. Running it through `formatDateET` instead would be wrong twice over: UTC midnight is
// 20:00 ET on the PREVIOUS day, so `2026-08-07T00:00:00Z` would render `2026-08-06`, and a value
// with no clock at all would acquire a `20:00:00` that was never in the record.
//
// A value that is not a well-formed day marker is returned unchanged rather than reformatted —
// there is nothing to truncate and inventing one would hide the anomaly.
export function formatDayMarker(value: string): string {
  const head = value.slice(0, 10);
  return /^\d{4}-\d{2}-\d{2}$/.test(head) ? head : value;
}

// Today's US-market calendar date (`yyyy-MM-dd`) — THE reference "today" for every date field and
// "Today" shortcut in the product. The market's own date, never the browser's: an operator east of
// New York is already on tomorrow's local date for most of their working day, so a local (or UTC)
// "today" fills in a session that has not happened.
export function todayEtDate(): string {
  return formatDateET(new Date());
}

// Render an ISO-8601 UTC instant (e.g. a market `next_open` from GET /market/clock) on the market
// clock as `yyyy-MM-dd HH:mm ET`. Falls back to the raw string if it cannot be parsed — never
// invents a time. Used by the Live market-status indicator and the honest "market is closed" panel.
export function formatMarketTime(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return formatDateTimeET(d, { seconds: false });
}

// --- Historical-window resolution (Data Contract row 12 owner) -------------------------------

// The US regular-trading-hours session anchors, as ET wall-clock times. Named constants — never
// scattered literals (no-magic-numbers). These are display/preset values, NOT engine thresholds.
export const ET_SESSION_OPEN = { hour: 9, minute: 30 } as const; // 09:30 ET
export const ET_SESSION_CLOSE = { hour: 16, minute: 0 } as const; // 16:00 ET

// Offset (in MINUTES east of UTC, e.g. -240 for New York in EDT) of the US-market zone AT the
// given UTC instant. DST-correct: it asks Intl what wall-clock time the zone shows for the
// instant, then differences against the same instant read as UTC. Pure.
function etOffsetMinutes(instant: Date): number {
  const p = etParts(instant);
  // Re-assemble those wall fields as if they were UTC; the gap from the true instant is the offset.
  const asUtc = Date.UTC(p.year, p.month - 1, p.day, p.hour, p.minute, p.second);
  return Math.round((asUtc - instant.getTime()) / 60000);
}

// The exact UTC instant for a given ET wall-clock date+time, DST-correct via America/New_York.
// e.g. (2026-06-02, 9, 30) -> the Date for 2026-06-02T13:30:00Z (EDT, -04:00); the SAME inputs on
// a winter date resolve to 14:30:00Z (EST, -05:00).
//
// The correction runs TWICE. Treating the ET wall fields as UTC is off by exactly the ET offset,
// so we measure the offset at that guess and correct — but the guess itself can land on the far
// side of a DST boundary from the true instant, in which case the offset measured there is the
// wrong one. Re-measuring at the corrected instant and re-correcting settles it. (One step was
// enough while this only served the RTH quick-picks, which are never within an hour of a
// transition; `parseEtDateTimeToUtcIso` now feeds it arbitrary times of day, including the
// 23:59:59 as-of seed.)
export function etWallTimeToUtc(
  isoDate: string,
  hour: number,
  minute: number,
  second = 0,
): Date {
  const [y, m, d] = isoDate.split("-").map(Number);
  const wallAsUtc = Date.UTC(y, m - 1, d, hour, minute, second);
  let instant = new Date(wallAsUtc - etOffsetMinutes(new Date(wallAsUtc)) * 60000);
  instant = new Date(wallAsUtc - etOffsetMinutes(instant) * 60000);
  return instant;
}

// --- Date / date-time entry (parse + validate) -----------------------------------------------
//
// Every date field in the product is a custom validated TEXT input rather than a native
// `<input type="date">`: the native picker renders in the browser's locale (so it would show
// `MM/DD/YYYY` or `DD.MM.YYYY` depending on the machine) and reads in the browser's zone, both of
// which this module exists to make uniform. `yyyy-MM-dd` is the SINGLE entry+display format.

// Parse a `yyyy-MM-dd` string, returning it normalized, or `undefined` for any malformed or
// out-of-range value — e.g. `2026-02-31` (Feb has no 31st), `2026-1-1` (un-padded), `01-01-2026`
// (wrong order), or empty. So an invalid entry never silently produces a window; it drives inline
// validation instead. The round-trip check (the constructed date's fields must survive) rejects
// overflow dates like 02-31 that the Date constructor would otherwise roll forward to 03-03.
export function parseIsoDate(value: string): string | undefined {
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value.trim());
  if (!m) return undefined;
  const year = Number(m[1]);
  const month = Number(m[2]);
  const day = Number(m[3]);
  if (month < 1 || month > 12 || day < 1 || day > 31) return undefined;
  // Construct at NOON UTC to avoid any edge near midnight, then verify the fields survived
  // (rejects 02-31 etc., which would otherwise overflow into the next month).
  const d = new Date(Date.UTC(year, month - 1, day, 12, 0, 0));
  if (
    d.getUTCFullYear() !== year ||
    d.getUTCMonth() !== month - 1 ||
    d.getUTCDate() !== day
  ) {
    return undefined;
  }
  return `${m[1]}-${m[2]}-${m[3]}`;
}

// True iff `value` is a well-formed, in-range `yyyy-MM-dd` date (used to gate submit buttons and
// the quick-picks; an empty string is NOT valid).
export function isValidIsoDate(value: string): boolean {
  return parseIsoDate(value) !== undefined;
}

// Parse a `yyyy-MM-dd HH:mm[:ss]` string READ AS US-EASTERN WALL TIME and return the equivalent
// tz-aware ISO-8601 UTC instant (`...Z`) — the form every backend `as_of` / window parameter
// expects. A bare `yyyy-MM-dd` (no time) resolves to ET midnight. Returns `undefined` for anything
// malformed, so a half-typed value never produces a request. The `T` separator is accepted as well
// as a space, so a pasted ISO-ish value still parses.
export function parseEtDateTimeToUtcIso(value: string): string | undefined {
  const m = /^(\d{4}-\d{2}-\d{2})(?:[ T](\d{2}):(\d{2})(?::(\d{2}))?)?$/.exec(value.trim());
  if (!m) return undefined;
  const isoDate = parseIsoDate(m[1]);
  if (!isoDate) return undefined;
  const hour = m[2] === undefined ? 0 : Number(m[2]);
  const minute = m[3] === undefined ? 0 : Number(m[3]);
  const second = m[4] === undefined ? 0 : Number(m[4]);
  if (hour > 23 || minute > 59 || second > 59) return undefined;
  return etWallTimeToUtc(isoDate, hour, minute, second).toISOString();
}

// THE row-12 resolver. Takes the user's selected ET calendar date (`yyyy-MM-dd`) and ET clock time
// (`HH:MM` or `HH:MM:SS`, the `<input type="time">` value) and returns an explicit tz-aware
// ISO-8601 UTC instant (`...Z`), resolved ONCE here before the POST body is built — so what the
// user picked on the exchange clock is exactly what is fetched, with no naive value and no silent
// UTC shift.
//
// Returns `undefined` for a missing/half-filled field (the caller then sends no window and the
// backend returns its honest 422), and `undefined` if the inputs do not parse — it never emits a
// malformed instant.
export function resolveEtWindowInstant(
  isoDate: string,
  time: string,
): string | undefined {
  if (!isoDate || !time) return undefined;
  return parseEtDateTimeToUtcIso(`${isoDate} ${time}`);
}

// --- Watched-source descriptor date formatting -----------------------------------------------
//
// The backend's row-6 watched-source descriptor (`scenario`) is rendered VERBATIM in the cockpit
// (single source of truth — the UI never recomputes the watched source). For a HISTORICAL watch it
// embeds the window as ISO-8601 instants, e.g. `historical AAPL 2024-05-14T13:30:00.000Z–...Z`.
// Every date the UI SHOWS must read `yyyy-MM-dd` on the market clock, so this is a pure DISPLAY
// reformat of the descriptor string — it replaces any embedded ISO-8601 instant with its
// `yyyy-MM-dd HH:mm ET` form via the ONE shared formatter; it changes no value, only how the date
// is shown. A descriptor with no ISO instant (e.g. a sim scenario, or `live AAPL`) is returned
// unchanged.
const ISO_INSTANT_RE =
  /\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(?::\d{2})?(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?/g;

export function formatWatchedSource(scenario: string): string {
  return scenario.replace(ISO_INSTANT_RE, (iso) =>
    formatDateTimeET(iso, { seconds: false }),
  );
}
