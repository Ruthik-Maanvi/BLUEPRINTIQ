'use client';

import { useEffect, useState } from "react";
import Link from 'next/link';
import { api } from "@/services/api";
import type { ProjectSummary, HealthResponse } from "@/types/material";

export default function Home() {
  const [projects, setProjects] = useState<ProjectSummary[]>([]);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.listProjects().catch(() => []),
      api.health().catch(() => null)
    ]).then(([projectsData, healthData]) => {
      setProjects(projectsData);
      setHealth(healthData);
      setLoading(false);
    });
  }, []);

  return (
    <div className="flex flex-col justify-between min-h-[85vh] max-w-5xl mx-auto space-y-16">
      
      {/* Premium Minimal Navigation */}
      <nav className="flex justify-between items-center w-full border-b border-blueprint-900 pb-6">
        <span className="text-sm font-mono font-bold tracking-wider text-blueprint-100">BLUEPRINTIQ</span>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-1.5 text-xs font-mono">
            <span className={`w-2 height-2 rounded-full ${health ? 'bg-signal-green' : 'bg-signal-red'}`} />
            <span className="text-blueprint-400">Engine Status</span>
          </div>
          <span className="text-xs font-mono text-blueprint-400 border-l border-blueprint-800 pl-4">v1.0 MVP</span>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="max-w-3xl space-y-8 my-auto">
        <div className="space-y-4">
          <p className="text-xs font-mono uppercase tracking-widest text-signal-orange font-semibold">
            Deterministic Construction Extraction
          </p>
          <h1 className="text-4xl md:text-5xl font-light tracking-tight text-blueprint-100 leading-[1.2]">
            Turn complex engineering blueprints into structured procurement plans.
          </h1>
        </div>
        
        <p className="text-base text-blueprint-400 leading-relaxed font-light max-w-2xl">
          Ingest layout specifications and bills of quantities. Our pipeline uses structural pattern matching to isolate materials, mapping items to an expert-level construction ontology with verifiable tracking logs.
        </p>

        <div className="pt-4 flex items-center gap-4">
          <Link 
            href="/upload" 
            className="inline-flex items-center justify-center bg-signal-orange text-blueprint-950 text-xs font-mono font-bold tracking-wide uppercase px-6 py-4 rounded-md hover:bg-opacity-90 transition-all shadow-sm"
          >
            Deploy Project Blueprints →
          </Link>
        </div>
      </section>

      {/* Dynamic Projects Grid Dashboard */}
      <section className="space-y-6">
        <div className="flex items-center justify-between border-b border-blueprint-900 pb-3">
          <h2 className="text-sm font-mono uppercase tracking-wider text-blueprint-400">Active Workspace Projects</h2>
          <span className="text-xs font-mono text-blueprint-600">{projects.length} Found</span>
        </div>

        {loading ? (
          <p className="text-xs font-mono text-blueprint-400 animate-pulse">Querying internal schema arrays...</p>
        ) : projects.length === 0 ? (
          <div className="rounded-lg border border-dashed border-blueprint-800 px-6 py-12 text-center text-sm text-blueprint-400">
            No active project models located. Begin by launching a blueprint file array.
          </div>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {projects.map((p) => (
              <Link
                key={p.id}
                href={`/results?projectId=${p.id}`}
                className="group block rounded-lg border border-blueprint-800 bg-blueprint-900/20 p-5 hover:border-signal-orange/60 hover:bg-blueprint-900/40 transition-all duration-200"
              >
                <div className="mb-4 flex items-start justify-between gap-2">
                  <span className="font-medium text-blueprint-100 truncate group-hover:text-signal-orange transition-colors">
                    {p.name}
                  </span>
                  <span className={`rounded-full border px-2 py-0.5 text-[10px] font-mono tracking-tight shrink-0 ${
                    p.status === "analyzed" ? "confidence-high" : "confidence-medium"
                  }`}>
                    {p.status}
                  </span>
                </div>
                <div className="flex justify-between items-center text-[11px] font-mono text-blueprint-500">
                  <span>ID: #{p.id}</span>
                  <span>{new Date(p.created_at).toLocaleDateString()}</span>
                </div>
              </Link>
            ))}
          </div>
        )}
      </section>

    </div>
  );
}