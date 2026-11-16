
import geopandas as gpd

# Path to the district boundary shapefile
district_path = (
    "data/raw/boundaries/"
    "File_872943_497c8eefc83a4c9fa496a5a0e42ca652/"
    "05/UTTARAKHAND_DISTRICT_BDY.shp"
)

# Read the shapefile
districts = gpd.read_file(district_path)

# Basic inspection
print("Number of districts:", len(districts))

print("\nCRS:")
print(districts.crs)

print("\nColumn names:")
print(districts.columns.tolist())

print("\nFirst five records:")
print(districts.head())

print("\nGeometry types:")
print(districts.geom_type.value_counts())

print("\nInvalid geometries:", (~districts.geometry.is_valid).sum())
print("Missing geometries:", districts.geometry.isna().sum())

print("\nDistrict names:")
print(districts["DISTRICT"].to_list())

print("\nDistrict codes:")
print(districts["DIST_LGD"].to_list())

print("\nUnique district count:")
print(districts["DISTRICT"].nunique())

# Inspect district headquarters layer
hq_path = (
    "data/raw/boundaries/"
    "File_872943_497c8eefc83a4c9fa496a5a0e42ca652/"
    "05/UTTARAKHAND_DISTRICT_HQ.shp"
)

hq = gpd.read_file(hq_path)

print("\nDistrict HQ layer:")
print("Number of records:", len(hq))

print("\nColumn names:")
print(hq.columns.tolist())

print("\nFirst five records:")
print(hq.head())

print("\nAll HQ records:")
print(hq.to_string())

# Verify district HQ points against district boundaries

print("\nCRS match:", districts.crs == hq.crs)

# Transform HQ points only if their CRS differs
if hq.crs != districts.crs:
    hq = hq.to_crs(districts.crs)

# Match each HQ point with the district polygon containing it
matched = gpd.sjoin(
    hq,
    districts[["DISTRICT", "DIST_LGD", "geometry"]],
    how="left",
    predicate="within"
)

print("\nHQ-to-boundary verification:")
print(
    matched[
        ["DISTRICT_left", "DISTRICT_right", "DIST_LGD"]
    ].to_string(index=False)
)

print("\nTotal HQ points:", len(hq))
print("Successfully matched:", matched["DIST_LGD"].notna().sum())
print("Unmatched:", matched["DIST_LGD"].isna().sum())

print("\nDistrict code validation:")

print("Total boundary codes:", len(districts["DIST_LGD"]))
print("Unique boundary codes:", districts["DIST_LGD"].nunique())

print("\nHQ district names:")
print(sorted(hq["DISTRICT"].unique()))

print("\nHQ district count:", hq["DISTRICT"].nunique())