"use client";

import React, { useState } from "react";
import { Sparkles, Copy, Check, Share2 } from "lucide-react";

interface AnalysisAnswerProps {
  answer: string;
  query?: string;
  question?: string;
  confidencePercentage?: string;
  confidenceScore?: number | null;
  confidenceLevel?: string | null;
  calibrationStatus?: string;
  taskType?: string;
}

export function AnalysisAnswer({
  answer,
  query,
  question,
  confidencePercentage,
  confidenceScore,
  confidenceLevel,
  calibrationStatus = "Empirically Calibrated",
  taskType,
}: AnalysisAnswerProps) {
  const displayQuery = query || question;
  const displayConfidence =
    confidencePercentage || (confidenceScore !== undefined && confidenceScore !== null ? `${Math.round(confidenceScore * 100)}%` : undefined);
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(answer);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="p-6 rounded-2xl bg-gradient-to-br from-slate-900/90 via-slate-900/60 to-cyan-950/30 border border-cyan-800/40 shadow-xl relative overflow-hidden backdrop-blur-sm">
      <div className="absolute top-0 right-0 w-80 h-full bg-gradient-to-l from-cyan-500/10 to-transparent pointer-events-none" />

      {/* Top Banner */}
      <div className="flex items-center justify-between pb-3 mb-3 border-b border-slate-800/60 text-xs">
        <div className="flex items-center space-x-2 text-cyan-400 font-mono font-medium">
          <Sparkles className="h-4 w-4" />
          <span>Synthesized Remote-Sensing Answer</span>
        </div>

        <div className="flex items-center space-x-2">
          {displayConfidence && (
            <span className="px-2.5 py-0.5 rounded-full bg-cyan-950/80 text-cyan-300 border border-cyan-800/60 text-[11px] font-mono font-semibold">
              {displayConfidence} ({calibrationStatus})
            </span>
          )}

          <button
            onClick={handleCopy}
            className="p-1.5 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-slate-300 hover:text-white transition flex items-center space-x-1 text-[11px]"
            title="Copy answer"
          >
            {copied ? <Check className="h-3.5 w-3.5 text-emerald-400" /> : <Copy className="h-3.5 w-3.5" />}
            <span className="hidden sm:inline">{copied ? "Copied" : "Copy"}</span>
          </button>
        </div>
      </div>

      {displayQuery && (
        <p className="text-xs text-slate-400 italic mb-2">
          &ldquo;{displayQuery}&rdquo;
        </p>
      )}

      {/* Main Answer Text */}
      <p className="text-base sm:text-lg text-white font-medium leading-relaxed">
        {answer}
      </p>
    </div>
  );
}
