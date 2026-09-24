"use client";

import React, { useState, useRef, useEffect } from "react";
import {
  GitCompare,
  Sliders,
  Columns,
  Layers,
  Crosshair,
  Maximize2,
  Minimize2,
  ZoomIn,
  ZoomOut,
  RotateCcw,
  Calendar,
  AlertCircle,
  CheckCircle2,
  MapPin,
  TrendingUp,
  Sparkles,
  Eye,
  Info,
} from "lucide-react";
import { BiTemporalPair, ChangeRegion, ChangeAnalysisSummary } from "../lib/types";
import { getImagePreviewUrl, getDirectArtifactUrl } from "../lib/api";

interface BiTemporalViewerProps {
  pair: BiTemporalPair;
  changeSummary?: ChangeAnalysisSummary | null;
  regions?: ChangeRegion[];
  artifactKey?: string | null;
  answer?: string;
  className?: string;
}

export function BiTemporalViewer({
  pair,
  changeSummary,
  regions = [],
  artifactKey,
  answer,
  className = "",
}: BiTemporalViewerProps) {
  const [mode, setMode] = useState<"side-by-side" | "split" | "overlay" | "regions">("side-by-side");
  const [sliderPos, setSliderPos] = useState<number>(50); // 0 to 100%
  const [isDragging, setIsDragging] = useState<boolean>(false);
  const [zoom, setZoom] = useState<number>(1);
  const [isFullscreen, setIsFullscreen] = useState<boolean>(false);
  const [selectedRegionId, setSelectedRegionId] = useState<string | null>(null);
  const [hoveredRegionId, setHoveredRegionId] = useState<string | null>(null);

  const containerRef = useRef<HTMLDivElement>(null);
  const sliderRef = useRef<HTMLDivElement>(null);

  const t1Url = getImagePreviewUrl(pair.image_t1.id);
  const t2Url = getImagePreviewUrl(pair.image_t2.id);
  const overlayUrl = artifactKey ? getDirectArtifactUrl(artifactKey) : null;

  const t1Date = pair.acquisition_time_t1
    ? new Date(pair.acquisition_time_t1).toLocaleDateString(undefined, {
        year: "numeric",
        month: "short",
        day: "numeric",
      })
    : "T1 (Earlier)";

  const t2Date = pair.acquisition_time_t2
    ? new Date(pair.acquisition_time_t2).toLocaleDateString(undefined, {
        year: "numeric",
        month: "short",
        day: "numeric",
      })
    : "T2 (Later)";

  const handleZoomIn = () => setZoom((prev) => Math.min(prev + 0.25, 3));
  const handleZoomOut = () => setZoom((prev) => Math.max(prev - 0.25, 0.5));
  const handleResetZoom = () => setZoom(1);

  // Split slider mouse events
  const handleMouseDown = () => setIsDragging(true);

  useEffect(() => {
    const handleMouseUp = () => setIsDragging(false);
    const handleMouseMove = (e: MouseEvent) => {
      if (!isDragging || !sliderRef.current) return;
      const rect = sliderRef.current.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const pct = Math.max(0, Math.min(100, (x / rect.width) * 100));
      setSliderPos(pct);
    };

    if (isDragging) {
      window.addEventListener("mousemove", handleMouseMove);
      window.addEventListener("mouseup", handleMouseUp);
    }
    return () => {
      window.removeEventListener("mousemove", handleMouseMove);
      window.removeEventListener("mouseup", handleMouseUp);
    };
  }, [isDragging]);

  const selectedRegion = regions.find((r) => r.region_id === selectedRegionId) || null;

  return (
    <div
      ref={containerRef}
      className={`flex flex-col rounded-xl overflow-hidden border border-slate-800 bg-slate-950/90 shadow-2xl transition-all ${
        isFullscreen ? "fixed inset-0 z-50 rounded-none bg-slate-950 p-6 flex flex-col" : className
      }`}
    >
      {/* Viewer Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 px-4 py-3 bg-slate-900/90 border-b border-slate-800">
        <div className="flex items-center space-x-2.5">
          <div className="p-1.5 rounded-lg bg-amber-950/60 border border-amber-700/60 text-amber-400">
            <GitCompare className="h-4 w-4" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-xs font-semibold text-slate-200 uppercase tracking-wider">
                Bi-Temporal Change Analysis
              </span>
              {changeSummary && (
                <span
                  className={`px-2 py-0.5 text-[10px] font-mono rounded-full border ${
                    changeSummary.detected
                      ? "bg-amber-950/80 border-amber-800 text-amber-300"
                      : "bg-emerald-950/80 border-emerald-800 text-emerald-300"
                  }`}
                >
                  {changeSummary.detected
                    ? `${changeSummary.change_percentage}% Change Detected`
                    : "No Significant Change"}
                </span>
              )}
            </div>
            <p className="text-[11px] text-slate-400 font-mono mt-0.5">
              T1: {t1Date} ({pair.image_t1.filename}) → T2: {t2Date} ({pair.image_t2.filename})
            </p>
          </div>
        </div>

        {/* View Mode Selectors & Controls */}
        <div className="flex items-center space-x-1.5 bg-slate-950/60 p-1 rounded-lg border border-slate-800/80">
          <button
            onClick={() => setMode("side-by-side")}
            className={`flex items-center space-x-1.5 px-2.5 py-1 text-xs rounded font-medium transition ${
              mode === "side-by-side"
                ? "bg-slate-800 text-amber-400 shadow-sm"
                : "text-slate-400 hover:text-slate-200 hover:bg-slate-900"
            }`}
            title="Side-by-Side Comparison"
          >
            <Columns className="h-3.5 w-3.5" />
            <span className="hidden sm:inline">Side-by-Side</span>
          </button>

          <button
            onClick={() => setMode("split")}
            className={`flex items-center space-x-1.5 px-2.5 py-1 text-xs rounded font-medium transition ${
              mode === "split"
                ? "bg-slate-800 text-amber-400 shadow-sm"
                : "text-slate-400 hover:text-slate-200 hover:bg-slate-900"
            }`}
            title="Interactive Split Slider"
          >
            <Sliders className="h-3.5 w-3.5" />
            <span className="hidden sm:inline">Split Slider</span>
          </button>

          <button
            onClick={() => setMode("overlay")}
            disabled={!overlayUrl}
            className={`flex items-center space-x-1.5 px-2.5 py-1 text-xs rounded font-medium transition ${
              mode === "overlay"
                ? "bg-slate-800 text-amber-400 shadow-sm"
                : overlayUrl
                ? "text-slate-400 hover:text-slate-200 hover:bg-slate-900"
                : "text-slate-600 cursor-not-allowed"
            }`}
            title="Heatmap / Change Map Overlay"
          >
            <Layers className="h-3.5 w-3.5" />
            <span className="hidden sm:inline">Change Overlay</span>
          </button>

          <button
            onClick={() => setMode("regions")}
            disabled={regions.length === 0}
            className={`flex items-center space-x-1.5 px-2.5 py-1 text-xs rounded font-medium transition ${
              mode === "regions"
                ? "bg-slate-800 text-amber-400 shadow-sm"
                : regions.length > 0
                ? "text-slate-400 hover:text-slate-200 hover:bg-slate-900"
                : "text-slate-600 cursor-not-allowed"
            }`}
            title="Change Regions Bounding Boxes"
          >
            <Crosshair className="h-3.5 w-3.5" />
            <span className="hidden sm:inline">Regions ({regions.length})</span>
          </button>

          <div className="h-4 w-px bg-slate-800 mx-1" />

          {/* Zoom & Fullscreen Controls */}
          <div className="flex items-center space-x-0.5">
            <button
              onClick={handleZoomOut}
              className="p-1 text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded transition"
              title="Zoom Out"
            >
              <ZoomOut className="h-3.5 w-3.5" />
            </button>
            <span className="text-[10px] font-mono text-slate-500 w-8 text-center">
              {Math.round(zoom * 100)}%
            </span>
            <button
              onClick={handleZoomIn}
              className="p-1 text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded transition"
              title="Zoom In"
            >
              <ZoomIn className="h-3.5 w-3.5" />
            </button>
            <button
              onClick={handleResetZoom}
              className="p-1 text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded transition"
              title="Reset Zoom"
            >
              <RotateCcw className="h-3.5 w-3.5" />
            </button>
            <button
              onClick={() => setIsFullscreen(!isFullscreen)}
              className="p-1 text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded transition"
              title={isFullscreen ? "Exit Fullscreen" : "Fullscreen"}
            >
              {isFullscreen ? <Minimize2 className="h-3.5 w-3.5" /> : <Maximize2 className="h-3.5 w-3.5" />}
            </button>
          </div>
        </div>
      </div>

      {/* Main Canvas Area */}
      <div className="relative flex-1 bg-slate-950 overflow-hidden flex items-center justify-center min-h-[420px]">
        {/* MODE 1: Side-by-Side Mode */}
        {mode === "side-by-side" && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2 p-4 w-full h-full max-w-6xl mx-auto">
            {/* T1 Reference Card */}
            <div className="relative rounded-lg border border-slate-800 bg-slate-900/60 overflow-hidden flex flex-col">
              <div className="flex items-center justify-between px-3 py-1.5 bg-slate-950/80 border-b border-slate-800/80 text-xs">
                <span className="font-semibold text-slate-300 flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-blue-500" />
                  Baseline T1
                </span>
                <span className="text-[11px] text-slate-400 font-mono flex items-center gap-1">
                  <Calendar className="h-3 w-3" />
                  {t1Date}
                </span>
              </div>
              <div className="relative flex-1 overflow-hidden flex items-center justify-center p-2">
                <img
                  src={t1Url}
                  alt={`Baseline T1 ${pair.image_t1.filename}`}
                  style={{ transform: `scale(${zoom})`, transformOrigin: "center" }}
                  className="max-h-[380px] w-auto object-contain rounded shadow-lg transition-transform duration-100"
                />
              </div>
            </div>

            {/* T2 Target Card */}
            <div className="relative rounded-lg border border-slate-800 bg-slate-900/60 overflow-hidden flex flex-col">
              <div className="flex items-center justify-between px-3 py-1.5 bg-slate-950/80 border-b border-slate-800/80 text-xs">
                <span className="font-semibold text-slate-300 flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-amber-500" />
                  Target T2
                </span>
                <span className="text-[11px] text-slate-400 font-mono flex items-center gap-1">
                  <Calendar className="h-3 w-3" />
                  {t2Date}
                </span>
              </div>
              <div className="relative flex-1 overflow-hidden flex items-center justify-center p-2">
                <img
                  src={t2Url}
                  alt={`Target T2 ${pair.image_t2.filename}`}
                  style={{ transform: `scale(${zoom})`, transformOrigin: "center" }}
                  className="max-h-[380px] w-auto object-contain rounded shadow-lg transition-transform duration-100"
                />
              </div>
            </div>
          </div>
        )}

        {/* MODE 2: Split Slider Mode */}
        {mode === "split" && (
          <div
            ref={sliderRef}
            onMouseDown={handleMouseDown}
            className="relative w-full max-w-4xl h-[420px] select-none cursor-ew-resize overflow-hidden rounded-lg border border-slate-800 shadow-2xl flex items-center justify-center bg-slate-900/40"
          >
            {/* T2 (Underneath / Full Layer) */}
            <img
              src={t2Url}
              alt="T2 Target"
              style={{ transform: `scale(${zoom})`, transformOrigin: "center" }}
              className="absolute inset-0 w-full h-full object-contain pointer-events-none"
            />

            {/* T1 (Clipped Top Layer) */}
            <div
              className="absolute inset-0 overflow-hidden pointer-events-none"
              style={{ width: `${sliderPos}%` }}
            >
              <img
                src={t1Url}
                alt="T1 Baseline"
                style={{
                  transform: `scale(${zoom})`,
                  transformOrigin: "center",
                  width: sliderRef.current?.clientWidth || "100%",
                }}
                className="absolute inset-0 h-full object-contain max-w-none"
              />
            </div>

            {/* Draggable Divider Bar */}
            <div
              className="absolute top-0 bottom-0 w-0.5 bg-amber-400 shadow-[0_0_12px_rgba(251,191,36,0.8)] pointer-events-none"
              style={{ left: `${sliderPos}%` }}
            >
              <div className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 w-8 h-8 rounded-full bg-slate-900 border-2 border-amber-400 flex items-center justify-center shadow-xl">
                <Sliders className="h-4 w-4 text-amber-400 rotate-90" />
              </div>
            </div>

            {/* Corner Date Badges */}
            <div className="absolute top-3 left-3 px-2 py-1 bg-slate-950/80 backdrop-blur rounded border border-slate-700 text-[11px] font-mono text-blue-300 pointer-events-none">
              T1: {t1Date}
            </div>
            <div className="absolute top-3 right-3 px-2 py-1 bg-slate-950/80 backdrop-blur rounded border border-slate-700 text-[11px] font-mono text-amber-300 pointer-events-none">
              T2: {t2Date}
            </div>
          </div>
        )}

        {/* MODE 3: Change Overlay / Heatmap Mode */}
        {mode === "overlay" && overlayUrl && (
          <div className="relative w-full max-w-4xl h-[420px] flex items-center justify-center p-4">
            <div className="relative overflow-hidden rounded-lg border border-slate-800 shadow-2xl">
              <img
                src={overlayUrl}
                alt="Change Map Overlay"
                style={{ transform: `scale(${zoom})`, transformOrigin: "center" }}
                className="max-h-[380px] w-auto object-contain transition-transform duration-100"
              />
              <div className="absolute bottom-3 right-3 px-2 py-1 bg-slate-950/90 rounded border border-amber-600/60 text-[11px] font-mono text-amber-300 flex items-center gap-1.5 shadow">
                <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
                Red Mask = Detected Land Change
              </div>
            </div>
          </div>
        )}

        {/* MODE 4: Regions / Visual Bounding Box Mode */}
        {mode === "regions" && (
          <div className="relative w-full max-w-4xl h-[420px] flex items-center justify-center p-4">
            <div className="relative overflow-hidden rounded-lg border border-slate-800 shadow-2xl">
              <img
                src={t2Url}
                alt="T2 Target with Regions"
                style={{ transform: `scale(${zoom})`, transformOrigin: "center" }}
                className="max-h-[380px] w-auto object-contain transition-transform duration-100"
              />

              {/* Render Change Region Bounding Boxes */}
              <div
                className="absolute inset-0 pointer-events-auto"
                style={{ transform: `scale(${zoom})`, transformOrigin: "center" }}
              >
                {regions.map((reg) => {
                  const [x1, y1, x2, y2] = reg.bbox;
                  const isSelected = selectedRegionId === reg.region_id;
                  const isHovered = hoveredRegionId === reg.region_id;

                  return (
                    <div
                      key={reg.region_id}
                      onClick={() => setSelectedRegionId(reg.region_id)}
                      onMouseEnter={() => setHoveredRegionId(reg.region_id)}
                      onMouseLeave={() => setHoveredRegionId(null)}
                      style={{
                        left: `${x1 * 100}%`,
                        top: `${y1 * 100}%`,
                        width: `${(x2 - x1) * 100}%`,
                        height: `${(y2 - y1) * 100}%`,
                      }}
                      className={`absolute cursor-pointer border-2 transition-all ${
                        isSelected
                          ? "border-amber-400 bg-amber-500/30 ring-2 ring-amber-400/50 z-20"
                          : isHovered
                          ? "border-amber-300 bg-amber-500/20 z-10"
                          : "border-red-500/80 bg-red-500/10"
                      }`}
                    >
                      <span className="absolute -top-5 left-0 px-1 py-0.2 bg-slate-900/90 text-[10px] font-mono text-amber-300 rounded border border-slate-700 shadow whitespace-nowrap">
                        {reg.label} ({Math.round(reg.confidence * 100)}%)
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Answer & Change Metrics Bar */}
      {answer && (
        <div className="px-4 py-3 bg-slate-900/70 border-t border-slate-800/80">
          <div className="flex items-start gap-2.5">
            <div className="p-1 rounded bg-amber-950/60 border border-amber-800 text-amber-400 mt-0.5">
              <Sparkles className="h-3.5 w-3.5" />
            </div>
            <div className="flex-1">
              <p className="text-xs font-medium text-slate-200 leading-relaxed">{answer}</p>
            </div>
          </div>
        </div>
      )}

      {/* Region Cards Drawer (When regions exist) */}
      {regions.length > 0 && (
        <div className="px-4 py-2.5 bg-slate-950/90 border-t border-slate-800/80 overflow-x-auto">
          <div className="flex items-center space-x-2">
            <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider whitespace-nowrap">
              Change Clusters ({regions.length}):
            </span>
            {regions.map((reg) => {
              const isSelected = selectedRegionId === reg.region_id;
              return (
                <button
                  key={reg.region_id}
                  onClick={() => {
                    setSelectedRegionId(reg.region_id);
                    setMode("regions");
                  }}
                  className={`flex items-center space-x-1.5 px-2.5 py-1 rounded-md text-xs font-mono transition whitespace-nowrap ${
                    isSelected
                      ? "bg-amber-950 border border-amber-500/80 text-amber-200"
                      : "bg-slate-900 hover:bg-slate-850 border border-slate-800 text-slate-300 hover:text-slate-100"
                  }`}
                >
                  <MapPin className="h-3 w-3 text-amber-400" />
                  <span>{reg.label}</span>
                  <span className="text-[10px] text-slate-500">
                    {reg.pixel_area} px
                  </span>
                </button>
              );
            })}
          </div>

          {/* Selected Region Detailed Meta */}
          {selectedRegion && (
            <div className="mt-2 pt-2 border-t border-slate-800/50 grid grid-cols-2 md:grid-cols-4 gap-2 text-[11px] font-mono text-slate-400">
              <div>
                <span className="text-slate-500">Pixels:</span> [{selectedRegion.pixel_geometry.x1}, {selectedRegion.pixel_geometry.y1}] to [{selectedRegion.pixel_geometry.x2}, {selectedRegion.pixel_geometry.y2}]
              </div>
              <div>
                <span className="text-slate-500">Area:</span> {selectedRegion.pixel_area} px ({(selectedRegion.relative_area * 100).toFixed(2)}%)
              </div>
              <div>
                <span className="text-slate-500">Confidence:</span> {Math.round(selectedRegion.confidence * 100)}%
              </div>
              <div>
                <span className="text-slate-500">Geo CRS:</span> {selectedRegion.geo_geometry?.crs || pair.image_t1.crs || "Pixel Space"}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
