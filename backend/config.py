"""
JalRakshak NCR — Backend Configuration Settings
"""

import os

class Settings:
    PROJECT_NAME: str = "JalRakshak NCR"
    VERSION: str = "2.0.0"
    SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "jalrakshak-sustainx-2026-neernetra-secret-key-32b")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 Hours
    OTP_EXPIRE_SECONDS: int = 300  # 5 Minutes
    
    # Cookie Configurations
    COOKIE_NAME: str = "access_token"
    COOKIE_SECURE: bool = False  # Set to True in HTTPS production
    COOKIE_SAMESITE: str = "lax"

settings = Settings()
