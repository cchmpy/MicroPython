import asyncio
from machine import Timer
async def bridge():                 # 桥接器协程
    while True:
        await tsf.wait()            # 等待TSF被ISR触发
        if not event.is_set(): 
            event.set()             # 触发Event，广播唤醒所有等待的任务
            
async def task1():
    while True:
        await event.wait()          # 等待Event触发
        print("Task1收到通知")
        if event.is_set(): event.clear()

async def task2():
    while True:
        await event.wait()
        print("Task2收到通知")
        if event.is_set(): event.clear()
        
async def main():
    global tsf,event,n
    tsf = asyncio.ThreadSafeFlag()  # 用于ISR安全触发
    event = asyncio.Event()         # 用于广播唤醒多个任务
    n = 0
    
    asyncio.create_task(bridge())   # 创建桥接协程    
    asyncio.create_task(task1())
    asyncio.create_task(task2())  
    
    timer=Timer(0,period=2000, mode=Timer.PERIODIC, callback=lambda _ : tsf.set())    
    while True:
        await asyncio.sleep(1)        
        if (n:=n+1)==10:            # 结束所有协程
            timer.deinit()
            break

asyncio.run(main())