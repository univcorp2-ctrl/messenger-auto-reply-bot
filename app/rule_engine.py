from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.config import Settings, get_settings


@dataclass(frozen=True)
class ReplyRule:
    name: str
    pattern: str
    response: str


DEFAULT_RULES: tuple[ReplyRule, ...] = (
    ReplyRule(
        "greeting",
        r"(?i)^(hi|hello|hey|こんにちは|こんばんは|おはよう)",
        "こんにちは！メッセージありがとうございます。ご用件を送ってください。",
    ),
    ReplyRule(
        "hours",
        r"(?i)(営業時間|open|hours|何時)",
        "営業時間についてのお問い合わせありがとうございます。担当者が確認して返信します。",
    ),
    ReplyRule(
        "price",
        r"(?i)(料金|価格|値段|price|cost|いくら)",
        "料金についてのお問い合わせありがとうございます。内容を確認してご案内します。",
    ),
    ReplyRule(
        "default",
        r".*",
        "メッセージありがとうございます。確認して返信します。",
    ),
)


class ReplyRuleError(ValueError):
    """Raised when reply rule JSON is invalid."""


def _coerce_rule(item: dict[str, Any], index: int) -> ReplyRule:
    name = str(item.get("name") or f"rule_{index}")
    pattern = item.get("pattern")
    response = item.get("response")
    if not isinstance(pattern, str) or not pattern:
        raise ReplyRuleError(f"rules[{index}].pattern must be a non-empty string")
    if not isinstance(response, str) or not response:
        raise ReplyRuleError(f"rules[{index}].response must be a non-empty string")
    try:
        re.compile(pattern)
    except re.error as exc:
        raise ReplyRuleError(f"rules[{index}].pattern is invalid regex: {exc}") from exc
    return ReplyRule(name=name, pattern=pattern, response=response)


def load_rules(path: str | Path | None) -> list[ReplyRule]:
    if not path:
        return list(DEFAULT_RULES)
    rule_path = Path(path)
    if not rule_path.exists():
        return list(DEFAULT_RULES)
    data = json.loads(rule_path.read_text(encoding="utf-8"))
    raw_rules = data.get("rules") if isinstance(data, dict) else data
    if not isinstance(raw_rules, list):
        raise ReplyRuleError("reply rules JSON must be a list or an object with a rules list")
    rules = [_coerce_rule(item, index) for index, item in enumerate(raw_rules)]
    return rules or list(DEFAULT_RULES)


def choose_reply(message_text: str, settings: Settings | None = None) -> str:
    settings = settings or get_settings()
    rules = load_rules(settings.reply_rules_path)
    text = message_text.strip()
    for rule in rules:
        if re.search(rule.pattern, text):
            return rule.response
    return DEFAULT_RULES[-1].response
