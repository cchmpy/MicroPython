from micropython import const
_GPIO_OUT_REG    = const(0x3FF44004)  # GPIO 0-31 输出寄存器地址
_GPIO_ENABLE_REG = const(0x3FF44020)  # GPIO 0-31 输出使能寄存器地址
_M23 = const(1 << 23)                 # Pin(23)引脚的位掩码

@micropython.viper
def toggle_n(n: int):
    p_enb = ptr32(_GPIO_ENABLE_REG)   # p_enb指向输出使能寄存器
    p_out = ptr32(_GPIO_OUT_REG)      # p_out指向输出寄存器 
    p_enb[0] |= _M23                  # 23引脚输出使能 
    for _ in range(n):
        p_out[0] ^= _M23              # 23引脚交替输出高低电平
toggle_n(100)
