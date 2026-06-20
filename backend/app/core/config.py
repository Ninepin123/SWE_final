"""全域設定（組長維護，修改前請在群組告知）。

設定值一律從 backend/.env 讀取，不要把連線字串或金鑰寫死在程式裡。
新增設定時：在這裡加欄位 + 在 .env.example 加範例值。
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str = "mysql+pymysql://nuksams_dev:nuksams_dev_password@127.0.0.1:3307/nuksams?charset=utf8mb4"
    secret_key: str = "dev-secret-change-me"
    access_token_expire_minutes: int = 30
    bootstrap_admin_account: str = "admin"
    bootstrap_admin_password: str = "ChangeMe!12345"
    bootstrap_admin_name: str = "系統管理員"
    bootstrap_admin_email: str | None = None
    cors_origins: list[str] = ["http://localhost:5173"]


settings = Settings()
