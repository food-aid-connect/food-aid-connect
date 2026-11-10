from datetime import date, time, timedelta
from decimal import Decimal

import pytest

from app import Batch


FIELDS = {'category', 'quantity_kg', 'use_by_date', 'pickup_address', 'pickup_start', 'pickup_end'}


def form_data(**overrides):
    data = {'title': 'Seasonal apples', 'quantity': '3 crates',
            'pickup_date': date.today().isoformat(), 'category': 'Fruit',
            'quantity_kg': '12.500', 'use_by_date': (date.today() + timedelta(days=2)).isoformat(),
            'pickup_address': '12 Rue de Rivoli, Paris', 'pickup_start': '09:00', 'pickup_end': '11:30'}
    data.update(overrides)
    return data


def test_details_stored_and_listed(client, donor, database):
    response = client.post('/batches/new', data=form_data())
    assert response.status_code == 302
    batch = Batch.query.one()
    assert batch.category == 'Fruit'
    assert batch.quantity_kg == Decimal('12.500')
    assert batch.use_by_date == date.today() + timedelta(days=2)
    assert batch.pickup_address == '12 Rue de Rivoli, Paris'
    assert batch.pickup_start == time(9)
    assert batch.pickup_end == time(11, 30)
    payload = client.get('/api/batches').get_json()[0]
    assert FIELDS <= payload.keys()
    assert payload['category'] == 'Fruit'
    assert payload['quantity_kg'] == 12.5
    assert payload['use_by_date'] == batch.use_by_date.isoformat()
    assert payload['pickup_address'] == batch.pickup_address
    assert payload['pickup_start'] == '09:00:00'
    assert payload['pickup_end'] == '11:30:00'


def test_past_use_by_rejected(client, donor):
    response = client.post('/batches/new', data=form_data(use_by_date=(date.today() - timedelta(days=1)).isoformat()))
    assert response.status_code == 400
    assert b'Use-by date cannot be earlier than today.' in response.data
    assert Batch.query.count() == 0


@pytest.mark.parametrize('days', [0, 1])
def test_today_or_future_accepted(client, donor, days):
    value = (date.today() + timedelta(days=days)).isoformat()
    assert client.post('/batches/new', data=form_data(use_by_date=value)).status_code == 302
    assert Batch.query.one().use_by_date.isoformat() == value


@pytest.mark.parametrize('changes', [
    {'use_by_date': 'not-a-date'}, {'quantity_kg': '-1'}, {'quantity_kg': 'NaN'},
    {'quantity_kg': '10000000'}, {'pickup_end': '08:00'}, {'pickup_start': 'wrong'},
    {'pickup_start': '09:00:00+02:00'}, {'category': 'x' * 81}])
def test_invalid_details_rejected(client, donor, changes):
    assert client.post('/batches/new', data=form_data(**changes)).status_code == 400
    assert Batch.query.count() == 0


def test_legacy_creation_and_filtering(client, donor, database):
    legacy = {'title': 'Bread', 'quantity': '10 loaves', 'pickup_date': '2026-11-12'}
    assert client.post('/batches/new', data=legacy).status_code == 302
    batch = Batch.query.one()
    assert all(getattr(batch, name) is None for name in FIELDS)
    available = client.get('/api/batches?status=available').get_json()
    assert len(available) == 1
    assert all(available[0][name] is None for name in FIELDS)
    batch.status = 'reserved'
    database.session.commit()
    assert client.get('/api/batches?status=available').get_json() == []
    assert len(client.get('/api/batches?status=reserved').get_json()) == 1
    assert client.get('/api/batches?status=invalid').status_code == 422


def test_documentation_and_form(client, donor):
    spec = client.get('/openapi.json').get_json()
    schemas = spec['components']['schemas']
    output_ref = spec['paths']['/api/batches']['get']['responses']['200']['content']['application/json']['schema']['items']['$ref']
    input_ref = spec['paths']['/batches/new']['post']['requestBody']['content']['application/x-www-form-urlencoded']['schema']['$ref']
    output = schemas[output_ref.rsplit('/', 1)[-1]]['properties']
    input_fields = schemas[input_ref.rsplit('/', 1)[-1]]['properties']
    for properties in (output, input_fields):
        assert FIELDS <= properties.keys()
        assert 'number' in properties['quantity_kg']['type']
        assert properties['use_by_date']['format'] == 'date'
        assert properties['pickup_start']['format'] == 'time'
        assert properties['pickup_end']['format'] == 'time'
    operation = spec['paths']['/batches/new']['post']
    assert '400' in operation['responses']
    assert 'requestBody' in operation
    assert client.get('/docs').status_code == 200
    html = client.get('/batches/new').get_data(as_text=True)
    for name in FIELDS:
        assert f'name="{name}"' in html


def test_registration_login_and_batch_authorization(client):
    assert client.get('/batches/new').status_code == 302
    for role in ('donor', 'charity'):
        email = f'{role}@example.org'
        assert client.post('/register', data={'email': email, 'password': 'test123', 'role': role}).status_code == 302
        assert client.post('/login', data={'email': email, 'password': 'test123'}).status_code == 302
        with client.session_transaction() as session:
            assert session['role'] == role
        response = client.post('/batches/new', data=form_data())
        assert response.status_code == 302
        client.get('/logout')
    assert Batch.query.count() == 1
