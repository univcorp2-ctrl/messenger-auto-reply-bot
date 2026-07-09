# CODEX.md

このrepoは、FacebookページのMessenger自動返信Botです。

## 技術スタック

- Python 3.11+
- FastAPI
- httpx
- pytest
- ruff
- Docker / devcontainer
- GitHub Actions

## 実装方針

- `app/main.py` は薄く保ち、署名検証、ルール選択、Meta API送信は別モジュールに分離する。
- Secretは必ず環境変数で受け取り、repoには実値を保存しない。
- Meta WebhookのPOSTは必ず200を速く返す。
- 返信ルールは `config/reply_rules.example.json` と同じスキーマを維持する。
- AI返信は任意機能。標準は `AUTO_REPLY_MODE=rules`。
