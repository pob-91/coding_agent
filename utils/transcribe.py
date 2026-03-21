import base64
import os
from typing import Literal

from openai import OpenAI


def transcribe_audio(audio_bytes: bytes, mime: str) -> str | None:
    format = _mime_to_format(mime)
    if format is None:
        return None

    # encode to base64
    encoded = base64.b64encode(audio_bytes).decode("utf-8")

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("OPEN_ROUTER_API_KEY"),
    )

    completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Please transcribe this audio file.",
                    },
                    {
                        "type": "input_audio",
                        "input_audio": {
                            "data": encoded,
                            "format": format,
                        },
                    },
                ],
            }
        ],
        model=os.getenv("AUDIO_MODEL", ""),
    )

    return completion.choices[0].message.content


def _mime_to_format(mime: str) -> Literal["wav", "mp3"] | None:
    if mime == "audio/mpeg" or mime == "audio/mp3":
        return "mp3"

    if mime == "audio/wav":
        return "wav"

    return None
