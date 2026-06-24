# AntiGravity - test_resume.py - owned by Dev 2 (Backend)
import io
import pytest
import fitz
import sqlite3
from docx import Document
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

from main import app
from services.parser import extract_pdf_text, extract_docx_text, extract_resume_text
from db.database import DB_PATH, init_db

client = TestClient(app)

def create_mock_pdf(text: str) -> bytes:
    doc = fitz.open()
    page = doc.new_page(width=3000, height=1000)
    rect = fitz.Rect(50, 50, 2950, 950)
    page.insert_textbox(rect, text)
    pdf_bytes = doc.write()
    doc.close()
    return pdf_bytes

def create_mock_docx(text: str) -> bytes:
    doc = Document()
    doc.add_paragraph(text)
    stream = io.BytesIO()
    doc.save(stream)
    return stream.getvalue()

@pytest.fixture(autouse=True)
def clean_db():
    init_db()
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("DELETE FROM candidates")
        conn.commit()
    finally:
        conn.close()
    yield
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("DELETE FROM candidates")
        conn.commit()
    finally:
        conn.close()

# Test parser services
def test_extract_pdf_text_success():
    text = "This is a valid PDF text that should easily exceed the limit of one hundred characters required by the validator check."
    pdf_bytes = create_mock_pdf(text)
    extracted = extract_pdf_text(pdf_bytes)
    assert text in extracted

def test_extract_pdf_text_too_short():
    pdf_bytes = create_mock_pdf("Too short")
    with pytest.raises(ValueError, match="under 100 characters"):
        extract_pdf_text(pdf_bytes)

def test_extract_docx_text_success():
    text = "This is a valid Word document text that should easily exceed the limit of one hundred characters required by the validator check."
    docx_bytes = create_mock_docx(text)
    extracted = extract_docx_text(docx_bytes)
    assert text in extracted

def test_extract_docx_text_too_short():
    docx_bytes = create_mock_docx("Too short")
    with pytest.raises(ValueError, match="under 100 characters"):
        extract_docx_text(docx_bytes)

def test_extract_resume_text_routing():
    pdf_text = "This is a PDF text routed correctly by the extractor. It must be at least one hundred characters long to pass validation."
    pdf_bytes = create_mock_pdf(pdf_text)
    assert pdf_text in extract_resume_text("resume.pdf", pdf_bytes)

    docx_text = "This is a DOCX text routed correctly by the extractor. It must be at least one hundred characters long to pass validation."
    docx_bytes = create_mock_docx(docx_text)
    assert docx_text in extract_resume_text("resume.docx", docx_bytes)

    with pytest.raises(ValueError, match="Unsupported file format"):
        extract_resume_text("resume.txt", b"some bytes")

# Test endpoints
@patch("routers.resume.extract_profile", new_callable=AsyncMock)
def test_upload_resume_pdf_success(mock_extract):
    mock_extract.return_value = {
        "name": "Jane Doe",
        "email": "jane.doe@example.com",
        "current_role": "Backend Engineer",
        "years_of_experience": 5,
        "skills": [
            {"name": "Python", "years": 4.0, "proficiency": "advanced"},
            {"name": "FastAPI", "years": 2.0, "proficiency": "intermediate"}
        ],
        "projects": [
            {
                "name": "Awesome Project",
                "description": "Building cool things.",
                "technologies": ["Python", "FastAPI"],
                "role": "Architect"
            }
        ],
        "education": ["BS CS"],
        "previous_roles": ["Dev"]
    }
    
    text = "Jane Doe's resume. This text is long enough to meet the validator constraints and should definitely be more than one hundred characters long."
    pdf_bytes = create_mock_pdf(text)
    
    response = client.post(
        "/api/upload-resume",
        files={"file": ("resume.pdf", pdf_bytes, "application/pdf")}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "candidate_id" in data
    assert data["name"] == "Jane Doe"
    assert data["skills_count"] == 2

    # Verify database insertion
    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT name, email, years_of_experience FROM candidates WHERE id = ?", (data["candidate_id"],))
        row = cursor.fetchone()
        assert row is not None
        assert row[0] == "Jane Doe"
        assert row[1] == "jane.doe@example.com"
        assert row[2] == 5
    finally:
        conn.close()

@patch("routers.resume.extract_profile", new_callable=AsyncMock)
def test_upload_resume_docx_success(mock_extract):
    mock_extract.return_value = {
        "name": "John Smith",
        "email": "john.smith@example.com",
        "current_role": "Software Developer",
        "years_of_experience": 3,
        "skills": [
            {"name": "Java", "years": 3.0, "proficiency": "intermediate"}
        ],
        "projects": [],
        "education": [],
        "previous_roles": []
    }
    
    text = "John Smith's resume. This text is long enough to meet the validator constraints and should definitely be more than one hundred characters long."
    docx_bytes = create_mock_docx(text)
    
    response = client.post(
        "/api/upload-resume",
        files={"file": ("resume.docx", docx_bytes, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "candidate_id" in data
    assert data["name"] == "John Smith"
    assert data["skills_count"] == 1

def test_upload_resume_unsupported_format():
    response = client.post(
        "/api/upload-resume",
        files={"file": ("resume.txt", b"plain text content is not supported", "text/plain")}
    )
    assert response.status_code == 422
    assert "Unsupported file format" in response.json()["detail"]

def test_upload_resume_too_short():
    pdf_bytes = create_mock_pdf("Too short text")
    response = client.post(
        "/api/upload-resume",
        files={"file": ("resume.pdf", pdf_bytes, "application/pdf")}
    )
    assert response.status_code == 422
    assert "under 100 characters" in response.json()["detail"]

@patch("routers.resume.extract_profile", new_callable=AsyncMock)
def test_upload_resume_ai_throws_exception(mock_extract):
    mock_extract.side_effect = Exception("AI API Error")
    
    text = "Resume text. This text is long enough to meet the validator constraints and should definitely be more than one hundred characters long."
    pdf_bytes = create_mock_pdf(text)
    
    response = client.post(
        "/api/upload-resume",
        files={"file": ("resume.pdf", pdf_bytes, "application/pdf")}
    )
    
    assert response.status_code == 500
    assert response.json()["detail"] == "Resume parsing failed"

@patch("routers.resume.extract_profile", new_callable=AsyncMock)
def test_upload_resume_validation_fails(mock_extract):
    mock_extract.return_value = {
        "name": "Invalid Candidate",
        "email": "invalid@example.com",
        "skills": []
    }
    
    text = "Candidate resume text. This text is long enough to meet the validator constraints and should definitely be more than one hundred characters long."
    pdf_bytes = create_mock_pdf(text)
    
    response = client.post(
        "/api/upload-resume",
        files={"file": ("resume.pdf", pdf_bytes, "application/pdf")}
    )
    
    assert response.status_code == 422
    assert "validation failed" in response.json()["detail"]
