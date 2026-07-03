import asyncio
async def foo(delay_ms):
    await asyncio.sleep_ms(delay_ms)
    5/0            # 抛出异常
    return delay_ms        
async def main():   
    result = await asyncio.gather(foo(100),foo(200),return_exceptions=True)
    print(result)  # 返回: [ZeroDivisionError('divide by zero',), ZeroDivisionError('divide by zero',)]
    
asyncio.run(main())
