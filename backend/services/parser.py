# Horizon - parser.py - owned by Dev 2 (Backend)
import io
import fitz  # PyMuPDF
from docx import Document

def extract_pdf_text(file_bytes: bytes) -> str:
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    text = "\n".join([page.get_text() for page in doc])
    if len(text) < 100:
        raise ValueError("Resume too short to parse")
    return text

def extract_docx_text(file_bytes: bytes) -> str:
    doc = Document(io.BytesIO(file_bytes))
    text = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
    if len(text) < 100:
        raise ValueError("Resume too short to parse")
    return text

def extract_resume_text(filename: str, file_bytes: bytes) -> str:
    ext = filename.lower().split('.')[-1]
    if ext == 'pdf':
        return extract_pdf_text(file_bytes)
    elif ext == 'docx':
        return extract_docx_text(file_bytes)
    else:
        raise ValueError("Unsupported file type. Please upload PDF or DOCX.")
