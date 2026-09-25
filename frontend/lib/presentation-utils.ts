export interface ConfidenceBadgeInfo {
  label: string;
  pct: string;
  color: string;
  level: "HIGH" | "MEDIUM" | "LOW";
}

export function formatConfidenceBadge(score?: number | null): ConfidenceBadgeInfo {
  if (score === undefined || score === null) {
    return {
      label: "Uncalibrated",
      pct: "N/A",
      color: "bg-slate-800 text-slate-400 border-slate-700",
      level: "LOW",
    };
  }

  const pct = `${Math.round(score * 100)}%`;

  if (score >= 0.85) {
    return {
      label: "High Confidence",
      pct,
      color: "bg-emerald-950/80 text-emerald-300 border-emerald-800/60",
      level: "HIGH",
    };
  } else if (score >= 0.65) {
    return {
      label: "Medium Confidence",
      pct,
      color: "bg-amber-950/80 text-amber-300 border-amber-800/60",
      level: "MEDIUM",
    };
  } else {
    return {
      label: "Low Confidence",
      pct,
      color: "bg-rose-950/80 text-rose-300 border-rose-800/60",
      level: "LOW",
    };
  }
}

export function formatTaskTypeLabel(taskType?: string | null): string {
  const norm = (taskType || "").toLowerCase();
  if (norm.includes("grounding")) return "Spatial Grounding";
  if (norm.includes("caption")) return "Scene Captioning";
  if (norm.includes("vqa") || norm === "visual_qa") return "Remote-Sensing VQA";
  if (norm.includes("temporal") || norm.includes("change")) return "Bi-Temporal Change";
  if (norm.includes("cross_modal") || norm.includes("fusion")) return "Optical + SAR Fusion";
  if (norm.includes("classification")) return "Land Cover Classification";
  return (taskType || "General Analysis").replace(/_/g, " ").toUpperCase();
}

export function formatFileSize(bytes: number): string {
  if (bytes === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
}

export function formatDuration(ms?: number): string {
  if (!ms && ms !== 0) return "N/A";
  if (ms < 1000) return `${Math.round(ms)}ms`;
  return `${(ms / 1000).toFixed(2)}s`;
}
