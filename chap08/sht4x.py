import time
class SHT4X:
    def __init__(self,i2c,addr=0x44):
        self._i2c = i2c        
        self._addr = addr
        self._buf = bytearray(6)                  # 读取测量结果:2温度+1校验+2湿度+1校验
    
    def measure(self,crc=False):                  # 测量并返回结果，参数crc是否校验
        self._i2c.writeto(self._addr,b'\xfd')     # 0xFD高精度测量指令
        time.sleep_ms(10)                         # 高精度测量需要9ms 
        self._i2c.readfrom_into(self._addr,self._buf)
        if crc:
            if not self._crc(): return None, None # 校验不正确返回None  
        t_ticks = self._buf[0] * 256 + self._buf[1]
        rh_ticks = self._buf[3] * 256 + self._buf[4]        
        t_degC = 175 * t_ticks/65535 - 45         # 温度测量结果
        rh_pRH = 125 * rh_ticks/65535 -6
        rh_pRH = int(min(100,max(0,rh_pRH)))      # 湿度测量结果
        return t_degC,rh_pRH
    
    def _crc(self):                               # 校验2组测量数据
        for n in range(0,4,3):            
            crc = 0xFF                            # 校验初始值        
            for i in range(n,n+2):                # 分别计算两个字节                
                crc ^= self._buf[i]               # 与一个字节异或
                for j in range(8):                # 进行8次循环移位和判断
                    if crc & 0x80:                # 检查最高位是否为1
                        crc=(crc<<1)^0x31         # 左移1位并异或多项式0x31
                    else:  crc<<=1                # 仅左移           
            if crc & 0xff != self._buf[n+2]:      # 任何一个通不过校验，就返回False
                return False 
        return True
                
if __name__ == '__main__':
    from machine import I2C
    i2c = I2C(0,scl=32,sda=33)
    sht40 = SHT4X(i2c)
    while True:
        t,h = sht40.measure(True)
        if t and h:
            print(f'{t:.2f},{int(h)} \r',end='')
        time.sleep(1)
    