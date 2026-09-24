"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  FileText,
  Download,
  Package,
  Layers,
  Sparkles,
  ExternalLink,
  ShieldCheck,
  RefreshCw,
  AlertCircle,
  FileCode,
  FileSpreadsheet,
} from "lucide-react";
import {
  getAnalysisHistory,
  getReportHtmlUrl,
  getReportPdfUrl,
  getReportPackageUrl,
} from "@/lib/api";
import { AnalysisHistoryItem } from "@/lib/types";
import { formatConfidenceBadge, formatTaskTypeLabel } from "@/lib/presentation-utils";

export default function ReportsLibraryPage() {
  const [reports, setReports] = useState<AnalysisHistoryItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadReports() {
      try {
        setLoading(true);
        setError(null);
        const res = await getAnalysisHistory({ page: 1, page_size: 50, status: "COMPLETED" });
        setReports(res.items || []);
      } catch (err: any) {
        setError(err?.message || "Failed to load reports");
      } finally {
        setLoading(false);
      }
    }
    loadReports();
  }, []);

  return (
    <div className="space-y-10 pb-16">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-6">
        <div>
          <div className="flex items-center space-x-2 text-xs font-mono text-cyan-400 mb-1">
            <Package className="h-3.5 w-3.5" />
            <span>Verifiable Intelligence Deliverables</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-black text-white tracking-tight">
            Reports &amp; Export Library
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 mt-1">
            Download publication-grade analysis reports, vector PDFs, machine-readable JSON schemas, and complete ZIP evidence packages.
          </p>
        </div>

        <Link
          href="/analyze"
          className="inline-flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-slate-950 font-bold text-xs shadow-md transition"
        >
          <Sparkles className="h-3.5 w-3.5" />
          <span>New Analysis</span>
        </Link>
      </div>

      {/* Export Format Highlights */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl bg-surface/50 border border-slate-800 space-y-2">
          <div className="h-8 w-8 rounded-lg bg-cyan-950 flex items-center justify-center text-cyan-400">
            <FileText className="h-4 w-4" />
          </div>
          <h3 className="text-xs font-bold text-white uppercase tracking-wider">Interactive HTML</h3>
          <p className="text-[11px] text-slate-400 leading-relaxed">
            Zero-dependency, fully-styled standalone document readable offline in any browser.
          </p>
        </div>

        <div className="p-4 rounded-xl bg-surface/50 border border-slate-800 space-y-2">
          <div className="h-8 w-8 rounded-lg bg-teal-950 flex items-center justify-center text-teal-400">
            <Download className="h-4 w-4" />
          </div>
          <h3 className="text-xs font-bold text-white uppercase tracking-wider">Publication PDF</h3>
          <p className="text-[11px] text-slate-400 leading-relaxed">
            ReportLab-generated vector layout with ISRO SIH header, metadata tables, and reproducibility tokens.
          </p>
        </div>

        <div className="p-4 rounded-xl bg-surface/50 border border-slate-800 space-y-2">
          <div className="h-8 w-8 rounded-lg bg-blue-950 flex items-center justify-center text-blue-400">
            <FileCode className="h-4 w-4" />
          </div>
          <h3 className="text-xs font-bold text-white uppercase tracking-wider">Machine JSON</h3>
          <p className="text-[11px] text-slate-400 leading-relaxed">
            Strict Pydantic-validated schema for downstream GIS pipelines and programmatic ingestion.
          </p>
        </div>

        <div className="p-4 rounded-xl bg-surface/50 border border-slate-800 space-y-2">
          <div className="h-8 w-8 rounded-lg bg-indigo-950 flex items-center justify-center text-indigo-400">
            <Package className="h-4 w-4" />
          </div>
          <h3 className="text-xs font-bold text-white uppercase tracking-wider">ZIP Package</h3>
          <p className="text-[11px] text-slate-400 leading-relaxed">
            Sanitized archive containing all formats, audit trace, raster evidence, and README.
          </p>
        </div>
      </div>

      {/* Reports Listing */}
      <div className="space-y-4">
        <h2 className="text-base font-bold text-white tracking-tight">Available Analysis Packages</h2>

        {loading ? (
          <div className="py-20 text-center space-y-3">
            <RefreshCw className="h-6 w-6 text-cyan-400 animate-spin mx-auto" />
            <p className="text-xs text-slate-400">Scanning reports catalog...</p>
          </div>
        ) : error ? (
          <div className="p-6 rounded-2xl bg-rose-950/20 border border-rose-800/40 text-xs text-rose-300 flex items-center space-x-3">
            <AlertCircle className="h-5 w-5 text-rose-400 flex-shrink-0" />
            <span>Error loading reports: {error}</span>
          </div>
        ) : reports.length === 0 ? (
          <div className="p-12 text-center rounded-2xl bg-surface/30 border border-slate-800 space-y-4">
            <Package className="h-10 w-10 text-slate-600 mx-auto" />
            <h3 className="text-sm font-semibold text-white">No Reports Generated Yet</h3>
            <p className="text-xs text-slate-400 max-w-sm mx-auto">
              Completed analyses automatically produce verifiable report deliverables. Run an analysis to generate export packages.
            </p>
            <Link
              href="/analyze"
              className="inline-flex items-center space-x-1.5 px-4 py-2 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-slate-950 font-bold text-xs"
            >
              <span>Launch Analysis</span>
            </Link>
          </div>
        ) : (
          <div className="space-y-3">
            {reports.map((report) => {
              const conf = formatConfidenceBadge(report.confidence_score);
              const reportId = report.analysis_id || report.id;
              return (
                <div
                  key={report.id}
                  className="p-5 rounded-2xl bg-surface/50 border border-slate-800 hover:border-slate-700/80 transition flex flex-col lg:flex-row lg:items-center justify-between gap-4"
                >
                  <div className="space-y-1.5 flex-1 min-w-0">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-mono text-[10px]">
                        {formatTaskTypeLabel(report.task_type)}
                      </span>
                      <span className={`px-2 py-0.5 rounded text-[10px] font-medium border ${conf.color}`}>
                        {conf.label} ({conf.pct})
                      </span>
                      <span className="text-[10px] font-mono text-slate-500">
                        #{reportId.slice(0, 8)}
                      </span>
                    </div>

                    <h3 className="text-sm font-semibold text-white truncate">
                      {report.question || "Remote-Sensing Intelligence Query"}
                    </h3>

                    <p className="text-xs text-slate-400 line-clamp-1 font-mono">
                      Generated: {report.created_at ? new Date(report.created_at).toLocaleString() : "Recently"}
                    </p>
                  </div>

                  {/* Multi-Format Export Action Bar */}
                  <div className="flex flex-wrap items-center gap-2">
                    <a
                      href={getReportHtmlUrl(reportId)}
                      target="_blank"
                      rel="noreferrer"
                      className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-700 hover:border-cyan-500 text-xs text-cyan-300 font-medium transition"
                    >
                      <FileText className="h-3.5 w-3.5" />
                      <span>HTML</span>
                    </a>

                    <a
                      href={getReportPdfUrl(reportId)}
                      target="_blank"
                      rel="noreferrer"
                      className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-700 hover:border-teal-500 text-xs text-teal-300 font-medium transition"
                    >
                      <Download className="h-3.5 w-3.5" />
                      <span>PDF</span>
                    </a>

                    <a
                      href={getReportPackageUrl(reportId)}
                      download
                      className="inline-flex items-center space-x-1.5 px-3.5 py-1.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-slate-950 font-bold text-xs transition"
                    >
                      <Package className="h-3.5 w-3.5" />
                      <span>ZIP Package</span>
                    </a>

                    <Link
                      href={`/analysis/${reportId}`}
                      className="inline-flex items-center space-x-1 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs text-slate-200 transition"
                    >
                      <span>Inspect</span>
                      <ExternalLink className="h-3 w-3" />
                    </Link>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
