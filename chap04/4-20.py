class Circle:
    # 创建类属性r(数据描述符对象)
    @property
    def r(self): 
        return self._r

    @r.setter
    def r(self, value):
        self._r = abs(value)
        self._s = 3.14*self._r**2
    
    @r.deleter
    def r(self):
        del self._r
        
    def __init__(self, r=0):
        self._r = r
        self._s = 3.14*r**2
        
    def __str__(self):
        if hasattr(self,'_r'):
            return f'r={self._r} s={self._s:.2f}'
        else:
            return f's={self._s:.2f}' 
c = Circle(10)
print(type(Circle.r)) # 输出:<class 'property'>
print(c.r)            # 调用getter(),输出：10
c.r = 20              # 调用setter()
print(c)              # 输出：r=20 s=1256.00
del c.r               # 调用deleter()
print(c)              # 输出：s=1256.00
