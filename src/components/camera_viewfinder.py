"""Camera viewfinder overlay component.

Provides a full-screen or dialog-based overlay containing the live camera feed,
with manual controls for taking pictures, recording videos, and flipping cameras.
"""

import asyncio
import logging
import os
import tempfile
from typing import Callable, Optional

import flet as ft

from theme import colors, tokens
import theme.colors as theme_colors

logger = logging.getLogger(__name__)

_HAS_CAMERA = False
try:
    from flet_camera import Camera
    from flet_camera.types import ResolutionPreset

    _HAS_CAMERA = True
except ImportError:
    pass

class CameraViewfinder(ft.Stack):
    """Full-screen camera viewfinder overlay."""

    def __init__(
        self,
        page: ft.Page,
        on_capture: Callable[[bytes, str, str], None],  # (data, mime, filename)
        on_close: Callable[[], None],
    ):
        super().__init__(expand=True)
        self._page = page
        self._on_capture = on_capture
        self._on_close = on_close

        self._camera: Optional[Camera] = None
        self._cameras = []
        self._current_camera_index = 0
        
        self._is_video_mode = False
        self._is_recording = False
        self._record_task = None
        self._video_path = None
        self._start_time = 0

        # UI Elements
        self._preview_container = ft.Container(expand=True, bgcolor=ft.Colors.BLACK)
        
        self._close_btn = ft.IconButton(
            icon=ft.Icons.CLOSE_ROUNDED,
            icon_color=ft.Colors.WHITE,
            icon_size=32,
            bgcolor="#44000000",  # Semi-transparent dark circle
            on_click=self._handle_close,
        )
        
        self._flip_btn = ft.IconButton(
            icon=ft.Icons.FLIP_CAMERA_IOS_ROUNDED,
            icon_color=ft.Colors.WHITE,
            icon_size=32,
            on_click=self._handle_flip,
            visible=False,
        )

        self._capture_btn = ft.Container(
            width=72,
            height=72,
            border_radius=36,
            border=ft.Border.all(4, theme_colors.KIRI_GREEN),
            bgcolor=ft.Colors.WHITE,
            on_click=self._handle_capture,
            animate=ft.Animation(tokens.ANIMATION_MS, ft.AnimationCurve.EASE_OUT),
        )

        self._mode_label = ft.Text(
            "SWITCH TO VIDEO",
            color=ft.Colors.WHITE,
            size=tokens.FONT_XS,
            weight=ft.FontWeight.BOLD,
        )
        
        self._mode_btn = ft.Container(
            content=self._mode_label,
            padding=ft.Padding.symmetric(horizontal=tokens.SPACE_LG, vertical=tokens.SPACE_XS),
            border_radius=tokens.RADIUS_XL,
            bgcolor="#44000000",
            on_click=self._toggle_mode,
        )

        self._timer_text = ft.Text(
            "00:00", 
            color=ft.Colors.WHITE, 
            size=tokens.FONT_LG, 
            weight=ft.FontWeight.BOLD,
            visible=False
        )

        # Layout
        self.controls = [
            self._preview_container,
            # Top Close Button
            ft.Container(
                content=self._close_btn,
                top=tokens.SPACE_LG,
                right=tokens.SPACE_LG,
            ),
            # Timer (Top Center)
            ft.Container(
                content=self._timer_text,
                top=tokens.SPACE_LG,
                alignment=ft.Alignment.TOP_CENTER,
            ),
            # Bottom Controls
            ft.Container(
                bottom=0,
                left=0,
                right=0,
                height=250,
                gradient=ft.LinearGradient(
                    begin=ft.Alignment.TOP_CENTER,
                    end=ft.Alignment.BOTTOM_CENTER,
                    colors=[ft.Colors.TRANSPARENT, "#CC000000"],
                ),
                content=ft.Column(
                    controls=[
                        # Mode Switcher
                        ft.Container(
                            content=self._mode_btn,
                            margin=ft.Margin.only(bottom=tokens.SPACE_MD),
                        ),
                        # Main Action Row
                        ft.Stack(
                            height=100,
                            controls=[
                                # Center: Capture Button
                                ft.Container(
                                    content=self._capture_btn,
                                    alignment=ft.Alignment.CENTER,
                                ),
                                # Right: Flip Button
                                ft.Container(
                                    content=self._flip_btn,
                                    right=tokens.SPACE_XXXL,
                                    alignment=ft.Alignment.CENTER_RIGHT,
                                ),
                            ],
                        ),
                        # Spacer for bottom safe area
                        ft.Container(height=tokens.SPACE_XXL),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.END,
                    spacing=0,
                ),
            )
        ]

    async def initialize(self) -> bool:
        """Initialize the camera and start preview."""
        if not _HAS_CAMERA:
            self._page.show_dialog(ft.SnackBar(content=ft.Text("Camera not supported on this platform.")))
            return False

        try:
            self._camera = Camera()
            self._preview_container.content = self._camera
            self.update()
            
            self._cameras = await self._camera.get_available_cameras()
            if not self._cameras:
                self._page.show_dialog(ft.SnackBar(content=ft.Text("No cameras found.")))
                return False

            if len(self._cameras) > 1:
                self._flip_btn.visible = True

            await self._camera.initialize(
                description=self._cameras[self._current_camera_index],
                resolution_preset=ResolutionPreset.MEDIUM,
                enable_audio=True,
            )
            self.update()
            return True
        except Exception as e:
            logger.error("Failed to initialize camera: %s", e)
            self._page.show_dialog(ft.SnackBar(content=ft.Text(f"Camera error: {e}")))
            return False

    async def _handle_flip(self, e):
        if not self._cameras or not self._camera:
            return
        
        self._current_camera_index = (self._current_camera_index + 1) % len(self._cameras)
        try:
            await self._camera.initialize(
                description=self._cameras[self._current_camera_index],
                resolution_preset=ResolutionPreset.MEDIUM,
                enable_audio=True,
            )
        except Exception as err:
            logger.error("Failed to flip camera: %s", err)

    def _toggle_mode(self, e):
        if self._is_recording:
            return
            
        self._is_video_mode = not self._is_video_mode
        self._mode_label.value = "SWITCH TO PHOTO" if self._is_video_mode else "SWITCH TO VIDEO"
        self._capture_btn.bgcolor = ft.Colors.RED if self._is_video_mode else ft.Colors.WHITE
        self.update()

    async def _handle_capture(self, e):
        if not self._camera:
            return

        if self._is_video_mode:
            if self._is_recording:
                await self._stop_video()
            else:
                await self._start_video()
        else:
            # Take photo
            try:
                # Provide visual feedback
                self._capture_btn.scale = 0.9
                self.update()
                await asyncio.sleep(0.1)
                
                image_bytes = await self._camera.take_picture()
                self._capture_btn.scale = 1.0
                self.update()
                
                if image_bytes:
                    self._on_capture(image_bytes, "image/jpeg", "photo.jpg")
                    self._handle_close(None)
            except Exception as err:
                logger.error("Photo capture failed: %s", err)

    async def _start_video(self):
        try:
            # Note: flet-camera on web/windows returns path in stop_video_recording()
            await self._camera.start_video_recording()
            self._is_recording = True
            
            # Update UI for recording state
            self._capture_btn.bgcolor = ft.Colors.RED
            self._capture_btn.border_radius = 8
            self._capture_btn.width = 48
            self._capture_btn.height = 48
            self._timer_text.visible = True
            self._timer_text.value = "00:00"
            self._flip_btn.visible = False
            self.update()

            self._record_task = self._page.run_task(self._video_timer)
        except Exception as err:
            logger.error("Video recording failed: %s", err)

    async def _stop_video(self):
        try:
            self._is_recording = False
            video_bytes = await self._camera.stop_video_recording()
            
            if video_bytes:
                self._on_capture(video_bytes, "video/mp4", "video.mp4")
                
            self._handle_close(None)
        except Exception as err:
            logger.error("Stop video failed: %s", err)

    async def _video_timer(self):
        elapsed = 0
        while self._is_recording and elapsed < 60:
            await asyncio.sleep(1)
            elapsed += 1
            mins, secs = divmod(elapsed, 60)
            self._timer_text.value = f"{mins:02d}:{secs:02d}"
            self.update()
            
        if self._is_recording and elapsed >= 60:
            # Reached 1 minute limit
            await self._stop_video()

    def _handle_close(self, e):
        if self._camera:
            try:
                # Cleanup inside the stack
                self._preview_container.content = None
                self.update()
            except Exception:
                pass
        self._on_close()
