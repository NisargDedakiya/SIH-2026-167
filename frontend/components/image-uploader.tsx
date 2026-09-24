"use client";

import React, { useState, useRef } from "react";
import { useRouter } from "next/navigation";
import { UploadCloud, FileType, AlertCircle, CheckCircle2, ArrowRight } from "lucide-react";
import { uploadImage } from "@/lib/api";

interface ImageUploaderProps {
  onSuccess?: (imageId: string) => void;
  onUploadComplete?: () => void;
  maxSizeMB?: number;
}

export function ImageUploader({ onSuccess, onUploadComplete, maxSizeMB = 500 }: ImageUploaderProps) {
  const router = useRouter();
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      processFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      processFile(e.target.files[0]);
    }
  };

  const processFile = async (file: File) => {
    setError(null);

    // Client-side quick validation
    const ext = file.name.split(".").pop()?.toLowerCase();
    const validExts = ["tif", "tiff", "png", "jpg", "jpeg"];
    if (!ext || !validExts.includes(ext)) {
      setError(`Unsupported format '.${ext || ""}'. Please upload GeoTIFF (.tif, .tiff), PNG, or JPEG.`);
      return;
    }

    if (file.size > maxSizeMB * 1024 * 1024) {
      setError(`File size exceeds maximum allowable limit of ${maxSizeMB} MB.`);
      return;
    }

    try {
      setIsUploading(true);
      setProgress(10);

      const res = await uploadImage(file, (p) => {
        setProgress(p);
      });

      setProgress(100);
      setTimeout(() => {
        if (onSuccess) {
          onSuccess(res.id);
        } else {
          router.push(`/images/${res.id}`);
        }
        if (onUploadComplete) {
          onUploadComplete();
        }
      }, 500);
    } catch (err: any) {
      setIsUploading(false);
      setError(err.message || "Failed to upload image. Please try again.");
    }
  };

  return (
    <div className="w-full">
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => !isUploading && fileInputRef.current?.click()}
        className={`relative flex flex-col items-center justify-center p-8 sm:p-12 border-2 border-dashed rounded-2xl cursor-pointer transition-all duration-200 backdrop-blur-sm ${
          isDragging
            ? "border-cyan-400 bg-cyan-950/20 scale-[0.99]"
            : "border-slate-800 hover:border-slate-700 bg-surface/40 hover:bg-surface/60"
        } ${isUploading ? "pointer-events-none opacity-90" : ""}`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".tif,.tiff,.png,.jpg,.jpeg"
          onChange={handleFileSelect}
          className="hidden"
        />

        {/* Upload Icon & Graphic */}
        <div className="h-16 w-16 rounded-2xl bg-cyan-950/50 border border-cyan-800/40 flex items-center justify-center mb-4 text-cyan-400 group-hover:scale-110 transition-transform shadow-lg shadow-cyan-950/30">
          <UploadCloud className="h-8 w-8" />
        </div>

        <h3 className="text-base sm:text-lg font-semibold text-white tracking-wide text-center">
          {isDragging ? "Drop raster image here" : "Upload Remote Sensing Imagery"}
        </h3>
        <p className="text-xs sm:text-sm text-slate-400 mt-1 text-center max-w-md">
          Drag & drop your satellite raster file here, or click to browse local files.
        </p>

        {/* Format Badges */}
        <div className="flex flex-wrap items-center justify-center gap-2 mt-4 text-[11px] font-mono text-slate-400">
          <span className="px-2.5 py-1 rounded-md bg-slate-900 border border-slate-800 text-cyan-300">
            .TIF / .TIFF (GeoTIFF)
          </span>
          <span className="px-2.5 py-1 rounded-md bg-slate-900 border border-slate-800 text-slate-300">
            .PNG
          </span>
          <span className="px-2.5 py-1 rounded-md bg-slate-900 border border-slate-800 text-slate-300">
            .JPG / .JPEG
          </span>
          <span className="px-2.5 py-1 rounded-md bg-slate-900 border border-slate-800 text-slate-400">
            Max: {maxSizeMB} MB
          </span>
        </div>

        {/* Upload Progress Bar */}
        {isUploading && (
          <div className="w-full max-w-md mt-6">
            <div className="flex justify-between text-xs font-mono text-slate-300 mb-1.5">
              <span>Ingesting & Extracting Metadata...</span>
              <span>{progress}%</span>
            </div>
            <div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-cyan-500 to-teal-400 transition-all duration-200"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>
        )}
      </div>

      {/* Error Message */}
      {error && (
        <div className="mt-4 p-3 rounded-lg bg-rose-950/40 border border-rose-800/60 text-xs text-rose-300 flex items-start space-x-2">
          <AlertCircle className="h-4 w-4 shrink-0 text-rose-400 mt-0.5" />
          <span>{error}</span>
        </div>
      )}
    </div>
  );
}
