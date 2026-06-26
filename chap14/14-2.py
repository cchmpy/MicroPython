from struct import unpack
import time, collections, math
from micropython import const
from machine import I2C
# 主要寄存器地址
_PWR_MGMT_1  = const(0x6B)                 # 电源管理1：重置\睡眠\循环\禁用测温\时钟源
_PWR_MGMT_2  = const(0x6C)                 # 电源管理2: 低功耗模式\加速度和陀螺仪待机
_SMPRT_DIV   = const(0x19)                 # 采样率分频器
_CONFIG      = const(0x1A)                 # 外部帧同步（FSYNC）引脚采样和数字低通滤波器（DLPF）
_GYRO_CONFIG  = const(0x1B)                # 陀螺仪自检和量程
_ACCEL_CONFIG = const(0x1C)                # 加速度计自检和量程

_FF_THR     = const(0x1D)                   # 自由落体检测中断 加速度阈值
_FF_DUR     = const(0x1E)                   # 自由落体检测中断 时间阈值
_MOT_THR    = const(0x1F)                   # 运动检测中断 加速度阈值
_MOT_DUR    = const(0x20)                   # 运动检测中断 时间阈值
_ZRMOT_THR   = const(0x21)                  # 零运动检测中断 加速度阈值
_ZRMOT_DUR   = const(0x22)                  # 零运动检测中断 时间阈值
_INT_ENABLE  = const(0x38)                  # 中断使能寄存器
_INT_STATUS  = const(0x3A)                  # 中断状态寄存器

_ACCEL_OUT_BEG = const(0x3B)                # 自此开始的14字节数据是加速度、温度、陀螺仪的测量数据
_MOT_STATUS    = const(0x61)                # 运动检测中断时的状态（运动的轴和极性）
_SIGNAL_PATH_RESET = const(0x68)            # 传感器信号路径复位

# 量程
_ACCEL_RANGE = [2, 4, 8, 16]                # 加速度计量程，单位:g
_GYRO_RANGE  = [250, 500, 1000, 2000]       # 陀螺仪量程，单位:度/秒
# 定义命名元组类型，方便访问单项数据，在MPU6050.read_named_data()中使用
_SensorData = collections.namedtuple('SensorData',['aX','aY','aZ','Temp','gX','gY','gZ'])

class MPU6050:
    # _INT_ENABLE(0x38)寄存器，中断对应bit位:
    INT_FF_BIT  = const(7)                  # 自由落体中断位
    INT_MOT_BIT = const(6)                  # 运动/加速度中断位
    INT_ZEMOT_BIT    = const(5)             # 静止中断位
    INT_DATA_RDY_BIT = const(0)             # 数据就绪位中断
    # _PWR_MGMT_2寄存器，低功耗模式的唤醒频率LOW_POWER_RATE:
    LPR_1P25 = const(0)                     # 1.25Hz
    LPR_5   = const(1)                      # 5Hz
    LPR_20  = const(2)                      # 20Hz
    LPR_40  = const(3)                      # 40Hz
    # 高通和低通滤波器参数常量,可在此自行定义
    ...
    def __init__(self,i2c:I2C, address=0x68, rate=200):
        self._i2c  = i2c
        self._adr  = address
        self._rate  = rate                  # 采样率，采样率分频器：SMPLRT_DIV=(8k or 1k)/rate-1
        # 读写数据的缓存
        self._byte = bytearray(1)           # 写入单字节数据的缓存
        self._word = bytearray(2)           # 写入双字节数据的缓存
        self._data = bytearray(14)          # 保存加速度、温度、陀螺仪的7个数据：aX,aY,aZ,Temp,gX,gY,gZ
        # 计算姿态角（欧拉角）的辅助变量
        self._last_ms = 0                   # 上次time.ticks_ms()
        self._q_sum = [0, 0]                # 辅助计算加速度计测量的姿态角,平方和quadratic sum 
        self._acc_a = [0, 0, 0]             # 加速度计测量的姿态角,_acc_angles
        self._gyr_a = [0, 0, 0]             # 陀螺仪测量的姿态角,_gyr_angles
        self.angles = [0, 0, 0]             # 互补滤波计算后的姿态角
        
        self._offset = [0,0,0,0,0,0,0]      # 校准偏移量，校准后的值=测量值-offset[i]
        self.init()                         # 初始化,进入正常工作状态 
    
    def _read_byte(self,reg):               # 读取寄存器的一个字节
        self._i2c.readfrom_mem_into(self._adr,reg,self._byte)
        return self._byte[0]
    
    def _write_byte(self,reg,val):          # 写入一个字节到寄存器
        self._byte[0] = val
        self._i2c.writeto_mem(self._adr,reg,self._byte)
    
    def _read_word(self,reg,signed=True):   # 读取寄存器的一个字/2字节
        self._i2c.readfrom_mem_into(self._adr,reg,self._word)
        fmt = '>h' if signed else '>H'      # 是不是有符号整数
        return unpack(fmt,self._word)[0]
    
    def _set_bitfield(self, reg, high_bit, bit_width, val):  # 设置8位寄存器某一区间字段的值 
        # high_bit：待设字段的高比特位，bit_width：待设字段宽度，val：待设值
        if high_bit>7 or high_bit<0 or bit_width>8 or bit_width<0:
            raise ValueError('high_bit or bit_width is invalid value')
        old = self._read_byte(reg)
        shift = high_bit - bit_width + 1                     # 左移位数
        mask = (2**bit_width - 1) << shift                   # 字段掩码，待设字段为1，其余为0
        new = (old & ~mask) | (val << shift)
        self._write_byte(reg, new)
    
    def set_gyro_fsr(self, fsr=0):                           # 设置陀螺仪量程 full scale range
        # fsr：0(±250°/s),1(±500),2(±1000),3(±2000)
        self._gyro_range = _GYRO_RANGE[fsr]                  # 成员变量定义和赋值
        self._set_bitfield(_GYRO_CONFIG,4,2,fsr)             # 对应比特位：bit4 bit3
    
    def set_accel_fsr(self, fsr=0):                          # 设置加速度计量程
        # fsr：0(±2g),1(±4g),2(±8g),3(±16g)
        self._accel_range = _ACCEL_RANGE[fsr]
        self._set_bitfield(_ACCEL_CONFIG,4,2,fsr)            # 对应比特位：bit4 bit3
    
    def set_accel_dhpf(self, dhpf=1):                        # 设置加速度计高通滤波器 
        # dhpf：0-reset, 1-5Hz, 2-2.5Hz, 3-1.25Hz, 4-0.63Hz, 7-hold 
        self._set_bitfield(_ACCEL_CONFIG,2,3,dhpf)           # 对应比特位：bit2 bit1 bit0
    
    def set_dlph(self, dlpf=1):                              # 设置加速度计、陀螺仪的低通滤波器
        # dlpf:0～7，数值对应参数见前文说明
        self._write_byte(_CONFIG, dlpf)
        self.sample_rate(self._rate)                         # 要保持原有采样率，需要重新设置分频器
        
    def enable_low_power(self,rate=LPR_40):                  # 低功耗模式使能
        self._write_byte(_PWR_MGMT_1, 0x28)                  # 设置CYCLE=1、TEMP_DIS=1、SLEEP=0
        self._set_bitfield(_PWR_MGMT_2,7,2,rate)             # 设置唤醒频率
        self._set_bitfield(_PWR_MGMT_2,2,3,7)                # 禁用陀螺仪
    
    def disable_low_power(self):                             # 禁用低功耗模式
        self._write_byte(_PWR_MGMT_1, 0x01)                  # 设置CYCLE=0、TEMP_DIS=0、SLEEP=0
        self._write_byte(_PWR_MGMT_2, 0)                     # 启用加速度、陀螺仪 
    
    def sleep(self,stby=True):                               # 睡眠或唤醒
        self._set_bitfield(_PWR_MGMT_1,6,1,int(stby))        # 睡眠位bit6
    
    def reset(self):                                         # 设备重置
        self._set_bitfield(_PWR_MGMT_1,7, 1, 1)              # 设备重置位bit7
        time.sleep_ms(100)
        self._write_byte(_SIGNAL_PATH_RESET,0x07)            # 传感器信号路径复位
        time.sleep_ms(100) 
   
    def enable_interrupt(self, int_bit=INT_MOT_BIT, thr=6, dur=2): # 中断使能
        # thr:加速度阈值，单位是2mg/LSB； 
        # dur:时间阈值，零运动检测时单位是64毫秒/LSB，自由落体和运动检测单位是1毫秒/LSB
        if int_bit == INT_FF_BIT:      addr_thr,addr_dur=_FF_THR,_FF_DUR
        elif int_bit == INT_MOT_BIT:   addr_thr,addr_dur=_MOT_THR,_MOT_DUR
        elif int_bit == INT_ZEMOT_BIT: addr_thr,addr_dur=_ZRMOT_THR,_ZRMOT_DUR
        else:  addr_thr,addr_dur=None,None
        # 设置三种运动检测类型的加速度阈值和时间阈值
        if addr_thr and addr_dur:
            self._write_byte(addr_thr,thr) 
            self._write_byte(addr_dur,dur) 
        # 设置中断标志位
        self._set_bitfield(_INT_ENABLE,int_bit, 1, 1)
    
    def disable_interrupt(self,int_bit=None):                # 禁用中断
        if int_bit is None:  self._write_byte(_INT_ENABLE,0) # 禁用所有中断
        else: self._set_bitfield(_INT_ENABLE,int_bit, 1,0)   # 禁用某个中断
    
    def read_int_status(self):                               # 读取中断状态（中断类型）
        return self._read_byte(_INT_STATUS)
        
    def read_int_mot_status(self):                           # 读取运动中断时的状态(轴和极性)
        return self._read_byte(_MOT_STATUS)
        
    def sample_rate(self,rate=None):                         # 获取和设置采用率,单位Hz
        if rate is None: return self._rate
        self._rate = rate
        dlpf = self._read_byte(_CONFIG) & 0x07               # 读取低通滤波器设置
        g_o_rate = 1000                                      # 陀螺仪输出速率1Khz
        if dlpf==0 or dlpf==7: g_o_rate=8000                 # 陀螺仪输出速率8Khz
        self._write_byte(_SMPRT_DIV, int(g_o_rate/self._rate-1))   # 设置采样率分频器
        
    def init(self):                                          # 初始化
        self._write_byte(_PWR_MGMT_1, 0x01)                  # 设置时钟源，关闭睡眠
        self._write_byte(_PWR_MGMT_2, 0)                     # 加速度、陀螺仪传感器使能，0是默认值
        self.set_dlph(1)                  # 为加速度计和陀螺仪配置数字低通滤波器DLPF，同时设置采样率
        self.set_accel_dhpf(1)            # 为加速度计设置高通滤波器
        self.set_accel_fsr(0)             # 设置陀螺仪量程为±250°/s，默认值
        self.set_gyro_fsr(0)              # 设置加速度计量程为±2g，默认值
        
    def read_data(self,scaled=True):                         # 读取数据并校准，返回list
        self._i2c.readfrom_mem_into(self._adr,_ACCEL_OUT_BEG,self._data)
        data = list(unpack(">hhhhhhh", self._data))
        for i in range(7): data[i] -= self._offset[i]        # 校准值
        if scaled:                                           # 单位换算,加速度g，角速度度/秒
            data[0:3] = [x / (65536 // self._accel_range // 2) for x in data[0:3]]
            data[3] = data[3]/340 + 36.53
            data[4:7] = [x / (65536 // self._gyro_range // 2) for x in data[4:7]]
        return data
        
    def read_named_data(self,scaled=True):                   # 读取数据并校准,返回命名元组 
        return _SensorData(*self.read_data(scaled))          # *为解包运算符，把列表分解为多个独立数据
    
    def calibrate(self,num=100):                             # 校准，计算偏差量。num:采样数量
        time.sleep_ms(500)                                   # 等待系统稳定
        delay_ms = int(1000/self._rate+0.5)                  # 数据更新时间间隔(四舍五入)
        self.read_data(False)                                # 第一个数据不用
        for i in range(7):self._offset[i]=0                  # 清零
        for _ in range(num):
            self._i2c.readfrom_mem_into(self._adr,_ACCEL_OUT_BEG,self._data)
            data = unpack(">hhhhhhh", self._data)
            for i in range(7): self._offset[i] += data[i] 
            time.sleep_ms(delay_ms)
        for i in range(7):self._offset[i] = int(self._offset[i]/num+0.5)     # 计算平均
        # 找到重力加速度所在的轴（水平、垂直放置时不同）
        j=0
        for i in range(1,3):
            if abs(self._offset[j])<abs(self._offset[i]): j=i 
        self._offset[j] = self._offset[j]-(32768 // self._accel_range)
        self._offset[3]=0                                    # 温度偏差量
            
    def cpm_filter(self,R=0.98):                             # 互补滤波计算姿态角 Complementary Filter 
        data = self.read_data(True)                          # 读取单位换算后的数据
        # 计算加速度计测量的姿态角(无法计算yaw偏航角)
        for i in range(2):
            self._q_sum[i]=data[i]*data[i]+data[2]*data[2]
            self._acc_a[i]=math.degrees((1-i*2)*math.atan2(data[1-i],self._q_sum[i]))
        
        # 获取两次测量时间差dt
        now =time.ticks_ms()
        if self._last_ms==0:                                 # 首次计算
            self.angles=self._gyr_a=self._acc_a              # 陀螺仪姿态角的初始值
            self._last_ms=now
            return
        dt = time.ticks_diff(now,self._last_ms)/1000         # 必须换算为秒，因为角速度是度/秒
        self._last_ms=now
        
        # 计算陀螺仪测量的姿态角和互补滤波后的姿态角 
        for i in range(3): 
            self._gyr_a[i]+= dt*data[i+4]                           # 陀螺仪姿态角
            self.angles[i]= R*self._gyr_a[i]+(1-R)*self._acc_a[i]   # 互补滤波姿态角
        
        if self.angles[2]>=360:
            self.angles[2]%=360
        elif self.angles[2]<=-360:
            self.angles[2]+=360*(self.angles[2]//(-360))
        return self.angles 
        
if __name__ == '__main__':                                   # 驱动程序使用示例
    from machine import Pin 
    mpu = MPU6050(I2C(0,scl=Pin(26), sda=Pin(27)))
    mpu.sample_rate(100)                                     # 设置采样率 
    mpu.calibrate()                                          # 校准
    print('Get ready!')
    mpu.enable_interrupt(MPU6050.INT_DATA_RDY_BIT)           # 数据就绪中断
    mpu.enable_interrupt(MPU6050.INT_ZEMOT_BIT,5,10)         # 零运动检测中断
    
    i=0 
    def cb(_):                                               # 中断回调函数
        global mpu,i
        int_status = mpu.read_int_status()                   # 读取中断状态
        if int_status & 0x01:                                # 数据就绪中断
            mpu.cpm_filter()                                 # 计算姿态角
        if int_status & 0x20:                                # 零运动检测中断
            i+=1
            print(i,'ZRMOT',hex(mpu.read_int_mot_status()))
    
    p23 = Pin(23,mode=Pin.IN)
    p23.irq(handler=cb, trigger=Pin.IRQ_RISING)
    while True:
        try:                                                 # 打印姿态角
            time.sleep_ms(500)
            print(f'roll:{mpu.angles[0]:.1f},pitch:{mpu.angles[1]:.1f},yaw:{mpu.angles[2]:.1f}')
        except KeyboardInterrupt: 
            mpu.disable_interrupt()                         # 禁用所有中断
            mpu.sleep(True); break 
