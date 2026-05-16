# X API Search - GitHub Actions Edition

X（Twitter）の特定アカウントから、直近9時間以内のツイートを定期検索し、GitHub Notifications で通知します。

## 機能

- 🔍 **複数アカウント検索**: config.yaml で定義したアカウントを自動検索
- 🔑 **キーワードフィルタ**: 検索文言を配列で管理
- ❤️ **フィルタリング**: いいね数1000以上で絞り込み
- 📡 **コスト最適化**: 複数アカウントを1リクエストで検索（OR クエリ）
- 📧 **HTML メール**: 見やすい表形式でメール送信
  - アカウント | ツイート(先頭30文字) | 投稿時間 | いいね数
  - ツイート内容をクリックで X.com で開く
- 📊 **CSV出力**: GitHub Artifacts に保存
- ⏰ **定期実行**: 3時～21時、3時間ごとに自動実行（GitHub Actions）

## セットアップ

### 1. GitHub Secrets を登録

リポジトリの **Settings → Secrets and variables → Actions** で以下を追加：

| Secret 名 | 値 |
|-----------|-----|
| `X_API_BEARER_TOKEN` | X API の Bearer Token |
| `GMAIL_USER` | Gmail アドレス（例: xxx@gmail.com） |
| `GMAIL_PASSWORD` | Gmail アプリパスワード |
| `RECIPIENT_EMAIL` | 検索結果を受け取るメール（例: myokformal@gmail.com） |

### 2. Gmail アプリパスワード取得

1. Google Account → Security
2. App passwords（2段階認証が必須）から生成
3. `GMAIL_PASSWORD` に登録

### 3. 検索対象を設定

`config.yaml` を編集して、アカウントとキーワードを追加します：

```yaml
accounts:
  - "denfaminicogame"
  - "livedoornews"

keywords:
  - "発売"
  - "開催"
```

### 4. 手動実行でテスト

```
GitHub → Actions → X API Search & Email → Run workflow
```

✅ myokformal@gmail.com に HTML 形式のメールが届きます

## 使用方法

### 自動実行

毎日 3時、6時、9時、12時、15時、18時、21時（UTC）に自動実行されます。  
各実行時に直近9時間以内のツイートを検索します。

### 手動実行

GitHub の Actions タブから「Run workflow」で即座に実行可能。

## 検索条件のカスタマイズ

`config.yaml` を編集して検索アカウントとキーワードを管理します。

### アカウントを追加

```yaml
accounts:
  - "denfaminicogame"
  - "livedoornews"
  - "imdb"
```

- `@` マークなしで指定（例：`denfaminicogame` ✓、`@denfaminicogame` ✗）

### キーワードを追加

```yaml
keywords:
  - "発売"
  - "開催"
  - "新作"
```

- キーワードはオプション（指定しなくても動作します）
- 複数キーワードは自動的に OR で繋がります

### クエリ例

```yaml
# シンプル：アカウントのみ
accounts:
  - "denfaminicogame"
  - "livedoornews"
# 生成されるクエリ: (from:denfaminicogame OR from:livedoornews)

# フィルタ付き：アカウント + キーワード
accounts:
  - "denfaminicogame"
keywords:
  - "発売日"
  - "開催予定"
# 生成されるクエリ: from:denfaminicogame (発売日 OR 開催予定)
```

### 設定のグローバル値

`config.yaml` の `global` セクション：

```yaml
global:
  hours: 9       # 検索期間（9時間以内）
  output: "csv"  # 出力形式（table または csv）
```

### 検索パラメータ

- **検索期間**: 直近9時間以内
- **最小いいね数**: 1000（内部で固定）
- **最大取得件数**: 100件

## ファイル構成

```
.
├── .github/
│   └── workflows/
│       └── search.yml            # GitHub Actions ワークフロー
├── config.yaml                   # 検索クエリ定義ファイル
├── search_tweets.py              # ツイート検索スクリプト
├── requirements.txt              # Python 依存関係
└── README.md                      # このファイル
```

## ローカルテスト

### 環境構築

```bash
# 仮想環境作成
python3 -m venv venv
source venv/bin/activate

# 依存関係をインストール
pip install -r requirements.txt
```

### スクリプト実行

```bash
# Bearer Token をセット
export X_API_BEARER_TOKEN="your_bearer_token_here"

# 実行（config.yaml から読み込む）
python search_tweets.py

# CSV形式で出力
python search_tweets.py --output csv

# 別の設定ファイルを使用
python search_tweets.py --config custom.yaml
```

### 出力確認

```bash
cat tweets.csv
```

## X API 従量課金について

### コスト削減の工夫

このスクリプトは X API の従量課金を最小化するため、以下の工夫をしています：

| シナリオ | API コール数 | コスト（月額） |
|--------|-----------|-----------|
| 個別検索（非効率） | 2アカウント × 240回 = **480回** | $2.40 |
| OR統合（2アカウント） | **1リクエスト × 240回 = 240回** | **$1.20** |
| OR統合（12アカウント） | **2リクエスト × 240回 = 480回** | **$2.40** |
| **推奨（10アカウント以下）** | **1リクエスト × 240回 = 240回** | **$1.20** |

### 大量アカウントの自動分割

このスクリプトは**自動的**にアカウント数を管理します：

- **10アカウント以下**: 1リクエストで検索
- **11〜20アカウント**: 2リクエストに自動分割
- **21〜30アカウント**: 3リクエストに自動分割

制限数（10）を超えると自動的に複数リクエストに分割されるため、アカウント数を気にせず追加できます。

### アカウント追加例

```yaml
# ✓ 2個：1リクエスト
accounts:
  - "account1"
  - "account2"

# ✓ 15個：自動的に2リクエスト
accounts:
  - "account1"
  - "account2"
  # ... 省略 ...
  - "account15"

# ✓ 50個まで対応可能：自動的に5リクエスト
# 制限なし！
```

## トラブルシューティング

### ツイートが取得できない

- **Bearer Token が有効か確認**: X Developer Console で再生成してください
- **X API エラー 401**: Bearer Token が正しく設定されているか確認（GitHub Secrets）
- **X API エラー 429**: レート制限に達しました。時間を置いて再実行してください

### メール送信が失敗する

- **Gmail ログイン失敗**: `GMAIL_PASSWORD` が正しいか確認
- **アプリパスワード未設定**: Google Account → Security から 2段階認証を有効化して生成
- **Secrets が未設定**: `GMAIL_USER`, `GMAIL_PASSWORD`, `RECIPIENT_EMAIL` を確認

```bash
# ローカルテスト（メール送信）
export GMAIL_USER="xxx@gmail.com"
export GMAIL_PASSWORD="app-password-here"
python send_email.py tweets.json myokformal@gmail.com
```

### config.yaml が読み込めない

```bash
# YAMLフォーマットエラーを確認
python3 -c "import yaml; yaml.safe_load(open('config.yaml'))"
```

### GitHub Actions が失敗する

1. Actions ログを確認: GitHub → Actions → X API Search & Email → 失敗したワークフロー
2. エラーメッセージから原因を特定
3. Secrets が設定されているか確認（Settings → Secrets and variables → Actions）

## ライセンス

MIT

## 作成日

2026-05-16
