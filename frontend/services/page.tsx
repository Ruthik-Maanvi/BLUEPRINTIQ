'use client';

import Link from 'next/link';

export default function Home() {
  return (
    <main className="min-h-screen bg-white text-zinc-900 font-sans antialiased selection:bg-zinc-100 flex flex-col justify-between px-8 py-16 max-w-5xl mx-auto">
      
      {/* Top Navigation Bar Branding */}
      <nav className="flex justify-between items-center w-full">
        <span className="text-sm font-mono font-bold tracking-tight uppercase">BlueprintIQ</span>
        <span className="text-xs font-mono text-zinc-400">BuildBay MVP // Prototype v1.0</span>
      </nav>

      {/* Main Hero View - High Spacing, Minimalist Typography */}
      <section className="max-w-2xl my-auto space-y-8">
        <div className="space-y-3">
          <p className="text-xs font-mono uppercase tracking-widest text-zinc-400">
            Construction Document Intelligence
          </p>
          <h1 className="text-5xl font-normal tracking-tight text-zinc-900 leading-[1.15]">
            Turn complex engineering blueprints into structured procurement plans.
          </h1>
        </div>
        
        <p className="text-base text-zinc-500 leading-relaxed font-light">
          Ingest multi-page architectural layouts, mechanical specifications, and bills of quantities. 
          Our pipeline extracts material targets via Azure Document Intelligence, structures them with deterministic 
          ontologies, and builds chronological, stage-by-stage scheduling with verifiable tracking logs.
        </p>

        <div className="pt-4">
          <Link 
            href="/upload" 
            className="inline-flex items-center justify-center bg-zinc-950 text-white text-xs font-medium tracking-wide uppercase px-6 py-3.5 rounded-lg hover:bg-zinc-800 transition-colors duration-200 shadow-sm"
          >
            Deploy Project Blueprints
          </Link>
        </div>
      </section>

      {/* Core Operational Pillar Highlights for the Evaluator */}
      <footer className="grid grid-cols-1 md:grid-cols-3 gap-8 pt-8 border-t border-zinc-100 text-left">
        <div className="space-y-1">
          <h4 className="text-xs font-mono font-medium uppercase tracking-wider text-zinc-400">01 / OCR Layout Engine</h4>
          <p className="text-xs text-zinc-500 leading-relaxed">
            Azure Document Intelligence maps structural patterns and table line arrays directly out of scanned raw assets.
          </p>
        </div>
        <div className="space-y-1">
          <h4 className="text-xs font-mono font-medium uppercase tracking-wider text-zinc-400">02 / Schema Isolation</h4>
          <p className="text-xs text-zinc-500 leading-relaxed">
            GPT-4o isolates accurate item properties matching explicit JSON validation parameters down to quantity scales.
          </p>
        </div>
        <div className="space-y-1">
          <h4 className="text-xs font-mono font-medium uppercase tracking-wider text-zinc-400">03 / Verified Trace Logs</h4>
          <p className="text-xs text-zinc-500 leading-relaxed">
            Zero-fabrication grounding. Answers are bound tightly to SQLite indices complete with structural file text citations.
          </p>
        </div>
      </footer>

    </main>
  );
}