"""Chat view — main conversational interface."""

from __future__ import annotations

import logging
from typing import Optional

import flet as ft

from agent.runner import AgentRunner
from components.input_bar import InputBar
from components.message_bubble import MessageBubble, ThinkingIndicator
from providers.gemma_provider import ResilientGemmaProvider
from session.manager import Session, SessionManager

logger = logging.getLogger(__name__)


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

        # Current session
        self.current_session: Optional[Session] = None
        self._is_generating = False

        # UI controls
        self._message_list = ft.ListView(
            expand=True,
            spacing=0,
            auto_scroll=True,
            padding=ft.padding.symmetric(horizontal=12, vertical=8),
        )

        self._thinking = ThinkingIndicator()
        self._thinking.visible = False

        self._input_bar = InputBar(on_send=self._on_send)

        self._streaming_bubble: Optional[MessageBubble] = None

    def new_chat(self):
        """Start a new conversation."""
        self.current_session = self.session_manager.create_session()
        self._message_list.controls.clear()
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

        # Rebuild message bubbles
        for msg in session.messages:
            bubble = MessageBubble(role=msg.role, content=msg.content)
            self._message_list.controls.append(bubble)

        self.page.update()

    def _add_welcome_message(self):
        """Show welcome message in empty chat."""
        welcome = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Image(
                        src="icon.png",
                        width=64,
                        height=64,
                        fit=ft.BoxFit.CONTAIN,
                    ),
                    ft.Text(
                        "Hello! I'm FletBot 👋",
                        size=22,
                        weight=ft.FontWeight.BOLD,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Text(
                        "Powered by Gemma 4 — ask me anything!",
                        size=14,
                        color=ft.Colors.ON_SURFACE_VARIANT,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Container(height=16),
                    # Quick suggestion chips
                    ft.Row(
                        controls=[
                            ft.ElevatedButton(
                                content=ft.Text("Explain quantum computing"),
                                on_click=lambda e: self._on_send(
                                    "Explain quantum computing in simple terms"
                                ),
                                style=ft.ButtonStyle(
                                    shape=ft.RoundedRectangleBorder(radius=20),
                                    padding=ft.padding.symmetric(horizontal=16, vertical=8),
                                ),
                            ),
                            ft.ElevatedButton(
                                content=ft.Text("Write a poem"),
                                on_click=lambda e: self._on_send(
                                    "Write a short poem about the ocean"
                                ),
                                style=ft.ButtonStyle(
                                    shape=ft.RoundedRectangleBorder(radius=20),
                                    padding=ft.padding.symmetric(horizontal=16, vertical=8),
                                ),
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        wrap=True,
                        spacing=8,
                    ),
                    ft.Row(
                        controls=[
                            ft.ElevatedButton(
                                content=ft.Text("Help me cook dinner"),
                                on_click=lambda e: self._on_send(
                                    "Suggest a quick dinner recipe with chicken"
                                ),
                                style=ft.ButtonStyle(
                                    shape=ft.RoundedRectangleBorder(radius=20),
                                    padding=ft.padding.symmetric(horizontal=16, vertical=8),
                                ),
                            ),
                            ft.ElevatedButton(
                                content=ft.Text("Translate to French"),
                                on_click=lambda e: self._on_send(
                                    "Translate 'Hello, how are you today?' to French"
                                ),
                                style=ft.ButtonStyle(
                                    shape=ft.RoundedRectangleBorder(radius=20),
                                    padding=ft.padding.symmetric(horizontal=16, vertical=8),
                                ),
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        wrap=True,
                        spacing=8,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=4,
            ),
            alignment=ft.Alignment.CENTER,
            expand=True,
            padding=40,
        )
        self._message_list.controls.append(welcome)

    def _on_send(self, text: str):
        """Handle user sending a message."""
        if self._is_generating or not text:
            return

        # Ensure we have a session
        if not self.current_session:
            self.new_chat()

        # Clear welcome message if it's the first message
        if self.current_session.message_count == 0:
            self._message_list.controls.clear()

        # Add user message
        self.current_session.add_message("user", text)
        user_bubble = MessageBubble(role="user", content=text)
        self._message_list.controls.append(user_bubble)

        # Show thinking indicator
        self._thinking.visible = True
        self._message_list.controls.append(self._thinking)
        self._input_bar.set_disabled(True)
        self._is_generating = True
        self.page.update()

        # Run AI generation in background
        self.page.run_task(self._generate_response, text)

    async def _generate_response(self, user_text: str):
        """Generate AI response with streaming."""
        try:
            # Remove thinking indicator and add streaming bubble
            if self._thinking in self._message_list.controls:
                self._message_list.controls.remove(self._thinking)

            # Create a streaming bubble that we'll update
            self._streaming_bubble = MessageBubble(role="assistant", content="")
            self._message_list.controls.append(self._streaming_bubble)
            self.page.update()

            full_response = ""
            model_used = ""

            async for chunk, model in self.runner.send_message_stream(
                user_text, self.current_session
            ):
                full_response += chunk
                model_used = model

                # Update the streaming bubble content
                if self._streaming_bubble in self._message_list.controls:
                    idx = self._message_list.controls.index(self._streaming_bubble)
                    self._message_list.controls[idx] = MessageBubble(
                        role="assistant", content=full_response
                    )
                    self._streaming_bubble = self._message_list.controls[idx]
                    self.page.update()

            # Save the complete response to session
            if full_response:
                self.current_session.add_message("assistant", full_response)
                self.session_manager.save(self.current_session)
                logger.info("Response from %s saved to session", model_used)

        except Exception as e:
            logger.error("Generation error: %s", e)
            # Remove thinking/streaming bubble and show error
            if self._thinking in self._message_list.controls:
                self._message_list.controls.remove(self._thinking)
            if self._streaming_bubble and self._streaming_bubble in self._message_list.controls:
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

    def build_view(self) -> ft.View:
        """Build the complete chat view."""

        def on_new_chat(e):
            self.new_chat()

        def on_history(e):
            self.on_navigate("/history")

        def on_settings(e):
            self.on_navigate("/settings")

        appbar = ft.AppBar(
            leading=ft.IconButton(
                icon=ft.Icons.HISTORY_ROUNDED,
                tooltip="History",
                on_click=on_history,
            ),
            title=ft.Text(
                "FletBot",
                weight=ft.FontWeight.W_600,
                size=20,
            ),
            center_title=True,
            bgcolor=ft.Colors.TRANSPARENT,
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
        )

        # Initialize with new chat if no session
        if not self.current_session:
            self.new_chat()

        # Build controls list with optional ad banner
        view_controls = [self._message_list]

        # AdMob banner (mobile only)
        try:
            from ads.manager import AdManager

            ad_manager = AdManager(self.page)
            banner = ad_manager.create_banner_ad()
            if banner:
                view_controls.append(banner)
        except Exception:
            pass  # Ads are optional — skip silently

        view_controls.append(self._input_bar)

        # Wrap in a gradient container
        gradient_bg = ft.Container(
            content=ft.Column(
                controls=view_controls,
                spacing=0,
                expand=True,
            ),
            expand=True,
            gradient=ft.LinearGradient(
                begin=ft.Alignment.TOP_LEFT,
                end=ft.Alignment.BOTTOM_RIGHT,
                colors=["#0B1914", "#050A08", "#1A1400"],
            ),
        )

        view = ft.View(
            route="/chat",
            controls=[gradient_bg],
            appbar=appbar,
            padding=0,
            spacing=0,
        )

        return view
