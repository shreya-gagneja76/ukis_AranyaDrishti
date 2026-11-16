
from pathlib import Path

import pandas as pd


# Project root: D:\AranyaDrishti
PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATASET_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "forest_cover"
    / "esa_worldcover_2021_v200"
    / "district_land_cover_composition_2021.csv"
)


class LandCoverService:

    def __init__(self):
        if not DATASET_PATH.exists():
            raise FileNotFoundError(
                f"Land-cover dataset not found: {DATASET_PATH}"
            )

        self.data = pd.read_csv(
            DATASET_PATH,
            dtype={"DIST_LGD": str}
        )

        self.data["DIST_LGD"] = (
            self.data["DIST_LGD"].str.zfill(3)
        )

        # Check for duplicate district-category combinations.
        if self.data.duplicated(
            subset=["DIST_LGD", "Class_Code"]
        ).any():
            raise ValueError(
                "Duplicate district and land-cover category records found."
            )

        # Verify that every district's percentages total approximately 100%.
        percentage_totals = (
            self.data.groupby("DIST_LGD")["Percent_of_District"].sum()
        )

        if not percentage_totals.between(
            99.99, 100.01
        ).all():
            raise ValueError(
                "Land-cover percentages do not sum to approximately 100%."
            )

        self.data = self.data.sort_values(
            by=["DIST_LGD", "Class_Code"]
        )

    def _format_district(self, district_lgd: str):
        district_data = self.data[
            self.data["DIST_LGD"] == district_lgd
        ]

        if district_data.empty:
            return None

        first_row = district_data.iloc[0]

        categories = district_data[
            [
                "Class_Code",
                "Land_Cover",
                "Pixel_Count",
                "Area_km2",
                "Percent_of_District"
            ]
        ].to_dict(orient="records")

        return {
            "DIST_LGD": district_lgd,
            "District": first_row["District"],
            "land_cover": categories
        }

    def get_by_lgd(self, district_lgd: str):
        district_lgd = str(district_lgd).zfill(3)

        return self._format_district(district_lgd)

    def get_all_districts(self):
        district_codes = (
            self.data["DIST_LGD"].drop_duplicates().tolist()
        )

        return [
            self._format_district(code)
            for code in district_codes
        ]
