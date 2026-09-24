"use client";

import React, { useState, useEffect } from "react";
import {
  GitCompare,
  Sliders,
  Play,
  Calendar,
  Layers,
  Sparkles,
  AlertTriangle,
  CheckCircle2,
  Clock,
  RotateCcw,
  Bot,
  Zap,
  ChevronDown,
  ChevronUp,
  MapPin,
  HelpCircle,
} from "lucide-react";
import {
  BiTemporalPair,
  ChangeAnalysisResponse,
  ImageInspect,
  AgentAnalyzeResponse,
} from "../lib/types";
import {
  createTemporalPair,
  listTemporalPairs,
  analyzeTemporalChange,
  getImageMetadata,
} from "../lib/api";
import { BiTemporalViewer } from "./bitemporal-viewer";

const QUICK_CHANGE_QUERIES = [
  "What changed between these two dates?",
  "Did urban development increase over time?",
  "Detect newly constructed buildings or structures.",
  "Identify vegetation loss and agricultural shifts.",
  "Are there new road corridors or transport alterations?",
];

interface TemporalWorkspaceProps {
  initialPairId?: string;
  availableImages?: ImageInspect[];
}

export function TemporalWorkspace({
  initialPairId,
  availableImages = [],
}: TemporalWorkspaceProps) {
  const [pairs, setPairs] = useState<BiTemporalPair[]>([]);
  const [selectedPair, setSelectedPair] = useState<BiTemporalPair | null>(null);
  const [loadingPairs, setLoadingPairs] = useState<boolean>(true);

  // New pair creation inputs
  const [t1ImageId, setT1ImageId] = useState<string>("");
  const [t2ImageId, setT2ImageId] = useState<string>("");
  const [creatingPair, setCreatingPair] = useState<boolean>(false);
  const [pairError, setPairError] = useState<string | null>(null);

  // Analysis parameters
  const [query, setQuery] = useState<string>("What changed between these two dates?");
  const [threshold, setThreshold] = useState<number>(0.35);
  const [minRegionSize, setMinRegionSize] = useState<number>(25);
  const [analyzing, setAnalyzing] = useState<boolean>(false);
  const [analysisResult, setAnalysisResult] = useState<ChangeAnalysisResponse | null>(null);
  const [agentResponse, setAgentResponse] = useState<AgentAnalyzeResponse | null>(null);
  const [showTrace, setShowTrace] = useState<boolean>(false);
  const [runAgentMode, setRunAgentMode] = useState<boolean>(true);

  // Load existing pairs
  useEffect(() => {
    async function loadPairs() {
      try {
        setLoadingPairs(true);
        const data = await listTemporalPairs(50, 0);
        setPairs(data);
        if (data.length > 0) {
          const defaultPair = initialPairId
            ? data.find((p) => p.pair_id === initialPairId) || data[0]
            : data[0];
          setSelectedPair(defaultPair);
        }
      } catch (err: any) {
        console.error("Failed to load bi-temporal pairs:", err);
      } finally {
        setLoadingPairs(false);
      }
    }
    loadPairs();
  }, [initialPairId]);

  // Handle new pair creation
  const handleCreatePair = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!t1ImageId || !t2ImageId) {
      setPairError("Please select both a baseline T1 image and a target T2 image.");
      return;
    }
    if (t1ImageId === t2ImageId) {
      setPairError("T1 and T2 must reference different satellite images.");
      return;
    }

    try {
      setCreatingPair(true);
      setPairError(null);
      const newPair = await createTemporalPair(t1ImageId, t2ImageId);
      setPairs((prev) => [newPair, ...prev]);
      setSelectedPair(newPair);
      setAnalysisResult(null);
    } catch (err: any) {
      setPairError(err.message || "Failed to create bi-temporal pair.");
    } finally {
      setCreatingPair(false);
    }
  };

  // Execute Change Analysis
  const handleRunAnalysis = async () => {
    if (!selectedPair) return;

    try {
      setAnalyzing(true);
      setPairError(null);

      if (runAgentMode) {
        // Run via Agentic Router
        const res = await fetch("http://localhost:8000/api/v1/agent/analyze", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            query,
            image_ids: [selectedPair.image_t1.id, selectedPair.image_t2.id],
            pair_id: selectedPair.pair_id,
          }),
        });
        if (!res.ok) {
          const err = await res.json();
          throw new Error(err.detail || "Agent analysis failed");
        }
        const agentData: AgentAnalyzeResponse = await res.json();
        setAgentResponse(agentData);

        // Also fetch structured change analysis metrics
        const directRes = await analyzeTemporalChange(
          selectedPair.pair_id,
          query,
          threshold,
          minRegionSize
        );
        setAnalysisResult(directRes);
      } else {
        // Direct tool analysis
        const directRes = await analyzeTemporalChange(
          selectedPair.pair_id,
          query,
          threshold,
          minRegionSize
        );
        setAnalysisResult(directRes);
        setAgentResponse(null);
      }
    } catch (err: any) {
      setPairError(err.message || "Change analysis failed.");
    } finally {
      setAnalyzing(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Workspace Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 p-5 rounded-2xl bg-gradient-to-r from-slate-900 via-slate-900/90 to-amber-950/20 border border-slate-800 shadow-xl">
        <div className="flex items-center space-x-3.5">
          <div className="p-2.5 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-400">
            <GitCompare className="h-6 w-6" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-slate-100 flex items-center gap-2">
              Bi-Temporal Change Intelligence
              <span className="px-2 py-0.5 text-xs font-mono rounded bg-amber-950/80 border border-amber-700/60 text-amber-300">
                Phase 5 Active
              </span>
            </h1>
            <p className="text-xs text-slate-400 mt-0.5">
              Siamese feature difference analysis, non-destructive co-registration, and text-guided Change VQA
            </p>
          </div>
        </div>

        {selectedPair && (
          <div className="flex items-center space-x-2 text-xs font-mono">
            <span
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg border ${
                selectedPair.validation.valid
                  ? "bg-emerald-950/60 border-emerald-800/80 text-emerald-300"
                  : "bg-amber-950/60 border-amber-800/80 text-amber-300"
              }`}
            >
              {selectedPair.validation.valid ? (
                <CheckCircle2 className="h-4 w-4 text-emerald-400" />
              ) : (
                <AlertTriangle className="h-4 w-4 text-amber-400" />
              )}
              {selectedPair.validation.valid
                ? `Compatible (${Math.round((selectedPair.overlap_ratio || 1) * 100)}% Overlap)`
                : "Validation Considerations"}
            </span>

            <span className="px-3 py-1.5 rounded-lg bg-slate-950/80 border border-slate-800 text-slate-300">
              Alignment: {selectedPair.alignment_status}
            </span>
          </div>
        )}
      </div>

      {/* Main Grid: Left Config Panel & Right Viewer */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Pair Selector & Query Settings (4 cols) */}
        <div className="lg:col-span-4 space-y-5">
          {/* Pair Selection & Registration Card */}
          <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/60 shadow-lg space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800/80 pb-2.5">
              <span className="text-xs font-semibold text-slate-200 uppercase tracking-wider flex items-center gap-1.5">
                <Layers className="h-3.5 w-3.5 text-amber-400" />
                Active Bi-Temporal Pair
              </span>
              <span className="text-[11px] font-mono text-slate-400">
                {pairs.length} {pairs.length === 1 ? "Pair" : "Pairs"} Available
              </span>
            </div>

            {/* Existing Pair Selector Dropdown */}
            {pairs.length > 0 ? (
              <div>
                <label className="text-xs font-medium text-slate-400 block mb-1.5">
                  Select Registered Image Pair:
                </label>
                <select
                  value={selectedPair?.pair_id || ""}
                  onChange={(e) => {
                    const chosen = pairs.find((p) => p.pair_id === e.target.value);
                    if (chosen) {
                      setSelectedPair(chosen);
                      setAnalysisResult(null);
                    }
                  }}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs font-mono text-slate-200 focus:outline-none focus:border-amber-500 transition"
                >
                  {pairs.map((p) => (
                    <option key={p.pair_id} value={p.pair_id}>
                      T1: {p.image_t1.filename} → T2: {p.image_t2.filename}
                    </option>
                  ))}
                </select>
              </div>
            ) : (
              <p className="text-xs text-slate-500 italic">
                No image pairs registered yet. Create one below.
              </p>
            )}

            {/* Quick Register New Pair Collapsible Form */}
            {availableImages.length >= 2 && (
              <form onSubmit={handleCreatePair} className="pt-2 border-t border-slate-800/60 space-y-3">
                <span className="text-[11px] font-semibold text-slate-400 block">
                  Or Register New Pair:
                </span>
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <label className="text-[10px] text-slate-500 block mb-1">T1 (Baseline):</label>
                    <select
                      value={t1ImageId}
                      onChange={(e) => setT1ImageId(e.target.value)}
                      className="w-full p-1.5 bg-slate-950 border border-slate-800 rounded text-[11px] font-mono text-slate-300"
                    >
                      <option value="">Select T1...</option>
                      {availableImages.map((img) => (
                        <option key={img.id} value={img.id}>
                          {img.filename}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="text-[10px] text-slate-500 block mb-1">T2 (Target):</label>
                    <select
                      value={t2ImageId}
                      onChange={(e) => setT2ImageId(e.target.value)}
                      className="w-full p-1.5 bg-slate-950 border border-slate-800 rounded text-[11px] font-mono text-slate-300"
                    >
                      <option value="">Select T2...</option>
                      {availableImages.map((img) => (
                        <option key={img.id} value={img.id}>
                          {img.filename}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={creatingPair || !t1ImageId || !t2ImageId}
                  className="w-full py-1.5 px-3 rounded-lg bg-slate-800 hover:bg-slate-750 border border-slate-700 text-xs font-medium text-slate-200 transition disabled:opacity-50"
                >
                  {creatingPair ? "Validating Overlap..." : "Register & Validate Pair"}
                </button>
              </form>
            )}
          </div>

          {/* Analysis Query & Controls Card */}
          <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/60 shadow-lg space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800/80 pb-2.5">
              <span className="text-xs font-semibold text-slate-200 uppercase tracking-wider flex items-center gap-1.5">
                <Sliders className="h-3.5 w-3.5 text-amber-400" />
                Query & Parameters
              </span>
              <label className="flex items-center space-x-1.5 cursor-pointer">
                <input
                  type="checkbox"
                  checked={runAgentMode}
                  onChange={(e) => setRunAgentMode(e.target.checked)}
                  className="rounded bg-slate-950 border-slate-800 text-amber-500 focus:ring-0"
                />
                <span className="text-[11px] font-mono text-amber-300 flex items-center gap-1">
                  <Bot className="h-3 w-3" /> Agent Mode
                </span>
              </label>
            </div>

            {/* Natural-language Query Input */}
            <div>
              <label className="text-xs font-medium text-slate-400 block mb-1.5">
                Analytical Question / Directive:
              </label>
              <textarea
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                rows={2}
                placeholder="e.g. What changed between these two dates?"
                className="w-full p-2.5 bg-slate-950 border border-slate-800 rounded-lg text-xs font-medium text-slate-100 placeholder-slate-600 focus:outline-none focus:border-amber-500 transition resize-none"
              />
            </div>

            {/* Quick Query Chips */}
            <div>
              <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider block mb-1.5">
                Quick Temporal Directives:
              </span>
              <div className="flex flex-wrap gap-1.5">
                {QUICK_CHANGE_QUERIES.map((q) => (
                  <button
                    key={q}
                    type="button"
                    onClick={() => setQuery(q)}
                    className="text-[10px] px-2 py-1 bg-slate-950 hover:bg-slate-850 border border-slate-800 hover:border-slate-700 text-slate-400 hover:text-slate-200 rounded transition text-left"
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>

            {/* Threshold & Filter Sliders */}
            <div className="space-y-3 pt-2 border-t border-slate-800/60">
              <div>
                <div className="flex justify-between text-xs font-mono mb-1">
                  <span className="text-slate-400">Change Threshold:</span>
                  <span className="text-amber-400">{threshold.toFixed(2)}</span>
                </div>
                <input
                  type="range"
                  min="0.10"
                  max="0.80"
                  step="0.05"
                  value={threshold}
                  onChange={(e) => setThreshold(parseFloat(e.target.value))}
                  className="w-full accent-amber-500 cursor-pointer"
                />
              </div>

              <div>
                <div className="flex justify-between text-xs font-mono mb-1">
                  <span className="text-slate-400">Min Cluster Size:</span>
                  <span className="text-amber-400">{minRegionSize} px</span>
                </div>
                <input
                  type="range"
                  min="10"
                  max="200"
                  step="5"
                  value={minRegionSize}
                  onChange={(e) => setMinRegionSize(parseInt(e.target.value))}
                  className="w-full accent-amber-500 cursor-pointer"
                />
              </div>
            </div>

            {/* Error Message */}
            {pairError && (
              <div className="p-2.5 rounded-lg bg-red-950/60 border border-red-800/80 text-xs text-red-300 flex items-start gap-2">
                <AlertTriangle className="h-4 w-4 text-red-400 shrink-0 mt-0.5" />
                <span>{pairError}</span>
              </div>
            )}

            {/* Execute Button */}
            <button
              onClick={handleRunAnalysis}
              disabled={analyzing || !selectedPair}
              className="w-full py-2.5 px-4 rounded-xl bg-gradient-to-r from-amber-600 to-amber-500 hover:from-amber-500 hover:to-amber-400 text-slate-950 font-semibold text-xs shadow-lg shadow-amber-950/40 flex items-center justify-center space-x-2 transition disabled:opacity-50"
            >
              {analyzing ? (
                <>
                  <div className="w-3.5 h-3.5 border-2 border-slate-950 border-t-transparent rounded-full animate-spin" />
                  <span>Processing Temporal Intelligence...</span>
                </>
              ) : (
                <>
                  <Play className="h-4 w-4 fill-current" />
                  <span>Execute Bi-Temporal Intelligence</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Right Column: Visual Dual-Canvas & Evidence Viewer (8 cols) */}
        <div className="lg:col-span-8 space-y-5">
          {selectedPair ? (
            <BiTemporalViewer
              pair={selectedPair}
              changeSummary={analysisResult?.change}
              regions={analysisResult?.regions || []}
              artifactKey={analysisResult?.artifact_key}
              answer={agentResponse?.answer || analysisResult?.answer}
            />
          ) : (
            <div className="h-[420px] rounded-xl border border-dashed border-slate-800 bg-slate-950/40 flex flex-col items-center justify-center p-6 text-center">
              <GitCompare className="h-10 w-10 text-slate-700 mb-3" />
              <h3 className="text-sm font-semibold text-slate-400">No Image Pair Selected</h3>
              <p className="text-xs text-slate-600 max-w-sm mt-1">
                Select an existing pair or register two satellite images to begin co-registration and change detection.
              </p>
            </div>
          )}

          {/* Observable Agent Trace Timeline (When executed in Agent mode) */}
          {agentResponse?.trace && (
            <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/60 shadow-lg">
              <button
                onClick={() => setShowTrace(!showTrace)}
                className="w-full flex items-center justify-between text-xs font-semibold text-slate-300 uppercase tracking-wider"
              >
                <span className="flex items-center gap-2">
                  <Bot className="h-4 w-4 text-amber-400" />
                  Agent Execution Audit Trace ({agentResponse.trace.events.length} Events, {agentResponse.processing_time_ms}ms)
                </span>
                {showTrace ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
              </button>

              {showTrace && (
                <div className="mt-3 pt-3 border-t border-slate-800/80 space-y-2">
                  <div className="flex items-center justify-between text-[11px] font-mono text-slate-400 mb-2">
                    <span>Task: {agentResponse.task}</span>
                    <span>Confidence: {Math.round(agentResponse.confidence.score * 100)}% ({agentResponse.confidence.method})</span>
                  </div>

                  <div className="space-y-1.5 font-mono text-[11px]">
                    {agentResponse.trace.events.map((ev, idx) => (
                      <div
                        key={idx}
                        className="p-2 rounded bg-slate-950 border border-slate-800/80 flex items-center justify-between"
                      >
                        <div className="flex items-center space-x-2">
                          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                          <span className="text-slate-300 font-semibold">{ev.event_type}</span>
                          {ev.tool_name && (
                            <span className="text-amber-400 text-[10px]">[{ev.tool_name}]</span>
                          )}
                        </div>
                        <span className="text-slate-500 text-[10px]">{ev.duration_ms ? `${ev.duration_ms}ms` : "OK"}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
