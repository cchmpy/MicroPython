import adafruit_miniqr,st77xx,time,gc
from machine import SPI,Pin
def draw_qr(lcd, text, x, y, w, h):            # 在LCD的矩形区域(x,y,w,h)中绘制二维码，尽可能放大
    qr = adafruit_miniqr.QRCode(qr_type=3)     # 定义QRCode对象，qr_type指定二维码版本
    qr.add_data(text.encode())                 # 添加文本的utf-8编码
    qr.make()                                  # 生成二维码点阵数据 
    qrw=qr.matrix.width; qrh=qr.matrix.height  # 像素宽、高（码元数）
    scale = min(w//qrw, h//qrh)                # 二维码点阵数据的放大倍数
    x+=(w-qrw*scale)//2; y+=(h-qrh*scale)//2   # 重新计算绘图开始坐标，保证图像居中
    for y1 in range(qrh):                      # 扫描所有行
        for x1 in range(qrw):                  # 扫描当前行的所有列
            c = lcd.WHITE if qr.matrix[x1, y1] else lcd.BLACK  # (x1,y1)点像素的颜色
            lcd.rect(x1*scale+x, y1*scale+y, scale, scale,c,1) # 用正方形表示每个像素
    return qr.matrix.width,qr.matrix.height    # 返回二维码码元

w = 240; h = 320                               # LCD分辨率（st7789v）
spi = SPI(2, 26_000_000, sck=0, mosi=4, miso=5)
font_cs = Pin(22,mode=Pin.OUT,value=1)         # 禁用字库片选 
lcd=st77xx.ST77xx(spi,dc=19,cs=21,rst=18,bl=23,width=w,height=h,font=None,
           source_forward=True, clr_inverse=False)

wifi = 'WIFI:T:WPA2;S:ESP32_AP;P:12345678;;'   # 二维码的Wi-Fi信息字符串
url = 'http://192.168.4.1'                     # 二维码的url
print(draw_qr(lcd,wifi,0,0,240,140))
print(draw_qr(lcd,url,0,180,240,140))
lcd.show()
try:                                           # Ctrl+C退出
    while True: time.sleep(1)
except KeyboardInterrupt: lcd.deinit();spi.deinit()
