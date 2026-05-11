import smtplib

from email.mime.text import MIMEText

from email.mime.multipart import MIMEMultipart

from dotenv import load_dotenv

import os


load_dotenv()


EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")

EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")


def send_email(
    recipient_email,
    subject,
    body
):

    try:

        msg = MIMEMultipart()

        msg["From"] = EMAIL_ADDRESS

        msg["To"] = recipient_email

        msg["Subject"] = subject

        msg.attach(
            MIMEText(body, "plain")
        )

        server = smtplib.SMTP(
            "smtp.gmail.com",
            587
        )

        server.starttls()

        server.login(
            EMAIL_ADDRESS,
            EMAIL_PASSWORD
        )

        server.sendmail(
            EMAIL_ADDRESS,
            recipient_email,
            msg.as_string()
        )

        server.quit()

        return True

    except Exception as e:

        print("SMTP Error:", e)

        return False