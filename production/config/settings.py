"""
Production Configuration Settings using Pydantic

Loads environment variables from .env file and provides type-safe configuration.
Never hardcode configuration - always use environment variables.
"""

from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import Field, validator


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # ========================================================================
    # APPLICATION SETTINGS
    # ========================================================================
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=False, env="DEBUG")
    secret_key: str = Field(default="change-me-in-production", env="SECRET_KEY")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(default="json", env="LOG_FORMAT")

    # ========================================================================
    # API CONFIGURATION
    # ========================================================================
    api_port: int = Field(default=8000, env="API_PORT")
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_workers: int = Field(default=4, env="API_WORKERS")

    # ========================================================================
    # DATABASE CONFIGURATION
    # ========================================================================
    database_url: str = Field(
        default="postgresql://cloudflow:password@localhost:5432/cloudflow_db",
        env="DATABASE_URL"
    )
    db_pool_size: int = Field(default=20, env="DB_POOL_SIZE")
    db_max_overflow: int = Field(default=40, env="DB_MAX_OVERFLOW")
    db_echo: bool = Field(default=False, env="DB_ECHO")

    # ========================================================================
    # REDIS CACHE CONFIGURATION
    # ========================================================================
    redis_url: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    cache_ttl: int = Field(default=3600, env="CACHE_TTL")
    cache_backend: str = Field(default="redis", env="CACHE_BACKEND")

    # ========================================================================
    # KAFKA CONFIGURATION
    # ========================================================================
    kafka_bootstrap_servers: str = Field(
        default="localhost:9092",
        env="KAFKA_BOOTSTRAP_SERVERS"
    )
    kafka_consumer_group: str = Field(default="cloudflow-agents", env="KAFKA_CONSUMER_GROUP")
    kafka_topic_messages: str = Field(default="customer-messages", env="KAFKA_TOPIC_MESSAGES")
    kafka_topic_escalations: str = Field(default="escalations", env="KAFKA_TOPIC_ESCALATIONS")
    kafka_topic_responses: str = Field(default="customer-responses", env="KAFKA_TOPIC_RESPONSES")

    # ========================================================================
    # COHERE AI CONFIGURATION (OpenAI Agents SDK Backend)
    # ========================================================================
    cohere_key: Optional[str] = Field(default=None, env="COHERE_KEY")
    cohere_model: str = Field(default="command-r-plus", env="COHERE_MODEL")
    cohere_base_url: str = Field(default="https://api.cohere.com/v1", env="COHERE_BASE_URL")
    debug: bool = Field(default=False, env="DEBUG")

    # ========================================================================
    # GMAIL INTEGRATION
    # ========================================================================
    gmail_enabled: bool = Field(default=True, env="GMAIL_ENABLED")
    gmail_client_id: str = Field(default="", env="GMAIL_CLIENT_ID")
    gmail_client_secret: str = Field(default="", env="GMAIL_CLIENT_SECRET")
    gmail_redirect_uri: str = Field(
        default="http://localhost:8000/api/gmail/callback",
        env="GMAIL_REDIRECT_URI"
    )
    gmail_scopes: str = Field(
        default="https://www.googleapis.com/auth/gmail.modify",
        env="GMAIL_SCOPES"
    )

    # ========================================================================
    # WHATSAPP BUSINESS API (via Twilio)
    # ========================================================================
    whatsapp_enabled: bool = Field(default=True, env="WHATSAPP_ENABLED")
    whatsapp_business_api_url: str = Field(
        default="https://graph.instagram.com/v18.0",
        env="WHATSAPP_BUSINESS_API_URL"
    )
    whatsapp_business_phone_id: str = Field(default="", env="WHATSAPP_BUSINESS_PHONE_ID")
    whatsapp_business_token: str = Field(default="", env="WHATSAPP_BUSINESS_TOKEN")
    whatsapp_webhook_verify_token: str = Field(default="", env="WHATSAPP_WEBHOOK_VERIFY_TOKEN")
    whatsapp_webhook_endpoint: str = Field(default="/api/whatsapp/webhook", env="WHATSAPP_WEBHOOK_ENDPOINT")

    # ========================================================================
    # TWILIO CONFIGURATION (for WhatsApp via Twilio)
    # ========================================================================
    twilio_account_sid: Optional[str] = Field(default=None, env="TWILIO_ACCOUNT_SID")
    twilio_auth_token: Optional[str] = Field(default=None, env="TWILIO_AUTH_TOKEN")
    twilio_number: Optional[str] = Field(default=None, env="TWILIO_NUMBER")

    # ========================================================================
    # WEB FORM CONFIGURATION
    # ========================================================================
    webform_enabled: bool = Field(default=True, env="WEBFORM_ENABLED")
    webform_endpoint: str = Field(default="/api/form/submit", env="WEBFORM_ENDPOINT")
    webform_max_file_size: int = Field(default=10485760, env="WEBFORM_MAX_FILE_SIZE")  # 10MB

    # ========================================================================
    # SENTRY ERROR TRACKING
    # ========================================================================
    sentry_dsn: Optional[str] = Field(default=None, env="SENTRY_DSN")
    sentry_enabled: bool = Field(default=True, env="SENTRY_ENABLED")
    sentry_environment: str = Field(default="development", env="SENTRY_ENVIRONMENT")
    sentry_traces_sample_rate: float = Field(default=0.1, env="SENTRY_TRACES_SAMPLE_RATE")

    # ========================================================================
    # PROMETHEUS MONITORING
    # ========================================================================
    prometheus_port: int = Field(default=9090, env="PROMETHEUS_PORT")
    prometheus_enabled: bool = Field(default=True, env="PROMETHEUS_ENABLED")
    metrics_port: int = Field(default=9091, env="METRICS_PORT")

    # ========================================================================
    # GRAFANA CONFIGURATION
    # ========================================================================
    grafana_port: int = Field(default=3000, env="GRAFANA_PORT")
    grafana_admin_user: str = Field(default="admin", env="GRAFANA_ADMIN_USER")
    grafana_admin_password: str = Field(default="admin", env="GRAFANA_ADMIN_PASSWORD")

    # ========================================================================
    # LOGGING CONFIGURATION
    # ========================================================================
    log_file: str = Field(default="/var/log/cloudflow/app.log", env="LOG_FILE")
    log_max_bytes: int = Field(default=10485760, env="LOG_MAX_BYTES")  # 10MB
    log_backup_count: int = Field(default=5, env="LOG_BACKUP_COUNT")

    # ========================================================================
    # RATE LIMITING
    # ========================================================================
    rate_limit_per_minute: int = Field(default=100, env="RATE_LIMIT_PER_MINUTE")
    rate_limit_per_hour: int = Field(default=1000, env="RATE_LIMIT_PER_HOUR")
    rate_limit_enabled: bool = Field(default=True, env="RATE_LIMIT_ENABLED")

    # ========================================================================
    # CELERY TASK QUEUE
    # ========================================================================
    celery_broker_url: str = Field(default="redis://localhost:6379/1", env="CELERY_BROKER_URL")
    celery_result_backend: str = Field(default="redis://localhost:6379/2", env="CELERY_RESULT_BACKEND")
    celery_task_serializer: str = Field(default="json", env="CELERY_TASK_SERIALIZER")
    celery_accept_content: str = Field(default="json", env="CELERY_ACCEPT_CONTENT")
    celery_result_expires: int = Field(default=3600, env="CELERY_RESULT_EXPIRES")
    celery_timezone: str = Field(default="UTC", env="CELERY_TIMEZONE")

    # ========================================================================
    # AUTHENTICATION & SECURITY
    # ========================================================================
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    jwt_expiration_hours: int = Field(default=24, env="JWT_EXPIRATION_HOURS")
    jwt_secret_key: str = Field(default="change-me", env="JWT_SECRET_KEY")
    allowed_origins: str = Field(
        default="http://localhost:3000,http://localhost:8000",
        env="ALLOWED_ORIGINS"
    )
    allowed_hosts: str = Field(default="localhost,127.0.0.1", env="ALLOWED_HOSTS")

    # ========================================================================
    # CORS CONFIGURATION
    # ========================================================================
    cors_allow_credentials: bool = Field(default=True, env="CORS_ALLOW_CREDENTIALS")
    cors_allow_methods: str = Field(
        default="GET,POST,PUT,DELETE,OPTIONS",
        env="CORS_ALLOW_METHODS"
    )
    cors_allow_headers: str = Field(
        default="Content-Type,Authorization",
        env="CORS_ALLOW_HEADERS"
    )

    # ========================================================================
    # FEATURE FLAGS
    # ========================================================================
    enable_sentiment_ml: bool = Field(default=False, env="ENABLE_SENTIMENT_ML")
    enable_escalation_ml: bool = Field(default=False, env="ENABLE_ESCALATION_ML")
    enable_vector_search: bool = Field(default=False, env="ENABLE_VECTOR_SEARCH")
    enable_kafka_streaming: bool = Field(default=True, env="ENABLE_KAFKA_STREAMING")

    # ========================================================================
    # OBSERVABILITY
    # ========================================================================
    tracing_enabled: bool = Field(default=True, env="TRACING_ENABLED")
    metrics_enabled: bool = Field(default=True, env="METRICS_ENABLED")
    health_check_enabled: bool = Field(default=True, env="HEALTH_CHECK_ENABLED")

    # ========================================================================
    # DEVELOPMENT SETTINGS
    # ========================================================================
    auto_reload: bool = Field(default=True, env="AUTO_RELOAD")
    reload_dirs: str = Field(default="src,production", env="RELOAD_DIRS")
    reload_delay: float = Field(default=0.25, env="RELOAD_DELAY")

    # Pydantic config
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    # ========================================================================
    # PROPERTIES FOR PARSED VALUES
    # ========================================================================

    @property
    def allowed_origins_list(self) -> List[str]:
        """Parse comma-separated allowed origins."""
        return [origin.strip() for origin in self.allowed_origins.split(",")]

    @property
    def allowed_hosts_list(self) -> List[str]:
        """Parse comma-separated allowed hosts."""
        return [host.strip() for host in self.allowed_hosts.split(",")]

    @property
    def cors_allow_methods_list(self) -> List[str]:
        """Parse comma-separated CORS methods."""
        return [method.strip() for method in self.cors_allow_methods.split(",")]

    @property
    def cors_allow_headers_list(self) -> List[str]:
        """Parse comma-separated CORS headers."""
        return [header.strip() for header in self.cors_allow_headers.split(",")]

    @property
    def reload_dirs_list(self) -> List[str]:
        """Parse comma-separated reload directories."""
        return [d.strip() for d in self.reload_dirs.split(",")]

    # ========================================================================
    # VALIDATION
    # ========================================================================

    @validator("debug")
    def validate_debug_in_production(cls, v, values):
        """Warn if debug is enabled in production."""
        if v and values.get("environment") == "production":
            raise ValueError("DEBUG must be False in production environment")
        return v

    @validator("secret_key")
    def validate_secret_key(cls, v, values):
        """Ensure secret key is not default value."""
        if v == "change-me-in-production" and values.get("environment") == "production":
            raise ValueError("SECRET_KEY must be changed from default in production")
        return v


# Create global settings instance
settings = Settings()
