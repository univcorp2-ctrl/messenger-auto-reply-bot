from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


def _as_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    verify_token: str
    page_access_token: str
    app_secret: str
    graph_api_version: str
    auto_reply_enabled: bool
    auto_reply_mode: str
    reply_rules_path: str
    openai_api_key: str
    openai_model: str
    openai_system_prompt: str
    log_level: str

    @property
    def messenger_endpoint(self) -> str:
        return f"https://graph.facebook.com/{self.graph_api_version}/me/messages"

    @property
    def has_page_access_token(self) -> bool:
        return bool(self.page_access_token.strip())

    @property
    def has_app_secret(self) -> bool:
        return bool(self.app_secret.strip())

    @property
    def ai_reply_enabled(self) -> bool:
        return self.auto_reply_mode.strip().lower() == "ai" and bool(self.openai_api_key.strip())


def get_settings() -> Settings:
    return Settings(
        verify_token=os.getenv("VERIFY_TOKEN", "dev-verify-token"),
        page_access_token=os.getenv("PAGE_ACCESS_TOKEN", ""),
        app_secret=os.getenv("APP_SECRET", ""),
        graph_api_version=os.getenv("GRAPH_API_VERSION", "v25.0"),
        auto_reply_enabled=_as_bool(os.getenv("AUTO_REPLY_ENABLED"), True),
        auto_reply_mode=os.getenv("AUTO_REPLY_MODE", "rules"),
        reply_rules_path=os.getenv("REPLY_RULES_PATH", "config/reply_rules.example.json"),
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-5.4-mini"),
        openai_system_prompt=os.getenv(
            "OPENAI_SYSTEM_PROMPT",
            "あなたはFacebookページの丁寧な一次受付担当です。短く自然に日本語で返信してください。",
        ),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
    )
