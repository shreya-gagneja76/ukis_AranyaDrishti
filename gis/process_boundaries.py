
from pathlib import Path
import geopandas as gpd

# Project paths
BASE_DIR = Path(__file__).resolve().parent.parent

BOUNDARY_PATH = (
    BASE_DIR
    / "data/raw/boundaries/"
    / "File_872943_497c8eefc83a4c9fa496a5a0e42ca652/"
    / "05/UTTARAKHAND_DISTRICT_BDY.shp"
)

HQ_PATH = (
    BASE_DIR
    / "data/raw/boundaries/"
    / "File_872943_497c8eefc83a4c9fa496a5a0e42ca652/"
    / "05/UTTARAKHAND_DISTRICT_HQ.shp"
)

OUTPUT_DIR = BASE_DIR / "data/processed"
OUTPUT_PATH = OUTPUT_DIR / "uttarakhand_districts.gpkg"

# 1. Read original datasets
districts = gpd.read_file(BOUNDARY_PATH)
hq = gpd.read_file(HQ_PATH)

# 2. Check required fields
assert "DIST_LGD" in districts.columns
assert "DISTRICT" in hq.columns

# 3. Match CRS
if hq.crs != districts.crs:
    hq = hq.to_crs(districts.crs)

# 4. Match headquarters to district polygons
matched = gpd.sjoin(
    hq[["DISTRICT", "geometry"]],
    districts[["DIST_LGD", "geometry"]],
    how="left",
    predicate="within"
)

# 5. Validate the mapping
assert len(matched) == 13
assert matched["DIST_LGD"].notna().all()
assert matched["DIST_LGD"].is_unique
assert districts["DIST_LGD"].is_unique

name_map = matched.set_index("DIST_LGD")["DISTRICT"]

assert set(name_map.index) == set(districts["DIST_LGD"])

# 6. Create clean district layer
districts_clean = districts[["DIST_LGD", "geometry"]].copy()

districts_clean["DISTRICT_NAME"] = (
    districts_clean["DIST_LGD"].map(name_map)
)

districts_clean = districts_clean[
    ["DIST_LGD", "DISTRICT_NAME", "geometry"]
]

# 7. Save processed output
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

districts_clean.to_file(
    OUTPUT_PATH,
    driver="GPKG",
    layer="districts"
)

print("Clean district layer created successfully.")
print("Output:", OUTPUT_PATH)
print("\nDistrict records:")
print(
    districts_clean[["DIST_LGD", "DISTRICT_NAME"]]
    .sort_values("DISTRICT_NAME")
    .to_string(index=False)
)
