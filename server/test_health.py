def test_health_returns_ok_without_database_access(client):
    response = client.get("/api/health/")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
