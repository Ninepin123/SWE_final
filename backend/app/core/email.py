"""Email 寄送工具：透過 SMTP（預設 Gmail）寄出通知信。

啟用方式（在 backend/.env 設定）：
    EMAIL_ENABLED=true
    SMTP_USER=youraccount@gmail.com
    SMTP_PASSWORD=xxxxxxxxxxxxxxxx     # Gmail「應用程式密碼」，不是平常登入的密碼！

重點：Gmail 不接受用一般帳號密碼透過 SMTP 登入。
你必須先在 Google 帳號開啟「兩步驟驗證」，再產生一組 16 碼的
「應用程式密碼」(App Password)，把那組密碼填到 SMTP_PASSWORD。

未啟用（EMAIL_ENABLED=false，預設）時 send_email() 會直接回傳 DISABLED，
不會嘗試連線，所以平常開發不用設定任何東西。
"""
from __future__ import annotations

import smtplib
import ssl
from email.message import EmailMessage

from app.core.config import settings


def send_email(to_email: str, subject: str, body: str | None = None) -> tuple[str, str | None]:
    """寄一封純文字信。

    回傳 (status, error_message)：
        - "SENT"     寄送成功
        - "DISABLED" 功能未啟用（EMAIL_ENABLED=false）
        - "FAILED"   設定不全或寄送失敗，error_message 會帶原因

    這個函式「不會」raise——寄信失敗絕對不能讓站內通知 / 主流程崩潰。
    """
    if not settings.email_enabled:
        return "DISABLED", None

    if not settings.smtp_user or not settings.smtp_password:
        return "FAILED", "SMTP_USER / SMTP_PASSWORD 未設定"

    if not to_email:
        return "FAILED", "收件者 email 為空"

    msg = EmailMessage()
    msg["From"] = settings.smtp_from or settings.smtp_user
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body or "")

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as server:
            server.starttls(context=context)
            server.login(settings.smtp_user, settings.smtp_password)
            server.send_message(msg)
        return "SENT", None
    except Exception as exc:  # noqa: BLE001 - 寄信失敗只記錄，不往上拋
        return "FAILED", str(exc)
