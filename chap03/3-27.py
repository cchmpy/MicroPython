# 示例1
class Descriptor:                  # 1. 定义一个描述符类，类名可以是任何合法名称
    def __get__(self, obj, owner): 
        return "我是描述符的值"
class Foo:
    foo_attr = Descriptor()        # 2、创建类属性并赋值为描述符实例对象
obj = Foo()
print(Foo.foo_attr)      # 通过类名访问类属性，直接返回其值，输出：<Descriptor object at 3ffd0180>
print(obj.foo_attr)                # 通过对象obj访问类属性，输出: "我是描述符的值"
print(getattr(obj, "foo_attr"))    # 调用内置函数访问类属性，输出: "我是描述符的值"

# 示例2
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

# 示例3
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
