"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const links = [
  { href: "/", label: "Cockpit" },
  { href: "/compare", label: "Compare" },
  { href: "/evals", label: "Evals" },
  { href: "/traces", label: "Traces" },
  { href: "/guardrails", label: "Guardrails" },
  { href: "/deploy-gate", label: "Deploy gate" },
];

export function SiteNav() {
  const path = usePathname();
  return (
    <header className="sticky top-0 z-30 border-b border-ink-700/60 bg-ink-900/80 backdrop-blur">
      <div className="mx-auto flex w-full max-w-7xl items-center justify-between px-6 py-3">
        <Link href="/" className="flex items-center gap-2">
          <span className="grid h-7 w-7 place-items-center rounded-md bg-gradient-to-br from-forge-accent to-forge-ice font-mono text-sm text-white shadow-glow">
            EF
          </span>
          <span className="font-mono text-sm tracking-[0.18em] text-ink-100">
            EVAL<span className="text-forge-ice">FORGE</span>
          </span>
        </Link>
        <nav className="flex items-center gap-1">
          {links.map((l) => {
            const active =
              l.href === "/" ? path === "/" : path?.startsWith(l.href);
            return (
              <Link
                key={l.href}
                href={l.href}
                data-testid={`nav-${l.label.toLowerCase().replace(/\s+/g, "-")}`}
                className={
                  "rounded-md px-3 py-1.5 text-sm transition " +
                  (active
                    ? "bg-ink-800 text-ink-100 shadow-glow"
                    : "text-ink-300 hover:bg-ink-800/60 hover:text-ink-100")
                }
              >
                {l.label}
              </Link>
            );
          })}
        </nav>
      </div>
    </header>
  );
}
