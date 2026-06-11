"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

// The persistent app-level navigation top bar (J-51 / approved IA skeleton): Cockpit · Journal ·
// Studies. Layout-mounted so it appears on every page (the first multi-page surface). The cockpit
// remains the home and stays one screen — this bar sits ABOVE it and the cockpit's own watch
// controls, never disturbing the one-screen cockpit grid.
//
// Studies is registered in the approved IA but its PAGE lands with J-60; until then it is shown as a
// DISABLED, non-navigable item (the approved skeleton must never carry a dead link to a missing
// page). It reads as "coming with studies" so the nav is honest about what exists today.
//
// Dark instrument-panel style, consistent with the cockpit: slate surfaces, restrained borders, the
// active link in emerald (the established "live/positive" accent), inactive in muted slate.

interface NavItem {
  href: string;
  label: string;
  enabled: boolean;
}

const NAV_ITEMS: NavItem[] = [
  { href: "/", label: "Cockpit", enabled: true },
  { href: "/journal", label: "Journal", enabled: true },
  // Studies page lands with J-60 — registered in the IA, disabled until its page exists (no dead link).
  { href: "/studies", label: "Studies", enabled: false },
];

export function NavBar() {
  const pathname = usePathname();
  return (
    <nav
      data-testid="app-nav"
      className="sticky top-0 z-30 border-b border-slate-800 bg-slate-950/90 backdrop-blur"
    >
      <div className="mx-auto flex max-w-7xl items-center gap-6 px-4 py-2.5">
        <span className="select-none text-sm font-semibold tracking-wide text-slate-300">
          Tapeology
        </span>
        <ul className="flex items-center gap-1">
          {NAV_ITEMS.map((item) => {
            // Active when the path matches exactly (Cockpit "/") or is nested under the page root
            // (e.g. /journal/[id] keeps Journal active). The cockpit "/" only matches itself.
            const active =
              item.href === "/"
                ? pathname === "/"
                : pathname === item.href || pathname.startsWith(`${item.href}/`);
            if (!item.enabled) {
              return (
                <li key={item.href}>
                  <span
                    data-testid="nav-link-disabled"
                    data-label={item.label}
                    aria-disabled="true"
                    title="Coming with replay studies"
                    className="cursor-not-allowed rounded px-3 py-1.5 text-sm font-medium text-slate-600"
                  >
                    {item.label}
                  </span>
                </li>
              );
            }
            return (
              <li key={item.href}>
                <Link
                  href={item.href}
                  data-testid="nav-link"
                  data-label={item.label}
                  aria-current={active ? "page" : undefined}
                  className={
                    "rounded px-3 py-1.5 text-sm font-medium transition-colors focus:outline-none focus:ring-1 focus:ring-emerald-500 " +
                    (active
                      ? "bg-slate-800 text-emerald-300"
                      : "text-slate-400 hover:bg-slate-900 hover:text-slate-200")
                  }
                >
                  {item.label}
                </Link>
              </li>
            );
          })}
        </ul>
      </div>
    </nav>
  );
}
