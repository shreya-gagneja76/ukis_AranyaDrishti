
from pathlib import Path
import math

import geopandas as gpd
import rasterio
from rasterio.features import geometry_mask
from rasterio.windows import Window, from_bounds
from shapely.geometry import box

BASE = Path(__file__).resolve().parent.parent

BOUNDARY = BASE / "data/processed/uttarakhand_districts.gpkg"

INPUT_DIR = (
    BASE / "data/raw/forest_cover/"
    "esa_worldcover_2021_v200/map"
)

OUTPUT_DIR = (
    BASE / "data/processed/forest_cover/"
    "esa_worldcover_2021_v200"
)

CHUNK_ROWS = 512

# Create output directory if it does not exist.
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Read and combine the 13 district geometries.
districts = gpd.read_file(BOUNDARY, layer="districts")

state = districts.to_crs("EPSG:4326")
state_geometry = state.geometry.union_all()

if state_geometry.is_empty:
    raise RuntimeError("Uttarakhand boundary geometry is empty.")

print("UTTARAKHAND WORLDCOVER CLIPPING")
print("=" * 55)

input_files = sorted(INPUT_DIR.glob("*.tif"))

if len(input_files) != 5:
    raise RuntimeError(
        f"Expected 5 source tiles, found {len(input_files)}"
    )

for input_path in input_files:

    output_path = (
        OUTPUT_DIR /
        f"{input_path.stem}_uttarakhand.tif"
    )

    with rasterio.open(input_path) as src:

        # Find the intersection between the state and this tile.
        tile_geometry = box(*src.bounds)

        intersection = state_geometry.intersection(
            tile_geometry
        )

        if intersection.is_empty:
            print(f"\nSkipping: {input_path.name}")
            continue

        # Calculate the raster window covering the intersection.
        bounds = intersection.bounds

        window = from_bounds(
            *bounds,
            transform=src.transform
        )

        # Round outward to avoid accidentally dropping edge pixels.
        col_start = max(
            0,
            math.floor(window.col_off)
        )

        row_start = max(
            0,
            math.floor(window.row_off)
        )

        col_end = min(
            src.width,
            math.ceil(window.col_off + window.width)
        )

        row_end = min(
            src.height,
            math.ceil(window.row_off + window.height)
        )

        width = col_end - col_start
        height = row_end - row_start

        if width <= 0 or height <= 0:
            raise RuntimeError(
                f"Invalid clipping window: {input_path.name}"
            )

        output_window = Window(
            col_start,
            row_start,
            width,
            height
        )

        output_transform = src.window_transform(
            output_window
        )

        # Preserve source metadata and update output dimensions.
        profile = src.profile.copy()

        profile.update(
            driver="GTiff",
            width=width,
            height=height,
            transform=output_transform,
            count=1,
            dtype="uint8",
            nodata=0,
            compress="LZW"
        )

        with rasterio.open(output_path, "w", **profile) as dst:

            # Process the raster in small row chunks.
            for row in range(0, height, CHUNK_ROWS):

                chunk_height = min(
                    CHUNK_ROWS,
                    height - row
                )

                source_window = Window(
                    col_start,
                    row_start + row,
                    width,
                    chunk_height
                )

                destination_window = Window(
                    0,
                    row,
                    width,
                    chunk_height
                )

                data = src.read(
                    1,
                    window=source_window
                )

                chunk_transform = src.window_transform(
                    source_window
                )

                # Identify pixels whose centres lie inside Uttarakhand.
                inside = geometry_mask(
                    [state_geometry],
                    out_shape=data.shape,
                    transform=chunk_transform,
                    invert=True,
                    all_touched=False
                )

                # Set pixels outside the state to NoData.
                data[~inside] = 0

                dst.write(
                    data,
                    1,
                    window=destination_window
                )

        print(f"\nCompleted: {input_path.name}")
        print(f"Output: {output_path.name}")
        print(f"Dimensions: {width} x {height}")
        print(f"Bounds: {output_transform * (0, 0)}")

print("\nClipping process completed.")
