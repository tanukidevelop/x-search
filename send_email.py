#!/usr/bin/env python3
"""
CSV結果をメール送信するスクリプト
GitHub Actions から呼ばれる
"""

import os
import smtplib
import csv
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime


def send_email():
    """CSV結果をメール送信"""

    gmail_user = os.getenv("GMAIL_USER")
    gmail_password = os.getenv("GMAIL_PASSWORD")
    recipient_email = os.getenv("RECIPIENT_EMAIL")

    if not all([gmail_user, gmail_password, recipient_email]):
        print("❌ メール設定が不足しています")
        return False

    try:
        # CSV ファイルを読み込み
        csv_file = "tweets.csv"
        if not os.path.exists(csv_file):
            print(f"❌ {csv_file} が見つかりません")
            return False

        # CSV から HTML テーブルを生成
        html_body = generate_html_table(csv_file)

        # メール構築
        msg = MIMEMultipart()
        msg["From"] = gmail_user
        msg["To"] = recipient_email
        msg["Subject"] = f"🐦 X API 検索結果 - {datetime.now().strftime('%Y-%m-%d %H:%M')}"

        msg.attach(MIMEText(html_body, "html"))

        # CSV をアタッチ
        with open(csv_file, "rb") as attachment:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(attachment.read())

        encoders.encode_base64(part)
        part.add_header("Content-Disposition", f"attachment; filename= {csv_file}")
        msg.attach(part)

        # メール送信
        print(f"📧 メール送信中: {recipient_email}")
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(gmail_user, gmail_password)
        server.send_message(msg)
        server.quit()

        print("✅ メール送信成功")
        return True

    except Exception as e:
        print(f"❌ メール送信失敗: {e}")
        return False


def generate_html_table(csv_file: str) -> str:
    """CSV をHTML テーブルに変換"""

    html = """
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body { font-family: 'Segoe UI', Arial, sans-serif; margin: 20px; }
            h1 { color: #1DA1F2; }
            table { border-collapse: collapse; width: 100%; margin-top: 20px; }
            th { background-color: #1DA1F2; color: white; padding: 12px; text-align: left; }
            td { padding: 10px; border-bottom: 1px solid #ddd; }
            tr:hover { background-color: #f5f5f5; }
            a { color: #1DA1F2; text-decoration: none; }
        </style>
    </head>
    <body>
        <h1>🐦 X API ツイート検索結果</h1>
        <p>24時間以内のツイートで、1000いいね以上のものです。</p>
    """

    try:
        with open(csv_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

            if rows:
                html += f"<p><strong>取得件数: {len(rows)}件</strong></p>"
                html += "<table><tr>"

                # ヘッダー
                for header in ["likes", "text", "url"]:
                    html += f"<th>{header}</th>"
                html += "</tr>"

                # データ行
                for row in rows:
                    html += "<tr>"
                    html += f"<td>{row.get('likes', '')}</td>"
                    text = row.get('text', '')[:100]
                    html += f"<td>{text}...</td>"
                    url = row.get('url', '')
                    html += f"<td><a href='{url}'>ツイート</a></td>"
                    html += "</tr>"
            else:
                html += "<p>マッチするツイートはありません</p>"

        html += """
        </table>
        <hr>
        <p style="color: #666; font-size: 12px;">
            このメールは自動で送信されています。<br>
            詳細は GitHub Actions のログを確認してください。
        </p>
    </body>
    </html>
    """

    return html


if __name__ == "__main__":
    send_email()
