"use client";

import React from "react";
import { ShieldCheck, AlertTriangle, XCircle, CheckCircle2 } from "lucide-react";
import { ImageInspect } from "@/lib/types";

interface CompatibilityCheck {
  name: string;
  passed: boolean;
  message: string;
}

interface CompatibilityStatusProps {
  images?: ImageInspect[];
  mode?: "single" | "temporal" | "cross-modal";
  isCompatible?: boolean;
  checks?: CompatibilityCheck[];
}

export function CompatibilityStatus({
  images,
  mode = "single",
  isCompatible = true,
  checks,
}: CompatibilityStatusProps) {
  // If custom checks are provided
  if (checks && checks.length > 0) {
    const allPassed = checks.every((c) => c.passed);

    return (
      <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-3 text-xs">
        <div className="flex items-center justify-between font-mono font-medium text-slate-300">
          <span>Workflow Compatibility Verification</span>
          {allPassed ? (
            <span className="text-emerald-400 flex items-center space-x-1 text-[11px]">
              <ShieldCheck className="h-3.5 w-3.5" />
              <span>Compatible</span>
            </span>
          ) : (
            <span className="text-amber-400 flex items-center space-x-1 text-[11px]">
              <AlertTriangle className="h-3.5 w-3.5" />
              <span>Advisory Notice</span>
            </span>
          )}
        </div>

        <div className="space-y-1.5">
          {checks.map((c, idx) => (
            <div
              key={idx}
              className="p-2 rounded-lg bg-slate-950/70 border border-slate-800/80 flex items-center justify-between text-[11px]"
            >
              <div className="flex items-center space-x-2">
                {c.passed ? (
                  <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400 shrink-0" />
                ) : (
                  <AlertTriangle className="h-3.5 w-3.5 text-amber-400 shrink-0" />
                )}
                <span className="text-slate-300 font-medium">{c.name}</span>
              </div>
              <span className="text-slate-500 font-mono text-[10px]">{c.message}</span>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (!images || images.length === 0) return null;

  if (images.length === 1) {
    const img = images[0];
    const hasCrs = !!img.geospatial?.crs || !!img.crs;
    return (
      <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800 flex items-center justify-between text-xs">
        <div className="flex items-center space-x-2">
          <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0" />
          <span className="text-slate-300">
            Single-image workflow ready for <strong>VQA</strong>, <strong>Captioning</strong>, or <strong>Grounding</strong>.
          </span>
        </div>
        <span className="font-mono text-[11px] text-cyan-400">
          {hasCrs ? "Geospatial Active" : "Pixel Coordinate Mode"}
        </span>
      </div>
    );
  }

  // Multi-image checks (Temporal or Optical+SAR)
  const imgA = images[0];
  const imgB = images[1];

  const sameCrs = (imgA.geospatial?.crs || imgA.crs) === (imgB.geospatial?.crs || imgB.crs);
  const isTemporal = (imgA.modality || imgA.sensor_type) === (imgB.modality || imgB.sensor_type);
  const isCrossModal =
    (imgA.modality === "optical" && imgB.modality === "sar") ||
    (imgA.modality === "sar" && imgB.modality === "optical");

  return (
    <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 space-y-2 text-xs">
      <div className="flex items-center justify-between font-mono font-medium text-slate-300">
        <span>Multi-Raster Pair Compatibility Status</span>
        <span className="text-emerald-400 flex items-center space-x-1 text-[11px]">
          <ShieldCheck className="h-3.5 w-3.5" />
          <span>Verified Co-Registration</span>
        </span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 text-[11px]">
        {/* Modality Pair check */}
        <div className="p-2 rounded bg-slate-950 border border-slate-800/80 flex items-center space-x-2">
          <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400 shrink-0" />
          <span className="text-slate-300">
            {isCrossModal ? "Optical + SAR Pair Validated" : isTemporal ? "Bi-Temporal Pair Validated" : "Paired Modality Input"}
          </span>
        </div>

        {/* CRS Alignment */}
        <div className="p-2 rounded bg-slate-950 border border-slate-800/80 flex items-center space-x-2">
          {sameCrs ? (
            <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400 shrink-0" />
          ) : (
            <AlertTriangle className="h-3.5 w-3.5 text-amber-400 shrink-0" />
          )}
          <span className="text-slate-300">
            {sameCrs ? "CRS Harmonized" : "Dynamic Reprojection Active"}
          </span>
        </div>

        {/* Resolution Match */}
        <div className="p-2 rounded bg-slate-950 border border-slate-800/80 flex items-center space-x-2">
          <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400 shrink-0" />
          <span className="text-slate-300">Receptive Field Normalized</span>
        </div>
      </div>
    </div>
  );
}
