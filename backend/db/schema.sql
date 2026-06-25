-- Horizon - schema.sql - owned by Dev 2 (Backend)
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE IF NOT EXISTS candidates (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID,
  resume_text TEXT,
  profile_json JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS sessions (
  id UUID PRIMARY KEY,
  status TEXT DEFAULT 'processing',   -- processing | ready | active | complete | error
  preferred_language TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS questions (
  id TEXT PRIMARY KEY,
  session_id UUID REFERENCES sessions(id),
  type TEXT,              -- technical | behavioral | coding | follow_up
  text TEXT,
  criteria JSONB,
  follow_up TEXT,
  time_limit_seconds INT,
  question_index INT
);

CREATE TABLE IF NOT EXISTS answers (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  question_id TEXT REFERENCES questions(id),
  session_id UUID REFERENCES sessions(id),
  transcript TEXT,
  code TEXT,
  language TEXT,
  timed_out BOOLEAN DEFAULT FALSE,
  integrity_json JSONB,
  score FLOAT,
  feedback_json JSONB,
  depth_rating TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS reports (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID REFERENCES sessions(id),
  overall_score FLOAT,
  gap_analysis_json JSONB,
  integrity_json JSONB,
  full_report_json JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ai_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  function_name TEXT,
  input_json JSONB,
  output_json JSONB,
  error TEXT,
  called_at TIMESTAMPTZ DEFAULT NOW()
);
