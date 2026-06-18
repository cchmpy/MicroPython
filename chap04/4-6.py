def factorial(n):
    def _fact(n, acc=1):       # 嵌套尾递归函数
        if n == 0:
            return acc
        return _fact(n - 1, acc * n)
    return _fact(n) 
print(factorial(5))           # 输出 120
