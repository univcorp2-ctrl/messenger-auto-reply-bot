# Deployment Guide

このアプリは公開HTTPS URLを持つ環境にデプロイしてください。Meta Messenger Webhookは外部から `POST /webhook` にアクセスできる必要があります。

## Docker

```bash
docker build -t messenger-auto-reply-bot .
docker run --env-file .env -p 8000:8000 messenger-auto-reply-bot
```

## Render例

1. New Web Serviceを作成
2. GitHub repoを接続
3. RuntimeにDockerを選択
4. Environment Variablesに `VERIFY_TOKEN`, `PAGE_ACCESS_TOKEN`, `APP_SECRET`, `GRAPH_API_VERSION`, `AUTO_REPLY_ENABLED`, `AUTO_REPLY_MODE` を設定
5. 発行されたURLの `/webhook` をMetaのCallback URLに設定

## Cloud Run例

```bash
gcloud run deploy messenger-auto-reply-bot \
  --source . \
  --region asia-northeast1 \
  --allow-unauthenticated
```

Secretの実値はCLI履歴に残さないよう、Secret Managerを使う構成を推奨します。
