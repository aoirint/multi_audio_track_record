import asyncio
from logging import getLogger

import flet as ft
import platformdirs

from ...audio_input_device_manager import AudioInputDevice, AudioInputDeviceManager
from ...config_store_manager import ConfigStoreManager
from ...scene import Scene, SceneDevice, SceneTrack
from ..app_state import AppState

logger = getLogger(__name__)


class AddSceneDialog(ft.View):  # type:ignore[misc]
    main_task_future: asyncio.Future | None

    scene_name_text_field: ft.TextField | None

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
        self.scene_name_text_field = None
        self.app_state = app_state
        self.audio_input_device_manager = audio_input_device_manager
        self.config_store_manager = config_store_manager

    def build(self) -> None:
        scene_name_text_field = ft.TextField(label="シーンの名前")
        self.scene_name_text_field = scene_name_text_field

        add_scene_button = ft.ElevatedButton(
            text="追加",
            on_click=self.on_scene_button_clicked,
        )

        self.controls = [
            ft.AppBar(
                title=ft.Text("シーンを追加"),
                bgcolor=ft.colors.SURFACE_VARIANT,
            ),
            ft.Container(
                content=ft.Column(
                    controls=[
                        scene_name_text_field,
                        ft.Container(
                            expand=True,
                        ),
                        ft.Row(
                            controls=[
                                add_scene_button,
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
        pass

    async def on_scene_button_clicked(
        self,
        event: ft.ControlEvent,
    ) -> None:
        page = self.page
        app_state = self.app_state
        audio_input_device_manager = self.audio_input_device_manager

        scene_name_text_field = self.scene_name_text_field
        assert scene_name_text_field is not None

        scene_name = scene_name_text_field.value
        if scene_name is None or len(scene_name) == 0:
            page.snack_bar = ft.SnackBar(
                content=ft.Text("シーンの名前を設定してください")
            )
            page.snack_bar.open = True
            page.update()
            return

        logger.info(f"creating new scene: {scene_name}")

        default_audio_input_device = (
            await audio_input_device_manager.get_default_audio_input_device()
        )

        scene = Scene(
            name=scene_name,
            output_dir=platformdirs.user_desktop_dir(),
            tracks=[
                SceneTrack(
                    name="デフォルト",
                ),
            ],
            devices=(
                [
                    SceneDevice(
                        portaudio_name=default_audio_input_device.portaudio_name,
                        portaudio_index=default_audio_input_device.portaudio_index,
                        portaudio_host_api_type=default_audio_input_device.portaudio_host_api_type,
                        portaudio_host_api_index=default_audio_input_device.portaudio_host_api_index,
                        portaudio_host_api_device_index=default_audio_input_device.portaudio_host_api_device_index,
                        sampling_rate=int(
                            default_audio_input_device.default_sampling_rate
                        ),
                        channels=default_audio_input_device.max_channels,
                        gain=0,
                        is_muted=False,
                        tracks=[0],
                    ),
                ]
                if default_audio_input_device is not None
                else []
            ),
        )

        app_state.scenes.append(scene)
        app_state.selected_scene_index = len(app_state.scenes) - 1

        # TODO: save config

        logger.info(f"created new scene: {scene_name}")

        page.views.pop()
        page.go("/")
