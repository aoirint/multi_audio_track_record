import json
import shutil
import tempfile
from pathlib import Path

from .base import Config, ConfigStoreManager


class ConfigStoreManagerFile(ConfigStoreManager):
    def __init__(self, path: Path):
        self.path = path

    async def load_config(self) -> Config:
        path = self.path

        with path.open(mode="r", encoding="utf-8") as fp:
            config_dict = json.load(fp)

        return Config.model_validate(config_dict)

    async def save_config(self, config: Config) -> None:
        path = self.path

        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8") as fp:
            config_dict = config.model_dump()
            json.dump(config_dict, fp)

            path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(fp.name, path)
