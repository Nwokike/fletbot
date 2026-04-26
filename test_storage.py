import flet as ft

async def main(page: ft.Page):
    prefs = ft.SharedPreferences()
    await prefs.set("test_key", "hello world")
    val = await prefs.get("test_key")
    print(f"Value from prefs: {val}")
    
    fp = ft.FilePicker()
    page.add(ft.ElevatedButton("Pick File", on_click=lambda e: fp.pick_files()))
    
ft.app(main, port=8550)
