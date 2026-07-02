import gc
# 装饰器函数-计算函数分配的内存和产生垃圾的字节大小
def gcit(func, *args, **kwargs): 
    name = func.__name__ if hasattr(func,'__name__') else ''
    def wrapper(*args, **kwargs):
        gc.collect()
        a0 = gc.mem_alloc()            # 函数执行前已经分配的内存大小
        result = func(*args, **kwargs)
        a1 = gc.mem_alloc()            # 函数调用分配的内存大小    
        gc.collect()                   # 回收函数产生的内存垃圾
        print(f'allocated:{a1-a0} garbage:{a1-gc.mem_alloc()}')
        return result
    return wrapper

@gcit
def foo(size=1024):
    bytearray(size)

foo(1024*10)   # 输出：allocated:10320 garbage:10256