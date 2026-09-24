"""
API Endpoints for SatQuery Report Engine & Analysis Packages (Part 50).
"""

import uuid
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.reports.generator import ReportGenerator

router = APIRouter()


@router.get("/{analysis_id}", status_code=status.HTTP_200_OK)
async def get_report_metadata(
    analysis_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve normalized report structure and summary for a completed analysis.
    """
    try:
        report = await ReportGenerator.build_report(analysis_id, db)
        return report.model_dump()
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate report metadata: {str(e)}"
        )


@router.get("/{analysis_id}/json", status_code=status.HTTP_200_OK)
async def get_json_report(
    analysis_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Download machine-readable JSON analysis report.
    """
    try:
        data = await ReportGenerator.get_json_report(analysis_id, db)
        return data
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export JSON report: {str(e)}"
        )


@router.get("/{analysis_id}/html")
async def get_html_report(
    analysis_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    View or download self-contained, publication-grade interactive HTML report.
    """
    try:
        html_content = await ReportGenerator.get_html_report(analysis_id, db)
        return Response(
            content=html_content,
            media_type="text/html; charset=utf-8",
            headers={
                "Content-Disposition": f"inline; filename=satquery_report_{str(analysis_id)[:8]}.html"
            }
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate HTML report: {str(e)}"
        )


@router.get("/{analysis_id}/pdf")
async def get_pdf_report(
    analysis_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Download publication-grade, formal multi-page PDF document compiled via ReportLab.
    """
    try:
        pdf_bytes = await ReportGenerator.get_pdf_report(analysis_id, db)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"inline; filename=satquery_report_{str(analysis_id)[:8]}.pdf"
            }
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate PDF report: {str(e)}"
        )


@router.get("/{analysis_id}/package")
async def download_analysis_package(
    analysis_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Download complete analysis package (.zip) containing analysis.json,
    report.html, report.pdf, trace.json, metadata.json, and visual evidence.
    """
    try:
        pkg_bytes = await ReportGenerator.get_analysis_package(analysis_id, db)
        return Response(
            content=pkg_bytes,
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename=satquery_package_{str(analysis_id)[:8]}.zip"
            }
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compile analysis package: {str(e)}"
        )
