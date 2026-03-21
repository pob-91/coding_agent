import hashlib
import hmac
import os
import time
from typing import Any

import requests

from model.file import FILE_TYPE, AudioFile, BaseFile
from utils.logger import get_logger

logger = get_logger(__name__)


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


def download_slack_file(file: Any, token: str) -> BaseFile | None:
    # NOTE: This can handle other types of files but currently only audio supported
    mimetype = file.get("mimetype", "")
    mime = _mime_to_format(mimetype)

    if mime is None:
        logger.warning(f"File of type: {mimetype} sent. Not supported.")
        return None

    download_url = file.get("url_private_download")
    filename = file.get("name", "unknown")

    response = requests.get(
        download_url,
        headers={"Authorization": f"Bearer {token}"},
    )
    response.raise_for_status()

    if not isinstance(response.content, bytes):
        raise Exception("Download file content not bytes.")

    return AudioFile(
        type=mime,
        data=response.content,
        name=filename,
    )


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


# private


def _mime_to_format(mime: str) -> FILE_TYPE | None:
    if mime == "audio/mpeg" or mime == "audio/mp3":
        return "mp3"
    if mime == "audio/mp4" or mime == "audio/m4a":
        return "mp4"
    if mime == "audio/wav":
        return "wav"

    return None
