"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const LINKS = [
  { href: "/", label: "Postings" },
  { href: "/programs/", label: "Program watch" },
  { href: "/about/", label: "About" },
];

export function Nav() {
  const pathname = usePathname();
  return (
    <nav aria-label="Main">
      <ul className="flex gap-1">
        {LINKS.map(({ href, label }) => {
          const current = pathname === href || pathname === href.replace(/\/$/, "");
          return (
            <li key={href}>
              <Link
                href={href}
                aria-current={current ? "page" : undefined}
                className={`inline-flex min-h-11 items-center px-2 text-base transition-colors hover:text-accent ${
                  current ? "font-semibold underline decoration-accent decoration-2 underline-offset-8" : "text-muted"
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
