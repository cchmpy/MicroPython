from machine import DAC, reset
from wavfile import WavFile                     # 引用程序7-7.py
import time
dac_left = DAC(25)
dac_right= DAC(26)
with WavFile('/sd/兰花草.wav',bufsize=12000) as f:
    print(f)
    print('播放wav文件...')    
    c = f.channels                              # 声道数
    b = f.sample_bits//8                        # 单个采样点单通道的字节数
    bc = b*c                                    # 单个采样点总字节数
    for data in f.read():
        i = 0                                   # 数据data中的第i个采样点
        while i<len(data):
            dac_left.write(data[i])             # 播放左声道
            if c==2: dac_right.write(data[i+b]) # 播放右声道
            i += bc                             # 下一个采样点
            time.sleep_us(8)                    # 大约的延时时间
reset()
