
from pathlib import Path
import geopandas as gpd
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent

GPKG_PATH = ROOT / "data" / "processed" / "uttarakhand_districts.gpkg"

CSV_PATH = (
    ROOT / "data" / "processed" / "forest_cover"
    / "esa_worldcover_2021_v200"
    / "district_tree_cover_2021_v2.csv"
)

OUTPUT_PATH = (
    ROOT / "data" / "processed" / "forest_cover"
    / "esa_worldcover_2021_v200"
    / "uttarakhand_district_forest_cover_2021.gpkg"
)

print("Reading district boundaries...")
districts = gpd.read_file(GPKG_PATH, layer="districts")

print("Reading forest-cover statistics...")
stats = pd.read_csv(CSV_PATH, dtype={"DIST_LGD": str})

districts["DIST_LGD"] = (
    districts["DIST_LGD"].astype(str).str.zfill(3)
)

print("Joining district attributes...")
merged = districts.merge(
    stats,
    on="DIST_LGD",
    how="left",
    validate="one_to_one"
)

if len(merged) != 13:
    raise ValueError("Expected exactly 13 districts.")

if merged["Tree_Cover_Percent"].isna().any():
    raise ValueError("Some districts have missing tree-cover data.")

if merged.geometry.isna().any() or (~merged.geometry.is_valid).any():
    raise ValueError("Invalid or missing district geometry.")

OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

if OUTPUT_PATH.exists():
    raise FileExistsError(
        f"Output already exists. Inspect it before overwriting: {OUTPUT_PATH}"
    )

print("Saving new GeoPackage...")
merged.to_file(
    OUTPUT_PATH,
    layer="district_forest_cover",
    driver="GPKG"
)

print("\nDATASET CREATED SUCCESSFULLY")
print("Output:", OUTPUT_PATH)
print("Districts:", len(merged))
print("Fields:", list(merged.columns))
print("CRS:", merged.crs)
print("Size (KB):", round(OUTPUT_PATH.stat().st_size / 1024, 2))
