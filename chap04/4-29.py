import math, utils       # 标准模块和自定义模块
class Foo(): pass        # 自定义类    
def foo(): pass          # 自定义函数
f = Foo()                # 自定义类实例
a = ['标准模块','自定义模块','内置函数','自定义函数',
     '内置类','自定义类','内置类实例','自定义类实例']
b = [math,utils,len,foo,str,Foo,'abc',f]

for x in ('__class__', '__name__', '__dict__','__file__','__path__',
          '__globals__','__bases__','__module__','__qualname__','__version__'):
    print(f'\n{x}:')
    for name,obj in zip(a,b):
        if hasattr(obj, x): print(f'{name}: {getattr(obj,x)}')
