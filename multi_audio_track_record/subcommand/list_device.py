from argparse import ArgumentParser, Namespace
from logging import getLogger
from typing import Annotated

import pyaudio
from pydantic import BaseModel, Field

logger = getLogger(__name__)


class PyAudioHostApiInfo(BaseModel):
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


class PyAudioDeviceInfo(BaseModel):
    index: int
    name: str
    max_input_channels: Annotated[int, Field(alias="maxInputChannels")]
    max_output_channels: Annotated[int, Field(alias="maxOutputChannels")]


class SubcommandListDeviceArguments(BaseModel):
    pass


async def subcommand_list_device(args: SubcommandListDeviceArguments) -> None:
    pa = pyaudio.PyAudio()

    default_host_api_info_dict = pa.get_default_host_api_info()
    default_host_api_info = PyAudioHostApiInfo.model_validate(
        default_host_api_info_dict
    )

    print(
        f"Default PortAudio Host API: {default_host_api_info.name} "
        f"(type: {default_host_api_info.type})"
    )

    device_count = default_host_api_info.device_count
    print(
        "index".ljust(6),
        "i".ljust(2),
        "o".ljust(2),
        "name",
    )
    for host_api_device_index in range(device_count):
        device_info_dict = pa.get_device_info_by_host_api_device_index(
            host_api_index=default_host_api_info.index,
            host_api_device_index=host_api_device_index,
        )
        device_info = PyAudioDeviceInfo.model_validate(device_info_dict)
        print(
            f"{host_api_device_index: <6}",
            f"{device_info.max_input_channels: <2}",
            f"{device_info.max_output_channels: <2}",
            f"{device_info.name}",
        )


async def execute_subcommand_list_device(
    args: Namespace,
) -> None:
    await subcommand_list_device(
        args=SubcommandListDeviceArguments(),
    )


async def add_arguments_subcommand_list_device(
    parser: ArgumentParser,
) -> None:
    parser.set_defaults(handler=execute_subcommand_list_device)
