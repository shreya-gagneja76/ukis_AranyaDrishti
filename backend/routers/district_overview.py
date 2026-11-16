
from fastapi import APIRouter, HTTPException

from backend.services.district_overview import DistrictOverviewService


router = APIRouter(
    prefix="/district-overview",
    tags=["District Overview"]
)

service = DistrictOverviewService()


@router.get("/{district_lgd}")
def get_district_overview(district_lgd: str):
    """Return combined environmental and land-cover data."""

    result = service.get_by_lgd(district_lgd)

    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"No overview data found for district LGD code: {district_lgd}"
        )

    return result
