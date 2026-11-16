
from pathlib import Path

import numpy as np
import rasterio
from rasterio.windows import Window
from scipy.ndimage import correlate


# --------------------------------------------------
# PATHS AND SETTINGS
# --------------------------------------------------

ROOT = Path(__file__).resolve().parent.parent

dem_path = (
    ROOT / "data" / "processed" / "terrain"
    / "uttarakhand_fabdem_30m_lcc.tif"
)

output_dir = ROOT / "data" / "processed" / "terrain"

slope_path = output_dir / "uttarakhand_slope_degrees.tif"
aspect_path = output_dir / "uttarakhand_aspect_degrees.tif"

NODATA = -9999.0
BLOCK_SIZE = 512

if not dem_path.exists():
    raise FileNotFoundError(f"DEM not found: {dem_path}")

if slope_path.exists() or aspect_path.exists():
    raise FileExistsError(
        "Slope or aspect output already exists. "
        "Inspect existing outputs before rerunning."
    )


# --------------------------------------------------
# HORN 3x3 KERNELS
# --------------------------------------------------

kernel_x = np.array([
    [-1, 0, 1],
    [-2, 0, 2],
    [-1, 0, 1]
], dtype=np.float32) / 8.0

kernel_y = np.array([
    [1, 2, 1],
    [0, 0, 0],
    [-1, -2, -1]
], dtype=np.float32) / 8.0

neighbour_kernel = np.ones((3, 3), dtype=np.uint8)


# --------------------------------------------------
# PROCESS DEM BLOCK BY BLOCK
# --------------------------------------------------

with rasterio.open(dem_path) as src:

    if src.crs is None or not src.crs.is_projected:
        raise ValueError("DEM must use a projected CRS.")

    x_resolution, y_resolution = src.res

    if not np.isclose(x_resolution, y_resolution):
        raise ValueError("Expected square DEM pixels.")

    if not np.isclose(x_resolution, 30.0):
        raise ValueError("Expected 30 m DEM resolution.")

    profile = src.profile.copy()

    profile.update(
        dtype="float32",
        count=1,
        nodata=NODATA,
        compress="deflate",
        predictor=3,
        BIGTIFF="IF_SAFER"
    )

    print("GENERATING SLOPE AND ASPECT")
    print("=" * 60)
    print("Input:", dem_path.name)
    print("Dimensions:", src.width, "x", src.height)
    print("Resolution:", x_resolution, "m")
    print("Block size:", BLOCK_SIZE)

    with rasterio.open(slope_path, "w", **profile) as slope_dst, \
         rasterio.open(aspect_path, "w", **profile) as aspect_dst:

        total_blocks = (
            (src.width + BLOCK_SIZE - 1) // BLOCK_SIZE
        ) * (
            (src.height + BLOCK_SIZE - 1) // BLOCK_SIZE
        )

        completed_blocks = 0

        for row in range(0, src.height, BLOCK_SIZE):
            for col in range(0, src.width, BLOCK_SIZE):

                height = min(BLOCK_SIZE, src.height - row)
                width = min(BLOCK_SIZE, src.width - col)

                # Read a one-pixel halo around the block.
                read_row = max(0, row - 1)
                read_col = max(0, col - 1)

                read_bottom = min(src.height, row + height + 1)
                read_right = min(src.width, col + width + 1)

                read_height = read_bottom - read_row
                read_width = read_right - read_col

                window = Window(
                    read_col,
                    read_row,
                    read_width,
                    read_height
                )

                dem = src.read(1, window=window, masked=True)
                dem = dem.filled(np.nan).astype(np.float32)

                valid = np.isfinite(dem)
                safe_dem = np.where(valid, dem, 0.0)

                # Calculate Horn derivatives.
                dz_dx = correlate(
                    safe_dem,
                    kernel_x,
                    mode="nearest"
                ) / x_resolution

                dz_dy = correlate(
                    safe_dem,
                    kernel_y,
                    mode="nearest"
                ) / y_resolution

                # Require a complete valid 3x3 neighbourhood.
                valid_neighbours = correlate(
                    valid.astype(np.uint8),
                    neighbour_kernel,
                    mode="constant",
                    cval=0
                ) == 9

                valid_output = valid & valid_neighbours

                gradient = np.hypot(dz_dx, dz_dy)

                slope = np.degrees(
                    np.arctan(gradient)
                ).astype(np.float32)

                # Aspect: downhill direction, clockwise from north.
                aspect = (
                    np.degrees(
                        np.arctan2(-dz_dx, -dz_dy)
                    ) + 360.0
                ) % 360.0

                aspect = aspect.astype(np.float32)

                flat = gradient < 1e-8

                slope[~valid_output] = NODATA
                aspect[~valid_output | flat] = NODATA

                # Extract only the central block.
                row_offset = row - read_row
                col_offset = col - read_col

                row_slice = slice(
                    row_offset,
                    row_offset + height
                )
                col_slice = slice(
                    col_offset,
                    col_offset + width
                )

                output_window = Window(col, row, width, height)

                slope_dst.write(
                    slope[row_slice, col_slice],
                    1,
                    window=output_window
                )

                aspect_dst.write(
                    aspect[row_slice, col_slice],
                    1,
                    window=output_window
                )

                completed_blocks += 1

                if completed_blocks % 20 == 0:
                    print(
                        f"Processed {completed_blocks}/{total_blocks} blocks"
                    )

print("\nTERRAIN DERIVATIVES COMPLETE")
print("Slope:", slope_path)
print("Aspect:", aspect_path)
