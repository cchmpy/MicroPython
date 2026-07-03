import asyncio
task = None
async def c1():
    global task
    task = asyncio.current_task()
    try: await asyncio.sleep(5)        
    except asyncio.CancelledError: print('c1被取消')    
    
async def c2():
    global task
    await asyncio.sleep(2)
    print('c2完成')
    if not task.done():
        task.cancel()                       # 向c1的任务发送 “取消请求”。
        print(f'c2取消了c1,其ID:{id(task)}')
    else: print('c1完成')
    
async def main(): 
    await asyncio.gather(c1(),c2())

asyncio.run(main())   