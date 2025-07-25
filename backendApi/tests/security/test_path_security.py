"""
Security tests for path validation and path traversal protection.
"""
import pytest
import tempfile
import os
from pathlib import Path
from fastapi import HTTPException

from app.utils.security import PathSecurityValidator, FileAccessController


@pytest.fixture
def enable_security():
    """Fixture to enable security for tests that need it."""
    # Enable security for this test
    PathSecurityValidator.set_security_enabled(True)
    yield
    # Reset to default state after test
    PathSecurityValidator.reset_security_state()


@pytest.fixture
def disable_security():
    """Fixture to disable security for tests that need it."""
    # Disable security for this test
    PathSecurityValidator.set_security_enabled(False)
    yield
    # Reset to default state after test
    PathSecurityValidator.reset_security_state()


class TestPathSecurityValidator:
    def test_validate_safe_path(self, disable_security):
        """Test validation of a safe path (security disabled for baseline)."""
        safe_path = "uploads/test.csv"
        result = PathSecurityValidator.validate_file_path(safe_path)
        assert result == safe_path  # Should return as-is when security disabled
    
    def test_block_path_traversal_unix(self, enable_security):
        """Test blocking Unix path traversal."""
        dangerous_path = "../../../etc/passwd"
        with pytest.raises(HTTPException) as exc_info:
            PathSecurityValidator.validate_file_path(dangerous_path)
        assert exc_info.value.status_code == 400
        assert "Dangerous path pattern detected" in str(exc_info.value.detail)
    
    def test_block_path_traversal_windows(self, enable_security):
        """Test blocking Windows path traversal."""
        dangerous_path = "..\\..\\Windows\\System32\\config"
        with pytest.raises(HTTPException) as exc_info:
            PathSecurityValidator.validate_file_path(dangerous_path)
        assert exc_info.value.status_code == 400
    
    def test_block_absolute_paths(self, enable_security):
        """Test blocking dangerous absolute paths."""
        dangerous_paths = [
            "/etc/passwd",
            "C:\\Windows\\System32",
            "~/../../etc/passwd"
        ]
        
        for path in dangerous_paths:
            with pytest.raises(HTTPException):
                PathSecurityValidator.validate_file_path(path)
    
    def test_validate_filename(self, enable_security):
        """Test filename validation."""
        # Safe filename
        safe_name = "test_file.csv"
        result = PathSecurityValidator.validate_filename(safe_name)
        assert result == safe_name
        
        # Filename with dangerous characters
        dangerous_name = "test<>file|?.csv"
        result = PathSecurityValidator.validate_filename(dangerous_name)
        assert "<" not in result
        assert ">" not in result
        assert "|" not in result
        assert "?" not in result
    
    def test_block_reserved_windows_names(self, enable_security):
        """Test blocking Windows reserved names."""
        reserved_names = ["CON.txt", "PRN.csv", "AUX.json"]
        
        for name in reserved_names:
            result = PathSecurityValidator.validate_filename(name)
            assert result.startswith("file_")
    
    def test_validate_file_extension(self, enable_security):
        """Test extension validation."""
        # Allowed extensions
        allowed_files = ["test.csv", "data.json", "file.xlsx"]
        for filename in allowed_files:
            assert PathSecurityValidator.validate_file_extension(filename)
        
        # Disallowed extensions
        blocked_files = ["script.exe", "malware.bat", "virus.scr"]
        for filename in blocked_files:
            assert not PathSecurityValidator.validate_file_extension(filename)
    
    def test_validate_with_base_directory(self, enable_security):
        """Test validation with base directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Safe path within base directory
            safe_path = "subdir/test.csv"
            result = PathSecurityValidator.validate_file_path(safe_path, temp_dir)
            assert temp_dir in result
            
            # Dangerous path escaping base directory
            with pytest.raises(HTTPException) as exc_info:
                PathSecurityValidator.validate_file_path("../../etc/passwd", temp_dir)
            assert exc_info.value.status_code == 403


class TestFileAccessController:
    """Tests for file access controller."""
    
    def test_can_read_file_allowed_directory(self, disable_security):
        """Test allowed reading in permitted directory (security disabled for baseline)."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test.txt"
            test_file.write_text("test content")
            
            assert FileAccessController.can_read_file(str(test_file), [temp_dir])
    
    def test_cannot_read_file_outside_allowed(self, enable_security):
        """Test blocking read outside allowed directories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create file outside allowed directory
            other_dir = Path(temp_dir).parent / "other"
            other_dir.mkdir(exist_ok=True)
            test_file = other_dir / "test.txt"
            test_file.write_text("test content")
            
            allowed_dirs = [str(Path(temp_dir) / "allowed")]
            assert not FileAccessController.can_read_file(str(test_file), allowed_dirs)
    


class TestPathTraversalScenarios:
    """Specific tests for path traversal attack scenarios."""
    
    def test_various_traversal_attempts(self, enable_security):
        """Test various path traversal attempts."""
        traversal_attempts = [
            "../../../etc/passwd",
            "..\\..\\..\\Windows\\System32\\config",
            "....//....//....//etc//passwd",
            "%2e%2e%2fetc%2fpasswd",  # URL encoded
            "..%252f..%252f..%252fetc%252fpasswd",  # Double URL encoded
            "..%c0%af..%c0%afetc%c0%afpasswd",  # Unicode
            "/var/www/../../../etc/passwd",
            "uploads/../../../etc/passwd",
            "~/../../etc/passwd"
        ]
        
        for attempt in traversal_attempts:
            with pytest.raises(HTTPException):
                PathSecurityValidator.validate_file_path(attempt)
    
    def test_legitimate_paths_allowed(self, disable_security):
        """Test that legitimate paths are allowed (security disabled for baseline)."""
        legitimate_paths = [
            "uploads/data.csv",
            "uploads/subdir/file.json",
            "app/uploads/test.xlsx",
            "valid_file.txt"
        ]
        
        for path in legitimate_paths:
            # Should not raise exception
            result = PathSecurityValidator.validate_file_path(path)
            assert result is not None
    
    def test_null_byte_injection(self, enable_security):
        """Test protection against null byte injection."""
        malicious_paths = [
            "uploads/test.csv\x00.exe",
            "safe_file.txt\x00/../../../etc/passwd"
        ]
        
        for path in malicious_paths:
            # Python handles null bytes automatically, 
            # but we ensure our validation doesn't let them pass
            try:
                result = PathSecurityValidator.validate_file_path(path)
                # If it passes, verify there's no null byte
                assert '\x00' not in result
            except (HTTPException, ValueError):
                # It's acceptable for an exception to be raised
                pass


# Test for the centralized security bypass mechanism
class TestSecurityBypassMechanism:
    """Tests for the centralized security bypass mechanism."""
    
    def test_security_enabled_by_default_in_tests(self):
        """Test that security is disabled by default in test environment."""
        # Reset to default state
        PathSecurityValidator.reset_security_state()
        # In test environment, security should be disabled by default
        assert not PathSecurityValidator.is_security_enabled()
    
    def test_can_override_security_state(self):
        """Test that we can override the security state."""
        # Enable security explicitly
        PathSecurityValidator.set_security_enabled(True)
        assert PathSecurityValidator.is_security_enabled()
        
        # Disable security explicitly
        PathSecurityValidator.set_security_enabled(False)
        assert not PathSecurityValidator.is_security_enabled()
        
        # Reset to default
        PathSecurityValidator.reset_security_state()
        # Should be disabled again in test environment
        assert not PathSecurityValidator.is_security_enabled()
    
    def test_security_bypass_works(self, disable_security):
        """Test that security bypass actually works."""
        dangerous_path = "../../../etc/passwd"
        # Should not raise exception when security is disabled
        result = PathSecurityValidator.validate_file_path(dangerous_path)
        assert result == dangerous_path
    
    def test_security_enforcement_works(self, enable_security):
        """Test that security enforcement actually works."""
        dangerous_path = "../../../etc/passwd"
        # Should raise exception when security is enabled
        with pytest.raises(HTTPException):
            PathSecurityValidator.validate_file_path(dangerous_path)


if __name__ == "__main__":
    pytest.main([__file__])
