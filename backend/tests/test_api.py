import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI
import json


@pytest.fixture
def client():
    """Create a test client."""
    from backend.main import app

    return TestClient(app)


@pytest.fixture
def auth_headers():
    """Create authenticated headers for testing."""
    # This would typically use a test JWT token
    return {"Authorization": "Bearer test_token"}


class TestVideoAPI:
    """Test suite for Video API endpoints."""

    def test_get_video_feed(self, client):
        """Test getting video feed."""
        response = client.get("/api/videos/feed")

        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert "videos" in data

    def test_upload_video(self, client, auth_headers):
        """Test video upload."""
        # Mock video file
        files = {"file": ("test.mp4", b"fake video content", "video/mp4")}
        data = {"description": "Test video upload", "hashtags": "test,video"}

        response = client.post(
            "/api/videos/upload", files=files, data=data, headers=auth_headers
        )

        assert response.status_code == 200
        result = response.json()
        assert "success" in result
        assert "video" in result

    def test_get_video_by_id(self, client, sample_video):
        """Test getting video by ID."""
        response = client.get(f"/api/videos/{sample_video.id}")

        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert data["video"]["id"] == sample_video.id

    def test_video_engagement(self, client, auth_headers, sample_video):
        """Test video engagement (like, comment, share)."""
        # Test like
        response = client.post(
            f"/api/videos/{sample_video.id}/like", headers=auth_headers
        )
        assert response.status_code == 200

        # Test comment
        response = client.post(
            f"/api/videos/{sample_video.id}/comment",
            json={"content": "Test comment"},
            headers=auth_headers,
        )
        assert response.status_code == 200

        # Test share
        response = client.post(
            f"/api/videos/{sample_video.id}/share", headers=auth_headers
        )
        assert response.status_code == 200


class TestAuthAPI:
    """Test suite for Authentication API endpoints."""

    def test_register_user(self, client):
        """Test user registration."""
        user_data = {
            "username": "testuser123",
            "email": "test@example.com",
            "password": "securepassword123",
        }

        response = client.post("/api/auth/register", json=user_data)

        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert "user" in data
        assert "token" in data

    def test_login_user(self, client, sample_user):
        """Test user login."""
        login_data = {"email": sample_user.email, "password": "password"}

        response = client.post("/api/auth/login", json=login_data)

        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert "token" in data
        assert data["user"]["id"] == sample_user.id

    def test_invalid_login(self, client):
        """Test invalid login credentials."""
        login_data = {"email": "invalid@example.com", "password": "wrongpassword"}

        response = client.post("/api/auth/login", json=login_data)

        assert response.status_code == 401

    def test_get_current_user(self, client, auth_headers, sample_user):
        """Test getting current authenticated user."""
        response = client.get("/api/auth/me", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["user"]["id"] == sample_user.id


class TestPaymentAPI:
    """Test suite for Payment API endpoints."""

    def test_create_tip(self, client, auth_headers):
        """Test creating a tip."""
        tip_data = {
            "creator_id": "creator_123",
            "amount": 5.00,
            "video_id": "video_123",
        }

        response = client.post("/api/payments/tip", data=tip_data, headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert "payment_intent_id" in data
        assert "client_secret" in data

    def test_get_wallet(self, client, auth_headers):
        """Test getting user wallet."""
        response = client.get("/api/payments/wallet", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert "wallet" in data
        assert "balance" in data["wallet"]

    def test_get_transaction_history(self, client, auth_headers):
        """Test getting transaction history."""
        response = client.get("/api/payments/transactions", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert "transactions" in data

    def test_request_payout(self, client, auth_headers):
        """Test requesting a payout."""
        response = client.post("/api/payments/payouts/request", headers=auth_headers)

        # This might fail if user doesn't have sufficient balance
        # which is expected behavior
        assert response.status_code in [200, 400]


class TestAnalyticsAPI:
    """Test suite for Analytics API endpoints."""

    def test_get_creator_dashboard(self, client, auth_headers):
        """Test getting creator dashboard."""
        response = client.get("/api/analytics/creator/dashboard", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert "current_month" in data
        assert "key_metrics" in data

    def test_track_video_view(self, client, sample_video):
        """Test tracking video view."""
        response = client.post(
            f"/api/analytics/videos/{sample_video.id}/track",
            data={"event_type": "view", "watch_time": 30.0},
        )

        assert response.status_code == 200
        data = response.json()
        assert "success" in data

    def test_get_trending_content(self, client):
        """Test getting trending content."""
        response = client.get("/api/analytics/trending/content")

        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert "trending_content" in data

    def test_get_time_series_data(self, client, auth_headers):
        """Test getting time series data."""
        response = client.get(
            "/api/analytics/time-series/views",
            params={"time_period": "week"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert "time_series" in data


class TestVideoEditorAPI:
    """Test suite for Video Editor API endpoints."""

    def test_create_project(self, client, auth_headers):
        """Test creating a video project."""
        project_data = {"title": "Test Project", "description": "A test video project"}

        response = client.post(
            "/api/editor/projects", data=project_data, headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert "project" in data

    def test_get_user_projects(self, client, auth_headers):
        """Test getting user's video projects."""
        response = client.get("/api/editor/projects", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert "projects" in data

    def test_upload_asset_to_project(self, client, auth_headers):
        """Test uploading asset to project."""
        # First create a project
        project_response = client.post(
            "/api/editor/projects", data={"title": "Test Project"}, headers=auth_headers
        )
        project_data = project_response.json()
        project_id = project_data["project"]["id"]

        # Upload asset
        files = {"file": ("test.mp4", b"fake video content", "video/mp4")}
        data = {"project_id": project_id, "asset_type": "video"}

        response = client.post(
            f"/api/editor/projects/{project_id}/assets",
            files=files,
            data=data,
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert "asset" in data

    def test_get_project_assets(self, client, auth_headers):
        """Test getting project assets."""
        # This would need an existing project with assets
        response = client.get(
            "/api/editor/projects/test_project/assets", headers=auth_headers
        )

        # May return empty if project doesn't exist
        assert response.status_code in [200, 404]


class TestErrorHandling:
    """Test suite for error handling and edge cases."""

    def test_404_handling(self, client):
        """Test 404 error handling."""
        response = client.get("/api/nonexistent/endpoint")

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    def test_validation_errors(self, client):
        """Test input validation errors."""
        # Test invalid registration data
        invalid_user = {
            "username": "",  # Empty username
            "email": "invalid-email",  # Invalid email
            "password": "123",  # Too short password
        }

        response = client.post("/api/auth/register", json=invalid_user)

        assert response.status_code == 422  # Validation error
        data = response.json()
        assert "detail" in data

    def test_unauthorized_access(self, client):
        """Test unauthorized access to protected endpoints."""
        response = client.get("/api/auth/me")  # No auth headers

        assert response.status_code == 401

    def test_rate_limiting(self, client):
        """Test rate limiting behavior."""
        # Make multiple rapid requests to test rate limiting
        responses = []
        for _ in range(10):
            response = client.post(
                "/api/auth/login",
                json={"email": "test@example.com", "password": "password"},
            )
            responses.append(response.status_code)

        # Some requests should be rate limited
        assert any(status == 429 for status in responses)


class TestIntegration:
    """Integration tests for complete user flows."""

    def test_complete_user_flow(self, client):
        """Test complete user registration to content creation flow."""
        # 1. Register user
        user_data = {
            "username": "integration_user",
            "email": "integration@example.com",
            "password": "securepassword123",
        }

        register_response = client.post("/api/auth/register", json=user_data)
        assert register_response.status_code == 200
        register_data = register_response.json()
        token = register_data["token"]

        auth_headers = {"Authorization": f"Bearer {token}"}

        # 2. Get user profile
        profile_response = client.get("/api/auth/me", headers=auth_headers)
        assert profile_response.status_code == 200
        profile_data = profile_response.json()
        user_id = profile_data["user"]["id"]

        # 3. Create video project
        project_response = client.post(
            "/api/editor/projects",
            data={"title": "Integration Test Project"},
            headers=auth_headers,
        )
        assert project_response.status_code == 200
        project_data = project_response.json()
        project_id = project_data["project"]["id"]

        # 4. Get analytics (should be empty initially)
        analytics_response = client.get(
            "/api/analytics/creator/dashboard", headers=auth_headers
        )
        assert analytics_response.status_code == 200
        analytics_data = analytics_response.json()
        assert analytics_data["current_month"]["total_views"] == 0

        # 5. Check wallet
        wallet_response = client.get("/api/payments/wallet", headers=auth_headers)
        assert wallet_response.status_code == 200
        wallet_data = wallet_response.json()
        assert wallet_data["wallet"]["balance"] == 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
