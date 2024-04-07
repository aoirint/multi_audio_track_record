from pydantic import BaseModel


class SceneTrack(BaseModel):
    name: str


class SceneDevice(BaseModel):
    portaudio_name: str
    portaudio_index: int
    portaudio_host_api_type: int
    portaudio_host_api_index: int
    portaudio_host_api_device_index: int
    sampling_rate: int
    channels: int
    gain: float
    muted: bool
    tracks: list[int]


class Scene(BaseModel):
    name: str
    output_dir: str
    tracks: list[SceneTrack]
    devices: list[SceneDevice]
