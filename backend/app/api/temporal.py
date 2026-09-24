"""
API Endpoints for SatQuery Bi-Temporal Change Intelligence.
Provides pair registration, spatial/temporal validation, co-registration,
change detection inference, and change region exploration.
"""

import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.temporal.schemas import (
    BiTemporalPairCreate,
    BiTemporalPairResponse,
    ChangeAnalysisRequest,
    ChangeAnalysisResponse,
    PairValidationResult,
)
from app.temporal.service import get_temporal_service

router = APIRouter()


@router.post("/pairs", response_model=BiTemporalPairResponse, status_code=status.HTTP_201_CREATED)
async def create_temporal_pair(
    request: BiTemporalPairCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Register and validate a bi-temporal satellite image pair (T1 and T2).
    Verifies temporal ordering (T1 < T2) and calculates spatial overlap.
    """
    svc = get_temporal_service()
    return await svc.create_pair(request=request, db=db)


@router.get("/pairs", response_model=List[BiTemporalPairResponse])
async def list_temporal_pairs(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """
    List registered bi-temporal image pairs with validation status and overlap metrics.
    """
    svc = get_temporal_service()
    return await svc.list_pairs(limit=limit, offset=offset, db=db)


@router.get("/pairs/{pair_id}", response_model=BiTemporalPairResponse)
async def get_temporal_pair(
    pair_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve metadata, spatial overlap, and alignment status for a specific bi-temporal pair.
    """
    svc = get_temporal_service()
    pair = await svc.get_pair(pair_id=pair_id, db=db)
    if not pair:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bi-temporal pair '{pair_id}' not found."
        )
    return pair


@router.post("/pairs/{pair_id}/validate", response_model=PairValidationResult)
async def validate_temporal_pair(
    pair_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Re-evaluate spatial compatibility and acquisition timestamp ordering for a pair.
    """
    svc = get_temporal_service()
    pair = await svc.get_pair(pair_id=pair_id, db=db)
    if not pair:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bi-temporal pair '{pair_id}' not found."
        )
    return pair.validation


@router.post("/analyze", response_model=ChangeAnalysisResponse, status_code=status.HTTP_200_OK)
async def analyze_temporal_change(
    request: ChangeAnalysisRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Directly execute bi-temporal change intelligence on a registered pair.
    Performs non-destructive alignment, Siamese feature difference inference,
    change map thresholding, region extraction, and grounded narrative synthesis.
    """
    svc = get_temporal_service()
    return await svc.execute_change_analysis(
        pair_id=request.pair_id,
        query=request.query or "What changed between these two dates?",
        threshold=request.threshold,
        min_region_size=request.min_region_size,
        db=db
    )
