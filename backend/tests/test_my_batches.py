import pytest

from app import app, Batch, db, User


@pytest.fixture
def batch_ids(records):
    with app.app_context():
        other_donor = User(email="other-donor@example.org", password_hash="unused", role="donor")
        db.session.add(other_donor)
        db.session.flush()

        mine_reserved = Batch(
            title="Apples", quantity="2 crates", pickup_date="2026-11-11",
            donor_id=records["donor"], charity_id=records["other"], status="reserved",
        )
        other_reserved = Batch(
            title="Potatoes", quantity="1 crate", pickup_date="2026-11-11",
            donor_id=other_donor.id, charity_id=records["charity"], status="reserved",
        )
        db.session.add_all([mine_reserved, other_reserved])
        db.session.flush()
        ids = {"mine_reserved": mine_reserved.id, "other_reserved": other_reserved.id}
        db.session.commit()
        return ids


def test_donor_sees_own_batches_in_all_statuses(client, records, batch_ids, sign_in):
    sign_in(client, records["donor"], "donor")

    response = client.get("/api/me/batches")

    assert response.status_code == 200
    assert [(batch["id"], batch["status"]) for batch in response.get_json()] == [
        (records["batch"], "available"),
        (batch_ids["mine_reserved"], "reserved"),
    ]


def test_charity_sees_only_batches_it_reserved(client, records, batch_ids, sign_in):
    sign_in(client, records["charity"])

    response = client.get("/api/me/reservations")

    assert response.status_code == 200
    assert [(batch["id"], batch["charity_id"]) for batch in response.get_json()] == [
        (batch_ids["other_reserved"], records["charity"]),
    ]


@pytest.mark.parametrize("path, allowed_role, wrong_role", [
    ("/api/me/batches", "donor", "charity"),
    ("/api/me/reservations", "charity", "donor"),
])
def test_requires_login_and_uses_database_role(client, records, sign_in, path, allowed_role, wrong_role):
    assert client.get(path).status_code == 401

    sign_in(client, records[wrong_role], allowed_role)
    assert client.get(path).status_code == 403


@pytest.mark.parametrize("path, role", [
    ("/api/me/batches", "donor"),
    ("/api/me/reservations", "charity"),
])
def test_empty_collection_returns_an_array(client, sign_in, path, role):
    with app.app_context():
        user = User(email="empty@example.org", password_hash="unused", role=role)
        db.session.add(user)
        db.session.commit()
        user_id = user.id
    sign_in(client, user_id, role)

    response = client.get(path)

    assert response.status_code == 200
    assert response.get_json() == []


@pytest.mark.parametrize("path", ["/api/me/batches", "/api/me/reservations"])
def test_my_batch_collections_are_documented(client, path):
    response = client.get("/openapi.json")

    assert response.status_code == 200
    paths = response.get_json()["paths"]
    operation = paths[path]["get"]
    assert "Batches" in operation["tags"]
    assert {"200", "401", "403"} <= operation["responses"].keys()
    schema = operation["responses"]["200"]["content"]["application/json"]["schema"]
    assert schema["type"] == "array"
    assert schema == paths["/api/batches"]["get"]["responses"]["200"]["content"]["application/json"]["schema"]
