#!/usr/bin/env python3
"""
メール送信スクリプト
検索結果を HTML テーブル形式でメール送信
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import List, Dict, Any


def create_html_table(tweets: List[Dict[str, Any]]) -> str:
    """ツイートを HTML テーブルで生成"""
    if not tweets:
        return "<p>条件に合うツイートはありません。</p>"

    html = '<table style="border-collapse: collapse; width: 100%; margin-top: 20px;">'
    html += """
    <tr style="background-color: #f0f0f0; border-bottom: 2px solid #333;">
        <th style="padding: 10px; text-align: left; border-right: 1px solid #ddd;">アカウント</th>
        <th style="padding: 10px; text-align: left; border-right: 1px solid #ddd;">ツイート内容</th>
        <th style="padding: 10px; text-align: center; border-right: 1px solid #ddd;">いいね数</th>
        <th style="padding: 10px; text-align: center;">投稿時刻</th>
    </tr>
    """

    for tweet in tweets:
        username = tweet["username"]
        text = tweet["text"].replace("<", "&lt;").replace(">", "&gt;")[:150]
        likes = tweet["public_metrics"]["like_count"]
        created_at = tweet["created_at"]
        tweet_id = tweet["id"]
        url = f"https://x.com/{username}/status/{tweet_id}"

        html += f"""
    <tr style="border-bottom: 1px solid #ddd;">
        <td style="padding: 10px; border-right: 1px solid #ddd;">
            <a href="https://x.com/{username}" style="color: #1DA1F2; text-decoration: none;">@{username}</a>
        </td>
        <td style="padding: 10px; border-right: 1px solid #ddd;">
            <a href="{url}" style="color: #1DA1F2; text-decoration: none;">{text}...</a>
        </td>
        <td style="padding: 10px; text-align: center; border-right: 1px solid #ddd;">{likes:,}</td>
        <td style="padding: 10px; text-align: center; font-size: 0.9em; color: #666;">{created_at[:10]}</td>
    </tr>
        """

    html += "</table>"
    return html


def send_email(recipient: str, subject: str, html_content: str) -> bool:
    """Gmail SMTP でメール送信"""
    gmail_user = os.getenv("GMAIL_USER")
    gmail_password = os.getenv("GMAIL_PASSWORD")

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

    # メール送信
    success = send_email(
        recipient=recipient,
        subject=f"🔍 X API 検索結果 - {datetime.now().strftime('%Y年%m月%d日')}",
        html_content=html_table
    )

    sys.exit(0 if success else 1)
