def counter(count=0):    
    def increment():
        nonlocal count               # 声明外层变量，可修改
        count += 1
        return count
    return increment                 # 返回嵌套函数本身
cnt = counter()
print(cnt(), cnt(), cnt())           # 输出 1, 2, 3
