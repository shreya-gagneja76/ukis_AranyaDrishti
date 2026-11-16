
from pathlib import Path

import rasterio

BASE = Path(__file__).resolve().parent.parent

MASK_DIR = (
    BASE / "data/processed/forest_cover/"
    "esa_worldcover_2021_v200/tree_cover_mask"
)

files = sorted(MASK_DIR.glob("*_tree_mask.tif"))

if len(files) != 5:
    raise RuntimeError(f"Expected 5 masks, found {len(files)}")

print("TREE-COVER MOSAIC GRID INSPECTION")
print("=" * 60)

for path in files:
    with rasterio.open(path) as src:
        print(f"\n{path.name}")
        print("CRS:", src.crs)
        print("Resolution:", src.res)
        print("Bounds:", src.bounds)
        print("Transform:", src.transform)
        print("Dimensions:", src.width, "x", src.height)
        print("NoData:", src.nodata)

print("\nInspection completed.")
