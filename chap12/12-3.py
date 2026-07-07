import espnow_light as light, asyncio          # 导入程序12-2.py（espnow_light.py）
from machine import UART, Signal, Pin

uart = UART(1,tx=22,rx=23,baudrate=115200)
gw = light.Gateway(uart)
try:  asyncio.run(gw.main())
except KeyboardInterrupt: print('ESP-NOW语音网已退出')
finally: gw.deinit()
