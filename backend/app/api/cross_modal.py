"""
API Router for Optical-SAR Cross-Modal Intelligence.
Provides endpoints for pair registration, validation, retrieval, and direct analysis.
"""

import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.cross_modal.schemas import (
    CrossModalAnalysisRequest,
    CrossModalAnalysisResponse,
    CrossModalValidationResult,
    OpticalSARPairCreate,
    OpticalSARPairResponse,
)
from app.cross_modal.service import get_cross_modal_service
from app.database.session import get_db

router = APIRouter()


@router.post("/pairs", response_model=OpticalSARPairResponse, status_code=status.HTTP_201_CREATED)
async def create_optical_sar_pair(
    request: OpticalSARPairCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Register and validate a new Optical-SAR image pair.
    Strictly verifies that one image is Optical/Multispectral and one is SAR,
    and computes spatial overlap and co-registration compatibility.
    """
    svc = get_cross_modal_service()
    try:
        return await svc.create_pair(create_req=request, db=db)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/pairs", response_model=List[OpticalSARPairResponse])
async def list_optical_sar_pairs(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """List registered Optical-SAR pairs with validation status and overlap metrics."""
    svc = get_cross_modal_service()
    return await svc.list_pairs(limit=limit, offset=offset, db=db)


@router.get("/pairs/{pair_id}", response_model=OpticalSARPairResponse)
async def get_optical_sar_pair(
    pair_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Retrieve metadata, spatial overlap, and alignment status for a specific Optical-SAR pair."""
    svc = get_cross_modal_service()
    pair = await svc.get_pair(pair_id=pair_id, db=db)
    if not pair:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Optical-SAR pair '{pair_id}' not found."
        )
    return pair


@router.post("/pairs/{pair_id}/validate", response_model=CrossModalValidationResult)
async def validate_optical_sar_pair(
    pair_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Re-evaluate spatial overlap and modality compatibility for a registered pair."""
    svc = get_cross_modal_service()
    pair = await svc.get_pair(pair_id=pair_id, db=db)
    if not pair:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Optical-SAR pair '{pair_id}' not found."
        )
    return pair.validation


@router.post("/analyze", response_model=CrossModalAnalysisResponse, status_code=status.HTTP_200_OK)
async def analyze_optical_sar_cross_modal(
    request: CrossModalAnalysisRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Executes cross-modal joint reasoning directly on a registered Optical-SAR pair.
    Performs non-destructive co-registration, feature fusion, modality contribution analysis,
    and returns grounded observations and visual evidence.
    """
    svc = get_cross_modal_service()
    try:
        return await svc.execute_cross_modal_analysis(
            pair_id=request.pair_id,
            query=request.query or "Analyze these optical and SAR images together.",
            task=request.task or "cross_modal_analysis",
            db=db
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Cross-modal analysis failed: {str(e)}")
