
from pathlib import Path
import rasterio

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = (
    BASE_DIR
    / "data"
    / "raw"
    / "forest_cover"
    / "esa_worldcover_2021_v200"
    / "map"
)

files = sorted(DATA_DIR.glob("*.tif"))

print("ESA WORLDCOVER 2021 V200 - RASTER INSPECTION")
print("=" * 55)

if len(files) != 5:
    raise RuntimeError(
        f"Expected 5 GeoTIFF files, found {len(files)}"
    )

for file in files:

    print(f"\nFILE: {file.name}")
    print("-" * 55)

    with rasterio.open(file) as src:

        print("CRS:", src.crs)
        print("Width (columns):", src.width)
        print("Height (rows):", src.height)
        print("Number of bands:", src.count)
        print("Data type:", src.dtypes)
        print("Resolution:", src.res)
        print("NoData value:", src.nodata)
        print("Bounds:", src.bounds)
        print("File size (MB):", round(file.stat().st_size / (1024**2), 2))

print("\nInspection completed.")
