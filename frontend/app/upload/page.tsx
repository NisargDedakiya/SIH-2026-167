"use client";

import React from "react";
import Link from "next/link";
import { ImageUploader } from "@/components/image-uploader";
import { ArrowLeft, Layers, ShieldCheck } from "lucide-react";

export default function UploadPage() {
  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div className="flex items-center space-x-2">
        <Link
          href="/"
          className="text-xs text-slate-400 hover:text-slate-200 flex items-center space-x-1 transition"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          <span>Back to Dashboard</span>
        </Link>
      </div>

      <div>
        <h1 className="text-2xl font-bold text-white tracking-tight">
          Ingestion & Geospatial Validation Hub
        </h1>
        <p className="text-xs text-slate-400 mt-1">
          Upload multi-band GeoTIFF, standard TIFF, or standard satellite snapshots for automated verification.
        </p>
      </div>

      <ImageUploader />

      <div className="p-4 rounded-xl bg-slate-900/40 border border-slate-800 text-xs text-slate-400 space-y-2">
        <div className="flex items-center space-x-2 text-cyan-400 font-semibold font-mono">
          <ShieldCheck className="h-4 w-4" />
          <span>Ingestion Standards & Protocol</span>
        </div>
        <p>
          • <strong>GeoTIFF (.tif, .tiff)</strong>: Automatically checks CRS, EPSG projections, affine transform, and bounding coordinates.
        </p>
        <p>
          • <strong>Standard TIFF</strong>: Verified for dimensional and band integrity; flagged with non-geospatial warning if projection tags are missing.
        </p>
        <p>
          • <strong>PNG / JPEG</strong>: Parsed as benchmark unreferenced visual rasters.
        </p>
        <p>
          • <strong>Memory Safety</strong>: Decimated windowed reading protects system RAM against gigabyte raster overload.
        </p>
      </div>
    </div>
  );
}
