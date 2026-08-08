"""P1 measurement harness: /auth/me latency (single + concurrent) and
event-loop responsiveness. Run against a running backend (mock auth)."""
import asyncio
import time

import httpx

BASE = "http://127.0.0.1:8000/api/v1"
TOKEN = "mock-test-token"
HEADERS = {"Authorization": f"Bearer {TOKEN}"}


async def one(client, label):
    t = time.perf_counter()
    r = await client.get(f"{BASE}/auth/me", headers=HEADERS)
    dt = (time.perf_counter() - t) * 1000
    print(f"  {label}: HTTP {r.status_code}  {dt:.1f} ms  {len(r.content)}B")
    return dt


async def main():
    async with httpx.AsyncClient() as client:
        await one(client, "warmup /auth/me")

        print("=== sequential /auth/me x5 ===")
        seq = [await one(client, f"seq#{i}") for i in range(5)]

        print("=== concurrent /auth/me x6 (mock auth, no real Firebase) ===")
        t0 = time.perf_counter()
        res = await asyncio.gather(*[one(client, f"con#{i}") for i in range(6)])
        wall = (time.perf_counter() - t0) * 1000
        print(f"  wall time for 6 concurrent: {wall:.1f} ms  (sum={sum(res):.1f} ms)")

        eps = [
            "/auth/me", "/profiles/me", "/profiles/me/completion",
            "/questionnaires/sessions", "/report/?limit=8",
            "/profiles/me/measurements", "/profiles/me/lab-reports",
        ]
        print("=== dashboard waterfall SEQUENTIAL ===")
        t0 = time.perf_counter()
        for ep in eps:
            tt = time.perf_counter()
            r = await client.get(f"{BASE}{ep}", headers=HEADERS)
            print(f"  {ep:35s} HTTP {r.status_code} {(time.perf_counter()-tt)*1000:6.1f} ms")
        print(f"  sequential total: {(time.perf_counter()-t0)*1000:.1f} ms")

        print("=== dashboard waterfall CONCURRENT ===")
        t0 = time.perf_counter()
        async def hit(ep):
            tt = time.perf_counter()
            r = await client.get(f"{BASE}{ep}", headers=HEADERS)
            return ep, r.status_code, (time.perf_counter()-tt)*1000
        results = await asyncio.gather(*[hit(ep) for ep in eps])
        for ep, code, ms in results:
            print(f"  {ep:35s} HTTP {code} {ms:6.1f} ms")
        print(f"  concurrent total (wall): {(time.perf_counter()-t0)*1000:.1f} ms")


asyncio.run(main())
