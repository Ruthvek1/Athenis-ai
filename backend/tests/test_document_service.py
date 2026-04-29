import pytest
from backend.services.document_service import DocumentService

def test_chunk_text():
    # Arrange
    text = "This is a very long text that we need to chunk. " * 50
    chunk_size = 100
    overlap = 20
    
    # Act
    chunks = DocumentService.chunk_text(text, chunk_size, overlap)
    
    # Assert
    assert len(chunks) > 1
    # Check that chunks are within size limits (roughly)
    for chunk in chunks:
        assert len(chunk) <= chunk_size + 50  # Allow some leeway for clean breaks
        
def test_extract_text_txt():
    # Arrange
    file_bytes = b"Hello world! This is a test file."
    
    # Act
    text = DocumentService.extract_text(file_bytes, "txt")
    
    # Assert
    assert "Hello world!" in text
