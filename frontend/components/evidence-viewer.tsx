"use client";

import React, { useState } from "react";
import {
  Crosshair,
  Layers,
  MapPin,
  ExternalLink,
  ChevronRight,
  ZoomIn,
  ZoomOut,
  RotateCcw,
  Sparkles,
  Maximize2,
  Minimize2,
  CheckCircle2,
  Eye,
  Columns
} from "lucide-react";
import { EvidenceRecord } from "../lib/types";
import { getEvidenceArtifactUrl } from "../lib/api";

interface EvidenceViewerProps {
  previewUrl: string;
  evidence: EvidenceRecord[];
  query?: string;
  targetExpression?: string;
  confidenceScore?: number;
  confidenceMethod?: string;
  className?: string;
}

export function EvidenceViewer({
  previewUrl,
  evidence,
  query,
  targetExpression,
  confidenceScore,
  confidenceMethod,
  className = "",
}: EvidenceViewerProps) {
  const [selectedRegionId, setSelectedRegionId] = useState<string | null>(
    evidence.length > 0 ? evidence[0].id : null
  );
  const [viewMode, setViewMode] = useState<"interactive" | "overlay" | "original" | "split">("interactive");
  const [zoom, setZoom] = useState<number>(1);
  const [isFullscreen, setIsFullscreen] = useState<boolean>(false);
  const [hoveredRegionId, setHoveredRegionId] = useState<string | null>(null);

  const selectedRegion = evidence.find((e) => e.id === selectedRegionId) || evidence[0] || null;

  const handleZoomIn = () => setZoom((prev) => Math.min(prev + 0.25, 3));
  const handleZoomOut = () => setZoom((prev) => Math.max(prev - 0.25, 0.5));
  const handleResetZoom = () => setZoom(1);

  // Overlay artifact URL (if any region has artifact_key)
  const overlayEvidence = evidence.find((e) => e.artifact_key);
  const overlayUrl = overlayEvidence ? getEvidenceArtifactUrl(overlayEvidence.id, false) : null;

  return (
    <div
      className={`flex flex-col rounded-xl overflow-hidden border border-slate-800 bg-slate-950/90 shadow-2xl transition-all ${
        isFullscreen
          ? "fixed inset-0 z-50 rounded-none bg-slate-950 p-6 flex flex-col"
          : className
      }`}
    >
      {/* Evidence Viewer Header */}
      <div className="flex flex-wrap items-center justify-between gap-2 px-4 py-3 bg-slate-900/90 border-b border-slate-800">
        <div className="flex items-center space-x-2.5">
          <div className="p-1.5 rounded-lg bg-emerald-950/60 border border-emerald-700/60 text-emerald-400">
            <Crosshair className="h-4 w-4" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-xs font-semibold text-slate-200 uppercase tracking-wider">
                Visual Evidence Grounding
              </span>
              <span className="px-2 py-0.5 text-[10px] font-mono rounded-full bg-emerald-950/80 border border-emerald-800/80 text-emerald-300">
                {evidence.length} {evidence.length === 1 ? "Region" : "Regions"} Located
              </span>
            </div>
            {targetExpression && (
              <p className="text-[11px] text-slate-400">
                Target: <span className="text-emerald-300 font-mono">{targetExpression}</span>
              </p>
            )}
          </div>
        </div>

        {/* View Controls & Mode Switcher */}
        <div className="flex items-center space-x-2">
          {/* Mode Switcher */}
          <div className="flex items-center p-0.5 rounded-lg bg-slate-950 border border-slate-800 text-xs font-medium text-slate-300">
            <button
              onClick={() => setViewMode("interactive")}
              className={`px-2.5 py-1 rounded-md transition ${
                viewMode === "interactive"
                  ? "bg-cyan-900/60 text-cyan-300 font-semibold border border-cyan-700/50"
                  : "hover:text-white"
              }`}
              title="Interactive vector overlays over original raster"
            >
              Interactive
            </button>
            {overlayUrl && (
              <button
                onClick={() => setViewMode("overlay")}
                className={`px-2.5 py-1 rounded-md transition ${
                  viewMode === "overlay"
                    ? "bg-emerald-900/60 text-emerald-300 font-semibold border border-emerald-700/50"
                    : "hover:text-white"
                }`}
                title="Pre-rendered server overlay artifact"
              >
                Rendered Overlay
              </button>
            )}
            <button
              onClick={() => setViewMode("original")}
              className={`px-2.5 py-1 rounded-md transition ${
                viewMode === "original"
                  ? "bg-slate-800 text-slate-200 font-semibold"
                  : "hover:text-white"
              }`}
              title="Original raster preview"
            >
              Original
            </button>
          </div>

          {/* Zoom controls */}
          <div className="flex items-center space-x-1 bg-slate-950/80 border border-slate-800 rounded-lg p-1">
            <button
              onClick={handleZoomOut}
              className="p-1.5 rounded hover:bg-slate-800 text-slate-400 hover:text-white transition"
              title="Zoom Out"
            >
              <ZoomOut className="h-3.5 w-3.5" />
            </button>
            <span className="text-[11px] font-mono text-slate-400 px-1">
              {Math.round(zoom * 100)}%
            </span>
            <button
              onClick={handleZoomIn}
              className="p-1.5 rounded hover:bg-slate-800 text-slate-400 hover:text-white transition"
              title="Zoom In"
            >
              <ZoomIn className="h-3.5 w-3.5" />
            </button>
            <button
              onClick={handleResetZoom}
              className="p-1.5 rounded hover:bg-slate-800 text-slate-400 hover:text-white transition"
              title="Reset Zoom"
            >
              <RotateCcw className="h-3 w-3" />
            </button>
            <button
              onClick={() => setIsFullscreen(!isFullscreen)}
              className="p-1.5 rounded hover:bg-slate-800 text-slate-400 hover:text-white transition"
              title={isFullscreen ? "Exit Fullscreen" : "Fullscreen"}
            >
              {isFullscreen ? (
                <Minimize2 className="h-3.5 w-3.5" />
              ) : (
                <Maximize2 className="h-3.5 w-3.5" />
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Main Content Area: Viewport + Region Inspector Sidebar */}
      <div className="flex-1 grid grid-cols-1 lg:grid-cols-12 gap-0 overflow-hidden min-h-[460px]">
        {/* Left / Center Viewport (8 or 7 cols) */}
        <div className="lg:col-span-8 relative bg-slate-950 flex items-center justify-center p-4 overflow-hidden border-b lg:border-b-0 lg:border-r border-slate-800">
          <div
            className="relative transition-transform duration-150 ease-out origin-center inline-block max-w-full max-h-full"
            style={{ transform: `scale(${zoom})` }}
          >
            {/* View Mode 1: Rendered Overlay Image */}
            {viewMode === "overlay" && overlayUrl ? (
              <img
                src={overlayUrl}
                alt="Visual Evidence Overlay"
                className="max-h-[480px] w-auto object-contain rounded-lg border border-slate-800 shadow-lg"
              />
            ) : viewMode === "original" ? (
              /* View Mode 2: Original Raster Image */
              <img
                src={previewUrl}
                alt="Original Remote-Sensing Raster"
                className="max-h-[480px] w-auto object-contain rounded-lg border border-slate-800 shadow-lg"
              />
            ) : (
              /* View Mode 3: Interactive Vector Overlay */
              <div className="relative inline-block">
                <img
                  src={previewUrl}
                  alt="Remote-Sensing Scene"
                  className="max-h-[480px] w-auto object-contain rounded-lg border border-slate-800 shadow-lg block"
                />

                {/* SVG Overlay containing normalized bounding boxes */}
                <svg
                  className="absolute inset-0 w-full h-full pointer-events-auto"
                  viewBox="0 0 1000 1000"
                  preserveAspectRatio="none"
                >
                  {evidence.map((reg, idx) => {
                    const [x1, y1, x2, y2] = reg.geometry;
                    const isSelected = reg.id === selectedRegionId;
                    const isHovered = reg.id === hoveredRegionId;

                    const svgX = x1 * 1000;
                    const svgY = y1 * 1000;
                    const svgW = (x2 - x1) * 1000;
                    const svgH = (y2 - y1) * 1000;

                    return (
                      <g
                        key={reg.id}
                        className="cursor-pointer transition-all duration-200"
                        onClick={() => setSelectedRegionId(reg.id)}
                        onMouseEnter={() => setHoveredRegionId(reg.id)}
                        onMouseLeave={() => setHoveredRegionId(null)}
                      >
                        {/* Semi-transparent filled region */}
                        <rect
                          x={svgX}
                          y={svgY}
                          width={svgW}
                          height={svgH}
                          fill={
                            isSelected
                              ? "rgba(16, 185, 129, 0.28)"
                              : isHovered
                              ? "rgba(6, 182, 212, 0.22)"
                              : "rgba(16, 185, 129, 0.12)"
                          }
                          stroke={isSelected ? "#10b981" : isHovered ? "#06b6d4" : "#059669"}
                          strokeWidth={isSelected ? 4 : isHovered ? 3 : 2}
                          rx={4}
                        />

                        {/* Interactive Pill Label */}
                        <g
                          transform={`translate(${svgX + 4}, ${
                            svgY > 30 ? svgY - 24 : svgY + svgH + 4
                          })`}
                        >
                          <rect
                            x={0}
                            y={0}
                            width={Math.max(120, reg.label.length * 9 + 45)}
                            height={20}
                            rx={4}
                            fill={isSelected ? "#064e3b" : "#0f172a"}
                            stroke={isSelected ? "#10b981" : "#334155"}
                            strokeWidth={1.5}
                          />
                          <text
                            x={8}
                            y={14}
                            fill="#f8fafc"
                            fontSize="11"
                            fontFamily="monospace"
                            fontWeight="600"
                          >
                            #{idx + 1} {reg.label} ({Math.round(reg.confidence * 100)}%)
                          </text>
                        </g>
                      </g>
                    );
                  })}
                </svg>
              </div>
            )}
          </div>

          {/* Quick HUD overlay pill */}
          <div className="absolute bottom-3 left-3 bg-slate-900/90 backdrop-blur border border-slate-800 rounded-lg px-3 py-1.5 flex items-center space-x-2 text-[11px] text-slate-300">
            <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
            <span>Mode: <strong className="text-emerald-300 font-mono capitalize">{viewMode}</strong></span>
            <span className="text-slate-600">|</span>
            <span>Scale: <span className="font-mono text-cyan-300">{Math.round(zoom * 100)}%</span></span>
          </div>
        </div>

        {/* Right Sidebar: Region Cards & Deep Coordinates Inspector (4 cols) */}
        <div className="lg:col-span-4 bg-slate-900/60 flex flex-col h-full overflow-hidden">
          {/* Section 1: Detected Region List */}
          <div className="p-3.5 border-b border-slate-800 bg-slate-900/80">
            <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center justify-between">
              <span>Detected Regions</span>
              <span className="text-[10px] font-normal text-slate-400">Click to inspect</span>
            </h4>
          </div>

          <div className="flex-1 overflow-y-auto p-3 space-y-2.5 max-h-[240px] lg:max-h-none">
            {evidence.map((reg, idx) => {
              const isSelected = reg.id === selectedRegionId;
              const isHovered = reg.id === hoveredRegionId;
              const cropUrl = reg.id ? getEvidenceArtifactUrl(reg.id, true) : null;

              return (
                <div
                  key={reg.id}
                  onClick={() => setSelectedRegionId(reg.id)}
                  onMouseEnter={() => setHoveredRegionId(reg.id)}
                  onMouseLeave={() => setHoveredRegionId(null)}
                  className={`p-3 rounded-lg border cursor-pointer transition-all ${
                    isSelected
                      ? "bg-emerald-950/40 border-emerald-600 shadow-md shadow-emerald-950/50"
                      : isHovered
                      ? "bg-slate-800/80 border-cyan-700"
                      : "bg-slate-950/60 border-slate-800 hover:border-slate-700"
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex items-center space-x-2">
                      <span
                        className={`flex items-center justify-center h-5 w-5 rounded text-[11px] font-mono font-bold ${
                          isSelected
                            ? "bg-emerald-500 text-slate-950"
                            : "bg-slate-800 text-slate-300"
                        }`}
                      >
                        {idx + 1}
                      </span>
                      <span className="text-xs font-medium text-slate-200 capitalize">
                        {reg.label}
                      </span>
                    </div>

                    {/* Confidence Pill */}
                    <span
                      className={`px-2 py-0.5 text-[10px] font-mono font-semibold rounded-full border ${
                        reg.confidence >= 0.85
                          ? "bg-emerald-950/70 border-emerald-700 text-emerald-300"
                          : "bg-amber-950/70 border-amber-700 text-amber-300"
                      }`}
                    >
                      {Math.round(reg.confidence * 100)}%
                    </span>
                  </div>

                  {/* Pixel Coordinates summary */}
                  <div className="mt-2 text-[11px] font-mono text-slate-400 grid grid-cols-2 gap-1 bg-slate-900/90 rounded p-1.5 border border-slate-800/70">
                    <div>
                      <span className="text-slate-500">Box: </span>
                      [{reg.pixel_geometry.x1}, {reg.pixel_geometry.y1}]
                    </div>
                    <div>
                      <span className="text-slate-500">Dim: </span>
                      {reg.pixel_geometry.width}x{reg.pixel_geometry.height}px
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Section 2: Selected Region Detailed Inspector */}
          {selectedRegion && (
            <div className="p-3.5 bg-slate-950 border-t border-slate-800 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-emerald-400 flex items-center space-x-1.5">
                  <MapPin className="h-3.5 w-3.5" />
                  <span>Geospatial & Coordinate Details</span>
                </span>
                <span className="text-[10px] font-mono text-slate-400">
                  ID: {selectedRegion.id.slice(0, 8)}...
                </span>
              </div>

              {/* Native CRS Bounds */}
              <div className="p-2 rounded bg-slate-900/90 border border-slate-800 text-[11px] font-mono space-y-1">
                <div className="text-slate-400 flex justify-between">
                  <span>CRS:</span>
                  <span className="text-cyan-300 font-semibold">
                    {selectedRegion.geo_geometry?.crs || "Non-georeferenced (Pixel Space)"}
                  </span>
                </div>
                {selectedRegion.geo_geometry?.bounds ? (
                  <div className="text-slate-300 pt-1 border-t border-slate-800/80 space-y-0.5">
                    <div>
                      X: [{selectedRegion.geo_geometry.bounds.min_x.toFixed(2)}, {selectedRegion.geo_geometry.bounds.max_x.toFixed(2)}]
                    </div>
                    <div>
                      Y: [{selectedRegion.geo_geometry.bounds.min_y.toFixed(2)}, {selectedRegion.geo_geometry.bounds.max_y.toFixed(2)}]
                    </div>
                  </div>
                ) : (
                  <div className="text-slate-500 text-[10px] italic">
                    Raw raster pixel coordinate bounds
                  </div>
                )}
              </div>

              {/* Region Crop Thumbnail & Artifact Link */}
              <div className="flex items-center justify-between gap-2 pt-1">
                <div className="flex items-center space-x-2">
                  <div className="h-10 w-10 rounded border border-slate-800 bg-slate-900 overflow-hidden flex items-center justify-center shrink-0">
                    <img
                      src={getEvidenceArtifactUrl(selectedRegion.id, true)}
                      alt="Crop thumbnail"
                      className="h-full w-full object-cover"
                      onError={(e) => {
                        (e.target as HTMLElement).style.display = "none";
                      }}
                    />
                  </div>
                  <div className="text-[11px]">
                    <div className="text-slate-300 font-medium capitalize">
                      {selectedRegion.label} Crop
                    </div>
                    <div className="text-slate-500 font-mono text-[10px]">
                      {selectedRegion.pixel_geometry.width}x{selectedRegion.pixel_geometry.height}px
                    </div>
                  </div>
                </div>

                <a
                  href={getEvidenceArtifactUrl(selectedRegion.id, true)}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="px-2.5 py-1.5 rounded text-[11px] font-medium bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-300 hover:text-white flex items-center space-x-1 transition"
                  title="Open high-res crop in new tab"
                >
                  <span>Crop</span>
                  <ExternalLink className="h-3 w-3" />
                </a>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
