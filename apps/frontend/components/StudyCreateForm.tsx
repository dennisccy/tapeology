"use client";

import { useMemo, useState } from "react";
import type { CreateStudyParams, ResearchTaxonomy } from "@/lib/types";
import { SymbolSearch } from "@/components/SymbolSearch";
import {
  ET_SESSION_CLOSE,
  ET_SESSION_OPEN,
  isValidDMY,
  localZoneLabel,
  parseDMYToIsoDate,
  resolveLocalWindowInstant,
  resolveSessionPreset,
} from "@/lib/datetime";

// The study create form (J-60). Source pick (reference quick-pick / seeded sim / arbitrary symbol +
// past window), setup × direction, and a level input shown ONLY for the two level setups (with the
// hindsight warning). For the arbitrary-window source it reuses the SAME symbol search + dd-MM-yyyy
// custom date input + the row-12 local-window resolver the cockpit uses (no second timezone path).
//
// The form does NO business logic — it builds the POST body and surfaces the backend's verbatim 422
// inline. All labels come from the taxonomy. Dark instrument-panel style; every control has hover /
// focus / active states. The Run button is disabled until the required fields are present (a courtesy;
// the backend remains the validation authority).

const REFERENCE_SOURCE_ID = "PG_SIP_REFERENCE";

// Sim scenarios that drive the two state-native setups (the reserved regime sims). Surfaced as a
// small select; the backend validates the id (an unknown sim is a 422).
const SIM_SCENARIOS = ["SIM-REVERSAL", "SIM-BUYER", "SIM-SHIFT", "SIM-SELLER"];

type SourceKind = "reference" | "sim" | "historical";

export function StudyCreateForm({
  taxonomy,
  onCreate,
  creating,
  error,
}: {
  taxonomy: ResearchTaxonomy | null;
  onCreate: (params: CreateStudyParams) => void;
  creating: boolean;
  error: string | null;
}) {
  const copy = taxonomy?.studies?.copy ?? {};
  const setups = taxonomy?.setups ?? [];
  const directions = taxonomy?.directions ?? [];
  const levelSetups = useMemo(
    () => new Set(taxonomy?.studies?.level_setups ?? ["level_break", "failed_move_fade"]),
    [taxonomy],
  );

  const [sourceKind, setSourceKind] = useState<SourceKind>("reference");
  const [simId, setSimId] = useState(SIM_SCENARIOS[0]);
  const [symbol, setSymbol] = useState("");
  const [dateStr, setDateStr] = useState("");
  const [startTime, setStartTime] = useState("");
  const [endTime, setEndTime] = useState("");
  const [setupType, setSetupType] = useState("absorption_reversal");
  const [direction, setDirection] = useState("long");
  const [levelPrice, setLevelPrice] = useState("");

  const requiresLevel = levelSetups.has(setupType);

  // The Run button is enabled when the required fields for the chosen source are present (courtesy;
  // the backend is the authority). A level setup needs a level; a historical study needs a symbol +
  // a valid date + both times.
  const canSubmit = useMemo(() => {
    if (requiresLevel && levelPrice.trim() === "") return false;
    if (sourceKind === "historical") {
      if (!symbol.trim() || !isValidDMY(dateStr) || !startTime || !endTime) return false;
    }
    return !creating;
  }, [requiresLevel, levelPrice, sourceKind, symbol, dateStr, startTime, endTime, creating]);

  const applyPreset = (which: "open" | "close" | "rth") => {
    const iso = parseDMYToIsoDate(dateStr);
    if (!iso) return;
    const start = ET_SESSION_OPEN;
    const end = which === "open" ? { hour: 9, minute: 35 } : ET_SESSION_CLOSE;
    const close = which === "close" ? { hour: 15, minute: 55 } : ET_SESSION_CLOSE;
    const preset = resolveSessionPreset(
      iso,
      which === "close" ? close : start,
      which === "open" ? end : ET_SESSION_CLOSE,
    );
    if (!preset) return;
    setStartTime(preset.startTimeInput);
    setEndTime(preset.endTimeInput);
  };

  const handleSubmit = () => {
    const base: CreateStudyParams = {
      source_kind: sourceKind,
      source_id:
        sourceKind === "reference"
          ? REFERENCE_SOURCE_ID
          : sourceKind === "sim"
            ? simId
            : symbol.trim().toUpperCase(),
      setup_type: setupType,
      direction,
    };
    if (requiresLevel && levelPrice.trim() !== "") {
      base.level_price = Number(levelPrice);
    }
    if (sourceKind === "historical") {
      const iso = parseDMYToIsoDate(dateStr);
      if (iso) {
        base.start = resolveLocalWindowInstant(iso, startTime);
        base.end = resolveLocalWindowInstant(iso, endTime);
      }
    }
    onCreate(base);
  };

  return (
    <section
      data-testid="study-create-form"
      className="rounded-lg border border-slate-800 bg-slate-900/40 p-4"
    >
      <h2 className="mb-3 text-sm font-semibold text-slate-200">
        {copy.create_title ?? "New study"}
      </h2>

      <div className="space-y-3">
        {/* Source picker. */}
        <Field label={copy.source_label ?? "Source"}>
          <div role="radiogroup" aria-label="Source" className="flex flex-col gap-1.5">
            <SourceRadio
              checked={sourceKind === "reference"}
              onChange={() => setSourceKind("reference")}
              label={copy.reference_source_label ?? "Reference window (committed PG SIP fixture — no credentials)"}
              testid="source-reference"
            />
            <SourceRadio
              checked={sourceKind === "sim"}
              onChange={() => setSourceKind("sim")}
              label={copy.sim_source_label ?? "Seeded sim scenario"}
              testid="source-sim"
            />
            <SourceRadio
              checked={sourceKind === "historical"}
              onChange={() => setSourceKind("historical")}
              label={copy.historical_source_label ?? "Symbol + past window"}
              testid="source-historical"
            />
          </div>
        </Field>

        {/* Source-specific controls. */}
        {sourceKind === "sim" && (
          <Field label="Sim scenario">
            <select
              data-testid="study-sim-select"
              value={simId}
              onChange={(e) => setSimId(e.target.value)}
              className={selectClass}
            >
              {SIM_SCENARIOS.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </Field>
        )}

        {sourceKind === "historical" && (
          <>
            <Field label="Symbol">
              <SymbolSearch
                value={symbol}
                onChange={setSymbol}
                onPick={setSymbol}
                placeholder="e.g. AAPL"
                ariaLabel="Study symbol"
                inputClassName={inputClass}
              />
            </Field>
            <Field label={`Date (dd-MM-yyyy, ${localZoneLabel()})`}>
              <input
                data-testid="study-date"
                value={dateStr}
                onChange={(e) => setDateStr(e.target.value)}
                placeholder="dd-MM-yyyy"
                className={inputClass}
              />
            </Field>
            <div className="flex gap-2">
              <Field label="Start (HH:mm)">
                <input
                  data-testid="study-start-time"
                  type="time"
                  value={startTime}
                  onChange={(e) => setStartTime(e.target.value)}
                  className={inputClass}
                />
              </Field>
              <Field label="End (HH:mm)">
                <input
                  data-testid="study-end-time"
                  type="time"
                  value={endTime}
                  onChange={(e) => setEndTime(e.target.value)}
                  className={inputClass}
                />
              </Field>
            </div>
            <div className="flex flex-wrap gap-1.5">
              <PresetButton onClick={() => applyPreset("open")} label="Open 9:30 ET" disabled={!isValidDMY(dateStr)} />
              <PresetButton onClick={() => applyPreset("close")} label="Close 16:00 ET" disabled={!isValidDMY(dateStr)} />
              <PresetButton onClick={() => applyPreset("rth")} label="Full RTH" disabled={!isValidDMY(dateStr)} />
            </div>
          </>
        )}

        {/* Setup × direction. */}
        <div className="flex gap-2">
          <Field label={copy.setup_label ?? "Setup"}>
            <select
              data-testid="study-setup"
              value={setupType}
              onChange={(e) => setSetupType(e.target.value)}
              className={selectClass}
            >
              {setups.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name}
                </option>
              ))}
            </select>
          </Field>
          <Field label={copy.direction_label ?? "Direction"}>
            <select
              data-testid="study-direction"
              value={direction}
              onChange={(e) => setDirection(e.target.value)}
              className={selectClass}
            >
              {directions.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name}
                </option>
              ))}
            </select>
          </Field>
        </div>

        {/* Level input — ONLY for the two level setups, with the hindsight warning. */}
        {requiresLevel && (
          <Field label={copy.level_label ?? "Level price (required for level setups)"}>
            <input
              data-testid="study-level"
              type="number"
              step="0.01"
              value={levelPrice}
              onChange={(e) => setLevelPrice(e.target.value)}
              placeholder="e.g. 100.50"
              className={`${inputClass} font-mono`}
            />
            <p
              data-testid="study-hindsight-warning"
              className="mt-1 rounded border border-amber-800/60 bg-amber-900/20 px-2 py-1 text-[11px] text-amber-200"
            >
              {copy.hindsight_level_caption ??
                "This level setup uses a level you supply with hindsight — illustrative only and excluded from any cross-study comparison."}
            </p>
          </Field>
        )}

        {/* The backend's verbatim 422 inline. */}
        {error && (
          <div
            data-testid="study-create-error"
            role="alert"
            className="rounded-md border border-rose-700/70 bg-rose-900/30 px-3 py-2 text-xs text-rose-200"
          >
            {error}
          </div>
        )}

        <button
          type="button"
          data-testid="study-create-button"
          disabled={!canSubmit}
          onClick={handleSubmit}
          className="w-full rounded-md border border-slate-700 bg-slate-800 px-3 py-2 text-sm font-medium text-slate-100 transition-colors hover:bg-slate-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-slate-500 active:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {creating ? "Running…" : copy.create_button ?? "Run study"}
        </button>
      </div>
    </section>
  );
}

const inputClass =
  "w-full rounded-md border border-slate-700 bg-slate-950/60 px-2.5 py-1.5 text-sm text-slate-200 placeholder:text-slate-600 focus:border-slate-500 focus:outline-none focus:ring-1 focus:ring-slate-600";
const selectClass = inputClass + " cursor-pointer";

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block flex-1">
      <span className="mb-1 block text-xs font-medium uppercase tracking-wider text-slate-500">
        {label}
      </span>
      {children}
    </label>
  );
}

function SourceRadio({
  checked,
  onChange,
  label,
  testid,
}: {
  checked: boolean;
  onChange: () => void;
  label: string;
  testid: string;
}) {
  return (
    <label
      data-testid={testid}
      className={`flex cursor-pointer items-start gap-2 rounded-md border px-2.5 py-1.5 text-xs transition-colors ${
        checked
          ? "border-slate-600 bg-slate-800 text-slate-100"
          : "border-slate-800 bg-slate-950/40 text-slate-400 hover:border-slate-700 hover:text-slate-200"
      }`}
    >
      <input
        type="radio"
        checked={checked}
        onChange={onChange}
        className="mt-0.5 accent-slate-400"
      />
      <span>{label}</span>
    </label>
  );
}

function PresetButton({
  onClick,
  label,
  disabled,
}: {
  onClick: () => void;
  label: string;
  disabled: boolean;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className="rounded border border-slate-700 bg-slate-800/60 px-2 py-1 text-[11px] text-slate-300 transition-colors hover:bg-slate-700 focus:outline-none focus-visible:ring-1 focus-visible:ring-slate-500 active:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-40"
    >
      {label}
    </button>
  );
}
