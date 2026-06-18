import time
def timeit(precision='us'):             # 装饰器工厂函数，默认使用us计时
    def timeit_(func):                  # 真正的装饰器函数 
        name = func.__name__ if hasattr(func,'__name__') else ''
        def ticks():                    # 嵌套函数，提取了重复代码 
            if precision=='ms': return time.ticks_ms()
            elif precision=='cpu': return time.ticks_cpu()
            else: return time.ticks_us()
        def wrapper(*args, **kwargs):   # 包装函数
            start = ticks()
            result = func(*args, **kwargs) 
            print(f'{name}() execution time: {time.ticks_diff(ticks(), start)}{precision}')
            return result
        return wrapper                  # 返回包装函数
    return timeit_                      # 返回装饰器函数
class Foo:
    def __init__(self): self._x = 0
    @timeit('ms')                       # 使用装饰器工厂装饰实例方法
    def ban(self,n=10000):
        for i in range(n): self._x+=i
Foo().ban()                           # 输出:ban() execution time: 62ms
