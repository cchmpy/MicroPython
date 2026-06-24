import time
from struct import unpack
from machine import Pin
from micropython import const
_CALIB  = const(0x88)                          # 校验数据起始地址(0x88-0x9F)
_ID     = const(0xD0)                          # 设备id
_CTRL   = const(0xF4)                          # 测量控制:过采样分辨率、电源模式
_CONFIG = const(0xF5)                          # 系统设置:待机时间、滤波系数 
_PRESS  = const(0xF7)                          # 气压原始采样值(0xF7-0xF9)
_TEMP   = const(0xFA)                          # 温度原始采样值 (0xFA-0xFC)

class BMP280:
    '''BMP280的子类必需实现两个方法:_write(memaddr,value)和_read(memaddr,nbytes=1)''' 
    CASE_HANDHELD_LOW = (0x57, 0x28)           # 手持式低功耗(应用场景)
    CASE_HANDHELD_DYN = (0x2F, 0x10)           # 手持动态设备
    CASE_WEATHER      = (0x25, 0x00)           # 天气监测
    CASE_FLOOR        = (0x2F, 0x48)           # 电梯/楼层变化检测
    CASE_DROP         = (0x2B, 0x00)           # 跌落检测
    CASE_INDOOR       = (0x57, 0x10)           # 室内导航

    def __init__(self,case):
        self.reference = 101325                # 基准气压（Pa）,默认值是海平面标准大气压
        self.set_case(case)                    # 设置应用场景
        self.read_calibration_data()           # 读取校准数据
        time.sleep_ms(100)                     # 等待模块初始化完成才能测量（实测最少20ms）
    
    def reference_press(self, press=None):     # 读取或设置基准气压值(Pa),用于计算相对高度
        if press is None: return self.reference
        self.reference = press
    
    def set_case(self,case):                   # 设置应用场景
        self._write(_CTRL, case[0])            # 配置寄存器:温压分辨率，模式
        self._write(_CONFIG, case[1])          # 配置寄存器:待机时间、滤波系数
        
    def read_calibration_data(self):           # 读取校准数据，并动态添加为实例属性
        para = ('T1','T2','T3','P1','P2','P3','P4','P5','P6','P7','P8','P9') 
        for r in range(_CALIB,_CALIB+24,2):
            i = (r-_CALIB)//2
            if r==_CALIB or r==_CALIB+6:       # 0x88 0x8e
                setattr(self,para[i],unpack('<H',self._read(r, 2))[0])    # 等同于self.T1=value 
            else:
                setattr(self,para[i],unpack('<h',self._read(r, 2))[0]) 
    
    @micropython.native
    def get_measurements(self):                # 获取测量结果,返回气温、气压、相对高度
        d = self._read(_PRESS,6)               # 读取原始采样值 
        raw_p = (d[0] << 12) | (d[1] << 4) | (d[2] >> 4)                 # 气压原始值
        raw_t = (d[3] << 12) | (d[4] << 4) | (d[5] >> 4)                 # 温度原始值

        # 使用校验值计算温度
        var1 = (((raw_t >> 3) - (self.T1 << 1)) * self.T2) >> 11
        var2 = (((((raw_t>>4) - self.T1) * ((raw_t>>4)-self.T1))>>12)* self.T3) >> 14
        t_fine = var1 + var2
        temperature = ((t_fine * 5 + 128) >> 8) / 100                    # 最终温度值(摄氏度）

        # 使用校验值计算气压
        var1 = (t_fine>>1) - 64000
        var2 = (((var1>>2) * (var1>>2)) >> 11 ) * self.P6
        var2 = var2 + ((var1 * self.P5) << 1)
        var2 = (var2>>2)+(self.P4<<16)
        var1 = (((self.P3*((var1>>2)*(var1>>2))>>13)>>3) + (((self.P2) * var1)>>1))>>18
        var1 = ((32768+var1)*self.P1)>>15        
        if var1 == 0: return 0                 # 避免除以零
        p=((1048576-raw_p)-(var2>>12))*3125
        if p < 0x80000000:
            p = (p << 1) // var1
        else:
            p = (p // var1) * 2
        var1 = (self.P9 * (((p>>3)*(p>>3))>>13))>>12
        var2 = (((p>>2)) * self.P8)>>13
        pressure = p + ((var1 + var2 + self.P7) >> 4)                    # 最终气压值(Pa)
        altitude = 44330*(1-(pressure/self.reference)**(1/5.256))        # 计算相对参考点的高度(米)
        return temperature, pressure, altitude                           # 返回气温、气压、相对高度

class BMP280_SPI(BMP280):
    def __init__(self, spi, cs, case=BMP280.CASE_HANDHELD_DYN):
        self.spi = spi
        self.spi.init(baudrate=10_000_000)                # BMP280最高支持10Mhz
        self.cs  = Pin(cs,mode=Pin.OUT,value=1)           # 片选
        if self._read(_ID) != b'\x58':
            raise ValueError("This device might not be BMP280")
        self.buf = bytearray(6)                           # 用于读取6字节原始采样数据的缓冲
        super().__init__(case)                            # 调用父类构造方法，以设置和初始化传感器
    
    def _write(self, memaddr, value):                     # 向寄存器写入1个字节
        self.cs(0)
        self.spi.write((memaddr & 0x7F).to_bytes(1))      # 写入寄存器地址,地址最高为0表示写入
        self.spi.write(value.to_bytes(1))                 # 写入数据
        self.cs(1)
        
    def _read(self, memaddr, nbytes=1):                   # 读取寄存器nbytes个字节 
        self.cs(0)
        self.spi.write((memaddr | 0x80).to_bytes(1))      # 写入寄存器地址,地址最高为1表示读取
        if nbytes==6:
            self.spi.readinto(self.buf)                   # 减少因频繁读取6字节采样数据造成的内存碎片
            data = self.buf
        else:
            data = self.spi.read(nbytes)                   # 读取
        self.cs(1)
        return data

class BMP280_I2C(BMP280):
    def __init__(self, i2c, addr=0x76,case=BMP280.CASE_HANDHELD_DYN):
        self.i2c = i2c
        self.addr = addr 
        if self.addr not in self.i2c.scan():              # 检查设备是否在线
            raise ValueError(f"BMP280 not found at address 0x{addr:2x}") 
        if self._read(_ID) != b'\x58':
            raise ValueError("This device might not be BMP280")
        self.buf = bytearray(6)
        super().__init__(case)
        
    def _write(self, memaddr, value):                     # 写入寄存器1个字节 
        self.i2c.writeto_mem(self.addr, memaddr, value.to_bytes(1))
        
    def _read(self, memaddr, nbytes=1):                   # 读取寄存器nbytes个字节
        if nbytes==6:
            self.i2c.readfrom_mem_into(self.addr, memaddr, self.buf)
            return self.buf
        else:
            return self.i2c.readfrom_mem(self.addr, memaddr, nbytes) 

if __name__ == '__main__':
    from machine import I2C, SPI
    # ------------------I2C-------------------------------
#     i2c = I2C(0,scl=Pin(23), sda=Pin(22), freq=100000)   
#     bmp = BMP280_I2C(i2c)                                 # 使用默认地址0x76
    # ------------------SPI-------------------------------
    spi = SPI(1,baudrate=10_000_000,sck=23,mosi=22,miso=19)
    bmp = BMP280_SPI(spi,cs=21)
    # ------------------公共代码---------------------------
    bmp.set_case(bmp.CASE_FLOOR)            # 设置应用场景
    # 在地面开机后，等待2秒，用于计算并设置参考气压，以计算相对高度
    pa,n = 0, 10
    print('Reference pressure sampling...')
    for _ in range(n):
        pa += bmp.get_measurements()[1]                   # 测试气压值n次并累加
        time.sleep_ms(200)                                # 该场景测试速率是7.3Hz，需延时137ms以上
    bmp.reference_press(pa//n)                            # 设置参考气压
    while True:
        d = bmp.get_measurements()
        print(f'{d[0]:.2f}℃ {d[1]}Pa {d[2]:.2f}m      \r',end='')  # 实际应通过液晶屏显示
        time.sleep_ms(500)
