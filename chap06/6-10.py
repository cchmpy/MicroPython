import io,os
from machine import Pin
class ButtonStream(io.IOBase):
    def __init__(self, c, pin=23): 
        self._n = 0                     # 通过按键输入字符的数量
        self._c = c                     # 当按键按下时，输入的单个字符
        self.btn = Pin(pin,mode=Pin.IN) # 定义引脚为输入模式
        self.btn.irq(self._press,trigger=Pin.IRQ_RISING)  # 定义引脚的中断回调函数和触发模式

    def _press(self,_):                 # 中断回调函数，参数'_'表示忽略传入的引脚参数
        self._n += 1                    # 按键次数增加1（输入一个字符）
        if hasattr(os, "dupterm_notify"):
            os.dupterm_notify(None)     # 通知REPL有输入数据，参数也可以为self

    def readinto(self, buf):            # 非阻塞模式的readinto()
        n = min(len(buf), self._n)
        for i in range(n):
            buf[i:i+1] = self._c        # self._c是bytes类型，所以使用切片赋值
        self._n -= n                    # 去掉已经读取的字符
        return None if n == 0 else n    # 若没有数据可读，立即返回None，不阻塞
    
    def write(self, buf):               # 忽略或不复制REPL的输出
        pass

if __name__ == '__main__':
    os.dupterm(ButtonStream(b'A'))      # 定义ButtonStream对象，按键将输入字母A，默认引脚23
    try:
        while True:
            a = input()                 # 可以通过与引脚连接的按钮输入字符
            print('The input is:', a)   # 在repl内按下回车键（输入完成）可打印输入数据   
    except KeyboardInterrupt:
        os.dupterm(None)
