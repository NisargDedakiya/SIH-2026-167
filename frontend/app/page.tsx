"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  Satellite,
  Sparkles,
  ArrowRight,
  Layers,
  GitCompare,
  Radio,
  Clock,
  CheckCircle2,
  AlertCircle,
  BarChart3,
  Target,
  MessageSquare,
  Cpu,
  ShieldCheck,
  Database,
  FileText,
  Zap,
} from "lucide-react";
import { getAnalysisHistory } from "@/lib/api";
import { AnalysisHistoryItem } from "@/lib/types";
import { formatConfidenceBadge, formatTaskTypeLabel } from "@/lib/presentation-utils";

// ── Capability data ───────────────────────────────────────────
const CAPABILITIES = [
  {
    icon: MessageSquare,
    label: "VQA",
    title: "Visual Question Answering",
    description: "Ask natural-language questions about satellite imagery. Fine-tuned on BigEarthNet v2.0.",
    href: "/analyze?task=vqa",
    accent: "#06B6D4",
    bg: "rgba(6,182,212,0.06)",
    border: "rgba(6,182,212,0.15)",
  },
  {
    icon: Target,
    label: "Grounding",
    title: "Spatial Object Grounding",
    description: "Text-prompted detection with pixel bounding boxes and CRS coordinates.",
    href: "/analyze?task=grounding",
    accent: "#10B981",
    bg: "rgba(16,185,129,0.06)",
    border: "rgba(16,185,129,0.15)",
  },
  {
    icon: GitCompare,
    label: "Change",
    title: "Bi-Temporal Analysis",
    description: "Non-destructive before/after comparison with NDVI heatmaps and change reporting.",
    href: "/temporal",
    accent: "#8B5CF6",
    bg: "rgba(139,92,246,0.06)",
    border: "rgba(139,92,246,0.15)",
  },
  {
    icon: Radio,
    label: "Fusion",
    title: "Optical + SAR Fusion",
    description: "Cartosat-2S and RISAT cross-modal analysis with disagreement detection.",
    href: "/cross-modal",
    accent: "#F59E0B",
    bg: "rgba(245,158,11,0.06)",
    border: "rgba(245,158,11,0.15)",
  },
];

// ── Example commands ──────────────────────────────────────────
const EXAMPLE_COMMANDS = [
  "What changed between these two images?",
  "Highlight all buildings in this scene.",
  "Compare optical and SAR imagery.",
  "What land-cover features are visible?",
  "Detect agricultural field boundaries.",
  "Estimate urban density in this satellite patch.",
];

// ── Task type badge config ────────────────────────────────────
function getTaskStyle(task: string) {
  const t = (task || "").toLowerCase();
  if (t.includes("grounding")) return { color: "#86EFAC", bg: "rgba(16,185,129,0.08)", label: "GND" };
  if (t.includes("temporal") || t.includes("change")) return { color: "#C4B5FD", bg: "rgba(139,92,246,0.08)", label: "CHG" };
  if (t.includes("cross") || t.includes("sar")) return { color: "#FCD34D", bg: "rgba(245,158,11,0.08)", label: "SAR" };
  if (t.includes("caption")) return { color: "#93C5FD", bg: "rgba(59,130,246,0.08)", label: "CAP" };
  return { color: "#67E8F9", bg: "rgba(6,182,212,0.08)", label: "VQA" };
}

// ── Recent Activity Item ──────────────────────────────────────
function ActivityItem({ item }: { item: AnalysisHistoryItem }) {
  const ts = getTaskStyle(item.task_type || item.task || "");
  const conf = formatConfidenceBadge(item.confidence_score);
  const itemId = item.analysis_id || item.id;
  const timeStr = item.created_at
    ? (() => {
        const diff = Date.now() - new Date(item.created_at).getTime();
        const mins = Math.floor(diff / 60000);
        if (mins < 1) return "just now";
        if (mins < 60) return `${mins}m ago`;
        const hrs = Math.floor(mins / 60);
        if (hrs < 24) return `${hrs}h ago`;
        return new Date(item.created_at).toLocaleDateString();
      })()
    : "recently";

  return (
    <Link
      href={`/analysis/${itemId}`}
      className="
        flex items-start gap-3 p-3.5 rounded-xl
        border border-[#1C2535] bg-[#111821]/50
        hover:border-[#25303D] hover:bg-[#151C26]/60
        transition-all group
      "
    >
      {/* Task badge */}
      <div
        className="flex-shrink-0 w-9 h-9 rounded-lg flex items-center justify-center text-[10px] font-mono font-bold"
        style={{ background: ts.bg, color: ts.color, border: `1px solid ${ts.color}30` }}
      >
        {ts.label}
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0 space-y-0.5">
        <p className="text-[12px] text-[#F2F5F8] font-medium line-clamp-1 group-hover:text-white transition-colors">
          {item.question || item.query || "Remote sensing analysis"}
        </p>
        <div className="flex items-center gap-2 text-[10px] font-mono text-[#687381]">
          <span>{formatTaskTypeLabel(item.task_type || item.task)}</span>
          <span>·</span>
          <span className={conf.color.split(" ")[2] ? conf.color.split(" ")[2] : "text-slate-400"}>
            {conf.pct}
          </span>
          <span>·</span>
          <span>{timeStr}</span>
        </div>
      </div>

      <ArrowRight className="w-3.5 h-3.5 text-[#303B49] group-hover:text-[#06B6D4] transition-colors flex-shrink-0 mt-1" />
    </Link>
  );
}

// ── Command Box ───────────────────────────────────────────────
function CommandBox() {
  const [exampleIdx, setExampleIdx] = useState(0);

  useEffect(() => {
    const iv = setInterval(() => {
      setExampleIdx((i) => (i + 1) % EXAMPLE_COMMANDS.length);
    }, 3200);
    return () => clearInterval(iv);
  }, []);

  return (
    <div className="relative max-w-2xl mx-auto">
      {/* Glow */}
      <div className="absolute -inset-px rounded-2xl bg-gradient-to-r from-cyan-600/20 via-transparent to-teal-600/10 blur-sm pointer-events-none" />

      <div className="relative rounded-2xl border border-[#25303D] bg-[#0D1320]/90 overflow-hidden">
        {/* Top bar */}
        <div className="flex items-center gap-2 px-4 py-2 border-b border-[#1C2535]">
          <Satellite className="w-3.5 h-3.5 text-cyan-400" />
          <span className="text-[10px] font-mono text-[#687381] uppercase tracking-widest">
            SatQuery Intelligence Engine
          </span>
          <div className="ml-auto flex items-center gap-1">
            <div className="w-2 h-2 rounded-full bg-[#303B49]" />
            <div className="w-2 h-2 rounded-full bg-[#303B49]" />
            <div className="w-2 h-2 rounded-full bg-cyan-500/60" />
          </div>
        </div>

        {/* Command area */}
        <div className="px-4 py-4">
          <p
            key={exampleIdx}
            className="text-sm text-[#A7B0BD] font-mono animate-fade-in min-h-[20px]"
          >
            <span className="text-cyan-400">›</span> {EXAMPLE_COMMANDS[exampleIdx]}
          </p>
        </div>

        {/* CTA */}
        <div className="px-4 py-3 bg-[#0B0F16] border-t border-[#1C2535] flex items-center justify-between">
          <span className="text-[10px] text-[#49576A] font-mono">
            VQA · Grounding · Temporal · SAR Fusion · Captioning
          </span>
          <Link
            href="/analyze"
            className="sq-btn sq-btn-primary text-[11px] px-4 py-1.5"
          >
            <Sparkles className="w-3 h-3" />
            Start Analysis
          </Link>
        </div>
      </div>
    </div>
  );
}

// ── Stats Bar ─────────────────────────────────────────────────
const STATS = [
  { label: "Analysis Engine", value: "Qwen2.5-VL", sub: "BigEarthNet LoRA Adapted" },
  { label: "Calibration", value: "Conformal", sub: "Prediction Scores" },
  { label: "Export Formats", value: "4 Formats", sub: "HTML · PDF · JSON · ZIP" },
  { label: "Benchmark", value: "VRSBench", sub: "Recall@0.5 Verified" },
];

// ── Main Page ─────────────────────────────────────────────────
export default function HomePage() {
  const [recentAnalyses, setRecentAnalyses] = useState<AnalysisHistoryItem[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(true);
  const [historyError, setHistoryError] = useState<string | null>(null);

  useEffect(() => {
    async function loadRecent() {
      try {
        setLoadingHistory(true);
        const data = await getAnalysisHistory({ page: 1, page_size: 6 });
        setRecentAnalyses(data.items || []);
      } catch (err: any) {
        setHistoryError(err?.message || "Could not load recent activity");
      } finally {
        setLoadingHistory(false);
      }
    }
    loadRecent();
  }, []);

  return (
    <div className="space-y-12 pb-12">

      {/* ── Hero ────────────────────────────────────── */}
      <section className="relative pt-8 pb-4">
        {/* Background accent */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[600px] h-[300px] bg-cyan-500/5 rounded-full blur-3xl pointer-events-none" />

        <div className="relative text-center space-y-5 max-w-3xl mx-auto">
          {/* Badge */}
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-[#0E1A24] border border-[#1D3040] text-[10px] font-mono text-cyan-300 shadow-sm">
            <div className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse" />
            <span>ISRO Smart India Hackathon · Problem Statement 26167</span>
          </div>

          {/* Headline */}
          <div className="space-y-2">
            <h1 className="text-4xl sm:text-5xl font-black text-white tracking-tight leading-[1.1]">
              Ask your imagery
              <br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-teal-300">
                anything.
              </span>
            </h1>
            <p className="text-sm sm:text-base text-[#A7B0BD] max-w-xl mx-auto leading-relaxed">
              Analyze satellite imagery with vision-language AI,
              change detection, spatial grounding, and multimodal reasoning.
            </p>
          </div>

          {/* Command interface */}
          <div className="pt-2">
            <CommandBox />
          </div>

          {/* Quick links */}
          <div className="flex flex-wrap items-center justify-center gap-2 pt-1">
            {[
              { href: "/history", label: "Analysis History", icon: Clock },
              { href: "/images", label: "Image Library", icon: Database },
              { href: "/reports", label: "Reports", icon: FileText },
              { href: "/evaluation", label: "Benchmarks", icon: BarChart3 },
            ].map(({ href, label, icon: Icon }) => (
              <Link
                key={href}
                href={href}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#111821] border border-[#25303D] text-[11px] text-[#A7B0BD] hover:text-white hover:border-[#303B49] hover:bg-[#151C26] transition-all"
              >
                <Icon className="w-3 h-3" />
                {label}
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* ── System Trust Indicators ──────────────────── */}
      <section>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          {STATS.map((s) => (
            <div
              key={s.label}
              className="px-4 py-3.5 rounded-xl bg-[#111821]/60 border border-[#1C2535] space-y-0.5"
            >
              <p className="text-[10px] text-[#687381] font-mono uppercase tracking-wider">{s.label}</p>
              <p className="text-sm font-bold text-white">{s.value}</p>
              <p className="text-[10px] text-[#A7B0BD]">{s.sub}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── Capabilities ─────────────────────────────── */}
      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-base font-bold text-white tracking-tight">Analysis Capabilities</h2>
            <p className="text-[11px] text-[#687381] mt-0.5 font-mono">
              Integrated remote-sensing intelligence verified across Phases 1–8
            </p>
          </div>
          <Link
            href="/analyze"
            className="flex items-center gap-1 text-[11px] text-cyan-400 hover:text-cyan-300 transition font-medium"
          >
            Open workspace
            <ArrowRight className="w-3 h-3" />
          </Link>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 sq-stagger">
          {CAPABILITIES.map((cap) => {
            const Icon = cap.icon;
            return (
              <Link
                key={cap.href}
                href={cap.href}
                className="group flex flex-col gap-3 p-4 rounded-xl border transition-all"
                style={{
                  background: cap.bg,
                  borderColor: cap.border,
                }}
              >
                <div className="flex items-center justify-between">
                  <div
                    className="w-8 h-8 rounded-lg flex items-center justify-center"
                    style={{ background: `${cap.accent}18`, border: `1px solid ${cap.accent}30` }}
                  >
                    <Icon className="w-4 h-4" style={{ color: cap.accent }} />
                  </div>
                  <span
                    className="text-[9px] font-mono font-bold tracking-widest uppercase px-1.5 py-0.5 rounded"
                    style={{ color: cap.accent, background: `${cap.accent}12` }}
                  >
                    {cap.label}
                  </span>
                </div>

                <div>
                  <h3 className="text-xs font-semibold text-white mb-1">{cap.title}</h3>
                  <p className="text-[11px] text-[#A7B0BD] leading-relaxed">{cap.description}</p>
                </div>

                <div
                  className="flex items-center gap-1 text-[10px] font-medium mt-auto opacity-70 group-hover:opacity-100 transition-opacity"
                  style={{ color: cap.accent }}
                >
                  <span>Launch</span>
                  <ArrowRight className="w-3 h-3" />
                </div>
              </Link>
            );
          })}
        </div>
      </section>

      {/* ── Recent Activity ───────────────────────────── */}
      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-base font-bold text-white tracking-tight">Recent Analyses</h2>
            <p className="text-[11px] text-[#687381] mt-0.5 font-mono">
              Live feed from persistent database
            </p>
          </div>
          <Link
            href="/history"
            className="flex items-center gap-1 text-[11px] text-cyan-400 hover:text-cyan-300 transition font-medium"
          >
            View all
            <ArrowRight className="w-3 h-3" />
          </Link>
        </div>

        {loadingHistory ? (
          <div className="space-y-2">
            {[0, 1, 2].map((i) => (
              <div key={i} className="h-16 rounded-xl sq-skeleton" />
            ))}
          </div>
        ) : historyError ? (
          <div className="flex items-center gap-3 p-4 rounded-xl bg-amber-500/5 border border-amber-500/20 text-xs text-amber-300">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            <span>Could not load recent activity: {historyError}</span>
          </div>
        ) : recentAnalyses.length === 0 ? (
          /* Empty state */
          <div className="flex flex-col items-center justify-center gap-4 py-14 rounded-xl border border-[#1C2535] border-dashed">
            <div className="w-12 h-12 rounded-full bg-[#111821] border border-[#25303D] flex items-center justify-center">
              <Satellite className="w-5 h-5 text-[#303B49]" />
            </div>
            <div className="text-center space-y-1">
              <p className="text-sm font-semibold text-white">No analyses yet</p>
              <p className="text-xs text-[#687381] max-w-xs">
                Upload satellite imagery and ask SatQuery your first question.
              </p>
            </div>
            <Link href="/analyze" className="sq-btn sq-btn-primary">
              <Sparkles className="w-3.5 h-3.5" />
              Start Analysis
            </Link>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
            {recentAnalyses.map((item) => (
              <ActivityItem key={item.id} item={item} />
            ))}
          </div>
        )}
      </section>

      {/* ── Trust Pillars ─────────────────────────────── */}
      <section>
        <div className="flex flex-wrap items-center justify-center gap-6 text-[11px] text-[#687381] py-4 border-t border-[#1C2535]">
          {[
            { icon: ShieldCheck, color: "#10B981", label: "Zero Data Fabrication" },
            { icon: CheckCircle2, color: "#06B6D4", label: "Calibrated Conformal Scores" },
            { icon: Database, color: "#14B8A6", label: "Reproducible Multi-Format Export" },
            { icon: Cpu, color: "#8B5CF6", label: "BigEarthNet Domain Adaptation" },
          ].map(({ icon: Icon, color, label }) => (
            <div key={label} className="flex items-center gap-1.5">
              <Icon className="w-3.5 h-3.5" style={{ color }} />
              <span>{label}</span>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
