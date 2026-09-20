"""Application Configuration Module using Pydantic Settings."""

import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    # Application Info
    APP_NAME: str = "ThreatGraph-AI"
    APP_ENV: str = "development"
    APP_DEBUG: bool = True
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "threatgraph-dev-super-secret-key-change-in-production-min32chars!"

    # Server Binding
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]

    # Neo4j Graph Database
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "ThreatIntelGraphPassword123!"
    NEO4J_DATABASE: str = "neo4j"

    # Redis Configuration
    REDIS_URL: str = "redis://localhost:6379/0"

    # Ingestion & Security Thresholds
    MAX_UPLOAD_SIZE_BYTES: int = 10 * 1024 * 1024  # 10 MB
    MIN_CONFIDENCE_THRESHOLD: float = 0.35
    CORROBORATION_REQUIRED_COUNT: int = 2
    MAX_GRAPH_HOP_DEPTH: int = 4

    # ML & Clustering Parameters
    HDBSCAN_MIN_CLUSTER_SIZE: int = 2
    HDBSCAN_MIN_SAMPLES: int = 1
    LINK_PREDICTION_SIMILARITY_THRESHOLD: float = 0.65

    # LLM Analysis (Google Gemini)
    GEMINI_API_KEY: str = ""
    LLM_ENABLED: bool = True
    LLM_MODEL: str = "gemini-2.0-flash"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )


settings = Settings()
