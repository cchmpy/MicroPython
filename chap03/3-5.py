import time
def timeit(func):                                            # 计算函数运行时间的函数装饰器
    name = func.__name__ if hasattr(func,'__name__') else '' # 原函数（待测函数）名称
    def wrapper(*args, **kwargs):
        start = time.ticks_us() 
        result = func(*args, **kwargs)
        print(f'{name}() execution time: {time.ticks_diff(time.ticks_us(), start)}us')
        return result
    return wrapper
@timeit
def foo(n=10000, x=0):
    for i in range(n): x+=i
foo()                                                   # 输出：foo() execution time: 45293us
