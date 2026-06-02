import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


class EmailNotification:
    """
    Reusable Email Notification Service using Gmail SMTP_SSL (port 465).
    Port 587 (STARTTLS) is blocked by Render — use 465 (SSL) instead.
    """

    def __init__(self, sender_email, sender_password,
                 smtp_server="smtp.gmail.com", smtp_port=465):
        self.sender_email    = sender_email
        self.sender_password = sender_password
        self.smtp_server     = smtp_server
        self.smtp_port       = smtp_port

    def send_email(self, recipient_email, subject, message_html):
        """
        Send an HTML email notification.
        :param recipient_email: Receiver email
        :param subject:         Email subject
        :param message_html:    HTML message body
        :return: True if sent successfully, False otherwise
        """
        try:
            msg = MIMEMultipart()
            msg['From']    = self.sender_email
            msg['To']      = recipient_email
            msg['Subject'] = subject
            msg.attach(MIMEText(message_html, 'html'))

            # FIX: use SMTP_SSL on port 465 with a hard timeout.
            # Render blocks port 587 (STARTTLS) — the socket hangs until
            # gunicorn kills the worker (WORKER TIMEOUT / SystemExit: 1).
            with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, timeout=10) as server:
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)

            print(f"Email sent to {recipient_email}")
            return True

        except Exception as e:
            print("EMAIL ERROR:", e)
            return False
