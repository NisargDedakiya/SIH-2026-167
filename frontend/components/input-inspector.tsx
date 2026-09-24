"use client";

import React from "react";
import { ImageInspect } from "@/lib/types";
import { Layers, Globe, Calendar, Eye, ShieldCheck, AlertTriangle } from "lucide-react";

interface InputInspectorProps {
  image?: any;
  images?: any[];
  role?: string; // "primary", "t1_before", "t2_after", "optical", "sar"
  onRemove?: () => void;
}

function SingleImageCard({ image, role = "primary", onRemove }: { image: any; role?: string; onRemove?: () => void }) {
  const roleLabel =
    role === "t1_before"
      ? "T1 Before Epoch"
      : role === "t2_after"
      ? "T2 After Epoch"
      : role === "optical"
      ? "Optical Source"
      : role === "sar"
      ? "SAR Microwave Source"
      : "Primary Input";

  const isGeo = image.is_geospatial || !!image.geospatial?.crs || !!image.crs;
  const filename = image.filename || image.original_filename || "satellite_scene.tif";
  const modality = (image.modality || image.sensor_type || "optical").toUpperCase();
  const sensor = image.metadata?.sensor || image.sensor;
  
  const width = image.raster?.width ?? image.width ?? (Array.isArray(image.dimensions) ? image.dimensions[0] : 512);
  const height = image.raster?.height ?? image.height ?? (Array.isArray(image.dimensions) ? image.dimensions[1] : 512);
  const bands = image.raster?.bands ?? image.channels ?? image.bands ?? 3;
  const crs = image.geospatial?.crs ? (image.geospatial.epsg ? `EPSG:${image.geospatial.epsg}` : image.geospatial.crs) : image.crs || "Pixel Frame";
  const gsd = image.geospatial?.resolution_x ?? image.gsd_meters;

  return (
    <div className="p-4 rounded-xl bg-slate-900/70 border border-slate-800 shadow-sm space-y-3 relative group">
      {onRemove && (
        <button
          onClick={onRemove}
          className="absolute top-3 right-3 text-slate-500 hover:text-rose-400 text-xs px-2 py-0.5 rounded bg-slate-800/80 transition"
          title="Remove from analysis"
        >
          ✕
        </button>
      )}

      {/* Role Badge & Filename */}
      <div className="flex items-start justify-between pr-8">
        <div>
          <span className="px-2 py-0.5 rounded text-[10px] font-mono uppercase tracking-wider font-semibold bg-cyan-950 text-cyan-300 border border-cyan-800/60">
            {roleLabel}
          </span>
          <h4 className="font-semibold text-sm text-white mt-1.5 truncate max-w-xs" title={filename}>
            {filename}
          </h4>
        </div>
      </div>

      {/* Technical Spec Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-1 text-xs">
        <div className="p-2 rounded-lg bg-slate-950/60 border border-slate-800/80">
          <span className="text-[10px] text-slate-500 uppercase font-mono block">Modality / Sensor</span>
          <span className="font-medium text-slate-200 truncate block">
            {modality} {sensor ? `· ${sensor}` : ""}
          </span>
        </div>

        <div className="p-2 rounded-lg bg-slate-950/60 border border-slate-800/80">
          <span className="text-[10px] text-slate-500 uppercase font-mono block">Dimensions</span>
          <span className="font-medium text-slate-200 block font-mono">
            {width} × {height} ({bands}b)
          </span>
        </div>

        <div className="p-2 rounded-lg bg-slate-950/60 border border-slate-800/80">
          <span className="text-[10px] text-slate-500 uppercase font-mono block">Projection / CRS</span>
          <span className="font-medium text-slate-200 truncate block font-mono">
            {crs}
          </span>
        </div>

        <div className="p-2 rounded-lg bg-slate-950/60 border border-slate-800/80">
          <span className="text-[10px] text-slate-500 uppercase font-mono block">Resolution (GSD)</span>
          <span className="font-medium text-slate-200 block font-mono">
            {gsd ? `${Number(gsd).toFixed(2)} m/px` : "10.0 m (nom.)"}
          </span>
        </div>
      </div>

      {/* Verification Status Pill */}
      <div className="flex items-center justify-between text-[11px] pt-1">
        <div className="flex items-center space-x-1.5">
          {isGeo ? (
            <span className="text-emerald-400 flex items-center space-x-1 font-mono">
              <ShieldCheck className="h-3.5 w-3.5" />
              <span>Georeferenced</span>
            </span>
          ) : (
            <span className="text-amber-400/90 flex items-center space-x-1 font-mono">
              <AlertTriangle className="h-3.5 w-3.5" />
              <span>Standard Pixel Frame</span>
            </span>
          )}
        </div>
        <span className="text-slate-500 font-mono text-[10px]">
          {image.format || "GeoTIFF"} {image.size ? `· ${(image.size / (1024 * 1024)).toFixed(2)} MB` : ""}
        </span>
      </div>
    </div>
  );
}

export function InputInspector({ image, images, role = "primary", onRemove }: InputInspectorProps) {
  if (images && images.length > 0) {
    return (
      <div className="space-y-3">
        {images.map((img, idx) => (
          <SingleImageCard
            key={img.id || img.image_id || idx}
            image={img}
            role={img.role || (idx === 0 ? "primary" : idx === 1 ? "secondary" : "input")}
            onRemove={onRemove}
          />
        ))}
      </div>
    );
  }

  if (!image) return null;
  return <SingleImageCard image={image} role={role} onRemove={onRemove} />;
}
