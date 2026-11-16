
from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import from_origin
from rasterio.windows import Window


# ============================================================
# PATHS AND SETTINGS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

MASK_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "forest_cover"
    / "esa_worldcover_2021_v200"
    / "tree_cover_mask"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "forest_cover"
    / "esa_worldcover_2021_v200"
)

OUTPUT_PATH = (
    OUTPUT_DIR
    / "uttarakhand_tree_cover_mosaic_2021.tif"
)

NODATA = 255
BLOCK_SIZE = 512
EXPECTED_TILE_COUNT = 5

# Small tolerance for floating-point grid calculations.
TOLERANCE = 1e-7


# ============================================================
# VALIDATE INPUT MASKS
# ============================================================

def validate_masks(mask_paths):
    if len(mask_paths) != EXPECTED_TILE_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_TILE_COUNT} tree-cover masks, "
            f"but found {len(mask_paths)}."
        )

    datasets = []

    for path in mask_paths:
        src = rasterio.open(path)

        if src.count != 1:
            src.close()
            raise ValueError(
                f"{path.name}: expected a single-band raster."
            )

        if src.crs != rasterio.crs.CRS.from_epsg(4326):
            src.close()
            raise ValueError(
                f"{path.name}: CRS must be EPSG:4326."
            )

        if src.dtypes[0] != "uint8":
            src.close()
            raise ValueError(
                f"{path.name}: data type must be uint8."
            )

        if src.nodata != NODATA:
            src.close()
            raise ValueError(
                f"{path.name}: NoData must be {NODATA}."
            )

        if (
            abs(src.res[0] - 1 / 12000) > TOLERANCE
            or abs(src.res[1] - 1 / 12000) > TOLERANCE
        ):
            src.close()
            raise ValueError(
                f"{path.name}: unexpected pixel resolution "
                f"{src.res}."
            )

        datasets.append(src)

    # All masks must have the same pixel resolution.
    reference_res = datasets[0].res

    for src in datasets[1:]:
        if (
            abs(src.res[0] - reference_res[0]) > TOLERANCE
            or abs(src.res[1] - reference_res[1]) > TOLERANCE
        ):
            raise ValueError(
                f"Resolution mismatch detected in {src.name}."
            )

    # Verify that tile extents do not overlap.
    for i in range(len(datasets)):
        a = datasets[i].bounds

        for j in range(i + 1, len(datasets)):
            b = datasets[j].bounds

            overlap_width = min(a.right, b.right) - max(
                a.left, b.left
            )

            overlap_height = min(a.top, b.top) - max(
                a.bottom, b.bottom
            )

            if (
                overlap_width > TOLERANCE
                and overlap_height > TOLERANCE
            ):
                raise ValueError(
                    "Overlapping tile extents detected: "
                    f"{Path(datasets[i].name).name} and "
                    f"{Path(datasets[j].name).name}"
                )

    return datasets


# ============================================================
# CREATE MOSAIC GRID
# ============================================================

def calculate_mosaic_grid(datasets):
    resolution_x, resolution_y = datasets[0].res

    left = min(src.bounds.left for src in datasets)
    right = max(src.bounds.right for src in datasets)

    bottom = min(src.bounds.bottom for src in datasets)
    top = max(src.bounds.top for src in datasets)

    width_float = (right - left) / resolution_x
    height_float = (top - bottom) / resolution_y

    width = round(width_float)
    height = round(height_float)

    if (
        abs(width_float - width) > TOLERANCE
        or abs(height_float - height) > TOLERANCE
    ):
        raise ValueError(
            "Mosaic extent is not aligned to the source pixel grid."
        )

    transform = from_origin(
        left,
        top,
        resolution_x,
        resolution_y
    )

    return width, height, transform, left, top


# ============================================================
# INITIALIZE OUTPUT WITH NODATA
# ============================================================

def initialize_output(dst):
    print("\nInitializing output with NoData...")

    for row_off in range(0, dst.height, BLOCK_SIZE):
        for col_off in range(0, dst.width, BLOCK_SIZE):

            height = min(
                BLOCK_SIZE,
                dst.height - row_off
            )

            width = min(
                BLOCK_SIZE,
                dst.width - col_off
            )

            window = Window(
                col_off,
                row_off,
                width,
                height
            )

            empty_block = np.full(
                (height, width),
                NODATA,
                dtype=np.uint8
            )

            dst.write(
                empty_block,
                1,
                window=window
            )


# ============================================================
# WRITE SOURCE TILES INTO MOSAIC
# ============================================================

def write_tiles(dst, datasets, mosaic_left, mosaic_top):

    resolution_x, resolution_y = dst.res

    for src in datasets:

        print(f"\nProcessing: {Path(src.name).name}")

        # Calculate the source tile's starting position
        # relative to the mosaic's upper-left corner.
        col_offset_float = (
            src.bounds.left - mosaic_left
        ) / resolution_x

        row_offset_float = (
            mosaic_top - src.bounds.top
        ) / resolution_y

        col_offset = round(col_offset_float)
        row_offset = round(row_offset_float)

        # Confirm that the tile starts on the mosaic grid.
        if (
            abs(col_offset_float - col_offset) > TOLERANCE
            or abs(row_offset_float - row_offset) > TOLERANCE
        ):
            raise ValueError(
                f"Grid alignment error in {Path(src.name).name}."
            )

        # Read and write the source in manageable blocks.
        for _, source_window in src.block_windows(1):

            data = src.read(
                1,
                window=source_window
            )

            destination_window = Window(
                col_offset + source_window.col_off,
                row_offset + source_window.row_off,
                source_window.width,
                source_window.height
            )

            # Direct write: do not read from the output dataset.
            # Source tile extents have already been checked
            # for overlap.
            dst.write(
                data,
                1,
                window=destination_window
            )

        print("  Tile written successfully.")


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("CREATING UTTARAKHAND TREE-COVER MOSAIC")
    print("=" * 60)

    if not MASK_DIR.exists():
        raise FileNotFoundError(
            f"Input mask directory not found:\n{MASK_DIR}"
        )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    # Do not overwrite an existing mosaic.
    if OUTPUT_PATH.exists():
        raise FileExistsError(
            "Output already exists. To avoid overwriting it, "
            "the script has stopped:\n"
            f"{OUTPUT_PATH}"
        )

    mask_paths = sorted(
        MASK_DIR.glob("*_tree_mask.tif")
    )

    print(f"\nInput masks found: {len(mask_paths)}")

    datasets = []

    try:
        datasets = validate_masks(mask_paths)

        width, height, transform, left, top = (
            calculate_mosaic_grid(datasets)
        )

        print("\nMOSAIC GRID")
        print("-" * 60)
        print(f"Dimensions: {width} x {height}")
        print("CRS: EPSG:4326")
        print(f"Resolution: {datasets[0].res}")
        print(f"NoData: {NODATA}")

        profile = {
            "driver": "GTiff",
            "height": height,
            "width": width,
            "count": 1,
            "dtype": "uint8",
            "crs": "EPSG:4326",
            "transform": transform,
            "nodata": NODATA,
            "compress": "LZW",
            "tiled": True,
            "blockxsize": BLOCK_SIZE,
            "blockysize": BLOCK_SIZE,
            "BIGTIFF": "IF_SAFER"
        }

        print("\nCreating output raster...")

        with rasterio.open(
            OUTPUT_PATH,
            "w",
            **profile
        ) as dst:

            initialize_output(dst)

            write_tiles(
                dst,
                datasets,
                left,
                top
            )

        print("\n" + "=" * 60)
        print("MOSAIC CREATED SUCCESSFULLY")
        print("=" * 60)
        print(f"\nOutput:\n{OUTPUT_PATH}")
        print(f"\nDimensions: {width} x {height}")
        print(f"CRS: EPSG:4326")
        print(f"Data type: uint8")
        print(f"NoData: {NODATA}")

    finally:
        for src in datasets:
            src.close()


if __name__ == "__main__":
    main()
