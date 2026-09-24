"use client";

import React, { useEffect, useState, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import {
  GitCompare,
  ArrowLeft,
  Layers,
  Sparkles,
  ShieldCheck,
  Clock,
  RefreshCw,
  PlusCircle,
} from "lucide-react";
import { ImageInspect } from "@/lib/types";
import { listImages } from "@/lib/api";
import { TemporalWorkspace } from "@/components/temporal-workspace";

function TemporalPageContent() {
  const searchParams = useSearchParams();
  const pairIdParam = searchParams.get("pair_id") || undefined;

  const [availableImages, setAvailableImages] = useState<ImageInspect[]>([]);
  const [loadingImages, setLoadingImages] = useState<boolean>(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  const fetchImages = async () => {
    try {
      setLoadingImages(true);
      setLoadError(null);
      const data = await listImages(50);
      setAvailableImages(data);
    } catch (err: any) {
      console.warn("Could not load image catalog:", err);
      setLoadError(err.message || "Failed to load catalog");
    } finally {
      setLoadingImages(false);
    }
  };

  useEffect(() => {
    fetchImages();
  }, []);

  return (
    <div className="space-y-6">
      {/* Top Breadcrumb & Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center space-x-3">
          <Link
            href="/"
            className="text-xs text-slate-400 hover:text-slate-200 flex items-center space-x-1.5 transition"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            <span>Dashboard</span>
          </Link>
          <span className="text-slate-600">/</span>
          <div className="flex items-center space-x-1.5 text-xs text-cyan-400 font-mono">
            <GitCompare className="h-3.5 w-3.5" />
            <span>Bi-Temporal Workspace</span>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={fetchImages}
            disabled={loadingImages}
            className="p-1.5 text-slate-400 hover:text-slate-200 rounded-lg hover:bg-slate-800/60 transition"
            title="Refresh Image Catalog"
          >
            <RefreshCw
              className={`h-4 w-4 ${loadingImages ? "animate-spin" : ""}`}
            />
          </button>
          <Link
            href="/upload"
            className="px-3 py-1.5 rounded-lg text-xs font-medium bg-cyan-950/60 border border-cyan-700/60 text-cyan-300 hover:bg-cyan-900/60 transition flex items-center space-x-1.5"
          >
            <PlusCircle className="h-3.5 w-3.5" />
            <span>Ingest Satellite Imagery</span>
          </Link>
        </div>
      </div>

      {/* Hero Header */}
      <div className="rounded-2xl border border-slate-800 bg-surface/50 p-6 backdrop-blur-sm relative overflow-hidden">
        <div className="absolute top-0 right-0 w-96 h-96 bg-gradient-to-bl from-cyan-500/10 via-teal-500/5 to-transparent rounded-full blur-3xl -z-10 pointer-events-none" />
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-1.5 max-w-3xl">
            <div className="flex items-center space-x-2">
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold tracking-wider uppercase bg-cyan-950 border border-cyan-700/60 text-cyan-300 font-mono">
                Phase 5 · Temporal Analysis
              </span>
              <span className="text-[11px] text-slate-400">
                Non-Destructive Co-Registration & Change Intelligence
              </span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-white flex items-center space-x-2.5">
              <GitCompare className="h-7 w-7 text-cyan-400" />
              <span>Bi-Temporal Change Intelligence</span>
            </h1>
            <p className="text-xs sm:text-sm text-slate-400 leading-relaxed">
              Pair satellite acquisitions across different epochs ($T_1$ and $T_2$).
              Detect morphological, structural, and land-use changes, ask natural language
              Change VQA questions, and inspect geo-referenced change polygons.
            </p>
          </div>

          <div className="flex flex-col sm:flex-row md:flex-col gap-2 shrink-0 text-xs font-mono">
            <div className="p-2.5 rounded-xl bg-slate-900/60 border border-slate-800/80 flex items-center space-x-2 text-slate-300">
              <ShieldCheck className="h-4 w-4 text-emerald-400" />
              <span>Zero-Modification Original Rasters</span>
            </div>
            <div className="p-2.5 rounded-xl bg-slate-900/60 border border-slate-800/80 flex items-center space-x-2 text-slate-300">
              <Clock className="h-4 w-4 text-cyan-400" />
              <span>Bilinear In-Memory Co-Registration</span>
            </div>
          </div>
        </div>
      </div>

      {/* Main Workspace Component */}
      <TemporalWorkspace
        initialPairId={pairIdParam}
        availableImages={availableImages}
      />
    </div>
  );
}

export default function TemporalPage() {
  return (
    <Suspense
      fallback={
        <div className="py-16 text-center text-xs font-mono text-slate-500">
          Loading Bi-Temporal Workspace...
        </div>
      }
    >
      <TemporalPageContent />
    </Suspense>
  );
}
