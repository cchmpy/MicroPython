import wavfile                         # 引用程序7-7.py
from machine import I2S
def play_blocking(wav_file, *, shift=0,loop=1, sck=22,ws=21,sd=23,id=0):
    if loop == 0: return 
    with wavfile.WavFile(wav_file) as f:
        bits = f.sample_bits
        i2s = I2S(id,sck=sck,ws=ws,sd=sd,mode=I2S.TX,
                  bits=bits, format=f.channels-1,
                  rate=f.sample_rate, ibuf=40000)
        while loop:
            for data in f.read():
                if shift: i2s.shift(buf=data,bits=bits,shift=shift)   # 音量控制
                i2s.write(data)         # 阻塞模式播放
            loop -= 1                   # 循环次数-1
        i2s.deinit()                    # 完成播放，释放I2S
play_blocking('sd/good.wav',loop=-2,shift=-2)