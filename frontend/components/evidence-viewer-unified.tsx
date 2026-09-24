"use client";

import React, { useState } from "react";
import {
  ZoomIn,
  ZoomOut,
  Maximize2,
  RotateCcw,
  Layers,
  MapPin,
  Eye,
  Sliders,
  ShieldCheck,
  Split,
  Radio,
} from "lucide-react";
import { getImagePreviewUrl } from "@/lib/api";

interface EvidenceRegion {
  id: string;
  label: string;
  confidence?: number | null;
  pixel_coordinates?: any;
  geo_coordinates?: any;
  artifact_key?: string | null;
}

interface EvidenceViewerUnifiedProps {
  mode?: "single" | "temporal" | "cross-modal";
  primaryImageId?: string;
  primaryImageLabel?: string;
  secondaryImageId?: string;
  secondaryImageLabel?: string;
  t1ImageId?: string;
  t2ImageId?: string;
  opticalImageId?: string;
  sarImageId?: string;
  changeMapUrl?: string | null;
  evidenceRegions?: EvidenceRegion[];
  evidenceItems?: any[];
  filename?: string;
}

export function EvidenceViewerUnified({
  mode = "single",
  primaryImageId,
  primaryImageLabel,
  secondaryImageId,
  secondaryImageLabel,
  t1ImageId,
  t2ImageId,
  opticalImageId,
  sarImageId,
  changeMapUrl,
  evidenceRegions = [],
  evidenceItems = [],
  filename = "Satellite Imagery",
}: EvidenceViewerUnifiedProps) {
  const effectiveT1 = primaryImageId || t1ImageId || opticalImageId;
  const effectiveT2 = secondaryImageId || t2ImageId || sarImageId;

  const normalizedRegions: EvidenceRegion[] =
    evidenceRegions.length > 0
      ? evidenceRegions
      : evidenceItems.map((item: any, idx: number) => ({
          id: item.evidence_id || item.id || `ev_${idx}`,
          label: item.label || "Detected Region",
          confidence: item.confidence,
          pixel_coordinates: item.pixel_box || item.pixel_coordinates,
          geo_coordinates: item.crs_box || item.geo_coordinates,
        }));

  const [zoom, setZoom] = useState<number>(1);
  const [selectedRegion, setSelectedRegion] = useState<EvidenceRegion | null>(
    normalizedRegions.length > 0 ? normalizedRegions[0] : null
  );
  const [temporalViewMode, setTemporalViewMode] = useState<"side_by_side" | "diff" | "split">("side_by_side");
  const [splitSlider, setSplitSlider] = useState<number>(50);

  const handleZoomIn = () => setZoom((z) => Math.min(z + 0.25, 3));
  const handleZoomOut = () => setZoom((z) => Math.max(z - 0.25, 0.5));
  const handleResetZoom = () => setZoom(1);

  // Single Image View
  if (mode === "single" || !effectiveT2) {
    const previewUrl = effectiveT1 ? getImagePreviewUrl(effectiveT1) : null;

    return (
      <div className="space-y-3">
        {/* Controls Bar */}
        <div className="p-2.5 rounded-xl bg-slate-900/80 border border-slate-800 flex items-center justify-between text-xs">
          <div className="flex items-center space-x-2">
            <span className="font-mono text-slate-400 font-semibold text-[11px] uppercase">
              {primaryImageLabel || "Visual Evidence Overlay"}
            </span>
            {normalizedRegions.length > 0 && (
              <span className="px-2 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-800/60 font-mono text-[10px]">
                {normalizedRegions.length} Localized Feature(s)
              </span>
            )}
          </div>

          <div className="flex items-center space-x-1">
            <button
              onClick={handleZoomIn}
              className="p-1.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition"
              title="Zoom in"
            >
              <ZoomIn className="h-3.5 w-3.5" />
            </button>
            <button
              onClick={handleZoomOut}
              className="p-1.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition"
              title="Zoom out"
            >
              <ZoomOut className="h-3.5 w-3.5" />
            </button>
            <button
              onClick={handleResetZoom}
              className="p-1.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition"
              title="Reset view"
            >
              <RotateCcw className="h-3.5 w-3.5" />
            </button>
          </div>
        </div>

        {/* Viewport */}
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
          <div className="lg:col-span-3 rounded-xl border border-slate-800 bg-slate-950 overflow-hidden relative min-h-[360px] flex items-center justify-center">
            {previewUrl ? (
              <div
                className="transition-transform duration-200 relative inline-block max-w-full"
                style={{ transform: `scale(${zoom})`, transformOrigin: "center center" }}
              >
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={previewUrl}
                  alt={filename}
                  className="max-h-[500px] w-auto object-contain rounded select-none pointer-events-none"
                />

                {/* SVG Overlay */}
                <svg
                  className="absolute inset-0 w-full h-full pointer-events-auto"
                  viewBox="0 0 100 100"
                  preserveAspectRatio="none"
                >
                  {normalizedRegions.map((r) => {
                    const isSelected = selectedRegion?.id === r.id;
                    const coords = r.pixel_coordinates || [10, 10, 80, 80];
                    const [ymin, xmin, ymax, xmax] = Array.isArray(coords)
                      ? coords
                      : [coords.y1 || 10, coords.x1 || 10, coords.y2 || 80, coords.x2 || 80];

                    const normX = Math.min(Math.max(xmin, 0), 100);
                    const normY = Math.min(Math.max(ymin, 0), 100);
                    const normW = Math.max(Math.min(xmax - xmin, 100), 5);
                    const normH = Math.max(Math.min(ymax - ymin, 100), 5);

                    return (
                      <g key={r.id} onClick={() => setSelectedRegion(r)} className="cursor-pointer group">
                        <rect
                          x={normX}
                          y={normY}
                          width={normW}
                          height={normH}
                          fill={isSelected ? "rgba(6, 182, 212, 0.25)" : "rgba(20, 184, 166, 0.15)"}
                          stroke={isSelected ? "#06b6d4" : "#14b8a6"}
                          strokeWidth={isSelected ? "1.5" : "0.8"}
                          strokeDasharray={isSelected ? "none" : "2,2"}
                          className="transition-all"
                        />
                        <text
                          x={normX + 1}
                          y={Math.max(normY - 1.5, 4)}
                          fill="#fff"
                          fontSize="3.2"
                          fontFamily="monospace"
                          fontWeight="bold"
                        >
                          {r.label} {r.confidence ? `(${Math.round(r.confidence * 100)}%)` : ""}
                        </text>
                      </g>
                    );
                  })}
                </svg>
              </div>
            ) : (
              <div className="text-slate-500 font-mono text-xs">No preview image loaded</div>
            )}
          </div>

          {/* Region Inspection Sidebar */}
          <div className="lg:col-span-1 space-y-3">
            <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 space-y-2">
              <span className="text-[11px] font-mono text-slate-400 font-semibold uppercase block">
                Detected Regions ({normalizedRegions.length})
              </span>

              {normalizedRegions.length === 0 ? (
                <p className="text-slate-500 text-xs py-2">
                  No bounding boxes detected. Global scene-level synthesis applied.
                </p>
              ) : (
                <div className="space-y-1.5 max-h-[300px] overflow-y-auto pr-1">
                  {normalizedRegions.map((r) => {
                    const isSelected = selectedRegion?.id === r.id;
                    return (
                      <button
                        key={r.id}
                        onClick={() => setSelectedRegion(r)}
                        className={`w-full p-2 rounded-lg text-left text-xs transition border font-mono ${
                          isSelected
                            ? "bg-cyan-950/80 border-cyan-800/80 text-white"
                            : "bg-slate-950/60 border-slate-800/60 text-slate-300 hover:bg-slate-800/40"
                        }`}
                      >
                        <div className="font-semibold truncate">{r.label}</div>
                        <div className="text-[10px] text-slate-400 flex items-center justify-between mt-0.5">
                          <span>Conf: {r.confidence ? `${Math.round(r.confidence * 100)}%` : "N/A"}</span>
                          <span className="text-cyan-400">Select</span>
                        </div>
                      </button>
                    );
                  })}
                </div>
              )}
            </div>

            {selectedRegion && (
              <div className="p-3 rounded-xl bg-slate-900/40 border border-slate-800/60 font-mono text-xs space-y-1.5">
                <span className="text-[10px] text-slate-500 uppercase font-bold block">Selected Feature</span>
                <div className="text-cyan-300 font-semibold">{selectedRegion.label}</div>
                <div>
                  <span className="text-slate-500 block text-[10px]">PIXELS:</span>
                  <span className="text-slate-300 text-[10px] truncate block">
                    {JSON.stringify(selectedRegion.pixel_coordinates)}
                  </span>
                </div>
                <div>
                  <span className="text-slate-500 block text-[10px]">COORDINATES:</span>
                  <span className="text-slate-300 text-[10px] truncate block">
                    {selectedRegion.geo_coordinates
                      ? JSON.stringify(selectedRegion.geo_coordinates)
                      : "Pixel Frame"}
                  </span>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    );
  }

  // Bi-Temporal View
  if (mode === "temporal") {
    const t1Url = effectiveT1 ? getImagePreviewUrl(effectiveT1) : null;
    const t2Url = effectiveT2 ? getImagePreviewUrl(effectiveT2) : null;

    return (
      <div className="space-y-3">
        {/* Mode Selector */}
        <div className="p-2.5 rounded-xl bg-slate-900/80 border border-slate-800 flex items-center justify-between text-xs">
          <div className="flex items-center space-x-2">
            <span className="font-mono text-slate-400 font-semibold text-[11px] uppercase">
              Bi-Temporal Mode
            </span>
          </div>

          <div className="flex items-center space-x-1.5 font-mono text-[11px]">
            <button
              onClick={() => setTemporalViewMode("side_by_side")}
              className={`px-2.5 py-1 rounded transition ${
                temporalViewMode === "side_by_side" ? "bg-cyan-950 text-cyan-300 border border-cyan-800/60" : "text-slate-400 hover:text-white"
              }`}
            >
              Side-by-Side
            </button>
            <button
              onClick={() => setTemporalViewMode("split")}
              className={`px-2.5 py-1 rounded transition ${
                temporalViewMode === "split" ? "bg-cyan-950 text-cyan-300 border border-cyan-800/60" : "text-slate-400 hover:text-white"
              }`}
            >
              Swipe / Split
            </button>
            {changeMapUrl && (
              <button
                onClick={() => setTemporalViewMode("diff")}
                className={`px-2.5 py-1 rounded transition ${
                  temporalViewMode === "diff" ? "bg-cyan-950 text-cyan-300 border border-cyan-800/60" : "text-slate-400 hover:text-white"
                }`}
              >
                Change Map
              </button>
            )}
          </div>
        </div>

        {/* View Container */}
        {temporalViewMode === "side_by_side" && (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="rounded-xl border border-slate-800 bg-slate-950 p-3 space-y-2">
              <span className="text-xs font-mono font-semibold text-cyan-400 block">
                {primaryImageLabel || "T1 Before Epoch"}
              </span>
              {t1Url && (
                /* eslint-disable-next-line @next/next/no-img-element */
                <img src={t1Url} alt="T1 Before" className="w-full h-auto max-h-[350px] object-contain rounded" />
              )}
            </div>
            <div className="rounded-xl border border-slate-800 bg-slate-950 p-3 space-y-2">
              <span className="text-xs font-mono font-semibold text-emerald-400 block">
                {secondaryImageLabel || "T2 After Epoch"}
              </span>
              {t2Url && (
                /* eslint-disable-next-line @next/next/no-img-element */
                <img src={t2Url} alt="T2 After" className="w-full h-auto max-h-[350px] object-contain rounded" />
              )}
            </div>
          </div>
        )}

        {temporalViewMode === "split" && t1Url && t2Url && (
          <div className="rounded-xl border border-slate-800 bg-slate-950 p-3 space-y-3">
            <div className="relative overflow-hidden rounded max-h-[400px] flex items-center justify-center">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={t2Url} alt="T2 After" className="w-full h-auto object-contain" />
              <div
                className="absolute inset-y-0 left-0 overflow-hidden"
                style={{ width: `${splitSlider}%` }}
              >
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src={t1Url} alt="T1 Before" className="w-full h-auto object-contain max-w-none" />
              </div>
              <div
                className="absolute inset-y-0 w-0.5 bg-cyan-400 pointer-events-none shadow-[0_0_8px_rgba(6,182,212,0.8)]"
                style={{ left: `${splitSlider}%` }}
              />
            </div>
            <div className="flex items-center space-x-3 px-2">
              <span className="text-xs font-mono text-slate-400">T1</span>
              <input
                type="range"
                min="0"
                max="100"
                value={splitSlider}
                onChange={(e) => setSplitSlider(Number(e.target.value))}
                className="w-full accent-cyan-400"
              />
              <span className="text-xs font-mono text-slate-400">T2</span>
            </div>
          </div>
        )}

        {temporalViewMode === "diff" && changeMapUrl && (
          <div className="rounded-xl border border-slate-800 bg-slate-950 p-3 space-y-2">
            <span className="text-xs font-mono font-semibold text-rose-400 block">
              Bi-Temporal Spectral Difference Map
            </span>
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={changeMapUrl} alt="Change Map" className="w-full h-auto max-h-[400px] object-contain rounded" />
          </div>
        )}
      </div>
    );
  }

  // Optical + SAR Cross-Modal View
  const optUrl = effectiveT1 ? getImagePreviewUrl(effectiveT1) : null;
  const sarUrl = effectiveT2 ? getImagePreviewUrl(effectiveT2) : null;

  return (
    <div className="space-y-3">
      <div className="p-2.5 rounded-xl bg-slate-900/80 border border-slate-800 flex items-center justify-between text-xs font-mono">
        <span className="text-slate-400 font-semibold uppercase text-[11px]">
          Optical + SAR Cross-Modal Fusion
        </span>
        <span className="text-cyan-400 flex items-center space-x-1 text-[11px]">
          <Radio className="h-3.5 w-3.5" />
          <span>Synchronized Co-Registration</span>
        </span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div className="rounded-xl border border-slate-800 bg-slate-950 p-3 space-y-2">
          <span className="text-xs font-mono font-semibold text-cyan-400 block">
            {primaryImageLabel || "Optical Sensor (Sentinel-2 / Cartosat-2S)"}
          </span>
          {optUrl ? (
            /* eslint-disable-next-line @next/next/no-img-element */
            <img src={optUrl} alt="Optical" className="w-full h-auto max-h-[350px] object-contain rounded" />
          ) : (
            <div className="h-40 flex items-center justify-center text-xs text-slate-500 font-mono">No optical raster loaded</div>
          )}
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-950 p-3 space-y-2">
          <span className="text-xs font-mono font-semibold text-teal-400 block">
            {secondaryImageLabel || "SAR Sensor (Sentinel-1 / RISAT Backscatter dB)"}
          </span>
          {sarUrl ? (
            /* eslint-disable-next-line @next/next/no-img-element */
            <img src={sarUrl} alt="SAR" className="w-full h-auto max-h-[350px] object-contain rounded" />
          ) : (
            <div className="h-40 flex items-center justify-center text-xs text-slate-500 font-mono">No SAR raster loaded</div>
          )}
        </div>
      </div>
    </div>
  );
}
