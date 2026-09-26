"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  Clock,
  Search,
  ArrowRight,
  FileText,
  Download,
  AlertCircle,
  RefreshCw,
  Sparkles,
  ChevronLeft,
  ChevronRight,
  MessageSquare,
  Target,
  GitCompare,
  Radio,
  X,
  Package,
  CheckCircle2,
  XCircle,
  Loader2,
} from "lucide-react";
import { getAnalysisHistory, getReportHtmlUrl, getReportPdfUrl, getReportPackageUrl } from "@/lib/api";
import { AnalysisHistoryItem } from "@/lib/types";
import { formatConfidenceBadge, formatTaskTypeLabel } from "@/lib/presentation-utils";

// ── Filter config ─────────────────────────────────────────────
const TASK_FILTERS = [
  { value: "", label: "All Tasks", icon: null },
  { value: "vqa", label: "VQA", icon: MessageSquare },
  { value: "grounding", label: "Grounding", icon: Target },
  { value: "caption", label: "Caption", icon: FileText },
  { value: "temporal_change", label: "Change", icon: GitCompare },
  { value: "cross_modal_fusion", label: "SAR+Opt", icon: Radio },
];

const STATUS_FILTERS = [
  { value: "", label: "All" },
  { value: "COMPLETED", label: "Completed" },
  { value: "RUNNING", label: "Running" },
  { value: "FAILED", label: "Failed" },
];

// ── Task styling ──────────────────────────────────────────────
function getTaskConfig(task: string) {
  const t = (task || "").toLowerCase();
  if (t.includes("grounding")) return { icon: Target, color: "#86EFAC", bg: "rgba(16,185,129,0.08)", label: "GND" };
  if (t.includes("temporal") || t.includes("change")) return { icon: GitCompare, color: "#C4B5FD", bg: "rgba(139,92,246,0.08)", label: "CHG" };
  if (t.includes("cross") || t.includes("sar")) return { icon: Radio, color: "#FCD34D", bg: "rgba(245,158,11,0.08)", label: "SAR" };
  if (t.includes("caption")) return { icon: FileText, color: "#93C5FD", bg: "rgba(59,130,246,0.08)", label: "CAP" };
  return { icon: MessageSquare, color: "#67E8F9", bg: "rgba(6,182,212,0.08)", label: "VQA" };
}

// ── Status Badge ──────────────────────────────────────────────
function StatusBadge({ status }: { status: string }) {
  const s = (status || "").toUpperCase();
  if (s === "COMPLETED") return (
    <span className="inline-flex items-center gap-1 text-[9px] font-mono font-semibold text-emerald-400 bg-emerald-500/08 border border-emerald-500/20 px-1.5 py-0.5 rounded">
      <CheckCircle2 className="w-2.5 h-2.5" />
      Done
    </span>
  );
  if (s === "FAILED") return (
    <span className="inline-flex items-center gap-1 text-[9px] font-mono font-semibold text-rose-400 bg-rose-500/08 border border-rose-500/20 px-1.5 py-0.5 rounded">
      <XCircle className="w-2.5 h-2.5" />
      Failed
    </span>
  );
  return (
    <span className="inline-flex items-center gap-1 text-[9px] font-mono font-semibold text-amber-400 bg-amber-500/08 border border-amber-500/20 px-1.5 py-0.5 rounded">
      <Loader2 className="w-2.5 h-2.5 animate-spin" />
      Running
    </span>
  );
}

// ── History Item Row ──────────────────────────────────────────
function HistoryItemRow({ item }: { item: AnalysisHistoryItem }) {
  const tc = getTaskConfig(item.task_type || item.task || "");
  const TaskIcon = tc.icon;
  const conf = formatConfidenceBadge(item.confidence_score);
  const itemId = item.analysis_id || item.id;

  const timeStr = item.created_at
    ? (() => {
        const d = new Date(item.created_at);
        const diff = Date.now() - d.getTime();
        const mins = Math.floor(diff / 60000);
        if (mins < 1) return "just now";
        if (mins < 60) return `${mins}m ago`;
        const hrs = Math.floor(mins / 60);
        if (hrs < 24) return `${hrs}h ago`;
        return d.toLocaleDateString(undefined, { month: "short", day: "numeric" });
      })()
    : "—";

  const timeAbsolute = item.created_at
    ? new Date(item.created_at).toLocaleString()
    : "";

  return (
    <div className="group flex items-start gap-3 p-3.5 hover:bg-[#111821]/60 transition-colors border-b border-[#1C2535] last:border-0">
      {/* Task icon */}
      <div
        className="flex-shrink-0 w-9 h-9 rounded-lg flex items-center justify-center mt-0.5"
        style={{ background: tc.bg, border: `1px solid ${tc.color}28` }}
      >
        <TaskIcon className="w-4 h-4" style={{ color: tc.color }} />
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0">
        <div className="flex items-start justify-between gap-2">
          <p className="text-[12px] text-[#F2F5F8] font-medium leading-snug line-clamp-2">
            {item.question || item.query || "Remote sensing analysis"}
          </p>
          <span
            className="text-[9px] font-mono text-[#49576A] flex-shrink-0 mt-0.5"
            title={timeAbsolute}
          >
            {timeStr}
          </span>
        </div>

        {item.answer && (
          <p className="text-[10px] text-[#687381] mt-0.5 line-clamp-1">
            {item.answer}
          </p>
        )}

        <div className="flex items-center flex-wrap gap-x-2 gap-y-1 mt-1.5">
          {/* Task */}
          <span
            className="text-[9px] font-mono font-semibold px-1.5 py-0.5 rounded"
            style={{ color: tc.color, background: tc.bg }}
          >
            {formatTaskTypeLabel(item.task_type || item.task)}
          </span>

          {/* Status */}
          <StatusBadge status={item.status || "COMPLETED"} />

          {/* Confidence */}
          {item.confidence_score != null && (
            <span className={`text-[9px] font-mono ${conf.color.includes("emerald") ? "text-emerald-400" : conf.color.includes("amber") ? "text-amber-400" : "text-rose-400"}`}>
              {conf.pct}
            </span>
          )}

          {/* Time */}
          {item.execution_time_ms && (
            <span className="text-[9px] font-mono text-[#49576A]">
              {(item.execution_time_ms / 1000).toFixed(1)}s
            </span>
          )}

          {/* ID */}
          <span className="text-[9px] font-mono text-[#303B49]">#{itemId.slice(0, 8)}</span>
        </div>
      </div>

      {/* Actions — visible on hover */}
      <div className="flex items-center gap-1.5 flex-shrink-0 opacity-0 group-hover:opacity-100 transition-opacity">
        <a
          href={getReportHtmlUrl(itemId)}
          target="_blank" rel="noreferrer"
          title="View HTML Report"
          className="w-7 h-7 flex items-center justify-center rounded-md bg-[#1C2535] hover:bg-[#25303D] text-[#687381] hover:text-cyan-400 transition"
        >
          <FileText className="w-3 h-3" />
        </a>
        <a
          href={getReportPdfUrl(itemId)}
          target="_blank" rel="noreferrer"
          title="Download PDF"
          className="w-7 h-7 flex items-center justify-center rounded-md bg-[#1C2535] hover:bg-[#25303D] text-[#687381] hover:text-teal-400 transition"
        >
          <Download className="w-3 h-3" />
        </a>
        <Link
          href={`/analysis/${itemId}`}
          className="flex items-center gap-1 px-2.5 py-1 rounded-md bg-[#1C2535] hover:bg-cyan-500/15 text-[10px] font-semibold text-[#A7B0BD] hover:text-cyan-300 transition"
        >
          Inspect
          <ArrowRight className="w-2.5 h-2.5" />
        </Link>
      </div>
    </div>
  );
}

// ── Main Page ─────────────────────────────────────────────────
export default function HistoryPage() {
  const [items, setItems] = useState<AnalysisHistoryItem[]>([]);
  const [total, setTotal] = useState<number>(0);
  const [page, setPage] = useState<number>(1);
  const [pageSize] = useState<number>(15);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

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

  useEffect(() => { fetchHistory(); }, [page, taskFilter, statusFilter]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchHistory();
  };

  const totalPages = Math.ceil(total / pageSize) || 1;

  return (
    <div className="space-y-5 pb-12">

      {/* ── Header ── */}
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2 mb-0.5">
            <span className="sq-section-label">Audit Trail & Provenance</span>
          </div>
          <h1 className="text-xl font-bold text-white tracking-tight">Analysis History</h1>
          <p className="text-[11px] text-[#687381] mt-0.5">
            Full audit trail of executed remote-sensing analyses and queries.
          </p>
        </div>
        <Link href="/analyze" className="sq-btn sq-btn-primary">
          <Sparkles className="w-3.5 h-3.5" />
          New Analysis
        </Link>
      </div>

      {/* ── Filters ── */}
      <div className="space-y-2">
        {/* Search */}
        <form onSubmit={handleSearchSubmit} className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-[#303B49]" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search by question, answer, or analysis ID…"
            className="
              w-full pl-9 pr-10 py-2.5 rounded-lg text-[12px]
              bg-[#111821] border border-[#1C2535] text-white
              placeholder-[#303B49]
              focus:outline-none focus:border-[#06B6D4]/50
              hover:border-[#25303D] transition
            "
          />
          {searchQuery && (
            <button
              type="button"
              onClick={() => { setSearchQuery(""); setPage(1); fetchHistory(); }}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-[#303B49] hover:text-white transition"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          )}
        </form>

        {/* Filter tabs */}
        <div className="flex flex-wrap items-center gap-2">
          {/* Task filters */}
          <div className="flex items-center gap-1 bg-[#0D1320] p-1 rounded-lg border border-[#1C2535]">
            {TASK_FILTERS.map((f) => (
              <button
                key={f.value}
                type="button"
                onClick={() => { setTaskFilter(f.value); setPage(1); }}
                className={`
                  flex items-center gap-1 px-2.5 py-1 rounded-md text-[10px] font-medium transition-all
                  ${taskFilter === f.value
                    ? "bg-[#1C2535] text-white"
                    : "text-[#49576A] hover:text-[#A7B0BD]"
                  }
                `}
              >
                {f.icon && <f.icon className="w-3 h-3" />}
                {f.label}
              </button>
            ))}
          </div>

          {/* Status filters */}
          <div className="flex items-center gap-1 bg-[#0D1320] p-1 rounded-lg border border-[#1C2535]">
            {STATUS_FILTERS.map((f) => (
              <button
                key={f.value}
                type="button"
                onClick={() => { setStatusFilter(f.value); setPage(1); }}
                className={`
                  px-2.5 py-1 rounded-md text-[10px] font-medium transition-all
                  ${statusFilter === f.value
                    ? "bg-[#1C2535] text-white"
                    : "text-[#49576A] hover:text-[#A7B0BD]"
                  }
                `}
              >
                {f.label}
              </button>
            ))}
          </div>

          {/* Count */}
          {!loading && (
            <span className="text-[10px] font-mono text-[#49576A] ml-auto">
              {total} {total === 1 ? "record" : "records"}
            </span>
          )}
        </div>
      </div>

      {/* ── Content ── */}
      {loading ? (
        <div className="rounded-xl bg-[#111821] border border-[#1C2535] overflow-hidden">
          {[0, 1, 2, 3, 4].map((i) => (
            <div key={i} className="flex items-start gap-3 p-3.5 border-b border-[#1C2535] last:border-0">
              <div className="w-9 h-9 rounded-lg sq-skeleton flex-shrink-0" />
              <div className="flex-1 space-y-2">
                <div className="h-3.5 sq-skeleton rounded w-3/4" />
                <div className="h-2.5 sq-skeleton rounded w-1/2" />
                <div className="h-2 sq-skeleton rounded w-1/4" />
              </div>
            </div>
          ))}
        </div>
      ) : error ? (
        <div className="flex items-center gap-3 p-4 rounded-xl bg-rose-500/05 border border-rose-500/20 text-xs text-rose-300">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>Error loading history: {error}</span>
          <button onClick={fetchHistory} className="ml-auto sq-btn sq-btn-ghost text-[10px] py-1">
            Retry
          </button>
        </div>
      ) : items.length === 0 ? (
        <div className="flex flex-col items-center justify-center gap-4 py-16 rounded-xl border border-[#1C2535] border-dashed">
          <div className="w-12 h-12 rounded-full bg-[#111821] border border-[#25303D] flex items-center justify-center">
            <Clock className="w-5 h-5 text-[#303B49]" />
          </div>
          <div className="text-center space-y-1">
            <p className="text-sm font-semibold text-white">No Analysis Records Found</p>
            <p className="text-xs text-[#687381] max-w-xs">
              {searchQuery || taskFilter || statusFilter
                ? "No analyses match your filters. Try clearing them."
                : "No remote-sensing analyses have been run yet."}
            </p>
          </div>
          <Link href="/analyze" className="sq-btn sq-btn-primary">
            <Sparkles className="w-3.5 h-3.5" />
            Start Analysis
          </Link>
        </div>
      ) : (
        <div className="rounded-xl bg-[#111821] border border-[#1C2535] overflow-hidden">
          {items.map((item) => (
            <HistoryItemRow key={item.id} item={item} />
          ))}
        </div>
      )}

      {/* ── Pagination ── */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between">
          <button
            type="button"
            disabled={page <= 1}
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            className="sq-btn sq-btn-ghost text-[11px] py-1.5 disabled:opacity-30"
          >
            <ChevronLeft className="w-3.5 h-3.5" />
            Previous
          </button>

          <span className="text-[11px] text-[#49576A] font-mono">
            Page {page} of {totalPages} · {(page - 1) * pageSize + 1}–{Math.min(page * pageSize, total)} of {total}
          </span>

          <button
            type="button"
            disabled={page >= totalPages}
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            className="sq-btn sq-btn-ghost text-[11px] py-1.5 disabled:opacity-30"
          >
            Next
            <ChevronRight className="w-3.5 h-3.5" />
          </button>
        </div>
      )}
    </div>
  );
}
