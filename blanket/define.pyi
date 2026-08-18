from typing import TypedDict

Sound = TypedDict("Sound", {"name": str, "title": str})

SoundCategory = TypedDict("SoundCategory", {"name": str, "sounds": list[Sound]})

VERSION: str
APP_ID: str
RES_PATH: str

SOUNDS: list[SoundCategory]
NOISES: list[Sound]

AUTHORS: list[str]
ARTISTS: dict[str, list[str]]
SOUND_ARTISTS: dict[str, list[str]]
SOUND_EDITORS: dict[str, list[str]]
