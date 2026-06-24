import wavfile                               # 引用程序7-7.py
from machine import I2S
class I2SPlayer: 
    PLAY, PAUSE, STOP = 0, 1, 2              # 播放状态 
    def __init__(self, i2s_id=0):
        self._id = i2s_id
        self._status = self.STOP
        
    def volume(self, shift=None):            # 获取或设置音量（移位多少）
        if shift is None: return self._shift
        self._shift = shift
    
    def state(self,status=None):            # 获取或设置播放状态
        if status is None: return self._status
        if hasattr(self,'_wav'):             # 如果已经打开wav文件
            if self._status==status or status not in (self.STOP,self.PAUSE,self.PLAY):
                return self._status
            self._status = status            # 状态有效且发生了变化，才会赋值和操作，PAUSE无需处理
            if status == self.STOP:
                self._i2s.deinit()
                self._wav.close()
            elif status == self.PLAY:
                self._handle(self._i2s)      # 从中断位置继续播放 
    
    def _write(self):                        # 移位并写入数据
        data = next(self._generator)
        if self._shift != 0:
            self._i2s.shift(buf=data, bits=self._bits, shift= self._shift)
        self._i2s.write(data)                # 写入数据，可触发回调调用 
    
    def _handle(self,i2s):                   # 回调函数
        try:
            if self._status == self.PLAY: self._write()  # PAUSE状态不播放
        except StopIteration:                # 文件播放完成，next()函数抛出异常
            self._loop -= 1                  # 重复次数减1
            if self._loop:                   # 重新播放
                self._generator = self._wav.read()       # 重新获取生成器
                self._write()                # 非阻塞模式开始播放，可触发回调
            else:                            # 全部播放完成
                self.state(self.STOP) 
    
    def play(self,wav_file, *,shift=0,loop=1,sck=22,ws=21,sd=23):
        self._loop = loop
        self._shift = shift
        if loop == 0:
            self._status = self.STOP
            return
        self._status = self.PLAY 
        self._wav = wavfile.WavFile(wav_file)# 定义WaveFile对象，打开一个wav文件
        self._bits = self._wav.sample_bits
        self._i2s = I2S(self._id,sck=sck,ws=ws,sd=sd,mode=I2S.TX,
                  bits=self._bits, format=self._wav.channels-1,
                  rate=self._wav.sample_rate, ibuf=40000)
        self._i2s.irq(self._handle)          # 设置回调，启用非阻塞模式
        self._generator = self._wav.read()   # 获取生成器
        self._write()                        # 写入数据，触发回调

if __name__ == '__main__':
    from machine import TouchPad
    import time
    # 电容触摸：停止、播放/暂停、音量增加、音量减少
    t = [TouchPad(0),TouchPad(4),TouchPad(32),TouchPad(33)]
    thre = 200                                           # 电容触摸阈值
    f,loop,shift = 'sd/500Miles.wav', 1, 1               # 待播放文件、循环次数、音量
    p = I2SPlayer()
    p.play(f,shift=shift,loop=loop,sck=22,ws=21,sd=23)   # 开始非阻塞模式播放
    
    while True:        
        if t[0].read()<thre: p.status(p.STOP)            # 停止播放
        elif t[1].read()<thre:                           # 暂停/播放
            if p.status() == p.STOP:                     # 停止后，重新播放
                p.play(f, shift=shift, loop=loop,sck=22,ws=21,sd=23)
            else:
                p.status(int(not p.status()))            # 切换暂停和播放
        elif t[2].read()<thre:  p.volume(shift:=shift+1) # 增加音量
        elif t[3].read()<thre: p.volume(shift:=shift-1)  # 减少音量
        else:
            time.sleep_ms(50)                            # 没有触摸信号，短暂休眠
            continue
        print(f'{p.volume()} \r',end='')
        time.sleep_ms(1000)                              # 有触摸信号，延长休眠，防止产生多次触摸信号
