# X API Search - GitHub Actions Edition

X（Twitter）の特定アカウントから、12時間以内のツイートを定期検索し、GitHub Notifications で通知します。

## 機能

- 🔍 **複数クエリ検索**: config.yaml で定義した複数の検索クエリを実行
- ❤️ **フィルタリング**: いいね数で絞り込み
- 📊 **CSV出力**: 検索結果を CSV 形式でエクスポート
- ⏰ **定期実行**: 3時～21時、3時間ごとに自動実行（GitHub Actions）

## セットアップ

### 1. GitHub Secrets を登録

リポジトリの **Settings → Secrets and variables → Actions** で以下を追加：

| Secret 名 | 値 |
|-----------|-----|
| `X_API_BEARER_TOKEN` | X API の Bearer Token（X Developer Console から取得） |

### 2. 検索アカウントを設定

`config.yaml` を編集して、検索対象のアカウントを追加します。良いね数は内部で1000に固定されています：

```yaml
search_configs:
  - name: "電ファミニコゲーマー"
    accounts:
      - "denfaminicogame"
  
  - name: "ニュースサイト"
    accounts:
      - "livedoornews"
      - "imdb"
```

### 3. GitHub Notifications を設定

1. GitHub → Settings → Notifications
2. Email address: ツイート検索結果の通知を受け取るメールアドレスを入力
3. Actions notification email を有効化

### 4. 手動実行でテスト

```
GitHub → Actions → X API Search & Email → Run workflow
```

## 使用方法

### 自動実行

毎日 3時、6時、9時、12時、15時、18時、21時（UTC）に自動実行されます。

### 手動実行

GitHub の Actions タブから「Run workflow」で即座に実行可能。

## 検索条件のカスタマイズ

`config.yaml` を編集して検索アカウントを管理します。

### 新しいアカウントを追加

`config.yaml` の `search_configs` に新しいエントリを追加します：

```yaml
search_configs:
  - name: "グループ名"
    accounts:
      - "account1"
      - "account2"
      - "account3"
```

### アカウント名の注意事項

- `@` マークなしで指定（例：`denfaminicogame` ✓、`@denfaminicogame` ✗）
- 複数アカウントを配列で管理可能
- 同一グループ内で複数アカウントを指定できます

### 設定のグローバル値

`config.yaml` の `global` セクション：

```yaml
global:
  hours: 12      # 検索期間（12時間以内）
  output: "csv"  # 出力形式（table または csv）
```

### 良いね数について

- スクリプト内部で **1000** に固定されています
- `config.yaml` での個別設定は不要です

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

## トラブルシューティング

### ツイートが取得できない

- **Bearer Token が有効か確認**: X Developer Console で再生成してください
- **X API エラー 401**: Bearer Token が正しく設定されているか確認（GitHub Secrets）
- **X API エラー 429**: レート制限に達しました。時間を置いて再実行してください

### config.yaml が読み込めない

```bash
# YAMLフォーマットエラーを確認
python3 -c "import yaml; yaml.safe_load(open('config.yaml'))"
```

### GitHub Actions が失敗する

1. Actions ログを確認: GitHub → Actions → X API Search & Email → 失敗したワークフロー
2. エラーメッセージから原因を特定
3. Secrets が設定されているか確認（Settings → Secrets and variables → Actions）

### 通知が届かない

- GitHub Notifications 設定を確認（Settings → Notifications）
- メールアドレスが正しいか確認
- メールフィルタで GitHub メールが除外されていないか確認

## ライセンス

MIT

## 作成日

2026-05-16
