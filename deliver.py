"""Send an archived product intelligence brief by email or Slack."""
import argparse
from email import policy
from email.message import EmailMessage
import json
import os
import smtplib
import ssl
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen


def setting(name):
    value = os.getenv(name, "").strip()
    if not value:
        raise ValueError(f"Set {name} before running delivery")
    return value


def email_report(report, period_end):
    host = setting("PIC_SMTP_HOST")
    sender = setting("PIC_EMAIL_FROM")
    recipients = setting("PIC_EMAIL_TO")
    username = os.getenv("PIC_SMTP_USERNAME")
    password = os.getenv("PIC_SMTP_PASSWORD")
    if bool(username) != bool(password):
        raise ValueError("Set both PIC_SMTP_USERNAME and PIC_SMTP_PASSWORD to authenticate")
    security = os.getenv("PIC_SMTP_SECURITY", "starttls")
    if security not in ("starttls", "ssl"):
        raise ValueError("PIC_SMTP_SECURITY must be starttls or ssl")
    port = int(os.getenv("PIC_SMTP_PORT", "465" if security == "ssl" else "587"))
    message = EmailMessage(policy=policy.SMTP)
    message["From"] = sender
    message["To"] = recipients
    message["Subject"] = f"Product intelligence brief | Week ending {period_end}"
    message.set_content(report)
    context = ssl.create_default_context()
    if security == "ssl":
        connection = smtplib.SMTP_SSL(host, port, timeout=30, context=context)
    else:
        connection = smtplib.SMTP(host, port, timeout=30)
    with connection as smtp:
        if security == "starttls":
            smtp.starttls(context=context)
        if username:
            smtp.login(username, password)
        refused = smtp.send_message(message)
    if refused:
        raise ValueError("SMTP refused one or more recipients. Check delivery before retrying.")


def slack_report(report):
    webhook = setting("PIC_SLACK_WEBHOOK_URL")
    url = urlsplit(webhook)
    if (url.scheme != "https" or url.netloc not in ("hooks.slack.com", "hooks.slack-gov.com")
            or not url.path.startswith("/services/")):
        raise ValueError("PIC_SLACK_WEBHOOK_URL must be a Slack incoming webhook")
    if len(report) > 39000:
        raise ValueError("Brief exceeds the Slack message limit. Shorten the report before delivery.")
    payload = {"text": report, "mrkdwn": False, "unfurl_links": False, "unfurl_media": False}
    request = Request(webhook, data=json.dumps(payload).encode("utf-8"),
                      headers={"Content-Type": "application/json"}, method="POST")
    with urlopen(request, timeout=30) as response:
        if response.status != 200 or response.read(32).strip() != b"ok":
            raise ValueError("Slack did not acknowledge the message")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("channel", choices=("email", "slack"))
    args = parser.parse_args()
    try:
        payload = json.load(sys.stdin)
        if args.channel == "email":
            email_report(payload["report"], payload["period_end"])
        else:
            slack_report(payload["report"])
    except HTTPError as error:
        sys.exit(f"Slack delivery failed with HTTP {error.code}")
    except (URLError, OSError) as error:
        sys.exit(f"{args.channel} delivery failed ({type(error).__name__})")
    except (KeyError, TypeError):
        sys.exit("Expected a JSON delivery request with report and period_end")
    except ValueError as error:
        sys.exit(str(error))
    print(json.dumps({"channel": args.channel, "accepted": True}))


if __name__ == "__main__":
    main()
