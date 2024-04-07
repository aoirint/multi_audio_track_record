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
from .views import AddAudioInputDeviceDialog, AddSceneDialog, Home

logger = getLogger(__name__)


async def create_default_scene(
    audio_input_device_manager: AudioInputDeviceManager,
) -> Scene:
    _default_audio_input_device = (
        await audio_input_device_manager.get_default_audio_input_device()
    )
    _desktop_dir = platformdirs.user_desktop_path()

    _default_scene = Scene(
        name="デフォルト",
        output_dir=str(_desktop_dir.resolve()),
        tracks=[
            SceneTrack(name="デフォルト"),
        ],
        devices=(
            [
                SceneDevice(
                    portaudio_name=_default_audio_input_device.portaudio_name,
                    portaudio_index=_default_audio_input_device.portaudio_index,
                    portaudio_host_api_type=_default_audio_input_device.portaudio_host_api_type,
                    portaudio_host_api_index=_default_audio_input_device.portaudio_host_api_index,
                    portaudio_host_api_device_index=_default_audio_input_device.portaudio_host_api_device_index,
                    sampling_rate=int(
                        _default_audio_input_device.default_sampling_rate
                    ),
                    channels=_default_audio_input_device.max_channels,
                    gain=0,
                    is_muted=False,
                    tracks=[0],
                ),
            ]
            if _default_audio_input_device is not None
            else []
        ),
    )

    return _default_scene


async def flet_app_main(page: ft.Page) -> None:
    page.title = f"Multi Audio Track Recorder v{APP_VERSION}"
    page.window_width = 800
    page.window_height = 600

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
    else:
        # 初回起動
        default_scene = await create_default_scene(
            audio_input_device_manager=audio_input_device_manager,
        )
        _scenes.append(default_scene)

    app_state = AppState(
        scenes=_scenes,
        selected_scene_index=0 if len(_scenes) > 0 else None,
        is_recording=False,
        recording_started_at=None,
        is_paused=False,
        is_muted=False,
    )

    async def on_route_change(event: ft.RouteChangeEvent) -> None:
        if page.route == "/":
            page.views.clear()
            page.views.append(
                Home(
                    route="/",
                    app_state=app_state,
                    audio_input_device_manager=audio_input_device_manager,
                    config_store_manager=config_store_manager,
                ),
            )
            logger.info(
                f"on_route_change: route={page.route}, view_count={len(page.views)}"
            )

        elif page.route == "/add_scene":
            page.views.append(
                AddSceneDialog(
                    route="/add_scene",
                    app_state=app_state,
                    audio_input_device_manager=audio_input_device_manager,
                    config_store_manager=config_store_manager,
                ),
            )
            logger.info(
                f"on_route_change: route={page.route}, view_count={len(page.views)}"
            )

        elif page.route == "/add_audio_input_device":
            page.views.append(
                AddAudioInputDeviceDialog(
                    route="/add_audio_input_device",
                    app_state=app_state,
                    audio_input_device_manager=audio_input_device_manager,
                    config_store_manager=config_store_manager,
                ),
            )
            logger.info(
                f"on_route_change: route={page.route}, view_count={len(page.views)}"
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
