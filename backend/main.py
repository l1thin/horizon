# Horizon - main.py - owned by Dev 2 (Backend)
# AI functions are imported from the ai/ package at project root:
# from ai.prompts import extract_profile, generate_questions, evaluate_all_answers
# Do NOT implement any Claude API logic in backend/ files.

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers.resume import router as resume_router
from routers.sessions import router as sessions_router
from routers.ws import router as ws_router
from routers.code import router as code_router
from routers.report import router as report_router

app = FastAPI(
    title="Horizon Backend",
    description="Backend API for Horizon Application",
    version="1.0.0"
)

# Configure CORS for GitHub Pages and local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for GitHub Pages compatibility
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routers
app.include_router(resume_router)
app.include_router(sessions_router)
app.include_router(ws_router)
app.include_router(code_router)
app.include_router(report_router)

@app.get("/")
async def root():
    return {"message": "Welcome to Horizon API"}
