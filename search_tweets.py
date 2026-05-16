#!/usr/bin/env python3
"""
X API ツイート検索スクリプト
- 複数アカウントから12時間以内のツイートを検索
- いいね数でフィルタリング
- Markdown テーブル形式で表示 & CSV出力

使用方法:
  python search_tweets.py
  python search_tweets.py --min_likes 1000
  python search_tweets.py --output csv
"""

import os
import json
import requests
import argparse
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any
from urllib.parse import urlencode
import csv

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ⚙️ 設定セクション
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ACCOUNTS = [
    "denfaminicogame",
]

DEFAULT_MIN_LIKES = 1000
DEFAULT_MAX_RESULTS = 100
OUTPUT_FORMAT = "table"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class XAPISearcher:
    """X API ツイート検索クラス"""

    BASE_URL = "https://api.x.com/2"

    def __init__(self, bearer_token: str = None):
        self.bearer_token = bearer_token or os.getenv("X_API_BEARER_TOKEN")
        if not self.bearer_token:
            raise ValueError("X_API_BEARER_TOKEN 環境変数が未設定です")

        self.headers = {
            "Authorization": self.bearer_token,
            "Content-Type": "application/json",
        }

    def search_tweets(
        self,
        account: str,
        min_likes: int = 1000,
        max_results: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        指定アカウントから12時間以内のツイートを検索
        """
        # 12時間以内のツイートに限定
        now = datetime.now(timezone.utc)
        start_time = (now - timedelta(hours=12)).isoformat().replace("+00:00", "Z")

        query = f"from:{account}"

        url = f"{self.BASE_URL}/tweets/search/recent"
        params = {
            "query": query,
            "start_time": start_time,
            "max_results": min(max_results, 100),
            "tweet.fields": "created_at,public_metrics",
            "expansions": "author_id",
            "user.fields": "username",
        }

        try:
            response = requests.get(url, params=params, headers=self.headers)
            response.raise_for_status()
            data = response.json()

            username = None
            if "includes" in data and "users" in data["includes"]:
                username = data["includes"]["users"][0]["username"]

            tweets = []
            for tweet in data.get("data", []):
                tweet["username"] = username
                if tweet["public_metrics"]["like_count"] >= min_likes:
                    tweets.append(tweet)

            return tweets

        except requests.exceptions.HTTPError as e:
            print(f"❌ API エラー: {e.response.status_code}")
            print(f"   詳細: {e.response.text}")
            return []
        except Exception as e:
            print(f"❌ エラー: {e}")
            return []

    def format_time_ago(self, created_at: str) -> str:
        """投稿からの経過時間を計算"""
        tweet_time = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        diff = now - tweet_time

        if diff.total_seconds() < 60:
            return "今"
        elif diff.total_seconds() < 3600:
            minutes = int(diff.total_seconds() / 60)
            return f"{minutes}分前"
        else:
            hours = int(diff.total_seconds() / 3600)
            return f"{hours}時間前"

    def print_markdown_table(self, all_tweets: List[Dict[str, Any]]):
        """Markdown テーブル形式で表示"""
        if not all_tweets:
            print("✅ 条件に合うツイートはありません")
            return

        print(f"\n# 🐦 X API 検索結果: {len(all_tweets)}件\n")
        
        # Markdown テーブル
        print("| アカウント名 | ツイート内容 | リンク | いいね数 | 経過時間 |")
        print("|-----------|-----------|--------|--------|---------|")
        
        for tweet in all_tweets:
            username = tweet["username"]
            text = tweet["text"].replace("\n", " ")[:80]
            tweet_id = tweet["id"]
            likes = tweet["public_metrics"]["like_count"]
            time_ago = self.format_time_ago(tweet["created_at"])
            url = f"https://x.com/{username}/status/{tweet_id}"
            
            print(f"| @{username} | {text}... | [link]({url}) | {likes:,} | {time_ago} |")

    def export_csv(self, all_tweets: List[Dict[str, Any]], filename: str = "tweets.csv"):
        """CSV形式でエクスポート"""
        if not all_tweets:
            print("✅ エクスポートするツイートがありません")
            return

        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "username",
                    "text",
                    "likes",
                    "created_at",
                    "url",
                ],
            )
            writer.writeheader()

            for tweet in all_tweets:
                writer.writerow(
                    {
                        "username": tweet["username"],
                        "text": tweet["text"],
                        "likes": tweet["public_metrics"]["like_count"],
                        "created_at": tweet["created_at"],
                        "url": f"https://x.com/{tweet['username']}/status/{tweet['id']}",
                    }
                )

        print(f"✅ CSV エクスポート完了: {filename}")


def main():
    parser = argparse.ArgumentParser(
        description="X API ツイート検索スクリプト（12時間以内）"
    )
    parser.add_argument(
        "--min_likes",
        type=int,
        default=DEFAULT_MIN_LIKES,
        help=f"最小いいね数（デフォルト: {DEFAULT_MIN_LIKES}）",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=DEFAULT_MAX_RESULTS,
        help=f"取得件数（デフォルト: {DEFAULT_MAX_RESULTS}）",
    )
    parser.add_argument(
        "--output",
        choices=["table", "csv"],
        default=OUTPUT_FORMAT,
        help="出力形式（デフォルト: table）",
    )
    parser.add_argument(
        "--accounts",
        type=str,
        help="検索アカウント（カンマ区切り）",
    )

    args = parser.parse_args()

    accounts = args.accounts.split(",") if args.accounts else ACCOUNTS

    print(f"🔍 X API ツイート検索")
    print(f"📅 期間: 12時間以内")
    print(f"❤️ フィルタ: {args.min_likes}いいね以上")
    print(f"👤 アカウント: {', '.join(accounts)}")

    try:
        searcher = XAPISearcher()
        all_tweets = []

        for account in accounts:
            print(f"\n📥 {account} を検索中...")
            tweets = searcher.search_tweets(
                account=account,
                min_likes=args.min_likes,
                max_results=args.limit,
            )
            all_tweets.extend(tweets)
            print(f"   ✅ {len(tweets)}件取得")

        # 新しい順でソート
        all_tweets.sort(
            key=lambda x: datetime.fromisoformat(
                x["created_at"].replace("Z", "+00:00")
            ),
            reverse=True,
        )

        # 出力
        if args.output == "table":
            searcher.print_markdown_table(all_tweets)
        elif args.output == "csv":
            searcher.export_csv(all_tweets)

    except ValueError as e:
        print(f"❌ エラー: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
