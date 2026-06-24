"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/services/api";
import type { SearchResultItem } from "@/types/material";

const TYPE_LABEL: Record<string, string> = {
  ocr_page: "Document text",
  material: "Material",
  reasoning: "Reasoning",
};

export default function SearchBar({ projectId }: { projectId?: number }) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResultItem[]>([]);
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const router = useRouter();

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  useEffect(() => {
    if (query.trim().length < 2) {
      setResults([]);
      return;
    }
    const handle = setTimeout(async () => {
      setLoading(true);
      try {
        const res = await api.search(query.trim(), projectId);
        setResults(res.results);
        setOpen(true);
      } catch {
        setResults([]);
      } finally {
        setLoading(false);
      }
    }, 280);
    return () => clearTimeout(handle);
  }, [query, projectId]);

  function goToResult(item: SearchResultItem) {
    if (item.project_id) {
      router.push(`/results?projectId=${item.project_id}&tab=search&q=${encodeURIComponent(query)}`);
    }
    setOpen(false);
  }

  return (
    <div ref={containerRef} className="relative w-full max-w-md">
      <div className="flex items-center gap-2 rounded-md border border-blueprint-600 bg-blueprint-900/60 px-3 py-2">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" className="text-blueprint-400 shrink-0">
          <circle cx="11" cy="11" r="7" stroke="currentColor" strokeWidth="2" />
          <path d="M21 21l-4.3-4.3" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
        </svg>
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => results.length > 0 && setOpen(true)}
          placeholder="Search documents, materials, reasoning…"
          className="w-full bg-transparent text-sm text-blueprint-100 placeholder:text-blueprint-400 outline-none"
        />
        {loading && <span className="text-xs text-blueprint-400">…</span>}
      </div>

      {open && results.length > 0 && (
        <div className="absolute z-50 mt-2 w-full rounded-md border border-blueprint-700 bg-blueprint-900 shadow-xl max-h-96 overflow-y-auto scrollbar-thin">
          {results.map((item, idx) => (
            <button
              key={`${item.content_type}-${item.content_id}-${idx}`}
              onClick={() => goToResult(item)}
              className="block w-full text-left px-4 py-3 border-b border-blueprint-800 last:border-0 hover:bg-blueprint-800 transition-colors"
            >
              <div className="flex items-center justify-between gap-2 mb-1">
                <span className="text-[10px] uppercase tracking-wide text-signal-orange font-medium">
                  {TYPE_LABEL[item.content_type] ?? item.content_type}
                </span>
                {item.document_name && (
                  <span className="text-[11px] text-blueprint-400 truncate">
                    {item.document_name}
                    {item.page_number ? ` · p.${item.page_number}` : ""}
                  </span>
                )}
              </div>
              <p className="text-sm font-mono text-blueprint-100 line-clamp-2">{item.snippet}</p>
            </button>
          ))}
        </div>
      )}

      {open && results.length === 0 && query.trim().length >= 2 && !loading && (
        <div className="absolute z-50 mt-2 w-full rounded-md border border-blueprint-700 bg-blueprint-900 px-4 py-3 text-sm text-blueprint-400 shadow-xl">
          No matches found in the uploaded project knowledge base.
        </div>
      )}
    </div>
  );
}