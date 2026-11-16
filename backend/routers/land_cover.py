
from fastapi import APIRouter, HTTPException

from backend.services.land_cover import LandCoverService


router = APIRouter(
    prefix="/land-cover",
    tags=["Land Cover"]
)

# Initialize the service once when the router is loaded.
service = LandCoverService()


@router.get("/")
def get_all_land_cover():
    """Return land-cover composition for all districts."""
    return service.get_all_districts()


@router.get("/{district_lgd}")
def get_district_land_cover(district_lgd: str):
    """Return land-cover composition for a specific district."""

    result = service.get_by_lgd(district_lgd)

    if result is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"No land-cover data found "
                f"for district LGD code: {district_lgd}"
            )
        )

    return result
