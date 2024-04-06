from logging import getLogger
from typing import Annotated

import pyaudio
from pydantic import BaseModel, Field

from .base import AudioInputDevice, AudioInputDeviceManager

logger = getLogger(__name__)


class _PyAudioHostApiInfo(BaseModel):
    """
    PortAudioにおけるHostAPIとは、
    WindowsではMMEやDirectSoundなど、
    LinuxではALSA/PulseAudioやJACKなど、
    macOSではCoreAudioなどのサウンドシステムを表す単位のこと。
    PortAudioがサポートするサウンドシステムの種類は、 PaHostApiTypeId 列挙型に記載されている。
    """

    index: int
    structVersion: int
    type: int
    """
    PaHostApiTypeId の値

    https://www.portaudio.com/docs/v19-doxydocs/portaudio_8h_source.html#l00275

    DirectSound: 1
    MME: 2
    CoreAudio: 5
    ALSA/PulseAudio: 8
    JACK: 12
    """
    name: str
    device_count: Annotated[int, Field(alias="deviceCount")]
    default_input_device: Annotated[int, Field(alias="defaultInputDevice")]
    default_output_device: Annotated[int, Field(alias="defaultOutputDevice")]


class _PyAudioDeviceInfo(BaseModel):
    index: int
    name: str
    max_input_channels: Annotated[int, Field(alias="maxInputChannels")]
    max_output_channels: Annotated[int, Field(alias="maxOutputChannels")]


class AudioInputDeviceManagerPyAudio(AudioInputDeviceManager):
    def __init__(self) -> None:
        self.__pyaudio_instance = pyaudio.PyAudio()

    async def get_audio_input_devices(self) -> list[AudioInputDevice]:
        __pyaudio_instance = self.__pyaudio_instance

        default_host_api_info_dict = __pyaudio_instance.get_default_host_api_info()
        default_host_api_info = _PyAudioHostApiInfo.model_validate(
            default_host_api_info_dict
        )
        device_count = default_host_api_info.device_count

        audio_input_devices: list[AudioInputDevice] = []
        for host_api_device_index in range(device_count):
            device_info_dict = (
                __pyaudio_instance.get_device_info_by_host_api_device_index(
                    host_api_index=default_host_api_info.index,
                    host_api_device_index=host_api_device_index,
                )
            )
            device_info = _PyAudioDeviceInfo.model_validate(device_info_dict)

            if device_info.max_input_channels == 0:
                continue

            audio_input_devices.append(
                AudioInputDevice(
                    portaudio_name=device_info.name,
                    portaudio_host_api_type=default_host_api_info.type,
                    portaudio_host_api_index=default_host_api_info.index,
                    portaudio_host_api_device_index=host_api_device_index,
                    max_channels=device_info.max_input_channels,
                )
            )

        return audio_input_devices
