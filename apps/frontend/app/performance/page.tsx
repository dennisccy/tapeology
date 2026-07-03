"use client";

import { useEffect, useState } from "react";
import { fetchPnlLedger, fetchProfiles } from "@/lib/api";
import type {
  PnlLedger,
  PnlLedgerRow,
  PnlSplitMeasurement,
  ProfilesPayload,
} from "@/lib/types";
import { formatDateDMY } from "@/lib/datetime";

// The /performance page (J-05) — the era's scorekeeping surface, reached from the fourth top-bar
// link (the nav renders GET /meta/ui-routes; this page ships together with its route-map entry).
//
// TWO canonical endpoints, rendered VERBATIM and nothing else:
//   * GET /research/pnl/ledger  (Data Contract row 32) — one append-only row per enhancement.
//   * GET /research/profiles    (Data Contract row 33) — the profile registry + champion pointer
//     (the ONLY source of the champion — never inferred from ledger provenance, never hardcoded).
//
// The page computes NOTHING: no arithmetic, no rounding, no re-formatting, no derived figures.
// Every numeric renders as String(value) — the same shortest round-trip decimal the API's JSON
// carries — so a value shown on the page equals the API value exactly (the committed
// reports/pnl/pnl-history.md full-precision render is the precedent). Train and hold-out are
// SEPARATE column groups (never pooled; no combined figure exists anywhere); each $ sits beside
// its R and its n; the API's `insufficient_sample` labels render as served; a founding row's
// null baseline renders an explicit absence marker — NEVER fabricated zeros. The visible
// simulated register is the API payload's `register` string — no frontend copy of it exists.
//
// States are honest and distinct: loading; backend unreachable → explicit per-panel unavailable
// state (the NavBar degraded-state pattern — never cached or fabricated rows); empty ledger →
// explicit empty state. Dark instrument-panel style consistent with /journal and /studies:
// slate surfaces, restrained borders, font-mono numerics, amber for degraded/insufficient.

const NUMERIC_CELL = "px-2 py-1.5 text-right font-mono text-xs text-slate-200 whitespace-nowrap";
const HEADER_CELL = "px-2 py-1 text-right text-[11px] font-medium text-slate-500";
const LABEL_CELL = "px-2 py-1.5 text-left text-xs text-slate-400 whitespace-nowrap";

// One measured split as one table row — the EXACT committed pnl-history.md table shape
// (side | split | net R | net $ | n | sample): train and hold-out stay separate rows, never
// pooled; values as served; the sample label driven solely by the API's `insufficient_sample`
// boolean and served minimum.
function MeasurementRow({
  side,
  split,
  m,
  minN,
}: {
  side: string;
  split: string;
  m: PnlSplitMeasurement;
  minN: number;
}) {
  return (
    <tr className="border-b border-slate-800/60 last:border-b-0">
      <td className={LABEL_CELL}>{side}</td>
      <td className={LABEL_CELL}>{split}</td>
      <td className={NUMERIC_CELL}>{String(m.net_r)}</td>
      <td className={NUMERIC_CELL}>{String(m.net_usd)}</td>
      <td className={NUMERIC_CELL}>{String(m.n)}</td>
      <td className="px-2 py-1.5 text-left">
        {m.insufficient_sample ? (
          <span className="inline-block whitespace-nowrap rounded border border-amber-800/60 bg-amber-900/20 px-1.5 py-0.5 text-[11px] text-amber-300">
            {`insufficient sample (n < ${minN})`}
          </span>
        ) : (
          <span className="text-[11px] text-slate-500">ok</span>
        )}
      </td>
    </tr>
  );
}

// One ledger row: title + id + date + the split table (baseline rows, candidate rows) + provenance.
function LedgerRowPanel({ row, minN }: { row: PnlLedgerRow; minN: number }) {
  const provenance = row.provenance;
  return (
    <article
      data-testid="ledger-row"
      data-enhancement-id={row.enhancement_id}
      className="rounded-lg border border-slate-800 bg-slate-900/60 p-4"
    >
      <header className="mb-3">
        <h3 className="text-sm font-semibold text-slate-200">{row.title}</h3>
        <p className="mt-0.5 font-mono text-[11px] text-slate-500">{row.enhancement_id}</p>
        <p className="mt-0.5 text-[11px] text-slate-500">
          Appended <span className="font-mono text-slate-400">{formatDateDMY(row.created_utc)}</span>
        </p>
      </header>

      <div className="overflow-x-auto">
        <table className="w-full border-collapse">
          <thead>
            <tr className="border-b border-slate-800">
              <th className="px-2 py-1 text-left text-[11px] font-medium text-slate-500">side</th>
              <th className="px-2 py-1 text-left text-[11px] font-medium text-slate-500">split</th>
              <th className={HEADER_CELL}>net R</th>
              <th className={HEADER_CELL}>net $</th>
              <th className={HEADER_CELL}>n</th>
              <th className="px-2 py-1 text-left text-[11px] font-medium text-slate-500">sample</th>
            </tr>
          </thead>
          <tbody>
            {row.baseline === null ? (
              <tr className="border-b border-slate-800/60">
                <td className={LABEL_CELL}>baseline</td>
                <td
                  colSpan={5}
                  data-testid="ledger-founding-marker"
                  className="px-2 py-1.5 text-left text-xs text-slate-500"
                >
                  no prior incumbent — founding row (the baseline side is explicitly absent, never
                  zeros)
                </td>
              </tr>
            ) : (
              <>
                <MeasurementRow side="baseline" split="train" m={row.baseline.train} minN={minN} />
                <MeasurementRow
                  side="baseline"
                  split="hold-out"
                  m={row.baseline.holdout}
                  minN={minN}
                />
              </>
            )}
            <MeasurementRow side="candidate" split="train" m={row.candidate.train} minN={minN} />
            <MeasurementRow
              side="candidate"
              split="hold-out"
              m={row.candidate.holdout}
              minN={minN}
            />
          </tbody>
        </table>
      </div>

      <footer className="mt-3 space-y-0.5 font-mono text-[11px] text-slate-500">
        <p>
          strategy {provenance.strategy_id} · profile {provenance.profile} · fingerprint{" "}
          <span className="break-all">{provenance.config_fingerprint}</span>
        </p>
        <p className="break-all">
          train: backtest {provenance.train.backtest_id} · dataset {provenance.train.dataset_id} ·
          checksum {provenance.train.dataset_checksum}
        </p>
        <p className="break-all">
          hold-out: backtest {provenance.holdout.backtest_id} · dataset{" "}
          {provenance.holdout.dataset_id} · checksum {provenance.holdout.dataset_checksum}
        </p>
      </footer>
    </article>
  );
}

// The explicit per-panel unavailable state (the NavBar degraded-state pattern): honestly no
// data — never cached or fabricated rows.
function UnavailablePanel({ testid, message }: { testid: string; message: string }) {
  return (
    <div
      data-testid={testid}
      className="rounded-lg border border-amber-800/60 bg-amber-900/20 px-4 py-6 text-center"
    >
      <p className="text-sm font-medium text-amber-300">{message}</p>
      <p className="mt-1 text-xs text-amber-200/70">
        Nothing cached and nothing fabricated is shown in its place.
      </p>
    </div>
  );
}

// A quiet loading placeholder (no fabricated values — just a pulse block).
function LoadingPanel({ testid }: { testid: string }) {
  return (
    <div
      data-testid={testid}
      className="animate-pulse rounded-lg border border-slate-800 bg-slate-900/40 px-4 py-6"
    >
      <div className="h-3 w-1/3 rounded bg-slate-800" />
      <div className="mt-3 h-3 w-2/3 rounded bg-slate-800" />
      <div className="mt-3 h-3 w-1/2 rounded bg-slate-800" />
    </div>
  );
}

export default function PerformancePage() {
  // null = fetch in flight; { ok: false } resolves to the explicit unavailable state.
  const [ledgerResult, setLedgerResult] = useState<{
    ok: boolean;
    ledger: PnlLedger | null;
    error?: string;
  } | null>(null);
  const [profilesResult, setProfilesResult] = useState<{
    ok: boolean;
    profiles: ProfilesPayload | null;
    error?: string;
  } | null>(null);

  useEffect(() => {
    let alive = true;
    fetchPnlLedger().then((result) => {
      if (alive) setLedgerResult(result);
    });
    fetchProfiles().then((result) => {
      if (alive) setProfilesResult(result);
    });
    return () => {
      alive = false;
    };
  }, []);

  const ledger = ledgerResult?.ok ? ledgerResult.ledger : null;
  const profiles = profilesResult?.ok ? profilesResult.profiles : null;

  return (
    <div className="min-h-screen">
      <main className="mx-auto max-w-7xl px-4 py-6">
        <header className="mb-4">
          <h1 data-testid="performance-title" className="text-lg font-semibold text-slate-200">
            Performance
          </h1>
          <p className="mt-1 max-w-3xl text-sm text-slate-500">
            The era&apos;s scorekeeping: one append-only PnL-ledger row per enhancement — net R
            and net $ per frozen split, each with its n — beside the current champion.
          </p>
          <p data-testid="performance-framing" className="mt-2 max-w-3xl text-xs text-slate-600">
            Simulated measurements of recorded historical tape under the disclosed fee/slippage
            assumptions — not live results, not a forecast, and not a profitability claim. Train
            and hold-out figures are separate and never pooled.
          </p>
        </header>

        <div className="grid grid-cols-1 gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(0,340px)]">
          {/* The PnL ledger (row 32), rendered verbatim. */}
          <section aria-label="PnL ledger">
            <h2 className="mb-2 text-sm font-semibold text-slate-300">PnL ledger</h2>
            {ledgerResult === null ? (
              <LoadingPanel testid="ledger-loading" />
            ) : !ledgerResult.ok || ledger === null ? (
              <UnavailablePanel
                testid="ledger-unavailable"
                message={ledgerResult.error ?? "The PnL ledger could not be loaded."}
              />
            ) : (
              <div className="space-y-4">
                {/* The visible simulated register — the API payload's own string, verbatim. */}
                <p
                  data-testid="pnl-register"
                  className="rounded border border-amber-800/60 bg-amber-900/20 px-3 py-2 text-xs text-amber-200"
                >
                  {ledger.register}
                </p>
                {ledger.rows.length === 0 ? (
                  <div
                    data-testid="ledger-empty"
                    className="flex min-h-[30vh] flex-col items-center justify-center rounded-lg border border-slate-800 bg-slate-900/40 px-4 py-10 text-center"
                  >
                    <span className="text-2xl text-slate-700">∅</span>
                    <p className="mt-2 text-sm text-slate-500">
                      The PnL ledger is empty — no enhancement has been validated yet.
                    </p>
                  </div>
                ) : (
                  ledger.rows.map((row) => (
                    <LedgerRowPanel
                      key={row.enhancement_id}
                      row={row}
                      minN={ledger.min_sample_size}
                    />
                  ))
                )}
              </div>
            )}
          </section>

          {/* The champion + profile registry (row 33), rendered verbatim. */}
          <aside aria-label="Champion">
            <h2 className="mb-2 text-sm font-semibold text-slate-300">Champion</h2>
            {profilesResult === null ? (
              <LoadingPanel testid="champion-loading" />
            ) : !profilesResult.ok || profiles === null ? (
              <UnavailablePanel
                testid="champion-unavailable"
                message={profilesResult.error ?? "The profile registry could not be loaded."}
              />
            ) : (
              <div
                data-testid="champion-summary"
                className="rounded-lg border border-slate-800 bg-slate-900/60 p-4"
              >
                <dl className="space-y-2">
                  <div className="flex items-baseline justify-between gap-2">
                    <dt className="text-xs text-slate-500">strategy</dt>
                    <dd data-testid="champion-strategy" className="font-mono text-sm text-slate-200">
                      {profiles.champion.strategy_id}
                    </dd>
                  </div>
                  <div className="flex items-baseline justify-between gap-2">
                    <dt className="text-xs text-slate-500">profile</dt>
                    <dd data-testid="champion-profile" className="font-mono text-sm text-slate-200">
                      {profiles.champion.profile}
                    </dd>
                  </div>
                </dl>
                <p className="mt-2 text-[11px] text-slate-600">
                  The current champion pointer, read verbatim from the profile registry endpoint.
                </p>

                <h3 className="mt-4 text-xs font-semibold text-slate-400">Profile registry</h3>
                <ul className="mt-1 space-y-1">
                  {profiles.profiles.map((profile) => (
                    <li
                      key={profile.id}
                      data-testid="profile-row"
                      className="flex flex-wrap items-center gap-1.5 text-xs"
                    >
                      <span className="font-mono text-slate-200">{profile.id}</span>
                      <span className="rounded border border-slate-700 bg-slate-800/60 px-1.5 py-0.5 text-[10px] text-slate-400">
                        {profile.frozen ? "frozen" : "not frozen"}
                      </span>
                      <span className="rounded border border-slate-700 bg-slate-800/60 px-1.5 py-0.5 text-[10px] text-slate-400">
                        {profile.is_default ? "default" : "candidate"}
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </aside>
        </div>
      </main>
    </div>
  );
}
