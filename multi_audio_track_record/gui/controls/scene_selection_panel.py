from logging import getLogger
from typing import Awaitable, Callable

import flet as ft

from ...audio_input_device_manager import AudioInputDeviceManager
from ...config_store_manager import ConfigStoreManager
from ..app_state import AppState

logger = getLogger(__name__)


class SceneSelectionPanel(ft.Container):  # type:ignore[misc]
    add_scene_button: ft.IconButton | None
    scene_dropdown: ft.Dropdown | None

    def __init__(
        self,
        app_state: AppState,
        audio_input_device_manager: AudioInputDeviceManager,
        config_store_manager: ConfigStoreManager,
        on_scene_index_selected: Callable[[int], Awaitable[None]],
    ):
        super().__init__()

        self.add_scene_button = None
        self.scene_dropdown = None

        self.app_state = app_state
        self.audio_input_device_manager = audio_input_device_manager
        self.config_store_manager = config_store_manager

        self.on_scene_index_selected_callback = on_scene_index_selected

    def build(self) -> None:
        app_state = self.app_state

        add_scene_button = ft.IconButton(
            icon=ft.icons.ADD,
            icon_size=24,
            on_click=self.on_add_scene_button_clicked,
        )

        scene_options: list[ft.dropdown.Option] = []
        for scene_index, scene in enumerate(app_state.scenes):
            scene_options.append(
                ft.dropdown.Option(
                    key=str(scene_index),
                    text=scene.name,
                ),
            )

        selected_scene_index = app_state.selected_scene_index
        scene_dropdown = ft.Dropdown(
            value=(
                str(selected_scene_index) if selected_scene_index is not None else None
            ),
            options=scene_options,
            on_change=self.on_scene_dropdown_change,
        )

        self.add_scene_button = add_scene_button
        self.scene_dropdown = scene_dropdown

        self.content = ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Text(value="シーン"),
                        add_scene_button,
                    ],
                ),
                scene_dropdown,
            ],
        )

    async def on_add_scene_button_clicked(
        self,
        event: ft.ControlEvent,
    ) -> None:
        page = self.page

        page.go("/add_scene")

    async def on_scene_dropdown_change(
        self,
        event: ft.ControlEvent,
    ) -> None:
        scene_dropdown = self.scene_dropdown
        assert scene_dropdown is not None

        selected_index_string = scene_dropdown.value
        assert selected_index_string is not None

        on_scene_index_selected_callback = self.on_scene_index_selected_callback

        # TODO: 録音中のシーン切り替えを禁止する

        selected_index = int(selected_index_string)
        await on_scene_index_selected_callback(selected_index)
