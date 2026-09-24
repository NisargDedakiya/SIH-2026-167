"use client";

import React, { useEffect, useState, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import {
  Radio,
  ArrowLeft,
  Layers,
  Sparkles,
  ShieldCheck,
  Clock,
  RefreshCw,
  PlusCircle,
  Cpu,
} from "lucide-react";
import { ImageInspect } from "@/lib/types";
import { listImages } from "@/lib/api";
import { CrossModalWorkspace } from "@/components/cross-modal-workspace";

function CrossModalPageContent() {
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
            <Radio className="h-3.5 w-3.5" />
            <span>Cross-Modal Workspace</span>
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
        <div className="absolute top-0 right-0 w-96 h-96 bg-gradient-to-bl from-cyan-500/10 via-amber-500/5 to-transparent rounded-full blur-3xl -z-10 pointer-events-none" />
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-1.5 max-w-3xl">
            <div className="flex items-center space-x-2">
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold tracking-wider uppercase bg-cyan-950 border border-cyan-700/60 text-cyan-300 font-mono">
                Phase 6 · Multimodal AI
              </span>
              <span className="text-[11px] text-slate-400">
                Cartosat Optical + RISAT SAR Joint Interpretation
              </span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-white flex items-center space-x-2.5">
              <Radio className="h-7 w-7 text-cyan-400" />
              <span>Optical + SAR Cross-Modal Intelligence</span>
            </h1>
            <p className="text-xs sm:text-sm text-slate-400 leading-relaxed">
              Synthesize multispectral optical imagery (spectral reflectance, vegetation color, cloud context)
              with Synthetic Aperture Radar (all-weather penetration, surface roughness, dielectric double-bounce).
              Ask multimodal questions, inspect physical agreements, and ground evidence across both sensor domains.
            </p>
          </div>

          <div className="flex flex-col sm:flex-row md:flex-col gap-2 shrink-0 text-xs font-mono">
            <div className="p-2.5 rounded-xl bg-slate-900/60 border border-slate-800/80 flex items-center space-x-2 text-slate-300">
              <ShieldCheck className="h-4 w-4 text-emerald-400" />
              <span>Physics-Aware SAR dB Log-Scale</span>
            </div>
            <div className="p-2.5 rounded-xl bg-slate-900/60 border border-slate-800/80 flex items-center space-x-2 text-slate-300">
              <Cpu className="h-4 w-4 text-amber-400" />
              <span>Modality Disagreement Reporting</span>
            </div>
          </div>
        </div>
      </div>

      {/* Main Workspace Component */}
      <CrossModalWorkspace
        initialPairId={pairIdParam}
        availableImages={availableImages}
      />
    </div>
  );
}

export default function CrossModalPage() {
  return (
    <Suspense
      fallback={
        <div className="py-16 text-center text-xs font-mono text-slate-500">
          Loading Cross-Modal Workspace...
        </div>
      }
    >
      <CrossModalPageContent />
    </Suspense>
  );
}
