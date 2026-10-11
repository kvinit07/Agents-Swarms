from fastapi.testclient import TestClient
import app as app_module

client = TestClient(app_module.app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_investigate_rejects_short_incident():
    response = client.post(
        "/investigate",
        json={
            "incident": "bad",
            "logs": "some log evidence",
            "deployments": "some deployment evidence",
        },
    )
    assert response.status_code == 422
