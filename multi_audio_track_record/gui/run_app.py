from dataclasses import dataclass
from logging import getLogger

import flet as ft
import platformdirs

from .. import __version__ as APP_VERSION
from ..audio import get_audio_input_devices
from ..config import Config, load_config_file, save_config_file
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
    page.window_width = 600
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

    add_audio_input_dialog_audio_input_device_dropdown = ft.Dropdown()
    add_audio_input_dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("音声入力デバイスを選択"),
        content=ft.Container(
            content=add_audio_input_dialog_audio_input_device_dropdown,
        ),
        actions_alignment=ft.MainAxisAlignment.END,
    )

    async def on_add_audio_input_dialog_completed(event: ft.ControlEvent) -> None:
        add_audio_input_dialog.open = False
        page.update()

    async def on_add_audio_input_dialog_canceled(event: ft.ControlEvent) -> None:
        add_audio_input_dialog.open = False
        page.update()

    add_audio_input_dialog.actions = [
        ft.TextButton("キャンセル", on_click=on_add_audio_input_dialog_canceled),
        ft.TextButton("追加", on_click=on_add_audio_input_dialog_completed),
    ]
    add_audio_input_dialog.on_dismiss = on_add_audio_input_dialog_canceled

    async def open_add_audio_input_dialog(event: ft.ControlEvent) -> None:
        audio_input_devices = get_audio_input_devices()

        add_audio_input_dialog_audio_input_device_dropdown.value = None

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
        add_audio_input_dialog_audio_input_device_dropdown.options = options

        page.dialog = add_audio_input_dialog
        add_audio_input_dialog.open = True
        page.update()

    add_audio_input_device_button = ft.IconButton(
        icon=ft.icons.ADD,
        icon_size=24,
        on_click=open_add_audio_input_dialog,
    )
    add_track_button = ft.IconButton(
        icon=ft.icons.ADD,
        icon_size=24,
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

    async def save_config() -> None:
        save_config_file(
            config=Config(
                struct_version=1,
                scenes=app_state.scenes,
                selected_scene_index=app_state.selected_scene_index,
            ),
            path=config_file_path,
        )

    async def load_scene(index: int) -> None:
        app_state.selected_scene_index = index

        raise NotImplementedError()

    async def add_default_scene() -> None:
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

        app_state.scenes.append(_default_scene)
        default_scene_index = len(app_state.scenes) - 1
        await load_scene(index=default_scene_index)

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
        ft.Column(
            controls=[
                ft.Column(
                    controls=[
                        ft.Text(value="シーン"),
                        ft.Text(value="（未実装）"),
                    ],
                ),
                ft.Row(
                    controls=[
                        ft.Column(
                            controls=[
                                ft.Text(value="音声入力デバイス"),
                                add_audio_input_device_button,
                                ft.Text(value="（未実装）"),
                            ],
                            expand=True,
                        ),
                        ft.Column(
                            controls=[
                                ft.Text(value="トラック"),
                                add_track_button,
                                ft.Text(value="（未実装）"),
                            ],
                            expand=True,
                        ),
                    ],
                    expand=True,
                ),
            ],
            spacing=24,
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
