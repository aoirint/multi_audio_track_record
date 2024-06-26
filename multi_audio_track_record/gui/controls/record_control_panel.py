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
from ...config_store_manager import ConfigStoreManager
from ...scene import Scene, SceneDevice
from ..app_state import AppState

logger = getLogger(__name__)


class RecordControlPanel(ft.Row):  # type:ignore[misc]
    mute_button: ft.IconButton | None
    record_button: ft.IconButton | None
    pause_button: ft.IconButton | None

    record_task_future: asyncio.Future | None

    def __init__(
        self,
        app_state: AppState,
        audio_input_device_manager: AudioInputDeviceManager,
        config_store_manager: ConfigStoreManager,
        alignment: ft.MainAxisAlignment,
    ):
        super().__init__(alignment=alignment)

        self.mute_button = None
        self.record_button = None
        self.pause_button = None

        self.app_state = app_state
        self.audio_input_device_manager = audio_input_device_manager
        self.config_store_manager = config_store_manager

        self.record_task_future = None

    def build(self) -> None:
        mute_button = ft.IconButton(
            icon=ft.icons.MIC,
            icon_size=32,
            on_click=self.on_mute_button_clicked,
        )

        record_button = ft.IconButton(
            icon=ft.icons.FIBER_MANUAL_RECORD,
            icon_size=64,
            on_click=self.on_record_button_clicked,
        )

        pause_button = ft.IconButton(
            icon=ft.icons.PAUSE,
            icon_size=32,
            disabled=True,
            on_click=self.on_pause_button_clicked,
        )

        self.mute_button = mute_button
        self.record_button = record_button
        self.pause_button = pause_button

        self.controls = [
            mute_button,
            record_button,
            pause_button,
        ]

    async def on_mute_button_clicked(self, event: ft.ControlEvent) -> None:
        page = self.page
        app_state = self.app_state

        mute_button = self.mute_button
        assert mute_button is not None

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

    async def on_record_button_clicked(self, event: ft.ControlEvent) -> None:
        page = self.page
        app_state = self.app_state

        record_button = self.record_button
        assert record_button is not None

        pause_button = self.pause_button
        assert pause_button is not None

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

    async def on_pause_button_clicked(self, event: ft.ControlEvent) -> None:
        page = self.page
        app_state = self.app_state

        pause_button = self.pause_button
        assert pause_button is not None

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

    async def on_scene_loaded(
        self,
        scene: Scene,
    ) -> None:
        pass

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
