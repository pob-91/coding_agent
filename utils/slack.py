import hashlib
import hmac
import os
import time


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
