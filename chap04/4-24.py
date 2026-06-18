class RGBLED: 
    @classmethod
    def from_hex(cls, hex_code):       # 从十六进制字符串创建实例（如 "#FF00FF"） 
        r = int(hex_code[1:3], 16)
        g = int(hex_code[3:5], 16)
        b = int(hex_code[5:7], 16)
        return cls(r, g, b)            # 等同于：RGBLED(r, g, b)
    def __init__(self, r, g, b):
        self._r, self._g, self._b = r, g, b
    def __repr__(self):
        return f'RGBLED({self._r}, {self._g}, {self._b})'
led = RGBLED.from_hex("#FF00FF")       # 使用类方法创建实例
print(led)                             # 输出: RGBLED(255, 0, 255)
