import httpx
import asyncio

async def test_upload():
    async with httpx.AsyncClient() as client:
        with open("dummy.pdf", "wb") as f:
            f.write(b"Hello world! This is a dummy pdf with enough text so it passes the length check. " * 10)
        with open("dummy.pdf", "rb") as f:
            files = {'file': ('dummy.pdf', f, 'application/pdf')}
            response = await client.post('http://localhost:8000/api/upload-resume', files=files)
            print(response.status_code)
            print(response.text)

if __name__ == "__main__":
    asyncio.run(test_upload())
