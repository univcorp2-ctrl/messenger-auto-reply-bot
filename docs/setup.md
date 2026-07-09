# 初期設定ガイド

FacebookページのMessengerへ届いたメッセージに自動返信するため、Meta Developer Appとデプロイ先の環境変数を設定します。

## 0. 先に決める値

| 名前 | 例 | 保存先 |
| --- | --- | --- |
| Verify Token | 長いランダム文字列 | デプロイ先 `VERIFY_TOKEN` とMeta画面 |
| Page Access Token | Metaが発行 | デプロイ先 `PAGE_ACCESS_TOKEN` |
| App Secret | Metaが発行 | デプロイ先 `APP_SECRET` |
| Callback URL | `https://your-domain.example.com/webhook` | Meta画面 |

## 1. アプリをデプロイする

Meta Webhookは公開HTTPS URLが必要です。Render、Fly.io、Cloud Run、RailwayなどにDockerまたはPythonアプリとしてデプロイします。

起動コマンド:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

必須環境変数:

```dotenv
VERIFY_TOKEN=<自分で決めた長い文字列>
PAGE_ACCESS_TOKEN=<Metaで取得したPage Access Token>
APP_SECRET=<Meta App Secret>
GRAPH_API_VERSION=v25.0
AUTO_REPLY_ENABLED=true
AUTO_REPLY_MODE=rules
REPLY_RULES_PATH=config/reply_rules.example.json
```

## 2. Meta Developer Appを作成する

1. Meta for Developersを開く
2. Create Appを押す
3. 用途に合う種類を選ぶ
4. App名と連絡先メールを入力
5. 作成後、Messenger productを追加

## 3. Facebook Pageを接続する

1. Messenger設定画面を開く
2. Access Tokens / Token GenerationのPage選択で対象Facebook Pageを選ぶ
3. 必要な権限を許可
4. Page Access Tokenを発行
5. デプロイ先の `PAGE_ACCESS_TOKEN` に保存

## 4. App Secretを保存する

Meta App DashboardのBasic SettingsからApp Secretを表示し、デプロイ先の `APP_SECRET` に保存します。本番では必須にしてください。

## 5. Webhookを登録する

1. MessengerまたはWebhooks設定を開く
2. Callback URLに `https://your-domain.example.com/webhook` を入力
3. Verify Tokenにデプロイ先 `VERIFY_TOKEN` と同じ値を入力
4. Verify and Saveを押す
5. `messages` と `messaging_postbacks` を購読

## 6. 動作確認

FacebookページにMessengerから `こんにちは` と送ります。期待される返信は次です。

```text
こんにちは！メッセージありがとうございます。ご用件を送ってください。
```

## 7. 返信文を変更する

`config/reply_rules.example.json` を編集してデプロイし直します。

## 8. AI返信モード 任意

```dotenv
AUTO_REPLY_MODE=ai
OPENAI_API_KEY=<OpenAI API Key>
OPENAI_MODEL=gpt-5.4-mini
OPENAI_SYSTEM_PROMPT=あなたはFacebookページの丁寧な一次受付担当です。短く自然に日本語で返信してください。
```

OpenAI APIが失敗した場合は、ルールベース返信へ自動fallbackします。

## 9. 本番チェックリスト

- `PAGE_ACCESS_TOKEN` がデプロイ先に入っている
- `VERIFY_TOKEN` がMeta画面とデプロイ先で完全一致している
- `APP_SECRET` がデプロイ先に入っている
- Webhook URLが公開HTTPSでアクセスできる
- `/health` が `ok: true` を返す
- Metaで `messages` を購読している
- Facebookページへ実際にメッセージを送って返信が届く
