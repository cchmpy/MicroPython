import time,neopixel    # neopixel库封装了bitstream调用
from machine import Pin
np = neopixel.NeoPixel(Pin(23),3)                 # 引脚必须是Pin对象，3代表灯珠的数量
np[0],np[1],np[2] = (100,0,0),(0,100,0),(0,0,100) # 定义每个灯的显示颜色,亮度100
np.write()              # 写入字节流
time.sleep(3)
np.fill([0,0,0])        # 所有灯颜色填充为[0,0,0]
np.write()              # 写入填充值,关灯
