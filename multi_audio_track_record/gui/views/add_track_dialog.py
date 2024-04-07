import asyncio
from logging import getLogger

import flet as ft

from ...audio_input_device_manager import AudioInputDeviceManager
from ...config_store_manager import ConfigStoreManager
from ...scene import SceneTrack
from ..app_state import AppState

logger = getLogger(__name__)


class AddTrackDialog(ft.View):  # type:ignore[misc]
    main_task_future: asyncio.Future | None

    track_name_text_field: ft.TextField | None

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
        self.track_name_text_field = None
        self.app_state = app_state
        self.audio_input_device_manager = audio_input_device_manager
        self.config_store_manager = config_store_manager

    def build(self) -> None:
        track_name_text_field = ft.TextField(label="トラックの名前")
        self.track_name_text_field = track_name_text_field

        add_track_button = ft.ElevatedButton(
            text="追加",
            on_click=self.on_track_button_clicked,
        )

        self.controls = [
            ft.AppBar(
                title=ft.Text("トラックを追加"),
                bgcolor=ft.colors.SURFACE_VARIANT,
            ),
            ft.Container(
                content=ft.Column(
                    controls=[
                        track_name_text_field,
                        ft.Container(
                            expand=True,
                        ),
                        ft.Row(
                            controls=[
                                add_track_button,
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

    async def on_track_button_clicked(
        self,
        event: ft.ControlEvent,
    ) -> None:
        page = self.page
        app_state = self.app_state

        track_name_text_field = self.track_name_text_field
        assert track_name_text_field is not None

        track_name = track_name_text_field.value
        if track_name is None or len(track_name) == 0:
            page.snack_bar = ft.SnackBar(
                content=ft.Text("トラックの名前を設定してください")
            )
            page.snack_bar.open = True
            page.update()
            return

        logger.info(f"creating new track: {track_name}")

        selected_scene_index = app_state.selected_scene_index
        assert selected_scene_index is not None
        scene = app_state.scenes[selected_scene_index]

        scene_track = SceneTrack(name=track_name)
        scene.tracks.append(scene_track)

        track_index = len(scene.tracks) - 1
        for device in scene.devices:
            device.tracks.append(track_index)

        # TODO: save config

        logger.info(f"created new track: {track_name}")

        page.views.pop()
        page.go("/")
