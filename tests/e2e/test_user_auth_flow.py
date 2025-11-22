"""
E2E test for complete user authentication flow:
User registration → email verification → login → logout
"""
import pytest
from unittest.mock import patch, Mock
from app.models.user import User


@pytest.mark.e2e
class TestUserAuthenticationFlow:
    """E2E tests for complete user authentication journey"""

    @pytest.mark.asyncio
    async def test_complete_user_registration_and_login_flow(self, client, db_session):
        """
        Test complete user journey from registration to login

        Flow:
        1. User registers with email/password
        2. System sends verification email
        3. User clicks verification link
        4. User logs in successfully
        5. User can access protected pages
        """

        # Step 1: User visits registration page
        response = client.get("/auth/register")
        assert response.status_code == 200
        assert b"Sign Up" in response.content or b"Register" in response.content

        # Step 2: User submits registration form
        registration_data = {
            "full_name": "New Test User",
            "email": "newuser@example.com",
            "password": "SecurePass123!",
            "confirm_password": "SecurePass123!"
        }

        # Mock email sending
        with patch('app.services.auth.send_verification_email') as mock_send_email:
            mock_send_email.return_value = True

            response = client.post("/auth/register", data=registration_data)

            # Should redirect to email sent page or show success message
            assert response.status_code in [200, 302, 303]

            # Verify user was created in database
            user = db_session.query(User).filter(User.email == "newuser@example.com").first()
            assert user is not None
            assert user.full_name == "New Test User"
            assert user.is_verified is False  # Not yet verified
            assert user.verification_token is not None

            # Verify email was sent
            mock_send_email.assert_called_once()

            verification_token = user.verification_token

        # Step 3: User cannot login before verification
        login_data = {
            "email": "newuser@example.com",
            "password": "SecurePass123!"
        }
        response = client.post("/auth/login", data=login_data)

        # Should fail or redirect back to login with error
        # Check user is not logged in
        dashboard_response = client.get("/")
        # Should redirect to login if not authenticated
        assert dashboard_response.status_code in [302, 303, 401]

        # Step 4: User clicks verification link in email
        response = client.get(f"/auth/verify?token={verification_token}")

        # Should redirect to login or show success message
        assert response.status_code in [200, 302, 303]

        # Verify user is now verified
        db_session.expire_all()  # Clear cache
        user = db_session.query(User).filter(User.email == "newuser@example.com").first()
        assert user.is_verified is True
        assert user.verification_token is None  # Token should be cleared

        # Step 5: User logs in successfully
        response = client.post("/auth/login", data=login_data, follow_redirects=False)

        # Should set session cookie and redirect to dashboard
        assert response.status_code in [200, 302, 303]

        # Verify session cookie was set
        assert "session" in client.cookies or "user_session" in client.cookies

        # Step 6: User can access protected pages
        response = client.get("/")
        assert response.status_code == 200
        # Dashboard should show user's name
        assert b"New Test User" in response.content or b"newuser@example.com" in response.content

        # Step 7: User can access entries page
        response = client.get("/entries/")
        assert response.status_code == 200

        # Step 8: User can logout
        response = client.post("/auth/logout")
        assert response.status_code in [200, 302, 303]

        # Step 9: After logout, user cannot access protected pages
        client.cookies.clear()
        response = client.get("/")
        # Should redirect to login
        assert response.status_code in [302, 303, 401]

    @pytest.mark.asyncio
    async def test_login_with_remember_me(self, client, db_session, test_user):
        """
        Test login with 'remember me' option

        Flow:
        1. User logs in with 'remember me' checked
        2. Session cookie should have extended expiry
        3. User remains logged in across browser sessions
        """

        login_data = {
            "email": test_user.email,
            "password": "testpassword123",
            "remember_me": "on"
        }

        response = client.post("/auth/login", data=login_data, follow_redirects=False)
        assert response.status_code in [200, 302, 303]

        # Verify user can access dashboard
        response = client.get("/")
        assert response.status_code == 200

        # Session cookie should persist
        assert "session" in client.cookies or "user_session" in client.cookies

    @pytest.mark.asyncio
    async def test_password_reset_flow(self, client, db_session, test_user):
        """
        Test complete password reset flow

        Flow:
        1. User clicks 'Forgot Password'
        2. User enters email
        3. System sends reset email
        4. User clicks reset link
        5. User enters new password
        6. User logs in with new password
        """

        # Step 1: User visits forgot password page
        response = client.get("/auth/forgot-password")
        assert response.status_code == 200
        assert b"Forgot Password" in response.content or b"Reset Password" in response.content

        # Step 2: User submits email
        with patch('app.services.auth.send_password_reset_email') as mock_send_email:
            mock_send_email.return_value = True

            response = client.post("/auth/forgot-password", data={"email": test_user.email})
            assert response.status_code in [200, 302, 303]

            # Verify reset token was created
            db_session.expire_all()
            user = db_session.query(User).filter(User.id == test_user.id).first()
            assert user.reset_password_token is not None

            reset_token = user.reset_password_token

        # Step 3: User clicks reset link in email
        response = client.get(f"/auth/reset-password?token={reset_token}")
        assert response.status_code == 200
        assert b"Reset Password" in response.content or b"New Password" in response.content

        # Step 4: User enters new password
        new_password_data = {
            "password": "NewSecurePass456!",
            "confirm_password": "NewSecurePass456!"
        }

        response = client.post(f"/auth/reset-password?token={reset_token}", data=new_password_data)
        assert response.status_code in [200, 302, 303]

        # Verify reset token was cleared
        db_session.expire_all()
        user = db_session.query(User).filter(User.id == test_user.id).first()
        assert user.reset_password_token is None

        # Step 5: User logs in with NEW password
        login_data = {
            "email": test_user.email,
            "password": "NewSecurePass456!"
        }

        response = client.post("/auth/login", data=login_data)
        assert response.status_code in [200, 302, 303]

        # Verify user can access dashboard
        response = client.get("/")
        assert response.status_code == 200

        # Step 6: User CANNOT login with old password
        client.cookies.clear()
        old_login_data = {
            "email": test_user.email,
            "password": "testpassword123"
        }

        response = client.post("/auth/login", data=old_login_data)
        # Should fail or redirect back to login

        # Verify user is not logged in
        response = client.get("/")
        assert response.status_code in [302, 303, 401]

    @pytest.mark.asyncio
    async def test_invalid_verification_token(self, client, db_session):
        """Test user cannot verify with invalid or expired token"""

        # Try to verify with invalid token
        response = client.get("/auth/verify?token=invalid_token_xyz")

        # Should show error or redirect to login
        assert response.status_code in [200, 302, 303, 400, 404]

        # Should contain error message if 200
        if response.status_code == 200:
            assert b"invalid" in response.content.lower() or b"expired" in response.content.lower()

    @pytest.mark.asyncio
    async def test_duplicate_email_registration(self, client, db_session, test_user):
        """Test user cannot register with already existing email"""

        registration_data = {
            "full_name": "Duplicate User",
            "email": test_user.email,  # Email already exists
            "password": "SecurePass123!",
            "confirm_password": "SecurePass123!"
        }

        response = client.post("/auth/register", data=registration_data)

        # Should fail with error
        assert response.status_code in [200, 400, 422]

        # Should contain error message
        if response.status_code == 200:
            assert b"already exists" in response.content.lower() or b"already registered" in response.content.lower()
