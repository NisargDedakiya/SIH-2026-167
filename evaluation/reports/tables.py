"""
Report table formatting utilities for SatQuery AI.
"""

from typing import Any, Dict, List


def format_markdown_table(headers: List[str], rows: List[List[Any]]) -> str:
    """Formats standard Markdown table."""
    col_widths = [len(h) for h in headers]
    for row in rows:
        for idx, val in enumerate(row):
            col_widths[idx] = max(col_widths[idx], len(str(val)))

    header_line = "| " + " | ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers)) + " |"
    sep_line = "| " + " | ".join("-" * col_widths[i] for i in range(len(headers))) + " |"

    row_lines = []
    for row in rows:
        row_str = "| " + " | ".join(str(val).ljust(col_widths[i]) for i, val in enumerate(row)) + " |"
        row_lines.append(row_str)

    return "\n".join([header_line, sep_line] + row_lines)


def format_html_table(headers: List[str], rows: List[List[Any]]) -> str:
    """Formats modern Tailwind-compatible HTML table."""
    thead = "".join(f"<th class='px-4 py-2 text-left text-xs font-semibold text-slate-300'>{h}</th>" for h in headers)
    tbody_rows = []
    for r in rows:
        tds = "".join(f"<td class='px-4 py-2.5 text-xs text-slate-200 border-t border-slate-800/80'>{v}</td>" for v in r)
        tbody_rows.append(f"<tr class='hover:bg-slate-800/40 transition'>{tds}</tr>")
    tbody = "".join(tbody_rows)

    return f"""
    <div class="overflow-x-auto rounded-lg border border-slate-800 bg-slate-950/60 shadow">
      <table class="min-w-full divide-y divide-slate-800 text-xs">
        <thead class="bg-slate-900/80">{thead}</thead>
        <tbody class="divide-y divide-slate-800/60">{tbody}</tbody>
      </table>
    </div>
    """
