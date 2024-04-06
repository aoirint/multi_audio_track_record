import asyncio
from logging import getLogger

import flet as ft

from ...audio_input_device_manager import AudioInputDevice, AudioInputDeviceManager
from ...config_store_manager import ConfigStoreManager
from ...scene import SceneDevice
from ..app_state import AppState

logger = getLogger(__name__)


class AddAudioInputDeviceDialog(ft.View):  # type:ignore[misc]
    main_task_future: asyncio.Future | None

    audio_input_device_dropdown: ft.Dropdown | None
    audio_input_devices: list[AudioInputDevice]

    def __init__(
        self,
        route: str,
        app_state: AppState,
        audio_input_device_manager: AudioInputDeviceManager,
        config_store_manager: ConfigStoreManager,
    ):
        super().__init__(
            route=route,
        )

        self.main_task_future = None
        self.app_state = app_state
        self.audio_input_device_manager = audio_input_device_manager
        self.config_store_manager = config_store_manager

    def build(self) -> None:
        audio_input_device_dropdown = ft.Dropdown()
        self.audio_input_device_dropdown = audio_input_device_dropdown

        add_audio_input_device_button = ft.ElevatedButton(
            text="追加",
            on_click=self.on_add_audio_input_device_button_clicked,
        )

        self.controls = [
            ft.AppBar(
                title=ft.Text("音声入力デバイスを追加"),
                bgcolor=ft.colors.SURFACE_VARIANT,
            ),
            ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text("音声入力デバイス"),
                        audio_input_device_dropdown,
                        ft.Container(
                            expand=True,
                        ),
                        ft.Row(
                            controls=[
                                add_audio_input_device_button,
                            ],
                            alignment=ft.MainAxisAlignment.END,
                        ),
                    ],
                ),
                padding=8,
                expand=True,
            ),
        ]

    def did_mount(self) -> None:
        page = self.page

        main_task_future = page.run_task(self.main_task)
        self.main_task_future = main_task_future

    def will_unmount(self) -> None:
        main_task_future = self.main_task_future
        if main_task_future is not None:
            main_task_future.cancel()

    async def main_task(self) -> None:
        page = self.page

        audio_input_device_manager = self.audio_input_device_manager
        audio_input_device_dropdown = self.audio_input_device_dropdown
        assert audio_input_device_dropdown is not None

        audio_input_devices = await audio_input_device_manager.get_audio_input_devices()
        self.audio_input_devices = audio_input_devices

        audio_input_device_dropdown.value = None

        options: list[ft.dropdown.Option] = []
        for audio_input_device_index, audio_input_device in enumerate(
            audio_input_devices
        ):
            options.append(
                ft.dropdown.Option(
                    key=f"{audio_input_device_index}",
                    text=audio_input_device.portaudio_name,
                ),
            )
        audio_input_device_dropdown.options = options
        audio_input_device_dropdown.value = options[0].key if len(options) > 0 else None

        page.update()

    async def on_add_audio_input_device_button_clicked(
        self,
        event: ft.ControlEvent,
    ) -> None:
        page = self.page
        app_state = self.app_state

        audio_input_device_dropdown = self.audio_input_device_dropdown
        assert audio_input_device_dropdown is not None

        audio_input_devices = self.audio_input_devices

        selected_audio_input_device_index_string = audio_input_device_dropdown.value
        assert selected_audio_input_device_index_string is not None
        selected_audio_input_device_index = int(
            selected_audio_input_device_index_string
        )

        audio_input_device = audio_input_devices[selected_audio_input_device_index]
        logger.info(f"selected {audio_input_device}")

        assert app_state.selected_scene_index is not None
        scene = app_state.scenes[app_state.selected_scene_index]
        scene.devices.append(
            SceneDevice(
                portaudio_name=audio_input_device.portaudio_name,
                portaudio_index=audio_input_device.portaudio_index,
                portaudio_host_api_type=audio_input_device.portaudio_host_api_type,
                portaudio_host_api_index=audio_input_device.portaudio_host_api_index,
                portaudio_host_api_device_index=audio_input_device.portaudio_host_api_device_index,
                channels=audio_input_device.max_channels,
                gain=0,
                muted=False,
                tracks=[0],
            ),
        )

        page.views.pop()
        page.go("/")
