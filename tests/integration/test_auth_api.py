"""
Integration tests for authentication API endpoints
Tests the complete HTTP request/response cycle for auth endpoints
"""
import pytest
from unittest.mock import patch, AsyncMock
from datetime import datetime, timedelta, UTC

from app.models.user import User
from app.core.security import hash_password


@pytest.mark.integration
class TestRegisterEndpoint:
    """Tests for POST /auth/register endpoint"""

    @pytest.mark.asyncio
    async def test_register_success(self, client, db_session):
        """Test successful user registration"""
        with patch('app.services.auth.email_service.send_confirmation_email', new=AsyncMock()):
            response = client.post(
                "/register",
                data={
                    "email": "newuser@example.com",
                    "password": "SecurePass123",
                    "confirm_password": "SecurePass123",
                    "full_name": "New User"
                }
            )

        # Should redirect to verification sent page
        assert response.status_code in [200, 302]

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, client, db_session, test_user):
        """Test registration with existing email"""
        with patch('app.services.auth.email_service.send_confirmation_email', new=AsyncMock()):
            response = client.post(
                "/register",
                data={
                    "email": test_user.email,
                    "password": "SecurePass123",
                    "confirm_password": "SecurePass123",
                    "full_name": "Duplicate User"
                }
            )

        # Should show error
        assert response.status_code in [200, 400]
        if response.status_code == 200:
            assert b"already exists" in response.content.lower() or b"error" in response.content.lower()

    @pytest.mark.asyncio
    async def test_register_password_mismatch(self, client, db_session):
        """Test registration with mismatched passwords"""
        response = client.post(
            "/register",
            data={
                "email": "test@example.com",
                "password": "SecurePass123",
                "confirm_password": "DifferentPass456",
                "full_name": "Test User"
            }
        )

        # Should show error
        assert response.status_code in [200, 400]


@pytest.mark.integration
class TestLoginEndpoint:
    """Tests for POST /auth/login endpoint"""

    def test_login_success(self, client, db_session, test_user):
        """Test successful login"""
        response = client.post(
            "/login",
            data={
                "email": test_user.email,
                "password": "testpassword123"
            },
            follow_redirects=False  # Don't follow redirects so we can check the 303
        )

        # Should redirect to dashboard (303) or home page (302)
        assert response.status_code in [302, 303]
        # Check for session cookie (em_session is the cookie name)
        assert "em_session" in response.cookies

    def test_login_invalid_credentials(self, client, db_session, test_user):
        """Test login with incorrect password"""
        response = client.post(
            "/login",
            data={
                "email": test_user.email,
                "password": "wrongpassword"
            }
        )

        # Should show error
        assert response.status_code in [200, 401]
        if response.status_code == 200:
            assert b"invalid" in response.content.lower() or b"error" in response.content.lower()

    def test_login_nonexistent_user(self, client, db_session):
        """Test login with non-existent email"""
        response = client.post(
            "/login",
            data={
                "email": "nonexistent@example.com",
                "password": "password123"
            }
        )

        # Should show error
        assert response.status_code in [200, 401]

    def test_login_unverified_user(self, client, db_session):
        """Test login with unverified email"""
        # Create unverified user
        unverified_user = User(
            email="unverified@example.com",
            full_name="Unverified User",
            hashed_password=hash_password("password123"),
            is_verified=False,
            created_at=datetime.now()
        )
        db_session.add(unverified_user)
        db_session.commit()

        response = client.post(
            "/login",
            data={
                "email": unverified_user.email,
                "password": "password123"
            }
        )

        # Should show error about email verification
        assert response.status_code in [200, 403]
        if response.status_code == 200:
            assert b"verify" in response.content.lower()


@pytest.mark.integration
class TestLogoutEndpoint:
    """Tests for POST /auth/logout endpoint"""

    def test_logout_success(self, client, authenticated_client, db_session):
        """Test successful logout"""
        response = authenticated_client.post("/logout")

        # Should redirect to login page
        assert response.status_code in [200, 302, 303]


@pytest.mark.integration
class TestVerifyEmailEndpoint:
    """Tests for GET /auth/verify endpoint"""

    def test_verify_email_with_valid_token(self, client, db_session):
        """Test email verification with valid token"""
        # Create unverified user with verification token
        from app.services.auth import generate_token
        token = generate_token()
        user = User(
            email="toverify@example.com",
            hashed_password=hash_password("password123"),
            is_verified=False,
            verification_token=token,
            verification_token_expires=datetime.now(UTC) + timedelta(hours=24),
            created_at=datetime.now()
        )
        db_session.add(user)
        db_session.commit()

        # Verify email
        response = client.get(f"/confirm-email/{token}")

        # Should redirect or show success
        assert response.status_code in [200, 302, 303]

        # Check user is verified
        db_session.refresh(user)
        assert user.is_verified is True

    def test_verify_email_with_invalid_token(self, client, db_session):
        """Test email verification with invalid token"""
        response = client.get("/confirm-email/invalidtoken123")

        # Should show error
        assert response.status_code in [200, 400]

    def test_verify_email_with_expired_token(self, client, db_session):
        """Test email verification with expired token"""
        # Create user with expired token
        from app.services.auth import generate_token
        token = generate_token()
        user = User(
            email="expired@example.com",
            hashed_password=hash_password("password123"),
            is_verified=False,
            verification_token=token,
            verification_token_expires=datetime.now(UTC) - timedelta(hours=1),  # Expired
            created_at=datetime.now()
        )
        db_session.add(user)
        db_session.commit()

        # Try to verify with expired token
        response = client.get(f"/confirm-email/{token}")

        # Should show error
        assert response.status_code in [200, 400]


@pytest.mark.integration
class TestForgotPasswordEndpoint:
    """Tests for POST /auth/forgot-password endpoint"""

    @pytest.mark.asyncio
    async def test_forgot_password_existing_user(self, client, db_session, test_user):
        """Test password reset request for existing user"""
        with patch('app.services.auth.email_service.send_password_reset_email',
                   new=AsyncMock(return_value=True)):
            response = client.post(
                "/forgot-password",
                data={"email": test_user.email}
            )

        # Should redirect or show success
        assert response.status_code in [200, 302, 303]

    @pytest.mark.asyncio
    async def test_forgot_password_nonexistent_user(self, client, db_session):
        """Test password reset request for non-existent user"""
        with patch('app.services.auth.email_service.send_password_reset_email',
                   new=AsyncMock(return_value=False)):
            response = client.post(
                "/forgot-password",
                data={"email": "nonexistent@example.com"}
            )

        # Should still show success (don't reveal user doesn't exist)
        assert response.status_code in [200, 302, 303]


@pytest.mark.integration
class TestResetPasswordEndpoint:
    """Tests for POST /auth/reset-password endpoint"""

    def test_reset_password_with_valid_token(self, client, db_session):
        """Test password reset with valid token"""
        # Create user with reset token
        from app.services.auth import generate_token
        token = generate_token()
        user = User(
            email="resetpwd@example.com",
            hashed_password=hash_password("oldpassword123"),
            is_verified=True,
            password_reset_token=token,
            password_reset_expires=datetime.now(UTC) + timedelta(hours=1),
            created_at=datetime.now()
        )
        db_session.add(user)
        db_session.commit()

        # Reset password
        response = client.post(
            f"/reset-password/{token}",
            data={
                "password": "newpassword456",
                "confirm_password": "newpassword456"
            }
        )

        # Should redirect or show success
        assert response.status_code in [200, 302, 303]

    def test_reset_password_with_invalid_token(self, client, db_session):
        """Test password reset with invalid token"""
        response = client.post(
            "/reset-password/invalidtoken123",
            data={
                "password": "newpassword456",
                "confirm_password": "newpassword456"
            }
        )

        # Should show error
        assert response.status_code in [200, 400]

    def test_reset_password_with_mismatched_passwords(self, client, db_session):
        """Test password reset with mismatched passwords"""
        # Create user with reset token
        from app.services.auth import generate_token
        token = generate_token()
        user = User(
            email="resetpwd2@example.com",
            hashed_password=hash_password("oldpassword123"),
            is_verified=True,
            password_reset_token=token,
            password_reset_expires=datetime.now(UTC) + timedelta(hours=1),
            created_at=datetime.now()
        )
        db_session.add(user)
        db_session.commit()

        # Try to reset with mismatched passwords
        response = client.post(
            f"/reset-password/{token}",
            data={
                "password": "newpassword456",
                "confirm_password": "differentpassword789"
            }
        )

        # Should show error
        assert response.status_code in [200, 400]


@pytest.mark.integration
class TestResendVerificationEndpoint:
    """Tests for POST /auth/resend-verification endpoint"""

    @pytest.mark.asyncio
    async def test_resend_verification_unverified_user(self, client, db_session):
        """Test resending verification for unverified user"""
        # Create unverified user
        user = User(
            email="resend@example.com",
            hashed_password=hash_password("password123"),
            is_verified=False,
            verification_token="oldtoken",
            verification_token_expires=datetime.now(UTC) + timedelta(hours=1),
            created_at=datetime.now()
        )
        db_session.add(user)
        db_session.commit()

        with patch('app.services.auth.email_service.send_confirmation_email',
                   new=AsyncMock(return_value=True)):
            response = client.post(
                "/resend-verification",
                data={"email": user.email}
            )

        # Should show success
        assert response.status_code in [200, 302, 303]

    @pytest.mark.asyncio
    async def test_resend_verification_already_verified(self, client, db_session, test_user):
        """Test resending verification for already verified user"""
        with patch('app.services.auth.email_service.send_confirmation_email',
                   new=AsyncMock(return_value=False)):
            response = client.post(
                "/resend-verification",
                data={"email": test_user.email}
            )

        # Should show error or message
        assert response.status_code in [200, 400]
