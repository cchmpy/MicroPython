import asyncio
lock = asyncio.Lock()
n = 0                          # 共享全局变量
async def foo(name):
    global n
    async with lock:
        print(f'任务{name}获得锁')
        n += 1
        await asyncio.sleep(1)  # 模拟耗时操作
        print(f'任务{name}释放锁lock,n={n}')

async def main():
    await asyncio.gather(foo('A'),foo('B'))
asyncio.run(main())