"use client";

import React, { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  FileText,
  Download,
  AlertCircle,
  RefreshCw,
  Clock,
  Layers,
  Sparkles,
  ExternalLink,
  ShieldCheck,
} from "lucide-react";
import {
  getAnalysisDetail,
  getReportHtmlUrl,
  getReportPdfUrl,
  getReportPackageUrl,
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

export default function AnalysisDetailPage() {
  const params = useParams();
  const router = useRouter();
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

  if (loading) {
    return (
      <div className="py-20 text-center space-y-4">
        <RefreshCw className="h-8 w-8 text-cyan-400 animate-spin mx-auto" />
        <p className="text-sm text-slate-300 font-medium">Reconstructing analysis report from database store...</p>
        <p className="text-xs text-slate-500 font-mono">Job ID: {id}</p>
      </div>
    );
  }

  if (error || !analysis) {
    return (
      <div className="max-w-2xl mx-auto py-16 space-y-6 text-center">
        <div className="p-6 rounded-2xl bg-rose-950/20 border border-rose-800/40 text-rose-300 space-y-3">
          <AlertCircle className="h-10 w-10 text-rose-400 mx-auto" />
          <h2 className="text-lg font-bold">Analysis Job Not Found</h2>
          <p className="text-xs text-rose-300/80 leading-relaxed">
            {error || `No record exists for identifier "${id}". The job may have been cleared or the ID is invalid.`}
          </p>
        </div>

        <div className="flex items-center justify-center space-x-4">
          <Link
            href="/history"
            className="inline-flex items-center space-x-2 px-4 py-2 rounded-xl bg-slate-900 border border-slate-800 text-xs text-slate-300 hover:text-white"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            <span>Back to History</span>
          </Link>
          <Link
            href="/analyze"
            className="inline-flex items-center space-x-2 px-4 py-2 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-slate-950 font-bold text-xs"
          >
            <Sparkles className="h-3.5 w-3.5" />
            <span>Start New Analysis</span>
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

  return (
    <div className="space-y-8 pb-16">
      {/* Navigation & Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-6">
        <div className="space-y-2">
          <div className="flex items-center space-x-2 text-xs">
            <Link
              href="/history"
              className="inline-flex items-center space-x-1 text-slate-400 hover:text-slate-200 transition"
            >
              <ArrowLeft className="h-3.5 w-3.5" />
              <span>History</span>
            </Link>
            <span className="text-slate-600">/</span>
            <span className="font-mono text-cyan-400 text-[11px]">Job #{analysis.analysis_id}</span>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <h1 className="text-2xl sm:text-3xl font-black text-white tracking-tight">
              {formatTaskTypeLabel(analysis.task_type)}
            </h1>
            <span className="px-2.5 py-1 rounded-md bg-emerald-950/80 border border-emerald-800/60 text-emerald-300 font-mono text-xs">
              {analysis.status}
            </span>
            <span className={`px-2.5 py-1 rounded-md border text-xs font-medium ${conf.color}`}>
              {conf.label} ({conf.pct})
            </span>
          </div>

          <p className="text-xs text-slate-400 flex items-center space-x-3">
            <span>Created: {analysis.created_at ? new Date(analysis.created_at).toLocaleString() : "Recently"}</span>
            <span>·</span>
            <span>Duration: {analysis.execution_time_ms ? `${(analysis.execution_time_ms / 1000).toFixed(2)}s` : "N/A"}</span>
          </p>
        </div>

        {/* Multi-Format Export Action Bar */}
        <div className="flex flex-wrap items-center gap-2">
          <a
            href={getReportHtmlUrl(analysis.analysis_id)}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center space-x-1.5 px-3 py-2 rounded-xl bg-slate-900 border border-slate-700 hover:border-cyan-500 text-xs text-cyan-300 font-medium transition"
          >
            <FileText className="h-4 w-4" />
            <span>Interactive HTML</span>
          </a>

          <a
            href={getReportPdfUrl(analysis.analysis_id)}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center space-x-1.5 px-3 py-2 rounded-xl bg-slate-900 border border-slate-700 hover:border-teal-500 text-xs text-teal-300 font-medium transition"
          >
            <Download className="h-4 w-4" />
            <span>Formal PDF</span>
          </a>

          <a
            href={getReportPackageUrl(analysis.analysis_id)}
            download
            className="inline-flex items-center space-x-1.5 px-4 py-2 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-slate-950 font-bold text-xs transition"
          >
            <Download className="h-4 w-4" />
            <span>ZIP Deliverable</span>
          </a>
        </div>
      </div>

      {/* Primary Answer & Confidence Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
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

      {/* Input Ingestion Inspector */}
      {analysis.input_images && analysis.input_images.length > 0 && (
        <InputInspector images={analysis.input_images} />
      )}

      {/* Interactive Evidence Visualizer */}
      <EvidenceViewerUnified
        mode={viewerMode}
        primaryImageId={analysis.primary_image_id}
        primaryImageLabel={isTemporal ? "Epoch T1 Image" : isCrossModal ? "Cartosat-2S Optical" : "Observed Scene"}
        secondaryImageId={analysis.secondary_image_id}
        secondaryImageLabel={isTemporal ? "Epoch T2 Image" : "RISAT SAR Backscatter"}
        evidenceItems={analysis.evidence_items}
      />

      {/* Structured Observations Panel */}
      {analysis.observations && (
        <ObservationsPanel
          observedFacts={analysis.observations.observed_facts}
          modelInferences={analysis.observations.model_inferences}
          uncertainCues={analysis.observations.uncertain_cues}
        />
      )}

      {/* Execution and Model Details */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-6">
          <ModelDetails details={analysis.model_details} />
        </div>
        <div className="lg:col-span-6">
          <ExecutionSummary
            executionTimeMs={analysis.execution_time_ms}
            milestones={analysis.execution_milestones}
          />
        </div>
      </div>

      {/* Observable Agent Trace */}
      <TechnicalTrace traces={analysis.agent_traces} />
    </div>
  );
}
