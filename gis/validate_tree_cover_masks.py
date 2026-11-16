
from pathlib import Path

import numpy as np
import rasterio
from rasterio.windows import Window

BASE = Path(__file__).resolve().parent.parent

INPUT_DIR = (
    BASE / "data/processed/forest_cover/"
    "esa_worldcover_2021_v200"
)

MASK_DIR = INPUT_DIR / "tree_cover_mask"

files = sorted(MASK_DIR.glob("*_tree_mask.tif"))

if len(files) != 5:
    raise RuntimeError(
        f"Expected 5 masks, found {len(files)}"
    )

print("TREE-COVER MASK VALIDATION")
print("=" * 55)

total_tree = 0
total_other = 0
total_nodata = 0

for mask_path in files:

    original_path = INPUT_DIR / (
        mask_path.name.replace("_tree_mask.tif", ".tif")
    )

    tree = 0
    other = 0
    nodata = 0

    with rasterio.open(original_path) as original, \
         rasterio.open(mask_path) as mask:

        if original.shape != mask.shape:
            raise ValueError(f"Dimension mismatch: {mask_path.name}")

        if original.crs != mask.crs:
            raise ValueError(f"CRS mismatch: {mask_path.name}")

        if original.transform != mask.transform:
            raise ValueError(f"Transform mismatch: {mask_path.name}")

        if mask.dtypes[0] != "uint8" or mask.nodata != 255:
            raise ValueError(f"Invalid mask format: {mask_path.name}")

        for row in range(0, mask.height, 512):

            height = min(512, mask.height - row)
            window = Window(0, row, mask.width, height)

            original_data = original.read(1, window=window)
            mask_data = mask.read(1, window=window)

            if not np.isin(mask_data, [0, 1, 255]).all():
                raise ValueError(
                    f"Unexpected pixel value: {mask_path.name}"
                )

            # Compare mask directly with original classification.
            if not np.array_equal(
                mask_data == 1,
                original_data == 10
            ):
                raise ValueError(
                    f"Tree-cover mismatch: {mask_path.name}"
                )

            tree += np.count_nonzero(mask_data == 1)
            other += np.count_nonzero(mask_data == 0)
            nodata += np.count_nonzero(mask_data == 255)

    total_tree += tree
    total_other += other
    total_nodata += nodata

    print(f"\n{mask_path.name}")
    print("Tree pixels:", f"{tree:,}")
    print("Other pixels:", f"{other:,}")
    print("NoData pixels:", f"{nodata:,}")
    print("Validation: PASSED")

print("\n" + "=" * 55)
print("TOTAL TREE PIXELS:", f"{total_tree:,}")
print("TOTAL OTHER PIXELS:", f"{total_other:,}")
print("TOTAL NODATA PIXELS:", f"{total_nodata:,}")
print("\nAll five masks validated successfully.")
