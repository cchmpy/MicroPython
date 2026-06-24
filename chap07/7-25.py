from esp32 import RMT
from time import sleep_ms
from micropython import const
import asyncio
_BURST = const(560)                                        # 突发脉冲高电平持续时间us 
class IrTxNec:
    def __init__(self,pin_tx,rmt_id=0):
        self._pin_tx = pin_tx 
        self._rmt = RMT(rmt_id,pin=pin_tx,clock_div=80,tx_carrier=(38000, 33, 1))      # 定义rmt对象
        self._buf = [0 for _ in range(2+32*2+1)]           # 保存指令码序列高低电平的持续时长,单位us 
        self._buf[0]= 9000                                 # 引导码高电平时长9ms
        self._buf[1]= 4500                                 # 引导码低电平时长4.5ms
        self._buf[-1] = _BURST                             # 结束码高电平时长 
        self._rpt_buf = (9000,2250,_BURST)                 # 重复码序列高-低-高电平持续时长 
        self._data=bytearray(4)                            # 保存地址码和指令码
    
    def _encode(self,addr,cmd):                            # 对地址和指令进行编码
        self._data[0] = addr & 0xFF                        # 地址码/地址码低8位
        self._data[1] = (addr ^ 0xFF) if addr<256 else (addr>>8)     # 地址码反码/地址码高8位
        self._data[2] = cmd & 0xFF                         # 指令码
        self._data[3] = cmd ^ 0xFF                         # 指令码反码 
        for i in range(4):                                 # 计算地址和指令比特数据的电平持续时间
            for j in range(8):
                k = 2+i*16+j*2
                self._buf[k] = _BURST                                # 二进制1和0,高电平持续时长相同
                self._buf[k+1]= _BURST*(1+((self._data[i]>>j)&1)*2)  # 二进制1和0,低电平持续时长不同
        return sum(self._buf)//1000                        # 返回指令码序列的总时长ms
                
    def send(self, addr, cmd):                             # 阻塞模式发送
        d=self._encode(addr,cmd) 
        self._rmt.write_pulses(self._buf,1)                # 开始发送脉冲序列 
        while not self._rmt.wait_done(): sleep_ms(d)       # 阻塞等待发送完成
            
    async def asend(self, addr, cmd, repeat=0):            # 异步模式发送。repeat是重复码的发送次数
        d=self._encode(addr,cmd)
        self._rmt.write_pulses(self._buf,1) 
        while not self._rmt.wait_done():
            await asyncio.sleep_ms(d+2) 
        if repeat:
            await asyncio.sleep_ms(110-d)                  # 指令码发送开始后110ms后才能发送重复码
            for i in range(repeat): 
                self._rmt.write_pulses(self._rpt_buf,1)
                while not self._rmt.wait_done():
                    await asyncio.sleep_ms(13)             # 重复码序列时长约为11.81ms
                if i<repeat-1: await asyncio.sleep_ms(97)  # 发送下一个重复码前需等待97ms(110-13)            
if __name__=='__main__':
    import ir_rx_nec                                       # 导入程序7-24.py（ir_rx_nec.py）
    # 红外接收----------------------------------------------
    def callback(data):                                    # 定义红外数据处理函数
        addr,cmd,repeat = data
        print(hex(addr),cmd,repeat)
    irrx = ir_rx_nec.IrRxNec(22)                           # 红外接收对象
    irrx.set_callback(callback)                            # 用户接口函数 
    # 阻塞发射----------------------------------------------
    irtx = IrTxNec(23)                                     # 红外发射对象
    cmd = [i for i in range(20)]                           # 待发送的指令码
    for c in cmd:
        irtx.send(90,c)                                    # 地址90 
        sleep_ms(300)
    # 异步发射----------------------------------------------
    async def task(addr,repeat):                           # 定义异步红外发射函数,每1秒发射1次
        global irtx,cmd
        for c in cmd:
            await irtx.asend(addr,c,repeat) 
            await asyncio.sleep(1)
    asyncio.run(task(9000,1))                              # 地址码9000,发射1次重复码
