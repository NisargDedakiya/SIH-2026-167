"""
HTML Report Exporter for SatQuery Analysis Reports.
Renders self-contained, publication-grade interactive HTML documents.
"""

import html
from app.reports.schemas import AnalysisReport


class HtmlReportExporter:
    @classmethod
    def export(cls, report: AnalysisReport) -> str:
        """Renders an interactive, styled, self-contained HTML report."""
        conf_badge = ""
        if report.confidence_percentage:
            conf_badge = f'<span class="badge badge-conf">{html.escape(report.confidence_percentage)} Confidence ({html.escape(report.calibration_status)})</span>'

        # Inputs table rows
        inputs_html = ""
        for img in report.inputs:
            inputs_html += f"""
            <tr>
              <td><strong>{html.escape(img.filename)}</strong><br/><small class="text-muted">{html.escape(img.role.upper())}</small></td>
              <td>{html.escape(img.modality.upper())}</td>
              <td>{html.escape(img.sensor or 'Unknown')}</td>
              <td>{html.escape(img.dimensions)}</td>
              <td>{html.escape(img.crs or 'None (Pixel-only)')}</td>
              <td><span class="badge badge-success">✓ {html.escape(img.validation_status.upper())}</span></td>
            </tr>
            """

        # Evidence table rows
        evidence_html = ""
        if report.evidence:
            for ev in report.evidence:
                conf_str = f"{int(ev.confidence * 100)}%" if ev.confidence is not None else "N/A"
                geo_str = str(ev.geographic_coordinates) if ev.geographic_coordinates else "Pixel coords only"
                evidence_html += f"""
                <tr>
                  <td><code>{html.escape(ev.evidence_id[:8])}</code></td>
                  <td><span class="badge badge-teal">{html.escape(ev.type.upper())}</span></td>
                  <td><strong>{html.escape(ev.label)}</strong></td>
                  <td>{conf_str}</td>
                  <td><small>{html.escape(geo_str[:60])}</small></td>
                </tr>
                """
        else:
            evidence_html = '<tr><td colspan="5" class="text-muted text-center">No discrete localized regions detected. Global scene-level synthesis applied.</td></tr>'

        # Observations
        observed_items = "".join(f"<li>{html.escape(item)}</li>" for item in report.observations.observed) or "<li>Direct spatial attributes validated in satellite imagery.</li>"
        inferred_items = "".join(f"<li>{html.escape(item)}</li>" for item in report.observations.inferred) or "<li>Interpretation derived from remote-sensing vision-language reasoning.</li>"
        uncertain_items = "".join(f"<li>{html.escape(item)}</li>" for item in report.observations.uncertain) or "<li>None identified under current resolution.</li>"

        # Milestones
        milestones_html = ""
        for m in report.execution_milestones:
            dur = f"{m.duration_ms} ms" if m.duration_ms is not None else "✓"
            milestones_html += f"""
            <div class="milestone-item">
              <span class="milestone-icon">✓</span>
              <div class="milestone-text">
                <strong>{html.escape(m.milestone)}</strong>
                <span class="text-muted">({html.escape(m.status)})</span>
              </div>
              <span class="milestone-duration">{dur}</span>
            </div>
            """

        # Limitations
        limitations_html = "".join(f"<li>{html.escape(lim)}</li>" for lim in report.limitations)

        # Models
        models_html = ""
        for mod in report.models:
            adapted_str = " (BigEarthNet LoRA Adapted)" if mod.is_adapted else ""
            models_html += f"""
            <div class="model-badge">
              <strong>{html.escape(mod.task.upper())}:</strong> {html.escape(mod.name)} v{html.escape(mod.version)}{adapted_str}
              <span class="text-muted">[{html.escape(mod.device)}]</span>
            </div>
            """

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>SatQuery AI Analysis Report · {html.escape(report.analysis_id[:8])}</title>
  <style>
    :root {{
      --bg: #090d16;
      --surface: #101726;
      --surface-border: #1e293b;
      --text: #f1f5f9;
      --text-muted: #94a3b8;
      --cyan: #06b6d4;
      --teal: #14b8a6;
      --emerald: #10b981;
      --amber: #f59e0b;
      --font: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      --font-mono: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    }}
    body {{
      background-color: var(--bg);
      color: var(--text);
      font-family: var(--font);
      margin: 0;
      padding: 40px 20px;
      line-height: 1.6;
    }}
    .container {{
      max-width: 900px;
      margin: 0 auto;
      background: var(--surface);
      border: 1px solid var(--surface-border);
      border-radius: 16px;
      padding: 40px;
      box-shadow: 0 20px 40px rgba(0,0,0,0.5);
    }}
    .header {{
      border-b: 1px solid var(--surface-border);
      padding-bottom: 24px;
      margin-bottom: 32px;
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
    }}
    .header-title {{
      font-size: 24px;
      font-weight: 800;
      color: #fff;
      margin: 0 0 6px 0;
      letter-spacing: -0.02em;
    }}
    .header-sub {{
      font-size: 13px;
      color: var(--cyan);
      font-family: var(--font-mono);
      margin: 0;
    }}
    .meta-box {{
      text-align: right;
      font-family: var(--font-mono);
      font-size: 11px;
      color: var(--text-muted);
    }}
    h2 {{
      font-size: 16px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: var(--cyan);
      margin: 32px 0 16px 0;
      font-family: var(--font-mono);
      display: flex;
      align-items: center;
      gap: 8px;
    }}
    .card {{
      background: rgba(15, 23, 42, 0.6);
      border: 1px solid var(--surface-border);
      border-radius: 12px;
      padding: 20px;
      margin-bottom: 24px;
    }}
    .query-text {{
      font-size: 15px;
      font-style: italic;
      color: #cbd5e1;
      margin: 0;
    }}
    .answer-card {{
      background: linear-gradient(135deg, rgba(6, 182, 212, 0.1), rgba(16, 185, 129, 0.05));
      border: 1px solid rgba(6, 182, 212, 0.4);
      border-radius: 12px;
      padding: 24px;
      margin-bottom: 28px;
    }}
    .answer-title {{
      font-size: 12px;
      font-family: var(--font-mono);
      text-transform: uppercase;
      color: var(--cyan);
      margin-bottom: 8px;
      display: flex;
      justify-content: space-between;
    }}
    .answer-text {{
      font-size: 18px;
      font-weight: 600;
      color: #fff;
      line-height: 1.5;
      margin: 0;
    }}
    .badge {{
      display: inline-block;
      padding: 3px 8px;
      border-radius: 6px;
      font-size: 11px;
      font-weight: 600;
      font-family: var(--font-mono);
    }}
    .badge-conf {{
      background: rgba(6, 182, 212, 0.2);
      color: #38bdf8;
      border: 1px solid rgba(6, 182, 212, 0.5);
    }}
    .badge-success {{
      background: rgba(16, 185, 129, 0.2);
      color: #34d399;
      border: 1px solid rgba(16, 185, 129, 0.4);
    }}
    .badge-teal {{
      background: rgba(20, 184, 166, 0.2);
      color: #2dd4bf;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 12px;
      margin: 12px 0;
    }}
    th {{
      text-align: left;
      padding: 10px;
      background: rgba(15, 23, 42, 0.8);
      color: var(--text-muted);
      border-bottom: 1px solid var(--surface-border);
      font-family: var(--font-mono);
      font-size: 11px;
      text-transform: uppercase;
    }}
    td {{
      padding: 10px;
      border-bottom: 1px solid rgba(30, 41, 59, 0.6);
    }}
    .obs-grid {{
      display: grid;
      grid-template-columns: 1fr 1fr 1fr;
      gap: 16px;
    }}
    .obs-col {{
      background: rgba(15, 23, 42, 0.5);
      border: 1px solid var(--surface-border);
      border-radius: 8px;
      padding: 14px;
    }}
    .obs-col h4 {{
      margin: 0 0 10px 0;
      font-size: 12px;
      font-family: var(--font-mono);
      text-transform: uppercase;
    }}
    .obs-col ul {{
      margin: 0;
      padding-left: 18px;
      font-size: 12px;
      color: #cbd5e1;
    }}
    .obs-col li {{
      margin-bottom: 6px;
    }}
    .milestone-item {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 8px 12px;
      border-bottom: 1px solid rgba(30, 41, 59, 0.6);
      font-size: 12px;
      font-family: var(--font-mono);
    }}
    .milestone-icon {{
      color: var(--emerald);
      margin-right: 8px;
    }}
    .milestone-duration {{
      color: var(--text-muted);
    }}
    .limitations-box {{
      background: rgba(245, 158, 11, 0.08);
      border: 1px solid rgba(245, 158, 11, 0.3);
      border-radius: 8px;
      padding: 16px;
      font-size: 12px;
      color: #fde68a;
    }}
    .limitations-box ul {{
      margin: 0;
      padding-left: 20px;
    }}
    .footer {{
      margin-top: 40px;
      padding-top: 20px;
      border-top: 1px solid var(--surface-border);
      font-size: 11px;
      color: var(--text-muted);
      display: flex;
      justify-content: space-between;
      font-family: var(--font-mono);
    }}
    @media print {{
      body {{ background: #fff; color: #000; padding: 0; }}
      .container {{ border: none; box-shadow: none; max-width: 100%; }}
      .card, .answer-card, .obs-col {{ border: 1px solid #ccc; }}
      .answer-text {{ color: #000; }}
      .header-title {{ color: #000; }}
    }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <div>
        <h1 class="header-title">{html.escape(report.system_title)}</h1>
        <p class="header-sub">{html.escape(report.problem_statement)}</p>
      </div>
      <div class="meta-box">
        <div><strong>REPORT ID:</strong> {html.escape(report.report_id)}</div>
        <div><strong>ANALYSIS ID:</strong> {html.escape(report.analysis_id)}</div>
        <div><strong>DATE:</strong> {html.escape(report.generated_at)}</div>
      </div>
    </div>

    <!-- 1. Question & Calibrated Answer -->
    <div class="card">
      <div style="font-family: var(--font-mono); font-size: 11px; color: var(--text-muted); margin-bottom: 6px;">NATURAL LANGUAGE INSTRUCTION</div>
      <p class="query-text">"{html.escape(report.query)}"</p>
    </div>

    <div class="answer-card">
      <div class="answer-title">
        <span>Synthesized Analytical Answer</span>
        {conf_badge}
      </div>
      <p class="answer-text">{html.escape(report.answer)}</p>
    </div>

    <!-- 2. Input Imagery Metadata -->
    <h2>1. Input Earth Observation Rasters</h2>
    <table>
      <thead>
        <tr>
          <th>Filename / Role</th>
          <th>Modality</th>
          <th>Sensor</th>
          <th>Dimensions</th>
          <th>CRS / Projection</th>
          <th>Validation</th>
        </tr>
      </thead>
      <tbody>
        {inputs_html}
      </tbody>
    </table>

    <!-- 3. Localized Visual Evidence -->
    <h2>2. Spatial Visual Evidence</h2>
    <table>
      <thead>
        <tr>
          <th>ID</th>
          <th>Type</th>
          <th>Feature Label</th>
          <th>Confidence</th>
          <th>Coordinates / Geo Reference</th>
        </tr>
      </thead>
      <tbody>
        {evidence_html}
      </tbody>
    </table>

    <!-- 4. Three-Tier Structured Observations -->
    <h2>3. Analytical Observations</h2>
    <div class="obs-grid">
      <div class="obs-col">
        <h4 style="color: var(--emerald);">✓ Observed Facts</h4>
        <ul>{observed_items}</ul>
      </div>
      <div class="obs-col">
        <h4 style="color: var(--cyan);">◆ Model Inferences</h4>
        <ul>{inferred_items}</ul>
      </div>
      <div class="obs-col">
        <h4 style="color: var(--amber);">⚠ Uncertain Cues</h4>
        <ul>{uncertain_items}</ul>
      </div>
    </div>

    <!-- 5. Observable Execution Milestones -->
    <h2>4. Execution Trace & Timing</h2>
    <div class="card" style="padding: 10px;">
      {milestones_html}
      <div style="text-align: right; padding: 10px; font-family: var(--font-mono); font-size: 11px; color: var(--cyan);">
        Total Processing Time: {report.total_processing_time_ms} ms
      </div>
    </div>

    <!-- 6. Specialist Models Provenance -->
    <h2>5. Model Provenance & Hardware</h2>
    <div class="card">
      {models_html}
    </div>

    <!-- 7. Operational Limitations -->
    <h2>6. Operational Limitations</h2>
    <div class="limitations-box">
      <ul>
        {limitations_html}
      </ul>
    </div>

    <div class="footer">
      <div>ISRO SIH Problem Statement 26167 · Department of Space</div>
      <div>Reproducibility Token: {html.escape(report.reproducibility_token)}</div>
    </div>
  </div>
</body>
</html>
"""
