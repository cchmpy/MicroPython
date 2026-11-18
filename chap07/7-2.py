import gc
# 装饰器函数：计算函数func分配的内存和产生垃圾（以字节为单位）
def gcit(func, *args, **kwargs): 
    name = func.__name__ if hasattr(func,'__name__') else ''
    def wrapper(*args, **kwargs):
        gc.disable()
        gc.collect()
        a0 = gc.mem_alloc()
        result = func(*args, **kwargs)
        a1 = gc.mem_alloc()        
        gc.collect()        
        print(f'allocated:{a1-a0} garbage:{a1-gc.mem_alloc()}')
        gc.enable()
        return result
    return wrapper
@gcit               # 使用示例   
def foo(size=1024):
    bytearray(size) # 定义一个引用计数为0的对象
foo(1024*10)        # 输出：allocated:10256 garbage:10256
