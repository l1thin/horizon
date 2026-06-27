# Horizon - executor.py - owned by Dev 2 (Backend)
import os

try:
    from ai.sandbox import LocalPythonRunner
except ImportError:
    pass

try:
    from ai.piston import PistonExecutor
except ImportError:
    pass

# Piston language aliases
SUPPORTED_LANGUAGES = {
    "python": "python", 
    "javascript": "javascript", 
    "java": "java", 
    "cpp": "c++"
}

async def execute_code(code: str, language: str, stdin: str = "") -> dict:
    # Normalize language
    lang = SUPPORTED_LANGUAGES.get(language)
    if not lang:
        return {"status_description": "Unsupported language", "passed": False, "stdout": "", "stderr": ""}

    if lang == "python":
        # Use local python runner (fast, secure via sandbox, no network)
        try:
            result = await LocalPythonRunner.run_code("python", code)
            success = result.get("success", False)
            output = result.get("output", "")
            
            return {
                "stdout": output if success else "",
                "stderr": output if not success else "",
                "status_description": "Accepted" if success else "Runtime Error",
                "passed": success
            }
        except Exception as e:
            return {"status_description": f"Local Executor Error: {str(e)}", "passed": False, "stdout": "", "stderr": str(e)}
    else:
        # Fallback to piston
        try:
            result = await PistonExecutor.run_code(lang, code)
            success = result.get("success", False)
            output = result.get("output", "")
            
            return {
                "stdout": output if success else "",
                "stderr": output if not success else "",
                "status_description": "Accepted" if success else "Runtime Error",
                "passed": success
            }
        except Exception as e:
            return {"status_description": f"Piston Error: {str(e)}", "passed": False, "stdout": "", "stderr": str(e)}
