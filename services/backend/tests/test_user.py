import os
from unittest.mock import patch

from fastapi import status

os.environ["TESTING"] = "1"


@patch("src.aws.cognito.Cognito.sign_up")
def test_sign_up(mock_sign_up, client):
    mock_sign_up.return_value = {"UserSub": "test-user-sub"}

    user_data = {"email": "testuser@example.com", "password": "TestPassword123!"}
    response = client.post("/api/v1/auth/sign_up", json=user_data)
    body = response.json()

    assert response.status_code == status.HTTP_201_CREATED
    assert body["id"] == "test-user-sub"


@patch("src.aws.cognito.Cognito.confirm_sign_up")
@patch("src.aws.cognito.Cognito.admin_add_user_to_group")
def test_confirm_sign_up(mock_add_user_to_group, mock_confirm_sign_up, client):
    mock_confirm_sign_up.return_value = None
    mock_add_user_to_group.return_value = None

    confirmation_data = {
        "email": "testuser@example.com",
        "confirmation_code": "123456",
    }
    response = client.post("/api/v1/auth/sign_up/confirm", json=confirmation_data)
    body = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert body["message"] == "Account confirmed successfully"


@patch("src.aws.cognito.Cognito.authenticate_user")
def test_sign_in(mock_authenticate_user, client):
    mock_authenticate_user.return_value = {
        "AuthenticationResult": {
            "access_token": "test-access-token",
            "refresh_token": "test-refresh-token",
            "id_token": "test-id-token",
            "token_type": "Bearer",
            "expires_in": 3600,
        }
    }

    login_data = {"email": "testuser@example.com", "password": "TestPassword123!"}
    response = client.post("/api/v1/auth/sign_in", json=login_data)
    body = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert body["access_token"] == "test-access-token"
    assert "refresh_token" in body
    assert "id_token" in body
    assert body["token_type"] == "Bearer"
    assert body["expires_in"] == 3600


@patch("src.aws.cognito.Cognito.forgot_password")
def test_forgot_password(mock_forgot_password, client):
    mock_forgot_password.return_value = None

    email_data = "testuser@example.com"
    response = client.post(f"/api/v1/auth/forgot_password?email={email_data}")
    body = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert body["message"] == "Password reset code sent to your email address"


def test_get_current_user(client, token):
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/api/v1/auth/me", headers=headers)
    body = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert "email" in body
    assert body["email"] == "user@email.com"


@patch("src.aws.cognito.Cognito.authenticate_refresh_token")
def test_refresh_token(mock_refresh_token, client):
    mock_refresh_token.return_value = {
        "AuthenticationResult": {
            "access_token": "new-access-token",
            "refresh_token": "new-refresh-token",
            "id_token": "new-id-token",
            "token_type": "Bearer",
            "expires_in": 3600,
        }
    }

    refresh_data = {"refresh_token": "old-refresh-token"}

    response = client.post("/api/v1/auth/token/refresh", json=refresh_data)
    body = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert body["access_token"] == "new-access-token"
    assert body["refresh_token"] == "new-refresh-token"
    assert body["id_token"] == "new-id-token"
    assert body["token_type"] == "Bearer"
    assert body["expires_in"] == 3600


def test_admin_endpoint(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}

    response = client.get("/api/v1/auth/admin", headers=headers)
    body = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert body["message"] == "Welcome, admin user"


def test_admin_endpoint_unauthorized(client, token):
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/api/v1/auth/admin", headers=headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN