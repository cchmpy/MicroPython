class RadiusDescriptor:
    def __get__(self, obj, owner): 
        return obj._r

    def __set__(self, obj, value):
        obj._r = abs(value)
        obj._s = 3.14*obj._r**2
    
    def __delete__(self,obj):
        del obj._r 

class Circle:
    r = RadiusDescriptor()  # 创建类属性

    def __init__(self, r=0):
        self._r = r
        self._s = 3.14*r**2
    
    def __str__(self):
        if hasattr(self,'_r'):
            return f'r={self._r} s={self._s:.2f}'
        else:
            return f's={self._s:.2f}' 
        
c = Circle(10)
print(type(Circle.r)) # <class 'RadiusDescriptor'>
print(c.r)            # 调用__get__(),输出：10
c.r = 20              # 调用__set__()
print(c)              # 输出：r=20 s=1256.00
del c.r               # 调用__delete__()
print(c)              # 输出：s=1256.00
