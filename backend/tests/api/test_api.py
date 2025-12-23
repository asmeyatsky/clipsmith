import pytest


class TestHealthEndpoints:
    def test_root_endpoint(self, client):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "running"

    def test_health_endpoint(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"


class TestAuthAPI:
    def test_register_user(self, client):
        response = client.post(
            "/auth/register",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "securepassword123"
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"
        assert data["is_active"] is True

    def test_register_duplicate_email(self, client):
        # Register first user
        client.post(
            "/auth/register",
            json={
                "username": "user1",
                "email": "duplicate@example.com",
                "password": "password123"
            }
        )

        # Try to register with same email
        response = client.post(
            "/auth/register",
            json={
                "username": "user2",
                "email": "duplicate@example.com",
                "password": "password456"
            }
        )
        assert response.status_code == 400

    def test_login_success(self, client):
        # Register user first
        client.post(
            "/auth/register",
            json={
                "username": "loginuser",
                "email": "login@example.com",
                "password": "mypassword123"
            }
        )

        # Login
        response = client.post(
            "/auth/login",
            json={
                "email": "login@example.com",
                "password": "mypassword123"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client):
        # Register user first
        client.post(
            "/auth/register",
            json={
                "username": "wrongpassuser",
                "email": "wrongpass@example.com",
                "password": "correctpassword"
            }
        )

        # Try to login with wrong password
        response = client.post(
            "/auth/login",
            json={
                "email": "wrongpass@example.com",
                "password": "wrongpassword"
            }
        )
        assert response.status_code == 401

    def test_get_current_user(self, client):
        # Register and login
        client.post(
            "/auth/register",
            json={
                "username": "meuser",
                "email": "me@example.com",
                "password": "password123"
            }
        )
        login_response = client.post(
            "/auth/login",
            json={
                "email": "me@example.com",
                "password": "password123"
            }
        )
        token = login_response.json()["access_token"]

        # Get current user
        response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "meuser"
        assert data["email"] == "me@example.com"

    def test_password_reset_request(self, client):
        # Register user first
        client.post(
            "/auth/register",
            json={
                "username": "resetuser",
                "email": "reset@example.com",
                "password": "oldpassword"
            }
        )

        # Request password reset
        response = client.post(
            "/auth/password-reset/request",
            json={"email": "reset@example.com"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data

    def test_password_reset_nonexistent_email(self, client):
        # Request reset for non-existent email (should still return success for security)
        response = client.post(
            "/auth/password-reset/request",
            json={"email": "nonexistent@example.com"}
        )
        assert response.status_code == 200


class TestVideoAPI:
    def _get_auth_token(self, client):
        client.post(
            "/auth/register",
            json={
                "username": "videouser",
                "email": "video@example.com",
                "password": "password123"
            }
        )
        response = client.post(
            "/auth/login",
            json={
                "email": "video@example.com",
                "password": "password123"
            }
        )
        return response.json()["access_token"]

    def test_list_videos_empty(self, client):
        response = client.get("/videos/")
        assert response.status_code == 200
        data = response.json()
        assert data["videos"] == []
        assert data["total"] == 0

    def test_search_videos_empty(self, client):
        response = client.get("/videos/search?q=test")
        assert response.status_code == 200
        data = response.json()
        assert data["videos"] == []
        assert data["total"] == 0

    def test_get_nonexistent_video(self, client):
        response = client.get("/videos/nonexistent-id")
        assert response.status_code == 404


class TestUserAPI:
    def _register_and_login(self, client, username, email):
        client.post(
            "/auth/register",
            json={
                "username": username,
                "email": email,
                "password": "password123"
            }
        )
        response = client.post(
            "/auth/login",
            json={
                "email": email,
                "password": "password123"
            }
        )
        return response.json()

    def test_get_user_profile(self, client):
        self._register_and_login(client, "profileuser", "profile@example.com")

        response = client.get("/users/profileuser")
        assert response.status_code == 200
        data = response.json()
        assert data["user"]["username"] == "profileuser"

    def test_get_nonexistent_profile(self, client):
        response = client.get("/users/nonexistentuser")
        assert response.status_code == 404

    def test_follow_user(self, client):
        # Create two users
        login1 = self._register_and_login(client, "follower", "follower@example.com")
        self._register_and_login(client, "followed", "followed@example.com")

        token = login1["access_token"]
        followed_id = login1["user"]["id"]  # We need the followed user's ID

        # Get the followed user's ID
        profile_response = client.get("/users/followed")
        followed_id = profile_response.json()["user"]["id"]

        # Follow the user
        response = client.post(
            f"/users/{followed_id}/follow",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200

    def test_follow_status(self, client):
        login = self._register_and_login(client, "statususer", "status@example.com")
        self._register_and_login(client, "targetuser", "target@example.com")

        token = login["access_token"]

        # Get target user ID
        profile_response = client.get("/users/targetuser")
        target_id = profile_response.json()["user"]["id"]

        # Check follow status (should be false initially)
        response = client.get(
            f"/users/{target_id}/follow_status",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        assert response.json()["is_following"] is False
