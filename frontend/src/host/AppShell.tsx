"use client";

import Link from "next/link";
import type { ReactNode } from "react";


export function AppShell({
  children,
  subtitle,
  actions,
}: {
  children: ReactNode;
  subtitle?: string;
  actions?: ReactNode;
}) {

  return (
    <div className="ax-shell min-h-screen flex flex-col">
      <header className="ax-header sticky top-0 z-20 border-b border-[var(--ax-line)] backdrop-blur-md">
        <div className="mx-auto flex max-w-[1600px] flex-wrap items-center gap-3 px-4 py-3">
          <Link href="/solo" className="ax-brand shrink-0">
            <span className="ax-brand-mark">Axiodrasil</span>
            <span className="ax-brand-sub">Bina</span>
          </Link>
          {subtitle ? (
            <p className="hidden text-sm text-[var(--ax-muted)] md:block">{subtitle}</p>
          ) : null}
          <div className="ml-auto flex items-center gap-2">{actions}</div>
        </div>
      </header>
      <main className="mx-auto flex w-full max-w-[1600px] flex-1 flex-col px-4 py-4">{children}</main>
    </div>
  );
}
