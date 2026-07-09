# Playwright Browser UI Automation Mode

このモードは、Meta Graph APIのPage Access Tokenを使わず、Playwrightでブラウザを開いてMessenger画面を操作する方式です。

## 方針

- Facebook / Metaのログインは人間がブラウザで手動実行します。
- Cookieやトークンを抜き取る処理はありません。
- 2FA、CAPTCHA、アクセス制限の回避はしません。
- 既存のログイン済みブラウザプロファイルを `UI_BOT_USER_DATA_DIR` に保存し、次回以降に再利用します。
- 実送信は `--send` を付けたときだけです。標準はdry-runです。
- Facebook UIのDOMは変わりやすいため、セレクタは環境変数で差し替えられる設計です。

## セットアップ

```bash
pip install -e ".[dev]"
python -m playwright install chromium
cp .env.example .env
```

## 1回目: 手動ログイン

```bash
python scripts/run_browser_messenger_bot.py --login-only
```

ブラウザが開いたら、Facebook / Messengerに手動でログインします。2FAが出た場合も通常通り自分で操作します。ログイン状態は `.playwright/facebook-profile` に保存されます。

## dry-runで確認

```bash
python scripts/run_browser_messenger_bot.py --once
```

この状態では返信文は作りますが、送信ボタンは押しません。

## 実際に送信

```bash
python scripts/run_browser_messenger_bot.py --once --send
```

複数件処理する場合:

```bash
python scripts/run_browser_messenger_bot.py --send --max-replies 10
```

## Business Suite Inboxを使う場合

Facebookの通常Messenger URLではなくBusiness SuiteのInboxを使いたい場合は、対象画面をブラウザで開き、そのURLを `--inbox-url` または `.env` に入れます。

```bash
python scripts/run_browser_messenger_bot.py \
  --inbox-url "https://business.facebook.com/latest/inbox/all" \
  --once \
  --send
```

## セレクタ調整

Facebook UIが変わって検出できない場合は `.env` のセレクタを調整します。複数セレクタは `||` で区切ります。

```dotenv
UI_BOT_THREAD_SELECTORS=div[aria-label*="未読"]||div[aria-label*="Unread"]
UI_BOT_MESSAGE_TEXT_SELECTORS=[data-testid="message-container"] [dir="auto"]||[role="main"] [dir="auto"]
UI_BOT_COMPOSER_SELECTORS=div[role="textbox"][contenteditable="true"]
UI_BOT_SEND_BUTTON_SELECTORS=div[aria-label="送信"]||div[aria-label="Send"]
```

## CIでのテスト

GitHub Actionsでは、実Facebookにはログインせず、ローカルHTMLでMessenger風の画面を作ってPlaywrightが次の動作をできるか確認します。

1. 未読スレッドをクリック
2. 受信メッセージ本文を読む
3. 返信ルールから返信文を作る
4. composerへ入力
5. Sendボタンをクリック
6. 画面に送信済みテキストが反映されることを検証

これにより、Playwright操作の基本経路は自動テストできます。実Facebookの画面はログイン状態やUI変更に依存するため、本番ではdry-runでセレクタ確認してから `--send` を使ってください。
