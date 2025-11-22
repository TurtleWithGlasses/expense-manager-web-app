"""
Integration tests for JWT authentication REST API endpoints
Tests the complete HTTP request/response cycle for token-based authentication
"""
import pytest
from datetime import datetime, timedelta
from app.models.user import User
from app.core.jwt import create_access_token, create_refresh_token, verify_token


@pytest.mark.integration
class TestAuthRestLoginEndpoint:
    """Tests for POST /api/auth/login endpoint"""

    @pytest.mark.asyncio
    async def test_login_success(self, client, db_session, test_user):
        """Test successful login returns JWT tokens"""
        login_data = {
            "email": "test@example.com",
            "password": "testpassword123"
        }

        response = client.post("/api/auth/login", json=login_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "access_token" in data["data"]
        assert "refresh_token" in data["data"]
        assert data["data"]["token_type"] == "bearer"
        assert "user" in data["data"]
        assert data["data"]["user"]["email"] == test_user.email

        # Verify tokens are valid
        access_payload = verify_token(data["data"]["access_token"], token_type="access")
        assert access_payload is not None
        assert access_payload["sub"] == str(test_user.id)

        refresh_payload = verify_token(data["data"]["refresh_token"], token_type="refresh")
        assert refresh_payload is not None
        assert refresh_payload["sub"] == str(test_user.id)

    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, client, db_session, test_user):
        """Test login with wrong password returns 401"""
        login_data = {
            "email": "test@example.com",
            "password": "WrongPassword123!"
        }

        response = client.post("/api/auth/login", json=login_data)

        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, client, db_session):
        """Test login with non-existent email returns 401"""
        login_data = {
            "email": "nonexistent@example.com",
            "password": "testpassword123"
        }

        response = client.post("/api/auth/login", json=login_data)

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_login_unverified_user(self, client, db_session, test_user):
        """Test login with unverified user returns 403"""
        # Mark user as unverified
        test_user.is_verified = False
        db_session.commit()

        login_data = {
            "email": "test@example.com",
            "password": "testpassword123"
        }

        response = client.post("/api/auth/login", json=login_data)

        assert response.status_code == 403
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_login_validation_error(self, client, db_session):
        """Test login with invalid email format returns 422"""
        login_data = {
            "email": "not-an-email",
            "password": "testpassword123"
        }

        response = client.post("/api/auth/login", json=login_data)

        assert response.status_code == 422


@pytest.mark.integration
class TestAuthRestRegisterEndpoint:
    """Tests for POST /api/auth/register endpoint"""

    @pytest.mark.asyncio
    async def test_register_success(self, client, db_session):
        """Test successful registration returns JWT tokens"""
        register_data = {
            "email": "newuser@example.com",
            "password": "NewPass123!",
            "full_name": "New User"
        }

        response = client.post("/api/auth/register", json=register_data)

        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert "access_token" in data["data"]
        assert "refresh_token" in data["data"]
        assert data["data"]["user"]["email"] == "newuser@example.com"

        # Verify user was created in database
        user = db_session.query(User).filter(User.email == "newuser@example.com").first()
        assert user is not None
        assert user.full_name == "New User"
        assert user.is_verified is True  # Auto-verified for mobile

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, client, db_session, test_user):
        """Test registration with existing email returns 400"""
        register_data = {
            "email": "test@example.com",  # Already exists
            "password": "NewPass123!"
        }

        response = client.post("/api/auth/register", json=register_data)

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "email" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_register_validation_errors(self, client, db_session):
        """Test validation errors are returned"""
        # Invalid email
        register_data = {
            "email": "not-an-email",
            "password": "testpassword123"
        }

        response = client.post("/api/auth/register", json=register_data)
        assert response.status_code == 422

        # Short password
        register_data = {
            "email": "test@example.com",
            "password": "short"  # Too short
        }

        response = client.post("/api/auth/register", json=register_data)
        assert response.status_code == 422


@pytest.mark.integration
class TestAuthRestRefreshEndpoint:
    """Tests for POST /api/auth/refresh endpoint"""

    @pytest.mark.asyncio
    async def test_refresh_token_success(self, client, db_session, test_user):
        """Test token refresh returns new access token"""
        # Create a valid refresh token
        refresh_token = create_refresh_token(data={"sub": str(test_user.id)})

        refresh_data = {
            "refresh_token": refresh_token
        }

        response = client.post("/api/auth/refresh", json=refresh_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "access_token" in data["data"]
        assert data["data"]["token_type"] == "bearer"

        # Verify new access token is valid
        new_access_token = data["data"]["access_token"]
        payload = verify_token(new_access_token, token_type="access")
        assert payload is not None
        assert payload["sub"] == str(test_user.id)

    @pytest.mark.asyncio
    async def test_refresh_with_invalid_token(self, client, db_session):
        """Test refresh with invalid token returns 401"""
        refresh_data = {
            "refresh_token": "invalid.token.here"
        }

        response = client.post("/api/auth/refresh", json=refresh_data)

        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_refresh_with_access_token(self, client, db_session, test_user):
        """Test refresh with access token (wrong type) returns 401"""
        # Create access token instead of refresh token
        access_token = create_access_token(data={"sub": str(test_user.id)})

        refresh_data = {
            "refresh_token": access_token
        }

        response = client.post("/api/auth/refresh", json=refresh_data)

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_refresh_with_expired_token(self, client, db_session, test_user):
        """Test refresh with expired token returns 401"""
        # Create an expired refresh token
        expired_token = create_refresh_token(
            data={"sub": str(test_user.id)},
            expires_delta=timedelta(seconds=-1)  # Already expired
        )

        refresh_data = {
            "refresh_token": expired_token
        }

        response = client.post("/api/auth/refresh", json=refresh_data)

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_refresh_for_deleted_user(self, client, db_session, test_user):
        """Test refresh for deleted user returns 401"""
        # Create refresh token
        refresh_token = create_refresh_token(data={"sub": str(test_user.id)})

        # Delete user
        db_session.delete(test_user)
        db_session.commit()

        refresh_data = {
            "refresh_token": refresh_token
        }

        response = client.post("/api/auth/refresh", json=refresh_data)

        assert response.status_code == 401


@pytest.mark.integration
class TestAuthRestLogoutEndpoint:
    """Tests for POST /api/auth/logout endpoint"""

    @pytest.mark.asyncio
    async def test_logout_success(self, client, db_session):
        """Test logout returns success (stateless JWT)"""
        response = client.post("/api/auth/logout")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


@pytest.mark.integration
class TestJWTAuthenticationDependency:
    """Tests for JWT authentication dependency in protected endpoints"""

    @pytest.mark.asyncio
    async def test_protected_endpoint_with_valid_token(self, client, db_session, test_user):
        """Test accessing protected endpoint with valid JWT token"""
        # Create access token
        access_token = create_access_token(data={"sub": str(test_user.id)})

        # Access protected endpoint (using entries REST API as example)
        headers = {
            "Authorization": f"Bearer {access_token}"
        }

        response = client.get("/api/entries", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    @pytest.mark.asyncio
    async def test_protected_endpoint_without_token(self, client, db_session):
        """Test accessing protected endpoint without token returns 403"""
        response = client.get("/api/entries")

        # Note: HTTPBearer returns 403 when no credentials provided
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_protected_endpoint_with_invalid_token(self, client, db_session):
        """Test accessing protected endpoint with invalid token returns 401"""
        headers = {
            "Authorization": "Bearer invalid.token.here"
        }

        response = client.get("/api/entries", headers=headers)

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_protected_endpoint_with_expired_token(self, client, db_session, test_user):
        """Test accessing protected endpoint with expired token returns 401"""
        # Create expired access token
        expired_token = create_access_token(
            data={"sub": str(test_user.id)},
            expires_delta=timedelta(seconds=-1)
        )

        headers = {
            "Authorization": f"Bearer {expired_token}"
        }

        response = client.get("/api/entries", headers=headers)

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_protected_endpoint_with_refresh_token(self, client, db_session, test_user):
        """Test accessing protected endpoint with refresh token (wrong type) returns 401"""
        # Create refresh token instead of access token
        refresh_token = create_refresh_token(data={"sub": str(test_user.id)})

        headers = {
            "Authorization": f"Bearer {refresh_token}"
        }

        response = client.get("/api/entries", headers=headers)

        assert response.status_code == 401
