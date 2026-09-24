"use client";

import React from "react";
import { Loader2 } from "lucide-react";

interface ProcessingIndicatorProps {
  label?: string;
  sublabel?: string;
}

export function ProcessingIndicator({
  label = "Processing remote-sensing raster...",
  sublabel = "Validating headers, extracting coordinate reference systems, and generating preview..."
}: ProcessingIndicatorProps) {
  return (
    <div className="flex flex-col items-center justify-center p-8 bg-surface/60 border border-surfaceBorder rounded-xl backdrop-blur-sm">
      <div className="relative flex items-center justify-center">
        <div className="h-14 w-14 rounded-full border-2 border-cyan-500/20 animate-ping absolute" />
        <Loader2 className="h-8 w-8 text-cyan-400 animate-spin" />
      </div>
      <p className="mt-4 text-sm font-semibold text-slate-200 tracking-wide">{label}</p>
      {sublabel && (
        <p className="mt-1 text-xs text-slate-400 max-w-sm text-center">{sublabel}</p>
      )}
    </div>
  );
}
