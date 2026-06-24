-- AntiGravity - schema.sql - owned by Dev 2 (Backend)
CREATE TABLE IF NOT EXISTS candidates (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT,
    current_role TEXT,
    years_of_experience INTEGER,
    skills TEXT,           -- JSON array of SkillEntry
    projects TEXT,         -- JSON array of ProjectEntry
    education TEXT,        -- JSON list
    previous_roles TEXT    -- JSON list
);
