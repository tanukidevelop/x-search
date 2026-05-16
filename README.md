# X API Search - GitHub Actions Edition

X（Twitter）の特定アカウントから、24時間以内のツイートを定期検索し、メールで結果を送信します。

## 機能

- 🔍 **複数アカウント検索**: 指定アカウントから24時間以内のツイートを検索
- ❤️ **フィルタリング**: いいね数で絞り込み
- 📧 **メール送信**: CSV 形式で結果をメール送信
- ⏰ **定期実行**: 3時～21時、3時間ごとに自動実行（GitHub Actions）

## セットアップ

### 1. GitHub Secrets を登録

リポジトリの **Settings → Secrets and variables → Actions** で以下を追加：

| Secret 名 | 値 |
|-----------|-----|
| `X_API_BEARER_TOKEN` | X API の Bearer Token |
| `GMAIL_USER` | Gmail アドレス（例: xxx@gmail.com） |
| `GMAIL_PASSWORD` | Gmail アプリパスワード（参照: 下記） |
| `RECIPIENT_EMAIL` | 受信メールアドレス |

### 2. Gmail アプリパスワード取得

1. Google Account → Security
2. App passwords を生成（2段階認証が必須）
3. `GMAIL_PASSWORD` に登録

### 3. 手動実行でテスト

```
GitHub → Actions → X API Search & Email → Run workflow
```

## 使用方法

### 自動実行

毎日 3時、6時、9時、12時、15時、18時、21時（UTC）に実行します。

### 手動実行

GitHub の Actions タブから「Run workflow」で即座に実行可能。

## 検索条件のカスタマイズ

`.github/workflows/search.yml` の以下を編集：

```yaml
--min_likes 1000              # いいね数（デフォルト: 1000）
--accounts "denfaminicogame"  # アカウント名（カンマ区切り）
```

例: 複数アカウント検索

```yaml
--accounts "denfaminicogame,livedoornews"
```

## ファイル構成

```
.
├── .github/
│   └── workflows/
│       └── search.yml            # GitHub Actions ワークフロー
├── search_tweets.py              # ツイート検索スクリプト
├── send_email.py                 # メール送信スクリプト
└── README.md                      # このファイル
```

## ローカルテスト

```bash
# 1. Bearer Token をセット
export X_API_BEARER_TOKEN="xxxxx"

# 2. スクリプト実行
python search_tweets.py --min_likes 1000

# 3. CSV 出力確認
cat tweets.csv
```

## トラブルシューティング

### メール送信が失敗する

- Gmail アプリパスワードが正しいか確認
- 2段階認証が有効か確認
- Secrets に正しい値が登録されているか確認

### ツイートが取得できない

- Bearer Token が有効か確認（X Developer Console で再生成）
- アカウント名が正しいか確認（@ なし）

## ライセンス

MIT

## 作成日

2026-05-16
