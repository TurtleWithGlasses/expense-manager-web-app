"""
Integration tests for CORS configuration
Tests that CORS headers are properly configured for mobile/external clients
"""
import pytest


@pytest.mark.integration
class TestCORSConfiguration:
    """Tests for CORS middleware configuration"""

    def test_cors_headers_on_preflight_request(self, client):
        """Test that CORS headers are present on OPTIONS preflight requests"""
        headers = {
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Authorization, Content-Type"
        }

        response = client.options("/api/auth/login", headers=headers)

        # Check that CORS headers are present
        assert "access-control-allow-origin" in response.headers
        assert "access-control-allow-methods" in response.headers
        assert "access-control-allow-headers" in response.headers

    def test_cors_headers_on_actual_request(self, client):
        """Test that CORS headers are present on actual requests"""
        headers = {
            "Origin": "http://localhost:3000"
        }

        response = client.get("/api/categories", headers=headers)

        # Should have CORS headers even on failed auth (403)
        assert "access-control-allow-origin" in response.headers

    def test_cors_allows_authorization_header(self, client, test_user):
        """Test that Authorization header is allowed via CORS"""
        from app.core.jwt import create_access_token

        # Create a valid token
        token = create_access_token(data={"sub": str(test_user.id)})

        headers = {
            "Origin": "http://localhost:3000",
            "Authorization": f"Bearer {token}"
        }

        response = client.get("/api/categories", headers=headers)

        # Should succeed (200) not fail due to CORS
        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers

    def test_cors_allows_content_type_header(self, client):
        """Test that Content-Type header is allowed via CORS"""
        headers = {
            "Origin": "http://localhost:3000",
            "Content-Type": "application/json"
        }

        # Use auth endpoint which doesn't require authentication
        response = client.post(
            "/api/auth/login",
            json={"email": "test@example.com", "password": "wrong"},
            headers=headers
        )

        # Should not fail due to CORS (will fail with 401 due to bad credentials)
        assert "access-control-allow-origin" in response.headers

    def test_cors_exposes_headers(self, client, test_user):
        """Test that specified headers are exposed via CORS"""
        from app.core.jwt import create_access_token

        token = create_access_token(data={"sub": str(test_user.id)})

        headers = {
            "Origin": "http://localhost:3000",
            "Authorization": f"Bearer {token}"
        }

        response = client.get("/api/entries", headers=headers)

        # Check exposed headers
        assert response.status_code == 200
        assert "access-control-expose-headers" in response.headers
        exposed = response.headers["access-control-expose-headers"].lower()
        assert "content-length" in exposed
