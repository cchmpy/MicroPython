class Color:
    _cache = {}    
    def __new__(cls, r, g, b):
        key = (r, g, b)
        if key not in cls._cache:
            cls._cache[key] = instance = super().__new__(cls)
            instance.r, instance.g, instance.b = r, g, b     # 添加属性并赋值（初始化）
        return cls._cache[key]
red1 = Color(255, 0, 0)
red2 = Color(255, 0, 0)
print(red1 is red2)                           # 输出: True (复用同一对象)
