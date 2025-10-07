from enum import Enum

class UserRole(str, Enum):
    """User roles enumeration"""
    ADMIN = "admin"
    USER = "user"
    
    def __str__(self):
        return self.value
