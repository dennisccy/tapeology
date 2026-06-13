"use client";

import { useEffect, useState } from "react";
import { fetchTaxonomy } from "@/lib/api";
import type { ResearchTaxonomy } from "@/lib/types";

// The cockpit FEED-BASIS BADGE (capability 28 honesty stamps, J-67; data-contract row 29 + row 24
// copy). Sits in the `/` status area beside the watched-source indicator / lag readout. It renders
// the SERVED current-watch feed basis (`snapshot.data_feed`: sim | iex | sip) VERBATIM with the
// taxonomy-owned per-feed label; on the live IEX basis the taxonomy-owned IEX-vs-SIP disclosure line
// renders beside it. The frontend hardcodes NO feed label or disclosure text — both come from
// `GET /research/taxonomy`'s `feed_basis` block.
//
// Honest absence (J-67): when no watch is active there is no served basis, so the badge renders
// NOTHING — never a fabricated "live"/"iex" guess. The badge is driven SOLELY by the served
// `dataFeed` value; it never derives the basis from the scenario string client-side.
//
// Copy discipline (J-66): the badge adds no imperative/predictive word of its own — its only strings
// are the backend-owned per-feed label + the backend-owned disclosure line.
//
// Color semantics: a neutral slate chip (the basis is a factual stamp, not a side/impact signal — it
// must not borrow the green/red/amber side palette). The live disclosure renders in muted slate too.

export function FeedBasisBadge({
  dataFeed,
}: {
  // The served current-watch feed basis off the snapshot's `data_feed` key (row 29), or
  // null/undefined when there is no watch / a pre-J-67 backend — in which case the badge is ABSENT.
  dataFeed: "sim" | "iex" | "sip" | null | undefined;
}) {
  const [taxonomy, setTaxonomy] = useState<ResearchTaxonomy | null>(null);

  // Load the taxonomy ONLY once a basis is actually served (the badge is absent otherwise, so the
  // idle cockpit costs no request). The taxonomy supplies the per-feed label + the disclosure line.
  useEffect(() => {
    if (!dataFeed || taxonomy) return;
    let cancelled = false;
    fetchTaxonomy().then((t) => {
      if (!cancelled && t) setTaxonomy(t);
    });
    return () => {
      cancelled = true;
    };
  }, [dataFeed, taxonomy]);

  // Honest absence: no watch / no served basis => render nothing (never a fabricated basis).
  if (!dataFeed) return null;

  const feeds = taxonomy?.feed_basis?.feeds ?? [];
  // The per-feed display label, owned by the taxonomy. Falls back to the raw feed id (an honest,
  // never-fabricated value) if the taxonomy has not loaded or lacks the block.
  const label = feeds.find((f) => f.id === dataFeed)?.name ?? dataFeed;
  // The live IEX-vs-SIP disclosure line — rendered ONLY when the served basis IS the live IEX feed
  // (config-aligned: an operator who upgrades live to SIP serves `sip`, and this IEX disclosure then
  // correctly stops showing). Backend-owned copy; the frontend never composes it.
  const disclosure =
    dataFeed === "iex" ? taxonomy?.feed_basis?.live_disclosure ?? null : null;

  return (
    <div className="flex flex-col gap-0.5" data-testid="feed-basis">
      <div className="flex items-center gap-1.5 rounded bg-slate-800 px-2 py-1 text-xs text-slate-300">
        <span className="text-slate-500">feed</span>
        <span className="font-mono font-semibold text-slate-200" data-testid="feed-basis-label">
          {label}
        </span>
      </div>
      {disclosure && (
        <span
          data-testid="feed-basis-disclosure"
          className="max-w-xs text-[11px] leading-tight text-slate-500"
        >
          {disclosure}
        </span>
      )}
    </div>
  );
}
