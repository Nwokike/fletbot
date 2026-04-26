"""Chat view — main conversational interface.

Uses design system tokens, native services (camera, audio, file picker),
and smart ad placement between messages.
"""

from __future__ import annotations

import logging
from typing import Optional

import flet as ft

from agent.runner import AgentRunner
from components.input_bar import InputBar
from components.message_bubble import MessageBubble, ThinkingIndicator
from components.quick_actions import QuickActionRow
from providers.base import MediaPart
from providers.gemma_provider import ResilientGemmaProvider
from services.audio import AudioService
from services.camera import CameraService
from services.file_picker import FilePickerService
from services.share import ShareService
from session.manager import Session, SessionManager
from theme import colors, tokens
from theme.styles import brand_gradient_bg, standard_appbar

logger = logging.getLogger(__name__)

# Insert an ad banner every N messages
_AD_INTERVAL = 6


class ChatView:
    """The main chat view managing conversation UI and agent interaction."""

    def __init__(
        self,
        page: ft.Page,
        api_key: str,
        session_manager: SessionManager,
        on_navigate: callable,
    ):
        self.page = page
        self.api_key = api_key
        self.session_manager = session_manager
        self.on_navigate = on_navigate

        # Provider + Runner
        self.provider = ResilientGemmaProvider(api_key=api_key)
        self.runner = AgentRunner(provider=self.provider)

        # Native services
        self._camera = CameraService(page)
        self._audio = AudioService(page)
        self._share = ShareService(page)
        self._file_picker = FilePickerService(page, on_result=self._on_file_picked)

        # Pending media attachment
        self._pending_media: list[MediaPart] | None = None

        # Current session
        self.current_session: Optional[Session] = None
        self._is_generating = False
        self._message_count_since_ad = 0

        # UI controls
        self._message_list = ft.ListView(
            expand=True,
            spacing=0,
            auto_scroll=True,
            padding=ft.Padding.symmetric(
                horizontal=tokens.SPACE_MD, vertical=tokens.SPACE_SM
            ),
        )

        self._thinking = ThinkingIndicator()
        self._thinking.visible = False

        self._input_bar = InputBar(
            on_send=self._on_send,
            on_camera=self._on_camera,
            on_mic=self._on_mic,
            on_attach=self._on_attach,
        )

        self._streaming_bubble: Optional[MessageBubble] = None

    # ── Session Management ──────────────────────────────────────────

    def new_chat(self):
        """Start a new conversation."""
        self.current_session = self.session_manager.create_session()
        self._message_list.controls.clear()
        self._message_count_since_ad = 0
        self._add_welcome_message()
        self.page.update()

    def load_session(self, session_id: str):
        """Load an existing conversation session."""
        session = self.session_manager.get_session(session_id)
        if not session:
            self.new_chat()
            return

        self.current_session = session
        self._message_list.controls.clear()
        self._message_count_since_ad = 0

        for msg in session.messages:
            bubble = MessageBubble(
                role=msg.role,
                content=msg.content,
                on_copy=self._copy_response,
                on_share=self._share_response,
            )
            self._message_list.controls.append(bubble)
            self._message_count_since_ad += 1
            self._maybe_insert_ad()

        self.page.update()

    # ── Welcome ─────────────────────────────────────────────────────

    def _add_welcome_message(self):
        """Show welcome message in empty chat."""
        welcome = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Image(
                        src="icon.png",
                        width=tokens.ICON_LOGO,
                        height=tokens.ICON_LOGO,
                        fit=ft.BoxFit.CONTAIN,
                    ),
                    ft.Text(
                        "Hello! I'm FletBot 👋",
                        size=tokens.FONT_XXL,
                        weight=ft.FontWeight.BOLD,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Text(
                        "Powered by Gemma 4 — ask me anything!",
                        size=14,
                        color=ft.Colors.ON_SURFACE_VARIANT,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Container(height=tokens.SPACE_LG),
                    QuickActionRow(on_send=self._on_send),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=tokens.SPACE_XS,
            ),
            alignment=ft.Alignment.CENTER,
            expand=True,
            padding=tokens.SPACE_XXXL,
        )
        self._message_list.controls.append(welcome)

    # ── Sending Messages ────────────────────────────────────────────

    def _on_send(self, text: str):
        """Handle user sending a message."""
        if self._is_generating or not text:
            return

        if not self.current_session:
            self.new_chat()

        # Clear welcome if first message
        if self.current_session.message_count == 0:
            self._message_list.controls.clear()

        # Add user message
        self.current_session.add_message("user", text)
        user_bubble = MessageBubble(role="user", content=text)
        self._message_list.controls.append(user_bubble)
        self._message_count_since_ad += 1

        # Show thinking indicator
        self._thinking.visible = True
        self._message_list.controls.append(self._thinking)
        self._input_bar.set_disabled(True)
        self._is_generating = True
        self.page.update()

        # Capture and clear pending media
        media = self._pending_media
        self._pending_media = None

        self.page.run_task(self._generate_response, text, media)

    async def _generate_response(
        self, user_text: str, media: list[MediaPart] | None = None
    ):
        """Generate AI response with streaming."""
        try:
            if self._thinking in self._message_list.controls:
                self._message_list.controls.remove(self._thinking)

            self._streaming_bubble = MessageBubble(
                role="assistant",
                content="",
                on_copy=self._copy_response,
                on_share=self._share_response,
            )
            self._message_list.controls.append(self._streaming_bubble)
            self.page.update()

            full_response = ""
            model_used = ""

            async for chunk, model in self.runner.send_message_stream(
                user_text, self.current_session, media=media
            ):
                full_response += chunk
                model_used = model

                if self._streaming_bubble in self._message_list.controls:
                    idx = self._message_list.controls.index(self._streaming_bubble)
                    self._message_list.controls[idx] = MessageBubble(
                        role="assistant",
                        content=full_response,
                        on_copy=self._copy_response,
                        on_share=self._share_response,
                    )
                    self._streaming_bubble = self._message_list.controls[idx]
                    self.page.update()

            if full_response:
                self.current_session.add_message("assistant", full_response)
                self.session_manager.save(self.current_session)
                self._message_count_since_ad += 1
                self._maybe_insert_ad()
                logger.info("Response from %s saved to session", model_used)

        except Exception as e:
            logger.error("Generation error: %s", e)
            if self._thinking in self._message_list.controls:
                self._message_list.controls.remove(self._thinking)
            if (
                self._streaming_bubble
                and self._streaming_bubble in self._message_list.controls
            ):
                self._message_list.controls.remove(self._streaming_bubble)

            error_bubble = MessageBubble(
                role="assistant",
                content=f"⚠️ Sorry, I encountered an error:\n\n`{str(e)[:200]}`\n\nPlease try again.",
            )
            self._message_list.controls.append(error_bubble)

        finally:
            self._is_generating = False
            self._thinking.visible = False
            self._input_bar.set_disabled(False)
            self.page.update()

    # ── Native Service Handlers ─────────────────────────────────────

    def _on_camera(self):
        """Handle camera button tap."""
        self.page.run_task(self._capture_camera)

    async def _capture_camera(self):
        from services import PermissionService
        perm = PermissionService(self.page)
        if not await perm.request_camera():
            return
        result = await self._camera.capture_photo()
        if result:
            data, mime = result
            self._pending_media = [MediaPart(mime_type=mime, data=data)]
            self.page.show_dialog(
                ft.SnackBar(content=ft.Text("📷 Photo attached — type your message"))
            )

    def _on_mic(self):
        """Handle mic button tap — toggle recording."""
        self.page.run_task(self._toggle_recording)

    async def _toggle_recording(self):
        if self._audio.is_recording:
            result = await self._audio.stop_recording()
            self._input_bar.set_recording(False)
            if result:
                data, mime = result
                self._pending_media = [MediaPart(mime_type=mime, data=data)]
                self.page.show_dialog(
                    ft.SnackBar(
                        content=ft.Text("🎤 Recording attached — type your message")
                    )
                )
        else:
            from services import PermissionService
            perm = PermissionService(self.page)
            if not await perm.request_microphone():
                return
            started = await self._audio.start_recording()
            if started:
                self._input_bar.set_recording(True)

    def _on_attach(self):
        """Handle attach button tap."""
        self._file_picker.pick_file()

    def _on_file_picked(self, data: bytes, mime: str, filename: str):
        """Callback when a file is picked."""
        self._pending_media = [
            MediaPart(mime_type=mime, data=data, filename=filename)
        ]
        self.page.show_dialog(
            ft.SnackBar(content=ft.Text(f"📎 {filename} attached — type your message"))
        )

    # ── Clipboard / Share ───────────────────────────────────────────

    def _copy_response(self, text: str):
        self.page.run_task(self._share.copy_text, text)

    def _share_response(self, text: str):
        self._share.share_text(text)

    # ── Smart Ad Placement ──────────────────────────────────────────

    def _maybe_insert_ad(self):
        """Insert a banner ad every N messages."""
        if self._message_count_since_ad >= _AD_INTERVAL:
            try:
                from ads.manager import AdManager

                ad_manager = AdManager(self.page)
                banner = ad_manager.create_inline_banner()
                if banner:
                    self._message_list.controls.append(banner)
                    self._message_count_since_ad = 0
            except Exception:
                pass  # Ads are optional

    # ── View Builder ────────────────────────────────────────────────

    def build_view(self) -> ft.View:
        """Build the complete chat view."""

        def on_new_chat(e):
            self.new_chat()

        def on_history(e):
            self.on_navigate("/history")

        def on_settings(e):
            self.on_navigate("/settings")

        appbar = standard_appbar(
            "FletBot",
            leading=ft.IconButton(
                icon=ft.Icons.HISTORY_ROUNDED,
                tooltip="History",
                on_click=on_history,
            ),
            actions=[
                ft.IconButton(
                    icon=ft.Icons.ADD_COMMENT_ROUNDED,
                    tooltip="New Chat",
                    on_click=on_new_chat,
                ),
                ft.IconButton(
                    icon=ft.Icons.SETTINGS_ROUNDED,
                    tooltip="Settings",
                    on_click=on_settings,
                ),
            ],
            transparent=True,
        )

        if not self.current_session:
            self.new_chat()

        view_controls: list[ft.Control] = [self._message_list, self._input_bar]

        gradient_bg = brand_gradient_bg(
            ft.Column(
                controls=view_controls,
                spacing=0,
                expand=True,
            )
        )

        view = ft.View(
            route="/chat",
            controls=[gradient_bg],
            appbar=appbar,
            padding=0,
            spacing=0,
        )

        return view
