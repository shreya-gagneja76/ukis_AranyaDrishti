
from pathlib import Path
from collections import defaultdict

import numpy as np
import pandas as pd
import rasterio
from pyproj import Geod

BASE = Path(__file__).resolve().parent.parent

INPUT_DIR = (
    BASE / "data/processed/forest_cover/"
    "esa_worldcover_2021_v200"
)

OUTPUT_FILE = (
    INPUT_DIR / "worldcover_class_area_2021.csv"
)

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

geod = Geod(ellps="WGS84")
class_area_m2 = defaultdict(float)
class_pixels = defaultdict(int)

files = sorted(INPUT_DIR.glob("*_uttarakhand.tif"))

if len(files) != 5:
    raise RuntimeError(
        f"Expected 5 clipped rasters, found {len(files)}"
    )

print("WORLDCOVER CLASS AREA CALCULATION")
print("=" * 55)

for path in files:

    print(f"\nProcessing: {path.name}")

    with rasterio.open(path) as src:

        transform = src.transform

        for row in range(src.height):

            data = src.read(
                1,
                window=((row, row + 1), (0, src.width))
            )[0]

            # Ignore NoData pixels.
            valid = data[data != 0]

            if valid.size == 0:
                continue

            # Get the four geographic corners of one pixel
            # in this raster row.
            x0, y0 = transform * (0, row)
            x1, y1 = transform * (1, row + 1)

            x0_next, y0_next = transform * (1, row)
            x1_next, y1_next = transform * (0, row + 1)

            pixel_area, _ = geod.polygon_area_perimeter(
                [x0, x0_next, x1, x1_next],
                [y0, y0_next, y1, y1_next]
            )

            pixel_area = abs(pixel_area)

            classes, counts = np.unique(
                valid,
                return_counts=True
            )

            for land_class, count in zip(classes, counts):
                class_pixels[int(land_class)] += int(count)

                class_area_m2[int(land_class)] += (
                    int(count) * pixel_area
                )

    print("Completed.")

# Build final results.
rows = []

for land_class in sorted(class_pixels):

    area_km2 = class_area_m2[land_class] / 1_000_000

    rows.append({
        "Class_Code": land_class,
        "Land_Cover": CLASS_NAMES.get(
            land_class, "Unknown"
        ),
        "Pixel_Count": class_pixels[land_class],
        "Area_km2": area_km2,
    })

results = pd.DataFrame(rows)

results.to_csv(OUTPUT_FILE, index=False)

print("\nFINAL LAND-COVER AREA")
print("=" * 75)
print(results.to_string(index=False, formatters={
    "Area_km2": "{:,.3f}".format
}))

print("\nTotal valid pixels:", sum(class_pixels.values()))
print(
    "Total area (km²):",
    round(sum(class_area_m2.values()) / 1_000_000, 3)
)

print("\nCSV saved to:")
print(OUTPUT_FILE)
