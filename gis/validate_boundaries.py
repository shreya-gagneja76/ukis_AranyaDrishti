
from pathlib import Path
import geopandas as gpd

BASE_DIR = Path(__file__).resolve().parent.parent

OUTPUT_PATH = (
    BASE_DIR / "data/processed/uttarakhand_districts.gpkg"
)

# Reopen the saved GeoPackage
districts = gpd.read_file(
    OUTPUT_PATH,
    layer="districts"
)

# Validate the saved dataset
print("Number of districts:", len(districts))
print("Unique district codes:", districts["DIST_LGD"].nunique())
print("Missing district names:", districts["DISTRICT_NAME"].isna().sum())
print("Invalid geometries:", (~districts.geometry.is_valid).sum())
print("Missing geometries:", districts.geometry.isna().sum())
print("CRS:", districts.crs)

# Assertions
assert len(districts) == 13
assert districts["DIST_LGD"].nunique() == 13
assert districts["DISTRICT_NAME"].notna().all()
assert districts.geometry.is_valid.all()
assert districts.geometry.notna().all()

print("\nSaved GeoPackage validation passed!")
