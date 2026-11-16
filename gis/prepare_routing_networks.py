from pathlib import Path

import geopandas as gpd

ROOT = Path(__file__).resolve().parents[1]

INPUT = ROOT / "data/processed/transport_osm/uttarakhand_roads.gpkg"
OUTPUT_DIR = ROOT / "data/processed/transport_osm"

VEHICLE_CLASSES = {
    "motorway", "trunk", "trunk_link",
    "primary", "primary_link",
    "secondary", "secondary_link",
    "tertiary", "tertiary_link",
    "residential", "unclassified",
    "living_street", "service",
}

FOOT_ONLY_CLASSES = {
    "path", "footway", "steps",
    "bridleway", "pedestrian",
}

REVIEW_CLASSES = {
    "track", "track_grade1", "track_grade2",
    "track_grade3", "track_grade4", "track_grade5",
    "cycleway", "busway",
}

OUTPUTS = {
    "vehicle": "uttarakhand_vehicle_roads.gpkg",
    "foot": "uttarakhand_foot_roads.gpkg",
    "review": "uttarakhand_roads_review.gpkg",
}


def main():
    print("Reading original road dataset...")

    roads = gpd.read_file(INPUT)

    if "fclass" not in roads.columns:
        raise ValueError("Required field 'fclass' is missing.")

    if roads.crs is None:
        raise ValueError("Road dataset has no CRS.")

    for filename in OUTPUTS.values():
        output_path = OUTPUT_DIR / filename
        if output_path.exists():
            raise FileExistsError(
                f"Output already exists; refusing to overwrite: {output_path}"
            )

    vehicle = roads[roads["fclass"].isin(VEHICLE_CLASSES)].copy()

    foot = roads[
        roads["fclass"].isin(VEHICLE_CLASSES | FOOT_ONLY_CLASSES)
    ].copy()

    review = roads[roads["fclass"].isin(REVIEW_CLASSES)].copy()

    datasets = {
        "vehicle": vehicle,
        "foot": foot,
        "review": review,
    }

    print("\nWriting candidate datasets...")

    for name, data in datasets.items():
        output_path = OUTPUT_DIR / OUTPUTS[name]
        data.to_file(
            output_path,
            layer=output_path.stem,
            driver="GPKG",
            index=False,
        )
        print(f"{name}: {len(data):,} features -> {output_path.name}")

    print("\nAll candidate datasets created.")
    print("Original road dataset was not modified.")


if __name__ == "__main__":
    main()
