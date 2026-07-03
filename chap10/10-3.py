import asyncio
async def foo(delay):                                         # 模拟一个可能耗时的任务
    await asyncio.sleep(delay)       
    return f'任务完成,耗时{delay}秒'

async def main():
    try:        
        result = await asyncio.wait_for(foo(1.5), timeout=2)  # 有时限的任务1
        print(result)                                         # 若任务在2秒内完成,输出结果
    except asyncio.TimeoutError:
        print('任务超时！超过2秒未完成')

    try:        
        result = await asyncio.wait_for(foo(3), timeout=2)    # 有时限的任务2
        print(result)
    except asyncio.TimeoutError:                              # 任务需要3秒,但超时设为2秒,会触发异常
        print("任务超时！超过2秒未完成")

asyncio.run(main())
