class Descriptor:                  # 1. 定义一个描述符类，类名可以是任何合法名称
    def __get__(self, obj, owner): 
        return "我是描述符的值"
class Foo:
    foo_attr = Descriptor()        # 2、创建类属性并赋值为描述符实例对象
obj = Foo()
print(Foo.foo_attr)      # 通过类名访问类属性，直接返回其值，输出：<Descriptor object at 3ffd0180>
print(obj.foo_attr)                # 通过对象obj访问类属性，输出: "我是描述符的值"
print(getattr(obj, "foo_attr"))    # 调用内置函数访问类属性，输出: "我是描述符的值"
