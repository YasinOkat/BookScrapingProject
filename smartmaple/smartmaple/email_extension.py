import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


class EmailExtension:
    def __init__(self, from_email, to_email, smtp_server, smtp_port, smtp_username, smtp_password):
        self.from_email = from_email
        self.to_email = to_email
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.smtp_username = smtp_username
        self.smtp_password = smtp_password

    @classmethod
    def from_crawler(cls, crawler):
        from_email = crawler.settings.get('EMAIL_FROM')
        to_email = crawler.settings.get('EMAIL_TO')
        smtp_server = crawler.settings.get('SMTP_SERVER')
        smtp_port = crawler.settings.get('SMTP_PORT')
        smtp_username = crawler.settings.get('SMTP_USERNAME')
        smtp_password = crawler.settings.get('SMTP_PASSWORD')

        return cls(from_email, to_email, smtp_server, smtp_port, smtp_username, smtp_password)

    def open_spider(self, spider):
        logging.getLogger().addHandler(
            EmailLogHandler(self.from_email, self.to_email, self.smtp_server, self.smtp_port, self.smtp_username,
                            self.smtp_password))

    def close_spider(self, spider):
        logging.getLogger().removeHandler(EmailLogHandler)


class EmailLogHandler(logging.Handler):
    def __init__(self, from_email, to_email, smtp_server, smtp_port, smtp_username, smtp_password):
        super().__init__()
        self.from_email = from_email
        self.to_email = to_email
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.smtp_username = smtp_username
        self.smtp_password = smtp_password

    def emit(self, record):
        if record.levelno >= logging.ERROR:
            subject = f"Scrapy Error - {record.name}"
            body = self.format(record)
            self.send_email(subject, body)

    def send_email(self, subject, body):
        msg = MIMEMultipart()
        msg['From'] = self.from_email
        msg['To'] = self.to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(self.smtp_username, self.smtp_password)
            server.send_message(msg)
