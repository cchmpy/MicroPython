import asyncio
class AsyncResource:
    async def __aenter__(self):             # 必须用 async def
        print("Entering context (async)")
        await asyncio.sleep(1)              # 模拟异步操作
        return self
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        print("Exiting context (async)")
        await asyncio.sleep(1)              # 模拟异步清理
async def main():
    async with AsyncResource() as r:        # 触发 __aenter__ 和 __aexit__
        print("Inside context")
asyncio.run(main())
