export interface BoundingBox {
  left: number;
  bottom: number;
  right: number;
  top: number;
}

export interface Resolution {
  x: number;
  y: number;
}

export interface RasterMetadata {
  width: number;
  height: number;
  bands: number;
  dtype: string;
  nodata: number | null;
}

export interface GeospatialMetadata {
  is_geospatial: boolean;
  crs: string | null;
  epsg: number | null;
  bounds: BoundingBox | null;
  resolution: Resolution | null;
  transform: number[] | null;
}

export interface ValidationResult {
  valid: boolean;
  warnings: string[];
  errors: string[];
}

export interface ImageInspect {
  id: string;
  filename: string;
  format: string;
  size_bytes: number;
  modality: string;
  raster: RasterMetadata;
  geospatial: GeospatialMetadata;
  validation: ValidationResult;
  width?: number;
  height?: number;
  channels?: number;
  sensor_type?: string;
  crs?: string | null;
  gsd_meters?: number | null;
  size?: number;
  metadata?: any;
}

export interface ImageUploadResponse {
  id: string;
  filename: string;
  status: "valid" | "warning" | "error";
  message: string;
}

export interface ImageValidationResponse {
  valid: boolean;
  warnings: string[];
  errors: string[];
  metadata?: ImageInspect;
}

// Phase 2: Remote-Sensing Single-Image AI Intelligence Types
export interface VqaResponse {
  analysis_id: string;
  status: string;
  task: string;
  answer: string;
  confidence: number;
  confidence_method: string;
  model: string;
  model_version: string;
  processing_time_ms: number;
  evidence: Array<Record<string, any>>;
  is_adapted?: boolean;
  adapter_id?: string;
  fallback_used?: boolean;
  fallback_reason?: string;
  adapter_metadata?: Record<string, any> | null;
  fallback?: Record<string, any> | null;
}

export interface CaptionResponse {
  analysis_id: string;
  status: string;
  task: string;
  caption: string;
  confidence: number;
  confidence_method: string;
  model: string;
  model_version: string;
  processing_time_ms: number;
  evidence: Array<Record<string, any>>;
}

export interface ModelInfo {
  name: string;
  version: string;
  task: string;
  supported_modalities: string[];
  is_default_for_task: boolean;
  is_adapted?: boolean;
  adapter_type?: string | null;
  dataset_provenance?: string | null;
  base_model?: string | null;
}

export interface AnalysisJob {
  id: string;
  image_id: string;
  task: string;
  query: string | null;
  model_name: string;
  model_version: string;
  status: string;
  result_json: Record<string, any> | null;
  confidence: number | null;
  confidence_method: string | null;
  processing_time_ms: number | null;
  error: string | null;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
}

// Phase 3: Agentic Query Router & Orchestration Types
export interface ToolSummary {
  name: string;
  version: string;
  task: string;
  status: "available" | "planned" | "completed";
  description?: string;
}

export interface TraceEvent {
  sequence: number;
  event_type: string;
  tool_name: string | null;
  status: string;
  parameters: Record<string, any> | null;
  output_metadata: Record<string, any> | null;
  duration_ms: number | null;
  timestamp: string;
}

export interface ExecutionTrace {
  trace_id: string;
  analysis_id: string | null;
  started_at: string;
  completed_at: string | null;
  original_query: string;
  normalized_query: string;
  detected_task: string;
  task_confidence: number;
  input_image_ids: string[];
  selected_tools: string[];
  tool_parameters: Record<string, any>;
  tool_status: string;
  tool_outputs: Record<string, any> | null;
  errors: string[];
  total_duration_ms: number;
  events: TraceEvent[];
}

export interface AgentConfidence {
  score: number;
  method: string;
}

export interface AgentAnalyzeResponse {
  analysis_id: string | null;
  status: "completed" | "unavailable" | "ambiguous" | "failed";
  task: string;
  answer: string;
  confidence: AgentConfidence;
  tools: ToolSummary[];
  trace_id: string;
  trace: ExecutionTrace | null;
  clarification_needed: string | null;
  processing_time_ms: number;
  evidence?: EvidenceRecord[];
  artifact_key?: string | null;
  is_adapted?: boolean;
  adapter_id?: string | null;
  fallback_used?: boolean;
  fallback_reason?: string | null;
  adapter_metadata?: Record<string, any> | null;
}

// Phase 4: Grounding & Visual Evidence Types
export interface PixelGeometry {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  width: number;
  height: number;
}

export interface GeoBounds {
  min_x: number;
  min_y: number;
  max_x: number;
  max_y: number;
}

export interface GeoGeometry {
  crs: string;
  bounds: GeoBounds;
  polygon: number[][];
  formatted: string;
}

export interface EvidenceRecord {
  id: string;
  analysis_id: string;
  image_id: string;
  type: string;
  label: string;
  confidence: number;
  geometry: number[]; // normalized [x1, y1, x2, y2] (0.0 to 1.0)
  pixel_geometry: PixelGeometry;
  geo_geometry: GeoGeometry | null;
  artifact_key: string | null;
  crop_artifact_key?: string | null;
}

export interface GroundingResponse {
  analysis_id: string;
  status: string;
  task: string;
  answer: string;
  target_expression: string;
  region_count: number;
  regions: EvidenceRecord[];
  confidence: number;
  confidence_method: string;
  model: string;
  model_version: string;
  processing_time_ms: number;
  artifact_key: string | null;
}

// Phase 5: Bi-Temporal Change Intelligence Types
export interface PairImageSummary {
  id: string;
  filename: string;
  modality: string;
  acquisition_time: string | null;
  width: number;
  height: number;
  crs: string | null;
  is_geospatial: boolean;
}

export interface PairValidationResult {
  valid: boolean;
  temporal_valid: boolean;
  spatially_compatible: boolean;
  overlap_ratio: number;
  status_code: string;
  message: string;
  warnings: string[];
  errors: string[];
}

export interface BiTemporalPair {
  pair_id: string;
  image_t1: PairImageSummary;
  image_t2: PairImageSummary;
  acquisition_time_t1: string | null;
  acquisition_time_t2: string | null;
  spatially_compatible: boolean;
  temporally_valid: boolean;
  overlap_ratio: number | null;
  alignment_status: string;
  registration_method: string | null;
  registration_metadata: Record<string, any> | null;
  validation: PairValidationResult;
  created_at: string;
}

export interface ChangeRegion {
  region_id: string;
  label: string;
  confidence: number;
  bbox: number[]; // normalized [x1, y1, x2, y2]
  pixel_geometry: PixelGeometry;
  geo_geometry: GeoGeometry | null;
  pixel_area: number;
  relative_area: number;
}

export interface ChangeAnalysisSummary {
  detected: boolean;
  change_score: number;
  change_percentage: number;
  regions_count: number;
  threshold_used?: number;
}

export interface ChangeProcessingDetails {
  alignment_performed: boolean;
  registration_method: string | null;
  model: string;
  model_version: string;
  processing_time_ms: number;
}

export interface ChangeAnalysisResponse {
  analysis_id: string;
  task: string;
  pair_id: string;
  answer: string;
  change: ChangeAnalysisSummary;
  regions: ChangeRegion[];
  confidence: {
    score: number;
    method: string;
  };
  evidence: Array<Record<string, any>>;
  processing: ChangeProcessingDetails;
  artifact_key: string | null;
  change_map_key: string | null;
  trace_id: string | null;
}

// Phase 6: Optical + SAR Cross-Modal Intelligence Types
export interface CrossModalValidationResult {
  valid: boolean;
  optical_valid: boolean;
  sar_valid: boolean;
  spatially_compatible: boolean;
  overlap_ratio: number;
  status_code: string;
  message: string;
  optical_modality: string;
  sar_modality: string;
  sar_polarization?: string | null;
  warnings: string[];
}

export interface CrossModalImageSummary {
  id: string;
  original_filename: string;
  modality: string;
  sensor?: string | null;
  crs?: string | null;
  resolution?: number | null;
  bounds?: Record<string, any> | null;
  acquisition_time?: string | null;
  band_count: number;
  dtype: string;
  polarization?: string | null;
}

export interface OpticalSARPair {
  id: string;
  optical_image: CrossModalImageSummary;
  sar_image: CrossModalImageSummary;
  optical_modality: string;
  sar_modality: string;
  optical_sensor?: string | null;
  sar_sensor?: string | null;
  spatial_compatibility: string;
  registration_status: string;
  validation_status: string;
  overlap_ratio?: number | null;
  alignment_method?: string | null;
  alignment_metadata?: Record<string, any> | null;
  validation: CrossModalValidationResult;
  created_at: string;
  updated_at: string;
}

export interface ModalityContribution {
  available: boolean;
  modality: string;
  sensor?: string | null;
  contribution: string;
  features: string[];
}

export interface ModalityDisagreement {
  agreement_status: "AGREEMENT" | "PARTIAL_AGREEMENT" | "DISAGREEMENT" | "INSUFFICIENT_EVIDENCE" | string;
  disagreement_type?: string | null;
  explanation: string;
}

export interface CrossModalEvidenceRegion {
  id: string;
  label: string;
  confidence: number;
  bbox: number[]; // normalized [ymin, xmin, ymax, xmax]
  pixel_geometry: {
    x1: number;
    y1: number;
    x2: number;
    y2: number;
    w: number;
    h: number;
  };
  geo_geometry?: Record<string, any> | null;
  supported_by: "optical" | "sar" | "both" | string;
  rationale?: string | null;
}

export interface CrossModalAnalysisRequest {
  pair_id: string;
  query?: string;
  task?: "cross_modal_analysis" | "cross_modal_vqa" | "cross_modal_grounding" | string;
}

export interface CrossModalAnalysisResponse {
  analysis_id: string;
  task: string;
  pair_id: string;
  query: string;
  answer: string;
  optical_summary: ModalityContribution;
  sar_summary: ModalityContribution;
  joint_observations: string[];
  disagreement: ModalityDisagreement;
  regions: CrossModalEvidenceRegion[];
  confidence: {
    score: number;
    method: string;
    variance?: number;
    optical_weight?: number;
    sar_weight?: number;
  };
  evidence: Array<Record<string, any>>;
  processing: {
    alignment_performed: boolean;
    fusion_method: string;
    model: string;
    model_version: string;
    processing_time_ms: number;
  };
}

// Phase 9: Evidence, Reports & Product UX Types
export interface AnalysisHistoryItem {
  id: string;
  analysis_id?: string;
  image_id?: string | null;
  pair_id?: string | null;
  cross_modal_pair_id?: string | null;
  task: string;
  task_type?: string;
  query: string;
  question?: string;
  status: string;
  answer?: string | null;
  confidence?: number | null;
  confidence_score?: number | null;
  confidence_method?: string | null;
  model_name: string;
  processing_time_ms?: number | null;
  execution_time_ms?: number | null;
  created_at?: string | null;
}

export interface AnalysisHistoryResponse {
  items: AnalysisHistoryItem[];
  total: number;
  page: number;
  limit: number;
  total_pages: number;
}

export interface FullAnalysisDetail {
  analysis_id: string;
  task?: string;
  task_type?: string;
  query?: string;
  question?: string;
  status: string;
  answer: string;
  confidence?: number | null;
  confidence_score?: number | null;
  confidence_level?: string | null;
  confidence_method?: string | null;
  model?: string;
  model_version?: string;
  processing_time_ms?: number | null;
  execution_time_ms?: number | null;
  created_at?: string | null;
  completed_at?: string | null;
  primary_image_id?: string;
  secondary_image_id?: string;
  inputs?: Array<{
    id: string;
    role: string;
    filename: string;
    modality: string;
    sensor?: string | null;
    width?: number;
    height?: number;
    crs?: string | null;
    is_geospatial?: boolean;
  }>;
  input_images?: Array<{
    image_id: string;
    filename: string;
    modality: string;
    crs?: string | null;
    gsd_meters?: number | null;
    dimensions?: [number, number];
    bands?: number;
  }>;
  evidence?: Array<{
    id: string;
    type: string;
    label: string;
    confidence?: number | null;
    pixel_coordinates?: any;
    geo_coordinates?: any;
    artifact_key?: string | null;
  }>;
  evidence_items?: Array<{
    evidence_id: string;
    evidence_type: string;
    label: string;
    confidence: number;
    pixel_box?: number[];
    crs_box?: number[];
    area_sq_meters?: number | null;
  }>;
  observations?: {
    observed_facts: string[];
    model_inferences: string[];
    uncertain_cues: string[];
  };
  model_details?: {
    architecture: string;
    base_model: string;
    adapter_id?: string;
    adapter_type?: string;
    quantization?: string;
  };
  execution_milestones?: Array<{
    name: string;
    duration_ms: number;
    status: string;
  }>;
  trace_events?: Array<{
    sequence: number;
    event_type: string;
    status: string;
    tool_name?: string | null;
    duration_ms?: number | null;
    timestamp?: string | null;
  }>;
  agent_traces?: Array<{
    step: number;
    action: string;
    description: string;
  }>;
  result?: Record<string, any>;
  is_adapted?: boolean;
}

export interface ReportMetadataResponse {
  report_id: string;
  analysis_id: string;
  generated_at: string;
  system_title: string;
  problem_statement: string;
  query: string;
  detected_task: string;
  answer: string;
  confidence_percentage?: string | null;
  calibration_status: string;
  inputs: Array<any>;
  evidence: Array<any>;
  observations: {
    observed: string[];
    inferred: string[];
    uncertain: string[];
  };
  models: Array<any>;
  execution_milestones: Array<any>;
  total_processing_time_ms: number;
  limitations: string[];
  reproducibility_token: string;
}

