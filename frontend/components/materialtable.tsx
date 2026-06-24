"use client";

import { useMemo, useState } from "react";
import type { Material } from "@/types/material";

function confidenceClass(score: number): string {
  if (score >= 0.8) return "confidence-high";
  if (score >= 0.6) return "confidence-medium";
  return "confidence-low";
}

export default function MaterialTable({ materials }: { materials: Material[] }) {
  const [stageFilter, setStageFilter] = useState<string>("all");
  const [methodFilter, setMethodFilter] = useState<string>("all");

  const stages = useMemo(
    () => Array.from(new Set(materials.map((m) => m.procurement_stage))).sort(),
    [materials]
  );

  const methods = useMemo(
    () =>
      Array.from(
        new Set(
          materials.map((m) =>
            m.extraction_method.startsWith("ontology_deterministic") ? "Ontology (deterministic)" : "GPT-4o (LLM)"
          )
        )
      ),
    [materials]
  );

  const filtered = materials.filter((m) => {
    const methodLabel = m.extraction_method.startsWith("ontology_deterministic")
      ? "Ontology (deterministic)"
      : "GPT-4o (LLM)";
    return (
      (stageFilter === "all" || m.procurement_stage === stageFilter) &&
      (methodFilter === "all" || methodLabel === methodFilter)
    );
  });

  if (materials.length === 0) {
    return (
      <div className="rounded-lg border border-blueprint-700 bg-blueprint-900/40 px-6 py-10 text-center text-blueprint-300">
        No materials extracted yet. Run analysis on this project to populate this table.
      </div>
    );
  }

  return (
    <div>
      <div className="mb-3 flex flex-wrap items-center gap-3 text-sm">
        <select
          value={stageFilter}
          onChange={(e) => setStageFilter(e.target.value)}
          className="rounded-md border border-blueprint-600 bg-blueprint-900 px-2 py-1 text-blueprint-100"
        >
          <option value="all">All stages</option>
          {stages.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
        <select
          value={methodFilter}
          onChange={(e) => setMethodFilter(e.target.value)}
          className="rounded-md border border-blueprint-600 bg-blueprint-900 px-2 py-1 text-blueprint-100"
        >
          <option value="all">All extraction methods</option>
          {methods.map((m) => (
            <option key={m} value={m}>
              {m}
            </option>
          ))}
        </select>
        <span className="text-blueprint-400">
          {filtered.length} of {materials.length} materials
        </span>
      </div>

      <div className="overflow-x-auto rounded-lg border border-blueprint-700">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-blueprint-900 text-left text-blueprint-300">
              <th className="px-4 py-2 font-medium">Material</th>
              <th className="px-4 py-2 font-medium">Category</th>
              <th className="px-4 py-2 font-medium">Stage</th>
              <th className="px-4 py-2 font-medium">Qty / Unit</th>
              <th className="px-4 py-2 font-medium">Confidence</th>
              <th className="px-4 py-2 font-medium">Source</th>
              <th className="px-4 py-2 font-medium">Evidence</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((m) => (
              <tr key={m.id} className="border-t border-blueprint-800 hover:bg-blueprint-900/50">
                <td className="px-4 py-2 font-medium text-blueprint-100">{m.material_name}</td>
                <td className="px-4 py-2 text-blueprint-300">{m.category}</td>
                <td className="px-4 py-2">
                  <span className="rounded-full border border-blueprint-600 px-2 py-0.5 text-xs text-blueprint-200">
                    {m.procurement_stage}
                  </span>
                  {m.secondary_stage && (
                    <span className="ml-1 text-xs text-blueprint-500">+ {m.secondary_stage}</span>
                  )}
                </td>
                <td className="px-4 py-2 text-blueprint-300">
                  {m.quantity !== null ? m.quantity : "—"} {m.unit ?? ""}
                </td>
                <td className="px-4 py-2">
                  <span className={`rounded-full border px-2 py-0.5 text-xs font-mono ${confidenceClass(m.confidence)}`}>
                    {(m.confidence * 100).toFixed(0)}%
                  </span>
                </td>
                <td className="px-4 py-2 text-blueprint-400 text-xs">
                  {m.source_document}
                  {m.source_page ? ` · p.${m.source_page}` : ""}
                </td>
                <td className="px-4 py-2 max-w-xs">
                  <p className="line-clamp-2 font-mono text-xs text-blueprint-300" title={m.evidence}>
                    {m.evidence}
                  </p>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}