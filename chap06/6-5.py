from time import sleep_ms
from machine import PWM
import asyncio
class Buzzer:
    def __init__(self, pin, vol=100):
        self._pwm = PWM(pin,freq=330,duty_u16=0) 
        self.volume(vol)                                # 调用成员函数设置音量 
    def deinit(self):
        self._pwm.deinit()
        
    def volume(self, vol=None):                         # 获取或设置音量vol:[0,100]
        if vol is None: return self._vol//65
        self._vol = vol*65
        
    def tone(self,freq=330,duration_ms=None,vol=None):  # 按设定时长和音量播放特定频率的声音
        if vol: self._vol = vol*65
        self._pwm.init(freq=freq,duty_u16=self._vol) 
        if duration_ms:
            sleep_ms(duration_ms)
            self.no_tone()
            
    async def atone(self,freq,duration_ms,vol=None):    # 异步播放设定时长、音量和频率的声音
        if vol: self._vol = vol*65
        self._pwm.init(freq=freq,duty_u16=self._vol) 
        await asyncio.sleep_ms(duration_ms)
        self.no_tone()

    def no_tone(self):                                  # 停止播放
        self._pwm.duty_u16(0)
        
if __name__=='__main__':
    tones = (0,262,294,330,349,392,440,494)                  # 音符1234567对应的频率（C调低音）
    a  = '11556650443322105544332055443320115566504433221'   # 小星星简谱，每个音符持续500ms
    bz = Buzzer(23,vol=20)                                   # 定义蜂鸣器对象 
    for x in a:                                              # 播放乐谱
        if x =='0': sleep_ms(500)
        else:   bz.tone(tones[ord(x)-ord('0')],500,5)
        sleep_ms(20)                                         # 每个音符播放完成后停顿20ms
