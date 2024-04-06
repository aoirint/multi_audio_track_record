from logging import getLogger

import flet as ft
import platformdirs

from .. import __version__ as APP_VERSION
from ..audio_input_device_manager import (
    AudioInputDeviceManager,
    AudioInputDeviceManagerPyAudio,
)
from ..config_store_manager import ConfigStoreManager, ConfigStoreManagerFile
from ..scene import Scene, SceneDevice, SceneTrack
from .app_state import AppState
from .views import AddAudioInputDialog, Home

logger = getLogger(__name__)


async def flet_app_main(page: ft.Page) -> None:
    page.title = f"Multi Audio Track Recorder v{APP_VERSION}"
    page.window_width = 600
    page.window_height = 400

    config_dir = platformdirs.user_config_path(
        appauthor="aoirint",
        appname="MultiAudioTrackRecorder",
    )
    config_file_path = config_dir / "config.json"

    config_store_manager: ConfigStoreManager = ConfigStoreManagerFile(
        path=config_file_path,
    )
    audio_input_device_manager: AudioInputDeviceManager = (
        AudioInputDeviceManagerPyAudio()
    )

    _scenes: list[Scene] = []
    if config_file_path.exists():
        config = await config_store_manager.load_config()
        for scene in config.scenes:
            _scenes.append(scene)

    app_state = AppState(
        scenes=_scenes,
        selected_scene_index=None,
        is_recording=False,
        is_paused=False,
        is_muted=False,
    )

    async def load_scene(index: int) -> None:
        app_state.selected_scene_index = index

        raise NotImplementedError()

    async def add_default_scene() -> None:
        _audio_input_devices = (
            await audio_input_device_manager.get_audio_input_devices()
        )
        _desktop_dir = platformdirs.user_desktop_path()

        _default_audio_input_device = (
            _audio_input_devices[0] if len(_audio_input_devices) > 0 else None
        )

        _default_scene = Scene(
            name="untitled",
            output_dir=str(_desktop_dir.resolve()),
            tracks=[
                SceneTrack(name="default"),
            ],
            devices=(
                [
                    SceneDevice(
                        portaudio_name=_default_audio_input_device.portaudio_name,
                        portaudio_host_api_type=_default_audio_input_device.portaudio_host_api_type,
                        portaudio_host_api_index=_default_audio_input_device.portaudio_host_api_index,
                        portaudio_host_api_device_index=_default_audio_input_device.portaudio_host_api_device_index,
                        channels=_default_audio_input_device.max_channels,
                        gain=0,
                        muted=False,
                        tracks=[0],
                    ),
                ]
                if _default_audio_input_device is not None
                else []
            ),
        )

        app_state.scenes.append(_default_scene)
        default_scene_index = len(app_state.scenes) - 1
        await load_scene(index=default_scene_index)

    async def on_route_change(event: ft.RouteChangeEvent) -> None:
        if page.route == "/":
            page.views.append(
                Home(
                    route="/",
                    app_state=app_state,
                    audio_input_device_manager=audio_input_device_manager,
                    config_store_manager=config_store_manager,
                ),
            )

        elif page.route == "/add_audio_input_device":
            page.views.append(
                AddAudioInputDialog(
                    route="/add_audio_input_device",
                    app_state=app_state,
                    audio_input_device_manager=audio_input_device_manager,
                    config_store_manager=config_store_manager,
                ),
            )

        page.update()

    async def on_view_pop(view: ft.View) -> None:
        page.views.pop()

        top_view = page.views[-1]
        page.go(top_view.route)

    page.on_route_change = on_route_change
    page.on_view_pop = on_view_pop
    page.go("/")


async def run_app() -> None:
    await ft.app_async(target=flet_app_main)
