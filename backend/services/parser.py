# AntiGravity - parser.py - owned by Dev 2 (Backend)
import fitz
import io
from docx import Document

def extract_pdf_text(file_bytes: bytes) -> str:
    """
    Extracts text from PDF bytes stream using PyMuPDF (fitz).
    Joins all page text outputs with a newline.
    Raises ValueError if extracted text is under 100 characters.
    """
    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
    except Exception as e:
        raise ValueError(f"Failed to parse PDF file: {str(e)}")

    try:
        pages_text = []
        for page in doc:
            pages_text.append(page.get_text())
        text = "\n".join(pages_text)
    finally:
        doc.close()

    if len(text.strip()) < 100:
        raise ValueError("Extracted text is under 100 characters (likely a scanned image PDF).")
    
    return text

def extract_docx_text(file_bytes: bytes) -> str:
    """
    Extracts text from DOCX bytes stream using python-docx.
    Joins paragraph texts, skipping empty paragraphs.
    Raises ValueError if extracted text is under 100 characters.
    """
    try:
        doc = Document(io.BytesIO(file_bytes))
    except Exception as e:
        raise ValueError(f"Failed to parse DOCX file: {str(e)}")

    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    text = "\n".join(paragraphs)

    if len(text.strip()) < 100:
        raise ValueError("Extracted text is under 100 characters.")
    
    return text

def extract_resume_text(filename: str, file_bytes: bytes) -> str:
    """
    Routes parsing to appropriate extractor based on file extension.
    Raises ValueError if format is unsupported.
    """
    lower_filename = filename.lower()
    if lower_filename.endswith(".pdf"):
        return extract_pdf_text(file_bytes)
    elif lower_filename.endswith(".docx"):
        return extract_docx_text(file_bytes)
    else:
        raise ValueError(f"Unsupported file format: {filename}. Only PDF and DOCX files are supported.")
