import json
from pathlib import Path
from typing import Annotated

from pydantic import BaseModel, Field


class SceneTrack(BaseModel):
    name: str


class SceneDevice(BaseModel):
    portaudio_name: str
    portaudio_host_api_type: int
    portaudio_host_api_index: int
    portaudio_host_api_device_index: int
    channels: int
    gain: float
    muted: bool
    tracks: list[int]


class Scene(BaseModel):
    struct_version: int
    name: str
    tracks: list[SceneTrack]
    devices: list[SceneDevice]


def load_scene_file(path: Path) -> Scene:
    with path.open(mode="r", encoding="utf-8") as fp:
        serialized_scene_dict = json.load(fp)

    return Scene.model_validate(serialized_scene_dict)


def save_scene_file(scene: Scene, path: Path) -> None:
    with path.open(mode="w", encoding="utf-8") as fp:
        serialized_scene_dict = scene.model_dump()
        json.dump(serialized_scene_dict, fp)
