
from pathlib import Path
import geopandas as gpd
import rasterio
import numpy as np
from shapely.geometry import box
from rasterio.windows import Window

BASE = Path(__file__).resolve().parent.parent

BOUNDARY = BASE / "data/processed/uttarakhand_districts.gpkg"

RASTER_DIR = (
    BASE / "data/raw/forest_cover/"
    "esa_worldcover_2021_v200/map"
)

districts = gpd.read_file(BOUNDARY, layer="districts")
state = districts.to_crs("EPSG:4326")
state_geometry = state.geometry.union_all()

print("WORLD COVER CLASS SAMPLE")
print("=" * 45)

for path in sorted(RASTER_DIR.glob("*.tif")):

    with rasterio.open(path) as src:

        tile_geometry = box(*src.bounds)
        intersection = state_geometry.intersection(tile_geometry)

        if intersection.is_empty:
            continue

        point = intersection.representative_point()
        row, col = src.index(point.x, point.y)

        row_start = max(0, row - 256)
        col_start = max(0, col - 256)

        height = min(512, src.height - row_start)
        width = min(512, src.width - col_start)

        window = Window(col_start, row_start, width, height)

        sample = src.read(1, window=window)

        classes, counts = np.unique(
            sample[sample != 0],
            return_counts=True
        )

        print(f"\n{path.name}")
        print("Classes found:", classes.tolist())
        print("Pixel counts:", counts.tolist())

print("\nSampling completed.")
