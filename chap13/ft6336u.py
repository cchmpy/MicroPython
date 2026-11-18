from machine import Pin
from micropython import const
from time import sleep_ms
from math import atan2,pi
# 寄存器映射地址
_CIPHER_LOW = const(0xA0)                            # 芯片代号(低字节) 0x02-Ft6336U
_TD_STATUS  = const(0x02)                            # 触点数量
_P1_XH      = const(0x03)                            # 触点1信息起始地址,触点2:_P2_XH=_P1_XH+6
_G_MODE     = const(0xA4)                            # 报点模式（中断轮询、中断触发）
_PERIOD_A   = const(0x88)                            # 主动模式下的报点间隔时间(ms),有效值[8,200]
_PERIOD_M   = const(0x89)                            # 监控模式下的报点间隔时间(ms)
_PWR_MODE   = const(0xA5)                            # 电源/操作模式
_GEST_ENABLE= const(0xD0)                            # 特殊手势模式使能 1:启用,0:禁用
_GEST_ID    = const(0xD3)                            # 特殊手势ID

class TPoint():                                      # 触点类定义
    def __init__(self):
        self.id = self.x = self.y = 0                # 触点id，x/y坐标值
        self.event = 3                               # 事件类型（按下、提取、接触、无事件）
        self.gest = None                             # 保留使用，存储滑动手势（上下左右无） 
    def init(self,other):                            # 用其它TPoint类实例初始化
        self.id = other.id;
        self.x=other.x; self.y=other.y
        self.event = other.event
        self.gest = other.gest 
    def __repr__(self):                              # 字符串方法
        return f'id={self.id},x={self.x},y={self.y},event={self.event}'
    
class FT6336U():
    # 类常量:电源模式
    P_ACTIVE=const(0);     P_MONITOR=const(1)        # 主动\监控模式  
    P_STANDBY=const(2);    P_HIBERNATE=const(3)      # 待机模式\休眠
    # 类常量:触点事件
    E_PRESS_DOWN=const(0); E_LIFT_UP=const(1)        # 按下\提起事件
    E_CONTACT=const(2);    E_NO_EVENT=const(3)       # 接触事件\无事件
    # 类常量:报点(中断使用)模式
    M_IRQ=const(1);        M_POLLING=const(0)        # 中断触发\中断轮询
       
    # 类常量:部分特殊手势ID,也用于报点模式下的滑动方向检测
    GEST_NO = const(0x00)                            # 无手势/无滑动
    GEST_LEFT=const(0x20); GEST_RIGHT=const(0x21)    # 左滑/右滑
    GEST_UP=const(0x22);   GEST_DOWN=const(0x23)     # 上滑/下滑
    GEST_DBLCLK = const(0x24)                        # 双击   
   
    def __init__(self,i2c, irq, rst=None, addr=0x38,width=320,height=480):
        self._i2c=i2c; self._addr=addr               # I2C接口、I2C从机地址
        self._int = Pin(irq,mode=Pin.IN,pull=Pin.PULL_UP)                          # 中断引脚
        self._rst = Pin(rst,mode=Pin.OUT,pull=Pin.PULL_UP,value=0) if rst else rst # 复位引脚 
        self._w=width; self._h=height                # 触屏像素宽度\高度
        self._angle=0                                # 触屏顺时针旋转角度,只有4种情况（0,90,180,270)
        
        self._buf=bytearray(4); self._buf1=bytearray(1)  # 读取触点信息、单个寄存器的缓存 
        self._touch1=TPoint();  self._touch2=TPoint()    # 触点1、触点2对象
        self._start  = TPoint()                      # 用于滑动手势检测的开始触点
        
        if self._rst:                                # 复位操作 
            sleep_ms(10)                             # 脉冲宽度应>=5ms
            self._rst(1)                             # 拉高电平，完成复位
            sleep_ms(300)                            # 不低于300ms,等待内置MCU完成启动
        
    def _write(self,addr,data:int):                  # 向addr地址的寄存器写入1个字节数据 
        self._i2c.writeto_mem(self._addr,addr,data.to_bytes(1))
        
    def _readinto(self,addr,buf):                    # 从addr读取len(buf)个字节数据 
        self._i2c.readfrom_mem_into(self._addr, addr, buf)
        
    def _rw_reg(self,addr,v=None):                   # 读取/设置addr地址的寄存器数据
        if v is None:
            self._readinto(addr,self._buf1)          # 读取
            return self._buf1[0]                     # 返回
        self._write(addr,v)                          # 写入 
    
    def period_active(self,active_ms=None):          # 读取/设置主动模式下的报点间隔时间ms
        return self._rw_reg(_PERIOD_A,active_ms)
    def period_monitor(self,monitor_ms=None):        # 读取/设置监控模式下的报点间隔时间ms
        return self._rw_reg(_PERIOD_M,monitor_ms)
    def irq_mode(self,mode=None):                    # 读取/设置报点模式:中断触发或中断轮询
        return self._rw_reg(_G_MODE,mode)        
    def power_mode(self,mode=None):                  # 获取或设置操作（电源）模式
        rtn = self._rw_reg(_PWR_MODE,mode)
        if mode==self.P_STANDBY or mode==self.P_HIBERNATE:
            sleep_ms(100)                            # 等待进入待机或休眠模式
        return rtn
        
    def rotate (self,angle=None):                    # 获取和设置触摸屏相对默认值顺时针旋转角度
        if angle is None: return self._angle
        self._angle = angle%360//90*90               # 确保4种取值:0,90,180,270 
    
    def get_points(self):                            # 返回触点的数量
        return self._rw_reg(_TD_STATUS,None) 
    
    def get_touch(self,point=1):                     # 读取触点1(point<=1)和触点2(point>=2)的信息
        if point<=1: p=0; tp=self._touch1            # p用于计算地址,tp是保存触点数据的目标对象
        else:        p=1; tp=self._touch2  
        self._readinto(_P1_XH + p*6, self._buf)      # 从内存读取数据
        # 解析数据
        tp.event  = self._buf[0]>>6                                # 触点事件
        tp.x      = ((self._buf[0] & 0x0F) << 8) | self._buf[1]    # 触点x坐标
        tp.id     = self._buf[2]>>4                                # 触点id
        tp.y      = ((self._buf[2] & 0x0F) << 8) | self._buf[3]    # 触点y坐标
        # 根据触屏顺时针旋转角度转换坐标值
        if self._angle==0:     return tp
        elif self._angle==90:  tp.x=self._h-tp.y; tp.y=tp.x
        elif self._angle==180: tp.x=self._w-tp.x; tp.y=self._h-tp.y 
        elif self._angle==270: tp.x=tp.y;         tp.y=self._w-tp.x
        return tp  
                 
    def set_callback(self,cb=None):                   # 设置中断触发(报点时)的回调函数
        self._int.irq(cb,Pin.IRQ_RISING)              # 上升沿触发
    
    def set_slide_start(self):                        # 用触点1初始化滑动开始点 
        self._start.init(self._touch1)
        
    def get_slide_direc(self):                        # 触点1滑动的方向
        dy = self._start.y-self._touch1.y             # 当前点与起始点y坐标之差
        dx = self._touch1.x-self._start.x             # 当前点与起始点x坐标之差
        if abs(dy)<5 and abs(dx)<5: return GEST_NO    # 滑动距离小于5,无效
        a = atan2(dy, dx) * 180 / pi                  # 计算起点到终点方向射线的角度
        if -45 <= a < 45: return GEST_RIGHT           # 右滑
        elif 45 <= a < 135:return GEST_UP             # 上滑
        elif -135 <= a < -45: return GEST_DOWN        # 下滑
        elif (135 <= a < 180) or (-180 <= a < -135): return GEST_LEFT     # 左滑
        return GEST_NO                                # 其它各种错误或情况    
   
    def gesture_enable(self, on=True):                # 启用或禁用特殊手势模式 
        self._write(_GEST_ENABLE,int(on))
    def get_gesture_id(self):                         # 读取特殊手势模式的手势ID 
        return self._rw_reg(_GEST_ID,None)
    
if __name__=='__main__':
    import  time, sys
    from machine import I2C
    def touch_cb(_):                                  # 报点模式下的中断回调
        global ft
        cnt=ft.get_points(); t1=ft.get_touch(1)
        if cnt<=1:                                    # 当手指抬起时，触点数量是0
            if t1.event == ft.E_LIFT_UP:              # 手指提起 
                d = ft.get_slide_direc()              # 获取滑动方向 
                if d == ft.GEST_NO: print('单击',t1)  # 单击/无手势,进行相关操作 
                elif d== ft.GEST_RIGHT:print('右滑')  # 右滑
                elif d== ft.GEST_LEFT: print('左滑')  # 左滑
                elif d== ft.GEST_UP: print('上滑')    # 上滑
                elif d== ft.GEST_DOWN: print('下滑')  # 下滑 
            elif t1.event == ft.E_PRESS_DOWN:         # 手指按下
                ft.set_slide_start()                  # 设置滑动起点
            elif t1.event == ft.E_CONTACT: pass       # 接触
        elif cnt == 2:
            print(t1,ft.get_touch(2)) 
            
    i2c=I2C(0,scl=13,sda=12) 
    ft=FT6336U(i2c,rst=None,irq=14)   
    ft.set_callback(touch_cb) 
    try:           
        while True: time.sleep(1)
    except KeyboardInterrupt: sys.exit(0)
