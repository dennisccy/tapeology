"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { fetchMergedCandles } from "./api";
import type { BarRow } from "./types";

// The /structure charts' LOADED-WINDOW owner: how many of a symbol+timeframe's recorded candles are
// currently in the browser, and how to page more in.
//
// Before this hook the page fetched EVERY registered series WITH every candle embedded
// (`GET /research/bars` with no params) and handed one whole series to the chart, which then
// `fitContent()`-squeezed thousands of bars into a 288px-tall canvas — megabytes transferred and
// drawn to show a screenful. Now the page fetches series METADATA only, and this hook pulls
// viewport-sized windows from `GET /research/candles`, extending them on demand as the operator
// zooms or scrolls.
//
// It reads the MERGED endpoint (every recorded series for the symbol+timeframe, folded server-side)
// rather than one series id: a symbol accumulates many overlapping immutable recordings, so a chart
// bound to one of them stops loading while a longer recording of the same pair sits in the store —
// the "zooming out loads nothing" report this hook's second revision exists to fix.
//
// It computes NOTHING about the candles: every row is the store's own row, served verbatim; the
// hook only decides WHICH already-recorded rows are currently in memory (a display/paging choice,
// the same class of choice as picking which timeframe to chart). `hasMoreBefore`/`hasMoreAfter` are
// the endpoint's own honest flags — except after a cap trim, which makes "more exists on that side"
// true by construction (see `MAX_LOADED_BARS`).

// The first window's size, split around the as-of instant. ~300 bars fills a ~1800px-wide chart at
// lightweight-charts' default 6px bar spacing, so the chart is full on first paint without a
// measurement round-trip; the chart then asks for exactly what its visible span is missing.
const INITIAL_BARS = 300;
// The share of the first window drawn BEFORE the as-of instant — the rest is later price action,
// shown as context to the right of the as-of marker (the page's existing extend-past-as-of choice).
const INITIAL_BEFORE_SHARE = 0.8;
// Never let one request exceed the endpoint's own `limit` ceiling (a 422 there, not a clamp).
const MAX_PAGE = 5000;
// The most candles one chart holds at once. Zooming a 1m chart all the way out can put 100k+ bars in
// view; loading them all would undo the CPU/memory win this paging work exists for. At the cap the
// window slides instead of growing — a load in one direction trims the far end — and the page says
// so in its caption. A `fill` request (the chart topping up its own viewport) is refused at the cap;
// an operator GESTURE still loads, so panning through the whole history stays possible.
export const MAX_LOADED_BARS = 5000;

export interface BarWindow {
  /** The loaded candles, ascending by ts — a contiguous window of the merged stored rows. */
  bars: BarRow[];
  /** True while any window request is in flight (the first window or a lazy extension). */
  loading: boolean;
  /** Stored rows exist outside the loaded window on that side (see the cap note above). */
  hasMoreBefore: boolean;
  hasMoreAfter: boolean;
  /** Honest failure of the LAST request — the window keeps whatever it had; nothing is faked. */
  error: string | null;
  /** Served merge facts, for the caption: recordings folded, total merged bars, revised timestamps. */
  seriesCount: number;
  availableBars: number;
  revisedTimestamps: number;
  /** The loaded window has hit MAX_LOADED_BARS and now slides rather than grows. */
  capped: boolean;
  /** Extend the window by up to `count` older / newer stored rows. `fill` requests are the chart
   *  topping up its own viewport (refused at the cap); omit it for operator-driven loads. */
  loadOlder: (count: number, opts?: { fill?: boolean }) => void;
  loadNewer: (count: number, opts?: { fill?: boolean }) => void;
}

/** Merge two ascending windows into one, de-duplicating by `ts` (the endpoint's cursors are both
 * inclusive, so adjacent pages overlap by exactly the cursor row). Rows are never modified — on a
 * duplicate `ts` the already-loaded row is kept, since both come verbatim from the same merge. */
function mergeRows(older: BarRow[], newer: BarRow[]): BarRow[] {
  if (older.length === 0) return newer;
  if (newer.length === 0) return older;
  const seen = new Set(older.map((row) => row.ts));
  const merged = older.concat(newer.filter((row) => !seen.has(row.ts)));
  merged.sort((a, b) => a.ts - b.ts);
  return merged;
}

/**
 * @param symbol         the loaded symbol (`null`/empty = nothing charted yet)
 * @param timeframe      the viewing timeframe whose recordings are merged and paged
 * @param asOfEpochMs    the as-of instant the first window is anchored around (`NaN` = newest bars)
 * @param opts.beforeOnly  the cockpit's NO-LOOKAHEAD clamp: fetch only rows AT OR BEFORE `asOf`
 *   (the whole first window before it, never the forward-context request), and refuse to page
 *   forward (`loadNewer` no-ops, `hasMoreAfter` stays false). The recorded store then only ever
 *   fills the space LEFT of the replay start; the live tape's own moving bars own everything to its
 *   right. Omitted (both /structure call sites) => the byte-identical straddle-the-anchor behavior.
 * @param opts.forwardToEnd  keep paging FORWARD after the first window until the loaded series
 *   reaches the newest recorded bar (or the cap refuses). Without it the window holds only the
 *   ~20% forward share of the first request — on a 5m chart almost exactly one session, which
 *   reads as "the chart stops at the day's close" even though nothing truncated it. Mutually
 *   exclusive with `beforeOnly` by construction: the clamp is checked first and wins.
 */
export function useBarWindow(
  symbol: string | null,
  timeframe: string | null,
  asOfEpochMs: number,
  opts?: { beforeOnly?: boolean; forwardToEnd?: boolean },
): BarWindow {
  // Read through a ref so the memoized extend()/effect keep stable identities (beforeOnly is
  // constant per call site — the cockpit always true, /structure never set).
  const beforeOnlyRef = useRef(opts?.beforeOnly ?? false);
  beforeOnlyRef.current = opts?.beforeOnly ?? false;
  const forwardToEndRef = useRef(opts?.forwardToEnd ?? false);
  forwardToEndRef.current = opts?.forwardToEnd ?? false;
  // The anchor generation whose forward fill is still owed, or -1 when none is. Bounding the fill
  // to ONE pass per anchor is what keeps it from fighting the operator: once the window has reached
  // the newest bar (or the cap), a later pan that re-opens `hasMoreAfter` — a cap trim does exactly
  // that — must not silently drag the window forward again under their hands.
  const forwardFillGenRef = useRef(-1);
  const [bars, setBars] = useState<BarRow[]>([]);
  const [loading, setLoading] = useState(false);
  const [hasMoreBefore, setHasMoreBefore] = useState(false);
  const [hasMoreAfter, setHasMoreAfter] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [merge, setMerge] = useState({ seriesCount: 0, availableBars: 0, revisedTimestamps: 0 });
  const [capped, setCapped] = useState(false);

  // The anchor generation: bumped whenever the symbol/timeframe/as-of changes, so a response from a
  // previous anchor that lands late is DROPPED rather than merged into the new window.
  const generationRef = useRef(0);
  // In-flight guard — one window request at a time per chart (a zoom or drag fires the range
  // callback continuously; without this a single gesture would queue dozens of pages).
  const inFlightRef = useRef(false);
  // The loaded rows + edge flags, mirrored in refs so the loadOlder/loadNewer callbacks can read the
  // current edges without being re-created (and re-subscribed by the chart) on every append.
  const barsRef = useRef<BarRow[]>([]);
  const moreBeforeRef = useRef(false);
  const moreAfterRef = useRef(false);

  const active = symbol && timeframe ? { symbol, timeframe } : null;
  const activeSymbol = active?.symbol ?? null;
  const activeTimeframe = active?.timeframe ?? null;

  // --- the first window: anchored around the as-of instant -----------------------------------
  useEffect(() => {
    generationRef.current += 1;
    const generation = generationRef.current;
    inFlightRef.current = false;
    barsRef.current = [];
    moreBeforeRef.current = false;
    moreAfterRef.current = false;
    setBars([]);
    setHasMoreBefore(false);
    setHasMoreAfter(false);
    setError(null);
    setCapped(false);
    setMerge({ seriesCount: 0, availableBars: 0, revisedTimestamps: 0 });

    if (!activeSymbol || !activeTimeframe) {
      setLoading(false);
      return;
    }
    setLoading(true);

    (async () => {
      const beforeOnly = beforeOnlyRef.current;
      const anchorTs = Number.isNaN(asOfEpochMs) ? undefined : asOfEpochMs / 1000;
      // beforeOnly draws the whole first window BEFORE the anchor (no forward context to share the
      // budget with); otherwise the window is split ~80/20 around it.
      const beforeLimit = beforeOnly
        ? INITIAL_BARS
        : Math.max(1, Math.round(INITIAL_BARS * INITIAL_BEFORE_SHARE));
      const afterLimit = Math.max(1, INITIAL_BARS - beforeLimit);
      // Two requests around the anchor: the run-up TO the as-of bar, plus the later price action
      // shown for context. With no anchor there is nothing to straddle — the newest window is the
      // honest default. beforeOnly (the cockpit no-lookahead clamp) skips the forward request
      // entirely so no stored bar AT OR AFTER the replay start is ever fetched.
      const [before, after] = await Promise.all([
        fetchMergedCandles(activeSymbol, activeTimeframe, {
          beforeTs: anchorTs,
          limit: beforeLimit,
        }),
        anchorTs === undefined || beforeOnly
          ? Promise.resolve(null)
          : fetchMergedCandles(activeSymbol, activeTimeframe, {
              afterTs: anchorTs,
              limit: afterLimit,
            }),
      ]);
      if (generation !== generationRef.current) return; // a newer anchor won — drop this response

      if (!before.ok || !before.data) {
        setLoading(false);
        setError(before.error ?? "The candle window could not be loaded.");
        return;
      }
      const merged = mergeRows(before.data.bars, after?.ok ? (after.data?.bars ?? []) : []);
      // `hasMoreAfter` comes from whichever request reached furthest right (the forward window when
      // it succeeded, otherwise the anchored one) — the endpoint's own flag, never inferred. Under
      // beforeOnly there is honestly no "after" to page into (the live tape owns that side), so it
      // is pinned false regardless of what the store holds past the clamp.
      const moreAfter = beforeOnly
        ? false
        : after?.ok && after.data
          ? after.data.has_more_after
          : before.data.has_more_after;
      barsRef.current = merged;
      moreBeforeRef.current = before.data.has_more_before;
      moreAfterRef.current = moreAfter;
      // Owe this anchor a forward fill (see `forwardFillGenRef`). Recorded here rather than in the
      // fill effect so it is tied to the generation whose window just landed.
      forwardFillGenRef.current =
        forwardToEndRef.current && !beforeOnly && moreAfter ? generation : -1;
      setBars(merged);
      setHasMoreBefore(before.data.has_more_before);
      setHasMoreAfter(moreAfter);
      setMerge({
        seriesCount: before.data.series_count,
        availableBars: before.data.bar_count,
        revisedTimestamps: before.data.revised_timestamps,
      });
      setError(after && !after.ok ? (after.error ?? null) : null);
      setLoading(false);
    })();
  }, [activeSymbol, activeTimeframe, asOfEpochMs]);

  // --- lazy extension in either direction -----------------------------------------------------
  const extend = useCallback(
    (direction: "older" | "newer", count: number, opts?: { fill?: boolean }) => {
      if (!activeSymbol || !activeTimeframe || inFlightRef.current) return;
      // No-lookahead clamp: never page forward past the replay start (the live tape owns that side).
      if (direction === "newer" && beforeOnlyRef.current) return;
      const edge =
        direction === "older" ? barsRef.current[0] : barsRef.current[barsRef.current.length - 1];
      if (!edge) return;
      if (direction === "older" ? !moreBeforeRef.current : !moreAfterRef.current) return;
      // At the cap the window SLIDES, it does not grow: a `fill` (the chart topping up its own
      // viewport) stops here, or it would walk the window through the entire history one page at a
      // time while the visible span it is trying to satisfy stays larger than the cap forever. An
      // operator gesture still loads — that is a real request to look somewhere else.
      if (opts?.fill && barsRef.current.length >= MAX_LOADED_BARS) return;

      const generation = generationRef.current;
      const limit = Math.min(MAX_PAGE, Math.max(1, Math.ceil(count)));
      inFlightRef.current = true;
      setLoading(true);

      (async () => {
        const result = await fetchMergedCandles(
          activeSymbol,
          activeTimeframe,
          direction === "older" ? { beforeTs: edge.ts, limit } : { afterTs: edge.ts, limit },
        );
        if (generation !== generationRef.current) return; // anchor changed mid-flight — drop it
        inFlightRef.current = false;
        setLoading(false);
        if (!result.ok || !result.data) {
          setError(result.error ?? "The candle window could not be extended.");
          return;
        }
        setError(null);
        setMerge({
          seriesCount: result.data.series_count,
          availableBars: result.data.bar_count,
          revisedTimestamps: result.data.revised_timestamps,
        });

        let merged =
          direction === "older"
            ? mergeRows(result.data.bars, barsRef.current)
            : mergeRows(barsRef.current, result.data.bars);
        if (merged.length === barsRef.current.length) {
          // The page carried nothing new (only the inclusive cursor row). Treat that side as done
          // rather than asking again — a degenerate response can never drive a request loop.
          if (direction === "older") {
            moreBeforeRef.current = false;
            setHasMoreBefore(false);
          } else {
            moreAfterRef.current = false;
            setHasMoreAfter(false);
          }
          return;
        }

        if (direction === "older") {
          moreBeforeRef.current = result.data.has_more_before;
          setHasMoreBefore(result.data.has_more_before);
        } else {
          moreAfterRef.current = result.data.has_more_after;
          setHasMoreAfter(result.data.has_more_after);
        }

        if (merged.length > MAX_LOADED_BARS) {
          // Trim the end AWAY from the direction just loaded, so the operator keeps the bars they
          // moved toward. The trimmed side provably still has rows, so its flag becomes true — an
          // honest statement about the LOADED window, not a fabricated server answer.
          if (direction === "older") {
            merged = merged.slice(0, MAX_LOADED_BARS);
            moreAfterRef.current = true;
            setHasMoreAfter(true);
          } else {
            merged = merged.slice(merged.length - MAX_LOADED_BARS);
            moreBeforeRef.current = true;
            setHasMoreBefore(true);
          }
          setCapped(true);
        }
        barsRef.current = merged;
        setBars(merged);
      })();
    },
    [activeSymbol, activeTimeframe],
  );

  const loadOlder = useCallback(
    (count: number, opts?: { fill?: boolean }) => extend("older", count, opts),
    [extend],
  );
  const loadNewer = useCallback(
    (count: number, opts?: { fill?: boolean }) => extend("newer", count, opts),
    [extend],
  );

  // --- forwardToEnd: page forward until the window reaches the newest recorded bar -------------
  // Re-fires as each page lands (`hasMoreAfter`/`loading` change), so it walks to the end without a
  // loop of its own — every page still goes through `extend`, keeping ONE fetch path, the in-flight
  // guard, and the generation drop for a superseded anchor.
  //
  // Requests are marked `fill`, which is load-bearing rather than cosmetic: at `MAX_LOADED_BARS` a
  // forward load TRIMS FROM THE LEFT, so an unbounded fill would eventually walk the setup the
  // chart was asked to show out of the loaded window. `extend` refuses a `fill` at the cap, so the
  // fill stops there instead, `capped` flips, and the page's existing caption says so.
  useEffect(() => {
    if (forwardFillGenRef.current !== generationRef.current) return;
    if (!hasMoreAfter || loading) {
      // `hasMoreAfter` false is the endpoint's own "that was the newest bar" — the fill is done.
      if (!hasMoreAfter) forwardFillGenRef.current = -1;
      return;
    }
    const remaining = MAX_LOADED_BARS - barsRef.current.length;
    if (remaining <= 0) {
      forwardFillGenRef.current = -1;
      return;
    }
    loadNewer(Math.min(MAX_PAGE, remaining), { fill: true });
  }, [hasMoreAfter, loading, bars, loadNewer]);

  return {
    bars,
    loading,
    hasMoreBefore,
    hasMoreAfter,
    error,
    seriesCount: merge.seriesCount,
    availableBars: merge.availableBars,
    revisedTimestamps: merge.revisedTimestamps,
    capped,
    loadOlder,
    loadNewer,
  };
}
