
import asyncio
import aiohttp
from aiohttp import FormData
from pathlib import Path

async def test_upload():
    file_path = Path("test_data/platform_sample_small.csv")
    if not file_path.exists():
        print(f"File {file_path} doesn't exist")
        return

    async with aiohttp.ClientSession() as session:
        with open(file_path, "rb") as f:
            form = FormData()
            form.add_field("file", f, filename="test.csv")

            async with session.post("http://localhost:8000/api/v1/reconciliation/ingest/platform", data=form) as resp:
                print(f"Status: {resp.status}")
                print(f"Response: {await resp.json()}")

if __name__ == "__main__":
    asyncio.run(test_upload())
