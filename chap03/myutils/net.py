import network,ntptime,time,asyncio
from machine import RTC

# 配置STA模式（客户端，连接到现有Wi-Fi）
def connect_wifi(ssid='ssid',key='key',timeout=30):            # timeout是超时秒数
    sta = network.WLAN(network.STA_IF)                         # 创建STA接口对象
    sta.active(True)
    if not sta.isconnected():
        print(f'连接到{ssid}...')
        sta.connect(ssid, key)
        while not sta.isconnected() and timeout>0:             # 如果没有连接且不超时
            time.sleep(1); timeout -= 1 
    if sta.isconnected(): print(f"连接成功:{sta.ifconfig()}") 
    else: print("连接超时") 
    return sta 

async def aconnect_wifi(ssid='ssid',key='key',timeout=30):     # 异步连接Wi-Fi
    sta = network.WLAN(network.STA_IF) 
    sta.active(True) 
    if not sta.isconnected():
        print(f'连接到{ssid}...')
        sta.connect(ssid, key)
        while not sta.isconnected() and timeout>0:
            await asyncio.sleep(1); timeout -= 1     
    if sta.isconnected(): print(f"连接成功:{sta.ifconfig()}") 
    else: print("连接超时") 
    return sta 

# 配置AP模式（热点，允许其它设备连接）
def create_ap(ssid='ESP32_AP',key='12345678',ip=None):
    ap = network.WLAN(network.AP_IF)                           # 创建AP接口对象
    ap.active(True)                                            # 激活AP接口
    if ip is not None:                                         # 设置网络层接口参数
        ap.ifconfig((ip, '255.255.255.0', ip, ip))
    ap.config(ssid=ssid, key=key, security=network.WLAN.SEC_WPA_WPA2)
    if ap.active(): print(f"已启用热点{ssid}:{ap.ifconfig()}")  # 检查AP接口是否激活
    else: print("启用热点失败")
    return ap 

def sync_ntp(timezone = 8):
    ntptime.timeout = 2                               # 修改默认超时时间
    ntptime.host = "ntp.aliyun.com"                   # 指定NTP服务器，也可使用默认值
    # 同步时间
    print('当前设备时间:', time.localtime())
    for _ in range(2):                                # 尝试2次，避免超时错误
        try: ntptime.settime()                        # 设置ESP32的RTC时间为ntp
        except Exception:  continue 
    
    # 设置时区（默认东八区）
    t = time.localtime(time.time() + timezone * 3600) # (年,月,日,时,分,秒,weekday,yearday)
    tm = t[0:3] + (0,) + t[3:6] + (0,)                # (年,月,日,weekday,时,分,秒,subseconds)元组拼接
    RTC().datetime(tm)                                # 重新设置适合时区的时间    
    print("同步后的时间:", time.localtime())  

def mac():                                            # 获取设备mac地址
    return network.WLAN(network.STA_IF).config('mac')


if __name__ == '__main__':
    sta = connect_wifi('wiff_ssid', 'wiff_psw')       # 使用正确的ssid和key连接Wi-Fi
    sync_ntp()

