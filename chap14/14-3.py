from micropython import const
from struct import unpack, pack_into
from machine import Pin
import time
# 寄存器地址
_SYSRANGE_START    = const(0x00)        # 测量模式，1：单次测量，2：最大频率连续测量，4：计时连续测量
_THRESH_HIGH       = const(0x0C)        # 高范围比较阈值，用于中断,双字节
_THRESH_LOW        = const(0x0E)        # 低范围比较阈值，用于中断,双字节
_MSRC_CONFIG       = const(0x60)        # MSRC_CONFIG_CONTROL
_FINAL_RATE_RTN_LIMIT = const(0x44)     # 最终测量信号速率限制
_SYSTEM_SEQUENCE   = const(0x01)        # SYSTEM_SEQUENCE_CONFIG 测量序列设置
# SPAD阵列（单光子雪崩二极管）
_SPAD_REF_START    = const(0x4F)        # DYNAMIC_SPAD_REF_EN_START_OFFSET
_SPAD_ENABLES      = const(0xB0)        # GLOBAL_CONFIG_SPAD_ENABLES_REF_0
_REF_EN_START_SELECT  = const(0xB6)     # GLOBAL_CONFIG_REF_EN_START_SELECT
_SPAD_NUM_REQUESTED   = const(0x4E)     # DYNAMIC_SPAD_NUM_REQUESTED_REF_SPAD

_INTERRUPT_GPIO     = const(0x0A)       # 中断设置
_INTERRUPT_CLEAR    = const(0x0B)       # 中断清理
_GPIO_MUX_ACTIVE_HIGH = const(0x84)     # GPIO_HV_MUX_ACTIVE_HIGH Gpio
_RESULT_INTERRUPT_STATUS=const(0x13)    # 测量结果的中断状态
_RESULT_RANGE       = const(0x1E)       # 测量结果,双字节
_OSC_CALIBRATE      = const(0xF8)       # 测量周期的偏移校准量
_MEASURE_PERIOD     = const(0x04)       # 测量周期
_I2C_SLAVE_ADDRESS  = const(0x8A)       # I2C地址

class VL53L0X:
    # 中断模式，对应寄存器：_INTERRUPT_GPIO 
    INT_DISABLED     = const(0)         # 禁用中断
    INT_LESS_LOW     = const(1)         # 当value<thresh_low时触发
    INT_GREATER_HIGH = const(2)         # 当value>thresh_high时触发
    INT_OUTOF_THR    = const(3)         # 当value<thresh_low OR value>thresh_high时触发
    INT_DATA_RDY     = const(4)         # 当测量数据就绪时触发
    
    def __init__(self, i2c, address=0x29, timeout_ms=0, gpio1=None):        
        self._byte = bytearray(1)       # 读写寄存器缓存
        self._word = bytearray(2)
        self._dword= bytearray(4) 
        self._i2c = i2c 
        self._adr = 0x29                                    # 上电默认地址
        # 设置新地址时，必须把该I2C总线上的地址为0x29的其它设备关闭（xshut引脚拉低）
        if self._adr != address:
            address &= 0x7F
            self._reg_byte(_I2C_SLAVE_ADDRESS, address)     # 设置新地址
            self._adr = address
        self._gpio1= None if gpio1 is None else Pin(gpio1,Pin.IN) # 中断引脚
        self._timeout_ms = timeout_ms                       # 测量超时
        self._continuous_mode = False                       # 连续测量模式或连续定时测量模式
        self.init()                                         # 初始化
   
    def _reg_byte(self,reg,val=None):                       # 寄存器单字节读写
        if val is None:                                     # 读取
            self._i2c.readfrom_mem_into(self._adr,reg,self._byte)
            return self._byte[0]
        else:                                               # 写入
            self._byte[0] = val
            self._i2c.writeto_mem(self._adr,reg,self._byte) 

    def _reg_word(self,reg,val=None):                       # 寄存器双字节读写
        if val is None:                                     # 读取
            self._i2c.readfrom_mem_into(self._adr,reg,self._word)
            return unpack('>H',self._word)[0]
        else:                                               # 写入
            pack_into('>H',self._word,0,val)
            self._i2c.writeto_mem(self._adr,reg,self._word)

    def _reg_dword(self,reg,val=None):                      # 寄存器四字节读写
        if val is None:                                     # 读取
            self._i2c.readfrom_mem_into(self._adr,reg,self._dword)
            return unpack('>I',self._dword)[0]
        else:                                               # 写入
            pack_into('>I',self._dword,0,val)
            self._i2c.writeto_mem(self._adr,reg,self._dword)

    def _reg_bit(self, reg=0x00, bit=0, val=None):          # 查询或设置8位寄存器某位的值
        data = self._reg_byte(reg)                          # 读取寄存器值
        mask = 1 << bit                                     # bit位掩码
        if val is None:  return bool(data & mask)
        elif val: data |= mask                              # bit位设为1
        else:    data &= ~mask                              # bit位设为0
        self._reg_byte(reg,data) 

    def _write_regs(self, *config):                         # 写入多个8位寄存器
        for reg, val in config: self._reg_byte(reg, val)

    def init(self): 
        # I2C标准模式
        self._write_regs((0x88, 0x00),(0x80, 0x01),(0xFF, 0x01),(0x00, 0x00))
        self._stop_variable = self._reg_byte(0x91)
        self._write_regs((0x00, 0x01),(0xFF, 0x00),(0x80, 0x00))  
        # 禁用signal_rate_msrc(bit1)和signal_rate_pre_range(bit4)限制检查
        self._reg_bit(_MSRC_CONFIG, 1, True)
        self._reg_bit(_MSRC_CONFIG, 4, True)
        # 设置最终测量信号速率限制为0.25 MCPS (million counts per second)
        self._reg_word(_FINAL_RATE_RTN_LIMIT, 32)           # 0.25*(1 << 7)=32
        self._reg_byte(_SYSTEM_SEQUENCE, 0xFF)
        spad_count, spad_is_aperture = self._spad_info() 
        # 读取SPAD map (RefGoodSpadMap)
        spad_map = bytearray(6)                             # 6字节
        self._i2c.readfrom_mem_into(self._adr,_SPAD_ENABLES,spad_map) 
        # 设置spad参考（set reference spads）
        self._write_regs((0xFF, 0x01),(_SPAD_REF_START, 0x00), (_SPAD_NUM_REQUESTED, 0x2c),
                   (0xFF, 0x00), (_REF_EN_START_SELECT, 0xb4)) 
        spads_enabled = 0
        first_spad_to_enable = 12 if spad_is_aperture else 0
        for i in range(48):
            if i < first_spad_to_enable or spads_enabled == spad_count:
                spad_map[(i // 8)] &= ~(1 << (i % 8))
            elif (spad_map[(i // 8)] >> (i % 8)) & 0x1 > 0:
                spads_enabled += 1
        self._i2c.writeto_mem(self._adr,_SPAD_ENABLES, spad_map) 
        self._write_regs(
            (0xFF, 0x01), (0x00, 0x00),
            (0xFF, 0x00), (0x09, 0x00), (0x10, 0x00),
            (0x11, 0x00), (0x24, 0x01), (0x25, 0xFF), (0x75, 0x00),
            (0xFF, 0x01), (0x4E, 0x2C), (0x48, 0x00), (0x30, 0x20),

            (0xFF, 0x00), (0x30, 0x09), (0x54, 0x00), (0x31, 0x04),
            (0x32, 0x03), (0x40, 0x83), (0x46, 0x25), (0x60, 0x00),
            (0x27, 0x00), (0x50, 0x06), (0x51, 0x00), (0x52, 0x96),
            (0x56, 0x08), (0x57, 0x30), (0x61, 0x00), (0x62, 0x00),
            (0x64, 0x00), (0x65, 0x00), (0x66, 0xA0),

            (0xFF, 0x01), (0x22, 0x32), (0x47, 0x14), (0x49, 0xFF), (0x4A, 0x00),
            (0xFF, 0x00), (0x7A, 0x0A), (0x7B, 0x00), (0x78, 0x21),
            (0xFF, 0x01), (0x23, 0x34), (0x42, 0x00), (0x44, 0xFF), (0x45, 0x26),
            (0x46, 0x05), (0x40, 0x40), (0x0E, 0x06), (0x20, 0x1A), (0x43, 0x40),
            (0xFF, 0x00), (0x34, 0x03), (0x35, 0x44),
            (0xFF, 0x01), (0x31, 0x04), (0x4B, 0x09), (0x4C, 0x05), (0x4D, 0x04),
            (0xFF, 0x00), (0x44, 0x00), (0x45, 0x20), (0x47, 0x08), (0x48, 0x28),
            (0x67, 0x00), (0x70, 0x04), (0x71, 0x01), (0x72, 0xFE), (0x76, 0x00), (0x77, 0x00),
            (0xFF, 0x01), (0x0D, 0x01),
            (0xFF, 0x00), (0x80, 0x01), (0x01, 0xF8),
            (0xFF, 0x01), (0x8E, 0x01), (0x00, 0x01), (0xFF, 0x00), (0x80, 0x00),) 
        self.interrupt_config(INT_DATA_RDY)                 # 设置默认中断类型：采样数据就绪
        self._reg_bit(_GPIO_MUX_ACTIVE_HIGH, 4, False)      # active low
        self._reg_byte(_INTERRUPT_CLEAR, 0x01)              # 清理中断
        self._reg_byte(_SYSTEM_SEQUENCE, 0x01)
        self._calibrate(0x40)
        self._reg_byte(_SYSTEM_SEQUENCE, 0x02)
        self._calibrate(0x00)
        self._reg_byte(_SYSTEM_SEQUENCE, 0xe8)

    def _spad_info(self):                                   # 单光子雪崩二极管信息
        self._write_regs((0x80, 0x01),(0xFF, 0x01),(0x00, 0x00),(0xFF, 0x06))
        self._reg_bit(0x83, 2, True) 
        self._write_regs((0xFF, 0x07),(0x81, 0x01),(0x80, 0x01),(0x94, 0x6b),(0x83, 0x00))
        start = time.ticks_ms()
        while self._reg_byte(0x83) == 0: self._check_timeout(start)
        self._reg_byte(0x83, 0x01)
        value = self._reg_byte(0x92)
        count = value & 0x7f
        is_aperture = bool(value & 0x80) 
        self._write_regs((0x81, 0x00),(0xFF, 0x06))
        self._reg_bit(0x83, 2, False)
        self._write_regs((0xFF, 0x01),(0x00, 0x01),(0xFF, 0x00),(0x80, 0x00)) 
        return count, is_aperture

    def _calibrate(self, vhv_init_byte):                    # 校准
        self._reg_byte(_SYSRANGE_START, 0x01 | vhv_init_byte & 0xFF)        
        if self._int_mode==INT_DATA_RDY:                    # 初始化时，默认设置INT_DATA_RDY中断模式
            start = time.ticks_ms()
            while self._reg_byte(_RESULT_INTERRUPT_STATUS) & 0x07 == 0:
                self._check_timeout(start)  
            self._reg_byte(_INTERRUPT_CLEAR, 0x01)
        self._reg_byte(_SYSRANGE_START, 0x00)

    def _check_timeout(self,start):                         # 检测测量是否超时
        if (self._timeout_ms > 0
            and time.ticks_diff(time.ticks_ms(), start) >= self._timeout_ms):
            raise RuntimeError("Timeout waiting for VL53L0X!")
   
    def interrupt_config(self,mode=INT_DATA_RDY,*,handle=None,thresh_low=200,thresh_high=800):
    # 设置中断模式和回调函数
        if mode==INT_LESS_LOW:
            self._reg_word(_THRESH_LOW,thresh_low//2)       # 实际距离是参数*2
        elif mode==INT_GREATER_HIGH:
            self._reg_word(_THRESH_HIGH,thresh_high//2) 
        elif mode==INT_OUTOF_THR:
            self._reg_word(_THRESH_LOW,thresh_low//2)
            self._reg_word(_THRESH_HIGH,thresh_high//2)
        self._int_mode = mode                               # 保存中断模式成员变量
        self._reg_byte(_INTERRUPT_GPIO, mode)               # 设置中断模式
        if self._gpio1 is not None:
            self._gpio1.irq(handle,trigger=Pin.IRQ_FALLING) # 设置中断回调 

    def range_continuous(self, period_ms=0):                # 启动连续测距或连续定时测距
        self._write_regs((0x80, 0x01),(0xFF, 0x01),(0x00, 0x00),(0x91, self._stop_variable),
                    (0x00, 0x01),(0xFF, 0x00),(0x80, 0x00))
        if period_ms:
            oscilator = self._reg_word(_OSC_CALIBRATE)
            if oscilator: period_ms *= oscilator 
            self._reg_dword(_MEASURE_PERIOD, period_ms) 
            self._reg_byte(_SYSRANGE_START, 0x04)           # 启动连续定时测距
        else:
            self._reg_byte(_SYSRANGE_START, 0x02)           # 启动连续测距（以尽可能快的速度）
        self._continuous_mode = True

    def range_stop(self):                                   # 停止连续测距
        self._reg_byte(_SYSRANGE_START, 0x01)               # 停止当前测量状态
        self._write_regs((_SYSRANGE_START, 0x01),(0xFF, 0x01), (0x00, 0x00),(0x91,
                     self._stop_variable), (0x00, 0x01),(0xFF, 0x00))
        self._continuous_mode = False

    def range_single(self):                                 # 启动单次测距
        if self._continuous_mode:
            self.range_stop()                               # 停止连续测量 
        self._write_regs((0x80, 0x01),(0xFF, 0x01),(0x00, 0x00), (0x91, self._stop_variable),
                    (0x00, 0x01),(0xFF, 0x00),(0x80, 0x00), (_SYSRANGE_START, 0x01))
        start = time.ticks_ms()
        while (self._reg_byte(_SYSRANGE_START) & 0x01)>0:   # 等待模块固件自动清除bit0位，<=1ms
            self._check_timeout(start)

    def read_in_poll(self): # 在轮询方式中读取数据
        # 非INT_DATA_RDY中断模式，因触发条件限制，不能通过_RESULT_INTERRUPT_STATUS查询测量是否完成。
        if self._int_mode==INT_DATA_RDY: 
            start = time.ticks_ms()    
            while (self._reg_byte(_RESULT_INTERRUPT_STATUS) & 0x07) == 0:
                self._check_timeout(start) 
        data = self._reg_word(_RESULT_RANGE)               # 读取结果,单位mm
        if self._int_mode:
            self._reg_byte(_INTERRUPT_CLEAR, 0x01)         # 清理中断状态，为下次中断触发准备条件
        return data

    def read_in_callback(self):                            # 在中断回调中读取数据
        # 中断触发，则必然完成测距，直接读取即可 
        data = self._reg_word(_RESULT_RANGE) 
        self._reg_byte(_INTERRUPT_CLEAR, 0x01)             # 清理中断状态
        return data
