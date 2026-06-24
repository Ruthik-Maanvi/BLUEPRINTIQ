"use client";

import Link from "next/link";
import SearchBar from "@/components/searchbar";

export default function Navbar() {
  return (
    <header className="sticky top-0 z-40 border-b border-blueprint-700 bg-blueprint-950/90 backdrop-blur">
      <div className="mx-auto flex max-w-7xl items-center gap-6 px-6 py-3">
        <Link href="/" className="flex items-center gap-2 shrink-0">
          <span className="grid h-8 w-8 place-items-center rounded border border-signal-orange/60 text-signal-orange font-mono text-xs">
            iQ
          </span>
          <span className="font-semibold tracking-tight text-blueprint-100">
            Blueprint<span className="text-signal-orange">IQ</span>
          </span>
        </Link>

        <div className="flex-1">
          <SearchBar />
        </div>

        <nav className="flex items-center gap-4 text-sm shrink-0">
          <Link href="/" className="text-blueprint-200 hover:text-white transition-colors">
            Projects
          </Link>
          <Link
            href="/upload"
            className="rounded-md bg-signal-orange px-3 py-1.5 font-medium text-blueprint-950 hover:bg-orange-400 transition-colors"
          >
            + Upload
          </Link>
        </nav>
      </div>
    </header>
  );
}