"""
Tests for EmailService

This module tests email sending functionality including:
- Generic email sending
- Password reset emails
- SMTP configuration handling
- Error handling
"""

import pytest
import pytest_asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from app.services.email_service import EmailService


@pytest.fixture
def email_service_instance():
    """Get EmailService instance (singleton)"""
    return EmailService()


@pytest.fixture
def mock_smtp_settings():
    """Mock SMTP settings"""
    with patch('app.services.email_service.settings') as mock_settings:
        mock_settings.smtp_host = "smtp.example.com"
        mock_settings.smtp_port = 587
        mock_settings.smtp_username = "test@example.com"
        mock_settings.smtp_password = "test_password"
        mock_settings.smtp_from_email = "noreply@example.com"
        mock_settings.smtp_from_name = "DAAV Test"
        mock_settings.smtp_use_tls = True
        mock_settings.frontend_url = "http://localhost:4200"
        mock_settings.password_reset_token_expire_hours = 24
        yield mock_settings


# ============================================
# SEND EMAIL TESTS
# ============================================

@pytest.mark.asyncio
async def test_send_email_success(email_service_instance, mock_smtp_settings):
    """Test successful email sending"""
    with patch('app.services.email_service.aiosmtplib.send', new_callable=AsyncMock) as mock_send:
        # Force reload service with mocked settings
        email_service_instance.smtp_username = mock_smtp_settings.smtp_username
        email_service_instance.smtp_password = mock_smtp_settings.smtp_password
        email_service_instance.smtp_host = mock_smtp_settings.smtp_host
        email_service_instance.smtp_port = mock_smtp_settings.smtp_port
        
        result = await email_service_instance.send_email(
            to_email="user@example.com",
            subject="Test Subject",
            body="Test body content"
        )
        
        assert result is True
        mock_send.assert_called_once()


@pytest.mark.asyncio
async def test_send_email_with_html(email_service_instance, mock_smtp_settings):
    """Test email sending with HTML body"""
    with patch('app.services.email_service.aiosmtplib.send', new_callable=AsyncMock) as mock_send:
        email_service_instance.smtp_username = mock_smtp_settings.smtp_username
        email_service_instance.smtp_password = mock_smtp_settings.smtp_password
        email_service_instance.smtp_host = mock_smtp_settings.smtp_host
        email_service_instance.smtp_port = mock_smtp_settings.smtp_port
        
        result = await email_service_instance.send_email(
            to_email="user@example.com",
            subject="Test Subject",
            body="Plain text body",
            html_body="<html><body><h1>Test HTML</h1></body></html>"
        )
        
        assert result is True
        mock_send.assert_called_once()
        
        # Verify message was created with both parts
        call_args = mock_send.call_args
        message = call_args[0][0]
        assert message["Subject"] == "Test Subject"
        assert message["To"] == "user@example.com"


@pytest.mark.asyncio
async def test_send_email_smtp_not_configured(email_service_instance):
    """Test email sending when SMTP is not configured"""
    # Simulate no SMTP configuration
    email_service_instance.smtp_username = None
    email_service_instance.smtp_password = None
    
    result = await email_service_instance.send_email(
        to_email="user@example.com",
        subject="Test Subject",
        body="Test body"
    )
    
    # Should return False when not configured
    assert result is False


@pytest.mark.asyncio
async def test_send_email_smtp_error(email_service_instance, mock_smtp_settings):
    """Test email sending with SMTP connection error"""
    with patch('app.services.email_service.aiosmtplib.send', new_callable=AsyncMock) as mock_send:
        email_service_instance.smtp_username = mock_smtp_settings.smtp_username
        email_service_instance.smtp_password = mock_smtp_settings.smtp_password
        
        # Simulate SMTP error
        mock_send.side_effect = Exception("SMTP connection failed")
        
        result = await email_service_instance.send_email(
            to_email="user@example.com",
            subject="Test Subject",
            body="Test body"
        )
        
        assert result is False


@pytest.mark.asyncio
async def test_send_email_authentication_error(email_service_instance, mock_smtp_settings):
    """Test email sending with authentication error"""
    with patch('app.services.email_service.aiosmtplib.send', new_callable=AsyncMock) as mock_send:
        email_service_instance.smtp_username = mock_smtp_settings.smtp_username
        email_service_instance.smtp_password = mock_smtp_settings.smtp_password
        
        # Simulate authentication error
        mock_send.side_effect = Exception("Authentication failed")
        
        result = await email_service_instance.send_email(
            to_email="user@example.com",
            subject="Test Subject",
            body="Test body"
        )
        
        assert result is False


@pytest.mark.asyncio
async def test_send_email_invalid_recipient(email_service_instance, mock_smtp_settings):
    """Test email sending with invalid recipient"""
    with patch('app.services.email_service.aiosmtplib.send', new_callable=AsyncMock) as mock_send:
        email_service_instance.smtp_username = mock_smtp_settings.smtp_username
        email_service_instance.smtp_password = mock_smtp_settings.smtp_password
        
        # Simulate invalid recipient error
        mock_send.side_effect = Exception("Invalid recipient")
        
        result = await email_service_instance.send_email(
            to_email="invalid-email",
            subject="Test Subject",
            body="Test body"
        )
        
        assert result is False


# ============================================
# PASSWORD RESET EMAIL TESTS
# ============================================

@pytest.mark.asyncio
async def test_send_password_reset_email_success(email_service_instance, mock_smtp_settings):
    """Test sending password reset email"""
    with patch('app.services.email_service.aiosmtplib.send', new_callable=AsyncMock) as mock_send:
        email_service_instance.smtp_username = mock_smtp_settings.smtp_username
        email_service_instance.smtp_password = mock_smtp_settings.smtp_password
        email_service_instance.smtp_host = mock_smtp_settings.smtp_host
        email_service_instance.smtp_port = mock_smtp_settings.smtp_port
        
        result = await email_service_instance.send_password_reset_email(
            to_email="user@example.com",
            username="testuser",
            reset_token="test_token_123"
        )
        
        assert result is True
        mock_send.assert_called_once()
        
        # Verify email content
        call_args = mock_send.call_args
        message = call_args[0][0]
        assert "Reset Your Password" in message["Subject"]
        assert message["To"] == "user@example.com"


@pytest.mark.asyncio
async def test_password_reset_email_contains_link(email_service_instance, mock_smtp_settings):
    """Test password reset email contains correct reset link"""
    with patch('app.services.email_service.aiosmtplib.send', new_callable=AsyncMock) as mock_send:
        email_service_instance.smtp_username = mock_smtp_settings.smtp_username
        email_service_instance.smtp_password = mock_smtp_settings.smtp_password
        email_service_instance.smtp_host = mock_smtp_settings.smtp_host
        email_service_instance.smtp_port = mock_smtp_settings.smtp_port
        
        reset_token = "unique_reset_token_456"
        
        result = await email_service_instance.send_password_reset_email(
            to_email="user@example.com",
            username="testuser",
            reset_token=reset_token
        )
        
        assert result is True
        
        # Verify the message contains the reset token in the link
        call_args = mock_send.call_args
        message = call_args[0][0]
        message_str = str(message)
        assert reset_token in message_str
        assert mock_smtp_settings.frontend_url in message_str


@pytest.mark.asyncio
async def test_password_reset_email_contains_username(email_service_instance, mock_smtp_settings):
    """Test password reset email contains username"""
    with patch('app.services.email_service.aiosmtplib.send', new_callable=AsyncMock) as mock_send:
        email_service_instance.smtp_username = mock_smtp_settings.smtp_username
        email_service_instance.smtp_password = mock_smtp_settings.smtp_password
        email_service_instance.smtp_host = mock_smtp_settings.smtp_host
        email_service_instance.smtp_port = mock_smtp_settings.smtp_port
        
        username = "john_doe"
        
        result = await email_service_instance.send_password_reset_email(
            to_email="john@example.com",
            username=username,
            reset_token="token_123"
        )
        
        assert result is True
        
        # Verify username is in the email
        call_args = mock_send.call_args
        message = call_args[0][0]
        message_str = str(message)
        assert username in message_str


@pytest.mark.asyncio
async def test_password_reset_email_contains_expiry(email_service_instance, mock_smtp_settings):
    """Test password reset email mentions token expiry"""
    with patch('app.services.email_service.aiosmtplib.send', new_callable=AsyncMock) as mock_send:
        email_service_instance.smtp_username = mock_smtp_settings.smtp_username
        email_service_instance.smtp_password = mock_smtp_settings.smtp_password
        email_service_instance.smtp_host = mock_smtp_settings.smtp_host
        email_service_instance.smtp_port = mock_smtp_settings.smtp_port
        
        result = await email_service_instance.send_password_reset_email(
            to_email="user@example.com",
            username="testuser",
            reset_token="token_123"
        )
        
        assert result is True
        
        # Verify expiry time is mentioned
        call_args = mock_send.call_args
        message = call_args[0][0]
        message_str = str(message)
        assert str(mock_smtp_settings.password_reset_token_expire_hours) in message_str


@pytest.mark.asyncio
async def test_password_reset_email_smtp_failure(email_service_instance, mock_smtp_settings):
    """Test password reset email with SMTP failure"""
    with patch('app.services.email_service.aiosmtplib.send', new_callable=AsyncMock) as mock_send:
        email_service_instance.smtp_username = mock_smtp_settings.smtp_username
        email_service_instance.smtp_password = mock_smtp_settings.smtp_password
        
        # Simulate SMTP failure
        mock_send.side_effect = Exception("SMTP server unavailable")
        
        result = await email_service_instance.send_password_reset_email(
            to_email="user@example.com",
            username="testuser",
            reset_token="token_123"
        )
        
        assert result is False


@pytest.mark.asyncio
async def test_password_reset_email_not_configured(email_service_instance):
    """Test password reset email when SMTP not configured"""
    email_service_instance.smtp_username = None
    email_service_instance.smtp_password = None
    
    result = await email_service_instance.send_password_reset_email(
        to_email="user@example.com",
        username="testuser",
        reset_token="token_123"
    )
    
    # Should return False when not configured
    assert result is False


# ============================================
# EMAIL FORMAT TESTS
# ============================================

@pytest.mark.asyncio
async def test_email_has_correct_from_address(email_service_instance, mock_smtp_settings):
    """Test email has correct From address"""
    with patch('app.services.email_service.aiosmtplib.send', new_callable=AsyncMock) as mock_send:
        email_service_instance.smtp_username = mock_smtp_settings.smtp_username
        email_service_instance.smtp_password = mock_smtp_settings.smtp_password
        email_service_instance.smtp_host = mock_smtp_settings.smtp_host
        email_service_instance.smtp_port = mock_smtp_settings.smtp_port
        email_service_instance.smtp_from_email = mock_smtp_settings.smtp_from_email
        email_service_instance.smtp_from_name = mock_smtp_settings.smtp_from_name
        
        result = await email_service_instance.send_email(
            to_email="user@example.com",
            subject="Test",
            body="Test"
        )
        
        assert result is True
        call_args = mock_send.call_args
        message = call_args[0][0]
        assert mock_smtp_settings.smtp_from_email in message["From"]
        assert mock_smtp_settings.smtp_from_name in message["From"]


@pytest.mark.asyncio
async def test_email_multipart_structure(email_service_instance, mock_smtp_settings):
    """Test email has proper multipart structure with HTML"""
    with patch('app.services.email_service.aiosmtplib.send', new_callable=AsyncMock) as mock_send:
        email_service_instance.smtp_username = mock_smtp_settings.smtp_username
        email_service_instance.smtp_password = mock_smtp_settings.smtp_password
        email_service_instance.smtp_host = mock_smtp_settings.smtp_host
        email_service_instance.smtp_port = mock_smtp_settings.smtp_port
        
        result = await email_service_instance.send_email(
            to_email="user@example.com",
            subject="Test",
            body="Plain text",
            html_body="<html><body>HTML content</body></html>"
        )
        
        assert result is True
        call_args = mock_send.call_args
        message = call_args[0][0]
        
        # Check message is multipart
        assert message.is_multipart()


@pytest.mark.asyncio
async def test_email_plain_text_only(email_service_instance, mock_smtp_settings):
    """Test email with plain text only (no HTML)"""
    with patch('app.services.email_service.aiosmtplib.send', new_callable=AsyncMock) as mock_send:
        email_service_instance.smtp_username = mock_smtp_settings.smtp_username
        email_service_instance.smtp_password = mock_smtp_settings.smtp_password
        email_service_instance.smtp_host = mock_smtp_settings.smtp_host
        email_service_instance.smtp_port = mock_smtp_settings.smtp_port
        
        result = await email_service_instance.send_email(
            to_email="user@example.com",
            subject="Test",
            body="Plain text only"
        )
        
        assert result is True
        call_args = mock_send.call_args
        message = call_args[0][0]
        
        # Should still be multipart but with only text part
        assert message["Subject"] == "Test"


# ============================================
# SMTP CONFIGURATION TESTS
# ============================================

@pytest.mark.asyncio
async def test_smtp_connection_parameters(email_service_instance, mock_smtp_settings):
    """Test SMTP connection uses correct parameters"""
    with patch('app.services.email_service.aiosmtplib.send', new_callable=AsyncMock) as mock_send:
        email_service_instance.smtp_username = mock_smtp_settings.smtp_username
        email_service_instance.smtp_password = mock_smtp_settings.smtp_password
        email_service_instance.smtp_host = mock_smtp_settings.smtp_host
        email_service_instance.smtp_port = mock_smtp_settings.smtp_port
        email_service_instance.smtp_use_tls = mock_smtp_settings.smtp_use_tls
        
        await email_service_instance.send_email(
            to_email="user@example.com",
            subject="Test",
            body="Test"
        )
        
        mock_send.assert_called_once()
        call_kwargs = mock_send.call_args[1]
        
        assert call_kwargs["hostname"] == mock_smtp_settings.smtp_host
        assert call_kwargs["port"] == mock_smtp_settings.smtp_port
        assert call_kwargs["username"] == mock_smtp_settings.smtp_username
        assert call_kwargs["password"] == mock_smtp_settings.smtp_password
        assert call_kwargs["use_tls"] == mock_smtp_settings.smtp_use_tls


@pytest.mark.asyncio
async def test_smtp_tls_disabled(email_service_instance, mock_smtp_settings):
    """Test SMTP connection with TLS disabled"""
    with patch('app.services.email_service.aiosmtplib.send', new_callable=AsyncMock) as mock_send:
        email_service_instance.smtp_username = mock_smtp_settings.smtp_username
        email_service_instance.smtp_password = mock_smtp_settings.smtp_password
        email_service_instance.smtp_host = mock_smtp_settings.smtp_host
        email_service_instance.smtp_port = mock_smtp_settings.smtp_port
        email_service_instance.smtp_use_tls = False
        
        await email_service_instance.send_email(
            to_email="user@example.com",
            subject="Test",
            body="Test"
        )
        
        call_kwargs = mock_send.call_args[1]
        assert call_kwargs["use_tls"] is False


# ============================================
# INTEGRATION TESTS
# ============================================

@pytest.mark.asyncio
async def test_multiple_emails_sequence(email_service_instance, mock_smtp_settings):
    """Test sending multiple emails in sequence"""
    with patch('app.services.email_service.aiosmtplib.send', new_callable=AsyncMock) as mock_send:
        email_service_instance.smtp_username = mock_smtp_settings.smtp_username
        email_service_instance.smtp_password = mock_smtp_settings.smtp_password
        email_service_instance.smtp_host = mock_smtp_settings.smtp_host
        email_service_instance.smtp_port = mock_smtp_settings.smtp_port
        
        # Send multiple emails
        result1 = await email_service_instance.send_email(
            to_email="user1@example.com",
            subject="Email 1",
            body="Body 1"
        )
        
        result2 = await email_service_instance.send_email(
            to_email="user2@example.com",
            subject="Email 2",
            body="Body 2"
        )
        
        result3 = await email_service_instance.send_password_reset_email(
            to_email="user3@example.com",
            username="user3",
            reset_token="token123"
        )
        
        assert result1 is True
        assert result2 is True
        assert result3 is True
        assert mock_send.call_count == 3


@pytest.mark.asyncio
async def test_email_service_singleton_pattern(email_service_instance):
    """Test EmailService follows singleton pattern"""
    # Create another instance
    another_instance = EmailService()
    
    # Should be the same instance
    assert email_service_instance is another_instance
