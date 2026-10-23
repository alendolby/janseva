import smtplib
from email.message import EmailMessage
from sqlalchemy import select
from app.core.config import settings
from app.models.entities import Notification, User, OfficeUser

def notify(db, case, message):
    user_ids = {case.citizen_id}
    if case.assigned_office_id:
        user_ids.update(db.scalars(select(OfficeUser.user_id).where(OfficeUser.office_id == case.assigned_office_id)))
    for user_id in user_ids:
        db.add(Notification(user_id=user_id, case_id=case.id, message=f"{case.public_case_id}: {message}"))

def deliver_email(email, subject, body):
    cfg = settings()
    if not cfg.smtp_host:
        return False  # In-app channel is always used, SMTP is explicitly opt-in.
    msg = EmailMessage(); msg["To"] = email; msg["From"] = cfg.smtp_from
    msg["Subject"] = subject; msg.set_content(body)
    with smtplib.SMTP(cfg.smtp_host, cfg.smtp_port, timeout=10) as smtp:
        if cfg.smtp_tls: smtp.starttls()
        if cfg.smtp_user: smtp.login(cfg.smtp_user, cfg.smtp_password)
        smtp.send_message(msg)
    return True
