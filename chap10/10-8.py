import asyncio
def my_exception_handler(loop, context):
    # 自定义处理逻辑：打印异常类型和消息
    exc = context.get('exception', None)
    msg = context.get('message', 'Unknown error')
    fut = context.get('future',None)
    print(f'{type(exc)}\n{msg}\n{id(fut)}')
    loop.stop()                                   # 停止事件循环

async def bad_coroutine():
    raise ValueError("Something went wrong")

loop = asyncio.get_event_loop()
loop.set_exception_handler(my_exception_handler)  # 设置自定义处理器
loop.create_task(bad_coroutine())                 # 创建任务并加入任务队列
loop.run_forever()      # 不使用run_until_complete,否则直接退出不能接收异常
