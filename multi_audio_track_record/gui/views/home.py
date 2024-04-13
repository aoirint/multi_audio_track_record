import asyncio
import traceback
from logging import getLogger

import flet as ft

from ...audio_input_device_manager import AudioInputDeviceManager
from ...config_store_manager import Config, ConfigStoreManager
from ..app_state import AppState
from ..controls.audio_input_device_list_panel import AudioInputDeviceListPanel
from ..controls.record_control_panel import RecordControlPanel
from ..controls.scene_selection_panel import SceneSelectionPanel
from ..controls.track_list_panel import TrackListPanel

logger = getLogger(__name__)


class Home(ft.View):  # type:ignore[misc]
    main_task_future: asyncio.Future | None

    scene_panel: SceneSelectionPanel | None
    audio_input_device_list_panel: AudioInputDeviceListPanel | None
    track_list_panel: TrackListPanel | None
    record_control_panel: RecordControlPanel | None

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

        self.scene_panel = None
        self.audio_input_device_list_panel = None
        self.track_list_panel = None
        self.record_control_panel = None

        self.app_state = app_state
        self.audio_input_device_manager = audio_input_device_manager
        self.config_store_manager = config_store_manager

    def build(self) -> None:
        app_state = self.app_state
        audio_input_device_manager = self.audio_input_device_manager
        config_store_manager = self.config_store_manager

        async def on_scene_index_selected(selected_scene_index: int) -> None:
            await self.load_scene(index=selected_scene_index)

        scene_panel = SceneSelectionPanel(
            app_state=app_state,
            audio_input_device_manager=audio_input_device_manager,
            config_store_manager=config_store_manager,
            on_scene_index_selected=on_scene_index_selected,
        )
        self.scene_panel = scene_panel

        audio_input_device_list_panel = AudioInputDeviceListPanel(
            app_state=app_state,
            audio_input_device_manager=audio_input_device_manager,
            config_store_manager=config_store_manager,
            expand=True,
        )
        self.audio_input_device_list_panel = audio_input_device_list_panel

        track_list_panel = TrackListPanel(
            app_state=app_state,
            audio_input_device_manager=audio_input_device_manager,
            config_store_manager=config_store_manager,
            expand=True,
        )
        self.track_list_panel = track_list_panel

        record_control_panel = RecordControlPanel(
            app_state=app_state,
            audio_input_device_manager=audio_input_device_manager,
            config_store_manager=config_store_manager,
            alignment=ft.MainAxisAlignment.CENTER,
        )
        self.record_control_panel = record_control_panel

        self.controls = [
            ft.Column(
                controls=[
                    scene_panel,
                    ft.Row(
                        controls=[
                            audio_input_device_list_panel,
                            track_list_panel,
                        ],
                        expand=True,
                    ),
                ],
                spacing=24,
                expand=True,
            ),
            record_control_panel,
        ]

    def did_mount(self) -> None:
        page = self.page

        main_task_future = page.run_task(self.main_task)
        self.main_task_future = main_task_future

    def will_unmount(self) -> None:
        main_task_future = self.main_task_future
        if main_task_future is not None:
            main_task_future.cancel()

    async def load_scene(self, index: int) -> None:
        app_state = self.app_state
        page = self.page

        audio_input_device_list_panel = self.audio_input_device_list_panel
        assert audio_input_device_list_panel is not None

        track_list_panel = self.track_list_panel
        assert track_list_panel is not None

        record_control_panel = self.record_control_panel
        assert record_control_panel is not None

        scene = app_state.scenes[index]

        await audio_input_device_list_panel.on_scene_loaded(
            scene=scene,
        )

        await track_list_panel.on_scene_loaded(
            scene=scene,
        )

        await record_control_panel.on_scene_loaded(
            scene=scene,
        )

        app_state.is_recording = False
        app_state.is_paused = False

        app_state.selected_scene_index = index
        page.update()

    async def save_config(self) -> None:
        config_store_manager = self.config_store_manager
        app_state = self.app_state

        await config_store_manager.save_config(
            config=Config(
                struct_version=1,
                scenes=app_state.scenes,
                selected_scene_index=app_state.selected_scene_index,
            ),
        )

    async def main_task(self) -> None:
        try:
            app_state = self.app_state

            selected_scene_index = app_state.selected_scene_index
            assert selected_scene_index is not None

            await self.load_scene(index=selected_scene_index)
        except Exception:
            logger.error(traceback.format_exc())
            raise
