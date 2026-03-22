import base64
import os
import subprocess

from openai import OpenAI

from data.open_router import OpenRouterHandler
from model.file import AudioFile


def transcribe_audio(
    file: AudioFile,
    configured_model: str | None = None,
) -> str | None:
    type = "wav"

    # The model only supports wav and mp3
    if file.type == "mp4":
        bytes = _mp4_bytes_to_mp3_bytes(file.data)
        encoded = base64.b64encode(bytes).decode("utf-8")
        type = "mp3"
    else:
        encoded = base64.b64encode(file.data).decode("utf-8")

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
                            "format": type,
                        },
                    },
                ],
            }
        ],
        model=OpenRouterHandler.get_audio_model(configured_model=configured_model),
    )

    return completion.choices[0].message.content


def _mp4_bytes_to_mp3_bytes(mp4_bytes: bytes) -> bytes:
    process = subprocess.Popen(
        [
            "ffmpeg",
            "-i",
            "pipe:0",  # input from stdin
            "-vn",  # no video
            "-acodec",
            "libmp3lame",
            "-ab",
            "192k",
            "-f",
            "mp3",
            "pipe:1",  # output to stdout
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )

    mp3_bytes, _ = process.communicate(mp4_bytes)
    return mp3_bytes
