import asyncio
import math
import struct
import tempfile
import traceback
from datetime import datetime, timezone
from logging import getLogger
from pathlib import Path

import flet as ft
import pyaudio

from ...audio_input_device_manager import AudioInputDeviceManager
from ...config_store_manager import Config, ConfigStoreManager
from ...scene import SceneDevice
from ..app_state import AppState

logger = getLogger(__name__)


class Home(ft.View):  # type:ignore[misc]
    main_task_future: asyncio.Future | None
    record_task_future: asyncio.Future | None

    scene_dropdown: ft.Dropdown | None

    audio_input_device_list_view: ft.ListView | None
    track_list_view: ft.ListView | None

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
        self.record_task_future = None

        self.scene_dropdown = None

        self.audio_input_device_list_view = None
        self.track_list_view = None

        self.app_state = app_state
        self.audio_input_device_manager = audio_input_device_manager
        self.config_store_manager = config_store_manager

    def build(self) -> None:
        page = self.page
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
        self.scene_dropdown = scene_dropdown

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
            page = self.page

            next_is_recording = not app_state.is_recording
            logger.info(
                "record button clicked: is_recording: "
                f"{app_state.is_recording} -> {next_is_recording}"
            )

            if next_is_recording:
                # 録音開始
                record_button.icon = ft.icons.STOP

                pause_button.icon = ft.icons.PAUSE
                pause_button.disabled = False

                app_state.is_paused = False
                app_state.is_recording = True

                self.record_task_future = page.run_task(self.record_task)
            else:
                # 録音終了
                record_button.icon = ft.icons.FIBER_MANUAL_RECORD

                pause_button.icon = ft.icons.PAUSE
                pause_button.disabled = True

                app_state.is_paused = False
                app_state.is_recording = False

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

        self.controls = [
            ft.Column(
                controls=[
                    ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Text(value="シーン"),
                                    add_scene_button,
                                ],
                            ),
                            scene_dropdown,
                        ],
                    ),
                    ft.Row(
                        controls=[
                            ft.Column(
                                controls=[
                                    ft.Row(
                                        controls=[
                                            ft.Text(value="音声入力デバイス"),
                                            add_audio_input_device_button,
                                        ],
                                    ),
                                    audio_input_device_list_view,
                                ],
                                expand=True,
                            ),
                            ft.Column(
                                controls=[
                                    ft.Row(
                                        controls=[
                                            ft.Text(value="トラック"),
                                            add_track_button,
                                        ],
                                    ),
                                    track_list_view,
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
        audio_input_device_list_view = self.audio_input_device_list_view
        track_list_view = self.track_list_view

        assert audio_input_device_list_view is not None

        scene = app_state.scenes[index]

        audio_input_device_list_view.controls.clear()
        for device in scene.devices:
            device_mute_button = ft.IconButton(icon=ft.icons.MIC, icon_size=20)
            device_edit_button = ft.IconButton(icon=ft.icons.EDIT, icon_size=20)

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
                                    ft.Text(
                                        value=f"{device.portaudio_name}",
                                        overflow=ft.TextOverflow.FADE,
                                        no_wrap=True,
                                        expand=True,
                                    ),
                                ],
                                expand=True,
                            ),
                            ft.Row(
                                controls=[
                                    device_mute_button,
                                    device_edit_button,
                                ],
                            ),
                        ],
                        spacing=0,
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    bgcolor=ft.colors.ON_SECONDARY,
                    alignment=ft.alignment.center,
                    padding=16,
                    height=70,
                ),
            )

        track_list_view.controls.clear()
        for track in scene.tracks:
            track_edit_button = ft.IconButton(icon=ft.icons.EDIT, icon_size=20)

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
                                    ft.Text(
                                        value=f"{track.name}",
                                        overflow=ft.TextOverflow.FADE,
                                        no_wrap=True,
                                        expand=True,
                                    ),
                                ],
                                expand=True,
                            ),
                            ft.Row(
                                controls=[
                                    track_edit_button,
                                ],
                            ),
                        ],
                        spacing=0,
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    bgcolor=ft.colors.ON_SECONDARY,
                    alignment=ft.alignment.center,
                    padding=16,
                    height=70,
                ),
            )

        app_state.is_recording = False
        app_state.is_paused = False

        app_state.selected_scene_index = index
        page.update()

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

        # TODO: 録音中のシーン切り替えを禁止する

        selected_index = int(selected_index_string)
        await self.load_scene(index=selected_index)

    async def on_add_audio_input_device_button_clicked(
        self,
        event: ft.ControlEvent,
    ) -> None:
        page = self.page

        page.go("/add_audio_input_device")

    async def on_add_track_button_clicked(
        self,
        event: ft.ControlEvent,
    ) -> None:
        page = self.page

        page.go("/add_track")

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

    async def record_task(self) -> None:
        try:
            app_state = self.app_state

            app_state.recording_started_at = datetime.now(tz=timezone.utc)

            selected_scene_index = self.app_state.selected_scene_index
            assert selected_scene_index is not None
            scene = self.app_state.scenes[selected_scene_index]

            devices = scene.devices
            tracks = scene.tracks

            pyaudio_instance = pyaudio.PyAudio()

            with tempfile.TemporaryDirectory() as tmpdir:
                tmpdir_path = Path(tmpdir)

                async with asyncio.TaskGroup() as task_group:
                    for device_index, device in enumerate(devices):
                        temp_output_path = tmpdir_path / f"{device_index}.bin"

                        task_group.create_task(
                            self.device_record_task(
                                pyaudio_instance=pyaudio_instance,
                                scene_device=device,
                                temp_output_path=temp_output_path,
                            ),
                        )

                try:
                    # TODO: use output dir from scene config
                    # TODO: choice output file extension (m4a, mp4) for VLC compatibility
                    recording_started_at = app_state.recording_started_at
                    timestamp = (
                        recording_started_at
                        if recording_started_at is not None
                        else datetime.now(tz=timezone.utc)
                    )

                    # e.g. 2024-04-01T00-00-00Z
                    timestamp_string = (
                        timestamp.astimezone(tz=timezone.utc)
                        .isoformat(timespec="seconds")
                        .replace("+00:00", "Z")
                        .replace(":", "-")
                    )
                    output_path = Path(scene.output_dir) / f"rec_{timestamp_string}.m4a"
                    output_path.parent.mkdir(parents=True, exist_ok=True)

                    cmd = [
                        "ffmpeg",
                        "-y",
                    ]

                    # 0番目の音声入力を無音にする
                    cmd += [
                        "-f",
                        "lavfi",
                        "-i",
                        "anullsrc",
                    ]

                    # 各音声入力デバイスを1番目以降の音声入力にする
                    for device_index, device in enumerate(devices):
                        temp_output_path = tmpdir_path / f"{device_index}.bin"

                        cmd += [
                            "-f",
                            "f32le",
                            "-ar",
                            str(device.sampling_rate),
                            "-ac",
                            str(device.channels),
                            "-i",
                            str(temp_output_path.resolve()),
                        ]

                    for track_index, track in enumerate(tracks):
                        track_device_input_indexes: list[int] = []

                        for device_index, device in enumerate(devices):
                            if track_index in device.tracks:
                                # 音声入力デバイスの入力は1番目以降
                                track_device_input_indexes.append(1 + device_index)

                        if len(track_device_input_indexes) == 0:
                            # トラックに入力される音声入力デバイスが0の場合、入力番号0の無音を入力する
                            track_device_input_indexes.append(0)

                        track_device_source_string = ""
                        for track_device_index in track_device_input_indexes:
                            track_device_source_string += f"[{track_device_index}:a:0]"

                        cmd += [
                            "-filter_complex",
                            f"{track_device_source_string}amix=inputs={len(track_device_input_indexes)}[t{track_index}]",
                        ]

                        cmd += [
                            "-map",
                            f"[t{track_index}]",
                            "-c:a",
                            "aac",  # Native FFmpeg AAC Encoder
                            "-b:a",
                            "160k",
                            "-metadata:s:a:0",
                            f"title={track.name}",  # .mp4
                            "-metadata:s:a:0",
                            f"handler_name={track.name}",  # .m4a (but VLC not working)
                        ]

                    cmd += [
                        str(output_path.resolve()),
                    ]

                    proc = await asyncio.create_subprocess_exec(
                        cmd[0],
                        *cmd[1:],
                    )

                    return_code = await proc.wait()
                    logger.info(f"FFmpeg return code: {return_code}")
                finally:
                    temp_output_path.unlink(missing_ok=True)
        except Exception:
            logger.error(traceback.format_exc())
            raise

    async def device_record_task(
        self,
        pyaudio_instance: pyaudio.PyAudio,
        scene_device: SceneDevice,
        temp_output_path: Path,
    ) -> None:
        app_state = self.app_state

        channels = 1
        format = pyaudio.paFloat32
        num_frames = 1024

        with temp_output_path.open("wb") as fp:
            total_byte_count = 0

            audio_input_stream = pyaudio_instance.open(
                input=True,
                input_device_index=scene_device.portaudio_index,
                rate=scene_device.sampling_rate,
                channels=channels,
                format=format,
                frames_per_buffer=num_frames,
            )

            try:
                while app_state.is_recording:
                    if not audio_input_stream.get_read_available():
                        logger.info("waiting")
                        await asyncio.sleep(0.01)
                        continue

                    chunk_bytes = audio_input_stream.read(num_frames=num_frames)

                    is_muted = app_state.is_muted or scene_device.is_muted
                    if not is_muted:
                        fp.write(chunk_bytes)
                    else:
                        # ミュート中は -60 dB 扱い
                        fp.write(struct.pack("<f", 1e-3) * len(chunk_bytes))

                    total_byte_count += len(chunk_bytes)

                    # 先頭 4 bytes (f32le)
                    first_float_bytes = chunk_bytes[:4]
                    first_float_value: float = struct.unpack(
                        "<f",
                        first_float_bytes,
                    )[0]

                    decibel_minimum_limit = -60
                    try:
                        first_float_decibel_value = max(
                            20 * math.log10(first_float_value),
                            decibel_minimum_limit,
                        )
                    except ValueError:
                        # ValueError: math domain error if first_float_value ~ 0.0
                        first_float_decibel_value = decibel_minimum_limit

                    logger.info(
                        f"[recording] {total_byte_count=} "
                        f"({first_float_decibel_value=} dB)"
                    )

                    await asyncio.sleep(0.01)
            finally:
                audio_input_stream.close()
                logger.info("audio_input_stream closed")
