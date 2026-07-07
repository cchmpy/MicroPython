import espnow_light as light, asyncio          # 导入程序12-2.py（espnow_light.py）
from machine import UART, Signal, Pin

signal = Signal(23, mode=Pin.OUT, invert=True)                         # 设备控制信号
device=light.Device(signal, device_name=light.NAME_LIVINGROOM_LAMP)    # 定义设备对象
try: asyncio.run(device.main())
except KeyboardInterrupt: print('ESP-NOW设备已退出')
finally: device.deinit()
