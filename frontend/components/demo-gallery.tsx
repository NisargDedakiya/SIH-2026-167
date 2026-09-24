"use client";

import React from "react";
import { Sparkles, ArrowRight, Layers, Target, GitCompare, Radio, FileText } from "lucide-react";
import Link from "next/link";

interface DemoPreset {
  id: string;
  title: string;
  category: string;
  icon: any;
  query: string;
  description: string;
  badge: string;
  href: string;
}

export function DemoGallery() {
  const presets: DemoPreset[] = [
    {
      id: "demo_vqa",
      title: "Remote-Sensing VQA",
      category: "Single Image",
      icon: Layers,
      query: "What is the dominant land cover class in this satellite patch?",
      description: "Fine-tuned on BigEarthNet v2.0; outputs standardized CORINE Land Cover classes.",
      badge: "BigEarthNet LoRA",
      href: "/analyze?demo=vqa",
    },
    {
      id: "demo_grounding",
      title: "Text-Guided Grounding",
      category: "Grounding",
      icon: Target,
      query: "Locate and draw bounding boxes around the industrial storage tanks.",
      description: "Predicts pixel and geospatial bounding boxes with Recall@0.5 evaluation metrics.",
      badge: "VRSBench Test",
      href: "/analyze?demo=grounding",
    },
    {
      id: "demo_temporal",
      title: "Bi-Temporal Change",
      category: "Temporal",
      icon: GitCompare,
      query: "What specific environmental changes occurred between T1 and T2?",
      description: "Non-destructive co-registration, difference map generation, and CDVQA reasoning.",
      badge: "CDVQA Benchmark",
      href: "/temporal",
    },
    {
      id: "demo_cross_modal",
      title: "Optical + SAR Fusion",
      category: "Cross-Modal",
      icon: Radio,
      query: "Analyze these optical and SAR images together to penetrate cloud cover.",
      description: "Cartosat-2S and RISAT joint interpretation using physics-aware radar backscatter.",
      badge: "ISRO SIH Mandate",
      href: "/cross-modal",
    },
    {
      id: "demo_report",
      title: "Formal Analysis Report",
      category: "Export",
      icon: FileText,
      query: "Generate interactive HTML, ReportLab PDF, and machine JSON certificates.",
      description: "Publication-grade multi-page document with embedded evidence rasters and limitations.",
      badge: "PDF / HTML / ZIP",
      href: "/reports",
    },
  ];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-mono font-bold uppercase tracking-wider text-white flex items-center space-x-2">
            <Sparkles className="h-4 w-4 text-cyan-400" />
            <span>Interactive Demo Scenarios</span>
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Pre-configured benchmark workflows for Hackathon jury demonstrations
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3.5">
        {presets.map((p) => {
          const IconComponent = p.icon;
          return (
            <Link
              key={p.id}
              href={p.href}
              className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 hover:border-cyan-800/60 hover:bg-slate-900/90 transition group flex flex-col justify-between space-y-3"
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <div className="p-1.5 rounded-lg bg-slate-950 text-cyan-400 border border-slate-800">
                    <IconComponent className="h-4 w-4" />
                  </div>
                  <span className="px-2 py-0.5 rounded text-[10px] font-mono font-semibold bg-cyan-950/80 text-cyan-300 border border-cyan-800/50">
                    {p.badge}
                  </span>
                </div>
                <h4 className="font-semibold text-sm text-white group-hover:text-cyan-300 transition">
                  {p.title}
                </h4>
                <p className="text-xs text-slate-400 mt-1 leading-relaxed">
                  {p.description}
                </p>
              </div>

              <div className="pt-2 border-t border-slate-800/60 flex items-center justify-between text-[11px] font-mono text-slate-500 group-hover:text-cyan-400 transition">
                <span className="truncate pr-2">&ldquo;{p.query}&rdquo;</span>
                <ArrowRight className="h-3.5 w-3.5 shrink-0 group-hover:translate-x-0.5 transition-transform" />
              </div>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
