
from fastapi.testclient import TestClient

from backend.main import app


client = TestClient(app)


def test_chamoli_district_overview():
    response = client.get("/district-overview/057")

    assert response.status_code == 200

    data = response.json()

    assert data["DIST_LGD"] == "057"
    assert data["DISTRICT_NAME"] == "CHAMOLI"
    assert len(data["environmental_context"]) == 58
    assert len(data["land_cover"]) == 11


def test_all_districts_have_overview():
    district_codes = [
        "056", "057", "058", "059", "060",
        "061", "062", "063", "064", "065",
        "066", "067", "068"
    ]

    for code in district_codes:
        response = client.get(f"/district-overview/{code}")

        assert response.status_code == 200
        assert response.json()["DIST_LGD"] == code


def test_unknown_district_overview():
    response = client.get("/district-overview/999")

    assert response.status_code == 404
