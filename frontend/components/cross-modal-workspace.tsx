"use client";

import React, { useState, useEffect } from "react";
import {
  Layers,
  Radio,
  Sparkles,
  ShieldCheck,
  AlertTriangle,
  CheckCircle2,
  HelpCircle,
  Clock,
  Eye,
  Crosshair,
  Sliders,
  ChevronDown,
  ChevronUp,
  Cpu,
  Info,
  Maximize2,
  RefreshCw,
  Zap,
} from "lucide-react";
import {
  OpticalSARPair,
  CrossModalAnalysisResponse,
  ImageInspect,
  CrossModalEvidenceRegion,
} from "../lib/types";
import {
  createOpticalSARPair,
  listOpticalSARPairs,
  analyzeCrossModal,
} from "../lib/api";

const PRESET_QUERIES = [
  {
    label: "Water & Flood Inundation",
    query: "Analyze both sensors for water bodies and flood inundation.",
    task: "cross_modal_analysis",
  },
  {
    label: "Urban Double-Bounce",
    query: "Verify structural footprints using SAR double-bounce backscatter and optical geometry.",
    task: "cross_modal_vqa",
  },
  {
    label: "Crop Vigor & Soil Roughness",
    query: "Assess agricultural vigor: optical NDVI vs SAR volume scattering.",
    task: "cross_modal_analysis",
  },
  {
    label: "All-Weather Cloud Penetration",
    query: "Compare surface optical visibility against SAR all-weather penetration.",
    task: "cross_modal_vqa",
  },
  {
    label: "Spectral vs Roughness Disagreement",
    query: "Where do optical spectral reflectance and SAR roughness disagree?",
    task: "cross_modal_grounding",
  },
];

interface CrossModalWorkspaceProps {
  initialPairId?: string;
  availableImages?: ImageInspect[];
}

export function CrossModalWorkspace({
  initialPairId,
  availableImages = [],
}: CrossModalWorkspaceProps) {
  const [pairs, setPairs] = useState<OpticalSARPair[]>([]);
  const [selectedPair, setSelectedPair] = useState<OpticalSARPair | null>(null);
  const [loadingPairs, setLoadingPairs] = useState<boolean>(true);

  // New pair creation inputs
  const [opticalImageId, setOpticalImageId] = useState<string>("");
  const [sarImageId, setSarImageId] = useState<string>("");
  const [creatingPair, setCreatingPair] = useState<boolean>(false);
  const [pairError, setPairError] = useState<string | null>(null);

  // Analysis parameters
  const [query, setQuery] = useState<string>(
    "Analyze both sensors for water bodies and flood inundation."
  );
  const [selectedTask, setSelectedTask] = useState<string>("cross_modal_analysis");
  const [analyzing, setAnalyzing] = useState<boolean>(false);
  const [analysisResult, setAnalysisResult] = useState<CrossModalAnalysisResponse | null>(null);
  const [activeTab, setActiveTab] = useState<"canvas" | "optical" | "sar" | "observations">("canvas");
  const [activeRegionId, setActiveRegionId] = useState<string | null>(null);
  const [showTrace, setShowTrace] = useState<boolean>(false);

  // Filter available images by modality
  const opticalImages = availableImages.filter(
    (img) =>
      img.modality.toLowerCase().includes("optical") ||
      img.modality.toLowerCase().includes("multispectral") ||
      img.modality.toLowerCase().includes("rgb")
  );
  const sarImages = availableImages.filter((img) =>
    img.modality.toLowerCase().includes("sar")
  );

  // Fallback lists if modality detection was generic
  const displayedOptical = opticalImages.length > 0 ? opticalImages : availableImages;
  const displayedSar = sarImages.length > 0 ? sarImages : availableImages;

  // Load existing pairs
  const loadPairs = async () => {
    try {
      setLoadingPairs(true);
      const data = await listOpticalSARPairs(50, 0);
      setPairs(data);
      if (data.length > 0) {
        const defaultPair = initialPairId
          ? data.find((p) => p.id === initialPairId) || data[0]
          : data[0];
        setSelectedPair(defaultPair);
      }
    } catch (err: any) {
      console.error("Failed to load Optical-SAR pairs:", err);
    } finally {
      setLoadingPairs(false);
    }
  };

  useEffect(() => {
    loadPairs();
  }, [initialPairId]);

  // Handle new pair creation
  const handleCreatePair = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!opticalImageId || !sarImageId) {
      setPairError("Please select both an Optical image and a SAR image.");
      return;
    }
    if (opticalImageId === sarImageId) {
      setPairError("Optical and SAR images cannot be identical. A cross-modal pair requires distinct sensors.");
      return;
    }

    try {
      setCreatingPair(true);
      setPairError(null);
      const newPair = await createOpticalSARPair(opticalImageId, sarImageId);
      setPairs((prev) => [newPair, ...prev]);
      setSelectedPair(newPair);
    } catch (err: any) {
      setPairError(err.message || "Failed to create Optical-SAR pair.");
    } finally {
      setCreatingPair(false);
    }
  };

  // Run Cross-Modal Joint Analysis
  const handleRunAnalysis = async () => {
    if (!selectedPair) return;
    try {
      setAnalyzing(true);
      setAnalysisResult(null);
      const res = await analyzeCrossModal(selectedPair.id, query, selectedTask);
      setAnalysisResult(res);
      if (res.regions && res.regions.length > 0) {
        setActiveRegionId(res.regions[0].id);
      }
    } catch (err: any) {
      alert(`Cross-modal analysis error: ${err.message}`);
    } finally {
      setAnalyzing(false);
    }
  };

  const getAgreementBadge = (status: string) => {
    switch (status) {
      case "AGREEMENT":
        return {
          bg: "bg-emerald-950/80 border-emerald-700/60 text-emerald-300",
          label: "Strong Cross-Modal Agreement",
          icon: <CheckCircle2 className="h-4 w-4 text-emerald-400" />,
        };
      case "PARTIAL_AGREEMENT":
        return {
          bg: "bg-amber-950/80 border-amber-700/60 text-amber-300",
          label: "Partial Modality Agreement",
          icon: <AlertTriangle className="h-4 w-4 text-amber-400" />,
        };
      case "DISAGREEMENT":
        return {
          bg: "bg-rose-950/80 border-rose-700/60 text-rose-300",
          label: "Complementary Disagreement",
          icon: <AlertTriangle className="h-4 w-4 text-rose-400" />,
        };
      default:
        return {
          bg: "bg-slate-900 border-slate-700 text-slate-300",
          label: "Modality Consistent",
          icon: <Info className="h-4 w-4 text-slate-400" />,
        };
    }
  };

  return (
    <div className="space-y-8">
      {/* Top Controls: Pair Selector or Creator */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Registered Pairs List / Active Pair Switcher */}
        <div className="lg:col-span-5 rounded-2xl border border-slate-800 bg-surface/60 p-5 backdrop-blur-sm space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-bold tracking-wide uppercase text-white flex items-center space-x-2">
              <Radio className="h-4 w-4 text-cyan-400" />
              <span>Optical-SAR Image Pairs</span>
            </h2>
            <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-slate-900 text-slate-400 border border-slate-800">
              {pairs.length} registered
            </span>
          </div>

          {loadingPairs ? (
            <div className="py-8 text-center text-xs font-mono text-slate-500 animate-pulse">
              Scanning database for Optical-SAR pairs...
            </div>
          ) : pairs.length === 0 ? (
            <div className="py-8 text-center text-xs text-slate-400 border border-dashed border-slate-800 rounded-xl p-4">
              No registered Optical-SAR pairs yet. Pair an Optical and a SAR image below.
            </div>
          ) : (
            <div className="space-y-2 max-h-56 overflow-y-auto pr-1">
              {pairs.map((p) => {
                const isSelected = selectedPair?.id === p.id;
                return (
                  <button
                    key={p.id}
                    onClick={() => {
                      setSelectedPair(p);
                      setAnalysisResult(null);
                    }}
                    className={`w-full text-left p-3 rounded-xl border text-xs transition flex flex-col space-y-1.5 ${
                      isSelected
                        ? "bg-cyan-950/40 border-cyan-700/80 text-white shadow-sm"
                        : "bg-slate-900/40 border-slate-800/80 text-slate-300 hover:bg-slate-800/40"
                    }`}
                  >
                    <div className="flex items-center justify-between font-mono text-[11px]">
                      <span className="font-semibold truncate max-w-[200px]">
                        {p.optical_image.original_filename}
                      </span>
                      <span className="text-slate-500">↔</span>
                      <span className="font-semibold truncate max-w-[200px] text-amber-400">
                        {p.sar_image.original_filename}
                      </span>
                    </div>
                    <div className="flex items-center space-x-2 text-[10px] text-slate-400">
                      <span className="px-1.5 py-0.5 rounded bg-cyan-950/80 border border-cyan-800/40 text-cyan-300">
                        {p.optical_sensor || "Optical"}
                      </span>
                      <span className="px-1.5 py-0.5 rounded bg-amber-950/80 border border-amber-800/40 text-amber-300">
                        {p.sar_sensor || "SAR"} ({p.validation.sar_polarization || "VV"})
                      </span>
                      <span className="text-slate-500">·</span>
                      <span className="text-emerald-400 font-mono">
                        {Math.round((p.overlap_ratio || 1.0) * 100)}% overlap
                      </span>
                    </div>
                  </button>
                );
              })}
            </div>
          )}

          {/* Quick Register New Pair Collapsible */}
          <details className="group pt-2 border-t border-slate-800/80">
            <summary className="text-xs font-semibold text-cyan-400 hover:text-cyan-300 cursor-pointer list-none flex items-center justify-between py-1">
              <span>+ Register New Optical + SAR Pair</span>
              <span className="text-[10px] text-slate-500 group-open:rotate-180 transition-transform">▼</span>
            </summary>

            <form onSubmit={handleCreatePair} className="space-y-3 pt-3">
              <div>
                <label className="block text-[11px] font-medium text-slate-300 mb-1">
                  1. Optical / Multispectral Raster (e.g., Cartosat-2S, Sentinel-2)
                </label>
                <select
                  value={opticalImageId}
                  onChange={(e) => setOpticalImageId(e.target.value)}
                  className="w-full text-xs bg-slate-900 border border-slate-700 rounded-lg p-2 text-white focus:outline-none focus:border-cyan-500"
                >
                  <option value="">Select Optical raster...</option>
                  {displayedOptical.map((img) => (
                    <option key={img.id} value={img.id}>
                      {img.filename} ({img.modality} · {img.raster.bands} bands)
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-[11px] font-medium text-slate-300 mb-1">
                  2. Synthetic Aperture Radar (SAR) Raster (e.g., RISAT, Sentinel-1)
                </label>
                <select
                  value={sarImageId}
                  onChange={(e) => setSarImageId(e.target.value)}
                  className="w-full text-xs bg-slate-900 border border-slate-700 rounded-lg p-2 text-white focus:outline-none focus:border-amber-500"
                >
                  <option value="">Select SAR raster...</option>
                  {displayedSar.map((img) => (
                    <option key={img.id} value={img.id}>
                      {img.filename} ({img.modality} · {img.raster.bands}b)
                    </option>
                  ))}
                </select>
              </div>

              {pairError && (
                <div className="p-2.5 rounded-lg bg-rose-950/60 border border-rose-800 text-rose-300 text-xs flex items-start space-x-2">
                  <AlertTriangle className="h-4 w-4 shrink-0 mt-0.5" />
                  <span>{pairError}</span>
                </div>
              )}

              <button
                type="submit"
                disabled={creatingPair}
                className="w-full py-2 px-3 rounded-lg bg-gradient-to-r from-cyan-600 to-teal-500 hover:from-cyan-500 hover:to-teal-400 text-white font-medium text-xs shadow-md transition disabled:opacity-50 flex items-center justify-center space-x-2"
              >
                {creatingPair ? (
                  <>
                    <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                    <span>Validating Modalities & Geometry...</span>
                  </>
                ) : (
                  <>
                    <Radio className="h-3.5 w-3.5" />
                    <span>Register & Validate Pair</span>
                  </>
                )}
              </button>
            </form>
          </details>
        </div>

        {/* Right: Active Pair Metadata & Verification Badges */}
        <div className="lg:col-span-7 rounded-2xl border border-slate-800 bg-surface/60 p-5 backdrop-blur-sm space-y-4 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-bold tracking-wide uppercase text-white flex items-center space-x-2">
                <Layers className="h-4 w-4 text-teal-400" />
                <span>Pair Alignment & Cross-Modal Verification</span>
              </h3>
              {selectedPair && (
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-950/80 text-emerald-300 border border-emerald-800/50 flex items-center space-x-1">
                  <ShieldCheck className="h-3 w-3" />
                  <span>Verified Pair</span>
                </span>
              )}
            </div>

            {selectedPair ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {/* Optical Raster Card */}
                <div className="p-3.5 rounded-xl bg-slate-900/60 border border-cyan-900/40 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-[11px] font-bold uppercase tracking-wider text-cyan-400">
                      Optical Channel
                    </span>
                    <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-800/40">
                      {selectedPair.optical_sensor || "Optical"}
                    </span>
                  </div>
                  <div className="text-xs font-semibold text-white truncate font-mono">
                    {selectedPair.optical_image.original_filename}
                  </div>
                  <div className="text-[11px] text-slate-400 space-y-1 font-mono">
                    <div>CRS: {selectedPair.optical_image.crs || "Projected / UTM"}</div>
                    <div>Bands: {selectedPair.optical_image.band_count} · {selectedPair.optical_image.dtype}</div>
                    <div>Res: {selectedPair.optical_image.resolution ? `${selectedPair.optical_image.resolution.toFixed(2)}m` : "Sub-meter"}</div>
                  </div>
                </div>

                {/* SAR Raster Card */}
                <div className="p-3.5 rounded-xl bg-slate-900/60 border border-amber-900/40 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-[11px] font-bold uppercase tracking-wider text-amber-400">
                      SAR Channel
                    </span>
                    <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-amber-950 text-amber-300 border border-amber-800/40">
                      {selectedPair.sar_sensor || "SAR"} · {selectedPair.validation.sar_polarization || "VV"}
                    </span>
                  </div>
                  <div className="text-xs font-semibold text-white truncate font-mono">
                    {selectedPair.sar_image.original_filename}
                  </div>
                  <div className="text-[11px] text-slate-400 space-y-1 font-mono">
                    <div>Scaling: dB Log-Scale ($10\log_{10}$)</div>
                    <div>Speckle Filter: 1%–99% Percentile</div>
                    <div>Polarization: {selectedPair.validation.sar_polarization || "Dual-pol VV/VH"}</div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-center py-10 text-slate-500 text-xs font-mono">
                Select an Optical-SAR pair to inspect co-registration and begin reasoning.
              </div>
            )}
          </div>

          {/* Validation Metrics Row */}
          {selectedPair && (
            <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80 flex flex-wrap items-center justify-between gap-3 text-xs">
              <div className="flex items-center space-x-2">
                <span className="h-2 w-2 rounded-full bg-emerald-400 shadow-[0_0_6px_rgba(52,211,153,0.6)]" />
                <span className="text-slate-300 font-medium">Spatial Overlap:</span>
                <span className="font-mono text-emerald-400 font-bold">
                  {Math.round((selectedPair.overlap_ratio || 1.0) * 100)}%
                </span>
              </div>

              <div className="flex items-center space-x-2">
                <span className="text-slate-400 font-mono">In-Memory Registration:</span>
                <span className="px-2 py-0.5 rounded bg-slate-900 border border-slate-700 text-cyan-300 text-[11px] font-mono">
                  {selectedPair.alignment_method || "Bilinear Resampling"}
                </span>
              </div>

              <div className="flex items-center space-x-1.5 text-slate-400 text-[11px]">
                <ShieldCheck className="h-3.5 w-3.5 text-emerald-400" />
                <span>Zero In-Place Overwrites</span>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Query & Task Control Hub */}
      <div className="rounded-2xl border border-slate-800 bg-surface/60 p-6 backdrop-blur-sm space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center space-x-2">
            <Sparkles className="h-5 w-5 text-cyan-400" />
            <h3 className="text-base font-bold text-white">Cross-Modal Reasoning Agent</h3>
          </div>

          {/* Task Pills */}
          <div className="flex items-center space-x-2 text-xs">
            <button
              type="button"
              onClick={() => setSelectedTask("cross_modal_analysis")}
              className={`px-3 py-1.5 rounded-lg border font-medium transition ${
                selectedTask === "cross_modal_analysis"
                  ? "bg-cyan-950 border-cyan-600 text-cyan-300 shadow-sm"
                  : "bg-slate-900 border-slate-800 text-slate-400 hover:text-white"
              }`}
            >
              Joint Analysis
            </button>
            <button
              type="button"
              onClick={() => setSelectedTask("cross_modal_vqa")}
              className={`px-3 py-1.5 rounded-lg border font-medium transition ${
                selectedTask === "cross_modal_vqa"
                  ? "bg-cyan-950 border-cyan-600 text-cyan-300 shadow-sm"
                  : "bg-slate-900 border-slate-800 text-slate-400 hover:text-white"
              }`}
            >
              Cross-Modal VQA
            </button>
            <button
              type="button"
              onClick={() => setSelectedTask("cross_modal_grounding")}
              className={`px-3 py-1.5 rounded-lg border font-medium transition ${
                selectedTask === "cross_modal_grounding"
                  ? "bg-cyan-950 border-cyan-600 text-cyan-300 shadow-sm"
                  : "bg-slate-900 border-slate-800 text-slate-400 hover:text-white"
              }`}
            >
              Cross-Modal Grounding
            </button>
          </div>
        </div>

        {/* Preset Query Badges */}
        <div className="flex flex-wrap gap-2 pt-1">
          {PRESET_QUERIES.map((preset, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => {
                setQuery(preset.query);
                setSelectedTask(preset.task);
              }}
              className="px-2.5 py-1 rounded-full text-[11px] font-medium bg-slate-900/80 hover:bg-slate-800 text-slate-300 border border-slate-700/60 hover:border-cyan-500/50 transition flex items-center space-x-1.5"
            >
              <span className="text-cyan-400">⚡</span>
              <span>{preset.label}</span>
            </button>
          ))}
        </div>

        {/* Textarea & Submit */}
        <div className="relative">
          <textarea
            rows={2}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask a question requiring both Optical spectral signatures and SAR structural backscatter..."
            className="w-full text-sm bg-slate-950/80 border border-slate-700/80 rounded-xl p-3.5 pr-28 text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500 transition resize-none"
          />
          <button
            type="button"
            disabled={analyzing || !selectedPair}
            onClick={handleRunAnalysis}
            className="absolute right-3 top-3 bottom-3 px-4 rounded-lg bg-gradient-to-r from-cyan-600 to-teal-500 hover:from-cyan-500 hover:to-teal-400 text-white text-xs font-semibold shadow-md transition disabled:opacity-50 flex items-center space-x-1.5"
          >
            {analyzing ? (
              <>
                <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                <span>Reasoning...</span>
              </>
            ) : (
              <>
                <Zap className="h-3.5 w-3.5" />
                <span>Execute</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Analysis Results Display */}
      {analysisResult && (
        <div className="space-y-6">
          {/* Main Answer Banner with Confidence */}
          <div className="rounded-2xl border border-cyan-800/40 bg-gradient-to-b from-cyan-950/30 to-surface/80 p-6 backdrop-blur-sm space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800/80 pb-3">
              <div className="flex items-center space-x-2">
                <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-cyan-900/60 border border-cyan-700/50 text-cyan-300 font-mono">
                  {analysisResult.task}
                </span>
                <span className="text-xs text-slate-400 font-mono">
                  {analysisResult.processing.model} ({analysisResult.processing.fusion_method})
                </span>
              </div>

              {/* Confidence Gauge */}
              <div className="flex items-center space-x-3 text-xs font-mono">
                <span className="text-slate-400">Confidence:</span>
                <div className="w-28 bg-slate-900 rounded-full h-2 overflow-hidden border border-slate-700">
                  <div
                    className="bg-gradient-to-r from-teal-400 to-emerald-400 h-full rounded-full transition-all duration-500"
                    style={{
                      width: `${Math.round(analysisResult.confidence.score * 100)}%`,
                    }}
                  />
                </div>
                <span className="font-bold text-emerald-400">
                  {Math.round(analysisResult.confidence.score * 100)}%
                </span>
              </div>
            </div>

            {/* Answer Text */}
            <div className="space-y-1">
              <div className="text-xs font-mono uppercase tracking-wider text-slate-400">
                Joint Multimodal Interpretation:
              </div>
              <p className="text-sm sm:text-base text-white leading-relaxed font-sans font-medium">
                {analysisResult.answer}
              </p>
            </div>
          </div>

          {/* Modality Contributions Comparison Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Optical Contribution */}
            <div className="p-5 rounded-2xl border border-cyan-900/50 bg-slate-950/60 space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <span className="h-2.5 w-2.5 rounded-full bg-cyan-400 shadow-[0_0_6px_rgba(34,211,238,0.6)]" />
                  <h4 className="text-xs font-bold uppercase tracking-wider text-cyan-300">
                    Optical Modality Contribution
                  </h4>
                </div>
                <span className="text-[10px] font-mono text-slate-400">
                  {analysisResult.optical_summary.sensor || "Multispectral"}
                </span>
              </div>
              <p className="text-xs text-slate-300 leading-relaxed">
                {analysisResult.optical_summary.contribution}
              </p>
              <div className="flex flex-wrap gap-1.5 pt-1">
                {analysisResult.optical_summary.features.map((feat, idx) => (
                  <span
                    key={idx}
                    className="px-2 py-0.5 rounded-md text-[10px] font-mono bg-cyan-950 border border-cyan-800/40 text-cyan-300"
                  >
                    {feat}
                  </span>
                ))}
              </div>
            </div>

            {/* SAR Contribution */}
            <div className="p-5 rounded-2xl border border-amber-900/50 bg-slate-950/60 space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <span className="h-2.5 w-2.5 rounded-full bg-amber-400 shadow-[0_0_6px_rgba(251,191,36,0.6)]" />
                  <h4 className="text-xs font-bold uppercase tracking-wider text-amber-300">
                    SAR Modality Contribution
                  </h4>
                </div>
                <span className="text-[10px] font-mono text-slate-400">
                  {analysisResult.sar_summary.sensor || "Synthetic Aperture Radar"}
                </span>
              </div>
              <p className="text-xs text-slate-300 leading-relaxed">
                {analysisResult.sar_summary.contribution}
              </p>
              <div className="flex flex-wrap gap-1.5 pt-1">
                {analysisResult.sar_summary.features.map((feat, idx) => (
                  <span
                    key={idx}
                    className="px-2 py-0.5 rounded-md text-[10px] font-mono bg-amber-950 border border-amber-800/40 text-amber-300"
                  >
                    {feat}
                  </span>
                ))}
              </div>
            </div>
          </div>

          {/* Physical Consistency & Disagreement Panel */}
          {analysisResult.disagreement && (
            <div className="p-4 rounded-xl border border-slate-800 bg-surface/70 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div className="flex items-center space-x-3">
                {getAgreementBadge(analysisResult.disagreement.agreement_status).icon}
                <div>
                  <div className="flex items-center space-x-2">
                    <span className="text-xs font-bold text-white font-mono">
                      {getAgreementBadge(analysisResult.disagreement.agreement_status).label}
                    </span>
                    <span
                      className={`text-[10px] font-mono px-2 py-0.5 rounded border ${
                        getAgreementBadge(analysisResult.disagreement.agreement_status).bg
                      }`}
                    >
                      {analysisResult.disagreement.agreement_status}
                    </span>
                  </div>
                  <p className="text-xs text-slate-400 mt-0.5">
                    {analysisResult.disagreement.explanation}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Spatial Evidence Regions Canvas & Visualizer */}
          <div className="rounded-2xl border border-slate-800 bg-surface/60 p-5 backdrop-blur-sm space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-3">
              <div className="flex items-center space-x-2">
                <Crosshair className="h-4 w-4 text-cyan-400" />
                <h4 className="text-xs font-bold uppercase tracking-wider text-white">
                  Cross-Modal Evidence Canvas ({analysisResult.regions.length} regions localized)
                </h4>
              </div>

              {/* View Tabs */}
              <div className="flex items-center space-x-2 text-xs">
                <button
                  type="button"
                  onClick={() => setActiveTab("canvas")}
                  className={`px-2.5 py-1 rounded-lg border transition ${
                    activeTab === "canvas"
                      ? "bg-cyan-950 border-cyan-700 text-cyan-300"
                      : "bg-slate-900 border-slate-800 text-slate-400 hover:text-white"
                  }`}
                >
                  Joint Overlay
                </button>
                <button
                  type="button"
                  onClick={() => setActiveTab("observations")}
                  className={`px-2.5 py-1 rounded-lg border transition ${
                    activeTab === "observations"
                      ? "bg-cyan-950 border-cyan-700 text-cyan-300"
                      : "bg-slate-900 border-slate-800 text-slate-400 hover:text-white"
                  }`}
                >
                  Observations ({analysisResult.joint_observations.length})
                </button>
              </div>
            </div>

            {/* Active View Content */}
            {activeTab === "canvas" ? (
              <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
                {/* Visual Bounding Box Canvas Simulation */}
                <div className="lg:col-span-8 bg-slate-950 rounded-xl border border-slate-800 relative min-h-[320px] flex items-center justify-center p-4 overflow-hidden">
                  {/* Subtle Grid Background */}
                  <div className="absolute inset-0 bg-[linear-gradient(to_right,#1e293b_1px,transparent_1px),linear-gradient(to_bottom,#1e293b_1px,transparent_1px)] bg-[size:2rem_2rem] opacity-30" />

                  {/* Render simulated bounding boxes with normalized coordinates */}
                  {analysisResult.regions.map((reg) => {
                    const isSelected = activeRegionId === reg.id;
                    const [ymin, xmin, ymax, xmax] = reg.bbox;
                    const top = `${ymin * 100}%`;
                    const left = `${xmin * 100}%`;
                    const width = `${Math.max((xmax - xmin) * 100, 15)}%`;
                    const height = `${Math.max((ymax - ymin) * 100, 15)}%`;

                    const borderColor =
                      reg.supported_by === "both"
                        ? "border-emerald-400 bg-emerald-500/10 text-emerald-300"
                        : reg.supported_by === "sar"
                        ? "border-amber-400 bg-amber-500/10 text-amber-300"
                        : "border-cyan-400 bg-cyan-500/10 text-cyan-300";

                    return (
                      <div
                        key={reg.id}
                        onClick={() => setActiveRegionId(reg.id)}
                        style={{ top, left, width, height }}
                        className={`absolute border-2 rounded-lg cursor-pointer transition-all duration-200 flex flex-col justify-between p-1.5 z-10 ${borderColor} ${
                          isSelected
                            ? "ring-2 ring-white shadow-lg scale-[1.02] z-20"
                            : "hover:scale-[1.01]"
                        }`}
                      >
                        <div className="flex items-center justify-between text-[10px] font-mono font-bold">
                          <span className="truncate">{reg.label}</span>
                          <span className="px-1 py-0.2 rounded bg-slate-950/80 text-[9px]">
                            {Math.round(reg.confidence * 100)}%
                          </span>
                        </div>
                        <div className="text-[9px] font-mono uppercase tracking-wider text-slate-300">
                          {reg.supported_by}
                        </div>
                      </div>
                    );
                  })}

                  <div className="absolute bottom-3 left-3 text-[10px] font-mono text-slate-500 flex items-center space-x-3 bg-slate-950/80 px-2 py-1 rounded border border-slate-800">
                    <span className="flex items-center space-x-1">
                      <span className="h-2 w-2 rounded-full bg-cyan-400" />
                      <span>Optical</span>
                    </span>
                    <span className="flex items-center space-x-1">
                      <span className="h-2 w-2 rounded-full bg-amber-400" />
                      <span>SAR</span>
                    </span>
                    <span className="flex items-center space-x-1">
                      <span className="h-2 w-2 rounded-full bg-emerald-400" />
                      <span>Joint (Both)</span>
                    </span>
                  </div>
                </div>

                {/* Region Details Sidebar */}
                <div className="lg:col-span-4 space-y-2 max-h-[320px] overflow-y-auto pr-1">
                  {analysisResult.regions.map((reg) => {
                    const isSelected = activeRegionId === reg.id;
                    return (
                      <div
                        key={reg.id}
                        onClick={() => setActiveRegionId(reg.id)}
                        className={`p-3 rounded-xl border text-xs cursor-pointer transition ${
                          isSelected
                            ? "bg-slate-900 border-cyan-600 shadow-sm"
                            : "bg-slate-950/40 border-slate-800 hover:bg-slate-900/40"
                        }`}
                      >
                        <div className="flex items-center justify-between font-mono">
                          <span className="font-bold text-white">{reg.label}</span>
                          <span className="text-emerald-400 font-semibold">
                            {Math.round(reg.confidence * 100)}%
                          </span>
                        </div>
                        <div className="text-[11px] text-slate-400 mt-1">
                          {reg.rationale || "Detected through multimodal feature fusion."}
                        </div>
                        <div className="mt-2 flex items-center justify-between text-[10px] font-mono text-slate-500">
                          <span>Origin: {reg.supported_by.toUpperCase()}</span>
                          <span>
                            [{reg.bbox.map((b) => b.toFixed(2)).join(", ")}]
                          </span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            ) : (
              <div className="space-y-2.5 py-2">
                {analysisResult.joint_observations.map((obs, idx) => (
                  <div
                    key={idx}
                    className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 text-xs text-slate-300 flex items-start space-x-3"
                  >
                    <span className="h-5 w-5 rounded-full bg-cyan-950 border border-cyan-800/60 flex items-center justify-center text-cyan-400 font-mono text-[10px] shrink-0 mt-0.5">
                      {idx + 1}
                    </span>
                    <span className="leading-relaxed">{obs}</span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Observable Execution Trace */}
          <div className="border border-slate-800 rounded-xl overflow-hidden bg-slate-950/40">
            <button
              type="button"
              onClick={() => setShowTrace(!showTrace)}
              className="w-full px-4 py-2.5 text-xs text-slate-400 hover:text-slate-200 flex items-center justify-between transition"
            >
              <span className="font-mono flex items-center space-x-2">
                <Clock className="h-3.5 w-3.5 text-cyan-400" />
                <span>Execution Trace & Performance Metrics</span>
              </span>
              {showTrace ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
            </button>

            {showTrace && (
              <div className="p-4 border-t border-slate-800 text-xs font-mono text-slate-300 space-y-2 bg-slate-950/80">
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  <div className="p-2 rounded bg-slate-900 border border-slate-800">
                    <div className="text-[10px] text-slate-500">Latency</div>
                    <div className="font-bold text-cyan-400">
                      {analysisResult.processing.processing_time_ms} ms
                    </div>
                  </div>
                  <div className="p-2 rounded bg-slate-900 border border-slate-800">
                    <div className="text-[10px] text-slate-500">Model</div>
                    <div className="font-bold text-white truncate">
                      {analysisResult.processing.model}
                    </div>
                  </div>
                  <div className="p-2 rounded bg-slate-900 border border-slate-800">
                    <div className="text-[10px] text-slate-500">Fusion Architecture</div>
                    <div className="font-bold text-white">
                      {analysisResult.processing.fusion_method}
                    </div>
                  </div>
                  <div className="p-2 rounded bg-slate-900 border border-slate-800">
                    <div className="text-[10px] text-slate-500">Co-Registration</div>
                    <div className="font-bold text-emerald-400">
                      {analysisResult.processing.alignment_performed ? "Bilinear Resampled" : "Native Grid"}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
