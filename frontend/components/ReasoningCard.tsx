"use client";

import type { MaterialWithReasoning } from "@/types/material";

function confidenceClass(score: number): string {
  if (score >= 0.8) return "confidence-high";
  if (score >= 0.6) return "confidence-medium";
  return "confidence-low";
}

export default function ReasoningCard({ item }: { item: MaterialWithReasoning }) {
  const r = item.reasoning;
  return (
    <div className="rounded-lg border border-blueprint-700 bg-blueprint-900/40 p-5">
      <div className="mb-3 flex items-center justify-between">
        <div>
          <h3 className="font-semibold text-blueprint-100">{item.material_name}</h3>
          <p className="text-xs text-blueprint-400">
            {item.category} · {item.procurement_stage}
          </p>
        </div>
        <span className={`rounded-full border px-2.5 py-1 text-xs font-mono ${confidenceClass(item.confidence)}`}>
          {(item.confidence * 100).toFixed(0)}% confidence
        </span>
      </div>

      {r ? (
        <dl className="space-y-2.5 text-sm">
          <div>
            <dt className="text-[11px] uppercase tracking-wide text-signal-orange">What was detected</dt>
            <dd className="text-blueprint-200">{r.what_detected}</dd>
          </div>
          <div>
            <dt className="text-[11px] uppercase tracking-wide text-signal-orange">Where it was detected</dt>
            <dd className="text-blueprint-200 font-mono text-xs leading-relaxed">{r.where_detected}</dd>
          </div>
          <div>
            <dt className="text-[11px] uppercase tracking-wide text-signal-orange">Why this category</dt>
            <dd className="text-blueprint-200">{r.why_category}</dd>
          </div>
          <div>
            <dt className="text-[11px] uppercase tracking-wide text-signal-orange">Why this stage</dt>
            <dd className="text-blueprint-200">{r.why_stage}</dd>
          </div>
          <div>
            <dt className="text-[11px] uppercase tracking-wide text-signal-orange">Confidence breakdown</dt>
            <dd className="text-blueprint-300 text-xs">{r.confidence_explanation}</dd>
          </div>
        </dl>
      ) : (
        <p className="text-sm text-blueprint-400">Evidence unavailable.</p>
      )}

      <p className="mt-3 border-t border-blueprint-800 pt-2 text-[11px] text-blueprint-500">
        {item.source_document}
        {item.source_page ? ` · page ${item.source_page}` : ""} · {item.extraction_method}
      </p>
    </div>
  );
}