from esp32 import ULP,wake_on_ulp
from machine import mem32,ADC,lightsleep,deepsleep,RTC
from esp32_ulp import src_to_binary
import time
source = '''\
#define RTC_CNTL_LOW_POWER_ST_REG     0x3FF480C0  # RTC低功耗控制寄存器地址
#define RTC_CNTL_RDY_FOR_WAKEUP       (BIT(19))   # RTC是否准备好被任何唤醒源唤醒的标志位    
#define RTC_CNTL_MAIN_STATE_IN_IDLE   (BIT(27))   # 芯片是否处于睡眠模式，0睡眠，1正常

    .set adc_channel, 4             # ADC1_CH4  GPIO32
    .set factor_log, 2              # 幂
    .set factor, (1 << factor_log)  # 采样次数2^factor_log，用于计算平均值
    .set low_thr, 500               # 测量结果的低阈值,低于该值唤醒系统
    .set high_thr, 3800             # 测量结果的高阈值,高于该值唤醒系统

    .text
result:  .long 0                    # 最终测量结果
entry:    
    move r0, 0                      # r0用于累加器   
    stage_rst                       # 重置计时器
measure:    
    adc r1, 0, adc_channel + 1      # 读取测量值
    add r0, r0, r1                  # 累加测量结果r0=r0+r1    
    stage_inc 1                     # 计时器增加1
    jumps measure, factor, lt       # 如果次数不够，继续测量

    rsh r0, r0, factor_log          # 移位，计算平均值    
    move r3, result                 # 将resutl变量的地址保存到r3
    st r0, r3, 0                    # 平均值现在r0中,将其存储到result中

    jumpr wake_up,low_thr,lt        # 如果测量值r0<low_thr, 则唤醒系统
    jumpr wake_up,high_thr,gt       # 如果测量值r0>high_thr, 则唤醒系统    
    jump exit                       # 如果测量值在区间内，则结束程序 
wake_up:    
    #检查系统是否准备好被唤醒    
    READ_RTC_FIELD(RTC_CNTL_LOW_POWER_ST_REG, RTC_CNTL_MAIN_STATE_IN_IDLE)  # 是否睡眠
    jumpr exit, 1, eq                                                       # 若处于正常模式,直接退出
    READ_RTC_FIELD(RTC_CNTL_LOW_POWER_ST_REG, RTC_CNTL_RDY_FOR_WAKEUP)      # 是否可以唤醒
    jumpr exit, 0, eq                                                       # 若不能唤醒  
    wake
exit:    
    halt
'''
adc=ADC(32,atten=ADC.ATTN_11DB)           # 初始化ADC通道
binary = src_to_binary(source,cpu='esp32')# 编译汇编程序
load_addr, entry_addr = 0, 4              # 程序被载入的地址、运行入口地址

wake_on_ulp(True)                         # 设置ulp唤醒源
ulp = ULP()                               # 定义ULP对象
ulp.set_wakeup_period(0, 500_000)         # 设置唤醒用寄存器和周期(5000ms)
ulp.load_binary(load_addr, binary)        # 加载汇编程序的机器码
ulp.run(entry_addr)                       # 启动定时器，ULP-FSM开始运行程序
print('Zzzz...')
time.sleep(0.1)
lightsleep(10000)                         # 进入睡眠
while True:
    print(f'{mem32[0x5000_0000] & 0xffff:4}\r',end='')  # 打印ULP-FSM测量的结果
    time.sleep(0.5)
