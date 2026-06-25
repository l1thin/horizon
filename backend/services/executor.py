# Horizon - executor.py - owned by Dev 2 (Backend)
import os
import asyncio
import httpx

LANGUAGE_IDS = {"python": 71, "javascript": 63, "java": 62, "cpp": 54}

async def run_on_judge0(code: str, language: str, stdin: str = "") -> dict:
    api_key = os.getenv("JUDGE0_KEY")
    if not api_key:
        return {"status_description": "Executor not configured", "passed": False}
        
    url = "https://judge0-ce.p.rapidapi.com/submissions"
    headers = {
        "content-type": "application/json",
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": "judge0-ce.p.rapidapi.com"
    }
    
    payload = {
        "source_code": code,
        "language_id": LANGUAGE_IDS[language],
        "stdin": stdin
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload, headers=headers)
            if response.status_code != 201:
                return {"status_description": f"Failed to submit code: {response.text}", "passed": False}
                
            token = response.json().get("token")
            if not token:
                return {"status_description": "Failed to get submission token", "passed": False}
                
            poll_url = f"{url}/{token}?base64_encoded=false"
            for _ in range(12):
                await asyncio.sleep(1.5)
                poll_resp = await client.get(poll_url, headers=headers)
                if poll_resp.status_code == 200:
                    result = poll_resp.json()
                    status_id = result.get("status", {}).get("id", 0)
                    if status_id > 2: # 1=queued, 2=processing
                        passed = status_id == 3 and not result.get("stderr")
                        return {
                            "stdout": result.get("stdout"),
                            "stderr": result.get("stderr"),
                            "status_description": result.get("status", {}).get("description"),
                            "passed": passed
                        }
                        
            return {"status_description": "Timeout", "passed": False}
        except Exception as e:
            return {"status_description": f"Error: {str(e)}", "passed": False}
