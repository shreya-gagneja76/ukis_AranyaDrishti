
from pathlib import Path
import csv

import geopandas as gpd
import numpy as np
import rasterio
from rasterio.features import rasterize
from rasterio.windows import transform as window_transform


# --------------------------------------------------
# PATHS AND SETTINGS
# --------------------------------------------------

ROOT = Path(__file__).resolve().parent.parent

boundary_path = ROOT / "data" / "processed" / "uttarakhand_districts.gpkg"

terrain_dir = ROOT / "data" / "processed" / "terrain"

elevation_path = terrain_dir / "uttarakhand_fabdem_30m_lcc.tif"
slope_path = terrain_dir / "uttarakhand_slope_degrees.tif"
aspect_path = terrain_dir / "uttarakhand_aspect_degrees.tif"

output_path = terrain_dir / "district_terrain_stats.csv"

if output_path.exists():
    raise FileExistsError(
        f"Output already exists. Inspect it before rerunning: {output_path}"
    )

for path in [boundary_path, elevation_path, slope_path, aspect_path]:
    if not path.exists():
        raise FileNotFoundError(f"Required input missing: {path}")


# --------------------------------------------------
# HISTOGRAM SETTINGS FOR MEDIAN ESTIMATION
# --------------------------------------------------

# Elevation median resolution: approximately 1 metre.
elevation_edges = np.arange(0, 8001, 1, dtype=np.float64)

# Slope median resolution: 0.1 degree.
slope_edges = np.linspace(0, 90, 901)

directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]


def histogram_median(histogram, edges):
    total = histogram.sum()

    if total == 0:
        return None

    target = (total - 1) // 2
    index = np.searchsorted(np.cumsum(histogram), target + 1)

    return float((edges[index] + edges[index + 1]) / 2)


# --------------------------------------------------
# LOAD DISTRICT BOUNDARIES
# --------------------------------------------------

districts = gpd.read_file(boundary_path)

if len(districts) != 13:
    raise ValueError(f"Expected 13 districts, found {len(districts)}")

if districts.crs is None:
    raise ValueError("District boundaries have no CRS.")

districts = districts.sort_values("DIST_LGD").reset_index(drop=True)


# --------------------------------------------------
# INITIALISE DISTRICT ACCUMULATORS
# --------------------------------------------------

stats = {}

for idx, district in districts.iterrows():

    stats[idx + 1] = {
        "district_id": str(district["DIST_LGD"]).zfill(3),
        "district_name": district["DISTRICT_NAME"],

        "elev_count": 0,
        "elev_sum": 0.0,
        "elev_min": float("inf"),
        "elev_max": float("-inf"),
        "elev_hist": np.zeros(len(elevation_edges) - 1, dtype=np.int64),

        "slope_count": 0,
        "slope_sum": 0.0,
        "slope_min": float("inf"),
        "slope_max": float("-inf"),
        "slope_hist": np.zeros(len(slope_edges) - 1, dtype=np.int64),

        "steep_count": 0,

        "aspect_count": 0,
        "aspect_directions": np.zeros(8, dtype=np.int64),
    }

shapes = [
    (geom, idx + 1)
    for idx, geom in enumerate(districts.geometry)
    if geom is not None and not geom.is_empty
]


# --------------------------------------------------
# PROCESS TERRAIN RASTERS BLOCK BY BLOCK
# --------------------------------------------------

with rasterio.open(elevation_path) as elev_src, \
     rasterio.open(slope_path) as slope_src, \
     rasterio.open(aspect_path) as aspect_src:

    sources = [elev_src, slope_src, aspect_src]

    for src in sources[1:]:

        if (
            src.width != elev_src.width
            or src.height != elev_src.height
            or src.crs != elev_src.crs
            or not src.transform.almost_equals(elev_src.transform)
        ):
            raise ValueError("Terrain rasters do not share the same grid.")

    if districts.crs != elev_src.crs:
        districts = districts.to_crs(elev_src.crs)

        shapes = [
            (geom, idx + 1)
            for idx, geom in enumerate(districts.geometry)
            if geom is not None and not geom.is_empty
        ]

    total_blocks = (
        (elev_src.width + 511) // 512
    ) * (
        (elev_src.height + 511) // 512
    )

    completed = 0

    print("CALCULATING DISTRICT TERRAIN STATISTICS")
    print("=" * 60)
    print("Districts:", len(districts))
    print("Raster dimensions:", elev_src.width, "x", elev_src.height)

    for _, window in elev_src.block_windows(1):

        elevation = elev_src.read(1, window=window, masked=True)
        slope = slope_src.read(1, window=window, masked=True)
        aspect = aspect_src.read(1, window=window, masked=True)

        elevation_data = elevation.filled(np.nan).astype(np.float32)
        slope_data = slope.filled(np.nan).astype(np.float32)
        aspect_data = aspect.filled(np.nan).astype(np.float32)

        labels = rasterize(
            shapes,
            out_shape=(int(window.height), int(window.width)),
            transform=window_transform(window, elev_src.transform),
            fill=0,
            dtype="uint8",
            all_touched=False
        )

        for district_id, result in stats.items():

            zone = labels == district_id

            if not zone.any():
                continue

            # Elevation
            valid_elev = (
                zone
                & ~np.ma.getmaskarray(elevation)
                & np.isfinite(elevation_data)
            )

            elev_values = elevation_data[valid_elev]

            if elev_values.size:

                if elev_values.min() < elevation_edges[0] or elev_values.max() > elevation_edges[-1]:
                    raise ValueError("Elevation outside histogram range.")

                result["elev_count"] += elev_values.size
                result["elev_sum"] += float(elev_values.sum(dtype=np.float64))
                result["elev_min"] = min(result["elev_min"], float(elev_values.min()))
                result["elev_max"] = max(result["elev_max"], float(elev_values.max()))

                result["elev_hist"] += np.histogram(
                    elev_values, bins=elevation_edges
                )[0]

            # Slope
            valid_slope = (
                zone
                & ~np.ma.getmaskarray(slope)
                & np.isfinite(slope_data)
            )

            slope_values = slope_data[valid_slope]

            if slope_values.size:

                if slope_values.min() < 0 or slope_values.max() > 90:
                    raise ValueError("Slope outside expected range.")

                result["slope_count"] += slope_values.size
                result["slope_sum"] += float(slope_values.sum(dtype=np.float64))
                result["slope_min"] = min(result["slope_min"], float(slope_values.min()))
                result["slope_max"] = max(result["slope_max"], float(slope_values.max()))

                result["slope_hist"] += np.histogram(
                    slope_values, bins=slope_edges
                )[0]

                result["steep_count"] += int(
                    np.count_nonzero(slope_values > 30)
                )

            # Aspect: exclude NoData and undefined flat terrain.
            valid_aspect = (
                zone
                & ~np.ma.getmaskarray(aspect)
                & np.isfinite(aspect_data)
            )

            aspect_values = aspect_data[valid_aspect]

            if aspect_values.size:

                if aspect_values.min() < 0 or aspect_values.max() >= 360:
                    raise ValueError("Aspect outside expected range.")

                direction_indices = (
                    ((aspect_values + 22.5) % 360) // 45
                ).astype(np.int8)

                result["aspect_count"] += aspect_values.size

                result["aspect_directions"] += np.bincount(
                    direction_indices, minlength=8
                )

        completed += 1

        if completed % 20 == 0:
            print(f"Processed {completed}/{total_blocks} blocks")


# --------------------------------------------------
# WRITE DISTRICT SUMMARY CSV
# --------------------------------------------------

fieldnames = [
    "DIST_LGD",
    "DISTRICT_NAME",
    "Elevation_Pixels",
    "Elevation_Min_m",
    "Elevation_Mean_m",
    "Elevation_Median_approx_m",
    "Elevation_Max_m",
    "Slope_Pixels",
    "Slope_Mean_deg",
    "Slope_Median_approx_deg",
    "Slope_Max_deg",
    "Steep_Terrain_Above_30deg_pct",
    "Aspect_Pixels",
]

fieldnames += [
    f"Aspect_{direction}_pct"
    for direction in directions
]

with open(output_path, "w", newline="", encoding="utf-8-sig") as file:

    writer = csv.DictWriter(file, fieldnames=fieldnames)
    writer.writeheader()

    for district_id, result in stats.items():

        elev_count = result["elev_count"]
        slope_count = result["slope_count"]
        aspect_count = result["aspect_count"]

        row = {
            "DIST_LGD": result["district_id"],
            "DISTRICT_NAME": result["district_name"],

            "Elevation_Pixels": elev_count,
            "Elevation_Min_m": result["elev_min"] if elev_count else None,
            "Elevation_Mean_m": result["elev_sum"] / elev_count if elev_count else None,
            "Elevation_Median_approx_m": histogram_median(
                result["elev_hist"], elevation_edges
            ),
            "Elevation_Max_m": result["elev_max"] if elev_count else None,

            "Slope_Pixels": slope_count,
            "Slope_Mean_deg": result["slope_sum"] / slope_count if slope_count else None,
            "Slope_Median_approx_deg": histogram_median(
                result["slope_hist"], slope_edges
            ),
            "Slope_Max_deg": result["slope_max"] if slope_count else None,

            "Steep_Terrain_Above_30deg_pct": (
                100 * result["steep_count"] / slope_count
                if slope_count else None
            ),

            "Aspect_Pixels": aspect_count,
        }

        for i, direction in enumerate(directions):

            row[f"Aspect_{direction}_pct"] = (
                100 * result["aspect_directions"][i] / aspect_count
                if aspect_count else None
            )

        writer.writerow(row)


print("\nDISTRICT TERRAIN SUMMARY COMPLETE")
print("Output:", output_path)
print("Districts written:", len(stats))
