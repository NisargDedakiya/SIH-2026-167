"use client";

import React from "react";
import { CheckCircle2, Loader2, Circle, AlertCircle } from "lucide-react";

export type ProgressStage = "idle" | "validating" | "interpreting" | "routing" | "running" | "generating" | "completed" | "error";

export interface AnalysisMilestone {
  id?: string;
  sequence?: number;
  title: string;
  milestone?: string;
  status: "pending" | "running" | "completed" | "failed" | string;
  description?: string;
  duration_ms?: number;
}

interface AnalysisProgressProps {
  stage?: ProgressStage;
  task?: string;
  toolName?: string;
  milestones?: AnalysisMilestone[];
  currentStep?: string;
}

const STAGES = [
  { key: "validating", label: "Input Rasters Validated" },
  { key: "interpreting", label: "Natural Language Query Interpreted" },
  { key: "routing", label: "Specialist Tool Dispatched" },
  { key: "running", label: "Remote-Sensing Inference Executing" },
  { key: "generating", label: "Visual Evidence & Bounding Boxes Generated" },
  { key: "completed", label: "Analytical Answer Synthesized" },
];

export function AnalysisProgress({ stage = "running", task, toolName, milestones, currentStep }: AnalysisProgressProps) {
  if (stage === "idle" && (!milestones || milestones.length === 0)) return null;

  // Custom milestones mode
  if (milestones && milestones.length > 0) {
    const isAllDone = milestones.every((m) => m.status === "completed");
    const hasFailed = milestones.some((m) => m.status === "failed");

    return (
      <div className="p-5 rounded-2xl bg-slate-900/90 border border-slate-800 shadow-xl space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            {isAllDone ? (
              <CheckCircle2 className="h-4 w-4 text-emerald-400" />
            ) : hasFailed ? (
              <AlertCircle className="h-4 w-4 text-rose-400" />
            ) : (
              <Loader2 className="h-4 w-4 text-cyan-400 animate-spin" />
            )}
            <span className="font-semibold text-xs font-mono uppercase tracking-wider text-white">
              {isAllDone ? "Analysis Completed" : hasFailed ? "Analysis Halted" : currentStep || "Reasoning Execution In Progress"}
            </span>
          </div>
          {task && (
            <span className="px-2 py-0.5 rounded bg-cyan-950 text-[10px] font-mono text-cyan-300 border border-cyan-800/60">
              {task}
            </span>
          )}
        </div>

        <div className="space-y-2.5 text-xs">
          {milestones.map((m, idx) => {
            const isCompleted = m.status === "completed";
            const isRunning = m.status === "running";
            const isFailed = m.status === "failed";

            return (
              <div
                key={m.id || idx}
                className={`flex items-start space-x-2.5 transition ${
                  isCompleted ? "text-slate-300" : isRunning ? "text-cyan-300 font-medium" : isFailed ? "text-rose-400" : "text-slate-600"
                }`}
              >
                {isCompleted ? (
                  <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0 mt-0.5" />
                ) : isRunning ? (
                  <Loader2 className="h-4 w-4 text-cyan-400 animate-spin shrink-0 mt-0.5" />
                ) : isFailed ? (
                  <AlertCircle className="h-4 w-4 text-rose-400 shrink-0 mt-0.5" />
                ) : (
                  <Circle className="h-4 w-4 text-slate-700 shrink-0 mt-0.5" />
                )}
                <div>
                  <div className="font-medium">{m.title || m.milestone}</div>
                  {m.description && <p className="text-[11px] text-slate-500 font-normal">{m.description}</p>}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    );
  }

  const getStageIndex = (s: ProgressStage) => {
    switch (s) {
      case "validating": return 0;
      case "interpreting": return 1;
      case "routing": return 2;
      case "running": return 3;
      case "generating": return 4;
      case "completed": return 5;
      default: return 0;
    }
  };

  const currentIndex = getStageIndex(stage);

  return (
    <div className="p-5 rounded-xl bg-slate-900/90 border border-slate-800 shadow-xl space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          {stage === "completed" ? (
            <CheckCircle2 className="h-4 w-4 text-emerald-400" />
          ) : (
            <Loader2 className="h-4 w-4 text-cyan-400 animate-spin" />
          )}
          <span className="font-semibold text-xs font-mono uppercase tracking-wider text-white">
            {stage === "completed" ? "Analysis Complete" : "Analysis In Progress"}
          </span>
        </div>
        {task && (
          <span className="px-2 py-0.5 rounded bg-cyan-950 text-[10px] font-mono text-cyan-300 border border-cyan-800/60">
            {task} {toolName ? `→ ${toolName}` : ""}
          </span>
        )}
      </div>

      {/* Step milestones */}
      <div className="space-y-2 text-xs">
        {STAGES.map((s, idx) => {
          const isDone = stage === "completed" || idx < currentIndex;
          const isCurrent = stage !== "completed" && idx === currentIndex;

          return (
            <div
              key={s.key}
              className={`flex items-center space-x-2.5 transition ${
                isDone ? "text-slate-300" : isCurrent ? "text-cyan-300 font-medium" : "text-slate-600"
              }`}
            >
              {isDone ? (
                <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400 shrink-0" />
              ) : isCurrent ? (
                <Loader2 className="h-3.5 w-3.5 text-cyan-400 animate-spin shrink-0" />
              ) : (
                <Circle className="h-3.5 w-3.5 text-slate-700 shrink-0" />
              )}
              <span>{s.label}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
