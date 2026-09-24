import type { Metadata } from "next";
import "./globals.css";
import { AppShell } from "@/components/app-shell";

export const metadata: Metadata = {
  title: "SatQuery AI — Agentic Remote-Sensing Intelligence",
  description: "Multimodal Remote Sensing Image Analysis & Geospatial Ingestion for ISRO SIH Problem 26167",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-background text-slate-100 min-h-screen flex flex-col space-grid">
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
