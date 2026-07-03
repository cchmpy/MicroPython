from esp32 import ULP
from machine import mem32,ADC
from esp32_ulp import src_to_binary
import time
source = '''\
data:   .long 0                            # 定义变量，保存测量结果 
entry:  move r3, data                      # R3保存data的地址
        adc r1,0,5                         # 测量ADC1_CH4/GPIO32管脚模拟量，保存至r1 
        st r1, r3, 0                       # 把r1保存到data ([r3+0])
        halt                               # 停止，直到ulp再次被唤醒
'''
ADC(32,atten=ADC.ATTN_11DB)                # 初始化ADC通道，确保ulp中测量结果符合预期
binary = src_to_binary(source,cpu='esp32') # 编译汇编程序
load_addr, entry_addr = 0, 4               # 程序被载入的地址、运行入口地址

ulp = ULP()                                # 定义ULP对象
ulp.set_wakeup_period(0, 500_000)          # 使用SENS_ULP_CP_SLEEP_CYC0_REG寄存器保存唤醒周期(500ms)
ulp.load_binary(load_addr, binary)         # 加载汇编程序的机器码
ulp.run(entry_addr)                        # 启动定时器，ULP-FSM开始运行程序

while True:
    print(f'{mem32[0x5000_0000] & 0xffff:4}\r',end='')  # 打印ULP-FSM测量的结果
    time.sleep(0.5)
