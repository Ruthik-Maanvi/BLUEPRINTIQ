"use client";

import { useState } from "react";
import type { ProcurementPlan } from "@/types/material";
import MaterialTable from "@/components/materialtable";

export default function ProcurementStages({ plan }: { plan: ProcurementPlan }) {
  const [expanded, setExpanded] = useState<Set<string>>(new Set());

  function toggle(stage: string) {
    setExpanded((prev) => {
      const next = new Set(prev);
      next.has(stage) ? next.delete(stage) : next.add(stage);
      return next;
    });
  }

  const totalItems = plan.stages.reduce((sum, s) => sum + s.item_count, 0);

  return (
    <div>
      <p className="mb-4 text-sm text-blueprint-400">
        {totalItems} material{totalItems === 1 ? "" : "s"} across {plan.stages.filter((s) => s.item_count > 0).length}{" "}
        active procurement stage{plan.stages.filter((s) => s.item_count > 0).length === 1 ? "" : "s"}.
      </p>
      <div className="space-y-2">
        {plan.stages.map((group) => {
          const isOpen = expanded.has(group.stage);
          const isEmpty = group.item_count === 0;
          return (
            <div
              key={group.stage}
              className={`rounded-lg border ${isEmpty ? "border-blueprint-800 opacity-50" : "border-blueprint-700"} overflow-hidden`}
            >
              <button
                onClick={() => !isEmpty && toggle(group.stage)}
                disabled={isEmpty}
                className="flex w-full items-center justify-between bg-blueprint-900/60 px-4 py-3 text-left disabled:cursor-default"
              >
                <div className="flex items-center gap-3">
                  <span className="font-mono text-xs text-signal-orange">
                    {String(group.order).padStart(2, "0")}
                  </span>
                  <span className="font-medium text-blueprint-100">{group.stage}</span>
                </div>
                <div className="flex items-center gap-3">
                  <span className="rounded-full border border-blueprint-600 px-2 py-0.5 text-xs text-blueprint-300">
                    {group.item_count} item{group.item_count === 1 ? "" : "s"}
                  </span>
                  {!isEmpty && (
                    <svg
                      width="14"
                      height="14"
                      viewBox="0 0 24 24"
                      fill="none"
                      className={`text-blueprint-400 transition-transform ${isOpen ? "rotate-180" : ""}`}
                    >
                      <path d="M6 9l6 6 6-6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
                    </svg>
                  )}
                </div>
              </button>
              {isOpen && (
                <div className="border-t border-blueprint-800 bg-blueprint-950 p-4">
                  <MaterialTable materials={group.materials} />
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}