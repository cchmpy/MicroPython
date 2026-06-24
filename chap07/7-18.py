from machine import I2S,Timer
import time
# i2s和音频格式配置字典默认数据
config ={'id':0,'sck':17,'ws':19,'sd':18,'bits':16,'rate':44100,
         'channels':1,'ibuf':40000,'ireadbuf':12000}

class I2SRecorder:
    RECORD, PAUSE, STOP = 0, 1, 2             # 录音状态 
    def __init__(self):
        self._i2s = I2S(config['id'],sck=config['sck'],ws=config['ws'],sd=config['sd'],
                        mode=I2S.RX, bits=config['bits'], format=config['channels']-1,
                        rate=config['rate'], ibuf=config['ibuf'])
        self._i2s.irq(self._handle)           # 设置回调，启动非阻塞模式
        self._buf = memoryview(bytearray(config['ireadbuf']))  # 读取录音数据的缓冲
        self._status = self.RECORD            # 准备录音
        self._target = None                   # 录音数据传输目标对象，该对象支持write()方法
        
    def state(self,status=None):              # 获取或设置录音状态
        if status is None: return self._status        
        if self._status==status or status not in (self.STOP,self.PAUSE,self.RECORD):
            return self._status
        self._status = status                 # 状态有效且发生了变化，PAUSE/STOP无需处理
        if status == self.PAUSE:
            if self._seconds>0:               # 还有录音时长
                self._timer.deinit()          # 停止定时器
                self._seconds -= time.time()-self._start # 剩余时长 
        elif status == self.RECORD:
            self._i2s.readinto(self._buf)     # 继续录音
            if self._seconds>0:               # 还有时长，重启定时器
                self._timer.init(period=self._seconds*1000, mode=Timer.ONE_SHOT,callback=self._timer_cb)
                self._start=time.time()
    
    def _handle(self,i2s):                    # i2s回调函数 
        if self._status==self.RECORD:         # 处于录音状态，则继续录制
            self._target.write(self._buf)         # 把录音数据写入目标对象
            i2s.readinto(self._buf) 
    
    def _timer_cb(self,t):                    # 定时器回调函数，用于停止录音
        self._status = self.STOP
        self._seconds = 0                     # 录音时长
        t.deinit()
        
    def record(self,target,seconds=0,timer_id=0): # 开始录音
        self._target = target
        self._seconds = seconds               # 录音秒数
        if seconds>0:                         # 若设定录音时长，则启用定时器
            self._timer = Timer(timer_id, period=seconds*1000, mode=Timer.ONE_SHOT,callback=self._timer_cb)
            self._start = time.time()         # 录音开始时间
        self._i2s.readinto(self._buf)         # 将录音数据读取到缓冲，触发回调
    
    def deinit(self):
        self._i2s.deinit()

if __name__ == '__main__':
    from machine import TouchPad    
    from wavfile import WavFile               # 引用程序7-7.py
    def get_target(t='i2s'):                  # 获取录音目标
        if t=='i2s':
            config['ibuf'],config['ireadbuf']  = 10000,6000         # 减少数值（减少延迟）
            player = I2S(1,sck=22,ws=21,sd=23,mode=I2S.TX,bits=config['bits'],
                             format=config['channels']-1,rate=config['rate'],ibuf=config['ibuf'])
            player.irq(lambda _ : None)       # 启动非阻塞模式
            return player
        elif t=='wav':
            config['ibuf'],config['ireadbuf']  = 40000,12000
            return WavFile('sd/r1.wav',new=True, channels=config['channels'],
                             sample_rate=config['rate'], sample_bits=config['bits'])   
    
    t_pause, t_stop, thre = TouchPad(32), TouchPad(4), 200         # 触摸控制、阈值
    target = get_target('wav')               # 数据接收者
    recorder = I2SRecorder()
    recorder.record(target,seconds=-1)       # 开始录音,时长30s
    
    while True:
        if recorder.state()==recorder.STOP:
            if hasattr(target,'close'):target.close() 
            if hasattr(target,'deinit'):target.deinit()
            recorder.deinit()
            break
        if t_pause.read()<thre:
            recorder.state(int(not recorder.state()))
            time.sleep_ms(1000)              # 有触摸延长休眠
        elif t_stop.read()<thre:
            recorder.state(recorder.STOP)
            time.sleep_ms(1000)
        time.sleep_ms(50)                    # 无触摸短暂休眠
