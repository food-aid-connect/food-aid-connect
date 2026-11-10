from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest

from app import app, db, Batch


def reserve_url(records):
    return f'/api/batches/{records["batch"]}/reserve'


def test_successful_reservation_updates_batch(client, records, sign_in):
    sign_in(client, records["charity"])
    response = client.post(reserve_url(records))
    assert response.status_code == 200
    assert response.json == {
        "message": "Batch reserved successfully", "batch_id": records["batch"],
        "status": "reserved", "charity_id": records["charity"]
    }
    with app.app_context():
        batch = db.session.get(Batch, records["batch"])
        assert batch.status == "reserved"
        assert batch.charity_id == records["charity"]


@pytest.mark.parametrize("user, status", [(None, 401), ("donor", 403)])
def test_access_restrictions(client, records, sign_in, user, status):
    if user:
        sign_in(client, records[user], user)
    assert client.post(reserve_url(records)).status_code == status
    with app.app_context():
        batch = db.session.get(Batch, records["batch"])
        assert batch.status == "available"
        assert batch.charity_id is None


def test_unknown_batch(client, records, sign_in):
    sign_in(client, records["charity"])
    assert client.post('/api/batches/999999/reserve').status_code == 404


def test_already_reserved_batch(client, records, sign_in):
    with app.app_context():
        batch = db.session.get(Batch, records["batch"])
        batch.status = "reserved"
        batch.charity_id = records["other"]
        db.session.commit()
    sign_in(client, records["charity"])
    response = client.post(reserve_url(records))
    assert response.status_code == 409
    assert response.json["message"] == "This batch is already reserved"
    with app.app_context():
        assert db.session.get(Batch, records["batch"]).charity_id == records["other"]


def test_second_charity_cannot_reserve(client, records, sign_in):
    sign_in(client, records["charity"])
    assert client.post(reserve_url(records)).status_code == 200
    sign_in(client, records["other"])
    assert client.post(reserve_url(records)).status_code == 409
    with app.app_context():
        assert db.session.get(Batch, records["batch"]).charity_id == records["charity"]


def test_concurrent_reservations_have_one_winner(records, sign_in):
    barrier = Barrier(2)

    def attempt(user_id):
        with app.test_client() as client:
            sign_in(client, user_id)
            barrier.wait(timeout=10)
            return user_id, client.post(reserve_url(records)).status_code

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(attempt, [records["charity"], records["other"]]))
    assert sorted(status for _, status in results) == [200, 409]
    winner = next(user_id for user_id, status in results if status == 200)
    with app.app_context():
        batch = db.session.get(Batch, records["batch"])
        assert batch.status == "reserved"
        assert batch.charity_id == winner


@pytest.mark.parametrize("role", ["charity", "donor", None])
def test_reserve_button_visibility(client, records, sign_in, role):
    if role:
        sign_in(client, records[role], role)
    response = client.get('/batches')
    assert response.status_code == 200
    assert b'Fresh bread' in response.data
    assert b'10 loaves' in response.data
    assert (b'>Reserve</button>' in response.data) == (role == "charity")


def test_reserved_batches_are_hidden(client, records, sign_in):
    sign_in(client, records["charity"])
    client.post(reserve_url(records))
    response = client.get('/batches')
    assert b'Fresh bread' not in response.data
    assert b'No food batches are currently available.' in response.data


def test_deleted_user_is_unauthenticated(client, records, sign_in):
    sign_in(client, 999999)
    assert client.post(reserve_url(records)).status_code == 401
    assert b'>Reserve</button>' not in client.get('/batches').data


def test_openapi_documents_reservation(client):
    response = client.get('/openapi.json')
    assert response.status_code == 200
    operation = response.json['paths']['/api/batches/{batch_id}/reserve']['post']
    assert {'200', '401', '403', '404', '409'} <= operation['responses'].keys()
    assert operation['responses']['409']['description'] == 'This batch is already reserved'
    assert operation['parameters'][0]['name'] == 'batch_id'
    assert client.get('/docs').status_code == 200


def test_existing_account_and_batch_flow(client):
    response = client.post('/register', data={
        'email': 'new-donor@example.org', 'password': 'test-password', 'role': 'donor'
    })
    assert response.status_code == 302
    assert response.location.endswith('/login')
    response = client.post('/login', data={
        'email': 'new-donor@example.org', 'password': 'test-password'
    })
    assert response.status_code == 302
    with client.session_transaction() as session:
        donor_id = session['user_id']
        assert session['role'] == 'donor'
    response = client.post('/batches/new', data={
        'title': 'Vegetables', 'quantity': '5 kg', 'pickup_date': '2026-11-11'
    })
    assert response.status_code == 302
    with app.app_context():
        batch = Batch.query.one()
        assert batch.donor_id == donor_id
        assert batch.status == 'available'
        assert batch.charity_id is None
    assert b'Vegetables' in client.get('/batches').data
    assert client.get('/logout').status_code == 302
    with client.session_transaction() as session:
        assert 'user_id' not in session


def test_charity_still_cannot_create_batches(client, records, sign_in):
    sign_in(client, records['charity'])
    response = client.post('/batches/new', data={
        'title': 'Forbidden', 'quantity': '5 kg', 'pickup_date': '2026-11-11'
    })
    assert response.status_code == 302
    with app.app_context():
        assert Batch.query.count() == 1
