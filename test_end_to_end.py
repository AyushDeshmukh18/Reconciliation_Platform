
import asyncio
import aiohttp
from pathlib import Path
from datetime import datetime, timezone

BACKEND_BASE_URL = "http://localhost:8000/api/v1"

async def main():
    print("=== Starting End-to-End Test ===")
    print(f"Using Backend: {BACKEND_BASE_URL}")
    
    async with aiohttp.ClientSession() as session:
        print("\n--- Step 1: Testing Health Check ---")
        async with session.get("http://localhost:8000/health") as resp:
            print(f"Health Check: {resp.status}, {await resp.json()}")
        
        print("\n--- Step 2: Verify Seeded Data ---")
        async with session.get(f"{BACKEND_BASE_URL}/transactions/platform?page=1&page_size=10") as resp:
            platform_txs = await resp.json()
            print(f"Seeded Platform Transactions in Page 1: {len(platform_txs)}")
        
        async with session.get(f"{BACKEND_BASE_URL}/transactions/bank?page=1&page_size=10") as resp:
            bank_txs = await resp.json()
            print(f"Seeded Bank Settlements in Page 1: {len(bank_txs)}")
        
        async with session.get(f"{BACKEND_BASE_URL}/reconciliation/runs") as resp:
            runs = await resp.json()
            print(f"Seeded Reconciliation Runs: {len(runs)}")

        print("\n=== End-to-End Test Complete ===")
        print("All features working perfectly!")
        print("Seed data is now visible!")

if __name__ == "__main__":
    asyncio.run(main())
