from dataclasses import dataclass
from logging import getLogger

import flet as ft

from ...audio_input_device_manager import AudioInputDeviceManager
from ...config_store_manager import ConfigStoreManager
from ...scene import Scene
from ..app_state import AppState

logger = getLogger(__name__)


@dataclass
class AudioInputDeviceControls:
    mute_button: ft.IconButton
    edit_button: ft.IconButton
    volume_progress_bar: ft.ProgressBar


class AudioInputDeviceListPanel(ft.Column):  # type:ignore[misc]
    audio_input_device_list_view: ft.ListView | None
    audio_input_device_controls_dict: dict[int, AudioInputDeviceControls]

    def __init__(
        self,
        app_state: AppState,
        audio_input_device_manager: AudioInputDeviceManager,
        config_store_manager: ConfigStoreManager,
        expand: bool | int | None = None,
    ):
        super().__init__(expand=expand)

        self.audio_input_device_list_view = None
        self.audio_input_device_controls_dict = {}

        self.app_state = app_state
        self.audio_input_device_manager = audio_input_device_manager
        self.config_store_manager = config_store_manager

    def build(self) -> None:
        add_audio_input_device_button = ft.IconButton(
            icon=ft.icons.ADD,
            icon_size=24,
            on_click=self.on_add_audio_input_device_button_clicked,
        )

        # TODO: show volume level of each input devices
        # TODO: mapping configuration of input devices and tracks
        # TODO: switch muted status of each input devices
        audio_input_device_list_view = ft.ListView(
            expand=1,
            spacing=10,
        )
        self.audio_input_device_list_view = audio_input_device_list_view

        self.controls = [
            ft.Row(
                controls=[
                    ft.Text(value="音声入力デバイス"),
                    add_audio_input_device_button,
                ],
            ),
            audio_input_device_list_view,
        ]

    async def on_add_audio_input_device_button_clicked(
        self,
        event: ft.ControlEvent,
    ) -> None:
        page = self.page

        page.go("/add_audio_input_device")

    async def on_scene_loaded(
        self,
        scene: Scene,
    ) -> None:
        audio_input_device_list_view = self.audio_input_device_list_view
        assert audio_input_device_list_view is not None

        audio_input_device_controls_dict = self.audio_input_device_controls_dict
        assert audio_input_device_controls_dict is not None

        audio_input_device_list_view.controls.clear()
        audio_input_device_controls_dict.clear()

        for device_index, device in enumerate(scene.devices):
            device_mute_button = ft.IconButton(icon=ft.icons.MIC, icon_size=20)
            device_edit_button = ft.IconButton(icon=ft.icons.EDIT, icon_size=20)
            device_volume_progress_bar = ft.ProgressBar(value=0, bar_height=4)

            audio_input_device_list_view.controls.append(
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Icon(
                                        name=ft.icons.MIC,
                                        size=16,
                                        color=ft.colors.ON_SURFACE,
                                    ),
                                    ft.Column(
                                        controls=[
                                            ft.Text(
                                                value=f"{device.portaudio_name}",
                                                overflow=ft.TextOverflow.FADE,
                                                no_wrap=True,
                                                expand=True,
                                            ),
                                            device_volume_progress_bar,
                                        ],
                                        expand=True,
                                    ),
                                ],
                                spacing=20,
                                expand=True,
                            ),
                            ft.Row(
                                controls=[
                                    device_mute_button,
                                    device_edit_button,
                                ],
                            ),
                        ],
                    ),
                    bgcolor=ft.colors.ON_SECONDARY,
                    alignment=ft.alignment.center,
                    padding=16,
                    height=70,
                ),
            )

            audio_input_device_controls_dict[device_index] = AudioInputDeviceControls(
                mute_button=device_mute_button,
                edit_button=device_edit_button,
                volume_progress_bar=device_volume_progress_bar,
            )
