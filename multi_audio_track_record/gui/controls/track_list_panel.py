from dataclasses import dataclass
from logging import getLogger

import flet as ft

from ...audio_input_device_manager import AudioInputDeviceManager
from ...config_store_manager import ConfigStoreManager
from ...scene import Scene
from ..app_state import AppState

logger = getLogger(__name__)


@dataclass
class TrackControls:
    edit_button: ft.IconButton
    volume_progress_bar: ft.ProgressBar


class TrackListPanel(ft.Column):  # type:ignore[misc]
    track_list_view: ft.ListView | None
    track_controls_dict: dict[int, TrackControls]

    def __init__(
        self,
        app_state: AppState,
        audio_input_device_manager: AudioInputDeviceManager,
        config_store_manager: ConfigStoreManager,
        expand: bool | int | None = None,
    ):
        super().__init__(expand=expand)

        self.track_list_view = None
        self.track_controls_dict = {}

        self.app_state = app_state
        self.audio_input_device_manager = audio_input_device_manager
        self.config_store_manager = config_store_manager

    def build(self) -> None:
        add_track_button = ft.IconButton(
            icon=ft.icons.ADD,
            icon_size=24,
            on_click=self.on_add_track_button_clicked,
        )

        track_list_view = ft.ListView(
            expand=1,
            spacing=10,
        )
        self.track_list_view = track_list_view

        self.controls = [
            ft.Row(
                controls=[
                    ft.Text(value="トラック"),
                    add_track_button,
                ],
            ),
            track_list_view,
        ]

    async def on_add_track_button_clicked(
        self,
        event: ft.ControlEvent,
    ) -> None:
        page = self.page

        page.go("/add_track")

    async def on_scene_loaded(
        self,
        scene: Scene,
    ) -> None:
        track_list_view = self.track_list_view
        assert track_list_view is not None

        track_controls_dict = self.track_controls_dict
        assert track_controls_dict is not None

        track_list_view.controls.clear()
        track_controls_dict.clear()

        for track_index, track in enumerate(scene.tracks):
            track_edit_button = ft.IconButton(icon=ft.icons.EDIT, icon_size=20)
            track_volume_progress_bar = ft.ProgressBar(value=0, bar_height=4)

            track_list_view.controls.append(
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Icon(
                                        name=ft.icons.MULTITRACK_AUDIO,
                                        size=16,
                                        color=ft.colors.ON_SURFACE,
                                    ),
                                    ft.Column(
                                        controls=[
                                            ft.Text(
                                                value=f"{track.name}",
                                                overflow=ft.TextOverflow.FADE,
                                                no_wrap=True,
                                                expand=True,
                                            ),
                                            track_volume_progress_bar,
                                        ],
                                        expand=True,
                                    ),
                                ],
                                spacing=20,
                                expand=True,
                            ),
                            ft.Row(
                                controls=[
                                    track_edit_button,
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

            track_controls_dict[track_index] = TrackControls(
                edit_button=track_edit_button,
                volume_progress_bar=track_volume_progress_bar,
            )
