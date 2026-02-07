import io
from pypdf import PdfReader
from docx import Document as DocxDocument
import logging

logger = logging.getLogger(__name__)

class DocumentService:
    @staticmethod
    def extract_text(file_bytes: bytes, file_type: str) -> str:
        text = ""
        try:
            if file_type == "pdf":
                reader = PdfReader(io.BytesIO(file_bytes))
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n\n"
            elif file_type == "docx":
                doc = DocxDocument(io.BytesIO(file_bytes))
                for para in doc.paragraphs:
                    text += para.text + "\n"
            elif file_type in ["txt", "md"]:
                text = file_bytes.decode("utf-8")
            else:
                raise ValueError(f"Unsupported file type: {file_type}")
        except Exception as e:
            logger.error(f"Error extracting text from {file_type}: {e}")
            raise
        return text

    @staticmethod
    def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> list[str]:
        """
        Manually chunk text into smaller pieces with overlap.
        """
        chunks = []
        start = 0
        text_length = len(text)

        while start < text_length:
            end = start + chunk_size
            
            # If we're not at the end of the text, try to find a nice breaking point (newline or space)
            if end < text_length:
                # Look back for a newline character within the last 100 characters of the chunk
                last_newline = text.rfind("\n", max(start, end - 100), end)
                if last_newline != -1:
                    end = last_newline + 1
                else:
                    # Look back for a space
                    last_space = text.rfind(" ", max(start, end - 50), end)
                    if last_space != -1:
                        end = last_space + 1
                        
            chunks.append(text[start:end].strip())
            start = end - overlap
            
            # Prevent infinite loop if overlap is somehow >= chunk advance
            if start <= start - overlap + (end - start):
                start = end - overlap if end - overlap > start else start + 1

        return [c for c in chunks if c]
