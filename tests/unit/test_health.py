import httpx2 as httpx

from varne.api.v1.router import ResponseHealth


def test_health_endpoint(client: httpx.Client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200

    data = ResponseHealth.model_validate(response.json())
    assert data.status == "healthy"
    assert data.environment
    assert data.version
