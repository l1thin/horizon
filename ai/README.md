# Horizon AI Layer — Onboarding Guide

Welcome to the AI Layer of **Horizon**! 

Horizon is a voice-first AI mock interview simulator. This specific directory (`ai/`) handles all of the heavy lifting regarding Artificial Intelligence, Prompt Engineering, Embedding Generation, and Multi-Modal Audio Processing. 

If you're a backend or frontend developer reading this: **This directory is treated as an isolated microservice.** You should only ever import from `ai/__init__.py`. 

---

## 🧭 The Core Workflow
An interview lifecycle in Horizon follows these 5 steps, all powered by this codebase:

1. **Profile Extraction** (`extract_profile`): We take a candidate's messy, raw resume text and use Claude to parse it into a clean, structured JSON object (skills, experience, projects).
2. **Question Generation** (`generate_questions`): We dynamically generate 7 highly personalized interview questions based on the candidate's specific profile and target role. Every question comes with a pre-generated `follow_up` to probe specific technical claims.
3. **Live Voice Turn** (`process_voice_turn`): During the actual interview, the candidate's raw audio bytes are passed directly to our Multi-Modal Voice Providers. The AI returns conversational text and generated audio to stream back.
4. **Answer Evaluation** (`evaluate_all_answers`): After the interview concludes, we evaluate all transcripts on a strict 0–10 calibrated scale, detailing what was good, what was missing, and providing a `depth_rating`.
5. **Skill Gap Analysis** (`compute_skill_gaps` & `compute_skill_gap_vectors`): We use Vector Embeddings and Cosine Similarity to calculate the mathematical distance between what the candidate knows and what the job requires, returning the top 3 biggest skill gaps.

---

## 📂 Directory Structure

Here is what every file does:

### The Public Interface
* **`__init__.py`**: The strictly enforced public API for the backend. If a function isn't exported here, the backend isn't allowed to use it.

### The Core Logic
* **`prompts.py`**: The central brain. Contains all the massive system prompts, JSON validation logic, and the Claude API integrations for profile parsing, question generation, and post-session evaluation.
* **`embeddings.py`**: Handles mathematical vector embeddings using OpenAI or Gemini. It converts technical skills into high-dimensional vectors to calculate how "close" a candidate's skill is to a required skill (Cosine Similarity).
* **`voice_providers.py`**: A **Factory Pattern** implementation for live voice conversations. Because handling raw binary audio varies wildly across LLMs, this file routes requests to the `ClaudeVoiceProvider`, `OpenAIVoiceProvider`, or `GeminiVoiceProvider` seamlessly.
* **`logger.py`**: A silent, asynchronous database logger using `asyncpg`. Every single AI call across the application is logged directly to Supabase for debugging, cost-tracking, and quality monitoring. If the DB fails, the logger fails silently to prevent breaking the live interview.

### Testing
* **`tests/test_prompts.py` & `tests/test_embeddings.py`**: The Pytest suite. We use `unittest.mock.AsyncMock` heavily here to simulate LLM responses. You can run the entire test suite locally without needing a valid API key or spending real money.

---

## 🔀 Multi-Model Support

The AI layer is completely model-agnostic for its heaviest features (Embeddings and Voice). 

By simply changing the `.env` file, the AI layer will dynamically swap out its underlying architecture:

```env
# Change the live voice interviewer model on the fly!
LLM_PROVIDER=openai   # Uses GPT-4o Realtime Audio
# LLM_PROVIDER=gemini # Uses Gemini 1.5 Pro Multimodal
# LLM_PROVIDER=claude # Uses Claude Sonnet
```

## 🛠️ Infrastructure Context
While developing in the `ai/` folder, remember that we ship alongside the backend.
- The `Dockerfile` at the project root packages `backend/` and `ai/` together.
- `.github/workflows/deploy.yml` runs our AI tests independently before running backend tests, and then ships the unified container to Railway.
