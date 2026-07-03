import esp32,time,gc
from machine import UART,ADC,deepsleep
from micropython import const
THRESHOLD_MID  = const(600)         # 危险气体轻微泄露的阈值电压（ADC测量值）
THRESHOLD_HIGH = const(1500)        # 危险气体浓度较高的阈值电压（ADC测量值）
buf = bytearray(b'\xAA\x08\x08\x01\x2f\x00\x00\x2a\x3f\x3f\x3f\x00')   # UART发送的播放MP3指令
SUM = sum(buf)                      # 指令校验和
adcs = [36,34]                      # 所有模拟信号输入引脚(连接天然气、一氧化碳传感器模块的逻辑输出)
pins = (39,35)                      # 所有数字输入引脚，用于唤醒系统（连接传感器模块的数字输出）
mid=[]                              # adc测量值>=THRESHOLD_MID的传感器在adcs列表的序号
high=[]                             # adc测量值>=THRESHOLD_HIGH的传感器在adcs列表的序号

uart1 = UART(1,baudrate=9600,rx=23,tx=22)        # 用于发送播放mp3的指令
esp32.wake_on_ext1(pins,esp32.WAKEUP_ANY_HIGH)   # 设置唤醒源

for i in range(len(adcs)):
    adcs[i] = ADC(adcs[i], atten=ADC.ATTN_11DB)  # 定义所有ADC对象
    
def play_file(uart,fname):                       # 播放名为fname的MP3文件，如"10"(10.mp3)
    buf[5],buf[6]=ord(fname[0]),ord(fname[1])    # 文件名两个字符的编码
    buf[-1]=(SUM+buf[5]+buf[6]) & 0xff           # 校验和
    uart.write(buf)                              # 写入xy-v17b模块
    
def measure(n=10):                               # 读取所有传感器的ADC值
    global adcs,mid,high
    mid.clear()
    high.clear()
    for i in range(len(adcs)):
        v = 0
        for j in range(n):                       # 对每个传感器进行多次测量，求平均值
            v += adcs[i].read_uv()               # 累加测量值 
        v //= n*1000                             # 求平均值(mv)
        if THRESHOLD_MID<=v<THRESHOLD_HIGH: mid.append(i) 
        elif v>=THRESHOLD_HIGH:             high.append(i)

while True:
    measure()
    if len(mid)==0 and len(high)==0:             # 环境安全
        print('Zzz...')
        time.sleep(1)
        deepsleep()
    else:
        for i in mid:                            # 检测到轻微泄露
            play_file(uart1,str(i+31))           # 语音播报,文件名31.mp3、32.mp3 ...
            time.sleep(5)                        # 播放间隔（含播放时间）   
        for i in high:                           # 检测到高浓度泄露
            play_file(uart1,str(i+41))           # 语音播报,文件名41.mp3、42.mp3 ...
            time.sleep(5)
    gc.collect() 
    time.sleep(1)
