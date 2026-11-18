class Circle:
    @property                                             # 创建类属性r（默认getter()）
    def r(self):  return self._r                          # 读取属性r
    @r.setter
    def r(self, value):                                   # 设置属性r
        self._r = abs(value); self._s = 3.14*self._r**2
    @r.deleter                                            # 删除属性r
    def r(self): del self._r
        
    def __init__(self, r=0):                              # 构造方法
        self._r = r;  self._s = 3.14*r**2
        
    def __str__(self):                                    # 特殊方法
        if hasattr(self,'_r'): return f'r={self._r} s={self._s:.2f}'
        else:                  return f's={self._s:.2f}' 
c = Circle(10)                                            # 定义实例
print(c.r)            # 调用getter(),输出：10
c.r = 20              # 调用setter()
print(c)              # 调用__str__(),输出：r=20 s=1256.00
del c.r               # 调用deleter()
print(c)              # 调用__str__(),输出：s=1256.00
