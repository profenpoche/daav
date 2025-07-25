import os
from pathlib import Path
from typing import List, Optional, Union
from pydantic import field_validator, ConfigDict, Field

try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings

class Settings(BaseSettings):
    # Nouvelle configuration Pydantic V2
    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore"  # Ignore les champs non définis
    )
    
    # Application
    app_name: str = "DAAV Backend API"
    app_version: str = "1.0.0"
    debug: bool = False
    environment: str = "development"
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Database
    mongodb_url: str = "mongodb://localhost:27017"
    database_name: str = "daav_datasets"
    
    # Logging
    log_level: str = "INFO"
    log_file: str = "app.log"
    log_max_size: str = "10MB"
    log_backup_count: int = 5

    # Security logging (configurable)
    security_log_file: str = "security.log"
    security_log_level: str = "INFO"
    security_log_max_size: str = "10MB"
    security_log_backup_count: int = 5
    
    # CORS - peut être une string ou une liste
    cors_origins: Union[List[str], str] = ["http://localhost:4200", "http://127.0.0.1:4200"]
    
    # Security
    secret_key: Optional[str] = None
    
    # Security middleware settings
    security_rate_limit: int = Field(default=100, description="Max requests per time window")
    security_time_window: int = Field(default=60, description="Time window in seconds")
    security_enabled: bool = Field(default=True, description="Enable security middleware")
    
    # File uploads
    upload_dir: str = "uploads"
    max_file_size: Union[int, str] = 100 * 1024 * 1024  # 100MB

    directory_white_list : Union[List[str], str] = []

    @field_validator('directory_white_list','cors_origins', mode='before')
    @classmethod
    def parse_str_list_tolist(cls, v):
        """Parse from string or list to list"""
        if isinstance(v, str):
            # Si c'est une string séparée par des virgules
            if ',' in v and not v.startswith('['):
                return [origin.strip() for origin in v.split(',')]
            # Si c'est déjà du JSON
            elif v.startswith('['):
                import json
                try:
                    return json.loads(v)
                except json.JSONDecodeError:
                    return [v]  # Fallback sur une seule origine
            else:
                return [v]  # Une seule origine
        return v  # Déjà une liste

    @field_validator('max_file_size', mode='before')
    @classmethod
    def parse_max_file_size(cls, v):
        """Parse max file size from string like '100MB' to bytes"""
        if isinstance(v, str):
            v = v.upper()
            if v.endswith('MB'):
                return int(v[:-2]) * 1024 * 1024
            elif v.endswith('KB'):
                return int(v[:-2]) * 1024
            elif v.endswith('GB'):
                return int(v[:-2]) * 1024 * 1024 * 1024
            elif v.isdigit():
                return int(v)
            else:
                # Fallback
                return 100 * 1024 * 1024
        return v

    @field_validator('port', mode='before')
    @classmethod
    def parse_port(cls, v):
        """Parse port from string to int"""
        if isinstance(v, str):
            return int(v)
        return v

    @field_validator('log_backup_count', mode='before')
    @classmethod
    def parse_log_backup_count(cls, v):
        """Parse log backup count from string to int"""
        if isinstance(v, str):
            return int(v)
        return v

    @field_validator('upload_dir', mode='before')
    @classmethod
    def resolve_upload_dir(cls, v):
        """Resolve upload directory  from absolute or relative path"""
        if not v:
            return "uploads"
        #already an absolute path    
        if os.path.isabs(v):
            return v
        
        # build the path from app root
        app_dir = Path(__file__).parent.parent 
        upload_path = app_dir / v
        return str(upload_path.resolve())

# Global settings instance
settings = Settings()