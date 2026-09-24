"use client";

import React, { useState } from "react";
import { Cpu, ChevronDown, ChevronUp, Sparkles, CheckCircle2 } from "lucide-react";

interface ModelDetailsProps {
  modelName?: string;
  modelVersion?: string;
  task?: string;
  isAdapted?: boolean;
  adapterType?: string | null;
  datasetProvenance?: string | null;
  device?: string;
  details?: {
    architecture?: string;
    base_model?: string;
    adapter_id?: string;
    adapter_type?: string;
    quantization?: string;
    model_name?: string;
    version?: string;
  };
}

export function ModelDetails({
  modelName,
  modelVersion = "1.0.0",
  task = "Remote-Sensing Vision Analysis",
  isAdapted = true,
  adapterType = "PEFT / LoRA (Rank 8)",
  datasetProvenance = "BigEarthNet v2.0 (Sentinel-1/2)",
  device = "CPU (Pure PyTorch)",
  details,
}: ModelDetailsProps) {
  const [open, setOpen] = useState(false);

  const effectiveName = modelName || details?.base_model || details?.model_name || "Qwen2.5-VL-7B-Instruct";
  const effectiveAdapter = adapterType || details?.adapter_type || details?.adapter_id || "satquery-bigearthnet-lora-v2";

  return (
    <div className="rounded-xl bg-slate-900/60 border border-slate-800 overflow-hidden text-xs">
      <button
        onClick={() => setOpen(!open)}
        className="w-full p-3.5 flex items-center justify-between hover:bg-slate-800/40 transition text-left"
      >
        <div className="flex items-center space-x-2.5">
          <div className="p-1 rounded bg-cyan-950 text-cyan-400 border border-cyan-800/50">
            <Cpu className="h-3.5 w-3.5" />
          </div>
          <div>
            <div className="font-mono font-medium text-white flex items-center space-x-2">
              <span>{modelName}</span>
              {isAdapted && (
                <span className="px-1.5 py-0.2 rounded text-[9px] font-mono bg-cyan-950 text-cyan-300 border border-cyan-800/60">
                  RS-Adapted
                </span>
              )}
            </div>
            <p className="text-[11px] text-slate-500 font-mono mt-0.5">
              Task: {task} · Execution on {device}
            </p>
          </div>
        </div>

        <div className="text-slate-400">
          {open ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
        </div>
      </button>

      {open && (
        <div className="p-3.5 pt-0 border-t border-slate-800/60 space-y-2 bg-slate-950/40 text-[11px] font-mono">
          <div className="grid grid-cols-2 gap-2 pt-2">
            <div>
              <span className="text-slate-500 block">BASE MODEL:</span>
              <span className="text-slate-300">Salesforce/blip-vqa-base</span>
            </div>
            <div>
              <span className="text-slate-500 block">MODEL VERSION:</span>
              <span className="text-slate-300">v{modelVersion}</span>
            </div>
            <div>
              <span className="text-slate-500 block">ADAPTATION ARCHITECTURE:</span>
              <span className="text-cyan-400">{adapterType || "Direct LoRA Adapter"}</span>
            </div>
            <div>
              <span className="text-slate-500 block">TRAINING DATASET:</span>
              <span className="text-slate-300">{datasetProvenance || "BigEarthNet v2.0"}</span>
            </div>
          </div>
          <p className="text-slate-500 pt-1 text-[10px] leading-relaxed">
            Trained and verified under strict zero-data-leakage 70/15/15 test partitions.
          </p>
        </div>
      )}
    </div>
  );
}
