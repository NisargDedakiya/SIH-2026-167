"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  Layers,
  UploadCloud,
  Search,
  ArrowRight,
  RefreshCw,
  AlertCircle,
  AlertTriangle,
  Sparkles,
  Grid3X3,
  List,
  X,
  ScanSearch,
  MapPin,
  Maximize2,
} from "lucide-react";
import { listImages, getImagePreviewUrl } from "@/lib/api";
import { ImageInspect } from "@/lib/types";
import { ImageUploader } from "@/components/image-uploader";

// ── Raster Preview ────────────────────────────────────────────
function RasterPreview({ imageId, filename, className = "" }: { imageId: string; filename: string; className?: string }) {
  const [status, setStatus] = useState<"loading" | "ok" | "error">("loading");
  const [retryNonce, setRetryNonce] = useState<number>(0);
  const previewUrl = `${getImagePreviewUrl(imageId)}${retryNonce > 0 ? `?retry=${retryNonce}` : ""}`;

  return (
    <div className={`relative bg-[#0A0E17] overflow-hidden flex items-center justify-center ${className}`}>
      {status === "loading" && (
        <div className="absolute inset-0 flex items-center justify-center z-10 bg-[#0A0E17]">
          <RefreshCw className="w-4 h-4 text-[#1C2535] animate-spin" />
        </div>
      )}
      {status === "error" ? (
        <div className="p-3 text-center space-y-2 z-10">
          <AlertTriangle className="w-5 h-5 text-amber-400/50 mx-auto" />
          <p className="text-[9px] font-mono text-[#49576A]">Preview unavailable</p>
          <button
            type="button"
            onClick={(e) => { e.preventDefault(); e.stopPropagation(); setStatus("loading"); setRetryNonce((n) => n + 1); }}
            className="text-[9px] text-cyan-500 hover:text-cyan-400 font-mono"
          >
            Retry
          </button>
        </div>
      ) : (
        <img
          key={previewUrl}
          src={previewUrl}
          alt={filename}
          className={`w-full h-full object-cover transition-all duration-500 group-hover:scale-105 ${status === "ok" ? "opacity-100" : "opacity-0"}`}
          onLoad={() => setStatus("ok")}
          onError={() => setStatus("error")}
        />
      )}
    </div>
  );
}

// ── Image Card (grid) ─────────────────────────────────────────
function ImageCard({ img }: { img: ImageInspect }) {
  const width = img.raster?.width ?? img.width;
  const height = img.raster?.height ?? img.height;
  const bands = img.raster?.bands ?? img.channels;
  const epsg = img.geospatial?.epsg;
  const crs = epsg ? `EPSG:${epsg}` : (img.geospatial?.crs || img.crs || "Unprojected");
  const resX = img.geospatial?.resolution?.x;
  const gsd = resX != null ? `${Number(resX).toFixed(2)}m` : null;
  const modality = (img.modality || "optical").toUpperCase();
  const format = img.format?.toUpperCase() || "IMG";
  const isGeo = img.geospatial?.is_geospatial;

  return (
    <div className="group rounded-xl bg-[#111821] border border-[#1C2535] hover:border-[#25303D] transition-all overflow-hidden flex flex-col">
      {/* Thumbnail */}
      <div className="relative">
        <RasterPreview imageId={img.id} filename={img.filename} className="aspect-[4/3]" />
        {/* Overlays */}
        <div className="absolute top-2 left-2 flex items-center gap-1">
          <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-black/75 text-cyan-300 border border-cyan-800/40">
            {format}
          </span>
          <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-black/75 text-[#A7B0BD] border border-[#25303D]">
            {modality}
          </span>
        </div>
        {isGeo && (
          <div className="absolute top-2 right-2">
            <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-emerald-900/80 text-emerald-300 border border-emerald-700/40 flex items-center gap-1">
              <MapPin className="w-2.5 h-2.5" />
              GEO
            </span>
          </div>
        )}
        {/* Hover overlay */}
        <div className="absolute inset-0 bg-black/0 group-hover:bg-black/40 transition-colors flex items-center justify-center opacity-0 group-hover:opacity-100">
          <div className="flex items-center gap-2">
            <Link
              href={`/images/${img.id}`}
              className="w-8 h-8 rounded-lg bg-[#111821]/90 border border-[#25303D] flex items-center justify-center text-[#A7B0BD] hover:text-white transition"
              onClick={(e) => e.stopPropagation()}
              title="View metadata"
            >
              <ScanSearch className="w-3.5 h-3.5" />
            </Link>
            <Link
              href={`/analyze?image_id=${img.id}`}
              className="px-3 py-1.5 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-[10px] font-bold text-slate-900 transition"
              onClick={(e) => e.stopPropagation()}
            >
              Analyze
            </Link>
          </div>
        </div>
      </div>

      {/* Metadata */}
      <div className="p-3 space-y-2 flex-1 flex flex-col">
        <p className="text-[11px] font-medium text-white truncate" title={img.filename}>
          {img.filename}
        </p>

        {width && height ? (
          <div className="grid grid-cols-2 gap-x-3 gap-y-0.5">
            {[
              ["Dimensions", `${width}×${height}`],
              ["Bands", bands ?? "—"],
              ["CRS", crs.length > 14 ? crs.slice(0, 14) + "…" : crs],
              ["GSD", gsd ?? "—"],
            ].map(([k, v]) => (
              <div key={String(k)} className="flex flex-col">
                <span className="text-[8px] text-[#303B49] font-mono uppercase">{k}</span>
                <span className="text-[10px] text-[#A7B0BD] font-mono">{v}</span>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-[9px] font-mono text-amber-500/60">Metadata unavailable</p>
        )}

        <div className="flex items-center gap-2 pt-1 mt-auto border-t border-[#1C2535]">
          <Link
            href={`/images/${img.id}`}
            className="text-[10px] text-[#687381] hover:text-[#A7B0BD] transition flex items-center gap-1"
          >
            <ScanSearch className="w-3 h-3" />
            Inspect
          </Link>
          <Link
            href={`/analyze?image_id=${img.id}`}
            className="ml-auto flex items-center gap-1 px-2.5 py-1 rounded-md bg-cyan-500/10 border border-cyan-500/20 text-[10px] font-semibold text-cyan-400 hover:bg-cyan-500/15 hover:text-cyan-300 transition"
          >
            Analyze
            <ArrowRight className="w-2.5 h-2.5" />
          </Link>
        </div>
      </div>
    </div>
  );
}

// ── Image List Row ────────────────────────────────────────────
function ImageRow({ img }: { img: ImageInspect }) {
  const width = img.raster?.width ?? img.width;
  const height = img.raster?.height ?? img.height;
  const bands = img.raster?.bands ?? img.channels;
  const epsg = img.geospatial?.epsg;
  const crs = epsg ? `EPSG:${epsg}` : (img.geospatial?.crs || img.crs || "—");
  const resX = img.geospatial?.resolution?.x;
  const gsd = resX != null ? `${Number(resX).toFixed(2)}m` : "—";
  const modality = (img.modality || "optical").toUpperCase();

  return (
    <div className="flex items-center gap-3 px-4 py-2.5 border-b border-[#1C2535] last:border-0 hover:bg-[#111821]/60 group transition-colors">
      {/* Mini thumbnail */}
      <div className="w-14 h-10 rounded-md overflow-hidden flex-shrink-0 bg-[#0A0E17] border border-[#1C2535]">
        <RasterPreview imageId={img.id} filename={img.filename} className="w-full h-full" />
      </div>

      {/* Filename + format */}
      <div className="flex-1 min-w-0">
        <p className="text-[11px] font-medium text-white truncate">{img.filename}</p>
        <div className="flex items-center gap-2 mt-0.5">
          <span className="text-[9px] font-mono text-[#49576A]">{modality}</span>
          <span className="text-[9px] font-mono text-[#303B49]">{img.format?.toUpperCase()}</span>
        </div>
      </div>

      {/* Dimensions */}
      <div className="hidden md:flex flex-col min-w-[80px]">
        <span className="text-[9px] font-mono text-[#303B49] uppercase">Dimensions</span>
        <span className="text-[10px] font-mono text-[#A7B0BD]">{width ?? "—"}×{height ?? "—"}</span>
      </div>

      {/* Bands */}
      <div className="hidden lg:flex flex-col min-w-[40px]">
        <span className="text-[9px] font-mono text-[#303B49] uppercase">Bands</span>
        <span className="text-[10px] font-mono text-[#A7B0BD]">{bands ?? "—"}</span>
      </div>

      {/* CRS */}
      <div className="hidden lg:flex flex-col min-w-[110px]">
        <span className="text-[9px] font-mono text-[#303B49] uppercase">CRS</span>
        <span className="text-[10px] font-mono text-[#A7B0BD] truncate">{crs}</span>
      </div>

      {/* GSD */}
      <div className="hidden xl:flex flex-col min-w-[50px]">
        <span className="text-[9px] font-mono text-[#303B49] uppercase">GSD</span>
        <span className="text-[10px] font-mono text-[#A7B0BD]">{gsd}</span>
      </div>

      {/* Actions */}
      <div className="flex items-center gap-1.5 flex-shrink-0 opacity-0 group-hover:opacity-100 transition-opacity">
        <Link href={`/images/${img.id}`} className="sq-btn sq-btn-ghost text-[9px] py-1 px-2">
          <ScanSearch className="w-3 h-3" />
          Inspect
        </Link>
        <Link href={`/analyze?image_id=${img.id}`} className="sq-btn sq-btn-primary text-[9px] py-1 px-2">
          <Sparkles className="w-3 h-3" />
          Analyze
        </Link>
      </div>
    </div>
  );
}

// ── Main Page ─────────────────────────────────────────────────
export default function ImagesCatalogPage() {
  const [images, setImages] = useState<ImageInspect[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [filterType, setFilterType] = useState<string>("");
  const [showUpload, setShowUpload] = useState<boolean>(false);
  const [viewMode, setViewMode] = useState<"grid" | "list">("grid");

  const fetchImages = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await listImages(100);
      setImages(data || []);
    } catch (err: any) {
      setError(err?.message || "Failed to load satellite image catalog");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchImages(); }, []);

  const filteredImages = images.filter((img) => {
    const epsg = img.geospatial?.epsg;
    const crs = epsg ? `EPSG:${epsg}` : (img.geospatial?.crs || "");
    const modality = img.modality || "";
    const matchesSearch =
      img.filename.toLowerCase().includes(searchQuery.toLowerCase()) ||
      modality.toLowerCase().includes(searchQuery.toLowerCase()) ||
      crs.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesType = !filterType || img.format?.toLowerCase() === filterType.toLowerCase();
    return matchesSearch && matchesType;
  });

  return (
    <div className="space-y-5 pb-12">

      {/* ── Header ── */}
      <div className="flex items-center justify-between">
        <div>
          <span className="sq-section-label">Geospatial Data Lake</span>
          <h1 className="text-xl font-bold text-white tracking-tight mt-0.5">Satellite Image Catalog</h1>
          <p className="text-[11px] text-[#687381] mt-0.5">
            Browse, inspect, and analyze ingested multispectral, SAR, and high-resolution rasters.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => setShowUpload(!showUpload)}
            className="sq-btn sq-btn-secondary text-[11px]"
          >
            <UploadCloud className="w-3.5 h-3.5 text-cyan-400" />
            {showUpload ? "Hide Upload" : "Upload Image"}
          </button>
          <Link href="/analyze" className="sq-btn sq-btn-primary text-[11px]">
            <Sparkles className="w-3.5 h-3.5" />
            Analyze
          </Link>
        </div>
      </div>

      {/* Upload panel */}
      {showUpload && (
        <div className="rounded-xl bg-[#111821] border border-[#1C2535] overflow-hidden sq-animate-in">
          <div className="flex items-center justify-between px-4 py-2.5 border-b border-[#1C2535]">
            <h2 className="text-[11px] font-semibold text-white uppercase tracking-wider">
              Ingest New Raster
            </h2>
            <button onClick={() => setShowUpload(false)} className="text-[#49576A] hover:text-white transition">
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
          <div className="p-4">
            <ImageUploader onUploadComplete={() => { fetchImages(); setShowUpload(false); }} />
          </div>
        </div>
      )}

      {/* ── Filters + View Toggle ── */}
      <div className="flex flex-col sm:flex-row gap-2">
        {/* Search */}
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-[#303B49]" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search by filename, sensor, or CRS…"
            className="
              w-full pl-9 pr-4 py-2 rounded-lg text-[12px]
              bg-[#111821] border border-[#1C2535] text-white
              placeholder-[#303B49]
              focus:outline-none focus:border-[#06B6D4]/50
              hover:border-[#25303D] transition
            "
          />
        </div>

        {/* Format filter */}
        <select
          value={filterType}
          onChange={(e) => setFilterType(e.target.value)}
          className="
            px-3 py-2 rounded-lg text-[11px] font-mono
            bg-[#111821] border border-[#1C2535] text-[#A7B0BD]
            focus:outline-none focus:border-[#06B6D4]/50 transition
          "
        >
          <option value="">All Formats</option>
          <option value="geotiff">GeoTIFF</option>
          <option value="tiff">TIFF</option>
          <option value="png">PNG</option>
          <option value="jpeg">JPEG</option>
        </select>

        {/* View toggle */}
        <div className="flex items-center bg-[#0D1320] border border-[#1C2535] rounded-lg p-0.5">
          <button
            type="button"
            onClick={() => setViewMode("grid")}
            className={`p-1.5 rounded-md transition ${viewMode === "grid" ? "bg-[#1C2535] text-white" : "text-[#49576A] hover:text-[#A7B0BD]"}`}
            aria-label="Grid view"
          >
            <Grid3X3 className="w-3.5 h-3.5" />
          </button>
          <button
            type="button"
            onClick={() => setViewMode("list")}
            className={`p-1.5 rounded-md transition ${viewMode === "list" ? "bg-[#1C2535] text-white" : "text-[#49576A] hover:text-[#A7B0BD]"}`}
            aria-label="List view"
          >
            <List className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* Count */}
        {!loading && (
          <div className="flex items-center px-3 text-[10px] font-mono text-[#49576A]">
            {filteredImages.length}/{images.length} images
          </div>
        )}
      </div>

      {/* ── Content ── */}
      {loading ? (
        viewMode === "grid" ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {[0, 1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="rounded-xl bg-[#111821] border border-[#1C2535] overflow-hidden">
                <div className="aspect-[4/3] sq-skeleton" />
                <div className="p-3 space-y-2">
                  <div className="h-3 sq-skeleton rounded w-3/4" />
                  <div className="h-2 sq-skeleton rounded w-1/2" />
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="rounded-xl bg-[#111821] border border-[#1C2535] overflow-hidden">
            {[0, 1, 2, 3, 4].map((i) => (
              <div key={i} className="flex items-center gap-3 px-4 py-2.5 border-b border-[#1C2535]">
                <div className="w-14 h-10 rounded-md sq-skeleton flex-shrink-0" />
                <div className="flex-1 space-y-1">
                  <div className="h-3 sq-skeleton rounded w-1/2" />
                  <div className="h-2 sq-skeleton rounded w-1/4" />
                </div>
              </div>
            ))}
          </div>
        )
      ) : error ? (
        <div className="flex items-center gap-3 p-4 rounded-xl bg-rose-500/05 border border-rose-500/20 text-xs text-rose-300">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>Error loading catalog: {error}</span>
          <button onClick={fetchImages} className="ml-auto sq-btn sq-btn-ghost text-[10px] py-1">Retry</button>
        </div>
      ) : filteredImages.length === 0 ? (
        <div className="flex flex-col items-center justify-center gap-4 py-16 rounded-xl border border-[#1C2535] border-dashed">
          <div className="w-12 h-12 rounded-full bg-[#111821] border border-[#25303D] flex items-center justify-center">
            <Layers className="w-5 h-5 text-[#303B49]" />
          </div>
          <div className="text-center space-y-1">
            <p className="text-sm font-semibold text-white">No Images Found</p>
            <p className="text-xs text-[#687381] max-w-xs">
              {searchQuery || filterType
                ? "No images match your search criteria."
                : "No satellite images have been ingested yet."}
            </p>
          </div>
          <button type="button" onClick={() => setShowUpload(true)} className="sq-btn sq-btn-primary">
            <UploadCloud className="w-3.5 h-3.5" />
            Upload Satellite Image
          </button>
        </div>
      ) : viewMode === "grid" ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 sq-stagger">
          {filteredImages.map((img) => <ImageCard key={img.id} img={img} />)}
        </div>
      ) : (
        <div className="rounded-xl bg-[#111821] border border-[#1C2535] overflow-hidden">
          {/* List header */}
          <div className="hidden lg:flex items-center gap-3 px-4 py-2 border-b border-[#1C2535] bg-[#0D1320]">
            <div className="w-14 flex-shrink-0" />
            <span className="flex-1 text-[9px] font-mono text-[#303B49] uppercase">Filename</span>
            <span className="w-[80px] text-[9px] font-mono text-[#303B49] uppercase">Dimensions</span>
            <span className="w-[40px] text-[9px] font-mono text-[#303B49] uppercase">Bands</span>
            <span className="w-[110px] text-[9px] font-mono text-[#303B49] uppercase">CRS</span>
            <span className="w-[50px] text-[9px] font-mono text-[#303B49] uppercase">GSD</span>
            <div className="w-24" />
          </div>
          {filteredImages.map((img) => <ImageRow key={img.id} img={img} />)}
        </div>
      )}
    </div>
  );
}
