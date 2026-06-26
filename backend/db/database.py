# Horizon - database.py - owned by Dev 2 (Backend)
import os
import asyncpg

_pool = None

async def init_db():
    global _pool
    if _pool is None:
        db_url = os.getenv("SUPABASE_URL")
        if not db_url:
            raise ValueError("SUPABASE_URL environment variable is not set")
            
        _pool = await asyncpg.create_pool(
            db_url,
            min_size=2,
            max_size=10
        )
        
        # Read and execute schema.sql on startup
        schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
        with open(schema_path, "r") as f:
            schema_sql = f.read()
        
        async with _pool.acquire() as conn:
            await conn.execute(schema_sql)

async def close_db():
    global _pool
    if _pool:
        await _pool.close()
        _pool = None

async def get_db():
    if _pool is None:
        await init_db()
    async with _pool.acquire() as conn:
        yield conn

# Helper functions to directly execute queries
async def execute(query: str, *args):
    if _pool is None:
        await init_db()
    async with _pool.acquire() as conn:
        return await conn.execute(query, *args)

async def fetch(query: str, *args):
    if _pool is None:
        await init_db()
    async with _pool.acquire() as conn:
        return await conn.fetch(query, *args)

async def fetchrow(query: str, *args):
    if _pool is None:
        await init_db()
    async with _pool.acquire() as conn:
        return await conn.fetchrow(query, *args)
