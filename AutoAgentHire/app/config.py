"""
Configuration management for AutoAgentHire
"""

import os
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    """Application settings"""
    
    # Server configuration
    HOST: str = Field(default="0.0.0.0", description="Server host")
    PORT: int = Field(default=8000, description="Server port")
    DEBUG: bool = Field(default=False, description="Debug mode")
    
    # CORS settings
    ALLOWED_ORIGINS: List[str] = Field(default=["*"], description="Allowed CORS origins")
    
    # Database configuration
    DATABASE_URL: str = Field(default="sqlite:///./autoagenthire.db", description="Database URL")
    
    # API Keys
    OPENAI_API_KEY: str = Field(default="", description="OpenAI API key")
    PINECONE_API_KEY: str = Field(default="", description="Pinecone API key")
    PINECONE_ENVIRONMENT: str = Field(default="us-east-1", description="Pinecone environment")
    
    # LinkedIn automation settings
    LINKEDIN_EMAIL: str = Field(default="", description="LinkedIn email")
    LINKEDIN_PASSWORD: str = Field(default="", description="LinkedIn password")
    
    # Automation settings
    MAX_APPLICATIONS_PER_DAY: int = Field(default=50, description="Maximum applications per day")
    APPLICATION_DELAY_MIN: int = Field(default=30, description="Minimum delay between applications (seconds)")
    APPLICATION_DELAY_MAX: int = Field(default=120, description="Maximum delay between applications (seconds)")
    
    # Vector store settings
    VECTOR_DIMENSION: int = Field(default=1536, description="Vector dimension for embeddings")
    SIMILARITY_THRESHOLD: float = Field(default=0.8, description="Similarity threshold for job matching")
    
    # File paths
    RESUME_PATH: str = Field(default="./uploads/resume.pdf", description="Path to user's resume")
    COVER_LETTER_TEMPLATE_PATH: str = Field(default="./templates/cover_letter.txt", description="Cover letter template path")
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    LOG_FILE: str = Field(default="autoagenthire.log", description="Log file path")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"  # Ignore extra fields in .env file

# Create global settings instance
settings = Settings()