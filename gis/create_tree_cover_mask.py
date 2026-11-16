
from pathlib import Path

import numpy as np
import rasterio
from rasterio.windows import Window

BASE = Path(__file__).resolve().parent.parent

INPUT_DIR = (
    BASE / "data/processed/forest_cover/"
    "esa_worldcover_2021_v200"
)

OUTPUT_DIR = INPUT_DIR / "tree_cover_mask"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

files = sorted(INPUT_DIR.glob("*_uttarakhand.tif"))

if len(files) != 5:
    raise RuntimeError(
        f"Expected 5 clipped rasters, found {len(files)}"
    )

print("CREATING TREE-COVER MASKS")
print("=" * 50)

for input_path in files:

    output_path = (
        OUTPUT_DIR /
        f"{input_path.stem}_tree_mask.tif"
    )

    tree_pixels = 0
    other_pixels = 0
    nodata_pixels = 0

    with rasterio.open(input_path) as src:

        profile = src.profile.copy()

        profile.update(
            dtype="uint8",
            nodata=255,
            compress="LZW"
        )

        with rasterio.open(output_path, "w", **profile) as dst:

            for row in range(0, src.height, 512):

                height = min(512, src.height - row)

                window = Window(
                    0, row, src.width, height
                )

                data = src.read(1, window=window)

                mask = np.full(
                    data.shape,
                    255,
                    dtype=np.uint8
                )

                valid = data != 0

                mask[valid] = 0
                mask[data == 10] = 1

                tree_pixels += np.count_nonzero(
                    data == 10
                )

                other_pixels += np.count_nonzero(
                    valid & (data != 10)
                )

                nodata_pixels += np.count_nonzero(
                    ~valid
                )

                dst.write(mask, 1, window=window)

    print(f"\nCreated: {output_path.name}")
    print(f"Tree-cover pixels: {tree_pixels:,}")
    print(f"Other valid pixels: {other_pixels:,}")
    print(f"NoData pixels: {nodata_pixels:,}")

print("\nAll tree-cover masks created.")
