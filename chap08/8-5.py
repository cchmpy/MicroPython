from micropython import const
from myutils import timeit
import time
cnt = [0]                    # 全局变量
_A = const(30000)            # 加法计算次数

@timeit('ms')
def foo():                   # 普通函数，直接访问全局变量    
    for i in range(_A):  cnt[0]+=1
    
@timeit('ms')
def foo_local():             # 普通函数，通过局部变量访问全局变量   
    c = cnt
    for i in range(_A):  c[0]+=1    
    
class Foo:
    cnt = [0]
    @classmethod
    @timeit('ms')
    def foo(cls):            # 类方法,直接访问类属性 
        for i in range(_A):  cls.cnt[0]+=1
    @classmethod
    @timeit('ms')
    def foo_local(cls):      # 类方法,通过局部变量访问类属性 
        t = cls.cnt
        for i in range(_A):  t[0]+=1
foo()              # 248ms
foo_local()        # 222ms,提高10%
Foo.foo()          # 293ms
Foo.foo_local()    # 222ms,提高24%
