# Horizon - logger.py - owned by Dev 3 (AI + Infra)
#
# Logs all Claude I/O to the database for debugging and cost tracking.
# Uses asyncpg to write to Supabase. Never raises — silent on failure.

import asyncpg
import os
import json
from datetime import datetime, timezone


# SQL to create this table (run once in Supabase):
# CREATE TABLE ai_logs (
#   id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
#   function_name TEXT,
#   input_json JSONB,
#   output_json JSONB,
#   error TEXT,
#   called_at TIMESTAMPTZ DEFAULT NOW()
# );


async def log_ai_call(
    function_name: str,
    input_data: dict,
    output_data: dict,
    error: str = None,
):
    """Logs all Claude I/O for debugging. Never raises — silent on failure."""
    try:
        conn = await asyncpg.connect(os.environ["SUPABASE_URL"])
        await conn.execute(
            "INSERT INTO ai_logs (function_name, input_json, output_json, error) VALUES ($1, $2, $3, $4)",
            function_name,
            json.dumps(input_data),
            json.dumps(output_data),
            error,
        )
        await conn.close()
    except Exception as e:
        print(f"[Horizon] ai_logger failed silently: {e}")
