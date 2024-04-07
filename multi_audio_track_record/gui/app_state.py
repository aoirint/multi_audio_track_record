from dataclasses import dataclass
from datetime import datetime

from ..scene import Scene


@dataclass
class AppState:
    scenes: list[Scene]
    selected_scene_index: int | None
    is_recording: bool
    recording_started_at: datetime | None
    is_paused: bool
    is_muted: bool
