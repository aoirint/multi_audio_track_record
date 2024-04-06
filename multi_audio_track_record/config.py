import json
import shutil
import tempfile
from pathlib import Path

from pydantic import BaseModel

from .scene import Scene


class Config(BaseModel):
    struct_version: int
    scenes: list[Scene]
    selected_scene_index: int | None


def load_config_file(path: Path) -> Config:
    with path.open(mode="r", encoding="utf-8") as fp:
        config_dict = json.load(fp)

    return Config.model_validate(config_dict)


def save_config_file(config: Config, path: Path) -> None:
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8") as fp:
        config_dict = config.model_dump()
        json.dump(config_dict, fp)

        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(fp.name, path)
