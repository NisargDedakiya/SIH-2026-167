"use client";

import React, { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  RefreshCw,
  Trash2,
  AlertCircle,
  Layers,
  CheckCircle2,
  Info
} from "lucide-react";

import { ImageInspect } from "@/lib/types";
import { getImageMetadata, getImagePreviewUrl, validateImage, deleteImage } from "@/lib/api";
import { ImagePreview } from "@/components/image-preview";
import { MetadataPanel } from "@/components/metadata-panel";
import { ValidationStatus } from "@/components/validation-status";
import { QueryPanel } from "@/components/query-panel";
import { ProcessingIndicator } from "@/components/processing-indicator";

export default function ImageWorkspacePage() {
  const params = useParams();
  const router = useRouter();
  const id = params?.id as string;

  const [image, setImage] = useState<ImageInspect | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [revalidating, setRevalidating] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [deleting, setDeleting] = useState<boolean>(false);

  const fetchImage = async () => {
    if (!id) return;
    try {
      setLoading(true);
      setError(null);
      const data = await getImageMetadata(id);
      setImage(data);
    } catch (err: any) {
      setError(err.message || "Failed to load image metadata");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchImage();
  }, [id]);

  const handleRevalidate = async () => {
    if (!id) return;
    try {
      setRevalidating(true);
      const res = await validateImage(id);
      if (res.metadata) {
        setImage(res.metadata);
      }
    } catch (err: any) {
      alert("Revalidation failed: " + err.message);
    } finally {
      setRevalidating(false);
    }
  };

  const handleDelete = async () => {
    if (!id || !confirm("Are you sure you want to delete this satellite image? This cannot be undone.")) return;
    try {
      setDeleting(true);
      await deleteImage(id);
      router.push("/");
    } catch (err: any) {
      alert("Failed to delete image: " + err.message);
      setDeleting(false);
    }
  };

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto py-12">
        <ProcessingIndicator
          label="Loading Image Metadata..."
          sublabel="Fetching raster properties and geospatial projection parameters..."
        />
      </div>
    );
  }

  if (error || !image) {
    return (
      <div className="max-w-2xl mx-auto py-12 text-center space-y-4">
        <div className="p-4 rounded-xl bg-rose-950/40 border border-rose-800 text-rose-300 flex items-center justify-center space-x-2 text-sm">
          <AlertCircle className="h-5 w-5 shrink-0" />
          <span>{error || "Image not found"}</span>
        </div>
        <Link
          href="/"
          className="inline-flex items-center space-x-2 px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium transition"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          <span>Return to Ingestion Hub</span>
        </Link>
      </div>
    );
  }

  const previewUrl = getImagePreviewUrl(image.id);

  return (
    <div className="space-y-6">
      {/* Top Header & Breadcrumbs */}
      <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-4 pb-2 border-b border-slate-800/80">
        <div>
          <div className="flex items-center space-x-2 text-xs text-slate-400 mb-1">
            <Link href="/" className="hover:text-cyan-400 transition flex items-center space-x-1">
              <ArrowLeft className="h-3.5 w-3.5" />
              <span>Dashboard</span>
            </Link>
            <span>/</span>
            <span>Image Workspace</span>
          </div>
          <h1 className="text-xl sm:text-2xl font-bold text-white tracking-tight flex items-center space-x-3">
            <span className="truncate max-w-md">{image.filename}</span>
            <span className="text-xs px-2.5 py-0.5 rounded-full font-mono font-medium bg-cyan-950 border border-cyan-800/60 text-cyan-300">
              {image.format}
            </span>
          </h1>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center space-x-2">
          <button
            onClick={handleRevalidate}
            disabled={revalidating}
            className="px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 hover:border-slate-700 text-slate-300 hover:text-white text-xs font-medium flex items-center space-x-1.5 transition disabled:opacity-50"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${revalidating ? "animate-spin" : ""}`} />
            <span>{revalidating ? "Validating..." : "Revalidate"}</span>
          </button>
          <button
            onClick={handleDelete}
            disabled={deleting}
            className="px-3 py-1.5 rounded-lg bg-rose-950/40 border border-rose-900/60 hover:bg-rose-900/60 text-rose-300 text-xs font-medium flex items-center space-x-1.5 transition disabled:opacity-50"
          >
            <Trash2 className="h-3.5 w-3.5" />
            <span>{deleting ? "Deleting..." : "Delete"}</span>
          </button>
        </div>
      </div>

      {/* 1. Interactive Image Preview Component */}
      <section>
        <ImagePreview
          previewUrl={previewUrl}
          filename={image.filename}
          width={image.raster.width}
          height={image.raster.height}
          format={image.format}
        />
      </section>

      {/* 2. Validation Status Reporting */}
      <section>
        <ValidationStatus validation={image.validation} />
      </section>

      {/* 3. Granular Technical Metadata Cards */}
      <section>
        <MetadataPanel image={image} />
      </section>

      {/* 4. Future-Proof Query Panel */}
      <section>
        <QueryPanel imageId={image.id} />
      </section>
    </div>
  );
}
