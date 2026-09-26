import type { Metadata } from "next";
import "./globals.css";
import { AppShell } from "@/components/app-shell";

export const metadata: Metadata = {
  title: "SatQuery AI — Remote-Sensing Intelligence Platform",
  description:
    "Multimodal satellite imagery analysis with vision-language AI. Supports GeoTIFF ingestion, VQA, spatial grounding, bi-temporal change detection, and Optical+SAR fusion. ISRO SIH Problem Statement 26167.",
  keywords: "satellite imagery, remote sensing, AI analysis, GeoTIFF, VQA, change detection, SAR, ISRO",
  authors: [{ name: "SatQuery AI Team" }],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@300;400;500;600;700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="bg-background text-slate-100 min-h-screen flex flex-col sq-grid-bg">
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
