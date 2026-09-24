"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  Sparkles,
  ArrowRight,
  Play,
  Layers,
  Cpu,
  GitCompare,
  Radio,
  FileText,
  BarChart3,
  Clock,
  CheckCircle2,
  AlertCircle,
  Database,
  ExternalLink,
  ShieldCheck,
} from "lucide-react";
import { DemoGallery } from "@/components/demo-gallery";
import { getAnalysisHistory } from "@/lib/api";
import { AnalysisHistoryItem } from "@/lib/types";
import { formatConfidenceBadge, formatTaskTypeLabel } from "@/lib/presentation-utils";

export default function HomePage() {
  const [recentAnalyses, setRecentAnalyses] = useState<AnalysisHistoryItem[]>([]);
  const [loadingHistory, setLoadingHistory] = useState<boolean>(true);
  const [historyError, setHistoryError] = useState<string | null>(null);

  useEffect(() => {
    async function loadRecent() {
      try {
        setLoadingHistory(true);
        const data = await getAnalysisHistory({ page: 1, page_size: 4 });
        setRecentAnalyses(data.items || []);
      } catch (err: any) {
        setHistoryError(err?.message || "Failed to load recent activity");
      } finally {
        setLoadingHistory(false);
      }
    }
    loadRecent();
  }, []);

  return (
    <div className="space-y-14 pb-12">
      {/* Hero Section */}
      <section className="relative text-center max-w-4xl mx-auto pt-6 space-y-6">
        <div className="inline-flex items-center space-x-2 px-3.5 py-1.5 rounded-full bg-cyan-950/70 border border-cyan-800/60 text-xs font-mono text-cyan-300 shadow-sm">
          <Sparkles className="h-3.5 w-3.5 text-cyan-400" />
          <span>ISRO Smart India Hackathon · Problem Statement 26167</span>
          <span className="text-slate-600">|</span>
          <span className="text-slate-300 font-semibold">Phase 9 · Product UX</span>
        </div>

        <h1 className="text-4xl sm:text-6xl font-black tracking-tight text-white leading-tight">
          SatQuery AI <br />
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 via-teal-300 to-emerald-400">
            Interactive Remote-Sensing Intelligence
          </span>
        </h1>

        <p className="text-base sm:text-lg text-slate-300 max-w-2xl mx-auto leading-relaxed">
          Production-grade vision-language analysis for satellite Earth observation.
          Combines BigEarthNet-adapted models, bi-temporal change detection, Cartosat-2S &amp; RISAT SAR fusion, and verifiable multi-format export.
        </p>

        {/* Primary Action Buttons */}
        <div className="flex flex-wrap items-center justify-center gap-4 pt-2">
          <Link
            href="/analyze"
            className="inline-flex items-center space-x-2 px-6 py-3.5 rounded-xl bg-gradient-to-r from-cyan-500 to-teal-500 hover:from-cyan-400 hover:to-teal-400 text-slate-950 font-bold text-sm shadow-lg shadow-cyan-950/50 hover:shadow-cyan-900/60 transition transform hover:-translate-y-0.5"
          >
            <Play className="h-4 w-4 fill-slate-950" />
            <span>Launch New Analysis</span>
          </Link>

          <Link
            href="/history"
            className="inline-flex items-center space-x-2 px-5 py-3.5 rounded-xl bg-slate-900/80 hover:bg-slate-800/90 border border-slate-700/70 text-slate-200 font-medium text-sm transition"
          >
            <Clock className="h-4 w-4 text-slate-400" />
            <span>Analysis History</span>
          </Link>

          <Link
            href="/reports"
            className="inline-flex items-center space-x-2 px-5 py-3.5 rounded-xl bg-slate-900/80 hover:bg-slate-800/90 border border-slate-700/70 text-slate-200 font-medium text-sm transition"
          >
            <FileText className="h-4 w-4 text-cyan-400" />
            <span>Reports Library</span>
          </Link>

          <Link
            href="/evaluation"
            className="inline-flex items-center space-x-2 px-5 py-3.5 rounded-xl bg-slate-900/80 hover:bg-slate-800/90 border border-slate-700/70 text-slate-200 font-medium text-sm transition"
          >
            <BarChart3 className="h-4 w-4 text-teal-400" />
            <span>Benchmark Engine</span>
          </Link>
        </div>

        {/* System Trust Pillars */}
        <div className="pt-4 flex flex-wrap items-center justify-center gap-6 text-xs text-slate-400">
          <div className="flex items-center space-x-1.5">
            <ShieldCheck className="h-4 w-4 text-emerald-400" />
            <span>Zero Data Fabrication</span>
          </div>
          <div className="flex items-center space-x-1.5">
            <CheckCircle2 className="h-4 w-4 text-cyan-400" />
            <span>Calibrated Conformal Scores</span>
          </div>
          <div className="flex items-center space-x-1.5">
            <Database className="h-4 w-4 text-teal-400" />
            <span>Reproducible Multi-Format Export</span>
          </div>
        </div>
      </section>

      {/* Interactive Hackathon Demonstration Presets */}
      <section className="space-y-4">
        <DemoGallery />
      </section>

      {/* Core Capabilities Grid */}
      <section className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold text-white tracking-tight">System Capabilities</h2>
            <p className="text-xs text-slate-400">Integrated remote-sensing architecture verified across Phases 1–8</p>
          </div>
          <Link
            href="/analyze"
            className="text-xs text-cyan-400 hover:text-cyan-300 font-medium inline-flex items-center"
          >
            <span>Open Workspace</span>
            <ArrowRight className="h-3 w-3 ml-1" />
          </Link>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Card 1 */}
          <div className="p-5 rounded-2xl bg-surface/60 border border-slate-800/80 backdrop-blur-sm space-y-3 hover:border-slate-700 transition">
            <div className="h-10 w-10 rounded-xl bg-cyan-950/80 border border-cyan-800/60 flex items-center justify-center text-cyan-400">
              <Layers className="h-5 w-5" />
            </div>
            <h3 className="font-semibold text-sm text-white">Geospatial Ingestion &amp; VQA</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              GeoTIFF, TIFF, PNG, and JPEG ingestion with automatic CRS, GSD, and band verification. Natural-language VQA fine-tuned on BigEarthNet v2.0.
            </p>
            <div className="pt-2">
              <Link
                href="/analyze"
                className="text-xs text-cyan-400 hover:text-cyan-300 font-medium inline-flex items-center"
              >
                <span>Analyze Single Image</span>
                <ArrowRight className="h-3 w-3 ml-1" />
              </Link>
            </div>
          </div>

          {/* Card 2 */}
          <div className="p-5 rounded-2xl bg-surface/60 border border-slate-800/80 backdrop-blur-sm space-y-3 hover:border-slate-700 transition">
            <div className="h-10 w-10 rounded-xl bg-teal-950/80 border border-teal-800/60 flex items-center justify-center text-teal-400">
              <Cpu className="h-5 w-5" />
            </div>
            <h3 className="font-semibold text-sm text-white">Object Grounding</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Text-prompted spatial detection returning pixel bounding boxes, CRS coordinates, and area measurements with VRSBench Recall@0.5 verification.
            </p>
            <div className="pt-2">
              <Link
                href="/analyze?task=grounding"
                className="text-xs text-teal-400 hover:text-teal-300 font-medium inline-flex items-center"
              >
                <span>Run Grounding</span>
                <ArrowRight className="h-3 w-3 ml-1" />
              </Link>
            </div>
          </div>

          {/* Card 3 */}
          <div className="p-5 rounded-2xl bg-surface/60 border border-slate-800/80 backdrop-blur-sm space-y-3 hover:border-slate-700 transition">
            <div className="h-10 w-10 rounded-xl bg-blue-950/80 border border-blue-800/60 flex items-center justify-center text-blue-400">
              <GitCompare className="h-5 w-5" />
            </div>
            <h3 className="font-semibold text-sm text-white">Bi-Temporal Change</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Non-destructive co-registration between T1 and T2 epochs with NDVI/difference metric heatmaps and CDVQA natural language reporting.
            </p>
            <div className="pt-2">
              <Link
                href="/temporal"
                className="text-xs text-blue-400 hover:text-blue-300 font-medium inline-flex items-center"
              >
                <span>Temporal Workspace</span>
                <ArrowRight className="h-3 w-3 ml-1" />
              </Link>
            </div>
          </div>

          {/* Card 4 */}
          <div className="p-5 rounded-2xl bg-surface/60 border border-cyan-800/40 backdrop-blur-sm space-y-3 bg-gradient-to-b from-cyan-950/20 to-transparent hover:border-cyan-700/60 transition">
            <div className="h-10 w-10 rounded-xl bg-cyan-950/80 border border-cyan-700/60 flex items-center justify-center text-cyan-400">
              <Radio className="h-5 w-5" />
            </div>
            <h3 className="font-semibold text-sm text-white">Optical + SAR Cross-Modal</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Cartosat-2S optical and RISAT SAR joint fusion, physics-aware radar backscatter analysis, cloud penetration, and modality disagreement detection.
            </p>
            <div className="pt-2">
              <Link
                href="/cross-modal"
                className="text-xs text-cyan-400 hover:text-cyan-300 font-medium inline-flex items-center"
              >
                <span>Cross-Modal Workspace</span>
                <ArrowRight className="h-3 w-3 ml-1" />
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Recent Analysis Activity Feed */}
      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold text-white tracking-tight">Recent Analysis Activity</h2>
            <p className="text-xs text-slate-400">Live feed from persistent database store</p>
          </div>
          <Link
            href="/history"
            className="text-xs text-cyan-400 hover:text-cyan-300 font-medium inline-flex items-center"
          >
            <span>View Full History</span>
            <ArrowRight className="h-3 w-3 ml-1" />
          </Link>
        </div>

        {loadingHistory ? (
          <div className="p-8 text-center rounded-2xl bg-surface/40 border border-slate-800 text-xs text-slate-400 animate-pulse">
            Loading recent analyses...
          </div>
        ) : historyError ? (
          <div className="p-6 rounded-2xl bg-amber-950/20 border border-amber-800/40 text-xs text-amber-300 flex items-center space-x-3">
            <AlertCircle className="h-5 w-5 flex-shrink-0 text-amber-400" />
            <span>Could not fetch recent activity: {historyError}</span>
          </div>
        ) : recentAnalyses.length === 0 ? (
          <div className="p-8 text-center rounded-2xl bg-surface/30 border border-slate-800/70 space-y-3">
            <FileText className="h-8 w-8 text-slate-600 mx-auto" />
            <p className="text-xs text-slate-400">No analyses recorded yet. Run your first satellite image query!</p>
            <Link
              href="/analyze"
              className="inline-flex items-center space-x-1.5 px-4 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-slate-950 font-bold text-xs"
            >
              <span>Start Analysis</span>
              <ArrowRight className="h-3.5 w-3.5" />
            </Link>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
            {recentAnalyses.map((item) => {
              const conf = formatConfidenceBadge(item.confidence_score);
              const itemId = item.analysis_id || item.id;
              return (
                <div
                  key={item.id}
                  className="p-4 rounded-xl bg-surface/50 border border-slate-800/80 hover:border-slate-700/80 transition flex flex-col justify-between space-y-3"
                >
                  <div className="flex items-center justify-between text-xs">
                    <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-mono text-[10px]">
                      {formatTaskTypeLabel(item.task_type)}
                    </span>
                    <span className={`px-2 py-0.5 rounded text-[10px] font-medium border ${conf.color}`}>
                      Confidence: {conf.label} ({conf.pct})
                    </span>
                  </div>

                  <p className="text-xs text-slate-200 line-clamp-2 font-medium">
                    &ldquo;{item.question || "Remote sensing automated query"}&rdquo;
                  </p>

                  <div className="flex items-center justify-between pt-2 border-t border-slate-800/60 text-[11px] text-slate-400">
                    <span className="font-mono text-[10px]">
                      {item.created_at ? new Date(item.created_at).toLocaleDateString() : "Recently"} · {item.execution_time_ms ? `${(item.execution_time_ms / 1000).toFixed(1)}s` : "completed"}
                    </span>

                    <div className="flex items-center space-x-3">
                      <Link
                        href={`/analysis/${itemId}`}
                        className="text-cyan-400 hover:text-cyan-300 font-medium inline-flex items-center"
                      >
                        <span>Details</span>
                        <ArrowRight className="h-3 w-3 ml-0.5" />
                      </Link>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </section>
    </div>
  );
}
