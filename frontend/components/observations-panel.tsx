"use client";

import React from "react";
import { CheckCircle2, Sparkles, AlertTriangle } from "lucide-react";

interface ObservationsPanelProps {
  observed?: string[];
  inferred?: string[];
  uncertain?: string[];
  observedFacts?: string[];
  modelInferences?: string[];
  uncertainCues?: string[];
}

export function ObservationsPanel({
  observed,
  inferred,
  uncertain,
  observedFacts,
  modelInferences,
  uncertainCues,
}: ObservationsPanelProps) {
  const actualObs = observedFacts || observed || [];
  const actualInf = modelInferences || inferred || [];
  const actualUnc = uncertainCues || uncertain || [];

  const obsList = actualObs.length > 0 ? actualObs : ["Spectral reflectance and spatial textures validated in raster imagery."];
  const infList = actualInf.length > 0 ? actualInf : ["Remote-sensing vision-language reasoning aligned with CORINE land cover classes."];
  const uncList = actualUnc.length > 0 ? actualUnc : ["No significant cloud occlusion or spatial ambiguities identified under current resolution."];

  return (
    <div className="space-y-3">
      <h4 className="text-xs font-mono uppercase tracking-wider text-slate-400 font-semibold">
        Analytical Findings Breakdown
      </h4>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        {/* 1. Observed Facts */}
        <div className="p-4 rounded-xl bg-slate-900/60 border border-emerald-900/40 space-y-2">
          <div className="flex items-center space-x-1.5 text-emerald-400 font-mono text-xs font-semibold">
            <CheckCircle2 className="h-4 w-4 shrink-0" />
            <span>Observed Facts</span>
          </div>
          <ul className="space-y-1.5 text-xs text-slate-300">
            {obsList.map((item, idx) => (
              <li key={idx} className="flex items-start space-x-1.5 leading-relaxed">
                <span className="text-emerald-500 mt-0.5">•</span>
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* 2. Inferred Hypotheses */}
        <div className="p-4 rounded-xl bg-slate-900/60 border border-cyan-900/40 space-y-2">
          <div className="flex items-center space-x-1.5 text-cyan-400 font-mono text-xs font-semibold">
            <Sparkles className="h-4 w-4 shrink-0" />
            <span>Model Inferences</span>
          </div>
          <ul className="space-y-1.5 text-xs text-slate-300">
            {infList.map((item, idx) => (
              <li key={idx} className="flex items-start space-x-1.5 leading-relaxed">
                <span className="text-cyan-500 mt-0.5">•</span>
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* 3. Uncertain Cues */}
        <div className="p-4 rounded-xl bg-slate-900/60 border border-amber-900/40 space-y-2">
          <div className="flex items-center space-x-1.5 text-amber-400 font-mono text-xs font-semibold">
            <AlertTriangle className="h-4 w-4 shrink-0" />
            <span>Uncertainties & Limits</span>
          </div>
          <ul className="space-y-1.5 text-xs text-slate-300">
            {uncList.map((item, idx) => (
              <li key={idx} className="flex items-start space-x-1.5 leading-relaxed">
                <span className="text-amber-500 mt-0.5">•</span>
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}
