from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # 앱
    app_env: str = "development"
    log_level: str = "INFO"

    # DB — 개별 값을 받아 URL 조합 (패스워드를 URL에 직접 노출하지 않기 위함)
    db_host: str = "db"
    db_port: int = 5432
    db_name: str = "lecture_quiz"
    db_user: str = "quiz_user"
    db_password: str

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    # 파일 업로드
    upload_dir: str = "/app/uploads"
    max_file_size_mb: int = 200


settings = Settings()
