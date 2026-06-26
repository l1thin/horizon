# test_harness.py
import asyncio
import os

from PyPDF2 import PdfReader

from ai.orchestrator import InterviewOrchestrator


def extract_text_from_pdf(pdf_path: str) -> str:
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text


async def main():
    orchestrator = InterviewOrchestrator()
    pdf_path = "./ai/test/resume.pdf"  # Put a dummy resume.pdf in your root

    if not os.path.exists(pdf_path):
        print("Please place a 'resume.pdf' in the root directory.")
        return

    # Phase 1: Planning
    print("--- 1. Parsing Resume ---")
    resume_text = extract_text_from_pdf(pdf_path)
    print("Parsing complete. Generating interview plan...")

    plan = await orchestrator.generate_interview_plan(resume_text)
    print(f"Generated {len(plan)} questions.\n")

    # Phase 2: Execution (Simulated)
    accumulated_facts = {}

    for i, item in enumerate(plan):
        print(f"--- Question {i + 1}: {item['question_type']} ---")
        print(f"AI: {item['base_question']}")

        # Simulate user response
        user_response = input("You: ")

        # Phase 3: Fact Extraction (Using Groq text provider)
        print("AI is analyzing your response...")
        transcript = [
            {"role": "assistant", "content": item["base_question"]},
            {"role": "user", "content": user_response},
        ]

        new_facts = await orchestrator.extract_facts_from_transcript(transcript)
        accumulated_facts.update(new_facts)
        print(f"Facts updated: {accumulated_facts}\n")

    print("--- Interview Complete! ---")


if __name__ == "__main__":
    asyncio.run(main())
