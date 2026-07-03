import asyncio
async def foo(delay_ms):
    await asyncio.sleep_ms(delay_ms)    
    return delay_ms        
async def main():   
    task = asyncio.create_task(foo(1000))    
    start = asyncio.ticks()                              # 当前毫秒数
    while not task.done():                               # 判断任务是否完成
        await asyncio.sleep_ms(100)
        diff = asyncio.ticks_diff(asyncio.ticks(),start) # 计算时间差
        if diff>700 and not task.done():                 # 修改该值，观察不同结果
            task.cancel()                                # 取消任务
            print('cancle')
            return
    else:  print('done')    
     
asyncio.run(main())

