
from fastapi import APIRouter, HTTPException, Query

from backend.services.environmental_context import (
    EnvironmentalContextService
)

router = APIRouter(
    prefix="/environmental-context",
    tags=["Environmental Context"]
)

# Initialize the service once when the router is loaded.
service = EnvironmentalContextService()


@router.get("/")
def get_all_districts():
    """Return environmental context for all districts."""
    return service.get_all_districts()


@router.get("/rank")
def rank_districts(
    metric: str = Query(..., description="Environmental metric to rank"),
    order: str = Query("desc", pattern="^(asc|desc)$"),
    limit: int = Query(5, ge=1, le=13)
):
    """Rank districts by a selected environmental metric."""

    try:
        return service.rank_districts(
            metric=metric,
            order=order,
            limit=limit
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )


@router.get("/{district_lgd}")
def get_district_context(district_lgd: str):
    """Return environmental context for a specific district."""

    result = service.get_by_lgd(district_lgd)

    if result is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"No environmental context found "
                f"for district LGD code: {district_lgd}"
            )
        )

    return result
