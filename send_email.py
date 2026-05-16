#!/usr/bin/env python3
"""
メール送信スクリプト
検索結果を HTML テーブル形式でメール送信
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any


def format_time_ago(created_at: str) -> str:
    """投稿からの経過時間を計算（例：12時間前）"""
    tweet_time = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
    now = datetime.now(timezone.utc)
    diff = now - tweet_time

    if diff.total_seconds() < 60:
        return "今"
    elif diff.total_seconds() < 3600:
        minutes = int(diff.total_seconds() / 60)
        return f"{minutes}分前"
    elif diff.total_seconds() < 86400:
        hours = int(diff.total_seconds() / 3600)
        return f"{hours}時間前"
    else:
        days = int(diff.total_seconds() / 86400)
        return f"{days}日前"


def create_html_table(tweets: List[Dict[str, Any]]) -> str:
    """ツイートを HTML テーブルで生成"""
    if not tweets:
        return "<p style='font-size: 1.1em; color: #666;'>0件でした</p>"

    html = '<table style="border-collapse: collapse; width: 100%; margin-top: 20px;">'
    html += """
    <tr style="background-color: #f0f0f0; border-bottom: 2px solid #333;">
        <th style="padding: 12px; text-align: left; border-right: 1px solid #ddd; width: 12%;">ユーザーID</th>
        <th style="padding: 12px; text-align: left; border-right: 1px solid #ddd; width: 12%;">アカウント</th>
        <th style="padding: 12px; text-align: left; border-right: 1px solid #ddd; width: 40%;">ツイート内容</th>
        <th style="padding: 12px; text-align: center; border-right: 1px solid #ddd; width: 12%;">投稿時間</th>
        <th style="padding: 12px; text-align: right; width: 12%;">いいね数</th>
    </tr>
    """

    for tweet in tweets:
        author_id = tweet.get("author_id", "N/A")
        username = tweet["username"]
        text = tweet["text"].replace("<", "&lt;").replace(">", "&gt;")[:30]
        likes = tweet["public_metrics"]["like_count"]
        created_at = tweet["created_at"]
        time_ago = format_time_ago(created_at)
        tweet_id = tweet["id"]
        url = f"https://x.com/{username}/status/{tweet_id}"

        html += f"""
    <tr style="border-bottom: 1px solid #ddd;">
        <td style="padding: 12px; border-right: 1px solid #ddd; font-size: 0.9em; color: #666;">{author_id}</td>
        <td style="padding: 12px; border-right: 1px solid #ddd;">
            <a href="https://x.com/{username}" style="color: #1DA1F2; text-decoration: none; font-weight: bold;">@{username}</a>
        </td>
        <td style="padding: 12px; border-right: 1px solid #ddd;">
            <a href="{url}" style="color: #1DA1F2; text-decoration: none;">{text}</a>
        </td>
        <td style="padding: 12px; text-align: center; border-right: 1px solid #ddd; font-size: 0.9em; color: #666;">{time_ago}</td>
        <td style="padding: 12px; text-align: right;">{likes:,}</td>
    </tr>
        """

    html += "</table>"
    return html


def send_email(recipient: str, subject: str, html_content: str, tweet_count: int = 0) -> bool:
    """Gmail SMTP でメール送信"""
    gmail_user = os.getenv("GMAIL_USER")
    gmail_password = os.getenv("GMAIL_PASSWORD")

    # 件名を動的に生成
    if tweet_count == 0:
        subject = "Amazonアフィ：該当無し"
    else:
        subject = f"Amazonアフィ：{tweet_count}件の候補ツイート"

    if not gmail_user or not gmail_password:
        print("❌ エラー: GMAIL_USER または GMAIL_PASSWORD が未設定です")
        return False

    try:
        # HTML メール構成
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = gmail_user
        message["To"] = recipient

        # HTML パート
        html_part = MIMEText(
            f"""
            <html>
                <head>
                    <meta charset="UTF-8">
                    <style>
                        body {{ font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif; color: #333; }}
                        h2 {{ color: #1DA1F2; }}
                        .header {{ background-color: #f5f5f5; padding: 20px; border-radius: 5px; }}
                    </style>
                </head>
                <body>
                    <div class="header">
                        <h2>🔍 X API ツイート検索結果</h2>
                        <p>実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    </div>
                    {html_content}
                    <hr style="margin-top: 30px; border: none; border-top: 1px solid #ddd;">
                    <p style="color: #999; font-size: 0.9em;">
                        このメールは自動で送信されました。<br>
                        <a href="https://github.com/tanukidevelop/x-search" style="color: #1DA1F2;">
                            GitHub リポジトリ
                        </a>
                    </p>
                </body>
            </html>
            """,
            "html",
            "utf-8"
        )
        message.attach(html_part)

        # SMTP で送信
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=10) as server:
            server.login(gmail_user, gmail_password)
            server.send_message(message)

        print(f"✅ メール送信完了: {recipient}")
        return True

    except smtplib.SMTPAuthenticationError:
        print("❌ エラー: Gmail ログイン失敗")
        print("   GMAIL_PASSWORD が正しいか確認してください")
        return False
    except Exception as e:
        print(f"❌ メール送信エラー: {e}")
        return False


if __name__ == "__main__":
    import sys
    import json

    # 使用例: python send_email.py <json_file> <recipient>
    if len(sys.argv) < 3:
        print("使用方法: python send_email.py <json_file> <recipient_email>")
        sys.exit(1)

    json_file = sys.argv[1]
    recipient = sys.argv[2]

    # JSON からツイートを読み込む
    try:
        with open(json_file, "r", encoding="utf-8") as f:
            tweets = json.load(f)
    except FileNotFoundError:
        print(f"❌ エラー: {json_file} が見つかりません")
        sys.exit(1)

    # HTML テーブルを生成
    html_table = create_html_table(tweets)

    # メール送信（件数を渡して件名を自動生成）
    success = send_email(
        recipient=recipient,
        subject="",  # send_email() 内で動的に生成
        html_content=html_table,
        tweet_count=len(tweets)
    )

    sys.exit(0 if success else 1)
