import pytest
from unittest.mock import MagicMock
from src.services.audio import AudioService
from src.services.camera import CameraService
from src.services.file_picker import FilePickerService
from src.services.share import ShareService

def test_audio_service_init(mock_page):
    service = AudioService(mock_page)
    assert service is not None

def test_file_picker_service_init(mock_page):
    service = FilePickerService(mock_page, lambda x, y, z: None)
    assert service is not None

def test_camera_service_init(mock_page):
    service = CameraService(mock_page)
    assert service is not None

def test_share_service_init(mock_page):
    service = ShareService(mock_page)
    assert service is not None

@pytest.mark.asyncio
async def test_share_copy(mock_page):
    service = ShareService(mock_page)
    await service.copy_text("test")
    mock_page.clipboard.set.assert_called_with("test")
