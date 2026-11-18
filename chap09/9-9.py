import asyncio
from machine import Timer 
async def task1():
    while True:
        await tsf1.wait()
        print("任务1被唤醒")
        
async def task2():
    while True:
        await tsf2.wait()
        print("任务2被唤醒")
        
async def task3():
    await asyncio.sleep(6)
    timer.deinit()    
    print('关闭所有任务')  

async def main():
    global timer,tsf1,tsf2
    def cb(_):    
        tsf1.set()
        tsf2.set()
    tsf1 = asyncio.ThreadSafeFlag()   # 创建tsf1
    tsf2 = asyncio.ThreadSafeFlag()   # 创建tsf1    
    asyncio.create_task(task1())      # 创建任务1并加入就绪队列
    asyncio.create_task(task2())      # 创建任务2并加入就绪队列
    timer = Timer(0,period=2000, mode=Timer.PERIODIC, callback=cb) # 启动定时器
    await asyncio.gather(task3())     # 不gather其它任务是为了能够关闭    
asyncio.run(main())