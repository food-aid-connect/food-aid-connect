# TESTS USERS: REGISTER - LOGIN - LOGOUT - CURRENT USER

# Note to self:
# - The message in response should always be the same we wrote in the corresponding route
# - Each test starts from an empty base, except for what is provided by records

# REGISTER TESTS ------------------------------------------------------------------------------------------------------

# TEST REGISTER 201
# 201 Created: The resource has been created
# Here, the account has been created
def test_register_returns_201(client):
    # The data of the new account
    new_user = {
        "email": "donor.test@example.org",
        "password": "test_pwd",
        "role": "donor",
    }

    # Send it to the register route
    response = client.post("/api/register", json=new_user)

    # Check the code
    assert response.status_code == 201

    # Check the content of the answer
    data = response.get_json()
    assert data["email"] == new_user["email"]
    assert data["role"] == new_user["role"]
    assert "password" not in data
    assert "password_hash" not in data


# TEST REGISTER 409
# 409 Conflict: Conflicts with the current state
# Here, the email is already used
# The request conflicts with the current state of the data
def test_register_existing_email_returns_409(client, records):
    # The data of the new account
    new_user = {
        "email": "donor@example.org",
        "password": "123456",
        "role": "donor",
    }

    # Send it to the register route
    response = client.post("/api/register", json=new_user)

    # Check the code
    assert response.status_code == 409

    # get_json() turns the answer into a Python dictionary
    assert response.get_json()["message"] == "This email is already registered"


# TEST REGISTER 422
# 422 Unprocessable Entity: The data sent is invalid
# Here, the entry has invalid data
def test_register_with_invalid_data_returns_422(client):
    # The data of the new account
    new_user = {
        "email": "donor@example.org",
        "password": "999",  # invalid password (3 digits instead of 6 minimum)
        "role": "donor",
    }

    # Send it to the register route
    response = client.post("/api/register", json=new_user)

    # Check the code
    assert response.status_code == 422

    # get_json() turns the answer into a Python dictionary
    assert response.get_json()["message"] == "Validation error"


# LOGIN TESTS ------------------------------------------------------------------------------------------------------

# Function that creates the small json file for creating a valid account
# As it is reused in many tests
def new_user_json():
    return {
        "email": "donor.test@example.org",
        "password": "abcdef",
        "role": "donor",
    }


# TEST LOGIN 200
# 200 OK: The request was successful, and the response contains what was requested
# Here, the login succeeded
def test_login_returns_200(client):
    user = new_user_json()
    client.post("/api/register", json=user)
    response = client.post("/api/login", json={"email": user["email"], "password": user["password"]})

    assert response.status_code == 200

    # Check the content of the answer
    data = response.get_json()
    assert data["email"] == user["email"]
    assert data["role"] == user["role"]
    assert "password" not in data
    assert "password_hash" not in data

    # The session is open: /api/me now knows who we are
    me_response = client.get("/api/me")
    assert me_response.status_code == 200
    assert me_response.get_json()["email"] == user["email"]


# TEST LOGIN 401
# 401 Unauthorized: The user is not logged in
# Here, the user cannot log in without the right password
def test_login_wrong_password_returns_401(client):
    user = new_user_json()
    client.post("/api/register", json=user)
    response = client.post("/api/login", json={"email": user["email"], "password": "999999"})

    assert response.status_code == 401

    # get_json() turns the answer into a Python dictionary
    assert response.get_json()["message"] == "Invalid email or password."

    # No session was opened: /api/me does not know us
    me_response = client.get("/api/me")
    assert me_response.status_code == 401


# TEST LOGIN 401
# 401 Unauthorized: The user is not logged in
# Here, the user cannot log in without the right email
def test_login_unknown_email_returns_401(client):
    response = client.post("/api/login", json={"email": "nobody@example.org", "password": "abcdef"})

    assert response.status_code == 401

    # get_json() turns the answer into a Python dictionary
    # Here, we use the same message so that someone who tries to hack the account
    # cannot know if the mistake comes from the email address or the password
    assert response.get_json()["message"] == "Invalid email or password."

    # No session was opened: /api/me does not know us
    me_response = client.get("/api/me")
    assert me_response.status_code == 401


# LOGOUT TESTS ------------------------------------------------------------------------------------------------------

# TEST LOGOUT 204
# 204 No Content: Succeeded, but nothing to return
# Here, the logout was successful, and there is nothing to return
# Therefore, there is no JSON to verify in this response
def test_logout_returns_204(client):
    user = new_user_json()
    client.post("/api/register", json=user)
    client.post("/api/login", json={"email": user["email"], "password": user["password"]})

    # The session is open: /api/me now knows who we are
    me_response = client.get("/api/me")
    assert me_response.status_code == 200
    assert me_response.get_json()["email"] == user["email"]

    response = client.post("/api/logout")

    assert response.status_code == 204

    # The session is now closed: /api/me does not know us anymore
    me_after_response = client.get("/api/me")
    assert me_after_response.status_code == 401


# CURRENT USER TESTS ------------------------------------------------------------------------------------------------------

# TEST CURRENT USER 200
# 200 OK: The request was successful, and the response contains what was requested
# Here, the account of the current user was found and returned
def test_me_returns_200(client):
    user = new_user_json()
    client.post("/api/register", json=user)
    client.post("/api/login", json={"email": user["email"], "password": user["password"]})

    # The session is open: /api/me now knows who we are
    me_response = client.get("/api/me")
    assert me_response.status_code == 200

    data = me_response.get_json()
    assert data["email"] == user["email"]
    assert data["role"] == user["role"]
    assert "id" in data
    assert "password" not in data
    assert "password_hash" not in data


# TEST CURRENT USER 401
# 401 Unauthorized: The user is not logged in
# Here, the current user is not logged in, so he cannot access the account
def test_me_without_login_returns_401(client):
    # Nobody is logged in, so /api/me refuses access
    me_response = client.get("/api/me")

    assert me_response.status_code == 401

    # get_json() turns the answer into a Python dictionary
    assert me_response.get_json()["message"] == "Please log in to see your account"