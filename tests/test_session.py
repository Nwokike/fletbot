import pytest
import tempfile
import shutil
from pathlib import Path
from src.session.manager import SessionManager

@pytest.fixture
def temp_storage():
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

def test_create_session(temp_storage):
    sm = SessionManager(storage_dir=temp_storage)
    session = sm.create_session()
    assert session.id is not None
    assert Path(temp_storage).joinpath(f"session_{session.id}.json").exists()

def test_save_and_get(temp_storage):
    sm = SessionManager(storage_dir=temp_storage)
    session = sm.create_session()
    session.add_message("user", "Hello AI")
    sm.save(session)
    
    loaded = sm.get_session(session.id)
    assert loaded.messages[0].content == "Hello AI"
    assert loaded.title == "Hello AI"

def test_list_sessions(temp_storage):
    sm = SessionManager(storage_dir=temp_storage)
    sm.create_session()
    sm.create_session()
    
    sessions = sm.list_sessions()
    assert len(sessions) == 2

def test_delete_session(temp_storage):
    sm = SessionManager(storage_dir=temp_storage)
    session = sm.create_session()
    sm.delete_session(session.id)
    assert sm.get_session(session.id) is None
