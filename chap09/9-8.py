import asyncio
event = asyncio.Event()
async def waiter(name):
    print(f'任务{name}等待事件...')
    await event.wait()                   # 阻塞直到事件被set()
    print(f'任务{name}收到设置事件信号!')

async def trigger():
    await asyncio.sleep(2)               # 模拟准备时间
    print('现在设置事件...')
    event.set()                          # 触发事件，唤醒所有等待的任务

async def main():
    await asyncio.gather(waiter('A'),waiter('B'),trigger())
asyncio.run(main())