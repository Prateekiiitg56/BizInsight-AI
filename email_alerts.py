import os
import smtplib
import logging
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()

EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

logger = logging.getLogger(__name__)


def send_negative_alert(
    receiver_email, negative_percentage, total_reviews, top_issues=None
):
    """
    Send email alert when negative sentiment becomes high.
    """

    if top_issues is None:
        top_issues = []

    subject = "⚠️ BizInsight AI Alert - High Negative Sentiment"

    issue_text = "\n".join([f"- {issue}" for issue in top_issues])

    body = f"""
Hello,

BizInsight AI detected an unusually high level of negative customer feedback.

Negative Reviews: {negative_percentage:.2f}%
Total Reviews Analysed: {total_reviews}

Top Issues:
{issue_text if issue_text else "No major issues identified"}

Please review your dashboard for more details.

Regards,
BizInsight AI
"""

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = receiver_email

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as smtp:

            smtp.ehlo()
            smtp.starttls()
            smtp.ehlo()

            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)

            smtp.send_message(msg)

        logger.info(f"Alert email sent successfully to {receiver_email}")

        return True

    except Exception as e:
        print("SMTP ERROR:", e)
        logging.error(f"Failed to send email to {receiver_email}: {e}")
        return False
