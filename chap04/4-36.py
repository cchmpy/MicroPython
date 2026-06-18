class Foo:
    x = 0                                                  # 类属性
    def __init__(self):
        self.y = 0                                         # 实例属性
    def __setattr__(self, name, value):
        print(f"__setattr__({name}, {value})")
        if name == 'y' and value<0: value = abs(value)     # y只能是非负数 
        super().__setattr__(name,value)                    # 修改存在实例属性值或存储新的实例属性 
Foo.x = 10           # 设置类属性，不调用__setatrr__()
obj = Foo()          # 初始化时设置类属性, 输出：__setattr__(y, 0) 
obj.y = -10          # 修改存在属性值,     输出：__setattr__(y, -10)
setattr(obj,'y',-1)  # 调用内置函数，      输出：__setattr__(y, -1)
obj.z = 20           # 增加新的实例属性，  输出：__setattr__(z, 20)
