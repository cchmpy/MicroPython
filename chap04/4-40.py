class Foo:
    class Descriptor:              # 1. 嵌套定义一个描述符类     
        def __set__(self, obj, value):
            obj.x = abs(value)     
    foo_attr = Descriptor()        # 2、创建类属性并赋值为描述符实例对象
    def __init__(self,x=0):
        self.x = 0                 # 实例属性
obj = Foo()
obj.foo_attr = -100                # 通过实例obj对类属性赋值，间接为操作实例属性x
print(obj.x)                       # 100
Foo.foo_attr = -100                # 通过类Foo对类属性赋值，类属性重新绑定到一个整型对象
print(Foo.foo_attr)                # -100，类属性不再是一个描述符
