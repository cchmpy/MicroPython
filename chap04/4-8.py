def power_factory(exponent):
    def power(base):
        return base ** exponent  # 捕获外部变量exponent
    return power
square = power_factory(2)        # 生成平方函数
cube = power_factory(3)          # 生成立方函数
print(square(4))                 # 输出: 16
print(cube(4))                   # 输出: 64
