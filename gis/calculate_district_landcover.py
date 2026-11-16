
from pathlib import Path
from collections import defaultdict

import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
from rasterio.features import rasterize
from pyproj import Geod

BASE = Path(__file__).resolve().parent.parent

INPUT_DIR = (
    BASE / "data" / "processed" / "forest_cover"
    / "esa_worldcover_2021_v200"
)

GPKG_PATH = BASE / "data" / "processed" / "uttarakhand_districts.gpkg"

OUTPUT_FILE = INPUT_DIR / "district_land_cover_composition_2021.csv"

CLASS_NAMES = {
    10: "Tree cover",
    20: "Shrubland",
    30: "Grassland",
    40: "Cropland",
    50: "Built-up",
    60: "Bare / sparse vegetation",
    70: "Snow and ice",
    80: "Permanent water bodies",
    90: "Herbaceous wetland",
    95: "Mangroves",
    100: "Moss and lichen",
}

BLOCK_SIZE = 512
EXPECTED_TREE_PIXELS = 385_494_041
EXPECTED_VALID_PIXELS = 720_207_290

geod = Geod(ellps="WGS84")

print("READING DISTRICT BOUNDARIES")
districts = gpd.read_file(GPKG_PATH, layer="districts")
districts["DIST_LGD"] = (
    districts["DIST_LGD"].astype(str).str.zfill(3)
)
districts = districts.sort_values("DIST_LGD").reset_index(drop=True)

districts = districts.to_crs("EPSG:4326")

district_shapes = [
    (geom, idx + 1)
    for idx, geom in enumerate(districts.geometry)
]

district_names = {
    idx + 1: row["DISTRICT_NAME"]
    for idx, row in districts.iterrows()
}

district_codes = {
    idx + 1: row["DIST_LGD"]
    for idx, row in districts.iterrows()
}

# Key: (district_id, class_code)
pixel_counts = defaultdict(int)
area_m2 = defaultdict(float)

district_valid_pixels = defaultdict(int)
district_tree_pixels = defaultdict(int)

files = sorted(INPUT_DIR.glob("*_Map_uttarakhand.tif"))

if len(files) != 5:
    raise RuntimeError(
        f"Expected 5 clipped rasters, found {len(files)}"
    )

print("\nDISTRICT-WISE LAND-COVER PROCESSING")
print("=" * 60)

for path in files:

    print(f"\nProcessing: {path.name}")

    with rasterio.open(path) as src:

        if src.crs.to_epsg() != 4326:
            raise ValueError(f"Unexpected CRS: {src.crs}")

        transform = src.transform

        for row_start in range(0, src.height, BLOCK_SIZE):

            for col_start in range(0, src.width, BLOCK_SIZE):

                height = min(
                    BLOCK_SIZE, src.height - row_start
                )

                width = min(
                    BLOCK_SIZE, src.width - col_start
                )

                window = rasterio.windows.Window(
                    col_start, row_start, width, height
                )

                data = src.read(1, window=window)

                # Assign every pixel to one district.
                district_ids = rasterize(
                    district_shapes,
                    out_shape=(height, width),
                    transform=src.window_transform(window),
                    fill=0,
                    dtype="uint8",
                    all_touched=False
                )

                # Encode district ID and land-cover class.
                encoded = (
                    district_ids.astype("uint16") * 256
                    + data.astype("uint16")
                )

                encoded[
                    (district_ids == 0) | (data == 0)
                ] = 0

                # Calculate area separately for each raster row.
                for local_row in range(height):

                    values = encoded[local_row]
                    values = values[values > 0]

                    if values.size == 0:
                        continue

                    unique_values, counts = np.unique(
                        values, return_counts=True
                    )

                    global_row = row_start + local_row

                    x0, y0 = transform * (0, global_row)
                    x1, y1 = transform * (1, global_row + 1)
                    x2, y2 = transform * (1, global_row)
                    x3, y3 = transform * (0, global_row + 1)

                    pixel_area, _ = geod.polygon_area_perimeter(
                        [x0, x2, x1, x3],
                        [y0, y2, y1, y3]
                    )

                    pixel_area = abs(pixel_area)

                    for value, count in zip(unique_values, counts):

                        value = int(value)
                        count = int(count)

                        district_id = value // 256
                        class_code = value % 256

                        key = (district_id, class_code)

                        pixel_counts[key] += count
                        area_m2[key] += count * pixel_area

                        district_valid_pixels[district_id] += count

                        if class_code == 10:
                            district_tree_pixels[district_id] += count

    print("Completed.")

# Validate total counts before saving.
total_valid = sum(pixel_counts.values())
total_tree = sum(district_tree_pixels.values())

print("\nCOUNT VALIDATION")
print("=" * 45)
print("Valid pixels:", f"{total_valid:,}")
print("Tree pixels:", f"{total_tree:,}")

if total_valid != EXPECTED_VALID_PIXELS:
    raise RuntimeError("Valid pixel count does not match expected total.")

if total_tree != EXPECTED_TREE_PIXELS:
    raise RuntimeError("Tree pixel count does not match expected total.")

# Build complete district x class table.
rows = []

for district_id in range(1, len(districts) + 1):

    total_district_area = sum(
        area_m2.get((district_id, class_code), 0.0)
        for class_code in CLASS_NAMES
    )

    for class_code, class_name in CLASS_NAMES.items():

        count = pixel_counts.get(
            (district_id, class_code), 0
        )

        area_km2 = (
            area_m2.get((district_id, class_code), 0.0)
            / 1_000_000
        )

        percentage = (
            area_m2.get((district_id, class_code), 0.0)
            / total_district_area * 100
            if total_district_area > 0 else 0
        )

        rows.append({
            "DIST_LGD": district_codes[district_id],
            "District": district_names[district_id],
            "Class_Code": class_code,
            "Land_Cover": class_name,
            "Pixel_Count": count,
            "Area_km2": area_km2,
            "Percent_of_District": percentage,
        })

results = pd.DataFrame(rows)

if OUTPUT_FILE.exists():
    raise FileExistsError(
        f"Output already exists; inspect it before replacing: {OUTPUT_FILE}"
    )

results.to_csv(OUTPUT_FILE, index=False)

print("\nDISTRICT LAND-COVER SUMMARY")
print("=" * 65)

summary = (
    results.groupby("Land_Cover")["Area_km2"]
    .sum()
    .sort_values(ascending=False)
)

print(summary.to_string(
    formatters={"Area_km2": "{:,.3f}".format}
))

print("\nRows generated:", len(results))
print("Output:", OUTPUT_FILE)
print("Size (KB):", round(OUTPUT_FILE.stat().st_size / 1024, 2))
