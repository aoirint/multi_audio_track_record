from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class AudioInputDevice:
    portaudio_name: str
    portaudio_host_api_type: int
    portaudio_host_api_index: int
    portaudio_host_api_device_index: int
    max_channels: int


class AudioInputDeviceManager(ABC):
    @abstractmethod
    async def get_audio_input_devices(self) -> list[AudioInputDevice]: ...
