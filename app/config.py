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

    # STT (faster-whisper)
    stt_model_size: str = "large-v3"
    stt_device: str = "cuda"        # cuda | cpu
    stt_compute_type: str = "float16"  # float16(GPU) | int8(CPU)

    # LLM (Qwen2.5-7B-Instruct via Ollama)
    llm_base_url: str = "http://localhost:11434/v1"
    llm_model: str = "qwen2.5:7b-instruct"
    llm_api_key: str = "ollama"     # Ollama는 키 불필요, openai SDK 형식 맞추기용
    llm_temperature: float = 0.3
    llm_max_tokens: int = 2048
    llm_quiz_count: int = 5


settings = Settings()
