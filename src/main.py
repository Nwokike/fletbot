"""FletBot — Consumer AI assistant powered by Gemma 4.

Main entry point. Handles routing between views:
- /login  — API key entry
- /chat   — Main chat interface
- /history — Conversation history
- /settings — User settings
"""

from __future__ import annotations

import logging
import sys

import flet as ft

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("fletbot")

# Fix Windows event loop policy
if sys.platform == "win32":
    import asyncio

    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


async def main(page: ft.Page):
    """Main Flet application entry point."""

    # ── Page Configuration ──────────────────────────────────────────
    page.title = "FletBot"
    page.favicon = "favicon.ico"
    page.theme_mode = ft.ThemeMode.DARK

    # Load premium typography
    page.fonts = {
        "Outfit": "https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap"
    }

    # Material 3 theme with Kiri Green (#00A859) and Gold (#FFD700)
    page.theme = ft.Theme(
        color_scheme_seed="#00A859",
        font_family="Outfit",
    )
    page.dark_theme = ft.Theme(
        color_scheme_seed="#00A859",
        font_family="Outfit",
    )

    # Desktop window sizing
    page.window.width = 420
    page.window.height = 780
    page.window.min_width = 360
    page.window.min_height = 600

    page.padding = 0
    page.spacing = 0

    # ── Shared State ────────────────────────────────────────────────
    from auth.token_manager import TokenManager
    from session.manager import SessionManager

    token_manager = TokenManager(page)
    session_manager = SessionManager()

    # Chat view instance (persists across navigations)
    chat_view_instance = None

    # ── Navigation Helpers ──────────────────────────────────────────
    def navigate_to(route: str):
        page.go(route)

    def on_login_success():
        navigate_to("/chat")

    def on_logout():
        navigate_to("/login")

    # ── Route Change Handler ────────────────────────────────────────
    async def route_change(e: ft.RouteChangeEvent | None = None):
        nonlocal chat_view_instance

        route = page.route
        logger.info("Route changed to: %s", route)

        # Clear views and rebuild from route
        page.views.clear()

        if route == "/login":
            from views.login_view import build_login_view

            view = build_login_view(
                page=page,
                on_login_success=on_login_success,
                token_manager=token_manager,
            )
            page.views.append(view)

        elif route == "/chat":
            api_key = await token_manager.get_api_key()
            if not api_key:
                page.views.clear()
                from views.login_view import build_login_view

                view = build_login_view(
                    page=page,
                    on_login_success=on_login_success,
                    token_manager=token_manager,
                )
                page.views.append(view)
                page.route = "/login"
                page.update()
                return

            # Create or reuse chat view instance
            if chat_view_instance is None or chat_view_instance.api_key != api_key:
                from views.chat_view import ChatView

                chat_view_instance = ChatView(
                    page=page,
                    api_key=api_key,
                    session_manager=session_manager,
                    on_navigate=navigate_to,
                )

            page.views.append(chat_view_instance.build_view())

        elif route == "/history":
            from views.history_view import build_history_view

            def on_select_session(session_id: str):
                if chat_view_instance:
                    chat_view_instance.load_session(session_id)
                navigate_to("/chat")

            view = build_history_view(
                page=page,
                session_manager=session_manager,
                on_select_session=on_select_session,
                on_back=lambda: navigate_to("/chat"),
            )
            # Keep chat view underneath for back navigation
            if chat_view_instance:
                page.views.insert(0, chat_view_instance.build_view())
            page.views.append(view)

        elif route == "/settings":
            from views.settings_view import build_settings_view

            view = build_settings_view(
                page=page,
                token_manager=token_manager,
                on_back=lambda: navigate_to("/chat"),
                on_logout=on_logout,
            )
            # Keep chat view underneath for back navigation
            if chat_view_instance:
                page.views.insert(0, chat_view_instance.build_view())
            page.views.append(view)

        else:
            # Unknown route — go to chat or login
            has_key = await token_manager.has_api_key()
            navigate_to("/chat" if has_key else "/login")
            return

        page.update()

    # ── View Pop Handler (Back navigation) ──────────────────────────
    def view_pop(e: ft.ViewPopEvent):
        if len(page.views) > 1:
            page.views.pop()
            top = page.views[-1]
            page.route = top.route
            page.update()

    # ── Register Handlers ───────────────────────────────────────────
    page.on_route_change = route_change
    page.on_view_pop = view_pop

    # ── Initial Route ───────────────────────────────────────────────
    has_key = await token_manager.has_api_key()
    if has_key:
        page.route = "/chat"
    else:
        page.route = "/login"

    # Trigger initial route change
    await route_change()


# ── Entry Point ─────────────────────────────────────────────────────
if __name__ == "__main__":
    ft.run(main)
