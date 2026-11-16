
from pathlib import Path

import pandas as pd


# Project root: D:\AranyaDrishti
PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATASET_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "district_environmental_context_2021.csv"
)


class EnvironmentalContextService:

    ALLOWED_METRICS = [
        "Tree_Cover_Percent",
        "Elevation_Mean_m",
        "Slope_Mean_deg",
        "Steep_Terrain_Above_30deg_pct",
        "LC_Percent_of_District_Tree_cover",
        "LC_Percent_of_District_Cropland",
        "LC_Percent_of_District_Shrubland",
        "LC_Percent_of_District_Grassland",
        "LC_Percent_of_District_Built-up",
    ]

    def __init__(self):
        if not DATASET_PATH.exists():
            raise FileNotFoundError(
                f"Environmental dataset not found: {DATASET_PATH}"
            )

        self.data = pd.read_csv(
            DATASET_PATH,
            dtype={"DIST_LGD": str}
        )

        self.data["DIST_LGD"] = (
            self.data["DIST_LGD"].str.zfill(3)
        )

        if self.data["DIST_LGD"].duplicated().any():
            raise ValueError(
                "Duplicate district LGD codes found."
            )

        self.data = self.data.set_index("DIST_LGD")

    def get_by_lgd(self, district_lgd: str):
        district_lgd = str(district_lgd).zfill(3)

        if district_lgd not in self.data.index:
            return None

        record = self.data.loc[district_lgd]

        return record.to_dict()

    def get_all_districts(self):
        return self.data.reset_index().to_dict(
            orient="records"
        )

    def rank_districts(
        self,
        metric: str,
        order: str = "desc",
        limit: int = 5
    ):
        if metric not in self.ALLOWED_METRICS:
            raise ValueError(
                f"Unsupported ranking metric: {metric}"
            )

        if order not in ("asc", "desc"):
            raise ValueError(
                "Order must be 'asc' or 'desc'."
            )

        if not 1 <= limit <= 13:
            raise ValueError(
                "Limit must be between 1 and 13."
            )

        result = (
            self.data[["DISTRICT_NAME", metric]]
            .sort_values(
                by=metric,
                ascending=(order == "asc")
            )
            .head(limit)
            .reset_index()
        )

        return result.to_dict(orient="records")
