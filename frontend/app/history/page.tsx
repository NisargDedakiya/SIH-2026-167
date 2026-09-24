"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  Clock,
  Search,
  Filter,
  ArrowRight,
  FileText,
  Download,
  AlertCircle,
  RefreshCw,
  Sparkles,
  ChevronLeft,
  ChevronRight,
  ExternalLink,
} from "lucide-react";
import { getAnalysisHistory, getReportHtmlUrl, getReportPdfUrl, getReportPackageUrl } from "@/lib/api";
import { AnalysisHistoryItem } from "@/lib/types";
import { formatConfidenceBadge, formatTaskTypeLabel } from "@/lib/presentation-utils";

export default function HistoryPage() {
  const [items, setItems] = useState<AnalysisHistoryItem[]>([]);
  const [total, setTotal] = useState<number>(0);
  const [page, setPage] = useState<number>(1);
  const [pageSize] = useState<number>(10);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [taskFilter, setTaskFilter] = useState<string>("");
  const [statusFilter, setStatusFilter] = useState<string>("");

  const fetchHistory = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await getAnalysisHistory({
        page,
        page_size: pageSize,
        task_type: taskFilter || undefined,
        status: statusFilter || undefined,
        search: searchQuery || undefined,
      });
      setItems(res.items || []);
      setTotal(res.total || 0);
    } catch (err: any) {
      setError(err?.message || "Failed to load analysis history");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, [page, taskFilter, statusFilter]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchHistory();
  };

  const totalPages = Math.ceil(total / pageSize) || 1;

  return (
    <div className="space-y-8 pb-16">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-6">
        <div>
          <div className="flex items-center space-x-2 text-xs font-mono text-cyan-400 mb-1">
            <Clock className="h-3.5 w-3.5" />
            <span>Audit Trail &amp; Provenance</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-black text-white tracking-tight">
            Analysis History
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 mt-1">
            Full audit history of executed remote-sensing analyses, spatial queries, and downloadable verification packages.
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

      {/* Filter Toolbar */}
      <div className="p-4 rounded-2xl bg-surface/60 border border-slate-800 space-y-4">
        <form onSubmit={handleSearchSubmit} className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3.5 top-3 h-4 w-4 text-slate-500" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search by question, answer text, or analysis ID..."
              className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-slate-900 border border-slate-700/80 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500"
            />
          </div>

          <div className="flex gap-2">
            <select
              value={taskFilter}
              onChange={(e) => {
                setTaskFilter(e.target.value);
                setPage(1);
              }}
              className="px-3 py-2.5 rounded-xl bg-slate-900 border border-slate-700/80 text-xs text-slate-300 focus:outline-none focus:border-cyan-500"
            >
              <option value="">All Tasks</option>
              <option value="vqa">VQA</option>
              <option value="grounding">Grounding</option>
              <option value="caption">Captioning</option>
              <option value="temporal_change">Temporal Change</option>
              <option value="cross_modal_fusion">Optical + SAR</option>
            </select>

            <select
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value);
                setPage(1);
              }}
              className="px-3 py-2.5 rounded-xl bg-slate-900 border border-slate-700/80 text-xs text-slate-300 focus:outline-none focus:border-cyan-500"
            >
              <option value="">All Statuses</option>
              <option value="COMPLETED">Completed</option>
              <option value="RUNNING">Running</option>
              <option value="FAILED">Failed</option>
            </select>

            <button
              type="submit"
              className="px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-medium text-slate-200 transition"
            >
              Filter
            </button>
          </div>
        </form>
      </div>

      {/* Main Table or Card List */}
      {loading ? (
        <div className="py-20 text-center space-y-3">
          <RefreshCw className="h-6 w-6 text-cyan-400 animate-spin mx-auto" />
          <p className="text-xs text-slate-400">Loading analysis history...</p>
        </div>
      ) : error ? (
        <div className="p-6 rounded-2xl bg-rose-950/20 border border-rose-800/40 text-xs text-rose-300 flex items-center space-x-3">
          <AlertCircle className="h-5 w-5 text-rose-400 flex-shrink-0" />
          <span>Error loading history: {error}</span>
        </div>
      ) : items.length === 0 ? (
        <div className="p-12 text-center rounded-2xl bg-surface/30 border border-slate-800 space-y-4">
          <Clock className="h-10 w-10 text-slate-600 mx-auto" />
          <h3 className="text-sm font-semibold text-white">No Analysis Records Found</h3>
          <p className="text-xs text-slate-400 max-w-sm mx-auto">
            {searchQuery || taskFilter || statusFilter
              ? "No analyses match your active filter criteria. Try clearing search filters."
              : "No remote sensing analyses have been conducted yet. Run your first query!"}
          </p>
          <Link
            href="/analyze"
            className="inline-flex items-center space-x-1.5 px-4 py-2 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-slate-950 font-bold text-xs"
          >
            <span>Start Analysis</span>
            <ArrowRight className="h-3.5 w-3.5" />
          </Link>
        </div>
      ) : (
        <div className="space-y-3">
          <div className="text-xs text-slate-400 flex items-center justify-between px-1">
            <span>
              Showing {(page - 1) * pageSize + 1}–{Math.min(page * pageSize, total)} of {total} records
            </span>
          </div>

          <div className="divide-y divide-slate-800/80 rounded-2xl bg-surface/50 border border-slate-800 overflow-hidden">
            {items.map((item) => {
              const conf = formatConfidenceBadge(item.confidence_score);
              const itemId = item.analysis_id || item.id;
              return (
                <div
                  key={item.id}
                  className="p-4 sm:p-5 hover:bg-slate-900/40 transition flex flex-col md:flex-row md:items-center justify-between gap-4"
                >
                  <div className="space-y-1.5 flex-1 min-w-0">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-mono text-[10px]">
                        {formatTaskTypeLabel(item.task_type)}
                      </span>
                      <span className={`px-2 py-0.5 rounded text-[10px] font-medium border ${conf.color}`}>
                        {conf.label} ({conf.pct})
                      </span>
                      <span className="text-[10px] font-mono text-slate-500">
                        #{itemId.slice(0, 8)}
                      </span>
                    </div>

                    <p className="text-sm font-semibold text-white truncate">
                      {item.question ? `“${item.question}”` : "Automated Remote-Sensing Analysis"}
                    </p>

                    {item.answer && (
                      <p className="text-xs text-slate-400 line-clamp-1">
                        {item.answer}
                      </p>
                    )}

                    <div className="flex items-center space-x-3 text-[11px] text-slate-500 pt-1 font-mono">
                      <span>{item.created_at ? new Date(item.created_at).toLocaleString() : "Recently"}</span>
                      <span>·</span>
                      <span>{item.execution_time_ms ? `${(item.execution_time_ms / 1000).toFixed(2)}s` : "N/A"}</span>
                    </div>
                  </div>

                  {/* Action links */}
                  <div className="flex items-center gap-2 flex-shrink-0">
                    <a
                      href={getReportHtmlUrl(itemId)}
                      target="_blank"
                      rel="noreferrer"
                      title="View HTML Report"
                      className="p-2 rounded-lg bg-slate-900 border border-slate-800 hover:border-cyan-500 text-slate-300 hover:text-cyan-400 transition text-xs"
                    >
                      <FileText className="h-4 w-4" />
                    </a>

                    <a
                      href={getReportPdfUrl(itemId)}
                      target="_blank"
                      rel="noreferrer"
                      title="Download PDF"
                      className="p-2 rounded-lg bg-slate-900 border border-slate-800 hover:border-teal-500 text-slate-300 hover:text-teal-400 transition text-xs"
                    >
                      <Download className="h-4 w-4" />
                    </a>

                    <Link
                      href={`/analysis/${itemId}`}
                      className="inline-flex items-center space-x-1.5 px-3.5 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-slate-950 font-bold text-xs transition"
                    >
                      <span>Inspect</span>
                      <ArrowRight className="h-3 w-3" />
                    </Link>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between pt-4 px-1">
              <button
                type="button"
                disabled={page <= 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                className="inline-flex items-center space-x-1 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-xs text-slate-300 hover:text-white disabled:opacity-40 disabled:cursor-not-allowed"
              >
                <ChevronLeft className="h-3.5 w-3.5" />
                <span>Previous</span>
              </button>

              <span className="text-xs text-slate-400 font-mono">
                Page {page} of {totalPages}
              </span>

              <button
                type="button"
                disabled={page >= totalPages}
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                className="inline-flex items-center space-x-1 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-xs text-slate-300 hover:text-white disabled:opacity-40 disabled:cursor-not-allowed"
              >
                <span>Next</span>
                <ChevronRight className="h-3.5 w-3.5" />
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
