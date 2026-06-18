class foo:               # 上下文管理器类
    def __enter__(self): print("Enter")
    def __exit__(self, *args): print("Exit")
def bar(x):              # 使用上下文管理器的生成器函数
    with foo():
        while True:
            x += 1
            yield x
def func():
    g = bar(0) # 生成器对象
    for _ in range(3):
        print(next(g))
func()
