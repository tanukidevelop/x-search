#!/usr/bin/env python3
"""
X API ツイート検索スクリプト
- config.yaml で定義された複数の検索クエリを実行
- 12時間以内のツイートをいいね数でフィルタリング
- Markdown テーブル形式で表示 & CSV出力

使用方法:
  python search_tweets.py                    # config.yaml から実行
  python search_tweets.py --output csv       # CSV形式で出力
  python search_tweets.py --config custom.yaml  # 別のconfig使用
"""

import os
import json
import requests
import argparse
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any
from urllib.parse import urlencode
import csv
import yaml

DEFAULT_CONFIG = "config.yaml"
DEFAULT_MAX_RESULTS = 100
MIN_LIKES = 1000  # 内部で固定
MAX_ACCOUNTS_PER_REQUEST = 10  # 1リクエストあたりの最大アカウント数


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
        指定アカウントから9時間以内のツイートを検索
        """
        # 9時間以内のツイートに限定
        now = datetime.now(timezone.utc)
        start_time = (now - timedelta(hours=9)).isoformat().replace("+00:00", "Z")

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
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "id",
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
                        "id": tweet["id"],
                        "username": tweet["username"],
                        "text": tweet["text"],
                        "likes": tweet["public_metrics"]["like_count"],
                        "created_at": tweet["created_at"],
                        "url": f"https://x.com/{tweet['username']}/status/{tweet['id']}",
                    }
                )

        print(f"✅ CSV エクスポート完了: {filename} ({len(all_tweets)}件)")

    def export_json(self, all_tweets: List[Dict[str, Any]], filename: str = "tweets.json"):
        """JSON形式でエクスポート（メール送信用）"""
        if not all_tweets:
            print("✅ エクスポートするツイートがありません")
            with open(filename, "w", encoding="utf-8") as f:
                json.dump([], f, ensure_ascii=False)
            return

        data = []
        for tweet in all_tweets:
            data.append(
                {
                    "id": tweet["id"],
                    "username": tweet["username"],
                    "text": tweet["text"],
                    "public_metrics": tweet["public_metrics"],
                    "created_at": tweet["created_at"],
                }
            )

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"✅ JSON エクスポート完了: {filename}")


def load_config(config_file: str = DEFAULT_CONFIG) -> Dict[str, Any]:
    """config.yaml から検索クエリを読み込む"""
    if not os.path.exists(config_file):
        raise FileNotFoundError(f"{config_file} が見つかりません")

    with open(config_file, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def build_or_query(accounts: List[str], keywords: List[str] = None) -> str:
    """アカウント配列とキーワード配列から OR クエリを生成"""
    if not accounts:
        raise ValueError("accounts が空です")

    # アカウント部分を生成
    if len(accounts) == 1:
        account_query = f"from:{accounts[0]}"
    else:
        account_query = f"({' OR '.join(f'from:{acc}' for acc in accounts)})"

    # キーワードがある場合は追加
    if keywords:
        if len(keywords) == 1:
            keyword_query = keywords[0]
        else:
            keyword_query = f"({' OR '.join(keywords)})"
        return f"{account_query} {keyword_query}"

    return account_query


def split_accounts(accounts: List[str], max_per_request: int = MAX_ACCOUNTS_PER_REQUEST) -> List[List[str]]:
    """アカウント数が多い場合はグループに分割"""
    if len(accounts) <= max_per_request:
        return [accounts]

    groups = []
    for i in range(0, len(accounts), max_per_request):
        groups.append(accounts[i:i + max_per_request])
    return groups


def search_by_query(searcher: 'XAPISearcher', query: str, min_likes: int, max_results: int) -> List[Dict[str, Any]]:
    """カスタムクエリで検索"""
    now = datetime.now(timezone.utc)
    start_time = (now - timedelta(hours=9)).isoformat().replace("+00:00", "Z")

    url = f"{searcher.BASE_URL}/tweets/search/recent"
    params = {
        "query": query,
        "start_time": start_time,
        "max_results": min(max_results, 100),
        "tweet.fields": "created_at,public_metrics,author_id",
        "expansions": "author_id",
        "user.fields": "username",
    }

    try:
        response = requests.get(url, params=params, headers=searcher.headers)
        response.raise_for_status()
        data = response.json()

        username_map = {}
        if "includes" in data and "users" in data["includes"]:
            for user in data["includes"]["users"]:
                username_map[user["id"]] = user["username"]

        tweets = []
        for tweet in data.get("data", []):
            author_id = tweet.get("author_id")
            tweet["username"] = username_map.get(author_id, "unknown")
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




def main():
    parser = argparse.ArgumentParser(
        description="X API ツイート検索スクリプト（config.yaml から実行）"
    )
    parser.add_argument(
        "--config",
        type=str,
        default=DEFAULT_CONFIG,
        help=f"設定ファイルパス（デフォルト: {DEFAULT_CONFIG}）",
    )
    parser.add_argument(
        "--output",
        choices=["table", "csv"],
        help="出力形式（デフォルト: config.yaml から使用）",
    )

    args = parser.parse_args()

    try:
        config = load_config(args.config)

        if "accounts" not in config:
            raise ValueError("config.yaml に accounts が定義されていません")

        accounts = config.get("accounts", [])
        keywords = config.get("keywords", [])
        output_format = args.output or config.get("global", {}).get("output", "table")

        print(f"🔍 X API ツイート検索")
        print(f"📅 期間: 9時間以内")
        print(f"❤️ 最小いいね数: {MIN_LIKES}")
        print(f"📄 アカウント数: {len(accounts)}")
        if keywords:
            print(f"🔑 キーワード数: {len(keywords)}")
        print()

        searcher = XAPISearcher()
        all_tweets = []

        # アカウント数が多い場合は複数リクエストに分割
        account_groups = split_accounts(accounts, MAX_ACCOUNTS_PER_REQUEST)
        request_count = len(account_groups)

        print(f"📡 APIリクエスト: {request_count}回\n")

        for idx, group in enumerate(account_groups, 1):
            query = build_or_query(group, keywords)
            print(f"[{idx}/{request_count}] 🔎 検索クエリ: {query}")

            tweets = search_by_query(
                searcher,
                query=query,
                min_likes=MIN_LIKES,
                max_results=DEFAULT_MAX_RESULTS,
            )
            all_tweets.extend(tweets)
            print(f"       ✅ {len(tweets)}件取得\n")

        # 新しい順でソート
        all_tweets.sort(
            key=lambda x: datetime.fromisoformat(
                x["created_at"].replace("Z", "+00:00")
            ),
            reverse=True,
        )

        # 出力
        if output_format == "table":
            searcher.print_markdown_table(all_tweets)
        elif output_format == "csv":
            searcher.export_csv(all_tweets)

    except FileNotFoundError as e:
        print(f"❌ エラー: {e}")
        return 1
    except ValueError as e:
        print(f"❌ エラー: {e}")
        return 1
    except Exception as e:
        print(f"❌ 予期しないエラー: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
