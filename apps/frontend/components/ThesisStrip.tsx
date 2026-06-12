"use client";

import { useEffect, useState } from "react";
import {
  declareThesis,
  fetchTaxonomy,
  recordAction,
  resolveThesis,
} from "@/lib/api";
import type {
  ManagementStance,
  ResearchTaxonomy,
  RiskFlag,
  StatementStatus,
  ThesisProjection,
  ThesisVerdict,
} from "@/lib/types";

// The thesis strip (capability 23): sits between the price chart and the panel grid on `/`.
//   * idle      — a single one-line declare affordance (J-68 strip-idle clause: nothing else moves);
//   * declaring — a fully taxonomy-driven form (setups/directions/level-requirement come from
//                 GET /research/taxonomy — no hardcoded labels), invalidation required, inline
//                 backend validation messages (422/409/404) surfaced verbatim;
//   * active    — the declared thesis rendered VERBATIM from the WS `thesis` projection: setup,
//                 direction, invalidation (mono), the frozen statements each with a live status, the
//                 `pending` verdict badge (slate), bound source + data_feed stamp, monitor status.
// Copy is thesis-attributed, present-tense, descriptive (J-66) — never imperative/predictive.
//
// The active display reads the snapshot's `thesis` key (pushed live over the WS) — the frontend
// derives nothing. Declaring just POSTs; the WS frame then carries the active thesis on its own.

const STATUS_STYLE: Record<StatementStatus, { dot: string; text: string; label: string }> = {
  met: { dot: "bg-emerald-500", text: "text-emerald-400", label: "met" },
  not_yet: { dot: "bg-slate-600", text: "text-slate-400", label: "not yet" },
  violated: { dot: "bg-rose-500", text: "text-rose-400", label: "violated" },
};

const FEED_LABEL: Record<string, string> = { sim: "SIM", sip: "SIP", iex: "IEX" };

// Verdict VISUAL semantics only (the design direction): pending slate, confirming emerald, weakening
// amber, rejecting rose, invalidated rose with a terminal treatment, expired slate. The DISPLAY COPY
// (the label text) is read from GET /research/taxonomy — the frontend hardcodes none of it. This map
// is the side/impact palette EXTENDED, never repurposed.
const VERDICT_STYLE: Record<ThesisVerdict, string> = {
  pending:
    "border-slate-700 bg-slate-800 text-slate-300",
  confirming:
    "border-emerald-700 bg-emerald-900/40 text-emerald-300",
  weakening:
    "border-amber-700 bg-amber-900/40 text-amber-300",
  rejecting:
    "border-rose-700 bg-rose-900/40 text-rose-300",
  // Terminal treatment: a heavier, ringed rose chip so an invalidated thesis reads as resolved/final
  // (not just another live verdict) — never a silent revert to the idle declare affordance.
  invalidated:
    "border-rose-500 bg-rose-950 text-rose-200 ring-1 ring-rose-500/50",
  expired:
    "border-slate-700 bg-slate-800 text-slate-400",
};

// The verdict's plain-language evidence line color, matched to the chip semantics (descriptive copy
// is read verbatim from the projection — never composed client-side).
const VERDICT_EVIDENCE_COLOR: Record<ThesisVerdict, string> = {
  pending: "text-slate-400",
  confirming: "text-emerald-300/90",
  weakening: "text-amber-300/90",
  rejecting: "text-rose-300/90",
  invalidated: "text-rose-200/90",
  expired: "text-slate-400",
};

function verdictLabel(
  verdict: ThesisVerdict,
  taxonomy: ResearchTaxonomy | null,
): string {
  // Display copy comes from the taxonomy (row 24); fall back to the raw enum only if it has not
  // loaded yet (the chip still renders — it never blocks on the catalog).
  const fromTaxonomy = taxonomy?.verdicts.find((v) => v.id === verdict)?.name;
  return fromTaxonomy ?? verdict;
}

// Entry risk-flag chips (capability 26, J-49): amber advisory chips on the thesis strip — one per
// FROZEN flag, each showing the taxonomy-owned `label` and its plain-language MEASURED `evidence`,
// both read VERBATIM off the projection (the strip derives nothing). Amber = the absorption/unclear
// semantics from the design system (these are advisories, not buy/sell side reads). No flags fired
// (or the key absent — never assessed) ⇒ NOTHING renders: no chips, and deliberately NO "all clear"
// badge (no naked reassurance). Frozen at declaration — they never change as the tape moves.
function RiskFlagChips({ flags }: { flags: RiskFlag[] | undefined }) {
  if (!flags || flags.length === 0) return null;
  return (
    <div
      data-testid="risk-flags"
      className="mt-3 flex flex-col gap-1.5 border-t border-slate-800 pt-3"
    >
      <span className="text-xs font-semibold uppercase tracking-wider text-amber-400/80">
        Entry risk flags
      </span>
      <div className="flex flex-col gap-1.5">
        {flags.map((f) => (
          <div
            key={f.flag}
            data-testid="risk-flag-chip"
            data-flag={f.flag}
            className="flex flex-wrap items-baseline gap-x-2 gap-y-0.5 rounded-md border-l-2 border-amber-500 border-y border-r border-y-amber-700/60 border-r-amber-700/60 bg-amber-900/30 px-2.5 py-1.5"
          >
            {/* Class-based amber advisory indicator — a left accent rule replaces the prior ⚠ emoji
                prefix (coherence cleanup, J-51), consistent with the cockpit's text/class-based
                design system (no icon library, no emoji). The amber semantics carry the advisory
                meaning; the label is taxonomy-owned and read verbatim. */}
            <span className="text-xs font-semibold uppercase tracking-wide text-amber-300">
              {f.label}
            </span>
            {/* The measured margin, rendered verbatim. Mono so the embedded numerics read cleanly,
                matching the cockpit's numeric discipline. */}
            <span className="font-mono text-xs text-amber-200/90">{f.evidence}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

// The holding-period MANAGEMENT STANCE block (capability 27, J-53; data-contract row 25 stance half).
// Shown ONLY when the active projection carries the stance keys — i.e. the thesis is ENTRY-MARKED,
// unresolved, and a live monitor is evaluating (the backend gates presence; the strip never guesses).
// It answers "does the tape still support this position?" with the stance label in the established
// verdict/stance palette (thesis_intact emerald, thesis_weakening amber, thesis_invalidated rose with
// the terminal treatment), its evidence line, and the live distance-to-invalidation ($ and R) + open
// R in font-mono. ALL values render VERBATIM from the projection — ZERO client-side arithmetic, ZERO
// client-side stance derivation. The "Descriptive only — not trading advice" register extends here;
// the distance/open-R copy carries the journaled-measurement register (consistent with realized-R).

// Stance VISUAL semantics only (the design direction) — the side/impact palette EXTENDED, never
// repurposed. The LABEL text comes from the projection's `label` (taxonomy-owned); this maps the id
// to its color treatment (a visual concern). thesis_invalidated carries the ringed terminal treatment.
const STANCE_STYLE: Record<ManagementStance["value"], { chip: string; evidence: string }> = {
  thesis_intact: {
    chip: "border-emerald-700 bg-emerald-900/40 text-emerald-300",
    evidence: "text-emerald-300/90",
  },
  thesis_weakening: {
    chip: "border-amber-700 bg-amber-900/40 text-amber-300",
    evidence: "text-amber-300/90",
  },
  thesis_invalidated: {
    chip: "border-rose-500 bg-rose-950 text-rose-200 ring-1 ring-rose-500/50",
    evidence: "text-rose-200/90",
  },
};

// One signed mono readout (distance / open-R) with a label — emerald when on the safe/favorable side,
// rose when adverse, slate when absent. The value is rendered verbatim (server-computed); only the
// display rounding happens here (toFixed) — never any arithmetic on the underlying numbers.
function StanceReadout({
  label,
  value,
  suffix = "",
  testid,
}: {
  label: string;
  value: number | null | undefined;
  suffix?: string;
  testid: string;
}) {
  const present = value != null;
  const tone = !present
    ? "text-slate-500"
    : value >= 0
      ? "text-emerald-400"
      : "text-rose-400";
  return (
    <span className="flex items-baseline gap-1.5 text-xs text-slate-500">
      {label}
      <span data-testid={testid} className={`font-mono text-sm font-semibold ${tone}`}>
        {present ? `${value >= 0 ? "+" : ""}${value.toFixed(2)}${suffix}` : "—"}
      </span>
    </span>
  );
}

function ManagementStanceBlock({ thesis }: { thesis: ThesisProjection }) {
  const stance = thesis.management_stance;
  if (!stance) return null; // backend-gated: no stance keys => nothing renders (no client guess)
  const style = STANCE_STYLE[stance.value] ?? STANCE_STYLE.thesis_weakening;
  const dist = thesis.distance_to_invalidation;
  return (
    <div
      data-testid="management-stance"
      data-stance={stance.value}
      className="mt-3 flex flex-col gap-2 border-t border-slate-800 pt-3"
    >
      <div className="flex flex-wrap items-center justify-between gap-2">
        <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
          Management stance
        </span>
        {/* The stance chip — color per the id; the LABEL text is taxonomy-owned (read verbatim). */}
        <span
          data-testid="stance-chip"
          className={`rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-wider ${style.chip}`}
        >
          {stance.label}
        </span>
      </div>
      {/* The stance's plain-language EVIDENCE (no naked stance) — read verbatim from the projection. */}
      {stance.evidence && (
        <p data-testid="stance-evidence" className={`text-sm ${style.evidence}`}>
          {stance.evidence}
        </p>
      )}
      {/* The live readouts — distance-to-invalidation ($ and R) + open R, all font-mono, verbatim. */}
      <div className="flex flex-wrap items-center gap-x-5 gap-y-1">
        <StanceReadout
          label="distance to invalidation"
          value={dist?.dollars}
          testid="distance-dollars"
        />
        <StanceReadout label="" value={dist?.r} suffix="R" testid="distance-r" />
        <StanceReadout label="open" value={thesis.open_r} suffix="R" testid="open-r" />
        <span className="ml-auto text-xs text-slate-600">
          journaled measurement, R = |entry − invalidation|
        </span>
      </div>
    </div>
  );
}

function StripShell({ children }: { children: React.ReactNode }) {
  return (
    <section
      data-testid="thesis-strip"
      className="mb-4 rounded-lg border border-slate-800 bg-slate-900/60 p-4"
    >
      {children}
    </section>
  );
}

// J-47: a surviving entry-marked thesis shown as ACTIVE-BUT-NOT-EVALUATED. The watch that declared
// it was stopped (or restarted, or a different source is being watched), so the tape is NOT being
// judged against it right now — but a real position is never orphaned. Rendered VERBATIM from the
// row-15 projection (the backend-owned `monitor_notice`), with NO client-side lifecycle inference,
// NO live verdict chip, and NO mark/resolve controls (those need a live tape) — only the frozen
// thesis facts, the recorded marks, and the not-evaluated notice. Re-watching the bound source
// resumes live evaluation on its own (the WS frame then carries an `ok` projection again).
function NotEvaluatedThesis({ thesis }: { thesis: ThesisProjection }) {
  const directionColor =
    thesis.direction === "long" ? "text-emerald-400" : "text-rose-400";
  const marks = thesis.marks;
  return (
    <StripShell>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap items-baseline gap-3">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
            Your thesis
          </span>
          <span className="text-sm font-semibold text-slate-200">
            {thesis.setup_type.replace(/_/g, " ")}
          </span>
          <span className={`text-sm font-semibold uppercase ${directionColor}`}>
            {thesis.direction}
          </span>
          <span className="text-sm text-slate-400">
            invalidation{" "}
            <span className="font-mono text-slate-200">
              {thesis.invalidation_price.toFixed(2)}
            </span>
          </span>
          {thesis.level_price != null && (
            <span className="text-sm text-slate-400">
              level{" "}
              <span className="font-mono text-slate-200">
                {thesis.level_price.toFixed(2)}
              </span>
            </span>
          )}
        </div>
        {/* A neutral (slate) not-evaluated chip — NOT a live verdict (no green/red): the tape is not
            being judged against this thesis right now. */}
        <span
          data-testid="not-evaluated-chip"
          data-monitor-status={thesis.monitor_status}
          className="rounded-full border border-slate-600 bg-slate-800 px-3 py-1 text-xs font-semibold uppercase tracking-wider text-slate-300"
        >
          ⏸ not evaluated
        </span>
      </div>

      {/* The backend-owned plain-language notice (the not-currently-evaluated or mismatched-source
          copy), rendered VERBATIM — the frontend composes none of it (data-contract row 24). */}
      {thesis.monitor_notice && (
        <p
          data-testid="not-evaluated-notice"
          className="mt-2 text-sm text-amber-300/90"
        >
          {thesis.monitor_notice}
        </p>
      )}

      {/* Recorded marks (J-52) — the real position that must never be orphaned, read verbatim. */}
      {(marks?.entry || marks?.exit) && (
        <div
          data-testid="recorded-marks"
          className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1 text-sm"
        >
          {marks?.entry && (
            <span className="text-slate-400">
              entry{" "}
              <span data-testid="entry-mark-price" className="font-mono text-slate-200">
                {marks.entry.price.toFixed(2)}
              </span>
              {marks.entry.spread_at_mark != null && (
                <span className="ml-1 text-xs text-slate-500">
                  spread{" "}
                  <span className="font-mono">
                    {marks.entry.spread_at_mark.toFixed(2)}
                  </span>
                </span>
              )}
            </span>
          )}
          {marks?.exit && (
            <span className="text-slate-400">
              exit{" "}
              <span data-testid="exit-mark-price" className="font-mono text-slate-200">
                {marks.exit.price.toFixed(2)}
              </span>
            </span>
          )}
        </div>
      )}

      {/* Realized move in R (J-52) — shown only once BOTH marks exist; a journaled measurement. */}
      {marks?.realized_r != null && (
        <p data-testid="realized-r" className="mt-2 text-sm text-slate-300">
          Realized move{" "}
          <span
            className={`font-mono font-semibold ${
              marks.realized_r >= 0 ? "text-emerald-400" : "text-rose-400"
            }`}
          >
            {marks.realized_r >= 0 ? "+" : ""}
            {marks.realized_r.toFixed(2)}R
          </span>
          <span className="ml-2 text-xs text-slate-500">
            journaled measurement, R = |entry − invalidation|
          </span>
        </p>
      )}

      {/* Frozen entry risk flags (J-49) persist on the surviving/not-evaluated strip too — they are a
          record of the entry moment, unchanged by the watch having stopped. Read verbatim. */}
      <RiskFlagChips flags={thesis.risk_flags} />

      <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-slate-500">
        <span>
          source <span className="text-slate-400">{thesis.bound_source}</span>
        </span>
        <span>
          feed{" "}
          <span className="text-slate-400">
            {FEED_LABEL[thesis.data_feed] ?? thesis.data_feed}
          </span>
        </span>
        <span className="ml-auto">Descriptive only — not trading advice.</span>
      </div>
    </StripShell>
  );
}

function ActiveThesis({
  thesis,
  taxonomy,
  last,
}: {
  thesis: ThesisProjection;
  taxonomy: ResearchTaxonomy | null;
  // The current last price (read off the live snapshot) — prefills the mark price field.
  last: number | null;
}) {
  const directionColor =
    thesis.direction === "long" ? "text-emerald-400" : "text-rose-400";
  const isInvalidated = thesis.verdict === "invalidated";
  const verdictChip = VERDICT_STYLE[thesis.verdict] ?? VERDICT_STYLE.pending;
  const evidenceColor =
    VERDICT_EVIDENCE_COLOR[thesis.verdict] ?? VERDICT_EVIDENCE_COLOR.pending;

  // Action marks (J-52) — read VERBATIM off the projection. `has_entry` is the backend-owned fact
  // the UI reads to WITHDRAW the Abandon control (it never guesses).
  const marks = thesis.marks;
  const hasEntry = marks?.has_entry ?? false;
  const hasExit = marks?.exit != null;

  // User resolution (J-50): the record actions on a LIVE thesis. System-owned terminal states
  // (invalidated) carry no user controls — the strip shows their terminal treatment instead. On
  // success the next WS frame carries `thesis: null`, so the strip returns to the declare affordance
  // on its own (the frontend derives nothing). A 409/422 surfaces an explicit inline message.
  const [resolving, setResolving] = useState<"played_out" | "abandoned" | null>(
    null,
  );
  const [resolveError, setResolveError] = useState<string | null>(null);
  const canResolve = !isInvalidated;
  // Abandon is WITHDRAWN the moment an entry mark exists (anti-survivorship, J-52 closing J-50's
  // deferred clause): a real position is never abandoned. An unmarked thesis still offers Abandon.
  const canAbandon = canResolve && !hasEntry;

  async function handleResolve(resolution: "played_out" | "abandoned") {
    setResolveError(null);
    setResolving(resolution);
    const result = await resolveThesis(thesis.id, resolution);
    if (!result.ok) {
      // No dead click, no swallowed failure — surface the backend detail verbatim. The WS frame
      // keeps the thesis active (nothing was resolved), so the controls stay available to retry.
      setResolveError(result.error ?? "The thesis could not be resolved.");
      setResolving(null);
    }
    // On success leave `resolving` set: the strip is about to unmount as the WS pushes `thesis: null`
    // (the button stays disabled in the brief interval, preventing a double-submit).
  }

  // Mark entry / exit (J-52): record the user's OWN already-taken action — a JOURNALING record,
  // never a fill, never an order. The price field prefills from the current last, is editable, and
  // is submitted VERBATIM. A 409/422 surfaces an explicit inline message (no dead click); the button
  // disables during submit. On success the next WS frame carries the recorded marks on its own.
  const [marking, setMarking] = useState<"entry" | "exit" | null>(null);
  const [markPrice, setMarkPrice] = useState<string>("");
  const [markEdited, setMarkEdited] = useState(false);
  const [markError, setMarkError] = useState<string | null>(null);

  // Eagerly PREFILL the price field from the current last so the value (not just a placeholder) is
  // populated and visible — until the user edits it (then their input is preserved verbatim and the
  // live last no longer clobbers it). Resets the edited flag once a mark is recorded (the field
  // clears) so the NEXT mark (exit) re-prefills from the then-current last.
  useEffect(() => {
    if (!markEdited && last != null) {
      setMarkPrice(last.toFixed(2));
    }
  }, [last, markEdited]);

  async function handleMark(kind: "entry" | "exit") {
    setMarkError(null);
    const priceNum = Number(markPrice);
    if (!markPrice.trim() || Number.isNaN(priceNum)) {
      setMarkError("Enter a price for the mark.");
      return;
    }
    setMarking(kind);
    const result = await recordAction(thesis.id, kind, priceNum);
    setMarking(null);
    if (result.ok) {
      // The WS frame will carry the recorded mark on its own. Reset the edited flag so the NEXT mark
      // (exit) re-prefills from the then-current last via the effect above.
      setMarkPrice("");
      setMarkEdited(false);
    } else {
      setMarkError(result.error ?? `The ${kind} mark could not be recorded.`);
    }
  }

  return (
    <StripShell>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap items-baseline gap-3">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
            Your thesis
          </span>
          <span className="text-sm font-semibold text-slate-200">
            {thesis.setup_type.replace(/_/g, " ")}
          </span>
          <span className={`text-sm font-semibold uppercase ${directionColor}`}>
            {thesis.direction}
          </span>
          <span className="text-sm text-slate-400">
            invalidation{" "}
            <span className="font-mono text-slate-200">
              {thesis.invalidation_price.toFixed(2)}
            </span>
          </span>
          {thesis.level_price != null && (
            <span className="text-sm text-slate-400">
              level{" "}
              <span className="font-mono text-slate-200">
                {thesis.level_price.toFixed(2)}
              </span>
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          {/* The live PUBLISHED verdict chip — color per the design direction (confirming emerald,
              weakening amber, rejecting/invalidated rose, pending slate); invalidated carries the
              terminal ringed treatment. The LABEL text is taxonomy-owned (hardcoded nowhere). */}
          <span
            data-testid="verdict-chip"
            data-verdict={thesis.verdict}
            className={`rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-wider ${verdictChip}`}
          >
            {isInvalidated ? "✕ " : ""}
            {verdictLabel(thesis.verdict, taxonomy)}
          </span>
        </div>
      </div>

      {/* The verdict's plain-language EVIDENCE line (no naked verdicts) — read verbatim from the
          projection, never composed client-side. Always present (every verdict carries evidence). */}
      {thesis.verdict_evidence && (
        <p
          data-testid="verdict-evidence"
          className={`mt-2 text-sm ${evidenceColor}`}
        >
          {thesis.verdict_evidence}
        </p>
      )}

      {/* Terminal invalidated notice: the thesis is resolved (not a live read) — shown explicitly so
          the strip never silently reverts to the idle declare affordance. */}
      {isInvalidated && (
        <p className="mt-1 text-xs font-medium uppercase tracking-wider text-rose-400">
          Thesis invalidated — resolved
        </p>
      )}

      {/* Frozen expected-behaviour statements, each with its live status (read verbatim). */}
      <ul className="mt-3 space-y-1.5">
        {thesis.statements.map((s, i) => {
          const style = STATUS_STYLE[s.status] ?? STATUS_STYLE.not_yet;
          return (
            <li key={i} className="flex items-start gap-2 text-sm">
              <span
                className={`mt-1.5 h-2 w-2 shrink-0 rounded-full ${style.dot}`}
                aria-hidden
              />
              <span className="text-slate-300">{s.text}</span>
              <span className={`ml-auto shrink-0 font-mono text-xs ${style.text}`}>
                {style.label}
              </span>
            </li>
          );
        })}
      </ul>

      <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-slate-500">
        <span>
          source <span className="text-slate-400">{thesis.bound_source}</span>
        </span>
        <span>
          feed{" "}
          <span className="text-slate-400">
            {FEED_LABEL[thesis.data_feed] ?? thesis.data_feed}
          </span>
        </span>
        {thesis.monitor_status === "failed" && (
          <span className="text-amber-400">
            Monitor unavailable — statement statuses may be stale.
          </span>
        )}
        <span className="ml-auto">Descriptive only — not trading advice.</span>
      </div>

      {/* Entry risk flags (capability 26, J-49) — frozen at declaration, advisory amber chips. Each
          carries the taxonomy label + its plain-language measured margin, rendered verbatim. */}
      <RiskFlagChips flags={thesis.risk_flags} />

      {/* Management stance (capability 27, J-53): the holding-period read — shown ONLY while the
          backend serves the stance keys (entry-marked + unresolved + evaluating). Stance label +
          evidence + live distance-to-invalidation ($ and R) + open R, all rendered VERBATIM. */}
      <ManagementStanceBlock thesis={thesis} />

      {/* Action marks (J-52): the user journals their OWN already-taken entry/exit. A JOURNALING
          record, never a fill/order. Recorded verbatim; realized move shown in R units only (never
          currency, never profit/loss framing). Hidden on a system-owned invalidated thesis. */}
      {canResolve && (
        <div
          data-testid="thesis-marks"
          className="mt-3 border-t border-slate-800 pt-3"
        >
          {/* Recorded marks line — entry/exit price (mono) + the moment spread, read verbatim. */}
          {(marks?.entry || marks?.exit) && (
            <div
              data-testid="recorded-marks"
              className="mb-2 flex flex-wrap items-center gap-x-4 gap-y-1 text-sm"
            >
              {marks?.entry && (
                <span className="text-slate-400">
                  entry{" "}
                  <span data-testid="entry-mark-price" className="font-mono text-slate-200">
                    {marks.entry.price.toFixed(2)}
                  </span>
                  {marks.entry.spread_at_mark != null && (
                    <span className="ml-1 text-xs text-slate-500">
                      spread{" "}
                      <span className="font-mono">
                        {marks.entry.spread_at_mark.toFixed(2)}
                      </span>
                    </span>
                  )}
                </span>
              )}
              {marks?.exit && (
                <span className="text-slate-400">
                  exit{" "}
                  <span data-testid="exit-mark-price" className="font-mono text-slate-200">
                    {marks.exit.price.toFixed(2)}
                  </span>
                  {marks.exit.spread_at_mark != null && (
                    <span className="ml-1 text-xs text-slate-500">
                      spread{" "}
                      <span className="font-mono">
                        {marks.exit.spread_at_mark.toFixed(2)}
                      </span>
                    </span>
                  )}
                </span>
              )}
            </div>
          )}

          {/* Realized move in R (J-52) — shown ONLY once BOTH marks exist; a journaled measurement in
              R units, with the spread-at-mark beside it. Never currency, never "profit/loss". */}
          {marks?.realized_r != null && (
            <p
              data-testid="realized-r"
              className="mb-2 text-sm text-slate-300"
            >
              Realized move{" "}
              <span
                className={`font-mono font-semibold ${
                  marks.realized_r >= 0 ? "text-emerald-400" : "text-rose-400"
                }`}
              >
                {marks.realized_r >= 0 ? "+" : ""}
                {marks.realized_r.toFixed(2)}R
              </span>
              <span className="ml-2 text-xs text-slate-500">
                journaled measurement, R = |entry − invalidation|
                {marks.exit?.spread_at_mark != null && (
                  <>
                    {" "}
                    · spread at exit{" "}
                    <span className="font-mono">
                      {marks.exit.spread_at_mark.toFixed(2)}
                    </span>
                  </>
                )}
              </span>
            </p>
          )}

          {/* Mark controls: Mark entry until entered; Mark exit once entered (until exited). The
              price field prefills from the current last, is editable, and submits verbatim. */}
          {!hasExit && (
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-xs text-slate-500">
                {hasEntry ? "Record your exit:" : "Record your entry:"}
              </span>
              <input
                type="number"
                step="any"
                inputMode="decimal"
                data-testid="mark-price-input"
                aria-label="mark price"
                className="w-28 rounded-md border border-slate-700 bg-slate-950 px-2 py-1.5 font-mono text-sm text-slate-200 focus:border-slate-500 focus:outline-none focus:ring-1 focus:ring-slate-500"
                value={markPrice}
                placeholder={last != null ? last.toFixed(2) : "price"}
                onChange={(e) => {
                  // The user typed — preserve their input verbatim; stop tracking the live last.
                  setMarkEdited(true);
                  setMarkPrice(e.target.value);
                  setMarkError(null);
                }}
              />
              {!hasEntry ? (
                <button
                  type="button"
                  data-testid="mark-entry"
                  disabled={marking !== null}
                  onClick={() => handleMark("entry")}
                  className="rounded-md border border-emerald-700 bg-emerald-800/40 px-3 py-1.5 text-sm font-medium text-emerald-200 transition-colors hover:bg-emerald-700/40 focus:outline-none focus:ring-1 focus:ring-emerald-500 active:bg-emerald-700/60 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {marking === "entry" ? "Recording…" : "Mark entry"}
                </button>
              ) : (
                <button
                  type="button"
                  data-testid="mark-exit"
                  disabled={marking !== null}
                  onClick={() => handleMark("exit")}
                  className="rounded-md border border-rose-700 bg-rose-800/40 px-3 py-1.5 text-sm font-medium text-rose-200 transition-colors hover:bg-rose-700/40 focus:outline-none focus:ring-1 focus:ring-rose-500 active:bg-rose-700/60 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {marking === "exit" ? "Recording…" : "Mark exit"}
                </button>
              )}
              {markError && (
                <p
                  data-testid="mark-error"
                  className="w-full text-sm text-rose-400"
                  role="alert"
                >
                  {markError}
                </p>
              )}
            </div>
          )}
        </div>
      )}

      {/* Resolution controls (J-50): record this thesis as played out or abandoned. Shown only on a
          LIVE thesis — a system-owned invalidated thesis is already resolved (terminal treatment
          above, no user controls). Copy is descriptive/thesis-attributed, never imperative. Abandon
          is WITHDRAWN once an entry mark exists (anti-survivorship, J-52). */}
      {canResolve && (
        <div
          data-testid="thesis-resolve"
          className="mt-3 flex flex-wrap items-center gap-2 border-t border-slate-800 pt-3"
        >
          <span className="text-xs text-slate-500">Close out your thesis:</span>
          <button
            type="button"
            data-testid="resolve-played-out"
            disabled={resolving !== null}
            onClick={() => handleResolve("played_out")}
            className="rounded-md border border-slate-700 bg-slate-800 px-3 py-1.5 text-sm font-medium text-slate-200 transition-colors hover:border-slate-600 hover:bg-slate-700 focus:outline-none focus:ring-1 focus:ring-slate-500 active:bg-slate-600 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {resolving === "played_out" ? "Resolving…" : "Played out"}
          </button>
          {/* Abandon is NOT rendered at all once an entry mark exists (anti-survivorship, J-52
              closing J-50's deferred clause): a real position is never abandoned. An unmarked thesis
              still offers it (J-50 must not regress). */}
          {canAbandon && (
            <button
              type="button"
              data-testid="resolve-abandon"
              disabled={resolving !== null}
              onClick={() => handleResolve("abandoned")}
              className="rounded-md border border-slate-700 bg-slate-800 px-3 py-1.5 text-sm font-medium text-slate-300 transition-colors hover:border-slate-600 hover:bg-slate-700 focus:outline-none focus:ring-1 focus:ring-slate-500 active:bg-slate-600 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {resolving === "abandoned" ? "Resolving…" : "Abandon"}
            </button>
          )}
          {resolveError && (
            <p
              data-testid="resolve-error"
              className="w-full text-sm text-rose-400"
              role="alert"
            >
              {resolveError}
            </p>
          )}
        </div>
      )}
    </StripShell>
  );
}

export function ThesisStrip({
  ticker,
  thesis,
  last,
}: {
  ticker: string;
  // The active-thesis projection carried on the live snapshot's `thesis` key (or null/undefined).
  thesis: ThesisProjection | null | undefined;
  // The current last price (off the live snapshot) — prefills the mark price field on the active
  // thesis. Optional/null when there is no last yet.
  last?: number | null;
}) {
  const [open, setOpen] = useState(false);
  const [taxonomy, setTaxonomy] = useState<ResearchTaxonomy | null>(null);
  const [taxonomyError, setTaxonomyError] = useState(false);
  const [setupType, setSetupType] = useState("");
  const [direction, setDirection] = useState("");
  const [invalidation, setInvalidation] = useState("");
  const [level, setLevel] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  // Load the taxonomy when the form opens OR when a thesis is active (so the verdict label/copy is
  // taxonomy-owned, not hardcoded). The idle line still costs no request. The form is fully driven
  // by it — the frontend hardcodes no setup/direction/verdict label.
  useEffect(() => {
    if ((!open && !thesis) || taxonomy) return;
    let cancelled = false;
    fetchTaxonomy().then((t) => {
      if (cancelled) return;
      if (!t) {
        setTaxonomyError(true);
        return;
      }
      setTaxonomy(t);
      // Default to the first setup/direction so the form is immediately valid to submit.
      if (t.setups[0]) setSetupType(t.setups[0].id);
      if (t.directions[0]) setDirection(t.directions[0].id);
    });
    return () => {
      cancelled = true;
    };
  }, [open, thesis, taxonomy]);

  // A thesis always wins — render it verbatim (the form is only for the idle state). A SURVIVING
  // entry-marked thesis on a stopped/restarted/mismatched watch reads as not-evaluated (J-47): it
  // is shown as the honest not-currently-evaluated variant (no live verdict, no controls) rather
  // than the live active display — read entirely from the projection (no client-side inference).
  if (thesis) {
    if (thesis.monitor_status === "not_evaluated") {
      return <NotEvaluatedThesis thesis={thesis} />;
    }
    return <ActiveThesis thesis={thesis} taxonomy={taxonomy} last={last ?? null} />;
  }

  const selectedSetup = taxonomy?.setups.find((s) => s.id === setupType);
  const requiresLevel = selectedSetup?.requires_level ?? false;

  function resetForm() {
    setOpen(false);
    setFormError(null);
    setInvalidation("");
    setLevel("");
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setFormError(null);
    const invalidationNum = Number(invalidation);
    if (!invalidation.trim() || Number.isNaN(invalidationNum)) {
      setFormError("Enter an invalidation price.");
      return;
    }
    let levelNum: number | null = null;
    if (requiresLevel) {
      if (!level.trim() || Number.isNaN(Number(level))) {
        setFormError("This setup needs a level price.");
        return;
      }
      levelNum = Number(level);
    }
    setSubmitting(true);
    const result = await declareThesis({
      ticker,
      setup_type: setupType,
      direction,
      invalidation_price: invalidationNum,
      level_price: levelNum,
    });
    setSubmitting(false);
    if (result.ok) {
      // Success: the WS frame will carry the active thesis on its own — just close the form. Form
      // values are preserved on failure (below) so the user can correct an inline rejection.
      resetForm();
    } else {
      // Surface the backend detail VERBATIM (422/409/404) — nothing was created, no coercion.
      setFormError(result.error ?? "The thesis could not be declared.");
    }
  }

  // Idle: a single one-line declare affordance — nothing else moves (J-68 strip-idle clause).
  if (!open) {
    return (
      <StripShell>
        <div className="flex items-center justify-between gap-3">
          <span className="text-sm text-slate-400">
            Declare a thesis on this ticker to watch the tape judged against it.
          </span>
          <button
            type="button"
            onClick={() => setOpen(true)}
            className="rounded-md border border-slate-700 bg-slate-800 px-3 py-1.5 text-sm font-medium text-slate-200 transition-colors hover:border-slate-600 hover:bg-slate-700 focus:outline-none focus:ring-1 focus:ring-slate-500 active:bg-slate-600"
          >
            Declare thesis
          </button>
        </div>
      </StripShell>
    );
  }

  // The taxonomy failed to load — explicit honest state, never a fabricated form.
  if (taxonomyError) {
    return (
      <StripShell>
        <div className="flex items-center justify-between gap-3">
          <span className="text-sm text-rose-400">
            Couldn’t load the setup catalog. The thesis form is unavailable.
          </span>
          <button
            type="button"
            onClick={resetForm}
            className="rounded-md border border-slate-700 bg-slate-800 px-3 py-1.5 text-sm text-slate-300 hover:bg-slate-700"
          >
            Close
          </button>
        </div>
      </StripShell>
    );
  }

  // Form open but the taxonomy is still loading.
  if (!taxonomy) {
    return (
      <StripShell>
        <span className="text-sm text-slate-500">Loading the setup catalog…</span>
      </StripShell>
    );
  }

  const inputCls =
    "rounded-md border border-slate-700 bg-slate-950 px-2 py-1.5 text-sm text-slate-200 focus:border-slate-500 focus:outline-none focus:ring-1 focus:ring-slate-500";

  return (
    <StripShell>
      <form onSubmit={handleSubmit}>
        <div className="flex flex-wrap items-end gap-3">
          <label className="flex flex-col gap-1 text-xs text-slate-500">
            Setup
            <select
              className={inputCls}
              value={setupType}
              onChange={(e) => {
                setSetupType(e.target.value);
                setFormError(null);
              }}
            >
              {taxonomy.setups.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name}
                </option>
              ))}
            </select>
          </label>

          <label className="flex flex-col gap-1 text-xs text-slate-500">
            Direction
            <select
              className={inputCls}
              value={direction}
              onChange={(e) => setDirection(e.target.value)}
            >
              {taxonomy.directions.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name}
                </option>
              ))}
            </select>
          </label>

          <label className="flex flex-col gap-1 text-xs text-slate-500">
            Invalidation
            <input
              type="number"
              step="any"
              inputMode="decimal"
              className={`${inputCls} w-28 font-mono`}
              value={invalidation}
              onChange={(e) => setInvalidation(e.target.value)}
              placeholder="price"
            />
          </label>

          {/* Level field appears ONLY when the selected setup requires it (taxonomy-driven). */}
          {requiresLevel && (
            <label className="flex flex-col gap-1 text-xs text-slate-500">
              Level
              <input
                type="number"
                step="any"
                inputMode="decimal"
                className={`${inputCls} w-28 font-mono`}
                value={level}
                onChange={(e) => setLevel(e.target.value)}
                placeholder="price"
              />
            </label>
          )}

          <button
            type="submit"
            disabled={submitting}
            className="rounded-md border border-emerald-700 bg-emerald-800/40 px-3 py-1.5 text-sm font-medium text-emerald-200 transition-colors hover:bg-emerald-700/40 focus:outline-none focus:ring-1 focus:ring-emerald-500 active:bg-emerald-700/60 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {submitting ? "Declaring…" : "Declare"}
          </button>
          <button
            type="button"
            onClick={resetForm}
            className="rounded-md border border-slate-700 bg-slate-800 px-3 py-1.5 text-sm text-slate-300 transition-colors hover:bg-slate-700 focus:outline-none focus:ring-1 focus:ring-slate-500"
          >
            Cancel
          </button>
        </div>

        {/* Inline backend validation message (422/409/404) — surfaced verbatim, nothing created. */}
        {formError && (
          <p className="mt-2 text-sm text-rose-400" role="alert">
            {formError}
          </p>
        )}
        <p className="mt-2 text-xs text-slate-600">
          Descriptive only — not trading advice.
        </p>
      </form>
    </StripShell>
  );
}
