
import geopandas as gpd
from pathlib import Path
from shapely.geometry import box
import math

base = Path(__file__).resolve().parent.parent

boundary_path = (
    base / "data" / "processed" / "uttarakhand_districts.gpkg"
)

districts = gpd.read_file(boundary_path, layer="districts")
state = districts.to_crs("EPSG:4326")

# Combine all 13 district geometries
state_geometry = state.geometry.union_all()

min_lon, min_lat, max_lon, max_lat = state.total_bounds

# Find candidate 3-degree tile boundaries
start_lon = math.floor(min_lon / 3) * 3
end_lon = math.floor(max_lon / 3) * 3

start_lat = math.floor(min_lat / 3) * 3
end_lat = math.floor(max_lat / 3) * 3

tiles = []

for south in range(start_lat, end_lat + 1, 3):
    for west in range(start_lon, end_lon + 1, 3):

        tile_geometry = box(
            west, south,
            west + 3, south + 3
        )

        if state_geometry.intersects(tile_geometry):
            lat_name = f"N{south:02d}"
            lon_name = f"E{west:03d}"

            tiles.append(lat_name + lon_name)

print("WorldCover tiles intersecting Uttarakhand:")
for tile in tiles:
    print(tile)

print("\nTotal tiles:", len(tiles))
