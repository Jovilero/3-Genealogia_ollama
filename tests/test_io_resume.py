import pytest
from pathlib import Path
from src.main import get_processed_chunks

def test_get_processed_chunks_empty(tmp_path):
    assert get_processed_chunks(tmp_path) == set()

def test_get_processed_chunks_with_files(tmp_path):
    # Create mock chunk files
    (tmp_path / "api_chunk_001.txt").write_text("data")
    (tmp_path / "api_chunk_005.txt").write_text("data")
    (tmp_path / "process.log").write_text("info")
    (tmp_path / "other.txt").write_text("other")

    processed = get_processed_chunks(tmp_path)
    
    assert processed == {1, 5}
    assert 1 in processed
    assert 5 in processed
    assert 2 not in processed

def test_get_processed_chunks_wrong_format(tmp_path):
    (tmp_path / "api_chunk_abc.txt").write_text("data")
    assert get_processed_chunks(tmp_path) == set()
