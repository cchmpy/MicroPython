class UpperStr(str):
    def __init__(self,value=''): 
        super().__init__(value.upper())  # 先调用基类str的初始化函数
        self._encode = self.encode()     # 然后才能调用继承自基类的方法
print(UpperStr())                        # 空字符串
print(UpperStr('abc你好'))               # ABC你好
