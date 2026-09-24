"use client";

import React from "react";
import { Zap, ShieldCheck, AlertCircle, Info } from "lucide-react";

interface ConfidenceCardProps {
  score?: number | null;
  method?: string | null;
  level?: string | null;
  calibrationQuality?: string;
}

export function ConfidenceCard({
  score,
  method = "Multimodal Calibrated Probability",
  level,
  calibrationQuality = "HIGH_CERTAINTY",
}: ConfidenceCardProps) {
  if (score === undefined || score === null) {
    return (
      <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-2 text-xs">
        <div className="flex items-center justify-between text-slate-400 font-mono">
          <span>Confidence Estimation</span>
          <span className="text-amber-400 flex items-center space-x-1">
            <AlertCircle className="h-3.5 w-3.5" />
            <span>Uncalibrated</span>
          </span>
        </div>
        <p className="text-slate-500 text-[11px]">
          The selected specialist model did not emit a calibrated probabilistic confidence bound.
        </p>
      </div>
    );
  }

  const pct = Math.round(score * 100);
  const isHigh = pct >= 75;
  const isModerate = pct >= 50 && pct < 75;

  const barColor = isHigh ? "bg-emerald-400" : isModerate ? "bg-cyan-400" : "bg-amber-400";
  const textColor = isHigh ? "text-emerald-400" : isModerate ? "text-cyan-400" : "text-amber-400";

  return (
    <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 shadow-sm space-y-3 text-xs">
      <div className="flex items-center justify-between">
        <span className="text-slate-400 font-mono uppercase tracking-wider text-[10px]">
          Confidence Rating
        </span>
        <span className={`font-mono font-semibold ${textColor}`}>
          {isHigh ? "High Certainty" : isModerate ? "Moderate Certainty" : "Low Certainty"}
        </span>
      </div>

      <div className="flex items-baseline space-x-2">
        <span className="text-3xl font-bold font-mono text-white">{pct}%</span>
        <span className="text-slate-400 text-[11px] font-mono">probabilistic score</span>
      </div>

      {/* Progress Bar */}
      <div className="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden">
        <div
          className={`h-full ${barColor} transition-all duration-500 rounded-full`}
          style={{ width: `${pct}%` }}
        />
      </div>

      <div className="pt-1 flex items-center justify-between text-[11px] text-slate-500 font-mono">
        <span className="truncate max-w-[200px]" title={method || ""}>
          Method: {method || "Multimodal Calibration"}
        </span>
        <span className="text-cyan-400/90 flex items-center space-x-1">
          <ShieldCheck className="h-3.5 w-3.5" />
          <span>Calibrated</span>
        </span>
      </div>
    </div>
  );
}
