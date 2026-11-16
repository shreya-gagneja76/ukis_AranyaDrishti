
from pathlib import Path
import math

import fiona
import numpy as np
import pandas as pd
import rasterio

from pyproj import CRS, Geod, Transformer
from rasterio.features import rasterize
from rasterio.windows import Window, from_bounds
from shapely.geometry import shape, mapping
from shapely.ops import transform as transform_geometry


# ============================================================
# PATHS AND SETTINGS
# ============================================================

BASE = Path(__file__).resolve().parent.parent

DISTRICT_FILE = (
    BASE / "data" / "processed"
    / "uttarakhand_districts.gpkg"
)

MOSAIC_FILE = (
    BASE / "data" / "processed" / "forest_cover"
    / "esa_worldcover_2021_v200"
    / "uttarakhand_tree_cover_mosaic_2021.tif"
)

# New output: preserve the previous CSV.
OUTPUT_FILE = (
    BASE / "data" / "processed" / "forest_cover"
    / "esa_worldcover_2021_v200"
    / "district_tree_cover_2021_v2.csv"
)

LAYER_NAME = "districts"

TREE_VALUE = 1
NODATA = 255

BLOCK_SIZE = 512

geod = Geod(ellps="WGS84")


# ============================================================
# LOAD DISTRICTS
# ============================================================

def load_districts(target_crs):

    districts = []

    with fiona.open(
        DISTRICT_FILE,
        layer=LAYER_NAME
    ) as source:

        source_crs = CRS.from_user_input(
            source.crs_wkt or source.crs
        )

        to_raster = Transformer.from_crs(
            source_crs,
            target_crs,
            always_xy=True
        )

        to_geographic = Transformer.from_crs(
            source_crs,
            CRS.from_epsg(4326),
            always_xy=True
        )

        for feature in source:

            properties = feature["properties"]

            name = str(properties["DISTRICT_NAME"])
            lgd = str(properties["DIST_LGD"])

            if feature["geometry"] is None:
                raise ValueError(
                    f"Missing geometry for {name}"
                )

            original_geometry = shape(
                feature["geometry"]
            )

            if (
                original_geometry.is_empty
                or not original_geometry.is_valid
            ):
                raise ValueError(
                    f"Invalid geometry for {name}"
                )

            raster_geometry = transform_geometry(
                to_raster.transform,
                original_geometry
            )

            geographic_geometry = transform_geometry(
                to_geographic.transform,
                original_geometry
            )

            district_area_m2, _ = (
                geod.geometry_area_perimeter(
                    geographic_geometry
                )
            )

            districts.append({
                "lgd": lgd,
                "name": name,
                "geometry": raster_geometry,
                "area_m2": abs(district_area_m2)
            })

    if len(districts) != 13:
        raise ValueError(
            f"Expected 13 districts, found {len(districts)}"
        )

    lgd_codes = [
        d["lgd"] for d in districts
    ]

    if len(set(lgd_codes)) != 13:
        raise ValueError(
            "Duplicate district LGD codes detected."
        )

    return districts


# ============================================================
# GEOGRAPHIC AREA OF ONE RASTER PIXEL
# ============================================================

def get_pixel_area_m2(transform, row):

    x0, y0 = transform * (0, row)
    x1, y1 = transform * (1, row)
    x2, y2 = transform * (1, row + 1)
    x3, y3 = transform * (0, row + 1)

    area, _ = geod.polygon_area_perimeter(
        [x0, x1, x2, x3],
        [y0, y1, y2, y3]
    )

    return abs(area)


# ============================================================
# MAIN
# ============================================================

def main():

    print("UTTARAKHAND DISTRICT-WISE TREE-COVER ANALYSIS")
    print("=" * 65)

    if not DISTRICT_FILE.exists():
        raise FileNotFoundError(DISTRICT_FILE)

    if not MOSAIC_FILE.exists():
        raise FileNotFoundError(MOSAIC_FILE)

    with rasterio.open(MOSAIC_FILE) as src:

        print("\nMosaic opened successfully.")
        print("CRS:", src.crs)
        print("Dimensions:", src.width, "x", src.height)

        districts = load_districts(src.crs)

        print("Districts loaded:", len(districts))

        # Each district gets a unique raster ID from 1 to 13.
        district_shapes = [
            (mapping(d["geometry"]), i)
            for i, d in enumerate(districts, start=1)
        ]

        # Calculate the combined district bounding window.
        min_x = min(
            d["geometry"].bounds[0] for d in districts
        )
        min_y = min(
            d["geometry"].bounds[1] for d in districts
        )
        max_x = max(
            d["geometry"].bounds[2] for d in districts
        )
        max_y = max(
            d["geometry"].bounds[3] for d in districts
        )

        bounds_window = from_bounds(
            min_x,
            min_y,
            max_x,
            max_y,
            transform=src.transform
        )

        # Align processing blocks to the GLOBAL raster grid.
        # This ensures that district boundaries are evaluated
        # consistently, regardless of individual district bounds.
        start_row = max(
            0,
            math.floor(bounds_window.row_off / BLOCK_SIZE)
            * BLOCK_SIZE
        )

        start_col = max(
            0,
            math.floor(bounds_window.col_off / BLOCK_SIZE)
            * BLOCK_SIZE
        )

        end_row = min(
            src.height,
            math.ceil(
                (bounds_window.row_off + bounds_window.height)
                / BLOCK_SIZE
            ) * BLOCK_SIZE
        )

        end_col = min(
            src.width,
            math.ceil(
                (bounds_window.col_off + bounds_window.width)
                / BLOCK_SIZE
            ) * BLOCK_SIZE
        )

        # Per-district accumulators.
        tree_counts = np.zeros(13, dtype=np.int64)
        valid_counts = np.zeros(13, dtype=np.int64)
        tree_areas = np.zeros(13, dtype=np.float64)

        total_tree_pixels = 0
        total_assigned_tree_pixels = 0

        print("\nProcessing globally aligned blocks...")

        for row_off in range(
            start_row,
            end_row,
            BLOCK_SIZE
        ):

            print(
                f"Processing raster rows "
                f"{row_off} - "
                f"{min(row_off + BLOCK_SIZE, end_row)}"
            )

            for col_off in range(
                start_col,
                end_col,
                BLOCK_SIZE
            ):

                height = min(
                    BLOCK_SIZE,
                    src.height - row_off
                )

                width = min(
                    BLOCK_SIZE,
                    src.width - col_off
                )

                block_window = Window(
                    col_off,
                    row_off,
                    width,
                    height
                )

                data = src.read(
                    1,
                    window=block_window
                )

                # Rasterize ALL districts together.
                district_ids = rasterize(
                    district_shapes,
                    out_shape=(height, width),
                    transform=src.window_transform(
                        block_window
                    ),
                    fill=0,
                    dtype="uint8",
                    all_touched=False
                )

                # ID 0 = outside districts.
                inside = district_ids > 0

                # Valid land-cover pixels inside districts.
                valid = (
                    inside
                    & (data != NODATA)
                )

                valid_hist = np.bincount(
                    district_ids[valid],
                    minlength=14
                )

                valid_counts += valid_hist[1:14]

                # Tree-cover pixels inside districts.
                tree = (
                    inside
                    & (data == TREE_VALUE)
                )

                total_tree_pixels += int(
                    np.count_nonzero(data == TREE_VALUE)
                )

                total_assigned_tree_pixels += int(
                    np.count_nonzero(tree)
                )

                tree_hist = np.bincount(
                    district_ids[tree],
                    minlength=14
                )

                tree_counts += tree_hist[1:14]

                # Calculate geodesic area row by row.
                for local_row in range(height):

                    row_ids = district_ids[local_row]
                    row_data = data[local_row]

                    row_tree = (
                        (row_ids > 0)
                        & (row_data == TREE_VALUE)
                    )

                    if not np.any(row_tree):
                        continue

                    row_hist = np.bincount(
                        row_ids[row_tree],
                        minlength=14
                    )

                    absolute_row = row_off + local_row

                    pixel_area = get_pixel_area_m2(
                        src.transform,
                        absolute_row
                    )

                    tree_areas += (
                        row_hist[1:14] * pixel_area
                    )

        # ====================================================
        # VALIDATION
        # ====================================================

        print("\nRASTER COUNT VALIDATION")
        print("=" * 65)

        print(
            "Tree pixels in processed extent:",
            f"{total_tree_pixels:,}"
        )

        print(
            "Tree pixels assigned to districts:",
            f"{total_assigned_tree_pixels:,}"
        )

        print(
            "Sum of district tree counts:",
            f"{tree_counts.sum():,}"
        )

        if total_tree_pixels != total_assigned_tree_pixels:
            raise ValueError(
                "Some tree pixels were not assigned to districts."
            )

        if total_assigned_tree_pixels != tree_counts.sum():
            raise ValueError(
                "District tree counts do not reconcile."
            )

        # ====================================================
        # BUILD RESULTS
        # ====================================================

        results = []

        for i, district in enumerate(districts):

            tree_area_km2 = (
                tree_areas[i] / 1_000_000
            )

            district_area_km2 = (
                district["area_m2"] / 1_000_000
            )

            tree_percent = (
                tree_areas[i] / district["area_m2"]
            ) * 100

            results.append({
                "DIST_LGD": district["lgd"],
                "District": district["name"],
                "Tree_Cover_Pixels": int(tree_counts[i]),
                "Valid_Land_Pixels": int(valid_counts[i]),
                "Tree_Cover_Area_km2": tree_area_km2,
                "District_Area_km2": district_area_km2,
                "Tree_Cover_Percent": tree_percent
            })

    # ========================================================
    # SAVE NEW CSV
    # ========================================================

    df = pd.DataFrame(results)

    df = df.sort_values(
        "District"
    ).reset_index(drop=True)

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    df.to_csv(
        OUTPUT_FILE,
        index=False,
        float_format="%.6f"
    )

    print("\n" + "=" * 65)
    print("FINAL DISTRICT-WISE TREE-COVER RESULTS")
    print("=" * 65)

    print(
        df.to_string(
            index=False,
            formatters={
                "Tree_Cover_Area_km2": "{:,.3f}".format,
                "District_Area_km2": "{:,.3f}".format,
                "Tree_Cover_Percent": "{:.3f}%".format
            }
        )
    )

    print("\nDistricts processed:", len(df))

    print(
        "Total tree-cover pixels:",
        f"{df['Tree_Cover_Pixels'].sum():,}"
    )

    print("\nNew CSV saved to:")
    print(OUTPUT_FILE)


if __name__ == "__main__":
    main()
