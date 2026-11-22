from datetime import date, timedelta

# TESTS BATCHES: CREATE-READ-UPDATE-DELETE

# Note to self: the message in response should always be the same we wrote in the corresponding route


# GET TESTS ------------------------------------------------------------------------------------------------------

# TEST GET 200
# 200 OK: The request was successful, and the response contains what was requested
# Here, the batch was found and returned
def test_get_batch_returns_200(client, records):
    # Send the request to the address of the batch created by "records"
    response = client.get(f"/api/batches/{records['batch']}")

    assert response.status_code == 200

    # get_json() turns the answer into a Python dictionary
    data = response.get_json()
    assert data["id"] == records["batch"]
    assert data["title"] == "Fresh bread"


# TEST GET 404
# 404 Not Found: The requested item does not exist.
# Here, there is no batch number 999
def test_get_missing_batch_returns_404(client):
    # Send the request to the address of the missing batch (999)
    response = client.get("/api/batches/999")

    assert response.status_code == 404

    # get_json() turns the answer into a Python dictionary
    assert response.get_json()["message"] == "Batch not found"


# POST TESTS ------------------------------------------------------------------------------------------------------

# Function that creates the small json file for creating a valid batch
# As it is reused in many tests
def valid_batch_json():
    # Dates are computed from today, so the tests do not break as time passes
    # (Rule : use date limited to the present day)
    return {
        "title": "Test bread",
        "quantity": "5 loaves",
        "pickup_date": date.today().isoformat(),
        "quantity_kg": 2.5,
        "use_by_date": (date.today() + timedelta(days=1)).isoformat(),
    }


# TEST POST 201
# 201 Created: The resource has been created
# Here, the batch has been created
def test_create_batch_returns_201(client, records, sign_in):
    sign_in(client, records["donor"], role="donor")
    response = client.post("/api/batches", json=valid_batch_json())

    assert response.status_code == 201

    # get_json() turns the answer into a Python dictionary
    data = response.get_json()
    assert data["donor_id"] == records["donor"]
    assert data["status"] == "available"
    assert data["title"] == "Test bread"


# TEST POST 401
# 401 Unauthorized: The user is not logged in
# Here, the donor cannot create a batch without logging in
def test_create_batch_without_login_returns_401(client):
    response = client.post("/api/batches", json=valid_batch_json())

    assert response.status_code == 401

    # get_json() turns the answer into a Python dictionary
    assert response.get_json()["message"] == "Please log in to post a batch"


# TEST POST 403
# 403 Forbidden: The user is connected but doesn't have the rights
# Here, a charity is not allowed to post a batch
def test_create_batch_as_charity_returns_403(client, records, sign_in):
    sign_in(client, records["charity"], role="charity")
    response = client.post("/api/batches", json=valid_batch_json())

    assert response.status_code == 403

    # get_json() turns the answer into a Python dictionary
    assert response.get_json()["message"] == "Only donors can post batches"


# TEST POST 422
# 422 Unprocessable Entity: The data sent is invalid
# Here, the entry has invalid data
def test_create_batch_with_invalid_json_returns_422(client):
    response = client.post("/api/batches", json={})

    # Even though nobody is signed in, the error is 422 and not 401
    # This is because the json is validated by @app.input BEFORE the
    # route function runs, and the login check is inside the function
    assert response.status_code == 422

    # get_json() turns the answer into a Python dictionary
    assert response.get_json()["message"] == "Validation error"


# PUT TESTS ------------------------------------------------------------------------------------------------------

# TEST PUT 200
# 200 OK: The request was successful, and the response contains what was requested
# Here, the batch was updated successfully
def test_update_batch_returns_200(client, records, sign_in):
    sign_in(client, records["donor"], role="donor")
    new_json = valid_batch_json()
    new_json["title"] = "new_title"
    response = client.put(f"/api/batches/{records['batch']}", json=new_json)

    assert response.status_code == 200

    # get_json() turns the answer into a Python dictionary
    data = response.get_json()
    assert data["title"] == "new_title"


# TEST PUT 401
# 401 Unauthorized: The user is not logged in
# Here, the donor cannot update a batch without logging in
def test_update_batch_without_login_returns_401(client, records):
    response = client.put(f"/api/batches/{records['batch']}", json=valid_batch_json())

    assert response.status_code == 401

    # get_json() turns the answer into a Python dictionary
    assert response.get_json()["message"] == "Please log in to update a batch"


# TEST PUT 403
# 403 Forbidden: The user is connected but doesn't have the rights
# Here, a user who did not post the batch is not allowed to update it
def test_update_batch_by_another_user_returns_403(client, records, sign_in):
    sign_in(client, records["other"], role="donor")
    response = client.put(f"/api/batches/{records['batch']}", json=valid_batch_json())

    assert response.status_code == 403

    # get_json() turns the answer into a Python dictionary
    assert response.get_json()["message"] == "Only the donor who posted the batch can update it"


# TEST PUT 404
# 404 Not Found: The requested item does not exist
# Here, a user cannot update a nonexisting batch
def test_update_missing_batch_returns_404(client, records, sign_in):
    sign_in(client, records["donor"], role="donor")
    response = client.put("/api/batches/999", json=valid_batch_json())

    assert response.status_code == 404

    # get_json() turns the answer into a Python dictionary
    assert response.get_json()["message"] == "Batch not found"


# TEST PUT 409
# 409 Conflict: Conflicts with the current state
# Here, the request is valid, but it conflicts with the state of the batch,
# which is already reserved and can no longer be modified
def test_update_reserved_batch_returns_409(client, records, sign_in):
    sign_in(client, records["charity"], role="charity")
    response = client.post(f"/api/batches/{records['batch']}/reserve")

    assert response.status_code == 200

    sign_in(client, records["donor"], role="donor")
    response = client.put(f"/api/batches/{records['batch']}", json=valid_batch_json())

    assert response.status_code == 409

    # get_json() turns the answer into a Python dictionary
    assert response.get_json()["message"] == "The batch must be available"


# DELETE TESTS ------------------------------------------------------------------------------------------------------

# TEST DELETE 204
# 204 No Content: Succeeded, but nothing to return
# Here, the deletion was successful, and there is nothing to return
# Therefore, there is no JSON to verify in this response
def test_delete_batch_returns_204(client, records, sign_in):
    sign_in(client, records["donor"], role="donor")
    response = client.delete(f"/api/batches/{records['batch']}")

    assert response.status_code == 204

    response = client.get(f"/api/batches/{records['batch']}")

    assert response.status_code == 404

    # get_json() turns the answer into a Python dictionary
    assert response.get_json()["message"] == "Batch not found"


# TEST DELETE 401
# 401 Unauthorized: The user is not logged in
# Here, the donor cannot delete a batch without logging in
def test_delete_batch_without_login_returns_401(client, records):
    response = client.delete(f"/api/batches/{records['batch']}")

    assert response.status_code == 401

    # get_json() turns the answer into a Python dictionary
    assert response.get_json()["message"] == "Please log in to delete a batch"


# TEST DELETE 403
# 403 Forbidden: The user is connected but doesn't have the rights
# Here, a user who did not post the batch is not allowed to delete it
def test_delete_batch_by_another_user_returns_403(client, records, sign_in):
    sign_in(client, records["other"], role="donor")
    response = client.delete(f"/api/batches/{records['batch']}")

    assert response.status_code == 403

    # get_json() turns the answer into a Python dictionary
    assert response.get_json()["message"] == "Only the donor who posted the batch can delete it"


# TEST DELETE 404
# 404 Not Found: The requested item does not exist
# Here, a user cannot delete a nonexisting batch
def test_delete_missing_batch_returns_404(client, records, sign_in):
    sign_in(client, records["donor"], role="donor")
    response = client.delete("/api/batches/999")

    assert response.status_code == 404

    # get_json() turns the answer into a Python dictionary
    assert response.get_json()["message"] == "Batch not found"


# TEST DELETE 409
# Here, the request is valid, but it conflicts with the state of the batch,
# which is already reserved and can no longer be deleted
def test_delete_reserved_batch_returns_409(client, records, sign_in):
    sign_in(client, records["charity"], role="charity")
    response = client.post(f"/api/batches/{records['batch']}/reserve")

    assert response.status_code == 200

    sign_in(client, records["donor"], role="donor")
    response = client.delete(f"/api/batches/{records['batch']}")

    assert response.status_code == 409

    # get_json() turns the answer into a Python dictionary
    assert response.get_json()["message"] == "The batch must be available"
