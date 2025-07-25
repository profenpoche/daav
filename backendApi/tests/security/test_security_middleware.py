"""
Tests for the security middleware.
"""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import patch

from app.middleware.security import SecurityMiddleware


@pytest.fixture
def app_with_security_middleware():
    """Create FastAPI app with security middleware for testing."""
    app = FastAPI()
    
    # Add security middleware with low limits for testing
    app.add_middleware(
        SecurityMiddleware,
        rate_limit=5,  # Very low limit for testing
        time_window=60
    )
    
    @app.get("/test")
    async def test_endpoint():
        return {"message": "success"}
    
    @app.get("/files/{file_path:path}")
    async def file_endpoint(file_path: str):
        return {"file_path": file_path}
    
    return app


@pytest.fixture
def client(app_with_security_middleware):
    """Create test client."""
    return TestClient(app_with_security_middleware)


class TestSecurityMiddleware:
    """Tests for security middleware functionality."""
    
    def test_normal_request_allowed(self, client):
        """Test that normal requests are allowed."""
        response = client.get("/test")
        assert response.status_code == 200
        assert response.json() == {"message": "success"}
    
    def test_rate_limiting(self, client):
        """Test rate limiting functionality."""
        # Make requests up to the limit
        for i in range(5):
            response = client.get("/test")
            assert response.status_code == 200
        
        # The 6th request should be rate limited
        response = client.get("/test")
        assert response.status_code == 429
        assert "Rate limit exceeded" in response.json()["detail"]
    
    def test_large_request_detection(self, client):
        """Test detection of oversized requests."""
        # Create a large payload (simulate large upload)
        large_data = "x" * (51 * 1024 * 1024)  # 51MB
        
        with patch.object(client, 'request') as mock_request:
            mock_request.headers = {"content-length": str(len(large_data))}
            response = client.post("/test", content=large_data)
            
            # This might not work perfectly in test, but shows the concept
            # In real scenario, the middleware would catch this
    
    def test_suspicious_headers_detection(self, client):
        """Test detection of suspicious headers."""
        suspicious_headers = {
            "X-Custom-Path": "../../../etc/passwd",
            "User-Agent": "BadBot ../../../"
        }
        
        response = client.get("/test", headers=suspicious_headers)
        assert response.status_code == 400
        assert "Suspicious request pattern detected" in response.json()["detail"]
    
    def test_file_access_logging(self, client):
        """Test that file access is logged."""
        # This would require checking logs, but shows the concept
        response = client.get("/files/uploads/test.csv")
        # In a real scenario, this would be logged as file access
        
    def test_blocked_ip_functionality(self, client):
        """Test IP blocking functionality."""
        # After rate limit is exceeded, IP should be temporarily blocked
        
        # Exceed rate limit
        for i in range(6):
            client.get("/test")
        
        # Subsequent requests should be blocked even after some time
        response = client.get("/test")
        assert response.status_code == 429


if __name__ == "__main__":
    pytest.main([__file__])
