import hashlib
import hmac
import os
import time
from typing import Any

import requests


def verify_slack_signature(body: bytes, signature: str, timestamp: str) -> bool:
    signing_secret = os.getenv("SLACK_SIGNING_SECRET", "")

    # Reject old timestamps (prevent replay attacks)
    if abs(time.time() - int(timestamp)) > 60 * 5:
        return False

    sig_basestring = f"v0:{timestamp}:{body.decode()}"
    my_signature = (
        "v0="
        + hmac.new(
            signing_secret.encode(), sig_basestring.encode(), hashlib.sha256
        ).hexdigest()
    )

    return hmac.compare_digest(my_signature, signature)


def send_slack_message(
    channel_id: str,
    text: str,
    token: str,
) -> Any:
    response = requests.post(
        "https://slack.com/api/chat.postMessage",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        json={
            "channel": channel_id,
            "text": text,
        },
    )
    return response.json()
