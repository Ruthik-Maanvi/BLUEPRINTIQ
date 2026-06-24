"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { api, ApiError } from "@/services/api";
import type {
  AskResponse,
  Material,
  MaterialWithReasoning,
  ProcurementPlan, 
  ProjectOut, 
} from "@/types/material";
import MaterialTable from "@/components/materialtable";
import ProcurementStages from "@/components/ProcurementStages";
import ReasoningCard from "@/components/ReasoningCard";

type Tab = "materials" | "procurement" | "reasoning" | "search";

function AskPanel({ projectId }: { projectId: number }) {
  const [question, setQuestion] = useState("");
  const [response, setResponse] = useState<AskResponse | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleAsk() {
    if (!question.trim()) return;
    setLoading(true);
    try {
      const res = await api.ask(projectId, question.trim());
      setResponse(res);
    } catch {
      setResponse({
        question,
        answer: "Could not reach the backend. Is it running on :8000?",
        grounded: false,
        citations: [],
      });
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="rounded-lg border border-blueprint-700 bg-blueprint-900/40 p-5">
      <h3 className="mb-2 font-semibold text-blueprint-100">Ask a question about this project</h3>
      <p className="mb-3 text-xs text-blueprint-400">
        Answers are grounded only in this project's uploaded documents and analysis — never general knowledge.
      </p>
      <div className="flex gap-2">
        <input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleAsk()}
          placeholder="e.g. How much rebar was specified and where?"
          className="flex-1 rounded-md border border-blueprint-600 bg-blueprint-900 px-3 py-2 text-sm text-blueprint-100 placeholder:text-blueprint-500 outline-none focus:border-signal-orange"
        />
        <button
          onClick={handleAsk}
          disabled={loading}
          className="rounded-md bg-signal-orange px-4 py-2 text-sm font-medium text-blueprint-950 hover:bg-orange-400 disabled:opacity-50"
        >
          {loading ? "Asking…" : "Ask"}
        </button>
      </div>

      {response && (
        <div className="mt-4 rounded-md border border-blueprint-800 bg-blueprint-950 p-4">
          <div className="mb-2 flex items-center gap-2">
            <span
              className={`rounded-full px-2 py-0.5 text-[11px] font-mono ${
                response.grounded ? "confidence-high" : "confidence-low"
              }`}
            >
              {response.grounded ? "Grounded" : "Not grounded"}
            </span>
          </div>
          <p className="text-sm text-blueprint-100">{response.answer}</p>
          {response.note && <p className="mt-2 text-xs text-blueprint-500">{response.note}</p>}
          {response.citations.length > 0 && (
            <div className="mt-3 space-y-2 border-t border-blueprint-800 pt-3">
              <p className="text-[11px] uppercase tracking-wide text-signal-orange">Evidence cited</p>
              {response.citations.map((c, i) => (
                <div key={i} className="text-xs text-blueprint-300">
                  <span className="text-blueprint-500">
                    [{c.document_name ?? "n/a"}{c.page_number ? ` p.${c.page_number}` : ""}]{" "}
                  </span>
                  <span className="font-mono">{c.snippet}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function ResultsContent() {
  const params = useSearchParams();
  const projectId = Number(params.get("projectId"));
  const initialTab = (params.get("tab") as Tab) || "materials";

  const [tab, setTab] = useState<Tab>(initialTab);
  const [project, setProject] = useState<ProjectOut | null>(null);
  const [materials, setMaterials] = useState<Material[]>([]);
  const [plan, setPlan] = useState<ProcurementPlan | null>(null);
  const [reasoning, setReasoning] = useState<MaterialWithReasoning[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!projectId) return;
    let active = true;
    Promise.all([
      api.getProject(projectId),
      api.getMaterials(projectId),
      api.getProcurement(projectId),
      api.getReasoning(projectId),
    ])
      .then(([p, m, plan, r]) => {
        if (!active) return;
        setProject(p);
        setMaterials(m);
        setPlan(plan);
        setReasoning(r);
      })
      .catch((err) => {
        if (active) setError(err instanceof ApiError ? err.message : "Failed to load project results.");
      })
      .finally(() => active && setLoading(false));
    return () => {
      active = false;
    };
  }, [projectId]);

  if (!projectId) return <p className="text-blueprint-300">No project specified.</p>;
  if (loading) return <p className="text-blueprint-300">Loading project results…</p>;
  if (error) return <p className="text-signal-red">{error}</p>;

  const tabs: { id: Tab; label: string; count?: number }[] = [
    { id: "materials", label: "Materials", count: materials.length },
    { id: "procurement", label: "Procurement Plan", count: plan?.stages.filter((s) => s.item_count > 0).length },
    { id: "reasoning", label: "Reasoning", count: reasoning.length },
    { id: "search", label: "Ask" },
  ];

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-semibold text-blueprint-100">{project?.name}</h1>
        <p className="text-sm text-blueprint-400">
          {project?.documents.length} document{project?.documents.length === 1 ? "" : "s"} · status: {project?.status}
        </p>
      </div>

      <div className="mb-6 flex gap-1 border-b border-blueprint-800">
        {tabs.map((t) => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`px-4 py-2 text-sm font-medium transition-colors ${
              tab === t.id
                ? "border-b-2 border-signal-orange text-blueprint-100"
                : "text-blueprint-400 hover:text-blueprint-200"
            }`}
          >
            {t.label}
            {t.count !== undefined ? ` (${t.count})` : ""}
          </button>
        ))}
      </div>

      {tab === "materials" && <MaterialTable materials={materials} />}
      {tab === "procurement" && plan && <ProcurementStages plan={plan} />}
      {tab === "reasoning" && (
        <div className="grid gap-4 md:grid-cols-2">
          {reasoning.map((item) => (
            <ReasoningCard key={item.id} item={item} />
          ))}
        </div>
      )}
      {tab === "search" && <AskPanel projectId={projectId} />}
    </div>
  );
}

export default function ResultsPage() {
  return (
    <Suspense fallback={<p className="text-blueprint-300">Loading…</p>}>
      <ResultsContent />
    </Suspense>
  );
}