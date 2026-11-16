# AranyaDrishti — Integration Notes

## 1. Purpose

This document describes the current GIS and backend work available for integration into the AranyaDrishti application.

It is intended as a handoff reference for frontend development and later team integration.

The project is being developed in separate areas before the frontend and backend components are brought together.

## 2. Responsibilities

### Member 1 — Frontend

Frontend development and application interface.

Expected integration responsibilities include:

- Displaying district-level information.
- Consuming the available backend API endpoints.
- Presenting environmental and land-cover statistics.
- Integrating district-level map visualizations where suitable GIS data is available.
- Handling loading, empty and error states from API requests.

### Member 2 — GIS and Backend

Current work includes:

- Uttarakhand district boundary preparation.
- Terrain and environmental data processing.
- ESA WorldCover land-cover processing.
- District-level tree-cover analysis.
- OpenStreetMap road and settlement preparation.
- Vehicle-network preprocessing.
- FastAPI backend services.
- API tests and technical documentation.

These responsibilities describe the current work allocation, not a claim that all application integration is finished.

## 3. Backend Integration

### Local API address

During local development, the backend runs at:

`http://127.0.0.1:8000`

Start it from the project root:

```powershell
python -m uvicorn backend.main:app --reload
```

The interactive API documentation is available at:

`http://127.0.0.1:8000/docs`

### Available API endpoints

| Frontend requirement | API endpoint |
|---|---|
| Check backend availability | `GET /` |
| Retrieve environmental context for all districts | `GET /environmental-context/` |
| Retrieve one district's environmental context | `GET /environmental-context/{district_lgd}` |
| Rank districts by an environmental metric | `GET /environmental-context/rank` |
| Retrieve land-cover data for all districts | `GET /land-cover/` |
| Retrieve one district's land-cover data | `GET /land-cover/{district_lgd}` |
| Retrieve combined district information | `GET /district-overview/{district_lgd}` |

For detailed parameters and response structures, refer to `backend_api_guide.md`.

## 4. District Identification

District-level datasets and APIs use the district LGD identifier.

The identifier is represented as a three-character string.

Example:

- District: Chamoli
- LGD code: `057`

Use the same identifier when requesting information from different district-level endpoints.

Do not convert LGD identifiers into numbers, because leading zeroes must be preserved.

The district boundary GeoPackage contains:

- `DIST_LGD`
- `DISTRICT_NAME`

These fields can be used to associate district geometries with API records.

## 5. Recommended Frontend Data Flow

For a district detail view, the combined overview endpoint is the simplest available integration option.

```text
User selects a district
        |
        v
Frontend obtains district LGD code
        |
        v
GET /district-overview/{district_lgd}
        |
        v
Backend combines two data sources
        |
        +--------------------------+
        |                          |
        v                          v
Environmental context         Land-cover records
        |                          |
        +------------+-------------+
                     |
                     v
              JSON response
                     |
                     v
             Frontend presentation
```

For example, selecting Chamoli can trigger:

`GET /district-overview/057`

The response contains:

- `DIST_LGD`
- `DISTRICT_NAME`
- `environmental_context`
- `land_cover`

This allows the frontend to populate a district overview without making separate requests for these two data categories.

## 6. Suggested API Request Pattern

A basic JavaScript example:

```javascript
const API_BASE_URL = "http://127.0.0.1:8000";

async function getDistrictOverview(districtLgd) {
  const response = await fetch(
    `${API_BASE_URL}/district-overview/${districtLgd}`
  );

  if (!response.ok) {
    throw new Error(
      `Failed to retrieve district overview: ${response.status}`
    );
  }

  return await response.json();
}
```

Example usage:

```javascript
const districtData = await getDistrictOverview("057");

console.log(districtData.DISTRICT_NAME);
console.log(districtData.environmental_context);
console.log(districtData.land_cover);
```

This is an illustrative frontend integration example. It assumes the frontend can reach the backend at the configured address.

For deployment or access from another device, the API base URL must be changed to the reachable backend address.

## 7. GIS Data Available for Map Integration

### District boundaries

**File:**

`data/processed/uttarakhand_districts.gpkg`

Contains all 13 district boundary geometries.

The layer is named `districts` and contains:

- `DIST_LGD`
- `DISTRICT_NAME`

This dataset is a potential source for district-level map visualization.

### District forest-cover geometries

**File:**

`data/processed/forest_cover/esa_worldcover_2021_v200/uttarakhand_district_forest_cover_2021.gpkg`

Contains district geometries and associated tree-cover statistics.

### Land-cover and tree-cover rasters

Available raster resources include:

- Clipped ESA WorldCover 2021 tiles.
- Corresponding tree-cover masks.
- Uttarakhand tree-cover mosaic.

These are raster datasets, not ready-made frontend GeoJSON responses.

They require an appropriate raster-serving or conversion workflow before direct use in a browser map.

### Terrain rasters

Available terrain products include:

- Elevation.
- Slope.
- Aspect.

These can support future terrain visualization, subject to suitable raster-serving or preprocessing arrangements.

### Coordinate reference systems

The processed GIS data uses multiple coordinate reference systems:

- EPSG:4326 for WorldCover and FABDEM source tiles.
- CRS84 for OSM road and settlement datasets.
- Custom LCC_WGS84 for projected district and derived datasets.

Transform spatial data to a common CRS before combining it in a map.

The custom LCC_WGS84 CRS should not be treated as an EPSG code without checking its actual CRS definition.

## 8. Transport-Network Integration Status

The project contains several prepared transport datasets:

- Uttarakhand road features.
- Vehicle-road candidate features.
- Foot-road candidate features.
- Settlement points.
- Candidate junctions and intersections.
- Vehicle connected components.
- A derived vehicle network containing road segments and network nodes.

The derived vehicle network contains:

- `road_segments`
- `network_nodes`

The road-segment layer includes `from_node`, `to_node` and `length_m` fields.

### Important limitation

The vehicle network has undergone structural checks and connectivity analysis, but its routing readiness is not yet established.

The current backend does not expose a completed routing or navigation API.

The prepared foot-road dataset is also not a verified pedestrian-routing graph.

Therefore, the frontend should not present turn-by-turn navigation, route distances or travel-time estimates as implemented features based solely on these datasets.

Further network validation and routing implementation are required before such features can be integrated.

## 9. Error and Loading States

Frontend API integration should account for:

- Loading while a request is in progress.
- HTTP 404 when a district is unavailable.
- HTTP 400 when an unsupported ranking metric is requested.
- Network errors when the backend cannot be reached.
- Empty or missing values in displayed data, where applicable.

The frontend should not assume that every API request succeeds.

## 10. Local Development Considerations

The backend dependencies are pinned in the root `requirements.txt`.

Activate the existing virtual environment and run the backend from the project root.

```powershell
.\.venv\Scripts\Activate.ps1

python -m uvicorn backend.main:app --reload
```

The current backend reads processed CSV datasets using paths relative to the project root.

Run the backend from the project root so that these relative data paths resolve correctly.

The local address `127.0.0.1` refers to the same machine. A frontend running on another device cannot use that address to reach the backend machine.

Cross-origin browser requests may also require CORS configuration. The current integration setup should be checked before connecting a separately hosted frontend.

## 11. Current Implementation Status

| Component | Status |
|---|---|
| Uttarakhand district boundaries | Processed |
| District environmental-context dataset | Processed |
| ESA WorldCover land-cover data | Processed |
| District land-cover composition | Processed |
| District tree-cover statistics | Processed |
| Terrain rasters and district statistics | Processed |
| OSM road and settlement datasets | Prepared |
| Vehicle candidate road network | Prepared |
| Derived vehicle network | Structurally checked; further routing validation needed |
| Environmental-context API | Implemented |
| Land-cover API | Implemented |
| District-overview API | Implemented |
| Backend test files | Present; 12 test cases |
| Frontend integration | To be completed jointly |
| Production-ready routing API | Not implemented |

## 12. Related Documentation

- `data_dictionary.md` — Dataset inventory, attributes, formats and CRS information.
- `backend_api_guide.md` — API endpoints, parameters, response structures and testing instructions.
