from app import app


def test_list_available_batches_returns_200():
    client = app.test_client()
    response = client.get("/api/batches?status=available")
    assert response.status_code == 200
    assert isinstance(response.get_json(), list)


def test_invalid_status_returns_422():
    client = app.test_client()
    response = client.get("/api/batches?status=abc")
    assert response.status_code == 422
    assert response.get_json()["message"] == "Validation error"