class Foo:
    class Descriptor: 
        def __delete__(self, obj):
            del obj.x
            # 若想防止删除实例属性，可用下方语句替换上方语句
            # raise AttributeError(f"Can't delete {obj}.x") 
    foo_attr = Descriptor() 
    def __init__(self,x=0):
        self.x = 0                 # 实例属性
obj = Foo()
del obj.foo_attr                   # 调用__delete__将删除obj.x
del Foo.foo_attr                   # 直接删除类属性
print(Foo.foo_attr)                # AttributeError: type object 'Foo' has no attribute '
