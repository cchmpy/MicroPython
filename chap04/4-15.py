import time
class TimeIt:
    def __init__(self,precision='us'):
        self.precision = precision 
    def __call__(self,func):
        name = func.__name__ if hasattr(func,'__name__') else ''
        def ticks():
            if self.precision=='ms': return time.ticks_ms()
            elif self.precision=='cpu': return time.ticks_cpu()
            else: return time.ticks_us()
        def wrapper(*args, **kwargs):
            start = ticks() 
            result = func(*args, **kwargs)
            print(f'{name}() execution time: {time.ticks_diff(ticks(), start)}{self.precision}')
            return result
        return wrapper   
@TimeIt('ms')
def foo(n, x):
    for i in range(n): x+=i
foo(10000, 0)                       # 输出：foo() execution time: 45ms
