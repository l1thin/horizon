# Horizon - executor.py - owned by Dev 2 (Backend)
import httpx

# Piston language aliases
SUPPORTED_LANGUAGES = {
    "python": "python", 
    "javascript": "javascript", 
    "java": "java", 
    "cpp": "c++"
}

async def execute_code(code: str, language: str, stdin: str = "") -> dict:
    url = "https://emkc.org/api/v2/piston/execute"
    
    piston_lang = SUPPORTED_LANGUAGES.get(language)
    if not piston_lang:
        return {"status_description": "Unsupported language", "passed": False}
    
    payload = {
        "language": piston_lang,
        "version": "*",
        "files": [
            {
                "content": code
            }
        ],
        "stdin": stdin
    }
    
    async with httpx.AsyncClient() as client:
        try:
            # We add a slight timeout because execution could take a couple seconds
            response = await client.post(url, json=payload, timeout=15.0)
            if response.status_code != 200:
                return {"status_description": f"Failed to execute code: {response.status_code}", "passed": False}
                
            result = response.json()
            
            run_result = result.get("run", {})
            compile_result = result.get("compile", {})
            
            # Check compilation first
            if compile_result and compile_result.get("code") != 0:
                return {
                    "stdout": "",
                    "stderr": compile_result.get("output", ""),
                    "status_description": "Compilation Error",
                    "passed": False
                }
                
            stderr = run_result.get("stderr", "")
            stdout = run_result.get("stdout", run_result.get("output", ""))
            
            passed = run_result.get("code") == 0 and not stderr.strip()
            
            return {
                "stdout": stdout,
                "stderr": stderr,
                "status_description": "Accepted" if passed else "Runtime Error",
                "passed": passed
            }
        except Exception as e:
            return {"status_description": f"Error: {str(e)}", "passed": False}
