import time, network, asyncio
import sht4x, font16x16, ssd1306_i2c, myutils
from esp32 import wake_on_touch
from machine import I2C, TouchPad, deepsleep, mem32
from micropython import const

_RTC_CNTL_STORE0_REG = const(0x3FF4804C)                # 保留寄存器地址
lock = asyncio.Lock()                                   # 定义全局变量:互斥锁

async def aconnect_wifi(ssid,key,timeout=30):           # 异步连接WI-FI
    wlan = network.WLAN()
    wlan.active(True)    
    if not wlan.isconnected():
        wlan.connect(ssid, key)        
        timeout = timeout*1000
        start = time.ticks_ms()
        while not wlan.isconnected():
            await asyncio.sleep_ms(1000)                # 异步等待
            if time.ticks_diff(time.ticks_ms(),start)>=timeout:
                break                                   # 连接超时则退出循环
    if wlan.isconnected():
        print(wlan.ifconfig()[0])
    else:
        print('连接超时')
    return wlan
        
async def async_datetime(ssid, key, timezone=8):        # 异步更新时间日期
    last = mem32[_RTC_CNTL_STORE0_REG]                  # 读取上次时间校准的时间点
    if last>3600 and abs(time.time()-last)<86400:return # 非断电重启且距上次校准不超过1天,不同步     
    
    wlan = await aconnect_wifi(ssid,key)
    if wlan.isconnected():
        async with lock:                                # 同步时间时使用互斥锁,预防竟态条件
            myutils.sync_ntp(timezone)                  # 同步时间日期
            mem32[_RTC_CNTL_STORE0_REG] = time.time()   # 保存同步操作的时间点    
    wlan.disconnect()                                   # 断开连接
    wlan.active(False)                                  # 关闭射频
    
async def measure_display(seconds=60):
    TouchPad(4).config(300)                             # 触摸唤醒
    wake_on_touch(True)

    i2c = I2C(0,scl=32,sda=33)                          # oled与sht40共用I2C总线
    fbm=font16x16.File('gb16x16.bin')                   # fbm用于打开并读取汉字字库
    oled=ssd1306_i2c.SSD1306_I2C(i2c,font=fbm)          # oled显示对象
    oled.clear()                                        # 清屏
    sht40 = sht4x.SHT4X(i2c)                            # 温湿度传感器
    weedday = '一二三四五六天'                            # 用于显示星期几
    
    for i in range(seconds):                            # 测量、显示信息60秒
        async with lock:  t = time.localtime()          # 当前时间
        oled.text_gb16x16(f'{t[0]}年{t[1]:02}月{t[2]:02}日',8,0,alpha=False)
        oled.text_gb16x16(f'星期{weedday[t[6]]} {t[3]:02}:{t[4]:02}:{t[5]:02}',0,16,alpha=False)
        t,h = sht40.measure(False)                      # 测量温湿度（不校验数据）    
        oled.text_gb16x16(f'温度：{t:6.2f}℃\n湿度：{h:3}%',0,32,alpha=False)
        oled.show()                                     # 显示
        await asyncio.sleep(1)                          # 异步等待

    oled.power(False)                                   # 关闭显示屏电源
    fbm.deinit()                                        # 关闭字库文件          
    deepsleep()                                         # 休眠等待触摸唤醒
    
async def main():                                       # 定义主任务，聚合多个任务
    await asyncio.gather(
        async_datetime('CMCC-7LhU','8c8yzcb5'),
        measure_display(30))
    
asyncio.run(main())

    
 