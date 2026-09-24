"use client";

import React from "react";
import { CheckCircle2, AlertTriangle, XCircle, ShieldCheck } from "lucide-react";
import { ValidationResult } from "@/lib/types";

interface ValidationStatusProps {
  status?: "valid" | "warning" | "error";
  validation?: ValidationResult;
  className?: string;
}

export function ValidationStatus({ status, validation, className = "" }: ValidationStatusProps) {
  // Determine state
  const hasErrors = validation && validation.errors && validation.errors.length > 0;
  const hasWarnings = validation && validation.warnings && validation.warnings.length > 0;

  let computedStatus: "valid" | "warning" | "error" = status || "valid";
  if (hasErrors) {
    computedStatus = "error";
  } else if (hasWarnings) {
    computedStatus = "warning";
  }

  const warnings = validation?.warnings || [];
  const errors = validation?.errors || [];

  return (
    <div className={`rounded-xl border p-4 transition-all ${
      computedStatus === "valid"
        ? "bg-emerald-950/20 border-emerald-700/40 text-emerald-300"
        : computedStatus === "warning"
        ? "bg-amber-950/20 border-amber-700/40 text-amber-300"
        : "bg-rose-950/20 border-rose-700/40 text-rose-300"
    } ${className}`}>
      <div className="flex items-center space-x-3">
        {computedStatus === "valid" && (
          <div className="p-2 rounded-lg bg-emerald-500/20 border border-emerald-500/40 text-emerald-400">
            <CheckCircle2 className="h-5 w-5" aria-hidden="true" />
          </div>
        )}
        {computedStatus === "warning" && (
          <div className="p-2 rounded-lg bg-amber-500/20 border border-amber-500/40 text-amber-400">
            <AlertTriangle className="h-5 w-5" aria-hidden="true" />
          </div>
        )}
        {computedStatus === "error" && (
          <div className="p-2 rounded-lg bg-rose-500/20 border border-rose-500/40 text-rose-400">
            <XCircle className="h-5 w-5" aria-hidden="true" />
          </div>
        )}

        <div className="flex-1">
          <div className="flex items-center space-x-2">
            <span className="font-semibold text-sm">
              {computedStatus === "valid" && "✓ Image Valid & Verified"}
              {computedStatus === "warning" && "⚠ Valid with Format Warnings"}
              {computedStatus === "error" && "✕ Invalid Raster File"}
            </span>
            <span className="text-[11px] px-2 py-0.5 rounded-full uppercase tracking-wider font-mono border bg-slate-900/60 border-slate-700/60 text-slate-300">
              {computedStatus}
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-0.5">
            {computedStatus === "valid" && "All raster headers, geospatial tags, and dimensions comply with remote-sensing standards."}
            {computedStatus === "warning" && "Image read successfully, but lacks complete geospatial projection or georeferencing metadata."}
            {computedStatus === "error" && "The file failed structural raster checks or contains invalid data."}
          </p>
        </div>
      </div>

      {/* Warnings list */}
      {warnings.length > 0 && (
        <div className="mt-3 pt-3 border-t border-amber-800/40">
          <p className="text-xs font-semibold text-amber-400 mb-1">Warnings ({warnings.length}):</p>
          <ul className="space-y-1">
            {warnings.map((w, idx) => (
              <li key={idx} className="text-xs text-amber-200/90 flex items-start space-x-1.5">
                <span className="text-amber-400 mt-0.5">•</span>
                <span>{w}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Errors list */}
      {errors.length > 0 && (
        <div className="mt-3 pt-3 border-t border-rose-800/40">
          <p className="text-xs font-semibold text-rose-400 mb-1">Errors ({errors.length}):</p>
          <ul className="space-y-1">
            {errors.map((e, idx) => (
              <li key={idx} className="text-xs text-rose-200/90 flex items-start space-x-1.5">
                <span className="text-rose-400 mt-0.5">•</span>
                <span>{e}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
