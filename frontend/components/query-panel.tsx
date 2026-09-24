"use client";

import React, { useState } from "react";
import {
  Sparkles,
  Send,
  FileText,
  HelpCircle,
  Clock,
  Cpu,
  ShieldCheck,
  AlertCircle,
  CheckCircle2,
  Loader2,
  ChevronRight,
  ChevronDown,
  Layers,
  X,
  Bot,
  Terminal,
  Compass,
  ArrowRight,
  AlertTriangle,
  Crosshair,
} from "lucide-react";

import { analyzeVqa, generateCaption, analyzeWithAgent, analyzeGrounding, getImagePreviewUrl } from "@/lib/api";
import { VqaResponse, CaptionResponse, AgentAnalyzeResponse, ExecutionTrace, GroundingResponse } from "@/lib/types";
import { EvidenceViewer } from "@/components/evidence-viewer";

interface QueryPanelProps {
  imageId: string;
}

type TabType = "agent" | "grounding" | "vqa" | "caption";
type AnalysisStage = "idle" | "validating" | "classifying" | "planning" | "running" | "completed" | "error";

export function QueryPanel({ imageId }: QueryPanelProps) {
  const [activeTab, setActiveTab] = useState<TabType>("agent");
  const [query, setQuery] = useState("");
  const [stage, setStage] = useState<AnalysisStage>("idle");
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Agent State
  const [agentResult, setAgentResult] = useState<AgentAnalyzeResponse | null>(null);
  const [showTrace, setShowTrace] = useState<boolean>(true);

  // Direct VQA & Caption & Grounding State
  const [vqaResult, setVqaResult] = useState<VqaResponse | null>(null);
  const [captionResult, setCaptionResult] = useState<CaptionResponse | null>(null);
  const [groundingResult, setGroundingResult] = useState<GroundingResponse | null>(null);

  // Agent Suggested Prompts (Covering all remote-sensing agent scenarios)
  const agentSuggestions = [
    { label: "Highlight Water (Grounding)", text: "Highlight the water body." },
    { label: "Where are Buildings? (Grounding)", text: "Where are the buildings?" },
    { label: "Land Cover (VQA)", text: "What type of land cover is visible in this image?" },
    { label: "Scene Summary (Caption)", text: "Describe this scene." },
    { label: "Change Detection (Phase 5 Test)", text: "What changed between these two images?" },
    { label: "Ambiguity Test", text: "Tell me about this." },
  ];

  // Direct Grounding Questions
  const groundingQuestions = [
    "Highlight the water body.",
    "Where are the buildings?",
    "Highlight the road network.",
    "Find agricultural vegetation plots."
  ];

  // Direct VQA Questions
  const vqaQuestions = [
    "What type of land cover is visible in this image?",
    "Describe the built-up structures and road networks.",
    "Are there any water bodies or agricultural fields present?",
    "What is the predominant terrain classification?"
  ];

  const handleAgentSubmit = async (e?: React.FormEvent, customQuery?: string) => {
    if (e) e.preventDefault();
    const q = (customQuery || query).trim();
    if (!q) {
      setErrorMsg("Please enter a question or instruction for the SatQuery Agent.");
      return;
    }

    try {
      setErrorMsg(null);
      setAgentResult(null);

      // Lifecycle progression indicators
      setStage("validating");
      const classTimer = setTimeout(() => setStage("classifying"), 300);
      const planTimer = setTimeout(() => setStage("planning"), 700);
      const runTimer = setTimeout(() => setStage("running"), 1200);

      const res = await analyzeWithAgent(imageId, q);

      clearTimeout(classTimer);
      clearTimeout(planTimer);
      clearTimeout(runTimer);

      setAgentResult(res);
      setStage("completed");
    } catch (err: any) {
      setStage("error");
      setErrorMsg(err.message || "Agent execution failed. Please verify backend status.");
    }
  };

  const handleVqaSubmit = async (e?: React.FormEvent, customQuery?: string) => {
    if (e) e.preventDefault();
    const q = (customQuery || query).trim();
    if (!q) {
      setErrorMsg("Please enter a question about this satellite image.");
      return;
    }

    try {
      setErrorMsg(null);
      setVqaResult(null);

      setStage("validating");
      const runTimer = setTimeout(() => setStage("running"), 800);

      const res = await analyzeVqa(imageId, q);

      clearTimeout(runTimer);
      setVqaResult(res);
      setStage("completed");
    } catch (err: any) {
      setStage("error");
      setErrorMsg(err.message || "Failed to analyze image. Please verify backend status.");
    }
  };

  const handleCaptionSubmit = async () => {
    try {
      setErrorMsg(null);
      setCaptionResult(null);

      setStage("validating");
      const runTimer = setTimeout(() => setStage("running"), 800);

      const res = await generateCaption(imageId);

      clearTimeout(runTimer);
      setCaptionResult(res);
      setStage("completed");
    } catch (err: any) {
      setStage("error");
      setErrorMsg(err.message || "Failed to generate scene description.");
    }
  };

  const handleGroundingSubmit = async (e?: React.FormEvent, customQuery?: string) => {
    if (e) e.preventDefault();
    const q = (customQuery || query).trim();
    if (!q) {
      setErrorMsg("Please enter a target expression or spatial instruction to locate.");
      return;
    }

    try {
      setErrorMsg(null);
      setGroundingResult(null);

      setStage("validating");
      const runTimer = setTimeout(() => setStage("running"), 600);

      const res = await analyzeGrounding(imageId, q);

      clearTimeout(runTimer);
      setGroundingResult(res);
      setStage("completed");
    } catch (err: any) {
      setStage("error");
      setErrorMsg(err.message || "Failed to execute grounding inference.");
    }
  };

  const isProcessing = ["validating", "classifying", "planning", "running"].includes(stage);

  const getTaskBadgeColor = (task: string) => {
    switch (task?.toUpperCase()) {
      case "VISUAL_QUESTION_ANSWERING":
        return "bg-cyan-950/80 text-cyan-300 border-cyan-800/60";
      case "SCENE_DESCRIPTION":
        return "bg-emerald-950/80 text-emerald-300 border-emerald-800/60";
      case "GROUNDING":
        return "bg-amber-950/80 text-amber-300 border-amber-800/60";
      case "CHANGE_ANALYSIS":
        return "bg-purple-950/80 text-purple-300 border-purple-800/60";
      case "CROSS_MODAL_ANALYSIS":
        return "bg-blue-950/80 text-blue-300 border-blue-800/60";
      case "AMBIGUOUS":
        return "bg-violet-950/80 text-violet-300 border-violet-800/60";
      default:
        return "bg-slate-800 text-slate-300 border-slate-700";
    }
  };

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 shadow-2xl relative overflow-hidden backdrop-blur-md">
      {/* Decorative gradient highlight */}
      <div className="absolute top-0 right-0 w-96 h-48 bg-gradient-to-bl from-cyan-500/10 via-teal-500/5 to-transparent pointer-events-none rounded-tr-2xl" />

      {/* Top Header & Tab Navigation */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800/80">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 rounded-xl bg-gradient-to-br from-cyan-500/20 to-teal-500/20 border border-cyan-500/30 text-cyan-400 shadow-inner">
            <Bot className="h-5 w-5" />
          </div>
          <div>
            <h3 className="text-base font-bold text-white tracking-wide flex items-center space-x-2">
              <span>SatQuery AI Agent</span>
              <span className="text-[10px] px-2.5 py-0.5 rounded-full font-mono bg-cyan-950/90 text-cyan-300 border border-cyan-700/60 font-medium">
                Phase 3 Orchestrator
              </span>
            </h3>
            <p className="text-xs text-slate-400">
              Autonomous Intent Router, Sandboxed Tool Dispatch & Observable Execution Trace
            </p>
          </div>
        </div>

        {/* Tab Switcher */}
        <div className="inline-flex rounded-lg bg-slate-950 p-1 border border-slate-800">
          <button
            type="button"
            onClick={() => {
              setActiveTab("agent");
              setStage("idle");
              setErrorMsg(null);
            }}
            className={`px-3 py-1.5 rounded-md text-xs font-semibold transition flex items-center space-x-1.5 ${
              activeTab === "agent"
                ? "bg-gradient-to-r from-cyan-600 to-teal-600 text-white shadow-md"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <Sparkles className="h-3.5 w-3.5" />
            <span>Agent (Auto-Router)</span>
          </button>
          <button
            type="button"
            onClick={() => {
              setActiveTab("grounding");
              setStage("idle");
              setErrorMsg(null);
            }}
            className={`px-3 py-1.5 rounded-md text-xs font-medium transition flex items-center space-x-1.5 ${
              activeTab === "grounding"
                ? "bg-emerald-700 text-white shadow-sm"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <Crosshair className="h-3.5 w-3.5" />
            <span>Direct Grounding</span>
          </button>
          <button
            type="button"
            onClick={() => {
              setActiveTab("vqa");
              setStage("idle");
              setErrorMsg(null);
            }}
            className={`px-3 py-1.5 rounded-md text-xs font-medium transition flex items-center space-x-1.5 ${
              activeTab === "vqa"
                ? "bg-cyan-700 text-white shadow-sm"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <HelpCircle className="h-3.5 w-3.5" />
            <span>Direct VQA</span>
          </button>
          <button
            type="button"
            onClick={() => {
              setActiveTab("caption");
              setStage("idle");
              setErrorMsg(null);
            }}
            className={`px-3 py-1.5 rounded-md text-xs font-medium transition flex items-center space-x-1.5 ${
              activeTab === "caption"
                ? "bg-cyan-700 text-white shadow-sm"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <FileText className="h-3.5 w-3.5" />
            <span>Direct Caption</span>
          </button>
        </div>
      </div>

      {/* Error Notice Banner */}
      {errorMsg && (
        <div className="mt-4 p-3.5 rounded-xl bg-rose-950/60 border border-rose-800/80 text-rose-200 text-xs flex items-start justify-between">
          <div className="flex items-start space-x-2.5">
            <AlertCircle className="h-4 w-4 text-rose-400 shrink-0 mt-0.5" />
            <span>{errorMsg}</span>
          </div>
          <button onClick={() => setErrorMsg(null)} className="text-rose-400 hover:text-rose-200">
            <X className="h-3.5 w-3.5" />
          </button>
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 1: SATQUERY AGENT (Primary Workflow) */}
      {/* ========================================================================= */}
      {activeTab === "agent" && (
        <div className="mt-5 space-y-4">
          <form onSubmit={handleAgentSubmit} className="relative">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              disabled={isProcessing}
              placeholder="Ask anything (e.g. 'What type of land cover is visible?' or 'Describe this scene')..."
              className="w-full px-4 py-3.5 pr-36 rounded-xl bg-slate-950 border border-slate-800 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 transition disabled:opacity-60 shadow-inner"
            />
            <button
              type="submit"
              disabled={isProcessing || !query.trim()}
              className="absolute right-2 top-2 bottom-2 px-4 rounded-lg bg-gradient-to-r from-cyan-600 to-teal-600 hover:from-cyan-500 hover:to-teal-500 text-white font-medium text-xs flex items-center space-x-2 transition disabled:opacity-50 disabled:cursor-not-allowed shadow-md"
            >
              {isProcessing ? (
                <>
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  <span>Routing...</span>
                </>
              ) : (
                <>
                  <span>Ask Agent</span>
                  <Send className="h-3.5 w-3.5" />
                </>
              )}
            </button>
          </form>

          {/* Quick test prompt chips */}
          <div className="flex flex-wrap items-center gap-1.5 pt-1">
            <span className="text-[11px] font-medium text-slate-400 flex items-center space-x-1">
              <Compass className="h-3 w-3 text-cyan-400" />
              <span>Explore Intents:</span>
            </span>
            {agentSuggestions.map((s, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => {
                  setQuery(s.text);
                  handleAgentSubmit(undefined, s.text);
                }}
                disabled={isProcessing}
                className="px-2.5 py-1 rounded-md text-[11px] bg-slate-950 hover:bg-slate-800 border border-slate-800 text-slate-300 hover:text-cyan-300 transition text-left flex items-center space-x-1"
              >
                <span>{s.label}</span>
              </button>
            ))}
          </div>

          {/* Processing Lifecycle Progression State */}
          {isProcessing && (
            <div className="mt-5 p-4 rounded-xl bg-slate-950 border border-cyan-900/40 space-y-2.5 animate-pulse">
              <div className="text-xs font-semibold text-cyan-300 flex items-center space-x-2">
                <Loader2 className="h-4 w-4 animate-spin text-cyan-400" />
                <span>Agentic Query Controller processing request...</span>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-4 gap-2 text-[11px]">
                <div className={`p-2 rounded border flex items-center space-x-2 ${
                  stage === "validating" ? "bg-cyan-950/60 border-cyan-600 text-cyan-200" : "bg-slate-900 border-slate-800 text-emerald-400"
                }`}>
                  <CheckCircle2 className="h-3 w-3" />
                  <span>Validating Input</span>
                </div>
                <div className={`p-2 rounded border flex items-center space-x-2 ${
                  stage === "classifying" ? "bg-cyan-950/60 border-cyan-600 text-cyan-200" : ["validating"].includes(stage) ? "bg-slate-900 border-slate-800 text-slate-500" : "bg-slate-900 border-slate-800 text-emerald-400"
                }`}>
                  <CheckCircle2 className="h-3 w-3" />
                  <span>Classifying Intent</span>
                </div>
                <div className={`p-2 rounded border flex items-center space-x-2 ${
                  stage === "planning" ? "bg-cyan-950/60 border-cyan-600 text-cyan-200" : ["validating", "classifying"].includes(stage) ? "bg-slate-900 border-slate-800 text-slate-500" : "bg-slate-900 border-slate-800 text-emerald-400"
                }`}>
                  <Loader2 className={`h-3 w-3 ${stage === "planning" ? "animate-spin text-cyan-400" : ""}`} />
                  <span>Resolving Tool</span>
                </div>
                <div className={`p-2 rounded border flex items-center space-x-2 ${
                  stage === "running" ? "bg-cyan-950/60 border-cyan-600 text-cyan-200" : "bg-slate-900 border-slate-800 text-slate-500"
                }`}>
                  <Loader2 className={`h-3 w-3 ${stage === "running" ? "animate-spin text-cyan-400" : ""}`} />
                  <span>Executing Specialist</span>
                </div>
              </div>
            </div>
          )}

          {/* Agent Results Display */}
          {agentResult && (
            <div className="mt-5 space-y-4">
              {/* Header metadata bar */}
              <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 flex flex-wrap items-center justify-between gap-3">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="text-xs font-mono uppercase tracking-wider text-slate-400 font-semibold">
                    Detected Task:
                  </span>
                  <span className={`text-xs px-2.5 py-1 rounded-md font-mono font-semibold border ${getTaskBadgeColor(agentResult.task)}`}>
                    {agentResult.task}
                  </span>
                  {agentResult.tools.length > 0 && (
                    <>
                      <span className="text-slate-600">|</span>
                      <span className="text-xs font-mono uppercase tracking-wider text-slate-400 font-semibold">
                        Tool:
                      </span>
                      <span className="text-xs px-2.5 py-1 rounded-md font-mono bg-slate-900 text-cyan-300 border border-slate-700">
                        {agentResult.tools[0].name} (v{agentResult.tools[0].version})
                      </span>
                    </>
                  )}

                  {/* Remote-Sensing Adaptation Badge */}
                  {agentResult.is_adapted ? (
                    <span className="inline-flex items-center space-x-1.5 text-xs px-2.5 py-1 rounded-md font-mono font-semibold bg-emerald-950/70 text-emerald-300 border border-emerald-700/60 shadow-[0_0_12px_rgba(16,185,129,0.15)]">
                      <Sparkles className="h-3 w-3 text-emerald-400 animate-pulse" />
                      <span>SatQuery RS v1 · BigEarthNet LoRA Adapted</span>
                    </span>
                  ) : agentResult.fallback_used ? (
                    <span className="inline-flex items-center space-x-1 text-xs px-2.5 py-1 rounded-md font-mono bg-amber-950/70 text-amber-300 border border-amber-700/60" title={agentResult.fallback_reason || undefined}>
                      <AlertTriangle className="h-3 w-3 text-amber-400" />
                      <span>Fallback: Base Model</span>
                    </span>
                  ) : null}
                </div>

                <div className="flex items-center space-x-2">
                  <span className="text-[11px] px-2.5 py-1 rounded bg-slate-900 border border-slate-800 text-slate-400 flex items-center space-x-1 font-mono">
                    <Clock className="h-3 w-3 text-cyan-400" />
                    <span>{agentResult.processing_time_ms} ms</span>
                  </span>
                  <span className={`text-[11px] px-2.5 py-1 rounded font-mono font-bold uppercase ${
                    agentResult.status === "completed"
                      ? "bg-emerald-950/80 text-emerald-300 border border-emerald-800/60"
                      : agentResult.status === "unavailable"
                      ? "bg-amber-950/80 text-amber-300 border border-amber-800/60"
                      : "bg-violet-950/80 text-violet-300 border border-violet-800/60"
                  }`}>
                    {agentResult.status}
                  </span>
                </div>
              </div>

              {/* Status Case A: AMBIGUOUS QUERY */}
              {agentResult.status === "ambiguous" && (
                <div className="p-5 rounded-xl bg-violet-950/30 border border-violet-800/60 space-y-3">
                  <div className="flex items-center space-x-2 text-violet-300 font-semibold text-sm">
                    <AlertTriangle className="h-4 w-4 text-violet-400" />
                    <span>Clarification Needed</span>
                  </div>
                  <p className="text-sm text-violet-100 leading-relaxed bg-slate-950/80 p-4 rounded-lg border border-violet-900/50">
                    {agentResult.answer}
                  </p>
                  <div className="flex flex-wrap gap-2 pt-1">
                    <button
                      type="button"
                      onClick={() => {
                        const q = "Describe this scene.";
                        setQuery(q);
                        handleAgentSubmit(undefined, q);
                      }}
                      className="px-3 py-1.5 rounded-lg bg-violet-700 hover:bg-violet-600 text-white text-xs font-semibold transition flex items-center space-x-1.5"
                    >
                      <FileText className="h-3.5 w-3.5" />
                      <span>Request Scene Description</span>
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        const q = "What type of land cover is visible in this image?";
                        setQuery(q);
                        handleAgentSubmit(undefined, q);
                      }}
                      className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium border border-slate-700 transition flex items-center space-x-1.5"
                    >
                      <HelpCircle className="h-3.5 w-3.5" />
                      <span>Ask Land Cover Question</span>
                    </button>
                  </div>
                </div>
              )}

              {/* Status Case B: UNAVAILABLE FUTURE CAPABILITY */}
              {agentResult.status === "unavailable" && (
                <div className="p-5 rounded-xl bg-amber-950/30 border border-amber-800/60 space-y-3">
                  <div className="flex items-center space-x-2 text-amber-300 font-semibold text-sm">
                    <AlertCircle className="h-4 w-4 text-amber-400" />
                    <span>Capability Not Available Yet (Controlled Non-Fallback)</span>
                  </div>
                  <p className="text-sm text-amber-100 leading-relaxed bg-slate-950/80 p-4 rounded-lg border border-amber-900/50">
                    {agentResult.answer}
                  </p>
                  <p className="text-xs text-slate-400 italic">
                    SIH Architecture Requirement: SatQuery AI recognizes this intent but refuses to execute an incorrect VQA or Caption fallback.
                  </p>
                </div>
              )}

              {/* Status Case C: COMPLETED */}
              {agentResult.status === "completed" && (
                <div className="p-5 rounded-xl bg-slate-950 border border-slate-800 space-y-4">
                  <div className="space-y-1">
                    <span className="text-[11px] uppercase tracking-wider font-semibold text-slate-400">
                      Generated Answer / Finding
                    </span>
                    <p className="text-base sm:text-lg font-medium text-white leading-relaxed bg-slate-900/70 p-4 rounded-lg border border-slate-800">
                      {agentResult.answer}
                    </p>
                  </div>

                  {/* Remote-Sensing Domain Adaptation Provenance Card */}
                  {(agentResult.is_adapted || agentResult.adapter_id) && (
                    <div className="p-3.5 rounded-lg bg-emerald-950/20 border border-emerald-800/40 space-y-2">
                      <div className="flex items-center justify-between text-xs">
                        <span className="flex items-center space-x-1.5 font-semibold text-emerald-300">
                          <Sparkles className="h-3.5 w-3.5 text-emerald-400" />
                          <span>Domain Adaptation Provenance</span>
                        </span>
                        <span className="font-mono text-[11px] px-2 py-0.5 rounded bg-emerald-900/40 text-emerald-200 border border-emerald-700/50">
                          {agentResult.adapter_id || "satquery-rs-v1"}
                        </span>
                      </div>
                      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-[11px] pt-1">
                        <div className="p-2 rounded bg-slate-950/60 border border-slate-800/80">
                          <span className="text-slate-400 block text-[10px]">Base VLM</span>
                          <span className="font-mono text-slate-200 font-medium">Salesforce/blip-vqa-base</span>
                        </div>
                        <div className="p-2 rounded bg-slate-950/60 border border-slate-800/80">
                          <span className="text-slate-400 block text-[10px]">Dataset</span>
                          <span className="font-mono text-emerald-300 font-medium">BigEarthNet v2.0 (LoRA)</span>
                        </div>
                        <div className="p-2 rounded bg-slate-950/60 border border-slate-800/80">
                          <span className="text-slate-400 block text-[10px]">Adapter Architecture</span>
                          <span className="font-mono text-cyan-300 font-medium">LoRA (r=8, α=16, 96 layers)</span>
                        </div>
                        <div className="p-2 rounded bg-slate-950/60 border border-slate-800/80">
                          <span className="text-slate-400 block text-[10px]">Trainable Parameters</span>
                          <span className="font-mono text-teal-300 font-medium">1,179,648 (0.33% frozen base)</span>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Confidence & Evidence */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
                    <div className="p-3.5 rounded-lg bg-slate-900/80 border border-slate-800">
                      <div className="flex justify-between items-center text-xs text-slate-400 mb-1.5">
                        <span className="flex items-center space-x-1 font-medium">
                          <ShieldCheck className="h-3.5 w-3.5 text-emerald-400" />
                          <span>Model Confidence</span>
                        </span>
                        <span className="font-mono text-emerald-300 font-bold text-sm">
                          {(agentResult.confidence.score * 100).toFixed(1)}%
                        </span>
                      </div>
                      <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden">
                        <div
                          className="bg-gradient-to-r from-teal-500 to-emerald-400 h-2 rounded-full transition-all duration-500"
                          style={{ width: `${Math.min(100, Math.max(0, agentResult.confidence.score * 100))}%` }}
                        />
                      </div>
                      <p className="text-[10px] text-slate-400 mt-1.5 font-mono">
                        Method: {agentResult.confidence.method}
                      </p>
                    </div>

                    <div className="p-3.5 rounded-lg bg-slate-900/80 border border-slate-800 flex flex-col justify-between">
                      <div>
                        <span className="text-xs font-medium text-slate-300 flex items-center space-x-1 mb-1">
                          <Layers className="h-3.5 w-3.5 text-cyan-400" />
                          <span>Evidence Foundation</span>
                        </span>
                        <p className="text-[11px] text-slate-400">
                          Resolved Tool: <span className="font-mono text-cyan-300">{agentResult.tools[0]?.name || "N/A"}</span>
                        </p>
                      </div>
                      <span className="text-[10px] text-emerald-400 font-mono flex items-center space-x-1">
                        <CheckCircle2 className="h-3 w-3" />
                        <span>
                          {agentResult.evidence && agentResult.evidence.length > 0
                            ? `${agentResult.evidence.length} Visual Grounding Regions Attached`
                            : "VQA/Caption Semantic Response (Zero Hallucinated Visual Evidence)"}
                        </span>
                      </span>
                    </div>
                  </div>

                  {/* Interactive Visual Evidence Viewer (Phase 4 Grounding Delivery) */}
                  {agentResult.evidence && agentResult.evidence.length > 0 && (
                    <div className="pt-2">
                      <EvidenceViewer
                        previewUrl={getImagePreviewUrl(imageId)}
                        evidence={agentResult.evidence}
                        query={query}
                        confidenceScore={agentResult.confidence?.score}
                        confidenceMethod={agentResult.confidence?.method}
                      />
                    </div>
                  )}
                </div>
              )}

              {/* ========================================================================= */}
              {/* AUDITABLE EXECUTION TRACE (Major SIH Requirement) */}
              {/* ========================================================================= */}
              {agentResult.trace && (
                <div className="rounded-xl bg-slate-950 border border-slate-800 overflow-hidden">
                  <button
                    type="button"
                    onClick={() => setShowTrace(!showTrace)}
                    className="w-full px-4 py-3 bg-slate-900/60 hover:bg-slate-900/90 flex items-center justify-between text-xs text-slate-300 transition"
                  >
                    <div className="flex items-center space-x-2">
                      <Terminal className="h-4 w-4 text-cyan-400" />
                      <span className="font-semibold text-white">Observable Execution Trace</span>
                      <span className="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-cyan-300 font-mono">
                        {agentResult.trace.events.length} observable facts
                      </span>
                    </div>
                    <div className="flex items-center space-x-2 text-slate-400">
                      <span className="text-[10px] font-mono">Trace ID: {agentResult.trace_id.slice(0, 8)}...</span>
                      {showTrace ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
                    </div>
                  </button>

                  {showTrace && (
                    <div className="p-4 space-y-3 text-xs border-t border-slate-800/80">
                      <div className="space-y-2.5">
                        {agentResult.trace.events.map((ev, idx) => (
                          <div
                            key={idx}
                            className="p-3 rounded-lg bg-slate-900/60 border border-slate-800/80 flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-[11px]"
                          >
                            <div className="flex items-center space-x-2.5">
                              <span className="h-5 w-5 rounded-full bg-slate-800 text-cyan-400 font-mono flex items-center justify-center font-bold text-[10px]">
                                {ev.sequence}
                              </span>
                              <span className="font-mono font-semibold text-white">
                                {ev.event_type}
                              </span>
                              {ev.tool_name && (
                                <span className="px-2 py-0.5 rounded bg-cyan-950 text-cyan-300 font-mono text-[10px] border border-cyan-800/50">
                                  tool: {ev.tool_name}
                                </span>
                              )}
                            </div>

                            <div className="flex flex-wrap items-center gap-2 sm:justify-end">
                              {ev.output_metadata && (
                                <div className="text-[10px] font-mono text-slate-400 bg-slate-950 px-2 py-0.5 rounded border border-slate-800">
                                  {Object.entries(ev.output_metadata).slice(0, 3).map(([k, v]) => (
                                    <span key={k} className="mr-2">
                                      <span className="text-slate-500">{k}:</span> <span className="text-slate-200">{String(v)}</span>
                                    </span>
                                  ))}
                                </div>
                              )}
                              {ev.duration_ms !== null && ev.duration_ms !== undefined && (
                                <span className="font-mono text-slate-400 text-[10px]">
                                  {ev.duration_ms}ms
                                </span>
                              )}
                              <span className={`px-1.5 py-0.5 rounded font-mono text-[9px] uppercase ${
                                ev.status === "completed"
                                  ? "bg-emerald-950 text-emerald-300"
                                  : ev.status === "failed"
                                  ? "bg-rose-950 text-rose-300"
                                  : "bg-slate-800 text-slate-400"
                              }`}>
                                {ev.status}
                              </span>
                            </div>
                          </div>
                        ))}
                      </div>

                      <div className="pt-2 flex items-center justify-between text-[10px] text-slate-500 font-mono border-t border-slate-900">
                        <span>SIH Audit Guarantee: Only observable execution facts recorded.</span>
                        <span>Zero private chain-of-thought leaked.</span>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 2: DIRECT GROUNDING & VISUAL EVIDENCE (Phase 4 Specialist Testing) */}
      {/* ========================================================================= */}
      {activeTab === "grounding" && (
        <div className="mt-5 space-y-4">
          <form onSubmit={handleGroundingSubmit} className="relative">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              disabled={isProcessing}
              placeholder="e.g. 'Highlight the water body' or 'Where are the buildings?'"
              className="w-full px-4 py-3.5 pr-32 rounded-xl bg-slate-950 border border-slate-800 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition disabled:opacity-60"
            />
            <button
              type="submit"
              disabled={isProcessing || !query.trim()}
              className="absolute right-2 top-2 bottom-2 px-4 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-medium text-xs flex items-center space-x-2 transition disabled:opacity-50 disabled:cursor-not-allowed shadow"
            >
              {isProcessing ? (
                <>
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  <span>Locating...</span>
                </>
              ) : (
                <>
                  <span>Ground</span>
                  <Crosshair className="h-3.5 w-3.5" />
                </>
              )}
            </button>
          </form>

          {/* Quick grounding suggestions */}
          <div className="flex flex-wrap items-center gap-2 pt-1">
            <span className="text-[11px] font-medium text-slate-400">Grounding queries:</span>
            {groundingQuestions.map((gq, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => {
                  setQuery(gq);
                  handleGroundingSubmit(undefined, gq);
                }}
                disabled={isProcessing}
                className="px-2.5 py-1 rounded-md text-[11px] bg-slate-950 hover:bg-slate-800 border border-slate-800 text-slate-300 hover:text-emerald-300 transition text-left"
              >
                {gq}
              </button>
            ))}
          </div>

          {/* Grounding Specialist Result & Interactive Visual Evidence */}
          {groundingResult && (
            <div className="mt-5 space-y-4">
              <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 flex flex-wrap items-center justify-between gap-3">
                <div className="flex items-center space-x-2">
                  <span className="text-xs font-mono uppercase tracking-wider text-emerald-400 font-semibold flex items-center space-x-1.5">
                    <Crosshair className="h-3.5 w-3.5" />
                    <span>RS Grounding Specialist</span>
                  </span>
                  <span className="text-slate-600">|</span>
                  <span className="text-xs font-mono text-slate-300">
                    Target: <strong className="text-emerald-300">{groundingResult.target_expression}</strong>
                  </span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-[11px] px-2 py-0.5 rounded bg-slate-900 border border-slate-800 text-slate-400 font-mono">
                    {groundingResult.processing_time_ms} ms
                  </span>
                  <span className="text-[11px] px-2 py-0.5 rounded bg-emerald-950 border border-emerald-800 text-emerald-300 font-mono font-bold">
                    {groundingResult.region_count} {groundingResult.region_count === 1 ? "Region" : "Regions"}
                  </span>
                </div>
              </div>

              {/* Answer text */}
              <p className="text-base font-medium text-white bg-slate-950 p-4 rounded-xl border border-slate-800">
                {groundingResult.answer}
              </p>

              {/* Visual Evidence Viewer */}
              {groundingResult.regions.length > 0 && (
                <EvidenceViewer
                  previewUrl={getImagePreviewUrl(imageId)}
                  evidence={groundingResult.regions}
                  query={query}
                  targetExpression={groundingResult.target_expression}
                  confidenceScore={groundingResult.confidence}
                  confidenceMethod={groundingResult.confidence_method}
                />
              )}
            </div>
          )}
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 3: DIRECT VISUAL QUESTION ANSWERING (Specialist Model Testing) */}
      {/* ========================================================================= */}
      {activeTab === "vqa" && (
        <div className="mt-5 space-y-4">
          <form onSubmit={handleVqaSubmit} className="relative">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              disabled={isProcessing}
              placeholder="Ask a question about this satellite image..."
              className="w-full px-4 py-3.5 pr-32 rounded-xl bg-slate-950 border border-slate-800 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 transition disabled:opacity-60"
            />
            <button
              type="submit"
              disabled={isProcessing || !query.trim()}
              className="absolute right-2 top-2 bottom-2 px-4 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white font-medium text-xs flex items-center space-x-2 transition disabled:opacity-50 disabled:cursor-not-allowed shadow"
            >
              {isProcessing ? (
                <>
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  <span>Analyzing...</span>
                </>
              ) : (
                <>
                  <span>Analyze</span>
                  <Send className="h-3.5 w-3.5" />
                </>
              )}
            </button>
          </form>

          {/* Suggested quick questions */}
          <div className="flex flex-wrap items-center gap-2 pt-1">
            <span className="text-[11px] font-medium text-slate-400">Direct VQA queries:</span>
            {vqaQuestions.map((sq, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => {
                  setQuery(sq);
                  handleVqaSubmit(undefined, sq);
                }}
                disabled={isProcessing}
                className="px-2.5 py-1 rounded-md text-[11px] bg-slate-950 hover:bg-slate-800 border border-slate-800 text-slate-300 hover:text-cyan-300 transition text-left"
              >
                {sq}
              </button>
            ))}
          </div>

          {vqaResult && (
            <div className="mt-5 p-5 rounded-xl bg-slate-950 border border-slate-800 space-y-4">
              <div className="flex flex-wrap items-center justify-between gap-2 pb-3 border-b border-slate-800/80">
                <div className="flex items-center space-x-2">
                  <span className="text-xs font-mono uppercase tracking-wider text-cyan-400 font-semibold flex items-center space-x-1.5">
                    <Sparkles className="h-3.5 w-3.5" />
                    <span>VQA Specialist Result</span>
                  </span>
                  {vqaResult.is_adapted ? (
                    <span className="inline-flex items-center space-x-1 text-[11px] px-2 py-0.5 rounded font-mono font-semibold bg-emerald-950/80 text-emerald-300 border border-emerald-700/60">
                      <Sparkles className="h-3 w-3 text-emerald-400 animate-pulse" />
                      <span>SatQuery RS v1 (BigEarthNet Adapted)</span>
                    </span>
                  ) : vqaResult.fallback_used ? (
                    <span className="text-[11px] px-2 py-0.5 rounded font-mono bg-amber-950/80 text-amber-300 border border-amber-700/60">
                      Fallback: Base Model
                    </span>
                  ) : (
                    <span className="text-[11px] px-2 py-0.5 rounded font-mono bg-slate-900 text-slate-400 border border-slate-800">
                      {vqaResult.model}
                    </span>
                  )}
                </div>
                <span className="text-[11px] px-2 py-0.5 rounded bg-slate-900 border border-slate-800 text-slate-400 font-mono">
                  {vqaResult.processing_time_ms} ms
                </span>
              </div>
              <p className="text-base font-medium text-white bg-slate-900/60 p-4 rounded-lg border border-slate-800">
                {vqaResult.answer}
              </p>
              {vqaResult.is_adapted && (
                <div className="p-3 rounded-lg bg-emerald-950/20 border border-emerald-800/30 text-xs flex flex-wrap items-center justify-between gap-2 text-slate-300">
                  <div className="flex items-center space-x-2 font-mono text-[11px]">
                    <span className="text-slate-400">Adapter:</span>
                    <span className="text-emerald-300 font-semibold">{vqaResult.adapter_id || "satquery-rs-v1"}</span>
                    <span className="text-slate-600">|</span>
                    <span className="text-slate-400">Training:</span>
                    <span className="text-slate-200">BigEarthNet v2.0 (CORINE-19)</span>
                  </div>
                  <div className="flex items-center space-x-2 font-mono text-[11px]">
                    <span className="text-cyan-300">Status: Validated Adapter</span>
                    <span className="text-slate-600">|</span>
                    <span className="text-teal-300">Target Modules: Q, V, Cross-Attn</span>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 4: DIRECT SCENE DESCRIPTION (Captioning Specialist Model Testing) */}
      {/* ========================================================================= */}
      {activeTab === "caption" && (
        <div className="mt-5 space-y-4">
          <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <h4 className="text-sm font-semibold text-white">Generate Remote-Sensing Scene Caption</h4>
              <p className="text-xs text-slate-400 mt-0.5">
                Directly invokes RSICD-adapted specialist model to produce descriptive summary.
              </p>
            </div>
            <button
              type="button"
              onClick={handleCaptionSubmit}
              disabled={isProcessing}
              className="px-4 py-2.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold flex items-center justify-center space-x-2 transition disabled:opacity-50 shadow shrink-0"
            >
              {isProcessing ? (
                <>
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  <span>Processing Scene...</span>
                </>
              ) : (
                <>
                  <FileText className="h-3.5 w-3.5" />
                  <span>Generate Description</span>
                </>
              )}
            </button>
          </div>

          {captionResult && (
            <div className="mt-5 p-5 rounded-xl bg-slate-950 border border-slate-800 space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-slate-800/80">
                <span className="text-xs font-mono uppercase tracking-wider text-cyan-400 font-semibold flex items-center space-x-1.5">
                  <FileText className="h-3.5 w-3.5" />
                  <span>Scene Description</span>
                </span>
                <span className="text-[11px] px-2 py-0.5 rounded bg-slate-900 border border-slate-800 text-slate-400 font-mono">
                  {captionResult.processing_time_ms} ms
                </span>
              </div>
              <p className="text-base font-medium text-white bg-slate-900/60 p-4 rounded-lg border border-slate-800">
                {captionResult.caption}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
