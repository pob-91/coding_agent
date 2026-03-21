from abc import ABC
from dataclasses import dataclass
from typing import Literal

FILE_TYPE = Literal["mp3", "mp4", "wav"]


class BaseFile(ABC):
    pass


@dataclass
class AudioFile(BaseFile):
    type: FILE_TYPE
    data: bytes
    name: str
