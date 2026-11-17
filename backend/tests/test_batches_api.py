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


def test_reservation_updates_filtered_batch_lists(client, records, sign_in):
    available = client.get("/api/batches?status=available").get_json()
    assert [batch["id"] for batch in available] == [records["batch"]]
    assert client.get("/api/batches?status=reserved").get_json() == []

    sign_in(client, records["charity"])
    assert client.post(f'/api/batches/{records["batch"]}/reserve').status_code == 200

    assert client.get("/api/batches?status=available").get_json() == []
    reserved = client.get("/api/batches?status=reserved").get_json()
    assert len(reserved) == 1
    assert reserved[0]["id"] == records["batch"]
    assert reserved[0]["charity_id"] == records["charity"]
    assert reserved[0]["status"] == "reserved"


def test_list_and_reservation_documented_together(client):
    spec = client.get("/openapi.json").get_json()
    listing = spec["paths"]["/api/batches"]["get"]
    status = next(parameter for parameter in listing["parameters"] if parameter["name"] == "status")
    assert status["schema"]["default"] == "available"
    assert set(status["schema"]["enum"]) == {"available", "reserved"}
    assert listing["responses"]["200"]["content"]["application/json"]["schema"]["type"] == "array"
    assert "post" in spec["paths"]["/api/batches/{batch_id}/reserve"]
