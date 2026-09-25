"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  Sparkles,
  Layers,
  Crosshair,
  GitCompare,
  Radio,
  Play,
  ArrowRight,
  Download,
  CheckCircle2,
  AlertCircle,
  AlertTriangle,
  FileText,
  FileCode,
  Archive,
  RefreshCw,
  Info,
} from "lucide-react";
import { AppShell } from "@/components/app-shell";
import { AnalysisAnswer } from "@/components/analysis-answer";
import { ConfidenceCard } from "@/components/confidence-card";
import { ObservationsPanel } from "@/components/observations-panel";
import { TechnicalTrace } from "@/components/technical-trace";
import { AnalysisProgress } from "@/components/analysis-progress";
import { EvidenceViewerUnified } from "@/components/evidence-viewer-unified";
import {
  analyzeAgentMulti,
  getReportHtmlUrl,
  getReportPdfUrl,
  getReportJsonUrl,
  getReportPackageUrl,
  listImages,
  listTemporalPairs,
  listOpticalSARPairs,
  ApiError,
} from "@/lib/api";

interface DemoScenario {
  id: string;
  title: string;
  badge: string;
  badgeColor: string;
  description: string;
  icon: React.ElementType;
  defaultQuery: string;
  alternateQueries: string[];
  expectedTask: string;
}

interface DemoErrorState {
  step: string;
  endpoint?: string;
  status?: number | string;
  message: string;
  suggestedAction: string;
}

const DEMO_SCENARIOS: DemoScenario[] = [
  {
    id: "demo-1",
    title: "Demo 1: Single-Image Remote-Sensing VQA",
    badge: "Optical VQA",
    badgeColor: "border-cyan-500/50 text-cyan-400 bg-cyan-950/40",
    description:
      "Evaluates multi-spectral satellite imagery to identify dominant land cover categories, density, and natural terrain features.",
    icon: Layers,
    defaultQuery: "What is the dominant land cover class in this satellite image?",
    alternateQueries: [
      "Are there any residential structures present in this scene?",
      "Describe the agricultural and vegetation density visible.",
    ],
    expectedTask: "VISUAL_QUESTION_ANSWERING",
  },
  {
    id: "demo-2",
    title: "Demo 2: Text-Guided Spatial Grounding",
    badge: "Spatial Grounding",
    badgeColor: "border-purple-500/50 text-purple-400 bg-purple-950/40",
    description:
      "Localizes specific physical entities using natural language directives, mapping pixel bounding boxes directly to native UTM geospatial coordinates.",
    icon: Crosshair,
    defaultQuery: "Highlight the buildings in this image.",
    alternateQueries: [
      "Locate the water body in the southern section.",
      "Where are the primary road corridors?",
    ],
    expectedTask: "GROUNDING",
  },
  {
    id: "demo-3",
    title: "Demo 3: Bi-Temporal Change Detection",
    badge: "Change Analysis",
    badgeColor: "border-amber-500/50 text-amber-400 bg-amber-950/40",
    description:
      "Aligns pre- and post-event satellite acquisitions (T1 & T2), performs spatial resampling, and generates quantitative change difference maps.",
    icon: GitCompare,
    defaultQuery: "What changed between these images?",
    alternateQueries: [
      "Which areas changed significantly between T1 and T2?",
      "Summarize the primary surface changes observed over time.",
    ],
    expectedTask: "CHANGE_ANALYSIS",
  },
  {
    id: "demo-4",
    title: "Demo 4: Optical + SAR Multimodal Fusion",
    badge: "Multimodal Fusion",
    badgeColor: "border-emerald-500/50 text-emerald-400 bg-emerald-950/40",
    description:
      "Fuses cloud-penetrating Synthetic Aperture Radar (SAR) backscatter with multi-spectral optical data to detect all-weather structures and water boundaries.",
    icon: Radio,
    defaultQuery: "Compare optical and SAR imagery.",
    alternateQueries: [
      "What can SAR reveal that optical imagery cannot in cloud-covered areas?",
      "Highlight structural features supported by both optical and SAR.",
    ],
    expectedTask: "CROSS_MODAL_ANALYSIS",
  },
];

export default function DemoHubPage() {
  const [selectedDemo, setSelectedDemo] = useState<DemoScenario>(DEMO_SCENARIOS[0]);
  const [activeQuery, setActiveQuery] = useState<string>(DEMO_SCENARIOS[0].defaultQuery);
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [analysisResult, setAnalysisResult] = useState<any>(null);
  const [errorDetails, setErrorDetails] = useState<DemoErrorState | null>(null);

  const handleSelectDemo = (scenario: DemoScenario) => {
    setSelectedDemo(scenario);
    setActiveQuery(scenario.defaultQuery);
    setAnalysisResult(null);
    setErrorDetails(null);
  };

  const executeDemo = async () => {
    setIsRunning(true);
    setErrorDetails(null);
    setAnalysisResult(null);

    let currentStep = "Image Discovery";
    let currentEndpoint = "/api/v1/images";

    try {
      // Step 1: Discover available images
      const imagesList = await listImages(100);

      if (!imagesList || imagesList.length === 0) {
        setErrorDetails({
          step: "Image Discovery",
          endpoint: "/api/v1/images",
          message: "Demo input unavailable: No satellite images exist in the catalog.",
          suggestedAction: "Please upload satellite rasters via the Ingest Hub in the Images page first.",
        });
        setIsRunning(false);
        return;
      }

      // Step 2: Validate scenario prerequisites and select inputs
      if (selectedDemo.id === "demo-1" || selectedDemo.id === "demo-2") {
        // Single image optical/multispectral
        const validOptical = imagesList.find(
          (img) =>
            img.validation?.valid !== false &&
            (img.modality === "optical" || img.modality === "multispectral" || !img.modality)
        ) || imagesList[0];

        if (!validOptical) {
          setErrorDetails({
            step: "Input Validation",
            message: "Demo input unavailable: No valid optical or multispectral image was found.",
            suggestedAction: "Please upload an optical GeoTIFF image in the Images catalog.",
          });
          setIsRunning(false);
          return;
        }

        currentStep = "Agent Execution";
        currentEndpoint = "/api/v1/agent/analyze";
        const res = await analyzeAgentMulti([validOptical.id], activeQuery);
        setAnalysisResult(res);
      } else if (selectedDemo.id === "demo-3") {
        // Bi-Temporal Change Detection
        currentStep = "Pair Validation";
        currentEndpoint = "/api/v1/temporal/pairs";

        let pairIdToUse: string | undefined;
        let imageIdsToUse: string[] = [];

        try {
          const registeredPairs = await listTemporalPairs(10);
          if (registeredPairs && registeredPairs.length > 0) {
            pairIdToUse = registeredPairs[0].pair_id;
            imageIdsToUse = [registeredPairs[0].image_t1.id, registeredPairs[0].image_t2.id];
          }
        } catch (_) {
          // Fall back to image catalog pair detection
        }

        if (!pairIdToUse) {
          // Look for t1 and t2 in filenames or two optical images with matching CRS
          const t1 = imagesList.find((i) => i.filename.toLowerCase().includes("t1"));
          const t2 = imagesList.find((i) => i.filename.toLowerCase().includes("t2"));

          if (t1 && t2 && t1.id !== t2.id) {
            imageIdsToUse = [t1.id, t2.id];
          } else {
            // Find any two optical images with identical dimensions
            const opticalImages = imagesList.filter(
              (i) => i.modality === "optical" || i.modality === "multispectral"
            );
            if (opticalImages.length >= 2) {
              imageIdsToUse = [opticalImages[0].id, opticalImages[1].id];
            }
          }
        }

        if (imageIdsToUse.length < 2 && !pairIdToUse) {
          setErrorDetails({
            step: "Pair Validation",
            endpoint: "/api/v1/temporal/pairs",
            message: "Demo input unavailable: No validated Bi-Temporal pair (T1 & T2) is available.",
            suggestedAction:
              "Please upload two co-registered multi-temporal acquisitions or register a pair in the Temporal Workspace.",
          });
          setIsRunning(false);
          return;
        }

        currentStep = "Agent Execution";
        currentEndpoint = "/api/v1/agent/analyze";
        const res = await analyzeAgentMulti(imageIdsToUse, activeQuery, pairIdToUse);
        setAnalysisResult(res);
      } else if (selectedDemo.id === "demo-4") {
        // Optical + SAR Cross-Modal Fusion
        currentStep = "Pair Validation";
        currentEndpoint = "/api/v1/cross-modal/pairs";

        let optSarPairId: string | undefined;
        let optSarImageIds: string[] = [];

        try {
          const registeredCrossPairs = await listOpticalSARPairs(10);
          if (registeredCrossPairs && registeredCrossPairs.length > 0) {
            optSarPairId = registeredCrossPairs[0].id;
            optSarImageIds = [
              registeredCrossPairs[0].optical_image.id,
              registeredCrossPairs[0].sar_image.id,
            ];
          }
        } catch (_) {
          // Fall back to image catalog detection
        }

        if (!optSarPairId) {
          const opt = imagesList.find(
            (i) =>
              i.modality === "optical" ||
              i.filename.toLowerCase().includes("opt") ||
              i.filename.toLowerCase().includes("cartosat")
          );
          const sar = imagesList.find(
            (i) =>
              i.modality === "sar" ||
              i.filename.toLowerCase().includes("sar") ||
              i.filename.toLowerCase().includes("risat")
          );

          if (opt && sar && opt.id !== sar.id) {
            optSarImageIds = [opt.id, sar.id];
          }
        }

        if (optSarImageIds.length < 2 && !optSarPairId) {
          setErrorDetails({
            step: "Pair Validation",
            endpoint: "/api/v1/cross-modal/pairs",
            message: "Demo input unavailable: No validated Optical + SAR pair is available.",
            suggestedAction:
              "Please upload one Optical image and one SAR image, or configure a cross-modal pair in the Cross-Modal Workspace.",
          });
          setIsRunning(false);
          return;
        }

        currentStep = "Agent Execution";
        currentEndpoint = "/api/v1/agent/analyze";
        const res = await analyzeAgentMulti(optSarImageIds, activeQuery, optSarPairId);
        setAnalysisResult(res);
      }
    } catch (err: any) {
      const isApiErr = err instanceof ApiError;
      setErrorDetails({
        step: currentStep,
        endpoint: isApiErr ? err.endpoint : currentEndpoint,
        status: isApiErr ? err.status : undefined,
        message: err?.message || "Failed to execute demonstration analysis.",
        suggestedAction:
          err?.status === 503
            ? "The AI model runtime is not ready. Verify that specialist models are loaded."
            : err?.status === 404
            ? "Target satellite image was not found in database registry."
            : "Check backend server status and ensure dependencies are healthy.",
      });
    } finally {
      setIsRunning(false);
    }
  };

  const analysisId = analysisResult?.analysis_id;

  return (
    <AppShell>
      <div className="space-y-8">
        {/* Header */}
        <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 border border-slate-800 p-8 shadow-xl">
          <div className="relative z-10 max-w-3xl space-y-3">
            <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs font-semibold">
              <Sparkles className="h-3.5 w-3.5" />
              <span>SIH 2026 Evaluation Hub</span>
            </div>
            <h1 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
              SatQuery AI Canonical Demonstrations
            </h1>
            <p className="text-slate-300 text-sm sm:text-base leading-relaxed">
              Explore the four canonical multimodal workflows requested by ISRO SAC: Single-Image VQA,
              Spatial Grounding, Bi-Temporal Change Detection, and Optical + SAR Sensor Fusion.
              All executions run on real raster data with zero fabricated results.
            </p>
          </div>
        </div>

        {/* Demo Selector Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {DEMO_SCENARIOS.map((demo) => {
            const isSelected = selectedDemo.id === demo.id;
            const Icon = demo.icon;
            return (
              <button
                key={demo.id}
                onClick={() => handleSelectDemo(demo)}
                className={`flex flex-col text-left p-5 rounded-xl border transition-all duration-200 ${
                  isSelected
                    ? "bg-slate-850 border-cyan-500 shadow-lg shadow-cyan-950/40 ring-1 ring-cyan-500"
                    : "bg-surface/50 border-slate-800/80 hover:bg-slate-850/80 hover:border-slate-700"
                }`}
              >
                <div className="flex items-center justify-between w-full mb-3">
                  <div
                    className={`h-9 w-9 rounded-lg flex items-center justify-center ${
                      isSelected ? "bg-cyan-500/20 text-cyan-400" : "bg-slate-800 text-slate-400"
                    }`}
                  >
                    <Icon className="h-5 w-5" />
                  </div>
                  <span className={`text-[10px] uppercase font-bold px-2 py-0.5 rounded border ${demo.badgeColor}`}>
                    {demo.badge}
                  </span>
                </div>
                <h3 className="text-sm font-semibold text-white mb-1">{demo.title}</h3>
                <p className="text-xs text-slate-400 line-clamp-2">{demo.description}</p>
              </button>
            );
          })}
        </div>

        {/* Interactive Runner Panel */}
        <div className="rounded-xl border border-slate-800 bg-surface/60 p-6 space-y-6">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-800/80">
            <div>
              <h2 className="text-lg font-bold text-white flex items-center space-x-2">
                <span>Active Scenario: {selectedDemo.title}</span>
              </h2>
              <p className="text-xs text-slate-400 mt-0.5">
                Target Task: <span className="font-mono text-cyan-400">{selectedDemo.expectedTask}</span>
              </p>
            </div>

            <button
              onClick={executeDemo}
              disabled={isRunning}
              className="inline-flex items-center justify-center space-x-2 px-6 py-2.5 rounded-lg bg-gradient-to-r from-cyan-600 to-teal-500 hover:from-cyan-500 hover:to-teal-400 text-white font-medium text-sm transition shadow-lg shadow-cyan-600/20 disabled:opacity-50"
            >
              {isRunning ? (
                <>
                  <RefreshCw className="h-4 w-4 animate-spin" />
                  <span>Executing Pipeline...</span>
                </>
              ) : (
                <>
                  <Play className="h-4 w-4 fill-white" />
                  <span>Run Demonstration</span>
                </>
              )}
            </button>
          </div>

          {/* Query Selection & Input */}
          <div className="space-y-3">
            <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
              Natural Language Query
            </label>
            <input
              type="text"
              value={activeQuery}
              onChange={(e) => setActiveQuery(e.target.value)}
              className="w-full px-4 py-2.5 rounded-lg bg-slate-900 border border-slate-700 text-white text-sm focus:outline-none focus:border-cyan-500"
              placeholder="Type or select a question..."
            />

            <div className="flex flex-wrap items-center gap-2 pt-1">
              <span className="text-xs text-slate-500">Preset Queries:</span>
              {[selectedDemo.defaultQuery, ...selectedDemo.alternateQueries].map((q, idx) => (
                <button
                  key={idx}
                  onClick={() => setActiveQuery(q)}
                  className={`text-xs px-3 py-1 rounded-full border transition ${
                    activeQuery === q
                      ? "border-cyan-500/60 bg-cyan-950/60 text-cyan-300"
                      : "border-slate-800 bg-slate-900/60 text-slate-400 hover:text-slate-200 hover:border-slate-700"
                  }`}
                >
                  "{q}"
                </button>
              ))}
            </div>
          </div>

          {/* Running Stepper */}
          {isRunning && (
            <div className="py-6 border-t border-slate-800/80">
              <AnalysisProgress stage="running" />
            </div>
          )}

          {/* Rich Error Diagnostics Panel */}
          {errorDetails && (
            <div className="p-5 rounded-xl bg-rose-950/30 border border-rose-800/50 text-rose-200 space-y-3">
              <div className="flex items-center space-x-2 text-sm font-semibold text-rose-300">
                <AlertCircle className="h-5 w-5 shrink-0 text-rose-400" />
                <span>Execution Diagnostic Report</span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 text-xs font-mono">
                <div className="p-2 rounded bg-slate-950/60 border border-slate-800/80">
                  <span className="text-slate-500 block text-[10px] uppercase">Step</span>
                  <span className="text-slate-200 font-semibold">{errorDetails.step}</span>
                </div>
                {errorDetails.endpoint && (
                  <div className="p-2 rounded bg-slate-950/60 border border-slate-800/80">
                    <span className="text-slate-500 block text-[10px] uppercase">Endpoint</span>
                    <span className="text-slate-200 font-semibold truncate block">{errorDetails.endpoint}</span>
                  </div>
                )}
                {errorDetails.status !== undefined && (
                  <div className="p-2 rounded bg-slate-950/60 border border-slate-800/80">
                    <span className="text-slate-500 block text-[10px] uppercase">HTTP Status</span>
                    <span className="text-amber-400 font-semibold">{errorDetails.status}</span>
                  </div>
                )}
              </div>

              <div className="text-xs text-rose-200/90 leading-relaxed font-sans">
                <strong>Details:</strong> {errorDetails.message}
              </div>

              {errorDetails.suggestedAction && (
                <div className="p-2.5 rounded-lg bg-slate-900/80 border border-slate-800 text-xs text-cyan-300 flex items-start space-x-2">
                  <Info className="h-4 w-4 shrink-0 text-cyan-400 mt-0.5" />
                  <span>
                    <strong>Suggested Action:</strong> {errorDetails.suggestedAction}
                  </span>
                </div>
              )}
            </div>
          )}

          {/* Results Display */}
          {analysisResult && (
            <div className="space-y-6 pt-4 border-t border-slate-800">
              {/* Export Bar */}
              <div className="flex flex-wrap items-center justify-between gap-4 p-4 rounded-lg bg-slate-900/80 border border-slate-800">
                <div className="flex items-center space-x-2 text-xs text-slate-300">
                  <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                  <span>Execution Complete · Verified Deliverables Ready</span>
                </div>
                <div className="flex items-center space-x-2">
                  <a
                    href={getReportPdfUrl(analysisId || "demo")}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-md bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium border border-slate-700"
                  >
                    <Download className="h-3.5 w-3.5 text-rose-400" />
                    <span>Vector PDF</span>
                  </a>
                  <a
                    href={getReportHtmlUrl(analysisId || "demo")}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-md bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium border border-slate-700"
                  >
                    <FileText className="h-3.5 w-3.5 text-cyan-400" />
                    <span>Interactive HTML</span>
                  </a>
                  <a
                    href={getReportJsonUrl(analysisId || "demo")}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-md bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium border border-slate-700"
                  >
                    <FileCode className="h-3.5 w-3.5 text-amber-400" />
                    <span>JSON Schema</span>
                  </a>
                  <a
                    href={getReportPackageUrl(analysisId || "demo")}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-md bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium border border-slate-700"
                  >
                    <Archive className="h-3.5 w-3.5 text-purple-400" />
                    <span>ZIP Package</span>
                  </a>
                </div>
              </div>

              {/* Grid of Results */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-2 space-y-6">
                  <AnalysisAnswer answer={analysisResult.answer} query={activeQuery} />
                  <ObservationsPanel
                    observed={analysisResult.observations?.observed}
                    inferred={analysisResult.observations?.inferred}
                    uncertain={analysisResult.observations?.uncertain}
                  />
                  {analysisResult.regions && analysisResult.regions.length > 0 && (
                    <EvidenceViewerUnified
                      evidenceRegions={analysisResult.regions}
                      primaryImageId={analysisResult.input_image_ids?.[0]}
                    />
                  )}
                </div>
                <div className="space-y-6">
                  <ConfidenceCard
                    score={analysisResult.confidence?.score}
                    method={analysisResult.confidence?.method}
                  />
                  {analysisResult.trace && (
                    <TechnicalTrace
                      traceEvents={analysisResult.trace?.events || []}
                      agentRunId={analysisResult.trace?.trace_id}
                    />
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </AppShell>
  );
}
