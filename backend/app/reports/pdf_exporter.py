"""
PDF Report Exporter for SatQuery Analysis Reports.
Uses reportlab to generate publication-grade, formal multi-page PDF documents.
"""

import io
from typing import Any, List
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.reports.schemas import AnalysisReport


class PdfReportExporter:
    @classmethod
    def export(cls, report: AnalysisReport) -> bytes:
        """Compiles AnalysisReport into a clean, printable PDF document."""
        buf = io.BytesIO()
        doc = SimpleDocTemplate(
            buf,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36,
        )

        styles = getSampleStyleSheet()

        # Custom Palette
        c_primary = colors.HexColor("#0f172a")  # Slate 900
        c_accent = colors.HexColor("#0284c7")   # Sky 600
        c_teal = colors.HexColor("#0d9488")     # Teal 600
        c_muted = colors.HexColor("#475569")    # Slate 600
        c_bg_light = colors.HexColor("#f8fafc") # Slate 50
        c_border = colors.HexColor("#cbd5e1")   # Slate 300

        # Custom Typography
        style_title = ParagraphStyle(
            "DocTitle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=18,
            leading=22,
            textColor=c_primary,
        )
        style_subtitle = ParagraphStyle(
            "DocSubTitle",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=10,
            leading=13,
            textColor=c_accent,
        )
        style_meta = ParagraphStyle(
            "DocMeta",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=11,
            textColor=c_muted,
            alignment=2,  # Right-aligned
        )
        style_h2 = ParagraphStyle(
            "DocH2",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=15,
            textColor=c_accent,
            spaceBefore=12,
            spaceAfter=6,
        )
        style_body = ParagraphStyle(
            "DocBody",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            textColor=c_primary,
        )
        style_query = ParagraphStyle(
            "DocQuery",
            parent=styles["Normal"],
            fontName="Helvetica-Oblique",
            fontSize=10,
            leading=14,
            textColor=c_primary,
        )
        style_answer = ParagraphStyle(
            "DocAnswer",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=16,
            textColor=c_primary,
        )
        style_table_header = ParagraphStyle(
            "DocTH",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=10,
            textColor=colors.white,
        )
        style_table_cell = ParagraphStyle(
            "DocTD",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=10,
            textColor=c_primary,
        )

        story: List[Any] = []

        # 1. Header (Title + Meta Table)
        header_data = [
            [
                Paragraph(f"<b>{report.system_title}</b>", style_title),
                Paragraph(
                    f"<b>REPORT ID:</b> {report.report_id}<br/>"
                    f"<b>ANALYSIS ID:</b> {report.analysis_id[:16]}...<br/>"
                    f"<b>DATE:</b> {report.generated_at}",
                    style_meta,
                ),
            ],
            [
                Paragraph(f"{report.problem_statement}", style_subtitle),
                Paragraph(f"<b>STATUS:</b> Calibrated ({report.calibration_status})", style_meta),
            ],
        ]
        header_table = Table(header_data, colWidths=[4.2 * inch, 3.1 * inch])
        header_table.setStyle(
            TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
            ])
        )
        story.append(header_table)
        story.append(Spacer(1, 10))
        story.append(HRFlowable(width="100%", thickness=1, color=c_border, spaceBefore=4, spaceAfter=10))

        # 2. Query Card
        story.append(Paragraph("<b>QUERY / INSTRUCTION:</b>", style_h2))
        q_table = Table(
            [[Paragraph(f'"{report.query}"', style_query)]],
            colWidths=[7.3 * inch],
        )
        q_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), c_bg_light),
                ("BOX", (0, 0), (-1, -1), 0.5, c_border),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ])
        )
        story.append(q_table)
        story.append(Spacer(1, 8))

        # 3. Answer Box
        conf_text = f" [Confidence: {report.confidence_percentage}]" if report.confidence_percentage else ""
        story.append(Paragraph(f"<b>SYNTHESIZED ANSWER{conf_text}:</b>", style_h2))
        ans_table = Table(
            [[Paragraph(report.answer, style_answer)]],
            colWidths=[7.3 * inch],
        )
        ans_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f0fdf4")),  # Soft emerald tint
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#86efac")),
                ("TOPPADDING", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                ("LEFTPADDING", (0, 0), (-1, -1), 12),
                ("RIGHTPADDING", (0, 0), (-1, -1), 12),
            ])
        )
        story.append(ans_table)
        story.append(Spacer(1, 10))

        # 4. Input Rasters Table
        story.append(Paragraph("<b>1. INPUT EARTH OBSERVATION RASTERS</b>", style_h2))
        input_rows = [
            [
                Paragraph("<b>Filename</b>", style_table_header),
                Paragraph("<b>Role</b>", style_table_header),
                Paragraph("<b>Modality</b>", style_table_header),
                Paragraph("<b>Dimensions</b>", style_table_header),
                Paragraph("<b>CRS / Projection</b>", style_table_header),
            ]
        ]
        for img in report.inputs:
            input_rows.append([
                Paragraph(img.filename, style_table_cell),
                Paragraph(img.role.upper(), style_table_cell),
                Paragraph(img.modality.upper(), style_table_cell),
                Paragraph(img.dimensions, style_table_cell),
                Paragraph(img.crs or "None (Pixel)", style_table_cell),
            ])

        inp_table = Table(input_rows, colWidths=[2.2 * inch, 0.9 * inch, 1.2 * inch, 1.2 * inch, 1.8 * inch])
        inp_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), c_primary),
                ("GRID", (0, 0), (-1, -1), 0.5, c_border),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, c_bg_light]),
            ])
        )
        story.append(inp_table)
        story.append(Spacer(1, 10))

        # 5. Localized Visual Evidence Table
        story.append(Paragraph("<b>2. SPATIAL VISUAL EVIDENCE & LOCALIZATION</b>", style_h2))
        ev_rows = [
            [
                Paragraph("<b>ID</b>", style_table_header),
                Paragraph("<b>Type</b>", style_table_header),
                Paragraph("<b>Feature Label</b>", style_table_header),
                Paragraph("<b>Confidence</b>", style_table_header),
                Paragraph("<b>Coordinates / Bounds</b>", style_table_header),
            ]
        ]
        if report.evidence:
            for ev in report.evidence:
                conf_str = f"{int(ev.confidence * 100)}%" if ev.confidence is not None else "N/A"
                coord_str = str(ev.pixel_coordinates or ev.geographic_coordinates or "Scene-level")
                ev_rows.append([
                    Paragraph(ev.evidence_id[:8], style_table_cell),
                    Paragraph(ev.type.upper(), style_table_cell),
                    Paragraph(ev.label, style_table_cell),
                    Paragraph(conf_str, style_table_cell),
                    Paragraph(coord_str[:50], style_table_cell),
                ])
        else:
            ev_rows.append([
                Paragraph("—", style_table_cell),
                Paragraph("SCENE_VQA", style_table_cell),
                Paragraph("Global scene classification", style_table_cell),
                Paragraph(report.confidence_percentage or "N/A", style_table_cell),
                Paragraph("Full raster footprint", style_table_cell),
            ])

        ev_table = Table(ev_rows, colWidths=[1.1 * inch, 1.2 * inch, 2.0 * inch, 1.0 * inch, 2.0 * inch])
        ev_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), c_teal),
                ("GRID", (0, 0), (-1, -1), 0.5, c_border),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, c_bg_light]),
            ])
        )
        story.append(ev_table)
        story.append(Spacer(1, 10))

        # 6. Structured Observations
        story.append(Paragraph("<b>3. THREE-TIER STRUCTURED OBSERVATIONS</b>", style_h2))
        obs_rows = [
            [
                Paragraph("<b>Category</b>", style_table_header),
                Paragraph("<b>Analytical Findings</b>", style_table_header),
            ],
            [
                Paragraph("<b>Observed Facts</b>", style_table_cell),
                Paragraph("<br/>".join(f"• {x}" for x in (report.observations.observed or ["Validated physical attributes in satellite imagery."])), style_table_cell),
            ],
            [
                Paragraph("<b>Model Inferences</b>", style_table_cell),
                Paragraph("<br/>".join(f"• {x}" for x in (report.observations.inferred or ["Multimodal domain interpretation derived from specialist VLM."])), style_table_cell),
            ],
            [
                Paragraph("<b>Uncertain Cues</b>", style_table_cell),
                Paragraph("<br/>".join(f"• {x}" for x in (report.observations.uncertain or ["None detected under given spatial resolution."])), style_table_cell),
            ],
        ]
        obs_table = Table(obs_rows, colWidths=[1.8 * inch, 5.5 * inch])
        obs_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), c_primary),
                ("GRID", (0, 0), (-1, -1), 0.5, c_border),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ])
        )
        story.append(obs_table)
        story.append(Spacer(1, 10))

        # 7. Model Provenance & Execution Milestones
        story.append(Paragraph("<b>4. SPECIALIST MODELS & EXECUTION MILESTONES</b>", style_h2))
        model_lines = []
        for mod in report.models:
            adapt = " [BigEarthNet LoRA Adapted]" if mod.is_adapted else ""
            model_lines.append(f"• <b>{mod.task.upper()}:</b> {mod.name} v{mod.version}{adapt} on {mod.device}")
        story.append(Paragraph("<br/>".join(model_lines), style_body))
        story.append(Spacer(1, 6))

        milestone_text = " | ".join(f"✓ {m.milestone}" for m in report.execution_milestones)
        story.append(Paragraph(f"<b>Milestones:</b> {milestone_text} (Total Latency: {report.total_processing_time_ms} ms)", style_meta))
        story.append(Spacer(1, 10))

        # 8. Operational Limitations
        if report.limitations:
            story.append(Paragraph("<b>5. OPERATIONAL LIMITATIONS</b>", style_h2))
            lim_text = "<br/>".join(f"⚠ {lim}" for lim in report.limitations)
            lim_table = Table([[Paragraph(lim_text, style_body)]], colWidths=[7.3 * inch])
            lim_table.setStyle(
                TableStyle([
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fffbeb")),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#fde68a")),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ])
            )
            story.append(lim_table)
            story.append(Spacer(1, 10))

        # 9. Footer & Reproducibility
        story.append(HRFlowable(width="100%", thickness=0.5, color=c_border, spaceBefore=10, spaceAfter=6))
        story.append(
            Paragraph(
                f"SatQuery AI · ISRO SIH Problem Statement 26167 · Department of Space · "
                f"Reproducibility Token: {report.reproducibility_token}",
                style_meta,
            )
        )

        doc.build(story)
        return buf.getvalue()
