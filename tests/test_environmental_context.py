
import pytest
from fastapi.testclient import TestClient

from backend.main import app


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_root_endpoint(client):
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["message"] == "AranyaDrishti API is running"


def test_get_all_districts(client):
    response = client.get("/environmental-context/")

    assert response.status_code == 200

    districts = response.json()

    assert len(districts) == 13
    assert all("DISTRICT_NAME" in district for district in districts)


def test_get_chamoli_context(client):
    response = client.get("/environmental-context/057")

    assert response.status_code == 200

    data = response.json()

    assert data["DISTRICT_NAME"] == "CHAMOLI"
    assert data["Elevation_Mean_m"] > 0
    assert data["Slope_Mean_deg"] > 0
    assert data["Tree_Cover_Percent"] > 0


def test_unknown_district_returns_404(client):
    response = client.get("/environmental-context/999")

    assert response.status_code == 404

    assert response.json() == {
        "detail": (
            "No environmental context found "
            "for district LGD code: 999"
        )
    }


def test_rank_districts_by_tree_cover(client):
    response = client.get(
        "/environmental-context/rank",
        params={
            "metric": "Tree_Cover_Percent",
            "order": "desc",
            "limit": 5
        }
    )

    assert response.status_code == 200

    results = response.json()

    assert len(results) == 5
    assert all("DIST_LGD" in item for item in results)
    assert all("DISTRICT_NAME" in item for item in results)
    assert all("Tree_Cover_Percent" in item for item in results)

    values = [
        item["Tree_Cover_Percent"]
        for item in results
    ]

    assert values == sorted(values, reverse=True)


def test_rank_districts_invalid_metric(client):
    response = client.get(
        "/environmental-context/rank",
        params={
            "metric": "Invalid_Metric",
            "order": "desc",
            "limit": 5
        }
    )

    assert response.status_code == 400

    assert response.json() == {
        "detail": "Unsupported ranking metric: Invalid_Metric"
    }
