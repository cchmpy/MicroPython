class Foo:
    x = 0                             # 类属性
    def __init__(self):
        self.y = 0                    # 实例属性
    def __delattr__(self, name):
        print(f"__delattr__({name})")
        super().__delattr__(name)     # 实际删除属性
obj = Foo()
del Foo.x      # 删除类属性,不会调用__delattr__()
del obj.y      # 删除存在的实例属性，  输出：__delattr__(y)
del obj.z      # 删除不存在的实例属性，输出：__delattr__(z)  AttributeError: no such attribute
