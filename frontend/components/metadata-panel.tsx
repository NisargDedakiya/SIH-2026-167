"use client";

import React from "react";
import { ImageInspect } from "@/lib/types";
import { FileText, Cpu, Globe2, Compass, Layers, Info } from "lucide-react";

interface MetadataPanelProps {
  image: ImageInspect;
}

function formatBytes(bytes: number): string {
  if (bytes === 0) return "0 Bytes";
  const k = 1024;
  const sizes = ["Bytes", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
}

export function MetadataPanel({ image }: MetadataPanelProps) {
  const { raster, geospatial } = image;

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      {/* 1. File Specifications Card */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4 flex flex-col justify-between">
        <div>
          <div className="flex items-center space-x-2 text-cyan-400 mb-3">
            <FileText className="h-4 w-4" />
            <h3 className="text-xs font-semibold uppercase tracking-wider font-mono">
              File Properties
            </h3>
          </div>
          <div className="space-y-2 text-xs">
            <div className="flex justify-between py-1 border-b border-slate-800/60">
              <span className="text-slate-400">Filename:</span>
              <span className="font-mono text-slate-200 truncate max-w-[160px]" title={image.filename}>
                {image.filename}
              </span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-800/60">
              <span className="text-slate-400">Raster Format:</span>
              <span className="font-mono font-medium text-cyan-300">{image.format}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-800/60">
              <span className="text-slate-400">File Size:</span>
              <span className="font-mono text-slate-200">{formatBytes(image.size_bytes)}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-800/60">
              <span className="text-slate-400">Inferred Modality:</span>
              <span className="font-mono capitalize text-slate-200">{image.modality}</span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-slate-400">Internal UUID:</span>
              <span className="font-mono text-[11px] text-slate-400 truncate max-w-[140px]" title={image.id}>
                {image.id}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* 2. Raster Technical Specifications Card */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4 flex flex-col justify-between">
        <div>
          <div className="flex items-center space-x-2 text-teal-400 mb-3">
            <Cpu className="h-4 w-4" />
            <h3 className="text-xs font-semibold uppercase tracking-wider font-mono">
              Raster Characteristics
            </h3>
          </div>
          <div className="space-y-2 text-xs">
            <div className="flex justify-between py-1 border-b border-slate-800/60">
              <span className="text-slate-400">Dimensions:</span>
              <span className="font-mono text-slate-200">
                {raster.width} × {raster.height} px
              </span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-800/60">
              <span className="text-slate-400">Total Pixels:</span>
              <span className="font-mono text-slate-200">
                {(raster.width * raster.height).toLocaleString()}
              </span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-800/60">
              <span className="text-slate-400">Spectral Bands:</span>
              <span className="font-mono text-teal-300 font-medium">{raster.bands} {raster.bands > 1 ? "Channels" : "Channel"}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-800/60">
              <span className="text-slate-400">Data Type:</span>
              <span className="font-mono text-slate-200">{raster.dtype}</span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-slate-400">NoData Value:</span>
              <span className="font-mono text-slate-300">
                {raster.nodata !== null ? raster.nodata : "None Specified"}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* 3. Geospatial Referencing Card */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4 flex flex-col justify-between">
        <div>
          <div className="flex items-center space-x-2 text-amber-400 mb-3">
            <Globe2 className="h-4 w-4" />
            <h3 className="text-xs font-semibold uppercase tracking-wider font-mono">
              Geospatial Projection
            </h3>
          </div>
          <div className="space-y-2 text-xs">
            <div className="flex justify-between py-1 border-b border-slate-800/60">
              <span className="text-slate-400">Georeferenced:</span>
              <span className={`font-mono font-medium ${geospatial.is_geospatial ? "text-emerald-400" : "text-amber-400"}`}>
                {geospatial.is_geospatial ? "True (Referenced)" : "False (Unreferenced)"}
              </span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-800/60">
              <span className="text-slate-400">CRS / Coordinate System:</span>
              <span className="font-mono text-slate-200 truncate max-w-[150px]" title={geospatial.crs || "N/A"}>
                {geospatial.crs || "None"}
              </span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-800/60">
              <span className="text-slate-400">EPSG Code:</span>
              <span className="font-mono text-amber-300 font-medium">
                {geospatial.epsg ? `EPSG:${geospatial.epsg}` : "None"}
              </span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-800/60">
              <span className="text-slate-400">Pixel Resolution (GSD):</span>
              <span className="font-mono text-slate-200">
                {geospatial.resolution
                  ? `${geospatial.resolution.x.toFixed(4)} × ${geospatial.resolution.y.toFixed(4)}`
                  : "N/A"}
              </span>
            </div>
            <div className="py-1">
              <span className="text-slate-400 block mb-0.5">Bounding Box:</span>
              {geospatial.bounds ? (
                <div className="font-mono text-[10px] text-slate-300 bg-slate-950/80 p-1.5 rounded border border-slate-800/80 space-y-0.5">
                  <div className="flex justify-between">
                    <span>West: {geospatial.bounds.left.toFixed(4)}</span>
                    <span>East: {geospatial.bounds.right.toFixed(4)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>South: {geospatial.bounds.bottom.toFixed(4)}</span>
                    <span>North: {geospatial.bounds.top.toFixed(4)}</span>
                  </div>
                </div>
              ) : (
                <span className="font-mono text-slate-500">No spatial coordinates</span>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
