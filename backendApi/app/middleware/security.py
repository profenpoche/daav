"""
Security middleware for the DAAV application.
"""
import time
import logging
from typing import Dict, Set
from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from collections import defaultdict, deque
from datetime import datetime, timedelta

from app.config.settings import settings
from app.config.security import log_security_event, SecurityConfig

logger = logging.getLogger(__name__)


class SecurityMiddleware(BaseHTTPMiddleware):
    """Security middleware to monitor and limit requests."""
    
    def __init__(self, app, rate_limit: int = 100, time_window: int = 60):
        """
        Args:
            app: FastAPI application
            rate_limit: Max number of requests per time window
            time_window: Time window in seconds
        """
        super().__init__(app)
        self.rate_limit = rate_limit
        self.time_window = time_window
        
        # Request storage by IP
        self.request_counts: Dict[str, deque] = defaultdict(deque)
        
        # Temporarily blocked IPs
        self.blocked_ips: Dict[str, datetime] = {}
        
        # Suspicious patterns to monitor (imported from config)
        self.suspicious_patterns = list(SecurityConfig.DANGEROUS_PATH_PATTERNS) + [
            'passwd', 'shadow', 'hosts'
        ]
    
    async def dispatch(self, request: Request, call_next):
        """Request processing with security checks."""
        client_ip = self._get_client_ip(request)
        
        # Check if IP is blocked
        if self._is_ip_blocked(client_ip):
            log_security_event(
                "BLOCKED_IP_ACCESS", 
                f"Blocked IP {client_ip} attempted access",
                "WARNING"
            )
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests. IP temporarily blocked."}
            )
        
        # Rate limiting
        if self._check_rate_limit(client_ip):
            self._block_ip(client_ip)
            log_security_event(
                "RATE_LIMIT_EXCEEDED", 
                f"IP {client_ip} exceeded rate limit",
                "WARNING"
            )
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded"}
            )
        
        # Analyze request for suspicious patterns
        if self._detect_suspicious_patterns(request):
            log_security_event(
                "SUSPICIOUS_PATTERN_DETECTED",
                f"Suspicious pattern in request from {client_ip}: {request.url.path}",
                "ERROR"
            )
            return JSONResponse(
                status_code=400,
                content={"detail": "Suspicious request pattern detected"}
            )
        
        # Check request size
        if self._check_request_size(request):
            log_security_event(
                "LARGE_REQUEST_DETECTED",
                f"Large request from {client_ip}",
                "WARNING"
            )
            return JSONResponse(
                status_code=413,
                content={"detail": "Request too large"}
            )
        
        # Process request
        start_time = time.time()
        try:
            response = await call_next(request)
            
            # Log file access
            if any(path in str(request.url.path) for path in ['/datasets/', '/upload']):
                log_security_event(
                    "FILE_ACCESS",
                    f"File access from {client_ip}: {request.url.path}",
                    "INFO"
                )
            
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            log_security_event(
                "REQUEST_ERROR",
                f"Error processing request from {client_ip}: {str(e)} (time: {process_time:.2f}s)",
                "ERROR"
            )
            raise
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP."""
        # Check proxy headers
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"
    
    def _check_rate_limit(self, ip: str) -> bool:
        """Check rate limiting."""
        now = datetime.now()
        cutoff = now - timedelta(seconds=self.time_window)
        
        # Clean old requests
        requests = self.request_counts[ip]
        while requests and requests[0] < cutoff:
            requests.popleft()
        
        # Add new request
        requests.append(now)
        
        # Check limit
        return len(requests) > self.rate_limit
    
    def _is_ip_blocked(self, ip: str) -> bool:
        """Check if an IP is blocked."""
        if ip in self.blocked_ips:
            # Check if block has expired (1 hour)
            if datetime.now() - self.blocked_ips[ip] > timedelta(hours=1):
                del self.blocked_ips[ip]
                return False
            return True
        return False
    
    def _block_ip(self, ip: str):
        """Temporarily block an IP."""
        self.blocked_ips[ip] = datetime.now()
    
    def _detect_suspicious_patterns(self, request: Request) -> bool:
        """Detect suspicious patterns in request."""
        # Check URL
        url_path = str(request.url.path).lower()
        query_params = str(request.url.query).lower()
        
        # Check suspicious patterns
        for pattern in self.suspicious_patterns:
            if pattern.lower() in url_path or pattern.lower() in query_params:
                return True
        
        # Check suspicious headers
        for header, value in request.headers.items():
            if any(pattern.lower() in value.lower() for pattern in self.suspicious_patterns):
                return True
        
        return False
    
    def _check_request_size(self, request: Request) -> bool:
        """Check request size."""
        # We can upload multiple file 10* limit size
        max_size = 10 * settings.max_file_size  # Convert to bytes
        
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                size = int(content_length)
                return size > max_size
            except ValueError:
                return False
        
        return False


class FileAccessMonitor:
    """File access monitor."""
    
    def __init__(self):
        self.access_log: Dict[str, list] = defaultdict(list)
    
    def log_file_access(self, ip: str, file_path: str, action: str):
        """Log a file access."""
        access_record = {
            'timestamp': datetime.now().isoformat(),
            'ip': ip,
            'file_path': file_path,
            'action': action
        }
        
        self.access_log[ip].append(access_record)
        
        # Log every file access to security.log with file info
        log_security_event(
            "FILE_ACCESS",
            f"File access from {ip}: action={action}, file={file_path}",
            "INFO"
        )
        
        # Clean old logs (keep only 24h)
        cutoff = datetime.now() - timedelta(hours=24)
        self.access_log[ip] = [
            record for record in self.access_log[ip]
            if datetime.fromisoformat(record['timestamp']) > cutoff
        ]
        
        # Detect suspicious access
        if self._is_suspicious_access_pattern(ip):
            log_security_event(
                "SUSPICIOUS_FILE_ACCESS_PATTERN",
                f"Suspicious file access pattern detected for IP {ip}",
                "CRITICAL"
            )
    
    def _is_suspicious_access_pattern(self, ip: str) -> bool:
        """Detect suspicious access patterns."""
        recent_accesses = self.access_log.get(ip, [])
        
        # More than 50 file accesses in 10 minutes
        recent_cutoff = datetime.now() - timedelta(minutes=10)
        recent_count = sum(
            1 for record in recent_accesses
            if datetime.fromisoformat(record['timestamp']) > recent_cutoff
        )
        
        if recent_count > 50:
            return True
        
        # Access to suspicious paths
        suspicious_paths = ['/etc/', '/proc/', '/sys/', 'C:\\Windows', '..']
        for record in recent_accesses[-10:]:  # Check last 10 accesses
            # Defensive check: file_path might be None (e.g., URN-based files)
            file_path = record.get('file_path')
            if file_path and any(suspect in file_path for suspect in suspicious_paths):
                return True
        
        return False


# Global monitor instance
file_access_monitor = FileAccessMonitor()


def log_file_access(ip: str, file_path: str, action: str = "read"):
    """Helper function to log file accesses."""
    file_access_monitor.log_file_access(ip, file_path, action)
