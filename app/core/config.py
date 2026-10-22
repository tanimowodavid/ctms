from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from urllib.parse import urlsplit


class Settings(BaseSettings):
	model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

	database_url: str = "postgresql+psycopg2://postgres:change-this-local-password@localhost:5432/tms"
	jwt_secret: str = "CHANGE_ME_TO_A_RANDOM_SECRET_AT_LEAST_32_CHARACTERS"
	cors_allowed_origins: str = ""
	setup_link_base_url: str = "http://localhost:3000/setup-password"
	smtp_host: str = "smtp.gmail.com"
	smtp_port: int = 587
	smtp_username: str = "your-account@gmail.com"
	smtp_password: str = "your-gmail-app-password"
	smtp_from_email: str = "your-account@gmail.com"
	smtp_starttls: bool = True
	smtp_use_ssl: bool = False
	smtp_timeout_seconds: int = 20
	worker_poll_seconds: int = 5
	worker_retry_base_seconds: int = 30
	worker_retry_max_seconds: int = 3600

	@property
	def allowed_origins(self) -> list[str]:
		return [origin.strip().rstrip("/") for origin in self.cors_allowed_origins.split(",") if origin.strip()]

	@field_validator("jwt_secret")
	@classmethod
	def require_strong_jwt_secret(cls, value: str) -> str:
		if len(value) < 32:
			raise ValueError("JWT_SECRET must contain at least 32 characters")
		return value

	@field_validator("cors_allowed_origins")
	@classmethod
	def validate_cors_origins(cls, value: str) -> str:
		for origin in (item.strip() for item in value.split(",") if item.strip()):
			parsed = urlsplit(origin)
			if (
				"*" in parsed.netloc
				or parsed.scheme not in {"http", "https"}
				or not parsed.netloc
				or parsed.path not in {"", "/"}
				or parsed.query
				or parsed.fragment
			):
				raise ValueError("CORS_ALLOWED_ORIGINS must contain exact http(s) origins, not wildcards or paths")
		return value


settings = Settings()
