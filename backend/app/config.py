"""Application configuration loaded from environment."""
import os
from datetime import timedelta


def _bool(v: str | None, default: bool = False) -> bool:
    if v is None:
        return default
    return v.strip().lower() in ("1", "true", "yes", "on")


class Config:
    APP_ENV = os.getenv("APP_ENV", "production")
    DEBUG = APP_ENV == "development"
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "dev-secret-change-me")

    # ---- DB ----
    MYSQL_HOST = os.getenv("MYSQL_HOST", "mysql")
    MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
    MYSQL_USER = os.getenv("MYSQL_USER", "cotask")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "cotask_pw")
    MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "cotask")
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}"
        f"@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}?charset=utf8mb4"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 1800,
        "pool_size": 10,
        "max_overflow": 20,
    }

    # ---- JWT ----
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-jwt-secret")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=15)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    JWT_TOKEN_LOCATION = ["headers", "cookies"]
    JWT_COOKIE_SECURE = APP_ENV == "production"
    JWT_COOKIE_HTTPONLY = True
    JWT_COOKIE_SAMESITE = "Lax"
    JWT_REFRESH_COOKIE_PATH = "/api/auth/refresh"
    JWT_COOKIE_CSRF_PROTECT = False

    # ---- Redis ----
    REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
    CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/1")
    CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/2")

    # ---- MinIO ----
    MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "minio:9000")
    MINIO_PUBLIC_ENDPOINT = os.getenv("MINIO_PUBLIC_ENDPOINT", "http://localhost:9000")
    MINIO_ACCESS_KEY = os.getenv("MINIO_ROOT_USER", "cotask_minio")
    MINIO_SECRET_KEY = os.getenv("MINIO_ROOT_PASSWORD", "cotask_minio_pw")
    MINIO_BUCKET = os.getenv("MINIO_BUCKET", "cotask-files")
    MINIO_SECURE = _bool(os.getenv("MINIO_SECURE"), False)

    # ---- AI ----
    AI_PROVIDER = os.getenv("AI_PROVIDER", "anthropic")
    AI_PROVIDER_FALLBACK = os.getenv("AI_PROVIDER_FALLBACK", "openai,deepseek,dashscope").split(",")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "")
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
    DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")
    AI_MODEL_ANTHROPIC = os.getenv("AI_MODEL_ANTHROPIC", "claude-sonnet-4-6")
    AI_MODEL_OPENAI = os.getenv("AI_MODEL_OPENAI", "gpt-4o-mini")
    AI_MODEL_DEEPSEEK = os.getenv("AI_MODEL_DEEPSEEK", "deepseek-chat")
    AI_MODEL_DASHSCOPE = os.getenv("AI_MODEL_DASHSCOPE", "qwen-max")
    AI_REQUEST_TIMEOUT = int(os.getenv("AI_REQUEST_TIMEOUT", "60"))

    # ---- SMS / Email ----
    # stub: local Redis code (logged in dev); aliyun: PNVS SMS auth service
    SMS_PROVIDER = os.getenv("SMS_PROVIDER", "stub")
    SMS_ACCESS_KEY = os.getenv("SMS_ACCESS_KEY", "")
    SMS_SECRET_KEY = os.getenv("SMS_SECRET_KEY", "")
    SMS_AUTH_SIGN_NAME = os.getenv("SMS_AUTH_SIGN_NAME", "速通互联验证平台")
    SMS_AUTH_TEMPLATE_CODE = os.getenv("SMS_AUTH_TEMPLATE_CODE", "100001")
    SMS_COUNTRY_CODE = os.getenv("SMS_COUNTRY_CODE", "86")
    SMTP_HOST = os.getenv("SMTP_HOST", "")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
    SMTP_FROM = os.getenv("SMTP_FROM", "no-reply@cotask.local")

    # ---- API meta ----
    API_TITLE = "CoTask API"
    API_VERSION = "1.0.0"
    OPENAPI_VERSION = "3.0.3"
    OPENAPI_URL_PREFIX = "/"
    OPENAPI_SWAGGER_UI_PATH = "/docs"
    OPENAPI_SWAGGER_UI_URL = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"
    OPENAPI_JSON_PATH = "/openapi.json"
    API_SPEC_OPTIONS = {
        "info": {"description": "CoTask backend API."},
    }

    # ---- Misc ----
    UPLOAD_MAX_BYTES = 100 * 1024 * 1024  # 100MB
    INVITE_CODE_LENGTH = 8
    SMS_CODE_LENGTH = int(os.getenv("SMS_CODE_LENGTH", "4"))
    SMS_CODE_TTL = 300  # 5 minutes
    NUDGE_COOLDOWN = 86400  # 24h
    DDL_WARNING_HOURS = 72


def get_config() -> type[Config]:
    return Config
