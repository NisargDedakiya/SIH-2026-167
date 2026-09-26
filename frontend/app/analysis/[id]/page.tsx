"use client";

import React, { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  FileText,
  Download,
  AlertCircle,
  RefreshCw,
  Clock,
  Sparkles,
  Package,
  FileCode,
  ChevronDown,
  ChevronRight,
  Cpu,
  Shield,
  AlertTriangle,
  CheckCircle2,
  Info,
  Hash,
  Calendar,
  Timer,
  Activity,
} from "lucide-react";
import {
  getAnalysisDetail,
  getReportHtmlUrl,
  getReportPdfUrl,
  getReportPackageUrl,
  getReportJsonUrl,
} from "@/lib/api";
import { FullAnalysisDetail } from "@/lib/types";
import { formatTaskTypeLabel, formatConfidenceBadge } from "@/lib/presentation-utils";
import { AnalysisAnswer } from "@/components/analysis-answer";
import { ConfidenceCard } from "@/components/confidence-card";
import { EvidenceViewerUnified } from "@/components/evidence-viewer-unified";
import { InputInspector } from "@/components/input-inspector";
import { ObservationsPanel } from "@/components/observations-panel";
import { ModelDetails } from "@/components/model-details";
import { ExecutionSummary } from "@/components/execution-summary";
import { TechnicalTrace } from "@/components/technical-trace";

// ── Collapsible Section ───────────────────────────────────────
function CollapsibleSection({
  label,
  icon: Icon,
  defaultOpen = false,
  children,
  badge,
}: {
  label: string;
  icon: React.ElementType;
  defaultOpen?: boolean;
  children: React.ReactNode;
  badge?: string;
}) {
  const [open, setOpen] = useState(defaultOpen);

  return (
    <div className="rounded-xl bg-[#111821] border border-[#1C2535] overflow-hidden">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between px-4 py-3 hover:bg-[#151C26] transition-colors text-left"
        aria-expanded={open}
      >
        <div className="flex items-center gap-2">
          <Icon className="w-3.5 h-3.5 text-[#687381]" />
          <span className="text-[11px] font-semibold text-white uppercase tracking-wider">{label}</span>
          {badge && (
            <span className="px-1.5 py-0.5 rounded text-[9px] font-mono bg-[#1C2535] text-[#687381]">
              {badge}
            </span>
          )}
        </div>
        {open ? (
          <ChevronDown className="w-3.5 h-3.5 text-[#49576A]" />
        ) : (
          <ChevronRight className="w-3.5 h-3.5 text-[#49576A]" />
        )}
      </button>
      {open && (
        <div className="border-t border-[#1C2535] p-4 sq-animate-in">
          {children}
        </div>
      )}
    </div>
  );
}

// ── Meta pill ─────────────────────────────────────────────────
function MetaPill({ icon: Icon, label, value }: { icon: React.ElementType; label: string; value: string }) {
  return (
    <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-[#0D1320] border border-[#1C2535]">
      <Icon className="w-3.5 h-3.5 text-[#49576A] flex-shrink-0" />
      <div>
        <p className="text-[9px] text-[#49576A] font-mono uppercase">{label}</p>
        <p className="text-[11px] text-[#A7B0BD] font-mono">{value}</p>
      </div>
    </div>
  );
}

// ── Main Page ─────────────────────────────────────────────────
export default function AnalysisDetailPage() {
  const params = useParams();
  const id = params?.id as string;

  const [analysis, setAnalysis] = useState<FullAnalysisDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    async function loadData() {
      try {
        setLoading(true);
        setError(null);
        const data = await getAnalysisDetail(id);
        setAnalysis(data);
      } catch (err: any) {
        setError(err?.message || "Failed to load analysis details");
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [id]);

  // Loading
  if (loading) {
    return (
      <div className="space-y-4 pb-12">
        {/* Skeleton header */}
        <div className="h-8 sq-skeleton rounded-lg w-48" />
        <div className="h-12 sq-skeleton rounded-xl" />
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
          <div className="lg:col-span-8 h-40 sq-skeleton rounded-xl" />
          <div className="lg:col-span-4 h-40 sq-skeleton rounded-xl" />
        </div>
        <div className="h-64 sq-skeleton rounded-xl" />
      </div>
    );
  }

  // Error
  if (error || !analysis) {
    return (
      <div className="max-w-xl mx-auto py-16 space-y-5">
        <div className="p-5 rounded-xl bg-rose-500/05 border border-rose-500/20 space-y-3 text-center">
          <AlertCircle className="w-8 h-8 text-rose-400 mx-auto" />
          <h2 className="text-base font-bold text-white">Analysis Not Found</h2>
          <p className="text-[11px] text-rose-300/70 leading-relaxed font-mono">
            {error || `No record found for ID "${id}". The analysis may not exist or may have been cleared.`}
          </p>
        </div>
        <div className="flex items-center justify-center gap-3">
          <Link href="/history" className="sq-btn sq-btn-secondary">
            <ArrowLeft className="w-3.5 h-3.5" />
            Back to History
          </Link>
          <Link href="/analyze" className="sq-btn sq-btn-primary">
            <Sparkles className="w-3.5 h-3.5" />
            New Analysis
          </Link>
        </div>
      </div>
    );
  }

  const conf = formatConfidenceBadge(analysis.confidence_score ?? analysis.confidence);
  const taskType = (analysis.task_type || analysis.task || "").toLowerCase();
  const isTemporal = taskType.includes("temporal") || taskType.includes("change");
  const isCrossModal = taskType.includes("cross_modal") || taskType.includes("fusion");
  const viewerMode: "single" | "temporal" | "cross-modal" = isTemporal ? "temporal" : isCrossModal ? "cross-modal" : "single";

  const createdStr = analysis.created_at ? new Date(analysis.created_at).toLocaleString() : "—";
  const durationStr = analysis.execution_time_ms ? `${(analysis.execution_time_ms / 1000).toFixed(2)}s` : "—";
  const taskLabel = formatTaskTypeLabel(analysis.task_type);
  const statusOk = (analysis.status || "").toUpperCase() === "COMPLETED";

  return (
    <div className="space-y-5 pb-12 sq-animate-in">

      {/* ── Breadcrumb + Header ── */}
      <div className="space-y-3">
        {/* Breadcrumb */}
        <div className="flex items-center gap-1.5 text-[10px] font-mono text-[#49576A]">
          <Link href="/history" className="hover:text-[#A7B0BD] transition flex items-center gap-1">
            <ArrowLeft className="w-3 h-3" />
            History
          </Link>
          <span>/</span>
          <span className="text-cyan-400">{analysis.analysis_id.slice(0, 12)}</span>
        </div>

        {/* Title row */}
        <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
          <div className="space-y-2">
            <div className="flex flex-wrap items-center gap-2">
              <h1 className="text-xl font-bold text-white tracking-tight">{taskLabel}</h1>
              {/* Status */}
              <span
                className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[10px] font-mono font-semibold border ${
                  statusOk
                    ? "text-emerald-400 bg-emerald-500/08 border-emerald-500/20"
                    : "text-rose-400 bg-rose-500/08 border-rose-500/20"
                }`}
              >
                {statusOk ? <CheckCircle2 className="w-2.5 h-2.5" /> : <AlertTriangle className="w-2.5 h-2.5" />}
                {analysis.status}
              </span>
              {/* Confidence */}
              <span
                className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[10px] font-mono font-semibold border ${
                  conf.level === "HIGH"
                    ? "text-emerald-400 bg-emerald-500/08 border-emerald-500/20"
                    : conf.level === "MEDIUM"
                    ? "text-amber-400 bg-amber-500/08 border-amber-500/20"
                    : "text-rose-400 bg-rose-500/08 border-rose-500/20"
                }`}
              >
                {conf.pct} · {conf.level}
              </span>
            </div>

            {/* Meta row */}
            <div className="flex flex-wrap gap-2">
              <MetaPill icon={Hash} label="Analysis ID" value={analysis.analysis_id.slice(0, 16)} />
              <MetaPill icon={Calendar} label="Created" value={createdStr} />
              <MetaPill icon={Timer} label="Duration" value={durationStr} />
            </div>
          </div>

          {/* Export bar */}
          <div className="flex flex-wrap gap-1.5 flex-shrink-0">
            <a
              href={getReportHtmlUrl(analysis.analysis_id)}
              target="_blank" rel="noreferrer"
              className="sq-btn sq-btn-ghost text-[10px] py-2 text-cyan-400"
            >
              <FileText className="w-3 h-3" />
              HTML
            </a>
            <a
              href={getReportPdfUrl(analysis.analysis_id)}
              target="_blank" rel="noreferrer"
              className="sq-btn sq-btn-ghost text-[10px] py-2"
            >
              <Download className="w-3 h-3" />
              PDF
            </a>
            <a
              href={getReportJsonUrl(analysis.analysis_id)}
              target="_blank" rel="noreferrer"
              className="sq-btn sq-btn-ghost text-[10px] py-2 text-blue-400"
            >
              <FileCode className="w-3 h-3" />
              JSON
            </a>
            <a
              href={getReportPackageUrl(analysis.analysis_id)}
              download
              className="sq-btn sq-btn-primary text-[10px] py-2"
            >
              <Package className="w-3 h-3" />
              ZIP Package
            </a>
          </div>
        </div>
      </div>

      {/* ── Primary Answer + Confidence ── */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        <div className="lg:col-span-8">
          <AnalysisAnswer
            answer={analysis.answer}
            question={analysis.question}
            confidenceScore={analysis.confidence_score}
            confidenceLevel={analysis.confidence_level}
            taskType={analysis.task_type}
          />
        </div>
        <div className="lg:col-span-4">
          <ConfidenceCard
            score={analysis.confidence_score}
            level={analysis.confidence_level}
            method={analysis.confidence_method}
          />
        </div>
      </div>

      {/* ── Visual Evidence ── */}
      <EvidenceViewerUnified
        mode={viewerMode}
        primaryImageId={analysis.primary_image_id}
        primaryImageLabel={isTemporal ? "Epoch T1" : isCrossModal ? "Cartosat-2S Optical" : "Observed Scene"}
        secondaryImageId={analysis.secondary_image_id}
        secondaryImageLabel={isTemporal ? "Epoch T2" : "RISAT SAR Backscatter"}
        evidenceItems={analysis.evidence_items}
      />

      {/* ── Observations ── */}
      {analysis.observations && (
        <CollapsibleSection
          label="Observations"
          icon={Activity}
          defaultOpen={true}
          badge={`${(analysis.observations.observed_facts?.length || 0) + (analysis.observations.model_inferences?.length || 0)} items`}
        >
          <ObservationsPanel
            observedFacts={analysis.observations.observed_facts}
            modelInferences={analysis.observations.model_inferences}
            uncertainCues={analysis.observations.uncertain_cues}
          />
        </CollapsibleSection>
      )}

      {/* ── Input Data ── */}
      {analysis.input_images && analysis.input_images.length > 0 && (
        <CollapsibleSection
          label="Input Data"
          icon={Info}
          defaultOpen={false}
          badge={`${analysis.input_images.length} image${analysis.input_images.length !== 1 ? "s" : ""}`}
        >
          <InputInspector images={analysis.input_images} />
        </CollapsibleSection>
      )}

      {/* ── Model + Execution ── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <CollapsibleSection label="Model Details" icon={Cpu} defaultOpen={false}>
          <ModelDetails details={analysis.model_details} />
        </CollapsibleSection>
        <CollapsibleSection label="Execution Summary" icon={Timer} defaultOpen={false}>
          <ExecutionSummary
            executionTimeMs={analysis.execution_time_ms}
            milestones={analysis.execution_milestones}
          />
        </CollapsibleSection>
      </div>

      {/* ── Technical Trace ── */}
      {analysis.agent_traces && analysis.agent_traces.length > 0 && (
        <CollapsibleSection
          label="Execution Trace"
          icon={Shield}
          defaultOpen={false}
          badge={`${analysis.agent_traces.length} events`}
        >
          <TechnicalTrace traces={analysis.agent_traces} />
        </CollapsibleSection>
      )}
    </div>
  );
}
