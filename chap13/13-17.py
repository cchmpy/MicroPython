import time, st77xx, gc
from camera import Camera, PixelFormat, FrameSize
from machine import SPI
# 定义硬件对象
spi = SPI(2, 40_000_000, sck=14, mosi=46, miso=3)
lcd=st77xx.ST77xx(spi,dc=2,cs=41,rst=1,bl=42,width=1,height=1,source_forward=True, clr_inverse=False )
lcd.rotate(90)                        # 横屏显示
cam = Camera(frame_size=FrameSize.QVGA, pixel_format=PixelFormat.RGB565)
start = time.time(); i = 0            # 用于计算帧率
try:
    while True:
        cam.free_buffer()
        if cam.frame_available():
            img = cam.capture()
            lcd.image_on_lcd(0,0,320,240,img)
            i += 1
        if i%1000==0: gc.collect()    # 定期垃圾回收
except KeyboardInterrupt:             # Ctrl+C退出
    diff = time.time()-start
    print(i/diff)                     # 打印帧率(实测24/25fps)
    lcd.deinit()
    cam.deinit()
