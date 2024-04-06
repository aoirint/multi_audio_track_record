from dataclasses import dataclass
from logging import getLogger

import flet as ft

from .. import __version__ as APP_VERSION

logger = getLogger(__name__)


@dataclass
class AppState:
    is_recording: bool = False
    is_paused: bool = False
    is_muted: bool = False


async def flet_app_main(page: ft.Page) -> None:
    page.title = f"Multi Audio Track Recorder v{APP_VERSION}"
    page.window_width = 400
    page.window_height = 400

    app_state = AppState()

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
        next_is_recording = not app_state.is_recording
        logger.info(
            f"record button clicked: is_recording: {app_state.is_recording} -> {next_is_recording}"
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
