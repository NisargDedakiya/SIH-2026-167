"use client";

import React, { useState } from "react";
import { ZoomIn, ZoomOut, RotateCcw, Maximize2, Minimize2, Eye } from "lucide-react";

interface ImagePreviewProps {
  previewUrl: string;
  filename: string;
  width?: number;
  height?: number;
  format?: string;
}

export function ImagePreview({
  previewUrl,
  filename,
  width,
  height,
  format
}: ImagePreviewProps) {
  const [zoom, setZoom] = useState<number>(1);
  const [isFullscreen, setIsFullscreen] = useState<boolean>(false);

  const handleZoomIn = () => setZoom((prev) => Math.min(prev + 0.25, 4));
  const handleZoomOut = () => setZoom((prev) => Math.max(prev - 0.25, 0.5));
  const handleReset = () => setZoom(1);

  return (
    <div
      className={`relative flex flex-col rounded-xl overflow-hidden border border-slate-800 bg-slate-950/80 transition-all ${
        isFullscreen
          ? "fixed inset-0 z-50 rounded-none bg-slate-950 p-6"
          : "w-full h-[480px] sm:h-[540px]"
      }`}
    >
      {/* Viewer Header */}
      <div className="flex items-center justify-between px-4 py-2.5 bg-slate-900/90 border-b border-slate-800 z-10">
        <div className="flex items-center space-x-2 truncate">
          <Eye className="h-4 w-4 text-cyan-400 shrink-0" />
          <span className="text-xs font-mono font-medium text-slate-200 truncate">
            {filename}
          </span>
          {format && (
            <span className="px-2 py-0.5 text-[10px] font-mono rounded bg-cyan-950/60 border border-cyan-800/60 text-cyan-300">
              {format}
            </span>
          )}
        </div>

        {/* Floating Zoom Controls */}
        <div className="flex items-center space-x-1.5 bg-slate-950/80 border border-slate-800 rounded-lg p-1">
          <button
            onClick={handleZoomOut}
            className="p-1.5 rounded hover:bg-slate-800 text-slate-300 hover:text-white transition"
            title="Zoom Out"
            aria-label="Zoom Out"
          >
            <ZoomOut className="h-3.5 w-3.5" />
          </button>
          <span className="text-[11px] font-mono text-slate-400 px-1.5">
            {Math.round(zoom * 100)}%
          </span>
          <button
            onClick={handleZoomIn}
            className="p-1.5 rounded hover:bg-slate-800 text-slate-300 hover:text-white transition"
            title="Zoom In"
            aria-label="Zoom In"
          >
            <ZoomIn className="h-3.5 w-3.5" />
          </button>
          <div className="h-3 w-[1px] bg-slate-800" />
          <button
            onClick={handleReset}
            className="p-1.5 rounded hover:bg-slate-800 text-slate-300 hover:text-white transition"
            title="Reset Zoom"
            aria-label="Reset Zoom"
          >
            <RotateCcw className="h-3.5 w-3.5" />
          </button>
          <button
            onClick={() => setIsFullscreen(!isFullscreen)}
            className="p-1.5 rounded hover:bg-slate-800 text-slate-300 hover:text-white transition"
            title={isFullscreen ? "Exit Fullscreen" : "Fullscreen"}
            aria-label="Toggle Fullscreen"
          >
            {isFullscreen ? (
              <Minimize2 className="h-3.5 w-3.5" />
            ) : (
              <Maximize2 className="h-3.5 w-3.5" />
            )}
          </button>
        </div>
      </div>

      {/* Interactive Raster Viewport */}
      <div className="relative flex-1 overflow-auto flex items-center justify-center p-4 select-none space-grid bg-slate-950">
        <div
          className="transition-transform duration-150 ease-out origin-center"
          style={{ transform: `scale(${zoom})` }}
        >
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={previewUrl}
            alt={filename}
            className="max-h-[440px] w-auto object-contain rounded-md shadow-2xl shadow-cyan-950/30 border border-slate-800/80"
          />
        </div>
      </div>

      {/* Footer Info Badge */}
      <div className="px-4 py-2 bg-slate-900/80 border-t border-slate-800/80 flex items-center justify-between text-[11px] text-slate-400 font-mono">
        <span>Rendered via 2%-98% Percentile Normalization</span>
        {width && height && (
          <span>
            Dimensions: {width} × {height} px
          </span>
        )}
      </div>
    </div>
  );
}
