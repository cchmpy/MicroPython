# 闭包实现计数器4-10.py
def counter():          # 外层函数
    count = 0           # 闭包捕获的变量
    def increment():    # 内层函数（闭包）
        nonlocal count  # 修改外层变量
        count += 1
        return count
    return increment

c = counter()  # c是一个闭包，记住了count
print(c())     # 1
print(c())     # 2
