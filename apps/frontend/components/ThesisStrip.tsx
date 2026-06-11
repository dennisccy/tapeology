"use client";

import { useEffect, useState } from "react";
import { declareThesis, fetchTaxonomy, resolveThesis } from "@/lib/api";
import type {
  ResearchTaxonomy,
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

function ActiveThesis({
  thesis,
  taxonomy,
}: {
  thesis: ThesisProjection;
  taxonomy: ResearchTaxonomy | null;
}) {
  const directionColor =
    thesis.direction === "long" ? "text-emerald-400" : "text-rose-400";
  const isInvalidated = thesis.verdict === "invalidated";
  const verdictChip = VERDICT_STYLE[thesis.verdict] ?? VERDICT_STYLE.pending;
  const evidenceColor =
    VERDICT_EVIDENCE_COLOR[thesis.verdict] ?? VERDICT_EVIDENCE_COLOR.pending;

  // User resolution (J-50): the two record actions on a LIVE thesis. System-owned terminal states
  // (invalidated) carry no user controls — the strip shows their terminal treatment instead. On
  // success the next WS frame carries `thesis: null`, so the strip returns to the declare affordance
  // on its own (the frontend derives nothing). A 409/422 surfaces an explicit inline message.
  const [resolving, setResolving] = useState<"played_out" | "abandoned" | null>(
    null,
  );
  const [resolveError, setResolveError] = useState<string | null>(null);
  const canResolve = !isInvalidated;

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

      {/* Resolution controls (J-50): record this thesis as played out or abandoned. Shown only on a
          LIVE thesis — a system-owned invalidated thesis is already resolved (terminal treatment
          above, no user controls). Copy is descriptive/thesis-attributed, never imperative. */}
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
          <button
            type="button"
            data-testid="resolve-abandon"
            disabled={resolving !== null}
            onClick={() => handleResolve("abandoned")}
            className="rounded-md border border-slate-700 bg-slate-800 px-3 py-1.5 text-sm font-medium text-slate-300 transition-colors hover:border-slate-600 hover:bg-slate-700 focus:outline-none focus:ring-1 focus:ring-slate-500 active:bg-slate-600 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {resolving === "abandoned" ? "Resolving…" : "Abandon"}
          </button>
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
}: {
  ticker: string;
  // The active-thesis projection carried on the live snapshot's `thesis` key (or null/undefined).
  thesis: ThesisProjection | null | undefined;
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

  // An active thesis always wins — render it verbatim (the form is only for the idle state).
  if (thesis) {
    return <ActiveThesis thesis={thesis} taxonomy={taxonomy} />;
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
