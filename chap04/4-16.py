def decorator1(func):
    def wrapper(*args,**kwargs):
        print("装饰器1前置处理")
        func(*args,**kwargs)
        print("装饰器1后置处理")
    return wrapper
def decorator2(func):
    def wrapper(*args,**kwargs):
        print("装饰器2前置处理")
        func(*args,**kwargs)
        print("装饰器2后置处理")
    return wrapper
def decorator3(func):
    def wrapper(*args,**kwargs):
        print("装饰器3前置处理")
        func(*args,**kwargs)
        print("装饰器3后置处理")
    return wrapper
@decorator1
@decorator2
@decorator3
def foo():  print("原始函数执行")
foo()
