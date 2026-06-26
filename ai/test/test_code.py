import asyncio
import json

from ai.orchestrator import InterviewOrchestrator
from ai.piston import PistonExecutor
from ai.sandbox import LocalPythonRunner


async def run_e2e_code_generation_test():
    print("--- 🤖 E2E DYNAMIC CODING PIPELINE TEST ---")
    orchestrator = InterviewOrchestrator()

    # 1. Define a Mock Candidate
    dummy_skills = ["Python", "Algorithms", "Optimization"]
    print(f"👤 Mocking Candidate skills: {dummy_skills}\n")

    # 2. Test Generator: Does it make a valid problem?
    print("🧠 1. AI generating a coding challenge...")
    challenge = await orchestrator.generate_coding_challenge(dummy_skills)
    question_text = challenge.get("base_question", "")

    print(f"\n[AI Challenge]: {challenge.get('title')}")
    print(f"[Problem]: {question_text}\n")

    # 3. Test Test-Generator: Does AI write executable Python assertions?
    print("🧪 2. AI generating hidden test cases...")
    ai_generated_tests = await orchestrator._generate_dynamic_tests(question_text)

    print(f"\n[Generated Test Suite]:\n{ai_generated_tests}\n")

    # 4. Test Orchestrator Logic: Does it grade the code?
    # We will simulate a 'perfect' candidate submission
    mock_solution = "def solve(nums, target):\n    # Simple O(n^2) approach\n    for i in range(len(nums)):\n        for j in range(i + 1, len(nums)):\n            if nums[i] + nums[j] == target:\n                return [i, j]\n    return []"

    # Combine code + tests
    full_execution_code = (
        f"{mock_solution}\n\n# --- AI GENERATED TESTS ---\n{ai_generated_tests}"
    )

    print("🚀 3. Sending to Piston Sandbox...")
    piston_result = await LocalPythonRunner.run_code("python", full_execution_code)

    print(f"\n[Piston Success]: {piston_result.get('success')}")
    print(f"[Piston Output]: {piston_result.get('output')}")

    # 5. Test Evaluator: Does the AI grade the performance?
    print("\n🧐 4. AI reviewing code quality and complexity...")
    review = await orchestrator.evaluate_code_submission(
        question_text=question_text,
        source_code=mock_solution,
        transcript_history=[{"role": "user", "content": "I'm using a nested loop."}],
        language="python",
    )

    print("\n--- FINAL SCORECARD ---")
    print(json.dumps(review, indent=2))


if __name__ == "__main__":
    asyncio.run(run_e2e_code_generation_test())
