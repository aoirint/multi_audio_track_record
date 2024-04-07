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
    struct_version: Annotated[int, Field(alias="structVersion")]
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
    struct_version: Annotated[int, Field(alias="structVersion")]
    name: str
    host_api: Annotated[int, Field(alias="hostApi")]
    max_input_channels: Annotated[int, Field(alias="maxInputChannels")]
    max_output_channels: Annotated[int, Field(alias="maxOutputChannels")]
    default_low_input_latency: Annotated[float, Field(alias="defaultLowInputLatency")]
    default_low_output_latency: Annotated[float, Field(alias="defaultLowOutputLatency")]
    default_high_input_latency: Annotated[float, Field(alias="defaultHighInputLatency")]
    default_high_output_latency: Annotated[
        float, Field(alias="defaultHighOutputLatency")
    ]
    default_sample_rate: Annotated[float, Field(alias="defaultSampleRate")]


class AudioInputDeviceManagerPyAudio(AudioInputDeviceManager):
    def __init__(self) -> None:
        self.__pyaudio_instance = pyaudio.PyAudio()

    async def __get_default_host_api_info(self) -> _PyAudioHostApiInfo:
        __pyaudio_instance = self.__pyaudio_instance

        default_host_api_info_dict = __pyaudio_instance.get_default_host_api_info()
        default_host_api_info = _PyAudioHostApiInfo.model_validate(
            default_host_api_info_dict
        )

        return default_host_api_info

    async def __get_audio_input_devices_with_host_api_info(
        self,
        host_api_info: _PyAudioHostApiInfo,
    ) -> list[AudioInputDevice]:
        __pyaudio_instance = self.__pyaudio_instance

        device_count = host_api_info.device_count

        audio_input_devices: list[AudioInputDevice] = []
        for host_api_device_index in range(device_count):
            device_info_dict = (
                __pyaudio_instance.get_device_info_by_host_api_device_index(
                    host_api_index=host_api_info.index,
                    host_api_device_index=host_api_device_index,
                )
            )
            device_info = _PyAudioDeviceInfo.model_validate(device_info_dict)

            if device_info.max_input_channels == 0:
                continue

            audio_input_devices.append(
                AudioInputDevice(
                    portaudio_name=device_info.name,
                    portaudio_index=device_info.index,
                    portaudio_host_api_type=host_api_info.type,
                    portaudio_host_api_index=host_api_info.index,
                    portaudio_host_api_device_index=host_api_device_index,
                    default_sampling_rate=device_info.default_sample_rate,
                    max_channels=device_info.max_input_channels,
                )
            )

        return audio_input_devices

    async def get_audio_input_devices(self) -> list[AudioInputDevice]:
        default_host_api_info = await self.__get_default_host_api_info()
        audio_input_devices = await self.__get_audio_input_devices_with_host_api_info(
            host_api_info=default_host_api_info,
        )

        return audio_input_devices

    async def get_default_audio_input_device(self) -> AudioInputDevice:
        __pyaudio_instance = self.__pyaudio_instance

        default_host_api_info_dict = __pyaudio_instance.get_default_host_api_info()
        default_host_api_info = _PyAudioHostApiInfo.model_validate(
            default_host_api_info_dict
        )
        default_input_device_index = default_host_api_info.default_input_device

        audio_input_devices = await self.__get_audio_input_devices_with_host_api_info(
            host_api_info=default_host_api_info,
        )

        for audio_input_device in audio_input_devices:
            if audio_input_device.portaudio_index == default_input_device_index:
                return audio_input_device

        raise Exception("Unexpected state. Default input device not found.")
