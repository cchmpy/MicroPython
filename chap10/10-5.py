import asyncio
async def foo(delay_ms):
    await asyncio.sleep_ms(delay_ms)
    return delay_ms        
async def main():    
    result = await asyncio.gather(foo(1000),foo(1200),foo(1300))   # 方式1
    print(result)                                                  # 返回: [1000, 1200, 1300]
    
    tasks = [foo(x) for x in range(500,1000,100)]                  # 协程列表
    result = await asyncio.gather(*tasks)                          # 方式2
    print(result)                                                  # 返回: [500, 600, 700, 800, 900]
asyncio.run(main())
