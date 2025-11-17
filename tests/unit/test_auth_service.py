"""
Unit tests for authentication service
Tests all auth-related business logic functions
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, AsyncMock
from sqlalchemy.exc import IntegrityError

from app.services import auth
from app.models.user import User
from app.core.security import verify_password


@pytest.mark.unit
class TestCreateUser:
    """Tests for create_user function"""

    @pytest.mark.asyncio
    async def test_create_user_success(self, db_session):
        """Test successful user creation"""
        email = "newuser@example.com"
        password = "SecurePassword123"
        full_name = "New User"

        with patch('app.services.auth.email_service.send_confirmation_email', new=AsyncMock()):
            user = await auth.create_user(
                db=db_session,
                email=email,
                password=password,
                full_name=full_name
            )

        assert user is not None
        assert user.email == email
        assert user.full_name == full_name
        assert user.is_verified is False
        assert user.verification_token is not None
        assert user.verification_token_expires is not None
        assert verify_password(password, user.hashed_password)

    @pytest.mark.asyncio
    async def test_create_user_duplicate_email(self, db_session, test_user):
        """Test creating user with duplicate email raises ValueError"""
        with pytest.raises(ValueError, match="User with this email already exists"):
            await auth.create_user(
                db=db_session,
                email=test_user.email,
                password="password123",
                send_confirmation=False
            )

    @pytest.mark.asyncio
    async def test_create_user_without_full_name(self, db_session):
        """Test creating user without full name"""
        email = "noname@example.com"

        with patch('app.services.auth.email_service.send_confirmation_email', new=AsyncMock()):
            user = await auth.create_user(
                db=db_session,
                email=email,
                password="password123"
            )

        assert user is not None
        assert user.email == email
        assert user.full_name is None

    @pytest.mark.asyncio
    async def test_create_user_email_failure_does_not_prevent_registration(self, db_session):
        """Test that email sending failure doesn't prevent user creation"""
        email = "emailfail@example.com"

        with patch('app.services.auth.email_service.send_confirmation_email',
                   new=AsyncMock(side_effect=Exception("Email service down"))):
            user = await auth.create_user(
                db=db_session,
                email=email,
                password="password123"
            )

        # User should still be created even if email fails
        assert user is not None
        assert user.email == email

    @pytest.mark.asyncio
    async def test_create_user_verification_token_expires_in_24_hours(self, db_session):
        """Test that verification token expires in 24 hours"""
        with patch('app.services.auth.email_service.send_confirmation_email', new=AsyncMock()):
            user = await auth.create_user(
                db=db_session,
                email="tokentest@example.com",
                password="password123"
            )

        time_diff = user.verification_token_expires - datetime.utcnow()
        # Allow 1 minute variance for test execution time
        assert timedelta(hours=23, minutes=59) <= time_diff <= timedelta(hours=24, minutes=1)


@pytest.mark.unit
class TestAuthenticateUser:
    """Tests for authenticate_user function"""

    def test_authenticate_valid_credentials(self, db_session, test_user):
        """Test authentication with valid credentials"""
        user = auth.authenticate_user(
            db=db_session,
            email=test_user.email,
            password="testpassword123"
        )

        assert user is not None
        assert user.id == test_user.id
        assert user.email == test_user.email

    def test_authenticate_invalid_email(self, db_session):
        """Test authentication with non-existent email"""
        user = auth.authenticate_user(
            db=db_session,
            email="nonexistent@example.com",
            password="password123"
        )

        assert user is None

    def test_authenticate_invalid_password(self, db_session, test_user):
        """Test authentication with incorrect password"""
        user = auth.authenticate_user(
            db=db_session,
            email=test_user.email,
            password="wrongpassword"
        )

        assert user is None

    def test_authenticate_unverified_user_raises_error(self, db_session):
        """Test authentication with unverified email raises ValueError"""
        # Create unverified user
        unverified_user = User(
            email="unverified@example.com",
            full_name="Unverified User",
            hashed_password=auth.hash_password("password123"),
            is_verified=False,
            created_at=datetime.now()
        )
        db_session.add(unverified_user)
        db_session.commit()

        with pytest.raises(ValueError, match="Please verify your email address"):
            auth.authenticate_user(
                db=db_session,
                email=unverified_user.email,
                password="password123"
            )


@pytest.mark.unit
class TestVerifyEmail:
    """Tests for verify_email function"""

    def test_verify_email_with_valid_token(self, db_session):
        """Test email verification with valid token"""
        # Create unverified user with verification token
        token = auth.generate_token()
        user = User(
            email="toverify@example.com",
            hashed_password=auth.hash_password("password123"),
            is_verified=False,
            verification_token=token,
            verification_token_expires=datetime.utcnow() + timedelta(hours=24),
            created_at=datetime.now()
        )
        db_session.add(user)
        db_session.commit()

        # Verify email
        verified_user = auth.verify_email(db=db_session, token=token)

        assert verified_user is not None
        assert verified_user.is_verified is True
        assert verified_user.verification_token is None
        assert verified_user.verification_token_expires is None

    def test_verify_email_with_invalid_token(self, db_session):
        """Test email verification with invalid token"""
        result = auth.verify_email(db=db_session, token="invalidtoken123")

        assert result is None

    def test_verify_email_with_expired_token(self, db_session):
        """Test email verification with expired token"""
        # Create user with expired token
        token = auth.generate_token()
        user = User(
            email="expired@example.com",
            hashed_password=auth.hash_password("password123"),
            is_verified=False,
            verification_token=token,
            verification_token_expires=datetime.utcnow() - timedelta(hours=1),  # Expired
            created_at=datetime.now()
        )
        db_session.add(user)
        db_session.commit()

        # Try to verify with expired token
        result = auth.verify_email(db=db_session, token=token)

        assert result is None


@pytest.mark.unit
class TestResendVerificationEmail:
    """Tests for resend_verification_email function"""

    @pytest.mark.asyncio
    async def test_resend_verification_success(self, db_session):
        """Test resending verification email for unverified user"""
        # Create unverified user
        user = User(
            email="resend@example.com",
            hashed_password=auth.hash_password("password123"),
            is_verified=False,
            verification_token="oldtoken",
            verification_token_expires=datetime.utcnow() + timedelta(hours=1),
            created_at=datetime.now()
        )
        db_session.add(user)
        db_session.commit()
        old_token = user.verification_token

        with patch('app.services.auth.email_service.send_confirmation_email',
                   new=AsyncMock(return_value=True)):
            result = await auth.resend_verification_email(
                db=db_session,
                email=user.email
            )

        assert result is True
        # Check that token was regenerated
        db_session.refresh(user)
        assert user.verification_token != old_token
        assert user.verification_token is not None

    @pytest.mark.asyncio
    async def test_resend_verification_for_nonexistent_user(self, db_session):
        """Test resending verification for non-existent email"""
        result = await auth.resend_verification_email(
            db=db_session,
            email="nonexistent@example.com"
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_resend_verification_for_already_verified_user(self, db_session, test_user):
        """Test resending verification for already verified user"""
        result = await auth.resend_verification_email(
            db=db_session,
            email=test_user.email
        )

        assert result is False


@pytest.mark.unit
class TestPasswordReset:
    """Tests for password reset functionality"""

    @pytest.mark.asyncio
    async def test_request_password_reset_success(self, db_session, test_user):
        """Test requesting password reset for existing user"""
        with patch('app.services.auth.email_service.send_password_reset_email',
                   new=AsyncMock(return_value=True)):
            result = await auth.request_password_reset(
                db=db_session,
                email=test_user.email
            )

        assert result is True
        db_session.refresh(test_user)
        assert test_user.password_reset_token is not None
        assert test_user.password_reset_expires is not None

    @pytest.mark.asyncio
    async def test_request_password_reset_nonexistent_user(self, db_session):
        """Test password reset request for non-existent user"""
        result = await auth.request_password_reset(
            db=db_session,
            email="nonexistent@example.com"
        )

        # Should return False without revealing user doesn't exist
        assert result is False

    @pytest.mark.asyncio
    async def test_request_password_reset_token_expires_in_1_hour(self, db_session, test_user):
        """Test that password reset token expires in 1 hour"""
        with patch('app.services.auth.email_service.send_password_reset_email',
                   new=AsyncMock(return_value=True)):
            await auth.request_password_reset(
                db=db_session,
                email=test_user.email
            )

        db_session.refresh(test_user)
        time_diff = test_user.password_reset_expires - datetime.utcnow()
        # Allow 1 minute variance
        assert timedelta(minutes=59) <= time_diff <= timedelta(hours=1, minutes=1)

    def test_reset_password_with_valid_token(self, db_session):
        """Test resetting password with valid token"""
        # Create user with reset token
        token = auth.generate_token()
        user = User(
            email="resetpwd@example.com",
            hashed_password=auth.hash_password("oldpassword123"),
            is_verified=True,
            password_reset_token=token,
            password_reset_expires=datetime.utcnow() + timedelta(hours=1),
            created_at=datetime.now()
        )
        db_session.add(user)
        db_session.commit()
        old_password_hash = user.hashed_password

        # Reset password
        new_password = "newpassword456"
        result = auth.reset_password(
            db=db_session,
            token=token,
            new_password=new_password
        )

        assert result is not None
        assert result.id == user.id
        assert result.password_reset_token is None
        assert result.password_reset_expires is None
        assert result.hashed_password != old_password_hash
        assert verify_password(new_password, result.hashed_password)

    def test_reset_password_with_invalid_token(self, db_session):
        """Test resetting password with invalid token"""
        result = auth.reset_password(
            db=db_session,
            token="invalidtoken123",
            new_password="newpassword456"
        )

        assert result is None

    def test_reset_password_with_expired_token(self, db_session):
        """Test resetting password with expired token"""
        # Create user with expired token
        token = auth.generate_token()
        user = User(
            email="expiredtoken@example.com",
            hashed_password=auth.hash_password("oldpassword123"),
            is_verified=True,
            password_reset_token=token,
            password_reset_expires=datetime.utcnow() - timedelta(hours=1),  # Expired
            created_at=datetime.now()
        )
        db_session.add(user)
        db_session.commit()

        # Try to reset with expired token
        result = auth.reset_password(
            db=db_session,
            token=token,
            new_password="newpassword456"
        )

        assert result is None


@pytest.mark.unit
class TestGenerateToken:
    """Tests for generate_token function"""

    def test_generate_token_returns_string(self):
        """Test that generate_token returns a string"""
        token = auth.generate_token()
        assert isinstance(token, str)
        assert len(token) > 0

    def test_generate_token_is_unique(self):
        """Test that generate_token generates unique tokens"""
        tokens = [auth.generate_token() for _ in range(100)]
        # All tokens should be unique
        assert len(tokens) == len(set(tokens))

    def test_generate_token_is_url_safe(self):
        """Test that generated token is URL-safe"""
        token = auth.generate_token()
        # URL-safe base64 should only contain alphanumeric, -, and _
        assert all(c.isalnum() or c in ['-', '_'] for c in token)
