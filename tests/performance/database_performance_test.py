# AsyncPG performance test for database queries
import asyncio
import asyncpg
import time

async def run_query(pool, query, params=None):
    async with pool.acquire() as conn:
        start = time.time()
        await conn.fetch(query, * (params or []))
        return time.time() - start

async def main():
    # Adjust connection details as needed for test environment
    pool = await asyncpg.create_pool(dsn="postgresql://postgres:postgres@localhost:5432/krai", min_size=1, max_size=10)
    queries = [
        "SELECT * FROM krai_intelligence.chunks LIMIT 1000;",
        "SELECT COUNT(*) FROM krai_core.products;",
        "SELECT * FROM krai_core.manufacturers WHERE id = $1;",
    ]
    for q in queries:
        durations = []
        for _ in range(20):
            dur = await run_query(pool, q)
            durations.append(dur)
        avg = sum(durations) / len(durations)
        print(f"Query: {q[:30]}... Avg time: {avg:.4f}s")
    await pool.close()

if __name__ == "__main__":
    asyncio.run(main())
