
from backend.services.environmental_context import (
    EnvironmentalContextService
)
from backend.services.land_cover import LandCoverService


class DistrictOverviewService:

    def __init__(self):
        self.environmental_service = EnvironmentalContextService()
        self.land_cover_service = LandCoverService()

    def get_by_lgd(self, district_lgd: str):
        district_lgd = str(district_lgd).zfill(3)

        environmental_data = (
            self.environmental_service.get_by_lgd(district_lgd)
        )

        land_cover_data = (
            self.land_cover_service.get_by_lgd(district_lgd)
        )

        if environmental_data is None or land_cover_data is None:
            return None

        return {
            "DIST_LGD": district_lgd,
            "DISTRICT_NAME": environmental_data.get("DISTRICT_NAME"),
            "environmental_context": environmental_data,
            "land_cover": land_cover_data["land_cover"]
        }
