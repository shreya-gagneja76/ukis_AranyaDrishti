
from pathlib import Path
from collections import Counter

import geopandas as gpd
import numpy as np
import rasterio
from rasterio.features import geometry_mask
from rasterio.windows import Window

BASE = Path(__file__).resolve().parent.parent

BOUNDARY = BASE / "data/processed/uttarakhand_districts.gpkg"

CLIP_DIR = (
    BASE / "data/processed/forest_cover/"
    "esa_worldcover_2021_v200"
)

# Read Uttarakhand's validated district boundaries.
districts = gpd.read_file(BOUNDARY, layer="districts")
districts = districts.to_crs("EPSG:4326")
state_geometry = districts.geometry.union_all()

print("WORLDCOVER CLIP VALIDATION")
print("=" * 55)

files = sorted(CLIP_DIR.glob("*_uttarakhand.tif"))

if len(files) != 5:
    raise RuntimeError(
        f"Expected 5 clipped rasters, found {len(files)}"
    )

for path in files:

    counts = Counter()
    outside_nonzero = 0

    with rasterio.open(path) as src:

        # 1. Validate CRS.
        if src.crs.to_string() != "EPSG:4326":
            raise ValueError(f"Unexpected CRS: {path.name}")

        # 2. Validate 10 m resolution.
        expected_resolution = (1 / 12000, 1 / 12000)

        if not np.allclose(
            src.res,
            expected_resolution,
            rtol=0,
            atol=1e-10
        ):
            raise ValueError(
                f"Unexpected resolution: {path.name}, {src.res}"
            )

        # 3. Validate NoData.
        if src.nodata != 0:
            raise ValueError(f"Unexpected NoData: {path.name}")

        # 4. Process the raster in 512-row windows.
        for row in range(0, src.height, 512):

            height = min(512, src.height - row)

            window = Window(
                0, row, src.width, height
            )

            data = src.read(1, window=window)
            transform = src.window_transform(window)

            inside = geometry_mask(
                [state_geometry],
                out_shape=data.shape,
                transform=transform,
                invert=True,
                all_touched=False
            )

            # Count nonzero pixels outside Uttarakhand.
            outside_nonzero += np.count_nonzero(
                (data != 0) & (~inside)
            )

            # Count valid land-cover classes inside Uttarakhand.
            values, frequencies = np.unique(
                data[(data != 0) & inside],
                return_counts=True
            )

            counts.update(
                dict(zip(
                    values.tolist(),
                    frequencies.tolist()
                ))
            )

        # 5. Display validation results.
        print(f"\n{path.name}")
        print("-" * 55)

        print("Dimensions:", src.width, "x", src.height)
        print("CRS:", src.crs)
        print("Resolution:", src.res)
        print("NoData:", src.nodata)

        print(
            "Valid pixels inside Uttarakhand:",
            sum(counts.values())
        )

        print(
            "Class counts:",
            dict(sorted(counts.items()))
        )

        print(
            "Nonzero pixels outside boundary:",
            outside_nonzero
        )

        if outside_nonzero != 0:
            raise ValueError(
                f"Boundary masking failed: {path.name}"
            )

print("\nAll five clipped rasters passed validation.")
