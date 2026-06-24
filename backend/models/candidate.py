# AntiGravity - candidate.py - owned by Dev 2 (Backend)
from pydantic import BaseModel
from typing import Literal, Any

class SkillEntry(BaseModel):
    name: str
    years: float
    proficiency: Literal['beginner', 'intermediate', 'advanced']

class ProjectEntry(BaseModel):
    name: str
    description: str
    technologies: list[str]
    role: str

class CandidateProfile(BaseModel):
    name: str
    email: str
    current_role: str
    years_of_experience: int
    skills: list[SkillEntry]
    projects: list[ProjectEntry]
    education: list[Any]
    previous_roles: list[Any]
