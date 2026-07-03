"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { API_BASE, UI_ROUTES_REQUEST_TIMEOUT_MS } from "@/lib/config";

// The persistent app-level navigation top bar (J-51 / approved IA skeleton): Cockpit · Journal ·
// Studies. Layout-mounted so it appears on every page; the cockpit remains the home and stays one
// screen — this bar sits ABOVE it, never disturbing the one-screen cockpit grid.
//
// J-01: the links render from GET /meta/ui-routes — the backend's canonical route map (Data
// Contract row 35) and the SINGLE source of truth for user-facing routes. There is deliberately
// NO hardcoded route list here, not even as a fallback: a fallback list would be exactly the
// hand-maintained duplicate this journey retires. When the route map is unreachable the nav shows
// an explicit degraded state (brand + honest placeholder) — never a fabricated link list. When a
// future page ships (e.g. Performance at J-05), the backend adds its entry and this bar picks it
// up with no frontend edit.
//
// Dark instrument-panel style, consistent with the cockpit: slate surfaces, restrained borders,
// the active link in emerald (the established "live/positive" accent), inactive in muted slate.

// One route-map entry, rendered verbatim (mirrors app/meta.py UI_ROUTES). `nav: false` entries
// (e.g. /journal/[id]) are real routes reached from within pages, not top-bar destinations.
interface UiRoute {
  path: string;
  label: string;
  nav: boolean;
}

export function NavBar() {
  const pathname = usePathname();
  // null = route map not loaded yet (initial fetch in flight); once loaded, links render exactly
  // the endpoint's entries. `unavailable` is the explicit degraded state — never a made-up list.
  const [routes, setRoutes] = useState<UiRoute[] | null>(null);
  const [unavailable, setUnavailable] = useState(false);

  useEffect(() => {
    let cancelled = false;
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), UI_ROUTES_REQUEST_TIMEOUT_MS);
    fetch(`${API_BASE}/meta/ui-routes`, { signal: controller.signal })
      .then((res) => {
        if (!res.ok) throw new Error(`route map HTTP ${res.status}`);
        return res.json();
      })
      .then((body: { routes: UiRoute[] }) => {
        if (!cancelled) {
          setRoutes(body.routes.filter((route) => route.nav));
          setUnavailable(false);
        }
      })
      .catch(() => {
        if (!cancelled) setUnavailable(true);
      })
      .finally(() => clearTimeout(timer));
    return () => {
      cancelled = true;
      controller.abort();
      clearTimeout(timer);
    };
  }, []);

  return (
    <nav
      data-testid="app-nav"
      className="sticky top-0 z-30 border-b border-slate-800 bg-slate-950/90 backdrop-blur"
    >
      <div className="mx-auto flex max-w-7xl items-center gap-6 px-4 py-2.5">
        <span className="select-none text-sm font-semibold tracking-wide text-slate-300">
          Tapeology
        </span>
        {unavailable ? (
          // Explicit degraded state: the route map could not be read, so there are honestly no
          // links to show (amber = the established "unclear/degraded" accent).
          <span
            data-testid="nav-unavailable"
            className="select-none text-xs font-medium text-amber-400/80"
          >
            navigation unavailable — backend unreachable
          </span>
        ) : (
          <ul className="flex items-center gap-1">
            {(routes ?? []).map((route) => {
              // Active when the path matches exactly (Cockpit "/") or is nested under the page
              // root (e.g. /journal/[id] keeps Journal active). The cockpit "/" only matches
              // itself.
              const active =
                route.path === "/"
                  ? pathname === "/"
                  : pathname === route.path || pathname.startsWith(`${route.path}/`);
              return (
                <li key={route.path}>
                  <Link
                    href={route.path}
                    data-testid="nav-link"
                    data-label={route.label}
                    aria-current={active ? "page" : undefined}
                    className={
                      "rounded px-3 py-1.5 text-sm font-medium transition-colors focus:outline-none focus:ring-1 focus:ring-emerald-500 " +
                      (active
                        ? "bg-slate-800 text-emerald-300"
                        : "text-slate-400 hover:bg-slate-900 hover:text-slate-200")
                    }
                  >
                    {route.label}
                  </Link>
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </nav>
  );
}
