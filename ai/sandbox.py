import contextlib
import io
import textwrap  # <-- Import this
import traceback


class LocalPythonRunner:
    @staticmethod
    async def run_code(language: str, code: str):
        if language != "python":
            return {"success": False, "output": "Only Python is supported locally."}

        # FIX: Deduplicate indentation so exec doesn't get confused
        cleaned_code = textwrap.dedent(code)

        buffer = io.StringIO()
        try:
            with contextlib.redirect_stdout(buffer):
                # We use a clean dictionary for locals/globals
                exec(cleaned_code, {"__builtins__": __builtins__}, {})
            return {"success": True, "output": buffer.getvalue()}
        except Exception:
            return {"success": False, "output": traceback.format_exc()}
