"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  Layers,
  UploadCloud,
  Search,
  ArrowRight,
  ExternalLink,
  RefreshCw,
  AlertCircle,
  Sparkles,
  MapPin,
  Calendar,
  Grid,
} from "lucide-react";
import { listImages, getImagePreviewUrl } from "@/lib/api";
import { ImageInspect } from "@/lib/types";
import { ImageUploader } from "@/components/image-uploader";

export default function ImagesCatalogPage() {
  const [images, setImages] = useState<ImageInspect[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [filterType, setFilterType] = useState<string>("");
  const [showUpload, setShowUpload] = useState<boolean>(false);

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

  useEffect(() => {
    fetchImages();
  }, []);

  const filteredImages = images.filter((img) => {
    const matchesSearch =
      img.filename.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (img.sensor_type && img.sensor_type.toLowerCase().includes(searchQuery.toLowerCase())) ||
      (img.crs && img.crs.toLowerCase().includes(searchQuery.toLowerCase()));

    const matchesType = !filterType || img.format.toLowerCase() === filterType.toLowerCase();

    return matchesSearch && matchesType;
  });

  return (
    <div className="space-y-8 pb-16">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-6">
        <div>
          <div className="flex items-center space-x-2 text-xs font-mono text-cyan-400 mb-1">
            <Layers className="h-3.5 w-3.5" />
            <span>Geospatial Data Lake</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-black text-white tracking-tight">
            Satellite Image Catalog
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 mt-1">
            Browse, inspect, and analyze ingested multispectral, SAR, and high-resolution Earth observation rasters.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            type="button"
            onClick={() => setShowUpload(!showUpload)}
            className="inline-flex items-center space-x-1.5 px-4 py-2.5 rounded-xl bg-slate-900 border border-slate-700 hover:border-slate-600 text-xs font-medium text-slate-200 transition"
          >
            <UploadCloud className="h-4 w-4 text-cyan-400" />
            <span>{showUpload ? "Hide Ingestion Hub" : "Upload Image"}</span>
          </button>

          <Link
            href="/analyze"
            className="inline-flex items-center space-x-1.5 px-4 py-2.5 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-slate-950 font-bold text-xs transition"
          >
            <Sparkles className="h-3.5 w-3.5" />
            <span>Analysis Workspace</span>
          </Link>
        </div>
      </div>

      {/* Expandable Upload Hub */}
      {showUpload && (
        <div className="p-6 rounded-2xl bg-surface/80 border border-slate-800 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-bold text-white uppercase tracking-wider">
              Ingest New Geospatial Raster
            </h2>
            <button
              onClick={() => setShowUpload(false)}
              className="text-xs text-slate-400 hover:text-white"
            >
              Close
            </button>
          </div>
          <ImageUploader onUploadComplete={() => { fetchImages(); setShowUpload(false); }} />
        </div>
      )}

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3.5 top-3 h-4 w-4 text-slate-500" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search by filename, sensor, or coordinate system..."
            className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500"
          />
        </div>

        <select
          value={filterType}
          onChange={(e) => setFilterType(e.target.value)}
          className="px-3 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-xs text-slate-300 focus:outline-none focus:border-cyan-500"
        >
          <option value="">All Formats</option>
          <option value="geotiff">GeoTIFF</option>
          <option value="tiff">Standard TIFF</option>
          <option value="png">PNG</option>
          <option value="jpeg">JPEG</option>
        </select>
      </div>

      {/* Images Grid */}
      {loading ? (
        <div className="py-20 text-center space-y-3">
          <RefreshCw className="h-6 w-6 text-cyan-400 animate-spin mx-auto" />
          <p className="text-xs text-slate-400">Loading catalog items...</p>
        </div>
      ) : error ? (
        <div className="p-6 rounded-2xl bg-rose-950/20 border border-rose-800/40 text-xs text-rose-300 flex items-center space-x-3">
          <AlertCircle className="h-5 w-5 text-rose-400 flex-shrink-0" />
          <span>Error loading catalog: {error}</span>
        </div>
      ) : filteredImages.length === 0 ? (
        <div className="p-12 text-center rounded-2xl bg-surface/30 border border-slate-800 space-y-4">
          <Layers className="h-10 w-10 text-slate-600 mx-auto" />
          <h3 className="text-sm font-semibold text-white">No Images Found</h3>
          <p className="text-xs text-slate-400 max-w-sm mx-auto">
            {searchQuery || filterType
              ? "No satellite images matched your filter. Try adjusting your query."
              : "No satellite images have been ingested yet. Upload an image to start."}
          </p>
          <button
            type="button"
            onClick={() => setShowUpload(true)}
            className="inline-flex items-center space-x-1.5 px-4 py-2 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-slate-950 font-bold text-xs"
          >
            <span>Upload Satellite Image</span>
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {filteredImages.map((img) => (
            <div
              key={img.id}
              className="rounded-2xl bg-surface/50 border border-slate-800 overflow-hidden hover:border-slate-700 transition flex flex-col justify-between group"
            >
              {/* Preview Thumbnail */}
              <div className="relative aspect-video bg-slate-950 overflow-hidden border-b border-slate-800/80">
                <img
                  src={getImagePreviewUrl(img.id)}
                  alt={img.filename}
                  className="w-full h-full object-cover group-hover:scale-105 transition duration-300"
                  onError={(e) => {
                    // Fallback to placeholder on broken preview
                    (e.target as HTMLElement).style.display = "none";
                  }}
                />
                <div className="absolute top-2 left-2">
                  <span className="px-2 py-0.5 rounded bg-slate-900/90 backdrop-blur-sm text-cyan-300 font-mono text-[10px] border border-cyan-800/50">
                    {img.format.toUpperCase()}
                  </span>
                </div>
                <div className="absolute top-2 right-2">
                  <span className="px-2 py-0.5 rounded bg-slate-900/90 backdrop-blur-sm text-slate-300 font-mono text-[10px] border border-slate-700">
                    {img.sensor_type || "optical"}
                  </span>
                </div>
              </div>

              {/* Specs & Details */}
              <div className="p-4 space-y-3 flex-1 flex flex-col justify-between">
                <div className="space-y-1">
                  <h3 className="text-xs font-bold text-white truncate" title={img.filename}>
                    {img.filename}
                  </h3>
                  <div className="grid grid-cols-2 gap-2 text-[11px] text-slate-400 font-mono pt-1">
                    <div>
                      <span className="text-slate-500">Dimensions:</span> {img.width}x{img.height}
                    </div>
                    <div>
                      <span className="text-slate-500">Bands:</span> {img.channels} ch
                    </div>
                    <div>
                      <span className="text-slate-500">CRS:</span> {img.crs || "Unprojected"}
                    </div>
                    <div>
                      <span className="text-slate-500">GSD:</span> {img.gsd_meters ? `${img.gsd_meters.toFixed(2)}m` : "N/A"}
                    </div>
                  </div>
                </div>

                {/* Card Actions */}
                <div className="pt-3 border-t border-slate-800/80 flex items-center justify-between">
                  <Link
                    href={`/images/${img.id}`}
                    className="text-xs text-slate-400 hover:text-slate-200 transition inline-flex items-center"
                  >
                    <span>Metadata</span>
                    <ExternalLink className="h-3 w-3 ml-1" />
                  </Link>

                  <Link
                    href={`/analyze?image_id=${img.id}`}
                    className="inline-flex items-center space-x-1 px-3 py-1.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-slate-950 font-bold text-xs transition"
                  >
                    <span>Analyze</span>
                    <ArrowRight className="h-3 w-3" />
                  </Link>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
