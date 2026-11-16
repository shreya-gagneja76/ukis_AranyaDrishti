
from fastapi.testclient import TestClient

from backend.main import app


client = TestClient(app)


def test_chamoli_land_cover():
    response = client.get("/land-cover/057")

    assert response.status_code == 200

    data = response.json()

    assert data["DIST_LGD"] == "057"
    assert data["District"] == "CHAMOLI"
    assert len(data["land_cover"]) == 11

    total_percentage = sum(
        item["Percent_of_District"]
        for item in data["land_cover"]
    )

    assert abs(total_percentage - 100) < 0.01


def test_all_districts_land_cover():
    response = client.get("/land-cover/")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 13

    for district in data:
        assert len(district["land_cover"]) == 11


def test_unknown_district_land_cover():
    response = client.get("/land-cover/999")

    assert response.status_code == 404
