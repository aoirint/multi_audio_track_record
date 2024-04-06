from dataclasses import dataclass

from ..scene import Scene


@dataclass
class AppState:
    scenes: list[Scene]
    selected_scene_index: int | None
    is_recording: bool
    is_paused: bool
    is_muted: bool
