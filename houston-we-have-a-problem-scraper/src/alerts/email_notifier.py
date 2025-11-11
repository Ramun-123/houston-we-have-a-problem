import smtplib
from email.mime.text import MIMEText
from typing import Optional

class EmailNotifier:
    def __init__(
        self,
        host: str,
        port: int = 587,
        username: Optional[str] = None,
        password: Optional[str] = None,
        from_addr: str = "",
        to_addr: str = "",
        use_tls: bool = True,
        enabled: bool = False,
    ) -> None:
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.from_addr = from_addr
        self.to_addr = to_addr
        self.use_tls = use_tls
        self.enabled = enabled

    def send(self, subject: str, body: str) -> bool:
        if not self.enabled:
            return False
        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = self.from_addr
        msg["To"] = self.to_addr

        if self.use_tls:
            server = smtplib.SMTP(self.host, self.port, timeout=10)
            server.starttls()
        else:
            server = smtplib.SMTP_SSL(self.host, self.port, timeout=10)

        try:
            if self.username and self.password:
                server.login(self.username, self.password)
            server.sendmail(self.from_addr, [self.to_addr], msg.as_string())
            return True
        finally:
            try:
                server.quit()
            except Exception:
                pass