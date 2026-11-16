# AranyaDrishti — Data Dictionary

This document describes the processed GIS datasets currently available in the AranyaDrishti project.

It is intended to help team members understand the available data, its structure, and its potential use during frontend and backend integration.

All paths are relative to the project root.

## 1. District Boundaries

**File:** `data/processed/uttarakhand_districts.gpkg`

- Format: GeoPackage
- Layer: `districts`
- Geometry: MultiPolygon Z
- Features: 13
- CRS: Custom `LCC_WGS84` projected coordinate reference system

| Field | Description |
|---|---|
| `DIST_LGD` | District LGD identifier |
| `DISTRICT_NAME` | District name |

**Purpose:** District boundary geometries for Uttarakhand. Useful for district-level mapping and spatial association.

## 2. Environmental Context

**File:** `data/processed/district_environmental_context_2021.csv`

- Format: CSV
- Records: 13
- Columns: 59
- Coverage: All 13 Uttarakhand districts

This dataset combines district-level environmental attributes, including terrain and land-cover-related measurements.

Important fields used by the backend include:

| Field | Description | Unit |
|---|---|---|
| `DIST_LGD` | District LGD identifier | Identifier |
| `DISTRICT_NAME` | District name | Text |
| `Tree_Cover_Percent` | District tree-cover percentage | Percent |
| `Elevation_Mean_m` | Mean elevation | Metres |
| `Slope_Mean_deg` | Mean slope | Degrees |
| `Steep_Terrain_Above_30deg_pct` | Share of terrain above 30 degrees slope | Percent |
| `LC_Percent_of_District_Tree_cover` | Tree-cover share of district area | Percent |
| `LC_Percent_of_District_Cropland` | Cropland share of district area | Percent |
| `LC_Percent_of_District_Shrubland` | Shrubland share of district area | Percent |
| `LC_Percent_of_District_Grassland` | Grassland share of district area | Percent |
| `LC_Percent_of_District_Built-up` | Built-up share of district area | Percent |

The dataset contains additional fields beyond those listed above. Refer to the CSV header for the complete schema.

**Purpose:** Supplies district-level environmental indicators to the environmental-context and district-overview APIs.

## 3. Land-Cover Composition

**File:** `data/processed/forest_cover/esa_worldcover_2021_v200/district_land_cover_composition_2021.csv`

- Format: CSV
- Records: 143
- Columns: 7
- District coverage: 13
- Records per district: 11

| Field | Description |
|---|---|
| `DIST_LGD` | District LGD identifier |
| `District` | District name |
| `Class_Code` | ESA WorldCover class code |
| `Land_Cover` | Land-cover class name |
| `Pixel_Count` | Number of pixels belonging to the class |
| `Area_km2` | Area occupied by the class |
| `Percent_of_District` | Percentage of district area occupied by the class |

The class percentages are validated to total approximately 100% for each district.

**Purpose:** Provides district-level land-cover composition for charts, summaries and land-cover API responses.

## 4. District Tree-Cover Statistics

**File:** `data/processed/forest_cover/esa_worldcover_2021_v200/district_tree_cover_2021_v2.csv`

- Format: CSV
- Records: 13
- Columns: 7

This dataset contains district-level tree-cover statistics derived from the processed WorldCover data.

The corresponding spatial dataset is:

**File:** `data/processed/forest_cover/esa_worldcover_2021_v200/uttarakhand_district_forest_cover_2021.gpkg`

- Layer: `district_forest_cover`
- Geometry: MultiPolygon Z
- Features: 13
- CRS: Custom `LCC_WGS84` projected CRS

Spatial dataset fields:

| Field | Description |
|---|---|
| `DIST_LGD` | District LGD identifier |
| `DISTRICT_NAME` | District name |
| `District` | District name |
| `Tree_Cover_Pixels` | Number of tree-cover pixels |
| `Valid_Land_Pixels` | Number of valid land pixels |
| `Tree_Cover_Area_km2` | Tree-cover area |
| `District_Area_km2` | District area |
| `Tree_Cover_Percent` | Tree-cover percentage |

**Purpose:** Supports district-level tree-cover statistics and spatial presentation.

## 5. WorldCover Raster Data

**Source product:** ESA WorldCover 2021, version 200.

### Clipped raster tiles

Directory:

`data/processed/forest_cover/esa_worldcover_2021_v200/`

Available tiles:

- `ESA_WorldCover_10m_2021_v200_N27E075_Map_uttarakhand.tif`
- `ESA_WorldCover_10m_2021_v200_N27E078_Map_uttarakhand.tif`
- `ESA_WorldCover_10m_2021_v200_N30E075_Map_uttarakhand.tif`
- `ESA_WorldCover_10m_2021_v200_N30E078_Map_uttarakhand.tif`
- `ESA_WorldCover_10m_2021_v200_N30E081_Map_uttarakhand.tif`

Raster properties:

- Bands: 1
- Data type: UInt8
- CRS: EPSG:4326
- NoData: 0
- Pixel resolution: approximately 10 metres

### Tree-cover masks

Directory:

`data/processed/forest_cover/esa_worldcover_2021_v200/tree_cover_mask/`

Five corresponding tree-cover mask rasters are available.

Raster properties:

- Bands: 1
- Data type: UInt8
- CRS: EPSG:4326
- NoData: 255

### Tree-cover mosaic

**File:** `data/processed/forest_cover/esa_worldcover_2021_v200/uttarakhand_tree_cover_mosaic_2021.tif`

- Bands: 1
- Data type: UInt8
- CRS: EPSG:4326
- NoData: 255
- Dimensions: 41693 × 32872 pixels

**Purpose:** Raster representation of tree-cover information for spatial analysis and map visualization.

## 6. Terrain Data

### District terrain statistics

**File:** `data/processed/terrain/district_terrain_stats.csv`

- Format: CSV
- Records: 13
- Columns: 21

Contains district-level terrain statistics.

### FABDEM source tiles

Directory:

`data/processed/terrain/FABDEM_v1.2_clipped/`

- 15 clipped raster tiles
- Single band
- Data type: Float32
- CRS: EPSG:4326
- NoData: -9999
- Resolution: approximately 30 metres

### Processed terrain rasters

Directory:

`data/processed/terrain/`

| File | Description | Data type | CRS |
|---|---|---|---|
| `uttarakhand_fabdem_30m_lcc.tif` | Processed elevation raster | Float32 | Custom LCC_WGS84 |
| `uttarakhand_slope_degrees.tif` | Slope raster | Float32 | Custom LCC_WGS84 |
| `uttarakhand_aspect_degrees.tif` | Aspect raster | Float32 | Custom LCC_WGS84 |

Common properties:

- Dimensions: 10987 × 9994 pixels
- Resolution: 30 metres
- NoData: -9999

**Purpose:** Supports terrain analysis and district-level environmental indicators.

## 7. Transport and OpenStreetMap Data

Directory:

`data/processed/transport_osm/`

The following GeoPackages are available:

| File | Layer | Features | Geometry | CRS |
|---|---|---:|---|---|
| `uttarakhand_roads.gpkg` | `uttarakhand_roads` | 132746 | MultiLineString Z | CRS84 |
| `uttarakhand_vehicle_roads.gpkg` | `uttarakhand_vehicle_roads` | 120671 | MultiLineString Z | CRS84 |
| `uttarakhand_foot_roads.gpkg` | `uttarakhand_foot_roads` | 127188 | MultiLineString Z | CRS84 |
| `uttarakhand_roads_review.gpkg` | `uttarakhand_roads_review` | 5489 | MultiLineString Z | CRS84 |
| `uttarakhand_settlements.gpkg` | `uttarakhand_settlements` | 14274 | Point | CRS84 |
| `uttarakhand_vehicle_components.gpkg` | `vehicle_components` | 120908 | LineString Z | Custom LCC_WGS84 |
| `uttarakhand_candidate_junctions.gpkg` | `candidate_junctions` | 139798 | Point | Custom LCC_WGS84 |
| `uttarakhand_candidate_intersections.gpkg` | `candidate_intersections` | 157683 | Point | Custom LCC_WGS84 |

### Common OSM road attributes

The road datasets contain attributes such as:

- `osm_id`
- `code`
- `fclass`
- `name`
- `ref`
- `oneway`
- `maxspeed`
- `layer`
- `bridge`
- `tunnel`

The vehicle-components dataset also contains `component_id`.

The settlements dataset contains:

- `osm_id`
- `code`
- `fclass`
- `population`
- `name`

### Derived vehicle network

**File:** `data/processed/transport_osm/uttarakhand_vehicle_network.gpkg`

This GeoPackage contains two layers:

**Layer: `road_segments`**

- Geometry: LineString Z
- Features: 255767
- CRS: Custom LCC_WGS84

Fields:

`segment_id`, `component_id`, `osm_id`, `code`, `fclass`, `name`, `ref`, `oneway`, `maxspeed`, `layer`, `bridge`, `tunnel`, `from_node`, `to_node`, `length_m`

**Layer: `network_nodes`**

- Geometry: Point
- Features: 227781
- CRS: Custom LCC_WGS84

Fields:

- `node_id`
- `node_type`

**Purpose:** Derived vehicle-network representation for further transport-network analysis and routing development.

**Integration note:** The presence of a prepared vehicle network does not mean a complete routing API or production-ready navigation system is available. Further connectivity and routing validation is still required.

## 8. Coordinate Reference System Notes

The processed datasets use more than one coordinate reference system.

| CRS | Where it appears |
|---|---|
| EPSG:4326 | WorldCover and FABDEM source tiles |
| CRS84 | OpenStreetMap road and settlement datasets |
| Custom LCC_WGS84 | Projected district, terrain and derived network datasets |

The `LCC_WGS84` CRS is a custom projected coordinate reference system. It should not be assumed to be an EPSG code.

Before combining spatial datasets, check their CRS and transform geometries where necessary.

## 9. Data Usage Guidance

For frontend integration:

- Use district identifiers (`DIST_LGD`) to associate district-level records.
- Use district names for labels and display.
- Use the backend API for environmental-context and land-cover responses.
- Use district boundary geometries when district-level map visualization is needed.
- Use raster datasets only in workflows that support raster rendering or raster-derived visualization.
- Treat intermediate transport datasets as processing outputs unless a specific integration requirement is established.

For API response structures and request examples, refer to `backend_api_guide.md`.

For current integration responsibilities and limitations, refer to `integration_notes.md`.

## 10. Data Status

This document describes the processed files and metadata inspected during documentation preparation.

It does not claim that every intermediate dataset is ready for direct frontend consumption. Dataset suitability depends on the intended application feature and the current integration requirements.
