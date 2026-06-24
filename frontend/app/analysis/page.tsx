"use client";

import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { api, ApiError } from "@/services/api";
import type { AnalyzeResponse } from "@/types/material";

function AnalysisContent() {
  const params = useSearchParams();
  const router = useRouter();
  const projectId = Number(params.get("projectId"));

  const [result, setResult] = useState<AnalyzeResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [running, setRunning] = useState(true);

  useEffect(() => {
    if (!projectId) return;
    let active = true;
    api
      .analyzeProject(projectId)
      .then((res) => {
        if (active) {
          setResult(res);
          setRunning(false);
        }
      })
      .catch((err) => {
        if (active) {
          setError(err instanceof ApiError ? err.message : "Analysis failed. Is the backend running on :8000?");
          setRunning(false);
        }
      });
    return () => {
      active = false;
    };
  }, [projectId]);

  if (!projectId) {
    return <p className="text-blueprint-300">No project specified. Go back to Upload.</p>;
  }

  return (
    <div className="mx-auto max-w-2xl">
      <h1 className="mb-1 text-2xl font-semibold text-blueprint-100">
        {running ? "Running OCR + extraction…" : "Analysis complete"}
      </h1>
      <p className="mb-6 text-sm text-blueprint-400">
        Project #{projectId} · OCR → ontology mapping → procurement staging → reasoning generation
      </p>

      {running && (
        <div className="flex items-center gap-3 rounded-lg border border-blueprint-700 bg-blueprint-900/40 px-5 py-6">
          <span className="h-3 w-3 animate-pulse rounded-full bg-signal-orange" />
          <p className="text-sm text-blueprint-300">
            Extracting text/tables, matching the construction ontology, and generating traceable reasoning for each
            document. This runs synchronously and typically finishes in a few seconds per document.
          </p>
        </div>
      )}

      {error && (
        <div className="rounded-lg border border-signal-red/40 bg-signal-red/10 px-5 py-4 text-sm text-signal-red">
          {error}
        </div>
      )}

      {result && (
        <div className="space-y-3">
          {result.documents.map((d) => (
            <div
              key={d.document}
              className={`rounded-lg border px-4 py-3 ${
                d.status === "completed" ? "border-blueprint-700 bg-blueprint-900/40" : "border-signal-red/40 bg-signal-red/10"
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="font-medium text-blueprint-100">{d.document}</span>
                <span className={`text-xs font-mono ${d.status === "completed" ? "text-signal-green" : "text-signal-red"}`}>
                  {d.status}
                </span>
              </div>
              {d.status === "completed" ? (
                <p className="mt-1 text-xs text-blueprint-400">
                  {d.pages} page{d.pages === 1 ? "" : "s"} processed · {d.materials_found} material
                  {d.materials_found === 1 ? "" : "s"} found
                </p>
              ) : (
                <p className="mt-1 text-xs text-signal-red">{d.reason}</p>
              )}
            </div>
          ))}

          <button
            onClick={() => router.push(`/results?projectId=${projectId}`)}
            className="mt-4 w-full rounded-md bg-signal-orange py-3 font-medium text-blueprint-950 hover:bg-orange-400 transition-colors"
          >
            View materials, procurement plan & reasoning →
          </button>
        </div>
      )}
    </div>
  );
}

export default function AnalysisPage() {
  return (
    <Suspense fallback={<p className="text-blueprint-300">Loading…</p>}>
      <AnalysisContent />
    </Suspense>
  );
}