import asyncio
import math
import struct
import tempfile
import traceback
from logging import getLogger
from pathlib import Path

import flet as ft
import pyaudio

from ...audio_input_device_manager import AudioInputDeviceManager
from ...config_store_manager import Config, ConfigStoreManager
from ..app_state import AppState

logger = getLogger(__name__)


class Home(ft.View):  # type:ignore[misc]
    main_task_future: asyncio.Future | None
    record_task_future: asyncio.Future | None
    audio_input_device_list_view: ft.ListView | None

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
        self.audio_input_device_list_view = None

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

        scene_dropdown = ft.Dropdown(
            value="0" if len(scene_options) > 0 else None,
            options=scene_options,
        )

        add_audio_input_device_button = ft.IconButton(
            icon=ft.icons.ADD,
            icon_size=24,
            on_click=self.on_add_audio_input_device_button_clicked,
        )

        audio_input_device_list_view = ft.ListView(
            expand=1,
            spacing=10,
            padding=20,
            auto_scroll=True,
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
            padding=20,
            auto_scroll=True,
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
            audio_input_device_list_view.controls.append(
                ft.Row(
                    controls=[
                        ft.Icon(name=ft.icons.MIC, size=16, color=ft.colors.ON_SURFACE),
                        ft.Text(f"{device.portaudio_name}"),
                        ft.IconButton(icon=ft.icons.MIC),
                    ],
                ),
            )

        for track in scene.tracks:
            track_list_view.controls.append(ft.Text(f"{track.name}"))

        app_state.is_recording = False
        app_state.is_paused = False

        app_state.selected_scene_index = index
        page.update()

    async def on_add_scene_button_clicked(
        self,
        event: ft.ControlEvent,
    ) -> None:
        logger.info("on_add_scene_button_clicked")

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
        logger.info("on_add_track_button_clicked")

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
            await self.load_scene(index=0)
        except Exception:
            logger.error(traceback.format_exc())
            raise

    async def record_task(self) -> None:
        try:
            app_state = self.app_state

            selected_scene_index = self.app_state.selected_scene_index
            assert selected_scene_index is not None
            scene = self.app_state.scenes[selected_scene_index]

            first_audio_input_device = scene.devices[0]

            first_track = scene.tracks[0]
            first_track_name = first_track.name

            input_sampling_rate = 44100
            channels = 1
            format = pyaudio.paFloat32
            num_frames = 1024

            pyaudio_instance = pyaudio.PyAudio()

            with tempfile.TemporaryDirectory() as tmpdir:
                tmpdir_path = Path(tmpdir)
                temp_output_path = tmpdir_path / "0.bin"
                try:
                    with temp_output_path.open("wb") as fp:
                        try:
                            audio_input_stream = pyaudio_instance.open(
                                input=True,
                                input_device_index=first_audio_input_device.portaudio_index,
                                rate=input_sampling_rate,
                                channels=channels,
                                format=format,
                                frames_per_buffer=num_frames,
                            )

                            total_byte_count = 0

                            while app_state.is_recording:
                                if not audio_input_stream.get_read_available():
                                    logger.info("waiting")
                                    await asyncio.sleep(0.01)
                                    continue

                                chunk_bytes = audio_input_stream.read(
                                    num_frames=num_frames
                                )

                                is_muted = (
                                    app_state.is_muted or first_audio_input_device.muted
                                )
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

                    output_file = "work/output.m4a"
                    cmd = [
                        "ffmpeg",
                        "-y",
                        "-f",
                        "f32le",
                        "-ar",
                        str(input_sampling_rate),
                        "-ac",
                        str(channels),
                        "-i",
                        str(temp_output_path.resolve()),
                        "-map",
                        "0:a:0",
                        "-c:a",
                        "aac",  # Native FFmpeg AAC Encoder
                        "-b:a",
                        "160k",
                        "-metadata:s:a:0",
                        f"title={first_track_name}",  # .mp4
                        "-metadata:s:a:0",
                        f"handler_name={first_track_name}",  # .m4a (but VLC not working)
                        output_file,
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
