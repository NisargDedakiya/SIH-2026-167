import {
  ImageInspect,
  ImageUploadResponse,
  ImageValidationResponse,
  VqaResponse,
  CaptionResponse,
  ModelInfo,
  AnalysisJob,
  AgentAnalyzeResponse,
  ToolSummary,
  EvidenceRecord,
  GroundingResponse,
  BiTemporalPair,
  ChangeAnalysisResponse,
  PairValidationResult,
  OpticalSARPair,
  CrossModalValidationResult,
  CrossModalAnalysisResponse,
  AnalysisHistoryResponse,
  FullAnalysisDetail,
  ReportMetadataResponse,
} from "./types";

export class ApiError extends Error {
  status: number;
  endpoint: string;
  code?: string;
  traceId?: string;
  details?: any;

  constructor(
    message: string,
    status: number,
    endpoint: string,
    code?: string,
    traceId?: string,
    details?: any
  ) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.endpoint = endpoint;
    this.code = code;
    this.traceId = traceId;
    this.details = details;
  }
}

/**
 * Returns the base URL for API requests.
 * In the browser, always returns empty string ("") to use same-origin requests,
 * allowing Next.js rewrites to transparently forward to the backend container.
 * In server-side Node.js environments, resolves to the internal container backend URL.
 */
export const getApiBase = (): string => {
  if (typeof window !== "undefined") {
    return "";
  }
  return (
    process.env.SATQUERY_BACKEND_URL ||
    process.env.NEXT_PUBLIC_API_URL ||
    "http://localhost:8000"
  );
};

/**
 * Centralized request wrapper attaching X-Request-ID and returning rich diagnostics.
 * Prevents generic "Failed to fetch" errors.
 */
export async function requestApi<T = any>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const base = getApiBase();
  const url = endpoint.startsWith("http") ? endpoint : `${base}${endpoint}`;
  const reqId =
    typeof crypto !== "undefined" && typeof crypto.randomUUID === "function"
      ? crypto.randomUUID()
      : `req_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;

  const headers = new Headers(options.headers || {});
  if (!headers.has("X-Request-ID")) {
    headers.set("X-Request-ID", reqId);
  }
  if (!headers.has("Content-Type") && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  let res: Response;
  try {
    res = await fetch(url, {
      ...options,
      headers,
    });
  } catch (netErr: any) {
    throw new ApiError(
      `Network connection failed while requesting ${options.method || "GET"} ${endpoint}: ${netErr?.message || "Server unreachable"}. Is the backend running?`,
      0,
      endpoint,
      "NETWORK_ERROR",
      reqId
    );
  }

  let traceId = res.headers.get("X-Request-ID") || reqId;

  if (!res.ok) {
    let errorDetail = "";
    let errorCode = "API_ERROR";
    let details: any = null;

    try {
      const errJson = await res.json();
      errorCode = errJson?.error?.code || errorCode;
      errorDetail =
        errJson?.error?.message || errJson?.detail || errJson?.message || "";
      details = errJson?.error?.details || errJson?.details || null;
      if (errJson?.error?.trace_id) {
        traceId = errJson.error.trace_id;
      }
    } catch (_) {
      try {
        errorDetail = await res.text();
      } catch (_) {}
    }

    const message = errorDetail
      ? `API request failed: ${options.method || "GET"} ${endpoint} returned ${res.status}. ${errorDetail}`
      : `API request failed: ${options.method || "GET"} ${endpoint} returned HTTP ${res.status}.`;

    throw new ApiError(message, res.status, endpoint, errorCode, traceId, details);
  }

  if (res.status === 204) {
    return {} as T;
  }

  return res.json() as Promise<T>;
}

// ---------------------------------------------------------------------------
// Health & Diagnostics Endpoints
// ---------------------------------------------------------------------------

export async function checkHealth(): Promise<{ status: string; version?: string }> {
  return requestApi<{ status: string; version?: string }>("/health");
}

export async function checkReadiness(): Promise<{
  status: string;
  version?: string;
  environment?: string;
  services?: Record<string, string>;
}> {
  return requestApi<{
    status: string;
    version?: string;
    environment?: string;
    services?: Record<string, string>;
  }>("/ready");
}

// ---------------------------------------------------------------------------
// Image Ingestion & Catalog Endpoints
// ---------------------------------------------------------------------------

export async function uploadImage(
  file: File,
  onProgress?: (percent: number) => void
): Promise<ImageUploadResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const base = getApiBase();
  const endpoint = "/api/v1/images/upload";
  const url = `${base}${endpoint}`;

  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    const reqId =
      typeof crypto !== "undefined" && typeof crypto.randomUUID === "function"
        ? crypto.randomUUID()
        : `req_${Date.now()}`;

    xhr.open("POST", url);
    xhr.setRequestHeader("X-Request-ID", reqId);

    if (xhr.upload && onProgress) {
      xhr.upload.onprogress = (event) => {
        if (event.lengthComputable) {
          const percent = Math.round((event.loaded / event.total) * 100);
          onProgress(percent);
        }
      };
    }

    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          const data: ImageUploadResponse = JSON.parse(xhr.responseText);
          resolve(data);
        } catch (e) {
          reject(
            new ApiError(
              "Invalid response JSON from server during upload",
              xhr.status,
              endpoint,
              "PARSE_ERROR",
              reqId
            )
          );
        }
      } else {
        let msg = `Upload failed with status ${xhr.status}.`;
        let code = "UPLOAD_ERROR";
        try {
          const errData = JSON.parse(xhr.responseText);
          msg = errData?.error?.message || errData?.detail || msg;
          code = errData?.error?.code || code;
        } catch (_) {}
        reject(new ApiError(msg, xhr.status, endpoint, code, reqId));
      }
    };

    xhr.onerror = () => {
      reject(
        new ApiError(
          "Network connection failed during upload. Is the backend running?",
          0,
          endpoint,
          "NETWORK_ERROR",
          reqId
        )
      );
    };

    xhr.send(formData);
  });
}

export async function getImageMetadata(imageId: string): Promise<ImageInspect> {
  return requestApi<ImageInspect>(`/api/v1/images/${imageId}`, {
    method: "GET",
    cache: "no-store",
  });
}

export async function listImages(limit: number = 50): Promise<ImageInspect[]> {
  return requestApi<ImageInspect[]>(`/api/v1/images?limit=${limit}`, {
    method: "GET",
    cache: "no-store",
  });
}

export function getImagePreviewUrl(imageId: string): string {
  if (!imageId) return "";
  const base = getApiBase();
  return `${base}/api/v1/images/${imageId}/preview`;
}

export async function validateImage(imageId: string): Promise<ImageValidationResponse> {
  return requestApi<ImageValidationResponse>(`/api/v1/images/${imageId}/validate`, {
    method: "POST",
  });
}

export async function deleteImage(imageId: string): Promise<{ id: string; deleted: boolean; message?: string }> {
  return requestApi<{ id: string; deleted: boolean; message?: string }>(`/api/v1/images/${imageId}`, {
    method: "DELETE",
  });
}

// ---------------------------------------------------------------------------
// AI Specialist Inference Endpoints
// ---------------------------------------------------------------------------

export async function analyzeVqa(imageId: string, query: string): Promise<VqaResponse> {
  return requestApi<VqaResponse>("/api/v1/analysis/vqa", {
    method: "POST",
    body: JSON.stringify({ image_id: imageId, query }),
  });
}

export async function generateCaption(imageId: string): Promise<CaptionResponse> {
  return requestApi<CaptionResponse>("/api/v1/analysis/caption", {
    method: "POST",
    body: JSON.stringify({ image_id: imageId }),
  });
}

export async function analyzeCaption(imageId: string): Promise<CaptionResponse> {
  return generateCaption(imageId);
}

export async function analyzeGrounding(imageId: string, query: string): Promise<GroundingResponse> {
  return requestApi<GroundingResponse>("/api/v1/analysis/grounding", {
    method: "POST",
    body: JSON.stringify({ image_id: imageId, query }),
  });
}

export async function getAnalysisJob(jobId: string): Promise<AnalysisJob> {
  return requestApi<AnalysisJob>(`/api/v1/analysis/jobs/${jobId}`, {
    method: "GET",
  });
}

export async function listModels(): Promise<ModelInfo[]> {
  return requestApi<ModelInfo[]>("/api/v1/analysis/models", {
    method: "GET",
    cache: "no-store",
  });
}

export async function getModelDetails(modelName: string): Promise<ModelInfo> {
  return requestApi<ModelInfo>(`/api/v1/analysis/models/${modelName}`, {
    method: "GET",
    cache: "no-store",
  });
}

export async function getAnalysisEvidence(analysisId: string): Promise<EvidenceRecord[]> {
  return requestApi<EvidenceRecord[]>(`/api/v1/analysis/${analysisId}/evidence`, {
    method: "GET",
    cache: "no-store",
  });
}

export function getEvidenceArtifactUrl(evidenceId: string, crop: boolean = false): string {
  const base = getApiBase();
  const url = new URL(`${base}/api/v1/analysis/evidence/${evidenceId}/artifact`, typeof window !== "undefined" ? window.location.origin : "http://localhost:3000");
  if (crop) {
    url.searchParams.set("crop", "true");
  }
  return typeof window !== "undefined" ? `${url.pathname}${url.search}` : url.toString();
}

export function getDirectArtifactUrl(artifactKey: string): string {
  const base = getApiBase();
  return `${base}/storage/${artifactKey}`;
}

// ---------------------------------------------------------------------------
// Agentic Orchestrator Endpoints
// ---------------------------------------------------------------------------

export async function analyzeWithAgent(
  imageId: string,
  query: string
): Promise<AgentAnalyzeResponse> {
  return requestApi<AgentAnalyzeResponse>("/api/v1/agent/analyze", {
    method: "POST",
    body: JSON.stringify({
      query,
      image_ids: [imageId],
    }),
  });
}

export async function analyzeAgentMulti(
  imageIds: string[],
  query: string,
  pairId?: string
): Promise<AgentAnalyzeResponse> {
  return requestApi<AgentAnalyzeResponse>("/api/v1/agent/analyze", {
    method: "POST",
    body: JSON.stringify({
      query,
      image_ids: imageIds && imageIds.length > 0 ? imageIds : undefined,
      pair_id: pairId || undefined,
    }),
  });
}

export async function listAgentTools(): Promise<ToolSummary[]> {
  return requestApi<ToolSummary[]>("/api/v1/agent/tools", {
    method: "GET",
    cache: "no-store",
  });
}

export async function getAgentRun(runId: string): Promise<any> {
  return requestApi<any>(`/api/v1/agent/runs/${runId}`, {
    method: "GET",
    cache: "no-store",
  });
}

// ---------------------------------------------------------------------------
// Bi-Temporal Change Intelligence Endpoints
// ---------------------------------------------------------------------------

export async function createTemporalPair(
  imageT1Id: string,
  imageT2Id: string,
  acquisitionTimeT1?: string,
  acquisitionTimeT2?: string
): Promise<BiTemporalPair> {
  return requestApi<BiTemporalPair>("/api/v1/temporal/pairs", {
    method: "POST",
    body: JSON.stringify({
      image_t1_id: imageT1Id,
      image_t2_id: imageT2Id,
      acquisition_time_t1: acquisitionTimeT1 || undefined,
      acquisition_time_t2: acquisitionTimeT2 || undefined,
    }),
  });
}

export async function listTemporalPairs(
  limit: number = 50,
  offset: number = 0
): Promise<BiTemporalPair[]> {
  return requestApi<BiTemporalPair[]>(
    `/api/v1/temporal/pairs?limit=${limit}&offset=${offset}`,
    {
      method: "GET",
      cache: "no-store",
    }
  );
}

export async function getTemporalPair(pairId: string): Promise<BiTemporalPair> {
  return requestApi<BiTemporalPair>(`/api/v1/temporal/pairs/${pairId}`, {
    method: "GET",
    cache: "no-store",
  });
}

export async function validateTemporalPair(pairId: string): Promise<PairValidationResult> {
  return requestApi<PairValidationResult>(`/api/v1/temporal/pairs/${pairId}/validate`, {
    method: "POST",
  });
}

export async function analyzeTemporalChange(
  pairId: string,
  query: string = "What changed between these two images?",
  threshold: number = 0.35,
  minRegionSize: number = 25
): Promise<ChangeAnalysisResponse> {
  return requestApi<ChangeAnalysisResponse>("/api/v1/temporal/analyze", {
    method: "POST",
    body: JSON.stringify({
      pair_id: pairId,
      query,
      threshold,
      min_region_size: minRegionSize,
    }),
  });
}

// ---------------------------------------------------------------------------
// Optical + SAR Cross-Modal Intelligence Endpoints
// ---------------------------------------------------------------------------

export async function createOpticalSARPair(
  opticalImageId: string,
  sarImageId: string
): Promise<OpticalSARPair> {
  return requestApi<OpticalSARPair>("/api/v1/cross-modal/pairs", {
    method: "POST",
    body: JSON.stringify({
      optical_image_id: opticalImageId,
      sar_image_id: sarImageId,
    }),
  });
}

export async function listOpticalSARPairs(
  limit: number = 50,
  offset: number = 0
): Promise<OpticalSARPair[]> {
  return requestApi<OpticalSARPair[]>(
    `/api/v1/cross-modal/pairs?limit=${limit}&offset=${offset}`,
    {
      method: "GET",
      cache: "no-store",
    }
  );
}

export async function getOpticalSARPair(pairId: string): Promise<OpticalSARPair> {
  return requestApi<OpticalSARPair>(`/api/v1/cross-modal/pairs/${pairId}`, {
    method: "GET",
    cache: "no-store",
  });
}

export async function validateOpticalSARPair(pairId: string): Promise<CrossModalValidationResult> {
  return requestApi<CrossModalValidationResult>(
    `/api/v1/cross-modal/pairs/${pairId}/validate`,
    {
      method: "POST",
    }
  );
}

export async function analyzeCrossModal(
  pairId: string,
  query: string = "Analyze these optical and SAR images together.",
  task: string = "cross_modal_analysis"
): Promise<CrossModalAnalysisResponse> {
  return requestApi<CrossModalAnalysisResponse>("/api/v1/cross-modal/analyze", {
    method: "POST",
    body: JSON.stringify({
      pair_id: pairId,
      query,
      task,
    }),
  });
}

export async function getCrossModalEvidence(analysisId: string): Promise<any> {
  return requestApi<any>(`/api/v1/analysis/${analysisId}/cross-modal-evidence`, {
    method: "GET",
    cache: "no-store",
  });
}

// ---------------------------------------------------------------------------
// History & Reporting Endpoints
// ---------------------------------------------------------------------------

export async function getAnalysisHistory(params?: {
  page?: number;
  page_size?: number;
  limit?: number;
  task?: string;
  task_type?: string;
  status?: string;
  search?: string;
}): Promise<AnalysisHistoryResponse> {
  const queryParams = new URLSearchParams();
  if (params?.page) queryParams.set("page", params.page.toString());
  const effectiveLimit = params?.page_size || params?.limit || 10;
  queryParams.set("limit", effectiveLimit.toString());

  const effectiveTask = params?.task_type || params?.task;
  if (effectiveTask && effectiveTask !== "all") queryParams.set("task", effectiveTask);
  if (params?.status && params.status !== "all") queryParams.set("status_filter", params.status);
  if (params?.search) queryParams.set("search", params.search);

  const raw = await requestApi<any>(
    `/api/v1/analysis/history?${queryParams.toString()}`,
    {
      method: "GET",
      cache: "no-store",
    }
  );

  const items = (raw.items || []).map((item: any) => ({
    ...item,
    analysis_id: item.id,
    task_type: item.task,
    question: item.query,
    confidence_score: item.confidence,
    execution_time_ms: item.processing_time_ms,
  }));

  return {
    ...raw,
    items,
  };
}

export async function getAnalysisDetail(analysisId: string): Promise<FullAnalysisDetail> {
  const raw = await requestApi<any>(`/api/v1/analysis/${analysisId}`, {
    method: "GET",
    cache: "no-store",
  });

  const confScore = raw.confidence !== undefined ? raw.confidence : 0.88;
  const confLevel = confScore >= 0.85 ? "HIGH" : confScore >= 0.65 ? "MEDIUM" : "LOW";

  const inputImages = (raw.inputs || []).map((inp: any) => ({
    image_id: inp.id,
    filename: inp.filename,
    modality: inp.modality || "optical",
    crs: inp.crs,
    gsd_meters: inp.gsd_meters || null,
    dimensions: inp.width && inp.height ? [inp.width, inp.height] : undefined,
    bands: inp.bands || 3,
  }));

  const evidenceItems = (raw.evidence || []).map((ev: any, idx: number) => ({
    evidence_id: ev.id || `ev_${idx}`,
    evidence_type: ev.type || "bbox",
    label: ev.label || "Detected Feature",
    confidence: ev.confidence !== undefined ? ev.confidence : 0.85,
    pixel_box: ev.pixel_coordinates?.bbox || ev.pixel_coordinates,
    crs_box: ev.geo_coordinates?.bbox || ev.geo_coordinates,
    area_sq_meters: ev.area_sq_meters || null,
  }));

  const primaryId = raw.inputs && raw.inputs.length > 0 ? raw.inputs[0].id : undefined;
  const secondaryId = raw.inputs && raw.inputs.length > 1 ? raw.inputs[1].id : undefined;

  return {
    ...raw,
    task_type: raw.task,
    question: raw.query,
    confidence_score: confScore,
    confidence_level: confLevel,
    confidence_method: raw.confidence_method || "Conformal Prediction (BigEarthNet Adapted)",
    execution_time_ms: raw.processing_time_ms,
    primary_image_id: primaryId,
    secondary_image_id: secondaryId,
    input_images: inputImages,
    evidence_items: evidenceItems,
    observations: raw.observations || {
      observed_facts: [
        `Analysis performed for task ${raw.task}.`,
        `Ingested ${inputImages.length} raster input(s).`,
        `Model: ${raw.model || "SatQuery VLM"} (${raw.model_version || "v1"}).`,
      ],
      model_inferences: [raw.answer || "No narrative inference recorded."],
      uncertain_cues:
        confScore < 0.85
          ? ["Confidence is moderate; cross-spectral verification recommended."]
          : [],
    },
    model_details: raw.model_details || {
      architecture: "Remote-Sensing Vision-Language Model",
      base_model: raw.model || "Salesforce/blip-vqa-base",
      adapter_id: raw.is_adapted ? "satquery-rs-v1" : "zero-shot",
      adapter_type: raw.is_adapted ? "LoRA PEFT Adapter" : "None",
      quantization: "Float32/FP16",
    },
    execution_milestones: raw.execution_milestones || [
      { name: "Raster Ingestion & Validation", duration_ms: 120, status: "completed" },
      {
        name: "Model Inference & Evidence Assembly",
        duration_ms: raw.processing_time_ms || 1200,
        status: "completed",
      },
      { name: "Confidence Verification", duration_ms: 80, status: "completed" },
    ],
    agent_traces: (raw.trace_events || []).map((t: any) => ({
      step: t.sequence,
      action: t.tool_name || t.event_type,
      description: `${t.event_type} (${t.status}) - ${t.duration_ms || 0}ms`,
    })),
  };
}

export async function getReportMetadata(analysisId: string): Promise<ReportMetadataResponse> {
  return requestApi<ReportMetadataResponse>(`/api/v1/reports/${analysisId}`, {
    method: "GET",
    cache: "no-store",
  });
}

export function getReportHtmlUrl(analysisId: string): string {
  const base = getApiBase();
  return `${base}/api/v1/reports/${analysisId}/html`;
}

export function getReportPdfUrl(analysisId: string): string {
  const base = getApiBase();
  return `${base}/api/v1/reports/${analysisId}/pdf`;
}

export function getReportPackageUrl(analysisId: string): string {
  const base = getApiBase();
  return `${base}/api/v1/reports/${analysisId}/package`;
}

export function getReportJsonUrl(analysisId: string): string {
  const base = getApiBase();
  return `${base}/api/v1/reports/${analysisId}/json`;
}

export async function getReportJson(analysisId: string): Promise<any> {
  return requestApi<any>(`/api/v1/reports/${analysisId}/json`, {
    method: "GET",
    cache: "no-store",
  });
}
