
from collections import defaultdict
from pathlib import Path

import geopandas as gpd
import pyogrio
from shapely.geometry import Point
from shapely.ops import substring
from shapely.strtree import STRtree


BASE = Path("data/processed/transport_osm")

ROADS_FILE = BASE / "uttarakhand_vehicle_components.gpkg"
INTERSECTIONS_FILE = BASE / "uttarakhand_candidate_intersections.gpkg"
JUNCTIONS_FILE = BASE / "uttarakhand_candidate_junctions.gpkg"

OUTPUT_FILE = BASE / "uttarakhand_vehicle_network.gpkg"

CHUNK_SIZE = 5000
MATCH_TOLERANCE = 0.001
POSITION_TOLERANCE = 1e-6


def main():

    if OUTPUT_FILE.exists():
        raise FileExistsError(
            f"Output already exists: {OUTPUT_FILE}. "
            "Inspect it before deciding whether to rebuild."
        )

    print("Reading input datasets...")

    roads = pyogrio.read_dataframe(
        ROADS_FILE,
        layer="vehicle_components"
    )

    intersections = pyogrio.read_dataframe(
        INTERSECTIONS_FILE,
        layer="candidate_intersections"
    )

    junctions = pyogrio.read_dataframe(
        JUNCTIONS_FILE,
        layer="candidate_junctions"
    )

    print("Components:", len(roads))
    print("Intersections:", len(intersections))
    print("Junctions:", len(junctions))

    # --------------------------------------------------
    # 1. Build existing junction lookup and spatial index
    # --------------------------------------------------

    junction_geoms = junctions.geometry.to_numpy()
    junction_ids = junctions["node_id"].to_numpy()

    junction_lookup = {
        (geom.x, geom.y): int(node_id)
        for geom, node_id in zip(junction_geoms, junction_ids)
    }

    junction_tree = STRtree(junction_geoms)

    # --------------------------------------------------
    # 2. Collect split positions for each component
    # --------------------------------------------------

    print("Preparing intersection split positions...")

    split_map = defaultdict(list)

    for row in intersections.itertuples(index=False):

        point = row.geometry
        key = (point.x, point.y)

        if key not in junction_lookup:
            raise ValueError(
                f"Intersection has no junction ID: {key}"
            )

        node_id = junction_lookup[key]

        split_map[int(row.component_a)].append(
            (point, node_id)
        )

        split_map[int(row.component_b)].append(
            (point, node_id)
        )

    # --------------------------------------------------
    # 3. Assign synthetic endpoint node IDs
    # --------------------------------------------------

    next_node_id = int(junctions["node_id"].max()) + 1

    synthetic_lookup = {}
    synthetic_records = []

    def endpoint_node(component_id, side, xy, is_loop):

        nonlocal next_node_id

        point = Point(xy)

        candidates = junction_tree.query(
            point.buffer(MATCH_TOLERANCE)
        )

        matches = [
            int(i)
            for i in candidates
            if point.distance(junction_geoms[int(i)])
            <= MATCH_TOLERANCE
        ]

        if len(matches) > 1:
            raise ValueError(
                f"Endpoint matches multiple junctions: "
                f"component={component_id}, side={side}"
            )

        if len(matches) == 1:
            return int(junction_ids[matches[0]])

        # Closed loops receive one shared synthetic node.
        # Other endpoints receive separate nodes.
        key = (
            ("loop", component_id)
            if is_loop
            else ("endpoint", component_id, side)
        )

        if key not in synthetic_lookup:

            node_id = next_node_id
            next_node_id += 1

            synthetic_lookup[key] = node_id

            synthetic_records.append({
                "node_id": node_id,
                "node_type": "synthetic_endpoint",
                "geometry": point
            })

        return synthetic_lookup[key]

    # --------------------------------------------------
    # 4. Prepare chunked segment writing
    # --------------------------------------------------

    segment_buffer = []

    segment_id = 1
    total_segments = 0
    total_length = 0.0
    source_length = 0.0

    layer_created = False

    def write_segment_chunk():

        nonlocal layer_created, total_segments

        if not segment_buffer:
            return

        frame = gpd.GeoDataFrame(
            segment_buffer,
            geometry="geometry",
            crs=roads.crs
        )

        pyogrio.write_dataframe(
            frame,
            OUTPUT_FILE,
            layer="road_segments",
            driver="GPKG",
            append=layer_created
        )

        total_segments += len(frame)
        layer_created = True

        segment_buffer.clear()

        print("Written segments:", total_segments)

    # --------------------------------------------------
    # 5. Split every component into road segments
    # --------------------------------------------------

    print("\nBuilding road segments...")

    for row in roads.itertuples(index=False):

        geom = row.geometry
        component_id = int(row.component_id)

        if geom is None or geom.is_empty:
            raise ValueError(
                f"Empty geometry: component={component_id}"
            )

        source_length += float(geom.length)

        coords = geom.coords

        start_xy = coords[0][:2]
        end_xy = coords[-1][:2]

        is_loop = start_xy == end_xy

        start_node = endpoint_node(
            component_id,
            "start",
            start_xy,
            is_loop
        )

        if is_loop:

            end_node = start_node

        else:

            end_node = endpoint_node(
                component_id,
                "end",
                end_xy,
                is_loop
            )

        positions = [
            (0.0, start_node),
            (float(geom.length), end_node)
        ]

        for point, node_id in split_map.get(
            component_id, []
        ):

            distance = float(geom.project(point))

            positions.append(
                (distance, int(node_id))
            )

        positions.sort(key=lambda item: item[0])

        # Merge duplicate positions and check node consistency.
        unique_positions = []

        for distance, node_id in positions:

            if unique_positions and abs(
                distance - unique_positions[-1][0]
            ) <= POSITION_TOLERANCE:

                if node_id != unique_positions[-1][1]:

                    raise ValueError(
                        f"Conflicting nodes at same position: "
                        f"component={component_id}"
                    )

            else:

                unique_positions.append(
                    (distance, node_id)
                )

        if unique_positions[0][1] != start_node:
            raise ValueError(
                f"Start node mismatch: component={component_id}"
            )

        if unique_positions[-1][1] != end_node:
            raise ValueError(
                f"End node mismatch: component={component_id}"
            )

        # Generate individual segments.
        for (d1, node_a), (d2, node_b) in zip(
            unique_positions[:-1],
            unique_positions[1:]
        ):

            if d2 - d1 <= POSITION_TOLERANCE:
                continue

            segment_geom = substring(
                geom,
                d1,
                d2
            )

            if (
                segment_geom.is_empty
                or segment_geom.geom_type != "LineString"
            ):

                raise ValueError(
                    f"Invalid segment: component={component_id}"
                )

            length_m = float(segment_geom.length)

            if length_m <= 0:
                raise ValueError(
                    f"Zero-length segment: component={component_id}"
                )

            segment_buffer.append({

                "segment_id": segment_id,
                "component_id": component_id,

                # Original OSM attributes.
                "osm_id": row.osm_id,
                "code": row.code,
                "fclass": row.fclass,
                "name": row.name,
                "ref": row.ref,
                "oneway": row.oneway,
                "maxspeed": row.maxspeed,
                "layer": row.layer,
                "bridge": row.bridge,
                "tunnel": row.tunnel,

                # Network attributes.
                "from_node": node_a,
                "to_node": node_b,
                "length_m": length_m,

                "geometry": segment_geom
            })

            segment_id += 1
            total_length += length_m

            if len(segment_buffer) >= CHUNK_SIZE:
                write_segment_chunk()

    write_segment_chunk()

    # --------------------------------------------------
    # 6. Check total geometry length preservation
    # --------------------------------------------------

    length_difference = abs(
        source_length - total_length
    )

    print("\nLength validation:")
    print("Original length (m):", source_length)
    print("Segment length (m):", total_length)
    print("Difference (m):", length_difference)

    if length_difference > max(
        0.01,
        source_length * 1e-9
    ):

        raise ValueError(
            "Segment length does not match original component length."
        )

    # --------------------------------------------------
    # 7. Write network node layer
    # --------------------------------------------------

    print("\nWriting network nodes...")

    node_frame = junctions[
        ["node_id", "geometry"]
    ].copy()

    node_frame["node_type"] = "candidate_junction"

    node_frame = node_frame[
        ["node_id", "node_type", "geometry"]
    ]

    # append=True adds a new layer to the existing GeoPackage.
    # It does not overwrite the road_segments layer.
    pyogrio.write_dataframe(
        node_frame,
        OUTPUT_FILE,
        layer="network_nodes",
        driver="GPKG",
        append=True
    )

    # Append synthetic nodes in manageable chunks.
    for start in range(
        0,
        len(synthetic_records),
        CHUNK_SIZE
    ):

        chunk = synthetic_records[
            start:start + CHUNK_SIZE
        ]

        frame = gpd.GeoDataFrame(
            chunk,
            geometry="geometry",
            crs=roads.crs
        )

        pyogrio.write_dataframe(
            frame,
            OUTPUT_FILE,
            layer="network_nodes",
            driver="GPKG",
            append=True
        )

    # --------------------------------------------------
    # 8. Final summary
    # --------------------------------------------------

    print("\n===== BUILD COMPLETE =====")

    print("Output:", OUTPUT_FILE)
    print("Road components:", len(roads))
    print("Road segments:", total_segments)

    print("Existing junction nodes:", len(junctions))
    print("Synthetic endpoint nodes:", len(synthetic_records))

    print(
        "Total network nodes:",
        len(junctions) + len(synthetic_records)
    )

    print(
        "Total segment length (km):",
        round(total_length / 1000, 3)
    )

    print("Length difference (m):", length_difference)


if __name__ == "__main__":
    main()
