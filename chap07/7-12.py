import time,dht,gc
from machine import UART
# 指定盘符指定路径的播放格式:AA 08 长度 盘符 路径 SM，其中路径是"/yyy*???", 根目录下文件名是yyy
buf = bytearray(b'\xAA\x08\x08\x01\x2f\x00\x00\x2a\x3f\x3f\x3f\x00')   # 待发送的帧数据
SUM = sum(buf)                                # 用于计算校验和
def play_file(uart,fname):                    # 播放名为fname的文件，如"10"(10.mp3)
    buf[5],buf[6]=ord(fname[0]),ord(fname[1]) # 文件名两个字符的编码
    buf[-1]=(SUM+buf[5]+buf[6]) & 0xff        # 校验和
    uart.write(buf)                           # 写入xy-v17b模块
    time.sleep_ms(360)                        # 等待播放完成（读0-9数字的时间）

def play_num(uart,n):                         # 播报99以内的非负数
    sn = str(n)
    play_file(uart,f'0{sn}')                  # 直接读出首个数字 0-9
    if len(sn)==2:
        play_file(uart,'10')                  # 读单位十（10.mp3）
        if sn[1] != '0': 
            play_file(uart,f'0{sn[1]}')       # 读个位上的数字
    
def play(uart,t,h):                           # 测量并播报温湿度
    play_file(uart,'20')                      # 播放"当前温度"语音
    time.sleep_ms(1000)                       # 等待播完
    play_num(uart,t)                          # 播报温度
    time.sleep_ms(200)                        # 暂停一下
    play_file(uart,'21')                      # 播放"摄氏度"
    time.sleep_ms(1000)
    play_file(uart,'22')                      # 播放"湿度百分之"
    time.sleep_ms(1000)
    play_num(uart,h)                          # 播报湿度
    
dht11 = dht.DHT11(19) 
uart1 = UART(1,baudrate=9600,rx=23,tx=22)
try:
    while True:
        dht11.measure()                       # 测量
        t,m = dht11.temperature(),dht11.humidity() 
        play(uart1,t,m)                       # 播报
        gc.collect()                          # 每个循环进行一次垃圾回收
        time.sleep(60)                        # 测量和播报间隔时间
except Exception as err:
    uart1.deinit()
