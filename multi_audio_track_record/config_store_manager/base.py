from abc import ABC, abstractmethod

from pydantic import BaseModel

from ..scene import Scene


class Config(BaseModel):
    struct_version: int
    scenes: list[Scene]
    selected_scene_index: int | None


class ConfigStoreManager(ABC):
    @abstractmethod
    async def load_config(self) -> Config: ...

    @abstractmethod
    async def save_config(self, config: Config) -> None: ...
