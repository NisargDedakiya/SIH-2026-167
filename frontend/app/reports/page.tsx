"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  FileText,
  Download,
  Package,
  Sparkles,
  ExternalLink,
  RefreshCw,
  AlertCircle,
  FileCode,
  Search,
  X,
  ChevronRight,
  Satellite,
  MessageSquare,
  Target,
  GitCompare,
  Radio,
} from "lucide-react";
import {
  getAnalysisHistory,
  getReportHtmlUrl,
  getReportPdfUrl,
  getReportPackageUrl,
  getReportJsonUrl,
} from "@/lib/api";
import { AnalysisHistoryItem } from "@/lib/types";
import { formatConfidenceBadge, formatTaskTypeLabel } from "@/lib/presentation-utils";

// ── Task styling ──────────────────────────────────────────────
function getTaskConfig(task: string) {
  const t = (task || "").toLowerCase();
  if (t.includes("grounding")) return { icon: Target, color: "#86EFAC", label: "GND" };
  if (t.includes("temporal") || t.includes("change")) return { icon: GitCompare, color: "#C4B5FD", label: "CHG" };
  if (t.includes("cross") || t.includes("sar")) return { icon: Radio, color: "#FCD34D", label: "SAR" };
  if (t.includes("caption")) return { icon: FileText, color: "#93C5FD", label: "CAP" };
  return { icon: MessageSquare, color: "#67E8F9", label: "VQA" };
}

// ── Report Preview ────────────────────────────────────────────
function ReportPreview({ report }: { report: AnalysisHistoryItem }) {
  const tc = getTaskConfig(report.task_type || report.task || "");
  const TaskIcon = tc.icon;
  const conf = formatConfidenceBadge(report.confidence_score);
  const reportId = report.analysis_id || report.id;

  return (
    <div className="flex flex-col h-full p-5 space-y-4">
      {/* Report header */}
      <div className="pb-3 border-b border-[#1C2535]">
        <div className="flex items-center gap-2 mb-2">
          <div
            className="w-7 h-7 rounded-md flex items-center justify-center"
            style={{ background: `${tc.color}14`, border: `1px solid ${tc.color}28` }}
          >
            <TaskIcon className="w-3.5 h-3.5" style={{ color: tc.color }} />
          </div>
          <span className="text-[9px] font-mono font-semibold uppercase tracking-wider" style={{ color: tc.color }}>
            {formatTaskTypeLabel(report.task_type || report.task)} Report
          </span>
        </div>
        <h3 className="text-sm font-semibold text-white leading-snug">
          {report.question || "Remote-Sensing Intelligence Query"}
        </h3>
        <p className="text-[10px] font-mono text-[#49576A] mt-1">
          {report.created_at ? new Date(report.created_at).toLocaleString() : "Recently"} ·
          #{reportId.slice(0, 8)}
        </p>
      </div>

      {/* Confidence */}
      <div className="space-y-1.5">
        <div className="flex justify-between items-center">
          <span className="text-[10px] text-[#687381] font-mono uppercase tracking-wider">Confidence</span>
          <span className="text-[11px] font-mono font-bold" style={{
            color: conf.pct && parseFloat(conf.pct) >= 85 ? "#10B981" : parseFloat(conf.pct || "0") >= 65 ? "#F59E0B" : "#EF4444"
          }}>
            {conf.pct || "—"}
          </span>
        </div>
        <div className="sq-confidence-bar">
          <div
            className="sq-confidence-fill"
            style={{ width: conf.pct || "0%" }}
          />
        </div>
      </div>

      {/* Answer preview */}
      {report.answer && (
        <div className="p-3 rounded-lg bg-[#0D1320] border border-[#1C2535]">
          <p className="text-[10px] text-[#687381] font-mono uppercase tracking-wider mb-1">Analysis Result</p>
          <p className="text-[11px] text-[#A7B0BD] leading-relaxed line-clamp-3">{report.answer}</p>
        </div>
      )}

      {/* Export actions */}
      <div className="pt-2 border-t border-[#1C2535] space-y-2 mt-auto">
        <p className="text-[10px] text-[#49576A] font-mono uppercase tracking-wider">Export Formats</p>
        <div className="grid grid-cols-2 gap-1.5">
          <a
            href={getReportHtmlUrl(reportId)}
            target="_blank" rel="noreferrer"
            className="sq-btn sq-btn-ghost text-[10px] py-2 justify-start gap-1.5"
          >
            <FileText className="w-3 h-3 text-cyan-400 flex-shrink-0" />
            HTML Report
          </a>
          <a
            href={getReportPdfUrl(reportId)}
            target="_blank" rel="noreferrer"
            className="sq-btn sq-btn-ghost text-[10px] py-2 justify-start gap-1.5"
          >
            <Download className="w-3 h-3 text-teal-400 flex-shrink-0" />
            PDF Report
          </a>
          <a
            href={getReportJsonUrl(reportId)}
            target="_blank" rel="noreferrer"
            className="sq-btn sq-btn-ghost text-[10px] py-2 justify-start gap-1.5"
          >
            <FileCode className="w-3 h-3 text-blue-400 flex-shrink-0" />
            JSON Schema
          </a>
          <a
            href={getReportPackageUrl(reportId)}
            download
            className="sq-btn sq-btn-primary text-[10px] py-2 justify-start gap-1.5"
          >
            <Package className="w-3 h-3 flex-shrink-0" />
            ZIP Package
          </a>
        </div>
        <Link
          href={`/analysis/${reportId}`}
          className="sq-btn sq-btn-secondary text-[10px] py-2 w-full justify-center"
        >
          <ExternalLink className="w-3 h-3" />
          View Full Analysis
        </Link>
      </div>
    </div>
  );
}

// ── Report List Item ──────────────────────────────────────────
function ReportListItem({
  report,
  isSelected,
  onClick,
}: {
  report: AnalysisHistoryItem;
  isSelected: boolean;
  onClick: () => void;
}) {
  const tc = getTaskConfig(report.task_type || report.task || "");
  const TaskIcon = tc.icon;
  const reportId = report.analysis_id || report.id;

  return (
    <button
      type="button"
      onClick={onClick}
      className={`
        w-full flex items-start gap-3 px-4 py-3 text-left transition-all
        border-b border-[#1C2535] last:border-0
        ${isSelected
          ? "bg-[#111821] border-l-2 border-l-cyan-500"
          : "hover:bg-[#0D1320]/50 border-l-2 border-l-transparent"
        }
      `}
    >
      <div
        className="flex-shrink-0 w-7 h-7 rounded-md flex items-center justify-center mt-0.5"
        style={{ background: `${tc.color}10`, border: `1px solid ${tc.color}22` }}
      >
        <TaskIcon className="w-3.5 h-3.5" style={{ color: tc.color }} />
      </div>
      <div className="flex-1 min-w-0">
        <p className={`text-[11px] font-medium leading-snug line-clamp-1 ${isSelected ? "text-white" : "text-[#A7B0BD]"}`}>
          {report.question || "Remote-sensing analysis"}
        </p>
        <p className="text-[9px] font-mono text-[#49576A] mt-0.5">
          {formatTaskTypeLabel(report.task_type || report.task)} · #{reportId.slice(0, 6)}
        </p>
        <p className="text-[9px] font-mono text-[#303B49] mt-0.5">
          {report.created_at ? new Date(report.created_at).toLocaleDateString() : "Recently"}
        </p>
      </div>
      <ChevronRight className={`w-3 h-3 flex-shrink-0 mt-1.5 transition-colors ${isSelected ? "text-cyan-400" : "text-[#25303D]"}`} />
    </button>
  );
}

// ── Export Format Cards ───────────────────────────────────────
const FORMAT_CARDS = [
  { icon: FileText, color: "#06B6D4", title: "Interactive HTML", desc: "Standalone offline document. Zero dependencies." },
  { icon: Download, color: "#14B8A6", title: "Publication PDF", desc: "ReportLab vector layout with ISRO SIH header." },
  { icon: FileCode, color: "#3B82F6", title: "Machine JSON", desc: "Pydantic-validated schema for GIS pipelines." },
  { icon: Package, color: "#8B5CF6", title: "ZIP Package", desc: "All formats + evidence artifacts + README." },
];

// ── Main Page ─────────────────────────────────────────────────
export default function ReportsLibraryPage() {
  const [reports, setReports] = useState<AnalysisHistoryItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState<string>("");

  useEffect(() => {
    async function loadReports() {
      try {
        setLoading(true);
        setError(null);
        const res = await getAnalysisHistory({ page: 1, page_size: 50, status: "COMPLETED" });
        const items = res.items || [];
        setReports(items);
        if (items.length > 0) setSelectedId(items[0].analysis_id || items[0].id);
      } catch (err: any) {
        setError(err?.message || "Failed to load reports");
      } finally {
        setLoading(false);
      }
    }
    loadReports();
  }, []);

  const filtered = reports.filter((r) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      (r.question || r.query || "").toLowerCase().includes(q) ||
      (r.task_type || r.task || "").toLowerCase().includes(q) ||
      (r.analysis_id || r.id || "").toLowerCase().includes(q)
    );
  });

  const selectedReport = filtered.find((r) => (r.analysis_id || r.id) === selectedId);

  return (
    <div className="space-y-5 pb-12">

      {/* ── Header ── */}
      <div className="flex items-center justify-between">
        <div>
          <span className="sq-section-label">Verifiable Intelligence Deliverables</span>
          <h1 className="text-xl font-bold text-white tracking-tight mt-0.5">
            Reports & Export Library
          </h1>
          <p className="text-[11px] text-[#687381] mt-0.5">
            Download publication-grade reports in HTML, PDF, JSON, and ZIP formats.
          </p>
        </div>
        <Link href="/analyze" className="sq-btn sq-btn-primary">
          <Sparkles className="w-3.5 h-3.5" />
          New Analysis
        </Link>
      </div>

      {/* ── Format overview ── */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-2.5">
        {FORMAT_CARDS.map((f) => (
          <div
            key={f.title}
            className="flex items-start gap-2.5 p-3 rounded-lg bg-[#111821] border border-[#1C2535]"
          >
            <div
              className="w-7 h-7 rounded-md flex items-center justify-center flex-shrink-0"
              style={{ background: `${f.color}12`, border: `1px solid ${f.color}25` }}
            >
              <f.icon className="w-3.5 h-3.5" style={{ color: f.color }} />
            </div>
            <div>
              <p className="text-[11px] font-semibold text-white">{f.title}</p>
              <p className="text-[9px] text-[#687381] leading-relaxed mt-0.5">{f.desc}</p>
            </div>
          </div>
        ))}
      </div>

      {/* ── Reports listing ── */}
      {loading ? (
        <div className="rounded-xl bg-[#111821] border border-[#1C2535] p-8 flex items-center justify-center">
          <div className="text-center space-y-2">
            <RefreshCw className="w-5 h-5 text-cyan-400 animate-spin mx-auto" />
            <p className="text-[11px] font-mono text-[#687381]">Scanning reports catalog…</p>
          </div>
        </div>
      ) : error ? (
        <div className="flex items-center gap-3 p-4 rounded-xl bg-rose-500/05 border border-rose-500/20 text-xs text-rose-300">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>Error loading reports: {error}</span>
        </div>
      ) : reports.length === 0 ? (
        <div className="flex flex-col items-center justify-center gap-4 py-16 rounded-xl border border-[#1C2535] border-dashed">
          <div className="w-12 h-12 rounded-full bg-[#111821] border border-[#25303D] flex items-center justify-center">
            <Package className="w-5 h-5 text-[#303B49]" />
          </div>
          <div className="text-center space-y-1">
            <p className="text-sm font-semibold text-white">No Reports Generated Yet</p>
            <p className="text-xs text-[#687381] max-w-xs">
              Complete an analysis to automatically generate exportable report packages.
            </p>
          </div>
          <Link href="/analyze" className="sq-btn sq-btn-primary">
            <Sparkles className="w-3.5 h-3.5" />
            Launch Analysis
          </Link>
        </div>
      ) : (
        <div className="flex gap-4 h-[560px]">
          {/* Left — Report list */}
          <div className="w-72 flex-shrink-0 rounded-xl bg-[#0D1320] border border-[#1C2535] flex flex-col overflow-hidden">
            {/* Search */}
            <div className="p-2.5 border-b border-[#1C2535]">
              <div className="relative">
                <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3 h-3 text-[#303B49]" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search reports…"
                  className="
                    w-full pl-7 pr-3 py-1.5 rounded-md text-[11px]
                    bg-[#111821] border border-[#1C2535] text-white
                    placeholder-[#303B49]
                    focus:outline-none focus:border-[#06B6D4]/40 transition
                  "
                />
              </div>
            </div>

            {/* List */}
            <div className="flex-1 overflow-y-auto">
              {filtered.length === 0 ? (
                <p className="text-[11px] text-[#49576A] text-center py-6">No reports match your search.</p>
              ) : (
                filtered.map((r) => (
                  <ReportListItem
                    key={r.id}
                    report={r}
                    isSelected={(r.analysis_id || r.id) === selectedId}
                    onClick={() => setSelectedId(r.analysis_id || r.id)}
                  />
                ))
              )}
            </div>

            <div className="px-4 py-2.5 border-t border-[#1C2535]">
              <p className="text-[9px] font-mono text-[#303B49]">{filtered.length} reports</p>
            </div>
          </div>

          {/* Right — Preview */}
          <div className="flex-1 rounded-xl bg-[#111821] border border-[#1C2535] overflow-y-auto">
            {selectedReport ? (
              <ReportPreview report={selectedReport} />
            ) : (
              <div className="flex items-center justify-center h-full text-[#49576A]">
                <div className="text-center space-y-2">
                  <FileText className="w-8 h-8 mx-auto opacity-30" />
                  <p className="text-[11px] font-mono">Select a report to preview</p>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
