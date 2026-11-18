import micropython as mpy, time
from machine import Timer
class Foo:
    def __init__(self):
        self._f = self.func         # 把示例方法self.func赋值给实例变量self._f
        self._t = Timer(0,mode=Timer.ONE_SHOT,period=500,callback=self.handle)
    def handle(self,_):             # 定时器中断回调函数
        mpy.heap_lock()             # 锁堆，禁止分配内存
        ...                         # 此处是中断处理逻辑
        x = 100                     # 小整数临时变量,使用栈内存
        # mpy.schedule(self.func,x) # 若这样调用则抛出MemoryError异常
        mpy.schedule(self._f,x)     # 在中断回调中调度一个耗时的操作
        mpy.heap_unlock()
    def func(self,x):               # 模拟一个耗时操作 
        for i in range(1000):x+=1
        print(x)
foo = Foo(); time.sleep(1)