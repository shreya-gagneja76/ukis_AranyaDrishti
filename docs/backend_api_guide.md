# AranyaDrishti — Backend API Guide

## 1. Overview

The AranyaDrishti backend is built using FastAPI.

It provides district-level environmental context, land-cover information, district rankings and combined district overview data for Uttarakhand.

**Application entry point:** `backend/main.py`

**Base URL (local development):**

`http://127.0.0.1:8000`

All endpoints described here use HTTP GET requests.

## 2. Available Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | API health message |
| GET | `/environmental-context/` | Retrieve environmental context for all districts |
| GET | `/environmental-context/{district_lgd}` | Retrieve environmental context for one district |
| GET | `/environmental-context/rank` | Rank districts using an environmental metric |
| GET | `/land-cover/` | Retrieve land-cover data for all districts |
| GET | `/land-cover/{district_lgd}` | Retrieve land-cover data for one district |
| GET | `/district-overview/{district_lgd}` | Retrieve combined district information |

District identifiers use three-character LGD codes represented as strings. For example, Chamoli uses `057`.

## 3. Root Endpoint

### GET `/`

Checks whether the backend is responding.

**Example request:**

`GET http://127.0.0.1:8000/`

**Successful response — 200 OK:**

```json
{
  "message": "AranyaDrishti API is running"
}
```

## 4. Environmental Context API

### GET `/environmental-context/`

Returns environmental-context records for all 13 districts.

**Example request:**

`GET /environmental-context/`

**Response:** JSON array containing district environmental-context records.

### GET `/environmental-context/{district_lgd}`

Returns environmental context for a specific district.

**Example request:**

`GET /environmental-context/057`

**Successful response:** A JSON object containing the environmental attributes for the requested district.

The response includes fields such as:

- `DISTRICT_NAME`
- `Tree_Cover_Percent`
- `Elevation_Mean_m`
- `Slope_Mean_deg`
- `Steep_Terrain_Above_30deg_pct`

The complete set of returned attributes is determined by the environmental-context CSV.

**Unknown district — 404 Not Found:**

```json
{
  "detail": "No environmental context found for district LGD code: 999"
}
```

## 5. Environmental Ranking API

### GET `/environmental-context/rank`

Ranks districts using a supported environmental metric.

**Query parameters:**

| Parameter | Required | Default | Description |
|---|---|---|---|
| `metric` | Yes | — | Environmental metric used for ranking |
| `order` | No | `desc` | Ranking order: `asc` or `desc` |
| `limit` | No | `5` | Number of districts to return; range 1–13 |

**Example request:**

`GET /environmental-context/rank?metric=Tree_Cover_Percent&order=desc&limit=5`

**Successful response:** JSON array containing ranked district records, including:

- `DIST_LGD`
- `DISTRICT_NAME`
- The requested metric

The records are sorted according to the requested order.

### Supported ranking metrics

The following metric names are accepted:

| Metric |
|---|
| `Tree_Cover_Percent` |
| `Elevation_Mean_m` |
| `Slope_Mean_deg` |
| `Steep_Terrain_Above_30deg_pct` |
| `LC_Percent_of_District_Tree_cover` |
| `LC_Percent_of_District_Cropland` |
| `LC_Percent_of_District_Shrubland` |
| `LC_Percent_of_District_Grassland` |
| `LC_Percent_of_District_Built-up` |

**Unsupported metric — 400 Bad Request:**

```json
{
  "detail": "Unsupported ranking metric: Invalid_Metric"
}
```

The `order` parameter accepts `asc` or `desc`. The endpoint also validates the limit range.

## 6. Land-Cover API

### GET `/land-cover/`

Returns land-cover composition for all 13 districts.

**Example request:**

`GET /land-cover/`

**Response:** JSON array containing district objects. Each district object includes its LGD identifier, district name and land-cover records.

### GET `/land-cover/{district_lgd}`

Returns land-cover composition for one district.

**Example request:**

`GET /land-cover/057`

**Successful response structure:**

```json
{
  "DIST_LGD": "057",
  "District": "CHAMOLI",
  "land_cover": [
    {
      "Class_Code": 0,
      "Land_Cover": "class name",
      "Pixel_Count": 0,
      "Area_km2": 0.0,
      "Percent_of_District": 0.0
    }
  ]
}
```

The values shown above are illustrative placeholders, not actual Chamoli measurements.

Each land-cover record contains:

| Field | Description |
|---|---|
| `Class_Code` | WorldCover class code |
| `Land_Cover` | Land-cover class name |
| `Pixel_Count` | Number of pixels |
| `Area_km2` | Area in square kilometres |
| `Percent_of_District` | Percentage of district area |

The current dataset contains 11 land-cover records per district.

The backend validates that class percentages sum to approximately 100% for each district.

**Unknown district:** Returns `404 Not Found`.

## 7. District Overview API

### GET `/district-overview/{district_lgd}`

Returns combined environmental-context and land-cover information for a district.

This endpoint is useful for frontend district detail pages because both datasets are available through a single request.

**Example request:**

`GET /district-overview/057`

**Successful response structure:**

```json
{
  "DIST_LGD": "057",
  "DISTRICT_NAME": "CHAMOLI",
  "environmental_context": {
    "DISTRICT_NAME": "CHAMOLI"
  },
  "land_cover": [
    {
      "Class_Code": 0,
      "Land_Cover": "class name",
      "Pixel_Count": 0,
      "Area_km2": 0.0,
      "Percent_of_District": 0.0
    }
  ]
}
```

The example demonstrates the response structure; placeholder values are not actual dataset measurements.

**Unknown district:** Returns `404 Not Found`.

## 8. Error Handling

| HTTP status | Meaning |
|---|---|
| 200 | Request successful |
| 400 | Invalid or unsupported ranking metric |
| 404 | Requested district or district overview not found |

Frontend code should check the HTTP status before attempting to display response data.

## 9. Running the Backend Locally

Run commands from the project root.

Activate the virtual environment:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install the pinned dependencies if necessary:

```powershell
python -m pip install -r requirements.txt
```

Start the development server:

```powershell
python -m uvicorn backend.main:app --reload
```

The backend will be available at:

`http://127.0.0.1:8000`

FastAPI interactive documentation:

`http://127.0.0.1:8000/docs`

OpenAPI schema:

`http://127.0.0.1:8000/openapi.json`

## 10. Frontend Integration Guidance

For frontend development:

1. Use the three-character district LGD code when requesting a district-specific endpoint.
2. Use `/district-overview/{district_lgd}` when a page needs both environmental and land-cover information.
3. Use `/environmental-context/rank` for district ranking features.
4. Use `/land-cover/` when district-wide land-cover records are needed.
5. Handle HTTP 404 responses for invalid or unavailable district codes.
6. Avoid hardcoding environmental measurements or land-cover percentages when the API can provide them.

The API currently provides district-level tabular data. It does not expose a completed route-finding or navigation endpoint.

## 11. Backend Tests

The project contains three test files under `tests/`:

| Test file | Coverage |
|---|---|
| `test_environmental_context.py` | Root endpoint, district retrieval, all-district retrieval, ranking and invalid metrics |
| `test_land_cover.py` | District land-cover retrieval, all-district retrieval, percentage totals and unknown districts |
| `test_district_overview.py` | District overview retrieval, all 13 districts and unknown districts |

The existing test suite contains 12 test cases.

Run the tests from the project root:

```powershell
python -m pytest -q
```

## 12. Implementation Notes

- Environmental-context data is loaded from `data/processed/district_environmental_context_2021.csv`.
- Land-cover data is loaded from `data/processed/forest_cover/esa_worldcover_2021_v200/district_land_cover_composition_2021.csv`.
- District identifiers are handled as strings and normalized to three characters.
- The district overview service combines environmental-context and land-cover services.
- API responses are generated from the processed datasets.

For dataset definitions and metadata, refer to `data_dictionary.md`.

For frontend responsibilities, integration considerations and known limitations, refer to `integration_notes.md`.
