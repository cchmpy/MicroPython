import asyncio
async def foo(loop):
    try:
        1 / 0                                 # 触发异常
    except ZeroDivisionError as err:
        print('触发异常')        
        context = {                           # 构造context字典
            'message': 'Division by zero in example_coroutine',
            'exception': err,
            'future': asyncio.current_task()}        
        loop.call_exception_handler(context)  # 手动触发事件循环的异常处理流程(使用默认处理器)

loop = asyncio.get_event_loop()
loop.run_until_complete(foo(loop))
loop.close()