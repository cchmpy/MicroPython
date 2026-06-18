import asyncio
class AsyncCounter:
    def __init__(self, stop):
        self._stop = stop
        self._current = 0    
    def __aiter__(self):
        return self    
    async def __anext__(self):              # 注意这里返回的是协程对象(awaitable)
        if self._current < self._stop:
            await asyncio.sleep(1)          # 模拟异步操作
            self._current += 1
            return self._current - 1
        else:
            raise StopAsyncIteration

async def main():
    async for number in AsyncCounter(3):
        print(number)
asyncio.run(main())
