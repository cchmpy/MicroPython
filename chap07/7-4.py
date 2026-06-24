import time
from machine import Pin
class Button:
    DOWN, UP = 0, 1    # 按键状态：按下、松开
    E_DOWN   = 1       # 事件：按下
    E_UP     = 2       # 事件：短按松开
    E_LONG_UP= 4       # 事件：长按松开
    
    def __init__(self, pin, pull_up=True, debounce=50, long_press=1000): 
        assert isinstance(pin,Pin),'pin must be an instance of Pin'  # 断言: 判定pin是不是Pin的实例
        self.pin       = pin              # 引脚对象，pin可定义使用内部还是外部上拉/下拉电阻
        self.pull_up   = pull_up          # True表示按键电路使用上拉电阻，否则为下拉电阻
        self.debounce  = debounce         # 消抖时间(毫秒) 
        self.long_press= long_press       # 长按最少时间(毫秒)
        
        self.last_time = 0                # 上次中断触发时间
        self.callback  = None             # 用户需自定义的回调函数 
        self.status    = self._state()    # 获取按键初始状态 
        self.pin.irq(self._handler, Pin.IRQ_FALLING | Pin.IRQ_RISING)# 设置中断回调
    
    def _state(self):                     # 获取按键状态
        if self.pull_up: return self.UP if self.pin() else self.DOWN
        else:            return self.DOWN if self.pin() else self.UP
   
    def _handler(self, pin):
        now = time.ticks_ms()                               # 当前触发中断的时间
        interval = time.ticks_diff(now, self.last_time)     # 两次触发中断的时间间隔
        if  interval> self.debounce:                        # 忽略抖动，仅处理有效按键动作
            s = self._state()                               # 中断触发时按键状态 
            if s != self.status:                            # 按键状态发生变化
                self.status, self.last_time= s,now          # 更新当前状态、时间
                if self.callback:
                    if self.status == self.DOWN:            # 如果按下按键
                        self.callback(self, self.E_DOWN)    # 调用用户设置回调 
                    else:                                   # 如果松开按键
                        if interval < self.long_press:      # 短按松开
                            self.callback(self, self.E_UP)
                        else:                               # 长按松开
                            self.callback(self, self.E_LONG_UP)
    
    def set_callback(self, callback):                       # 用户调用的方法，用以设置回调
        self.callback = callback

if __name__ == '__main__':
    def button_event(button, event):
        if event == button.E_DOWN:  print("按下")
        elif event == button.E_UP:  print("短按松开")
        elif event == button.E_LONG_UP: print("长按松开")    
    btn = Button(Pin(34,Pin.IN), pull_up=True)              # 定义Button类实例
    btn.set_callback(button_event)                          # 设置回调函数
    while True: time.sleep(1)
