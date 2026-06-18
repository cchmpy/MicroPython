import time
class TimeIt:
    def __init__(self,func):
        self.func = func
        self.name = func.__name__ if hasattr(func,'__name__') else ''
    def __call__(self,*args,**kwargs):
        start = time.ticks_us() 
        result = self.func(*args, **kwargs)
        print(f'{self.name}() execution time: {time.ticks_diff(time.ticks_us(), start)}us')
        return result   
@TimeIt
def foo(n, x):
    for i in range(n): x+=i    
foo(1000, 0)                        # 输出：foo() execution time: 45292us
