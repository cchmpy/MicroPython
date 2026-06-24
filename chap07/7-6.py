import math, time
from machine import DAC, reset
from micropython import const
_SQUARE   = const(0)        # 方波
_SAWTOOTH = const(1)        # 锯齿波
_SINE     = const(2)        # 正弦波
_TRIANGLE = const(3)        # 三角波
dac       = DAC(25)
n         = 100             # 单周期内的采样点数
samples   = [None,bytearray(n),bytearray(n),bytearray(n)]  # 保存单周期的波形的样本电压

for i in range(n):                                       # 正弦波n个采样点的电压值（0-255）
    samples[_SINE][i] = 128 + int(127 * math.sin(2 * math.pi * i / n))
for i in range(n):                                       # 锯齿波：值从0线性上升到255
    samples[_SAWTOOTH][i] = 255 * i // n
for i in range(n):                                       # 三角波：先上升再下降
    if i < n//2: samples[_TRIANGLE][i] = 510 * i // n    # 上升沿
    else:  samples[_TRIANGLE][i] = 510 - 510 * i // n    # 下降沿

def play_tone(freq, duration, waveform=_SAWTOOTH):
    # freq:频率  duration:持续播放时间(毫秒)  waveform: 波形 
    T = 1_000_000 // freq                                # 波形周期（微秒）
    t = T // n                                           # 每个采样点持续的时间（微秒）
    start = time.ticks_ms()    
    while time.ticks_diff(time.ticks_ms(), start) < duration: # 持续播放
        if waveform == _SQUARE:
            dac.write(255)                               # 方波的高电平
            time.sleep_us(T//2)                          # 高电平持续时间
            dac.write(0)                                 # 方波的低电平
            time.sleep_us(T//2)                          # 低电平持续时间
        else:
            for sample in samples[waveform]:
                dac.write(sample)
                time.sleep_us(t)

tones = (0,262,294,330,349,392,440,494)                  # 简谱音符1234567对应的频率（C调低音）
a  = '115566504433221055443320'                          # 小星星的部分简谱，每个音符持续500ms
for i in range(4):
    print(i)
    for x in a:                                          # 播放乐谱
        if x =='0': time.sleep_ms(500)
        else:   play_tone(tones[ord(x)-ord('0')],500,i)
        time.sleep_ms(20)                                # 音符间停顿20ms
reset()
