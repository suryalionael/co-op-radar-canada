"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const LINKS = [
  { href: "/", label: "Jobs" },
  { href: "/companies/", label: "Companies" },
  { href: "/programs/", label: "Programs" },
  { href: "/about/", label: "About" },
];

export function Nav() {
  const pathname = usePathname();
  return (
    <nav aria-label="Main">
      <ul className="flex gap-1 md:gap-4">
        {LINKS.map(({ href, label }) => {
          const current = href === "/" ? pathname === "/" : pathname.startsWith(href.replace(/\/$/, ""));
          return (
            <li key={href}>
              <Link
                href={href}
                aria-current={current ? "page" : undefined}
                className={`inline-flex min-h-11 items-center border-b-[3px] px-1.5 pt-0.5 font-display text-base font-bold transition-colors md:text-[1.0625rem] ${
                  current ? "border-signal text-rail-fg" : "border-transparent text-rail-muted hover:text-rail-fg"
                }`}
              >
                {label}
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
