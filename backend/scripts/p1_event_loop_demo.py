"""Demonstrate that a SYNCHRONOUS call inside an async endpoint blocks the
event loop (serializes concurrent requests), vs the same work off-loaded via
asyncio.to_thread (concurrent).

This simulates what firebase_admin.auth.verify_id_token does in production:
a blocking network call (here modeled with time.sleep). It proves the P1-1
fix (to_thread) restores concurrency without weakening verification.

Not imported by the app; run directly:
    python scripts/p1_event_loop_demo.py
"""
import asyncio
import time


async def blocking_verify():
    # Models the sync firebase_admin call: blocks the running thread.
    time.sleep(0.2)
    return {"uid": "x"}


async def threaded_verify():
    return await asyncio.to_thread(lambda: (time.sleep(0.2), {"uid": "x"})[1])


async def bench(name, verify):
    t0 = time.perf_counter()
    await asyncio.gather(*[verify() for _ in range(6)])
    wall = (time.perf_counter() - t0) * 1000
    print(f"  {name}: 6 concurrent verify -> wall {wall:.1f} ms")
    return wall


async def main():
    print("If verify() runs blocking on the event loop, 6x0.2s -> ~1200ms (serialized).")
    print("If verify() runs via asyncio.to_thread, 6x0.2s -> ~200ms (concurrent).")
    await bench("blocking (current prod behavior)", blocking_verify)
    await bench("threaded (P1-1 fix)", threaded_verify)


asyncio.run(main())
