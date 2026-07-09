from __future__ import annotations

import json

import pytest

from app.config import get_settings
from app.rule_engine import ReplyRuleError, choose_reply, load_rules


def test_choose_reply_uses_matching_rule(tmp_path, monkeypatch) -> None:
    rules_path = tmp_path / "rules.json"
    rules_path.write_text(
        json.dumps(
            {
                "rules": [
                    {"name": "price", "pattern": "料金", "response": "料金の返信"},
                    {"name": "default", "pattern": ".*", "response": "default"},
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("REPLY_RULES_PATH", str(rules_path))
    assert choose_reply("料金を教えて", settings=get_settings()) == "料金の返信"


def test_choose_reply_falls_back_to_default_rule(tmp_path, monkeypatch) -> None:
    rules_path = tmp_path / "rules.json"
    rules_path.write_text(
        json.dumps({"rules": [{"name": "default", "pattern": ".*", "response": "default"}]}),
        encoding="utf-8",
    )
    monkeypatch.setenv("REPLY_RULES_PATH", str(rules_path))
    assert choose_reply("unknown", settings=get_settings()) == "default"


def test_load_rules_rejects_invalid_regex(tmp_path) -> None:
    rules_path = tmp_path / "rules.json"
    rules_path.write_text(
        json.dumps({"rules": [{"name": "broken", "pattern": "[", "response": "x"}]}),
        encoding="utf-8",
    )
    with pytest.raises(ReplyRuleError):
        load_rules(rules_path)
