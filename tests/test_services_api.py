import unittest
from unittest.mock import MagicMock
import flet as ft
from src.services.audio import AudioService
from src.services.camera import CameraService
from src.services.file_picker import FilePickerService
from src.services import PermissionService
from src.auth.token_manager import TokenManager

class TestServicesAPI(unittest.TestCase):
    def setUp(self):
        # Mock the page object
        self.page = MagicMock(spec=ft.Page)
        self.page.overlay = []

    def test_audio_service_init(self):
        service = AudioService(self.page)
        self.assertIsNotNone(service)
        # Check if overlay is NOT used for recorder (service)
        self.assertEqual(len(self.page.overlay), 0)

    def test_file_picker_service_init(self):
        service = FilePickerService(self.page, lambda x, y, z: None)
        self.assertIsNotNone(service)
        # Check if overlay is NOT used
        self.assertEqual(len(self.page.overlay), 0)

    def test_token_manager_init(self):
        tm = TokenManager(self.page)
        self.assertIsNotNone(tm)
        self.assertTrue(hasattr(tm, '_prefs'))
        self.assertIsInstance(tm._prefs, ft.SharedPreferences)

    def test_camera_service_init(self):
        service = CameraService(self.page)
        self.assertIsNotNone(service)

    def test_permission_service_init(self):
        service = PermissionService(self.page)
        self.assertIsNotNone(service)
        self.assertEqual(len(self.page.overlay), 0)

if __name__ == '__main__':
    unittest.main()
