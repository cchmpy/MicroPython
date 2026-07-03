import asyncio
from machine import Pin
async def blink(led:Pin,period_ms):       # 通过async def定义协程
    while True:
        led.toggle()
        await asyncio.sleep_ms(period_ms) # 异步延时，await表示异步等待延时操作完成，期间让出CPU

async def main(led1, led2):               # 定义主协程
    asyncio.create_task(blink(led1, 800))
    asyncio.create_task(blink(led2, 600))
    await asyncio.sleep_ms(10_000)        # 异步延时，期间让出CPU，事件循环可执行其它操作

asyncio.run(main(Pin(23,mode=Pin.OUT), Pin(22,mode=Pin.OUT)))  # 启动事件循环，运行主协程
