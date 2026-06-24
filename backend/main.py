# AntiGravity - main.py - owned by Dev 2 (Backend)
from fastapi import FastAPI
from routers.resume import router as resume_router

app = FastAPI(
    title="AntiGravity Backend",
    description="Resume Upload & Parsing API",
    version="1.0.0"
)

# Include resume router
app.include_router(resume_router)

@app.get("/")
async def root():
    return {"message": "Welcome to AntiGravity API"}
