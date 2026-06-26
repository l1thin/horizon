import httpx


class PistonExecutor:
    PISTON_API_URL = "https://emkc.org/api/v2/piston/execute"

    @classmethod
    async def run_code(cls, language: str, full_code: str) -> dict:
        payload = {
            "language": language,
            "version": "*",
            "files": [{"content": full_code}],
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    cls.PISTON_API_URL, json=payload, timeout=10.0
                )
                response.raise_for_status()
                data = response.json()

                run_result = data.get("run", {})
                stdout = run_result.get("stdout", "")
                stderr = run_result.get("stderr", "")

                is_success = "ALL TESTS PASSED" in stdout and not stderr

                return {
                    "success": is_success,
                    "output": stdout if is_success else (stderr or stdout),
                    "language": data.get("language", language),
                }
            except httpx.HTTPError as e:
                print(f"[PISTON API ERROR] {e}")
                return {"success": False, "output": "Execution Engine Unavailable.", "error": f"{e}"}
