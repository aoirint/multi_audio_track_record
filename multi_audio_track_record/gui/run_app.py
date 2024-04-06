from dataclasses import dataclass
from logging import getLogger

import flet as ft
import platformdirs

from .. import __version__ as APP_VERSION
from ..audio import get_audio_input_devices
from ..config import load_config_file
from ..scene import Scene, SceneDevice, SceneTrack

logger = getLogger(__name__)


@dataclass
class AppState:
    scenes: list[Scene]
    selected_scene_index: int | None
    is_recording: bool
    is_paused: bool
    is_muted: bool


async def flet_app_main(page: ft.Page) -> None:
    page.title = f"Multi Audio Track Recorder v{APP_VERSION}"
    page.window_width = 400
    page.window_height = 400

    config_dir = platformdirs.user_config_path(
        appauthor="aoirint",
        appname="MultiAudioTrackRecorder",
    )
    config_file_path = config_dir / "config.json"

    _scenes: list[Scene] = []
    if config_file_path.exists():
        config = load_config_file(path=config_file_path)
        for scene in config.scenes:
            _scenes.append(scene)

    app_state = AppState(
        scenes=_scenes,
        selected_scene_index=None,
        is_recording=False,
        is_paused=False,
        is_muted=False,
    )

    mute_button = ft.IconButton(
        icon=ft.icons.MIC,
        icon_size=32,
    )

    record_button = ft.IconButton(
        icon=ft.icons.FIBER_MANUAL_RECORD,
        icon_size=64,
    )

    pause_button = ft.IconButton(
        icon=ft.icons.PAUSE,
        icon_size=32,
        disabled=True,
    )

    async def load_scene(scene: Scene) -> None:
        raise NotImplementedError()

    async def load_default_scene() -> None:
        _audio_input_devices = get_audio_input_devices()
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

        await load_scene(scene=_default_scene)

    async def on_mute_button_clicked(event: ft.ControlEvent) -> None:
        next_is_muted = not app_state.is_muted
        logger.info(
            f"mute button clicked: is_muted: {app_state.is_muted} -> {next_is_muted}"
        )

        if next_is_muted:
            mute_button.icon = ft.icons.MIC_OFF
        else:
            mute_button.icon = ft.icons.MIC

        app_state.is_muted = next_is_muted

        page.update()

    mute_button.on_click = on_mute_button_clicked

    async def on_record_button_clicked(event: ft.ControlEvent) -> None:
        next_is_recording = not app_state.is_recording
        logger.info(
            "record button clicked: is_recording: "
            f"{app_state.is_recording} -> {next_is_recording}"
        )

        if next_is_recording:
            record_button.icon = ft.icons.STOP
            pause_button.disabled = False

            app_state.is_paused = False
        else:
            record_button.icon = ft.icons.FIBER_MANUAL_RECORD
            pause_button.icon = ft.icons.PAUSE
            pause_button.disabled = True

        app_state.is_recording = next_is_recording

        page.update()

    record_button.on_click = on_record_button_clicked

    async def on_pause_button_clicked(event: ft.ControlEvent) -> None:
        next_is_paused = not app_state.is_paused
        logger.info(
            f"pause button clicked: is_muted: {app_state.is_paused} -> {next_is_paused}"
        )

        if next_is_paused:
            pause_button.icon = ft.icons.FIBER_MANUAL_RECORD
        else:
            pause_button.icon = ft.icons.PAUSE

        app_state.is_paused = not app_state.is_paused

        page.update()

    pause_button.on_click = on_pause_button_clicked

    page.add(
        ft.Container(
            ft.Text(value="label"),
            expand=True,
        ),
        ft.Row(
            controls=[
                mute_button,
                record_button,
                pause_button,
            ],
            alignment=ft.MainAxisAlignment.CENTER,
        ),
    )


async def run_app() -> None:
    await ft.app_async(target=flet_app_main)
