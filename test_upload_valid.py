import fitz
import httpx
import asyncio

async def test():
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "This is a dummy resume with enough text. " * 50)
    pdf_bytes = doc.write()
    doc.close()
    
    async with httpx.AsyncClient() as client:
        files = {'file': ('resume.pdf', pdf_bytes, 'application/pdf')}
        resp = await client.post('http://localhost:8000/api/upload-resume', files=files)
        print("Status:", resp.status_code)
        print("Body:", resp.text)

if __name__ == "__main__":
    asyncio.run(test())
