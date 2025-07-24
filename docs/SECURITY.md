# Security Guide - DAAV Backend

## 🚨 Identified and Fixed Vulnerabilities

### 1. Path Traversal / Directory Traversal
**Problem:** The system allowed access to files outside authorized directories via sequences like `../../../etc/passwd`.

**Implemented solutions:**
- ✅ Module `app/utils/security.py` with strict path validation
- ✅ Class `PathSecurityValidator` to sanitize and validate all paths
- ✅ Verification that files remain within authorized directories
- ✅ Blocking of dangerous patterns (`../`, `~/`, `/etc/`, etc.)

### 2. File Injection
**Problem:** File upload without validation allowing malicious file writing.

**Implemented solutions:**
- ✅ Validation of allowed file extensions
- ✅ Filename sanitization (removal of dangerous characters)
- ✅ File size limitation (1000MB by default)
- ✅ Validation of destination directories

### 3. Unrestricted Directory Access
**Problem:** Recursive reading of all files without restriction.

**Implemented solutions:**
- ✅ Whitelist of authorized directories
- ✅ Exclusion of system and hidden files

## 🛡️ Implemented Security Measures

### Path Validation (`PathSecurityValidator`)
```python
# Usage
validated_path = PathSecurityValidator.validate_file_path(user_input)
safe_filename = PathSecurityValidator.validate_filename(filename)
```

**Features:**
- Detection of dangerous patterns
- Path normalization
- Extension validation
- Base directory control

### Access Control (`FileAccessController`)
```python
# Access verification
can_access = FileAccessController.can_read_file(file_path, allowed_dirs)
content = FileAccessController.get_restricted_file_content(file_path, max_size)
```

**Features:**
- Verification of authorized directories
- File size limitation
- Permission management

### Security Middleware (`SecurityMiddleware`)

**Integration in main.py:**
```python
from app.middleware.security import SecurityMiddleware

# Add to your FastAPI app
app.add_middleware(
    SecurityMiddleware,
    rate_limit=100,  # Max requests per time window
    time_window=60   # Time window in seconds
)
```

**Configuration examples:**
```python
# Development (permissive)
app.add_middleware(SecurityMiddleware, rate_limit=1000, time_window=60)

# Production (balanced)
app.add_middleware(SecurityMiddleware, rate_limit=100, time_window=60)

# High security (strict)
app.add_middleware(SecurityMiddleware, rate_limit=50, time_window=60)
```

**Features:**
- ✅ Rate limiting (configurable req/min per IP)
- ✅ Path traversal detection (`../`, `/etc/`, etc.)
- ✅ Suspicious pattern detection (encoded attacks)
- ✅ Large request size blocking (>50MB)
- ✅ Temporary IP blocking (1 hour after violations)
- ✅ File access monitoring and logging
- ✅ Automatic security event logging

**What it blocks:**
- Path traversal: `../../../etc/passwd`
- Rate limits: >100 requests/minute from same IP
- Large uploads: >50MB requests
- Suspicious headers: Headers containing attack patterns
- System paths: `/etc/`, `/proc/`, `C:\Windows\`

## 📁 Authorized Directories

### Whitelist
- `uploads/` - Files uploaded by users
- `app/uploads/` - Alternative upload directory
- `app/ptx/` - PTX data
- `app/inputs/` - Input files

### Forbidden Directories
- `/etc/`, `/proc/`, `/sys/` (Unix)
- `C:\Windows\`, `C:\Users\` (Windows)  
- Any system or user directory

## 📄 Allowed File Extensions

### Data Formats
- `.csv`, `.tsv` - Tabular data files
- `.json` - JSON data
- `.xlsx`, `.xls` - Excel files
- `.parquet` - Parquet format
- `.avro` - Avro format
- `.feather`, `.orc` - Other data formats

### Text Formats
- `.txt` - Text files
- `.md` - Markdown
- `.yml`, `.yaml` - YAML configuration
- `.xml` - XML data
- `.log` - Log files

## 🔧 Configuration

### Environment Variables
```bash
# PDC Token (required for PDC authentication)
PDC_TOKEN=your_secure_token_here

# Upload directory (optional, default: uploads)
UPLOAD_DIR=uploads

# Max file size (optional, default: 100MB)
MAX_FILE_SIZE=100MB

# WhiteList directory who can bypass path restriction security
# Example by default /opt is not readeable to avoid unauthorized access to 3rd app conf
# You can add a sub directory on this list to avoid this exclusion to give access to subpath
DIRECTORY_WHITE_LIST=/opt/uploads,/opt/static
```

### Security Configuration
```python
# app/config/settings.py (existing configurations)
class Settings(BaseSettings):
    max_file_size: Union[int, str] = 100 * 1024 * 1024  # 100MB
    upload_dir: str = "uploads"

# app/config/security.py (security-specific configurations)
class SecurityConfig:
    ALLOWED_FILE_EXTENSIONS = {'.csv', '.json', '.parquet', ...}
    DANGEROUS_PATH_PATTERNS = [r'\.\./', r'\.\.\\', ...]
```

## 🔍 Monitoring and Logs

### Security Logs
Security events are logged in `security.log`:

```
[SECURITY] 2024-01-01 12:00:00 - WARNING - PATH_TRAVERSAL_BLOCKED: ../../../etc/passwd from IP 192.168.1.100
[SECURITY] 2024-01-01 12:01:00 - ERROR - SUSPICIOUS_PATTERN_DETECTED: Multiple path traversal attempts from IP 192.168.1.100
[SECURITY] 2024-01-01 12:02:00 - CRITICAL - IP_BLOCKED: IP 192.168.1.100 blocked for 1 hour
```

### Monitored Event Types
- `PATH_TRAVERSAL_BLOCKED` - Path traversal attempt
- `SUSPICIOUS_PATTERN_DETECTED` - Suspicious pattern detected
- `RATE_LIMIT_EXCEEDED` - Rate limit exceeded
- `FILE_ACCESS` - File access
- `UPLOAD_BLOCKED` - Upload blocked

## 🧪 Security Tests

### Running Tests
```bash
cd backendApi
python -m pytest tests/security/test_path_security.py -v
```

### Tested Scenarios
- ✅ Unix/Windows path traversal
- ✅ Null byte injection
- ✅ Windows reserved filenames
- ✅ Unauthorized extensions
- ✅ Excessive file sizes
- ✅ Access outside authorized directories

## 🚀 Deployment Recommendations

### In Production
1. **Environment variables**: Configure all tokens/secrets
2. **HTTPS**: Use HTTPS exclusively
3. **Reverse Proxy**: Nginx/Apache with additional limitations
4. **Monitoring**: Monitor security logs
5. **Backup**: Regularly backup authorized data only

### Nginx Configuration (example)
```nginx
# Limit upload size
client_max_body_size 100M;

# Security headers
add_header X-Content-Type-Options nosniff;
add_header X-Frame-Options DENY;
add_header X-XSS-Protection "1; mode=block";

# Block access to sensitive files
location ~ /\. {
    deny all;
}

location ~ \.(env|ini|conf)$ {
    deny all;
}
```

## 🔄 Maintenance

### Updating Rules
Security rules can be updated in:
- `app/config/security.py` - General configuration
- `app/utils/security.py` - Validation logic
- `app/middleware/security.py` - Monitoring middleware

### Regular Audit
1. Check security logs weekly
2. Update allowed extensions list if necessary
3. Adjust rate limiting according to usage
4. Test regularly with pen-test tools

## 📞 Security Contact

In case of vulnerability discovery:
1. **DO NOT** create public issue
2. Contact security team directly
3. Provide detailed PoC
4. Wait for fix before publication
